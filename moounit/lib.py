import uuid
from extism.extism import CompiledPlugin, TypeInferredFunction, HOST_FN_REGISTRY
import extism
import json
import os

import contextvars
from enum import Enum
from typing import List, Dict, Callable, Union, Any
from dataclasses import dataclass
import pytest
from core.types.protos.extensions_pb2 import (
    ExtensionCommandResponse,
    ExtensionCommand,
    ExtensionManifest,
    MainCommand,
    MainCommandResponse,
)


@dataclass
class Expectation:
    command: MainCommand
    response: Union[MainCommandResponse, Callable[[], MainCommandResponse]]
    times: int


@dataclass
class SystemTimeExpectation:
    return_value: Union[int, Callable[[], int]]
    times: int


@dataclass
class HashExpectation:
    hash_type: str
    data: bytes
    return_value: Union[bytes, Callable[[], bytes]]
    times: int


@dataclass
class OpenClientFdExpectation:
    path: str
    return_value: Union[int, Callable[[], int]]
    times: int


@dataclass
class WriteSockExpectation:
    sock_id: int
    buf: bytes
    return_value: Union[int, Callable[[], int]]
    times: int


@dataclass
class ReadSockExpectation:
    sock_id: int
    read_len: int
    return_value: Union[bytes, Callable[[], bytes]]
    times: int


received_commands: dict[list[MainCommand]] = []


class Scope(Enum):
    SESSION = "session"
    LOCAL = "local"


current_scope = contextvars.ContextVar("current_scope", default=Scope.SESSION)


class Moounit:
    _instances: Dict[str, "Moounit"] = {}

    def _parse_manifest(self, path: str) -> ExtensionManifest:
        with open(os.path.join(path, "package.json"), "r") as f:
            manifest = json.load(f)
            return ExtensionManifest(
                moosync_extension=True,
                display_name=manifest["name"],
                version=manifest["version"],
                extension_entry=os.path.join(path, manifest["extensionEntry"]),
            )

    def _get_extism_manifest(
        self, manifest: ExtensionManifest
    ) -> (uuid.UUID, CompiledPlugin):
        id = uuid.uuid4()

        def _guard(default: Any, func: Callable[[Moounit], Any], error_msg: str) -> Any:
            instance = Moounit._instances.get(id)
            try:
                if instance:
                    return func(instance)

                raise AssertionError(error_msg)
            except Exception as e:
                if instance:
                    instance.pending_exception = e
                return default

        def system_time() -> int:
            return _guard(
                0,
                lambda i: i._check_system_time(),
                "Unexpected call to system_time. If this call is expected, please ensure you have set an expectation using expect_system_time.",
            )

        def open_clientfd(path: str) -> int:
            return _guard(
                0,
                lambda i: i._check_open_clientfd(path),
                f"Unexpected call to open_clientfd with path: {path}. If this call is expected, please ensure you have set an expectation using expect_open_clientfd.",
            )

        def write_sock(sock_id: int, buf: bytes) -> int:
            return _guard(
                0,
                lambda i: i._check_write_sock(sock_id, buf),
                f"Unexpected call to write_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_write_sock.",
            )

        def read_sock(sock_id: int, read_len: int) -> bytes:
            return _guard(
                b"",
                lambda i: i._check_read_sock(sock_id, read_len),
                f"Unexpected call to read_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_read_sock.",
            )

        def hash(hash_type: str, data: bytes) -> bytes:
            return _guard(
                b"",
                lambda i: i._check_hash(hash_type, data),
                f"Unexpected call to hash with type: {hash_type}, data: {data}. If this call is expected, please ensure you have set an expectation using expect_hash.",
            )

        def send_main_command(data: bytes) -> bytes:
            instance = None
            if id in Moounit._instances:
                instance = Moounit._instances[id]
            elif len(Moounit._instances) == 1:
                instance = list(Moounit._instances.values())[0]

            if not instance:
                return b""

            try:
                return instance.handle_main_command(data)
            except Exception as e:
                instance.pending_exception = e
                return b""

        fns = [
            TypeInferredFunction(
                None,
                system_time.__name__,
                system_time,
                [int(0).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                open_clientfd.__name__,
                open_clientfd,
                [int(1).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                write_sock.__name__,
                write_sock,
                [int(2).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                read_sock.__name__,
                read_sock,
                [int(3).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None, hash.__name__, hash, [int(4).to_bytes(length=4, byteorder="big")]
            ),
            TypeInferredFunction(
                None,
                send_main_command.__name__,
                send_main_command,
                [int(5).to_bytes(length=4, byteorder="big")],
            ),
        ]

        HOST_FN_REGISTRY.clear()
        HOST_FN_REGISTRY.extend(fns)

        compiled = CompiledPlugin(
            {
                "wasm": [
                    {
                        "path": manifest.extension_entry,
                        "name": manifest.display_name,
                    }
                ]
            },
            wasi=True,
            functions=fns,
        )

        return (id, compiled)

    def _load_extension(self, path: str, manifest: ExtensionManifest):
        (id, compiled_plugin) = self._get_extism_manifest(manifest)
        self.plugin = extism.Plugin(compiled_plugin)
        Moounit._instances[id] = self

    def call_entry(self) -> bytes:
        ret = self.plugin.call("entry", data=b"")
        if self.pending_exception:
            exc = self.pending_exception
            self.pending_exception = None
            raise exc
        return ret

    def send_command(self, command: ExtensionCommand) -> ExtensionCommandResponse:
        data = command.SerializeToString()
        resp = self.plugin.call("handle_extension_command", data)
        if self.pending_exception:
            exc = self.pending_exception
            self.pending_exception = None
            raise exc
        return ExtensionCommandResponse.FromString(resp)

    def __init__(self, path: str):
        self.pending_exception: Exception | None = None
        self.session_expectations: List[Expectation] = []
        self.local_expectations: List[Expectation] = []

        self.session_system_time_expectations: List[SystemTimeExpectation] = []
        self.local_system_time_expectations: List[SystemTimeExpectation] = []

        self.session_hash_expectations: List[HashExpectation] = []
        self.local_hash_expectations: List[HashExpectation] = []

        self.session_open_clientfd_expectations: List[OpenClientFdExpectation] = []
        self.local_open_clientfd_expectations: List[OpenClientFdExpectation] = []

        self.session_write_sock_expectations: List[WriteSockExpectation] = []
        self.local_write_sock_expectations: List[WriteSockExpectation] = []

        self.session_read_sock_expectations: List[ReadSockExpectation] = []
        self.local_read_sock_expectations: List[ReadSockExpectation] = []

        manifest = self._parse_manifest(path)
        self._load_extension(path, manifest)

    def expect_command(
        self,
        command: MainCommand,
        response: Union[MainCommandResponse, Callable[[], MainCommandResponse]],
        times: int = 1,
    ):
        expectation = Expectation(
            command=command,
            response=response,
            times=times,
        )
        if current_scope.get() == Scope.LOCAL:
            self.local_expectations.append(expectation)
        else:
            self.session_expectations.append(expectation)

    def expect_system_time(
        self, return_value: Union[int, Callable[[], int]], times: int = 1
    ):
        expectation = SystemTimeExpectation(return_value=return_value, times=times)
        if current_scope.get() == Scope.LOCAL:
            self.local_system_time_expectations.append(expectation)
        else:
            self.session_system_time_expectations.append(expectation)

    def expect_hash(
        self,
        hash_type: str,
        data: bytes,
        return_value: Union[bytes, Callable[[], bytes]],
        times: int = 1,
    ):
        expectation = HashExpectation(
            hash_type=hash_type, data=data, return_value=return_value, times=times
        )
        if current_scope.get() == Scope.LOCAL:
            self.local_hash_expectations.append(expectation)
        else:
            self.session_hash_expectations.append(expectation)

    def expect_open_clientfd(
        self, path: str, return_value: Union[int, Callable[[], int]], times: int = 1
    ):
        expectation = OpenClientFdExpectation(
            path=path, return_value=return_value, times=times
        )
        if current_scope.get() == Scope.LOCAL:
            self.local_open_clientfd_expectations.append(expectation)
        else:
            self.session_open_clientfd_expectations.append(expectation)

    def expect_write_sock(
        self,
        sock_id: int,
        buf: bytes,
        return_value: Union[int, Callable[[], int]],
        times: int = 1,
    ):
        expectation = WriteSockExpectation(
            sock_id=sock_id, buf=buf, return_value=return_value, times=times
        )
        if current_scope.get() == Scope.LOCAL:
            self.local_write_sock_expectations.append(expectation)
        else:
            self.session_write_sock_expectations.append(expectation)

    def expect_read_sock(
        self,
        sock_id: int,
        read_len: int,
        return_value: Union[bytes, Callable[[], bytes]],
        times: int = 1,
    ):
        expectation = ReadSockExpectation(
            sock_id=sock_id, read_len=read_len, return_value=return_value, times=times
        )
        if current_scope.get() == Scope.LOCAL:
            self.local_read_sock_expectations.append(expectation)
        else:
            self.session_read_sock_expectations.append(expectation)

    def clear_local_expectations(self):
        self.local_expectations.clear()
        self.local_system_time_expectations.clear()
        self.local_hash_expectations.clear()
        self.local_open_clientfd_expectations.clear()
        self.local_write_sock_expectations.clear()
        self.local_read_sock_expectations.clear()

    def verify_and_clear_local_expectations(self):
        errors = []
        if self.local_expectations:
            errors.append(f"Unused command expectations: {self.local_expectations}")
        if self.local_system_time_expectations:
            errors.append(
                f"Unused system_time expectations: {self.local_system_time_expectations}"
            )
        if self.local_hash_expectations:
            errors.append(f"Unused hash expectations: {self.local_hash_expectations}")
        if self.local_open_clientfd_expectations:
            errors.append(
                f"Unused open_clientfd expectations: {self.local_open_clientfd_expectations}"
            )
        if self.local_write_sock_expectations:
            errors.append(
                f"Unused write_sock expectations: {self.local_write_sock_expectations}"
            )
        if self.local_read_sock_expectations:
            errors.append(
                f"Unused read_sock expectations: {self.local_read_sock_expectations}"
            )

        self.clear_local_expectations()

        if errors:
            raise AssertionError("\n".join(errors))

    def clear_session_expectations(self):
        self.session_expectations.clear()
        self.session_system_time_expectations.clear()
        self.session_hash_expectations.clear()
        self.session_open_clientfd_expectations.clear()
        self.session_write_sock_expectations.clear()
        self.session_read_sock_expectations.clear()

    def verify_and_clear_session_expectations(self):
        errors = []
        if self.session_expectations:
            errors.append(
                f"Unused session command expectations: {self.session_expectations}"
            )
        if self.session_system_time_expectations:
            errors.append(
                f"Unused session system_time expectations: {self.session_system_time_expectations}"
            )
        if self.session_hash_expectations:
            errors.append(
                f"Unused session hash expectations: {self.session_hash_expectations}"
            )
        if self.session_open_clientfd_expectations:
            errors.append(
                f"Unused session open_clientfd expectations: {self.session_open_clientfd_expectations}"
            )
        if self.session_write_sock_expectations:
            errors.append(
                f"Unused session write_sock expectations: {self.session_write_sock_expectations}"
            )
        if self.session_read_sock_expectations:
            errors.append(
                f"Unused session read_sock expectations: {self.session_read_sock_expectations}"
            )

        self.clear_session_expectations()

        if errors:
            raise AssertionError("\n".join(errors))

    def _get_value(self, val: Union[Any, Callable[[], Any]]) -> Any:
        if callable(val):
            return val()
        return val

    def _consume_expectation(
        self,
        local_list: List[Any],
        session_list: List[Any],
        matcher: Callable[[Any], bool],
        error_msg: str,
    ) -> Any:
        expectations = local_list + session_list
        for exp in expectations:
            if matcher(exp):
                exp.times -= 1
                if exp.times <= 0:
                    if exp in local_list:
                        local_list.remove(exp)
                    else:
                        session_list.remove(exp)
                return exp
        raise AssertionError(error_msg)

    def _check_system_time(self) -> int:
        exp = self._consume_expectation(
            self.local_system_time_expectations,
            self.session_system_time_expectations,
            lambda _: True,
            "Unexpected call to system_time. If this call is expected, please ensure you have set an expectation using expect_system_time.",
        )
        return self._get_value(exp.return_value)

    def _check_hash(self, hash_type: str, data: bytes) -> bytes:
        exp = self._consume_expectation(
            self.local_hash_expectations,
            self.session_hash_expectations,
            lambda e: e.hash_type == hash_type and e.data == data,
            f"Unexpected call to hash with type: {hash_type}, data: {data}. If this call is expected, please ensure you have set an expectation using expect_hash.",
        )
        return self._get_value(exp.return_value)

    def _check_open_clientfd(self, path: str) -> int:
        exp = self._consume_expectation(
            self.local_open_clientfd_expectations,
            self.session_open_clientfd_expectations,
            lambda e: e.path == path,
            f"Unexpected call to open_clientfd with path: {path}. If this call is expected, please ensure you have set an expectation using expect_open_clientfd.",
        )
        return self._get_value(exp.return_value)

    def _check_write_sock(self, sock_id: int, buf: bytes) -> int:
        exp = self._consume_expectation(
            self.local_write_sock_expectations,
            self.session_write_sock_expectations,
            lambda e: e.sock_id == sock_id and e.buf == buf,
            f"Unexpected call to write_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_write_sock.",
        )
        return self._get_value(exp.return_value)

    def _check_read_sock(self, sock_id: int, read_len: int) -> bytes:
        exp = self._consume_expectation(
            self.local_read_sock_expectations,
            self.session_read_sock_expectations,
            lambda e: e.sock_id == sock_id and e.read_len == read_len,
            f"Unexpected call to read_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_read_sock.",
        )
        return self._get_value(exp.return_value)

    def handle_main_command(self, data: bytes) -> bytes:
        command = MainCommand.FromString(data)

        exp = self._consume_expectation(
            self.local_expectations,
            self.session_expectations,
            lambda e: e.command == command,
            f"Unexpected command: {command}. If this command is expected, please ensure you have set an expectation using expect_command.",
        )

        resp = exp.response
        if callable(resp):
            return resp().SerializeToString()
        return resp.SerializeToString()


@pytest.fixture(autouse=True)
def moounit_session():
    """
    Pytest fixture to manage Moounit expectation scopes.
    Sets the scope to LOCAL for each test function and clears local expectations afterwards.
    """
    token = current_scope.set(Scope.LOCAL)
    yield
    current_scope.reset(token)
    for instance in Moounit._instances.values():
        instance.verify_and_clear_local_expectations()


def pytest_addoption(parser):
    """
    Add CLI option for extension path.
    """
    parser.addoption(
        "--extension-path",
        action="store",
        default=None,
        help="Path to the extension to test",
    )


@pytest.fixture
def moounit(request, moounit_session):  # pylint: disable=unused-argument
    """
    Pytest fixture to provide a Moounit instance configured via CLI.
    """
    path: str = request.config.getoption("--extension-path")
    if path:
        # Handle multiple files passed via $(locations)
        path = path.split(" ")[0]
    print("got path", path, os.path.dirname(path), os.getcwd())
    if not path:
        pytest.fail("--extension-path CLI option is required")

    if not os.path.exists(path):
        pytest.fail(f"Extension not found at {path}")

    if os.path.isfile(path):
        path = os.path.dirname(path)

    instance = Moounit(path)
    instance.call_entry()
    return instance
