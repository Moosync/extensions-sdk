import json
import os
import tempfile
import uuid
from collections.abc import Callable
from typing import TypeVar

from google.protobuf.message import Message
import extism
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    ExtensionAccountDetail,
    ExtensionCommand,
    ExtensionCommandResponse,
    ExtensionManifest,
    HttpRequest,
    HttpResult,
    MainCommand,
    MainCommandResponse,
    ManifestPermissions,
)
from extism.extism import (
    HOST_FN_REGISTRY,
    CompiledPlugin,
    ExplicitFunction,
    Function,
    TypeInferredFunction,
    ValType,
)

from moounit.expectations import ExpectationManager, current_scope
from moounit.passthrough import RealSocketManager
from moounit.recorder import Recorder


class Moounit:
    _instances: dict[uuid.UUID, "Moounit"] = {}

    def _parse_manifest(self, path: str) -> ExtensionManifest:
        with open(os.path.join(path, "package.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
            return ExtensionManifest(
                moosync_extension=True,
                display_name=manifest["name"],
                version=manifest["version"],
                extension_entry=os.path.join(path, manifest["extensionEntry"]),
                permissions=ManifestPermissions(
                    hosts=(manifest.get("permissions") or {}).get("hosts"),
                    paths=(manifest.get("permissions") or {}).get("paths"),
                ),
            )

    def _get_extism_manifest(
        self, manifest: ExtensionManifest
    ) -> tuple[uuid.UUID, CompiledPlugin]:
        id_ = uuid.uuid4()

        T = TypeVar("T")

        def _guard(func: Callable[[Moounit], T], error_msg: str) -> T:
            instance = Moounit._instances.get(id_)
            if not instance:
                raise AssertionError(error_msg)

            if instance._host_exception is not None:
                raise instance._host_exception

            try:
                return func(instance)
            except AssertionError as exc:
                instance._host_exception = exc
                raise

        def system_time() -> int:
            return _guard(
                lambda i: i.manager._check_system_time(),
                "Unexpected call to system_time. If this call is expected, please ensure you have set an expectation using expect_system_time.",
            )

        def open_clientfd(path: str) -> int:
            return _guard(
                lambda i: i.manager._check_open_clientfd(path),
                f"Unexpected call to open_clientfd with path: {path}. If this call is expected, please ensure you have set an expectation using expect_open_clientfd.",
            )

        def write_sock(sock_id: bytes, buf: bytes) -> int:
            return _guard(
                lambda i: i.manager._check_write_sock(
                    int.from_bytes(sock_id, "little"), buf
                ),
                f"Unexpected call to write_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_write_sock.",
            )

        def read_sock(sock_id: bytes, read_len: int) -> bytes:
            return _guard(
                lambda i: i.manager._check_read_sock(
                    int.from_bytes(sock_id, "little"), read_len
                ),
                f"Unexpected call to read_sock with sock_id: {sock_id}. If this call is expected, please ensure you have set an expectation using expect_read_sock.",
            )

        def send_main_command(data: bytes) -> bytes:
            return _guard(
                lambda i: i.manager.handle_main_command(data),
                "No Moounit instance found for send_main_command",
            )

        def batch_http_request(data: bytes) -> bytes:
            return _guard(
                lambda i: i.manager._check_batch_http_request(data),
                "Unexpected call to batch_http_request. If this call is expected, please ensure you have set an expectation using expect_batch_http_request.",
            )

        def http_request(
            plugin: extism.CurrentPlugin,
            inputs: list[extism.Val],
            outputs: list[extism.Val],
            *_user_data: bytes,
        ) -> None:
            req_offs = inputs[0].value
            body_offs = inputs[1].value
            offs = _guard(
                lambda i: i.manager._check_http_request(plugin, req_offs, body_offs),
                "Unexpected call to extism:host/env::http_request. If this call is expected, please ensure you have set an expectation using expect_batch_http_request.",
            )
            outputs[0]._assign(offs)

        def http_status_code(
            _plugin: extism.CurrentPlugin,
            _inputs: list[extism.Val],
            outputs: list[extism.Val],
            *_user_data: bytes,
        ) -> None:
            code = _guard(
                lambda i: i.manager._check_http_status_code(),
                "Unexpected call to extism:host/env::http_status_code.",
            )
            outputs[0]._assign(code)

        def http_headers(
            plugin: extism.CurrentPlugin,
            _inputs: list[extism.Val],
            outputs: list[extism.Val],
            *_user_data: bytes,
        ) -> None:
            offs = _guard(
                lambda i: i.manager._check_http_headers(plugin),
                "Unexpected call to extism:host/env::http_headers.",
            )
            outputs[0]._assign(offs)

        fns: list[Function] = [
            TypeInferredFunction(
                None,
                system_time.__name__,
                system_time,
                [(0).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                open_clientfd.__name__,
                open_clientfd,
                [(1).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                write_sock.__name__,
                write_sock,
                [(2).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                read_sock.__name__,
                read_sock,
                [(3).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                send_main_command.__name__,
                send_main_command,
                [(4).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                batch_http_request.__name__,
                batch_http_request,
                [(5).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_request",
                [ValType.I64, ValType.I64],
                [ValType.I64],
                http_request,
                [(6).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_status_code",
                [],
                [ValType.I32],
                http_status_code,
                [(7).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_headers",
                [],
                [ValType.I64],
                http_headers,
                [(8).to_bytes(length=4, byteorder="big")],
            ),
        ]

        HOST_FN_REGISTRY.clear()
        HOST_FN_REGISTRY.extend(fns)

        allowed_paths = {}
        for src, dest in manifest.permissions.paths.items():
            temp_dir = tempfile.TemporaryDirectory()
            self._temp_dirs.append(temp_dir)
            allowed_paths[temp_dir.name] = dest
            self._mapped_paths[src] = temp_dir.name

        compiled = CompiledPlugin(
            {
                "wasm": [
                    {
                        "path": manifest.extension_entry,
                        "name": manifest.display_name,
                    }
                ],
                "allowed_hosts": manifest.permissions.hosts._values,
                "allowed_paths": allowed_paths,
                "config": {"pid": str(os.getpid())},
            },
            wasi=True,
            functions=fns,
        )

        return (id_, compiled)

    def _load_extension(self, manifest: ExtensionManifest):
        (id_, compiled_plugin) = self._get_extism_manifest(manifest)
        self._plugin_id = id_
        self.plugin = extism.Plugin(compiled_plugin)
        Moounit._instances[id_] = self

    def close(self):
        """Free plugin resources and remove from Moounit instances registry."""
        if hasattr(self, "_plugin_id") and self._plugin_id in Moounit._instances:
            del Moounit._instances[self._plugin_id]
        if hasattr(self, "plugin") and self.plugin is not None:
            del self.plugin
            self.plugin = None

    def _check_host_exception(self):
        if self._host_exception is not None:
            exc = self._host_exception
            self._host_exception = None
            raise exc

    def call_entry(self) -> bytes:
        if self.plugin is None:
            raise RuntimeError("Plugin not loaded")
        ret = self.plugin.call("entry", data=b"")
        self._check_host_exception()
        return ret

    def send_command(self, command: ExtensionCommand) -> ExtensionCommandResponse:
        if self.plugin is None:
            raise RuntimeError("Plugin not loaded")
        data = command.SerializeToString()
        resp = self.plugin.call("handle_extension_command", data)
        self._check_host_exception()
        return ExtensionCommandResponse.FromString(resp)

    def __init__(
        self,
        path: str,
        recorder: Recorder | None = None,
        passthrough: bool = True,
    ):
        self.passthrough = passthrough
        self.recorder = recorder or Recorder()
        self.manager = ExpectationManager(recorder=self.recorder, moounit=self)
        self._host_exception: Exception | None = None
        self._temp_dirs: list[tempfile.TemporaryDirectory] = []
        self._mapped_paths: dict[str, str] = {}

        manifest = self._parse_manifest(path)
        self.socket_manager = RealSocketManager(dict(manifest.permissions.paths))
        self._load_extension(manifest)

    @property
    def accounts(self) -> dict[str, ExtensionAccountDetail]:
        return self.manager.accounts

    def get_mapped_paths(self) -> dict[str, str]:
        return self._mapped_paths

    def expect_command(
        self,
        command: MainCommand,
        response: MainCommandResponse | Callable[[], MainCommandResponse],
        times: int = 1,
    ) -> None:
        self.manager.expect_command(command, response, times=times)

    def expect_system_time(
        self, return_value: int | Callable[[], int], times: int = 1
    ) -> None:
        self.manager.expect_system_time(return_value, times=times)

    def expect_open_clientfd(
        self, path: str, return_value: int | Callable[[], int], times: int = 1
    ) -> None:
        self.manager.expect_open_clientfd(path, return_value, times=times)

    def expect_write_sock(
        self, sock_id: int, return_value: int | Callable[[], int], times: int = 1
    ) -> None:
        self.manager.expect_write_sock(sock_id, return_value, times=times)

    def expect_read_sock(
        self,
        sock_id: int,
        read_len: int,
        return_value: bytes | Callable[[], bytes],
        times: int = 1,
    ) -> None:
        self.manager.expect_read_sock(sock_id, read_len, return_value, times=times)

    def expect_batch_http_request(
        self,
        requests: BatchHttpRequest,
        responses: BatchHttpResponse | Callable[[], BatchHttpResponse],
        times: int = 1,
    ) -> None:
        self.manager.expect_batch_http_request(requests, responses, times=times)

    def replay_ignore(
        self,
        request: Message,
        ignore_fields: list[str] | None = None,
        regex: bool = False,
        test_name: str | None = None,
    ) -> None:
        self.manager.replay_ignore(
            request=request,
            ignore_fields=ignore_fields,
            regex=regex,
            test_name=test_name,
        )

    def clear_local_expectations(self) -> None:
        self.manager.clear_local_expectations()

    def verify_and_clear_local_expectations(self) -> None:
        self.manager.verify_and_clear_local_expectations()

    def clear_session_expectations(self) -> None:
        self.manager.clear_session_expectations()

    def verify_and_clear_session_expectations(self) -> None:
        self.manager.verify_and_clear_session_expectations()

    def __getattr__(self, name: str) -> object:
        return getattr(self.manager, name)
