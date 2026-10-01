import json
import os
import tempfile
import uuid
from collections.abc import Callable
from typing import Any

import extism
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    ExtensionCommand,
    ExtensionCommandResponse,
    ExtensionManifest,
    MainCommand,
    MainCommandResponse,
    ManifestPermissions,
)
from extism.extism import (
    HOST_FN_REGISTRY,
    CompiledPlugin,
    Function,
    TypeInferredFunction,
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

        def _guard(func: Callable[[Moounit], Any], error_msg: str) -> Any:
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

        def hash_(hash_type: str, data: bytes) -> bytes:
            return _guard(
                lambda i: i.manager._check_hash(hash_type, data),
                f"Unexpected call to hash with type: {hash_type}, data: {data}. If this call is expected, please ensure you have set an expectation using expect_hash.",
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
                "hash",
                hash_,
                [(4).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                send_main_command.__name__,
                send_main_command,
                [(5).to_bytes(length=4, byteorder="big")],
            ),
            TypeInferredFunction(
                None,
                batch_http_request.__name__,
                batch_http_request,
                [(6).to_bytes(length=4, byteorder="big")],
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
    ):
        self.recorder = recorder or Recorder()
        self.manager = ExpectationManager(recorder=self.recorder, moounit=self)
        self._host_exception: Exception | None = None
        self._temp_dirs: list[tempfile.TemporaryDirectory] = []
        self._mapped_paths: dict[str, str] = {}

        manifest = self._parse_manifest(path)
        self.socket_manager = RealSocketManager(dict(manifest.permissions.paths))
        self._load_extension(manifest)

    def get_mapped_paths(self) -> dict[str, str]:
        return self._mapped_paths

    def expect_command(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_command(*args, **kwargs)

    def expect_system_time(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_system_time(*args, **kwargs)

    def expect_hash(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_hash(*args, **kwargs)

    def expect_open_clientfd(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_open_clientfd(*args, **kwargs)

    def expect_write_sock(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_write_sock(*args, **kwargs)

    def expect_read_sock(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_read_sock(*args, **kwargs)

    def expect_batch_http_request(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.expect_batch_http_request(*args, **kwargs)

    def replay_ignore(self, *args: Any, **kwargs: Any) -> Any:
        return self.manager.replay_ignore(*args, **kwargs)

    def clear_local_expectations(self) -> None:
        self.manager.clear_local_expectations()

    def verify_and_clear_local_expectations(self) -> None:
        self.manager.verify_and_clear_local_expectations()

    def clear_session_expectations(self) -> None:
        self.manager.clear_session_expectations()

    def verify_and_clear_session_expectations(self) -> None:
        self.manager.verify_and_clear_session_expectations()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.manager, name)
