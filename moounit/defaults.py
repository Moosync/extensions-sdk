from core.types.protos.extensions_pb2 import (
    BatchHttpRequest,
    BatchHttpResponse,
    HttpResponse,
    HttpResult,
    MainCommand,
    MainCommandResponse,
    GetSongResponse,
    GetEntityResponse,
    GetCurrentSongResponse,
    GetPlayerStateResponse,
    GetVolumeResponse,
    GetTimeResponse,
    GetQueueResponse,
    GetPreferenceResponse,
    SetPreferenceResponse,
    GetSecureResponse,
    SetSecureResponse,
    AddSongsResponse,
    RemoveSongResponse,
    UpdateSongResponse,
    AddPlaylistResponse,
    AddToPlaylistResponse,
    RegisterOauthResponse,
    OpenExternalUrlResponse,
    SetAccountResponse,
    RegisterUserPreferenceResponse,
    UnregisterUserPreferenceResponse,
    ExtensionsUpdatedResponse,
    GetAppVersionResponse,
    GetCacheResponse,
    SetCacheResponse,
    SpawnProcessResponse,
    WriteProcessStdinResponse,
    ReadProcessStdoutResponse,
    KillProcessResponse,
    GetProcessStatusResponse,
    NotifyPlayerEventResponse,
    PreferenceData,
)


def default_main_command_response(cmd: MainCommand) -> MainCommandResponse:
    which = cmd.WhichOneof("command")
    if not which:
        return MainCommandResponse()

    mapping = {
        "get_song": lambda: MainCommandResponse(get_song=GetSongResponse()),
        "get_entity": lambda: MainCommandResponse(get_entity=GetEntityResponse()),
        "get_current_song": lambda: MainCommandResponse(
            get_current_song=GetCurrentSongResponse()
        ),
        "get_player_state": lambda: MainCommandResponse(
            get_player_state=GetPlayerStateResponse()
        ),
        "get_volume": lambda: MainCommandResponse(
            get_volume=GetVolumeResponse(volume=1.0)
        ),
        "get_time": lambda: MainCommandResponse(get_time=GetTimeResponse(time=0.0)),
        "get_queue": lambda: MainCommandResponse(get_queue=GetQueueResponse()),
        "get_preference": lambda: MainCommandResponse(
            get_preference=GetPreferenceResponse(
                data=PreferenceData(key=cmd.get_preference.data.key)
            )
        ),
        "set_preference": lambda: MainCommandResponse(
            set_preference=SetPreferenceResponse(success=True)
        ),
        "get_secure": lambda: MainCommandResponse(
            get_secure=GetSecureResponse(
                data=PreferenceData(key=cmd.get_secure.data.key)
            )
        ),
        "set_secure": lambda: MainCommandResponse(
            set_secure=SetSecureResponse(success=True)
        ),
        "add_songs": lambda: MainCommandResponse(add_songs=AddSongsResponse()),
        "remove_song": lambda: MainCommandResponse(
            remove_song=RemoveSongResponse(success=True)
        ),
        "update_song": lambda: MainCommandResponse(update_song=UpdateSongResponse()),
        "add_playlist": lambda: MainCommandResponse(
            add_playlist=AddPlaylistResponse(playlist_id="default-playlist")
        ),
        "add_to_playlist": lambda: MainCommandResponse(
            add_to_playlist=AddToPlaylistResponse(success=True)
        ),
        "register_oauth": lambda: MainCommandResponse(
            register_oauth=RegisterOauthResponse(success=True)
        ),
        "open_external_url": lambda: MainCommandResponse(
            open_external_url=OpenExternalUrlResponse(success=True)
        ),
        "set_account": lambda: MainCommandResponse(
            set_account=SetAccountResponse(success=True)
        ),
        "register_user_preference": lambda: MainCommandResponse(
            register_user_preference=RegisterUserPreferenceResponse(success=True)
        ),
        "unregister_user_preference": lambda: MainCommandResponse(
            unregister_user_preference=UnregisterUserPreferenceResponse(success=True)
        ),
        "extensions_updated": lambda: MainCommandResponse(
            extensions_updated=ExtensionsUpdatedResponse()
        ),
        "get_app_version": lambda: MainCommandResponse(
            get_app_version=GetAppVersionResponse(version="1.0.0")
        ),
        "get_cache": lambda: MainCommandResponse(get_cache=GetCacheResponse()),
        "set_cache": lambda: MainCommandResponse(
            set_cache=SetCacheResponse(success=True)
        ),
        "spawn_process": lambda: MainCommandResponse(
            spawn_process=SpawnProcessResponse(process_id=1, pid=1234)
        ),
        "write_process_stdin": lambda: MainCommandResponse(
            write_process_stdin=WriteProcessStdinResponse(bytes_written=0)
        ),
        "read_process_stdout": lambda: MainCommandResponse(
            read_process_stdout=ReadProcessStdoutResponse(data=b"")
        ),
        "kill_process": lambda: MainCommandResponse(
            kill_process=KillProcessResponse(success=True)
        ),
        "get_process_status": lambda: MainCommandResponse(
            get_process_status=GetProcessStatusResponse(is_running=True, exit_code=0)
        ),
        "notify_player_event": lambda: MainCommandResponse(
            notify_player_event=NotifyPlayerEventResponse()
        ),
    }

    builder = mapping.get(which)
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
