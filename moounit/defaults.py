from collections.abc import Callable
from core.types.protos import extensions_pb2
from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpResponse,
    HttpResult,
    MainCommand,
    MainCommandResponse,
)
from moounit.generated import MAIN_COMMAND_DEFAULT_RESPONSES


def default_main_command_response(cmd: MainCommand) -> MainCommandResponse:
    which = cmd.WhichOneof("command")
    if not which:
        return MainCommandResponse()

    overrides: dict[str, Callable[[], MainCommandResponse]] = {
        "get_volume": lambda: MainCommandResponse(
            get_volume=extensions_pb2.GetVolumeResponse(volume=1.0)
        ),
        "get_preference": lambda: MainCommandResponse(
            get_preference=extensions_pb2.GetPreferenceResponse(
                data=extensions_pb2.PreferenceData(key=cmd.get_preference.data.key)
            )
        ),
        "get_secure": lambda: MainCommandResponse(
            get_secure=extensions_pb2.GetSecureResponse(
                data=extensions_pb2.PreferenceData(key=cmd.get_secure.data.key)
            )
        ),
        "set_preference": lambda: MainCommandResponse(
            set_preference=extensions_pb2.SetPreferenceResponse(success=True)
        ),
        "set_secure": lambda: MainCommandResponse(
            set_secure=extensions_pb2.SetSecureResponse(success=True)
        ),
        "add_songs": lambda: MainCommandResponse(
            add_songs=extensions_pb2.AddSongsResponse(success=True)
        ),
        "remove_song": lambda: MainCommandResponse(
            remove_song=extensions_pb2.RemoveSongResponse(success=True)
        ),
        "update_song": lambda: MainCommandResponse(
            update_song=extensions_pb2.UpdateSongResponse(success=True)
        ),
        "add_playlist": lambda: MainCommandResponse(
            add_playlist=extensions_pb2.AddPlaylistResponse(playlist_id="default-playlist")
        ),
        "add_to_playlist": lambda: MainCommandResponse(
            add_to_playlist=extensions_pb2.AddToPlaylistResponse(success=True)
        ),
        "register_oauth": lambda: MainCommandResponse(
            register_oauth=extensions_pb2.RegisterOauthResponse(success=True)
        ),
        "open_external_url": lambda: MainCommandResponse(
            open_external_url=extensions_pb2.OpenExternalUrlResponse(success=True)
        ),
        "set_account": lambda: MainCommandResponse(
            set_account=extensions_pb2.SetAccountResponse(success=True)
        ),
        "register_user_preference": lambda: MainCommandResponse(
            register_user_preference=extensions_pb2.RegisterUserPreferenceResponse(success=True)
        ),
        "unregister_user_preference": lambda: MainCommandResponse(
            unregister_user_preference=extensions_pb2.UnregisterUserPreferenceResponse(success=True)
        ),
        "extensions_updated": lambda: MainCommandResponse(
            extensions_updated=extensions_pb2.ExtensionsUpdatedResponse(success=True)
        ),
        "get_app_version": lambda: MainCommandResponse(
            get_app_version=extensions_pb2.GetAppVersionResponse(version="1.0.0")
        ),
        "set_cache": lambda: MainCommandResponse(
            set_cache=extensions_pb2.SetCacheResponse(success=True)
        ),
        "spawn_process": lambda: MainCommandResponse(
            spawn_process=extensions_pb2.SpawnProcessResponse(process_id=1, pid=1234)
        ),
        "write_process_stdin": lambda: MainCommandResponse(
            write_process_stdin=extensions_pb2.WriteProcessStdinResponse(
                bytes_written=len(cmd.write_process_stdin.data) if cmd.write_process_stdin else 0
            )
        ),
        "kill_process": lambda: MainCommandResponse(
            kill_process=extensions_pb2.KillProcessResponse(success=True)
        ),
        "get_process_status": lambda: MainCommandResponse(
            get_process_status=extensions_pb2.GetProcessStatusResponse(is_running=True, exit_code=0)
        ),
        "ws_connect": lambda: MainCommandResponse(
            ws_connect=extensions_pb2.WsConnectResponse(connection_id=1)
        ),
        "ws_send": lambda: MainCommandResponse(
            ws_send=extensions_pb2.WsSendResponse(success=True)
        ),
        "ws_close": lambda: MainCommandResponse(
            ws_close=extensions_pb2.WsCloseResponse(success=True)
        ),
    }

    builder = overrides.get(which) or MAIN_COMMAND_DEFAULT_RESPONSES.get(which)
    if builder:
        return builder()

    return MainCommandResponse()


def default_batch_http_response(req: BatchHttpRequest) -> BatchHttpResponse:
    results = []
    for _ in req.requests:
        results.append(
            HttpResult(
                response=HttpResponse(
                    status_code=200,
                    status_text="OK",
                    headers={},
                    body=b"",
                )
            )
        )
    return BatchHttpResponse(responses=results)


def default_system_time() -> int:
    return 0


def default_open_clientfd(_path: str) -> int:
    return 100


def default_write_sock(_sock_id: int, buf: bytes) -> int:
    return len(buf)


def default_read_sock(_sock_id: int, _read_len: int) -> bytes:
    return b""
