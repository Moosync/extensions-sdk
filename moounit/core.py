# pylint: disable=duplicate-code
import os
import platform
import re
import sys
import tempfile
import uuid
import warnings
from collections.abc import Callable
from typing import TypeVar

from google.protobuf.message import Message
import extism
from extism.extism import (
    HOST_FN_REGISTRY,
    CompiledPlugin,
    ExplicitFunction,
    Function,
    TypeInferredFunction,
    ValType,
)
from core.types.protos.extensions_pb2 import (
    ExtensionAccountDetail,
    ExtensionCommand,
    ExtensionCommandResponse,
    ExtensionManifest,
    ExtensionProviderScope,
    MainCommand,
    MainCommandResponse,
)

from moounit.expectations import ExpectationManager, current_scope
from moounit.generated import (
    PLAYER_COMMANDS,
    GeneratedMoounitGuestClient,
)
from moounit.passthrough import (
    RealProcessManager,
    RealSocketManager,
    RealWebSocketManager,
)
from moounit.recorder import Recorder
from moounit.sanitize import (
    sanitize_extension_command,
    sanitize_extension_response,
)

EVENT_TO_PROVIDER_SCOPE: dict[str, int] = {
    "requested_search_result": ExtensionProviderScope.SEARCH,
    "requested_playlists": ExtensionProviderScope.PLAYLISTS,
    "requested_playlist_songs": ExtensionProviderScope.PLAYLIST_SONGS,
    "requested_artist_songs": ExtensionProviderScope.ARTIST_SONGS,
    "requested_album_songs": ExtensionProviderScope.ALBUM_SONGS,
    "requested_recommendations": ExtensionProviderScope.RECOMMENDATIONS,
    "scrobble": ExtensionProviderScope.SCROBBLE,
    "playback_details_requested": ExtensionProviderScope.PLAYBACK_DETAILS,
    "requested_lyrics": ExtensionProviderScope.LYRICS,
    "requested_cover_art": ExtensionProviderScope.COVER_ART,
    "requested_song_context_menu": ExtensionProviderScope.SONG_CONTEXT_MENU,
    "requested_playlist_context_menu": ExtensionProviderScope.PLAYLIST_CONTEXT_MENU,
    "perform_account_login": ExtensionProviderScope.ACCOUNTS,
    "oauth_callback": ExtensionProviderScope.ACCOUNTS,
    "song_added": ExtensionProviderScope.DATABASE_SONG_EVENTS,
    "song_removed": ExtensionProviderScope.DATABASE_SONG_EVENTS,
    "playlist_added": ExtensionProviderScope.DATABASE_PLAYLIST_EVENTS,
    "playlist_removed": ExtensionProviderScope.DATABASE_PLAYLIST_EVENTS,
    "player_state_changed": ExtensionProviderScope.PLAYER_UI_EVENTS,
    "seeked": ExtensionProviderScope.PLAYER_UI_EVENTS,
    "volume_changed": ExtensionProviderScope.PLAYER_UI_EVENTS,
    "song_changed": ExtensionProviderScope.PLAYER_DATA_EVENTS,
    "song_queue_changed": ExtensionProviderScope.PLAYER_DATA_EVENTS,
    "can_play": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_play": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_pause": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_stop": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_seek": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_set_volume": ExtensionProviderScope.PLAYER_PROVIDER,
    "player_load_track": ExtensionProviderScope.PLAYER_PROVIDER,
}


class Moounit(GeneratedMoounitGuestClient):
    _instances: dict[uuid.UUID, "Moounit"] = {}
    _session_called_player_commands: set[str] = set()
    _has_player_provider_extension: bool = False
    _called_player_commands: set[str] = set()
    package_name: str = ""

    def _parse_manifest(self, path: str) -> ExtensionManifest:
        manifest_path = None
        if os.path.isfile(path):
            if path.endswith(".pb"):
                manifest_path = path
            else:
                cand = os.path.join(os.path.dirname(path), "manifest.pb")
                if os.path.exists(cand):
                    manifest_path = cand
        elif os.path.isdir(path):
            cand = os.path.join(path, "manifest.pb")
            if os.path.exists(cand):
                manifest_path = cand

        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "rb") as f:
                manifest = ExtensionManifest.FromString(f.read())
            parent = os.path.dirname(manifest_path)
            if not os.path.isabs(manifest.extension_entry):
                manifest.extension_entry = os.path.join(
                    parent, manifest.extension_entry
                )
            return manifest

        raise FileNotFoundError(f"manifest.pb not found for path: {path}")

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

        def send_main_command(data: bytes) -> bytes:
            return _guard(
                lambda i: i.manager.handle_main_command(data),
                "No Moounit instance found for send_main_command",
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
                send_main_command.__name__,
                send_main_command,
                [(0).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_request",
                [ValType.I64, ValType.I64],
                [ValType.I64],
                http_request,
                [(1).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_status_code",
                [],
                [ValType.I32],
                http_status_code,
                [(2).to_bytes(length=4, byteorder="big")],
            ),
            ExplicitFunction(
                "extism:host/env",
                "http_headers",
                [],
                [ValType.I64],
                http_headers,
                [(3).to_bytes(length=4, byteorder="big")],
            ),
        ]

        HOST_FN_REGISTRY.clear()
        HOST_FN_REGISTRY.extend(fns)

        allowed_paths = {}
        cache_dir = getattr(self, "_cache_dir", None)
        ext_cache_dir = cache_dir.name if cache_dir is not None else tempfile.gettempdir()
        for p in manifest.permissions.paths:
            resolved_src = re.sub(
                r"\{([A-Z_][A-Z0-9_]*)\}",
                lambda m: ext_cache_dir if m.group(1) == "CACHE_DIR" else os.environ.get(m.group(1), ""),
                p.source,
            )
            temp_dir = tempfile.TemporaryDirectory()
            self._temp_dirs.append(temp_dir)
            allowed_paths[temp_dir.name] = p.target
            self._mapped_paths[resolved_src] = temp_dir.name
            self._mapped_paths[p.source] = temp_dir.name
            self._mapped_paths[p.target] = temp_dir.name

        if hasattr(self, "process_manager") and self.process_manager is not None:
            self.process_manager.mapped_paths = self._mapped_paths

        target_os = (
            "linux"
            if sys.platform.startswith("linux")
            else (
                "macos"
                if sys.platform == "darwin"
                else (
                    "windows" if sys.platform in ("win32", "cygwin") else sys.platform
                )
            )
        )
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            target_arch = "x86_64"
        elif machine in ("aarch64", "arm64"):
            target_arch = "aarch64"
        elif machine in ("i386", "i686", "x86"):
            target_arch = "x86"
        else:
            target_arch = machine

        compiled = CompiledPlugin(
            {
                "wasm": [
                    {
                        "path": manifest.extension_entry,
                        "name": manifest.display_name,
                    }
                ],
                "allowed_hosts": [h.host for h in manifest.permissions.hosts],
                "allowed_paths": allowed_paths,
                "config": {
                    "pid": str(os.getpid()),
                    "os": target_os,
                    "arch": target_arch,
                },
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

    def check_player_methods(self) -> None:
        if 0 < len(self._called_player_commands) < len(PLAYER_COMMANDS):
            missing = [
                cmd
                for cmd in PLAYER_COMMANDS
                if cmd not in self._called_player_commands
            ]
            warnings.warn(
                f"[Moosync Extension Warning] Not all player methods are registered or called. Missing: {', '.join(missing)}",
                UserWarning,
                stacklevel=2,
            )

    def close(self):
        """Free plugin resources and remove from Moounit instances registry."""
        self.check_player_methods()
        if hasattr(self, "socket_manager") and self.socket_manager:
            self.socket_manager.close_all()
        if hasattr(self, "ws_manager") and self.ws_manager:
            self.ws_manager.close_all()
        if hasattr(self, "process_manager") and self.process_manager:
            self.process_manager.close_all()
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

        event = command.WhichOneof("event")
        if event in PLAYER_COMMANDS:
            if "_called_player_commands" not in self.__dict__:
                self._called_player_commands = set()
            self._called_player_commands.add(event)
            Moounit._session_called_player_commands.add(event)

        if (
            event in EVENT_TO_PROVIDER_SCOPE
            and hasattr(self, "manifest")
            and self.manifest is not None
        ):
            required_scope = EVENT_TO_PROVIDER_SCOPE[event]
            scopes = {s.scope for s in self.manifest.scopes}
            assert required_scope in scopes, (
                f"Cannot call '{event}': extension does not have required scope "
                f"'{ExtensionProviderScope.Name(required_scope)}' in manifest scopes: "
                f"{[ExtensionProviderScope.Name(s) for s in scopes]}"
            )

        if event == "perform_account_login":
            account_id = command.perform_account_login.account_id
            if account_id:
                assert (
                    account_id in self.accounts
                ), f"Cannot call 'perform_account_login': account '{account_id}' does not exist in registered accounts: {list(self.accounts.keys())}"
            else:
                assert len(self.accounts) > 0, (
                    "Cannot call 'perform_account_login': no account exists. "
                    "The extension must register an account before login can be called."
                )

        sanitize_extension_command(command, self.package_name)
        data = command.SerializeToString()
        resp = self.plugin.call("handle_extension_command", data)
        self._check_host_exception()
        res_obj = ExtensionCommandResponse.FromString(resp)
        sanitize_extension_response(res_obj, self.package_name)
        return res_obj

    def __init__(
        self,
        path: str,
        recorder: Recorder | None = None,
        passthrough: bool = True,
        package_name: str | None = None,
    ):
        self.passthrough = passthrough
        self.recorder = recorder or Recorder()
        self.manager = ExpectationManager(recorder=self.recorder, moounit=self)
        self._host_exception: Exception | None = None
        self._temp_dirs: list[tempfile.TemporaryDirectory] = []
        self._cache_dir = tempfile.TemporaryDirectory()
        self._temp_dirs.append(self._cache_dir)
        self._mapped_paths: dict[str, str] = {}

        manifest = self._parse_manifest(path)
        self.manifest = manifest
        self._called_player_commands: set[str] = set()
        if any(
            s.scope == ExtensionProviderScope.PLAYER_PROVIDER
            for s in self.manifest.scopes
        ):
            Moounit._has_player_provider_extension = True
        self.package_name = package_name or manifest.name or manifest.display_name or ""
        allowed_paths = {p.source: p.target for p in manifest.permissions.paths}
        allowed_hosts = [h.host for h in manifest.permissions.hosts]
        self.socket_manager = RealSocketManager(allowed_paths)
        self.ws_manager = RealWebSocketManager(allowed_hosts)
        self.process_manager = RealProcessManager(
            allowed_binaries=list(manifest.permissions.binaries)
        )
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

    def replay_ignore(
        self,
        request: Message,
        ignore_fields: list[str] | str | None = None,
        ignore_field: list[str] | str | None = None,
        regex: str | None = None,
        test_name: str | None = None,
    ) -> None:
        self.manager.replay_ignore(
            request=request,
            ignore_fields=ignore_fields,
            ignore_field=ignore_field,
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
        if name in (
            "package_name",
            "manifest",
            "plugin",
            "manager",
            "_called_player_commands",
            "socket_manager",
            "ws_manager",
            "process_manager",
        ):
            raise AttributeError(name)
        return getattr(self.manager, name)
