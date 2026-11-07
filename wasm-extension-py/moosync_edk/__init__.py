from enum import Enum
import os
import sys
from datetime import timedelta
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar, Union, cast

edk_paths = [p + "/moosync_edk" for p in sys.path if p.endswith("wasm-extension-py")]
__package__ = "moosync_edk"
__path__ = edk_paths
if "moosync_edk" not in sys.modules:
    sys.modules["moosync_edk"] = sys.modules[__name__]

import extism
from core.types.protos import extensions_pb2, preferences_pb2, songs_pb2, themes_pb2, ui_pb2

# Re-export protos
from core.types.protos.extensions_pb2 import *
from core.types.protos.preferences_pb2 import *
from core.types.protos.songs_pb2 import *
from core.types.protos.ui_pb2 import *
from google.protobuf.duration_pb2 import Duration
from google.protobuf.message import Message

T = TypeVar("T", bound=Message)

try:
    from .generated_api import *
    from .generated_dispatcher import *
except (ImportError, ValueError):
    try:
        from generated_api import *
        from generated_dispatcher import *
    except (ImportError, ValueError):
        from moosync_edk.generated_api import *
        from moosync_edk.generated_dispatcher import *

open_sock = open_clientfd
batch_http_request_host = batch_http_request


class CustomPrint:
    buf = ""

    def write(self, text):
        self.buf += text
        self.flush()

    def flush(self):
        extism.log(extism.LogLevel.Debug, self.buf)
        self.buf = ""


class HttpRequest:
    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[bytes, str]] = None,
        timeout_ms: Optional[int] = None,
    ):
        self.url = url
        self.method = method
        self.headers = headers or {}
        if isinstance(body, str):
            self.body = body.encode("utf-8")
        else:
            self.body = body
        self.timeout_ms = timeout_ms

    def to_proto(self) -> extensions_pb2.HttpRequest:
        return extensions_pb2.HttpRequest(
            url=self.url,
            method=self.method.upper(),
            headers=self.headers,
            body=self.body,
            timeout_ms=self.timeout_ms,
        )


class HttpResponse:
    def __init__(self, proto: extensions_pb2.HttpResponse):
        self.status_code: int = proto.status_code
        self.status_text: str = proto.status_text
        self.headers: dict = dict(proto.headers)
        self.body: bytes = proto.body

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        import json
        return json.loads(self.text)


class HttpResult:
    def __init__(self, proto: extensions_pb2.HttpResult):
        which = proto.WhichOneof("result")
        if which == "response":
            self.response: Optional[HttpResponse] = HttpResponse(proto.response)
            self.error: Optional[str] = None
        elif which == "error":
            self.response = None
            self.error = proto.error
        else:
            self.response = None
            self.error = "Empty HTTP result"


class PlaybackDetailsReturnType:
    def __init__(
        self,
        url: str,
        duration: Optional[timedelta] = None,
    ):
        self.url = url
        self.duration = duration

    def to_proto(self) -> extensions_pb2.PlaybackDetailsRequestedResponse:
        proto_duration = None
        if self.duration is not None:
            proto_duration = duration_to_proto(self.duration)
        return extensions_pb2.PlaybackDetailsRequestedResponse(
            url=self.url,
            duration=proto_duration,
        )


def http_batch_request(requests: Sequence[Union[HttpRequest, Dict[str, Any]]]) -> List[HttpResponse]:
    if not requests:
        return []
    proto_reqs = []
    for r in requests:
        if isinstance(r, HttpRequest):
            proto_reqs.append(r.to_proto())
        elif isinstance(r, dict):
            req_obj = HttpRequest(**r)
            proto_reqs.append(req_obj.to_proto())
        else:
            raise ValueError(f"Invalid request type: {type(r)}")

    batch = extensions_pb2.BatchHttpRequest(requests=proto_reqs)
    data = batch.SerializeToString()
    mem = extism.memory.alloc(data)
    if mem is None:
        raise Exception("Failed to allocate memory for HTTP batch request")
    res_offset = batch_http_request_host(mem.offset)

    res_mem_handle = extism.memory.find(res_offset)
    if res_mem_handle is None:
        raise Exception(f"Failed to find memory for batch HTTP response at offset {res_offset}")

    res_bytes = extism.memory.bytes(res_mem_handle)
    extism.memory.free(mem)

    batch_resp = extensions_pb2.BatchHttpResponse()
    batch_resp.ParseFromString(res_bytes)

    if batch_resp.HasField("error") and batch_resp.error:
        raise Exception(batch_resp.error)

    responses = []
    for idx, item in enumerate(batch_resp.responses):
        which = item.WhichOneof("result")
        if which == "response":
            responses.append(HttpResponse(item.response))
        elif which == "error":
            raise Exception(f"Request #{idx} failed: {item.error}")
        else:
            raise Exception(f"Request #{idx} returned empty HTTP result")
    return responses


def http_batch_get(
    urls: List[str],
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> List[HttpResponse]:
    reqs = [HttpRequest(url=u, method="GET", headers=headers, timeout_ms=timeout_ms) for u in urls]
    return http_batch_request(reqs)


def http_request(
    url: str,
    method: str = "GET",
    body: Optional[Union[bytes, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> HttpResponse:
    req = HttpRequest(
        url=url,
        method=method,
        headers=headers,
        body=body,
        timeout_ms=timeout_ms,
    )
    resps = http_batch_request([req])
    if not resps:
        raise Exception("Host runner returned empty response")
    return resps[0]


def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> HttpResponse:
    return http_request(url=url, method="GET", headers=headers, timeout_ms=timeout_ms)


def send_main_command_(
    cmd: extensions_pb2.MainCommand,
) -> extensions_pb2.MainCommandResponse:
    return send_main_command(cmd)
    resp.ParseFromString(res_bytes)
    return resp


class Api:
    def get_song(self, options: songs_pb2.GetSongOptions) -> List[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(
            get_song=extensions_pb2.GetSongRequest(options=options)
        )
        resp = send_main_command_(req)
        return list(resp.get_song.songs)

    def get_current_song(self) -> Optional[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(
            get_current_song=extensions_pb2.GetCurrentSongRequest()
        )
        resp = send_main_command_(req)
        if resp.HasField("get_current_song"):
            if resp.get_current_song.HasField("song"):
                return resp.get_current_song.song
        return None

    def get_player_state(self) -> extensions_pb2.PlayerState:
        req = extensions_pb2.MainCommand(
            get_player_state=extensions_pb2.GetPlayerStateRequest()
        )
        resp = send_main_command_(req)
        return resp.get_player_state.state

    def get_volume(self) -> float:
        req = extensions_pb2.MainCommand(get_volume=extensions_pb2.GetVolumeRequest())
        resp = send_main_command_(req)
        return resp.get_volume.volume

    def get_time(self) -> float:
        req = extensions_pb2.MainCommand(get_time=extensions_pb2.GetTimeRequest())
        resp = send_main_command_(req)
        return resp.get_time.time

    def get_queue(self) -> Optional[extensions_pb2.QueueState]:
        req = extensions_pb2.MainCommand(get_queue=extensions_pb2.GetQueueRequest())
        resp = send_main_command_(req)
        return resp.get_queue.queue

    def get_preference(
        self, data: extensions_pb2.PreferenceData
    ) -> extensions_pb2.PreferenceData:
        req = extensions_pb2.MainCommand(
            get_preference=extensions_pb2.GetPreferenceRequest(data=data)
        )
        resp = send_main_command_(req)
        return resp.get_preference.data

    def get_secure(
        self, data: extensions_pb2.PreferenceData
    ) -> extensions_pb2.PreferenceData:
        req = extensions_pb2.MainCommand(
            get_secure=extensions_pb2.GetSecureRequest(data=data)
        )
        resp = send_main_command_(req)
        return resp.get_secure.data

    def set_preference(self, data: extensions_pb2.PreferenceData) -> bool:
        req = extensions_pb2.MainCommand(
            set_preference=extensions_pb2.SetPreferenceRequest(data=data)
        )
        resp = send_main_command_(req)
        return resp.set_preference.success

    def set_secure(self, data: extensions_pb2.PreferenceData) -> bool:
        req = extensions_pb2.MainCommand(
            set_secure=extensions_pb2.SetSecureRequest(data=data)
        )
        resp = send_main_command_(req)
        return resp.set_secure.success

    def get_cache(self, key: str, proto_class: Type[T]) -> Optional[T]:
        req = extensions_pb2.MainCommand(
            get_cache=extensions_pb2.GetCacheRequest(key=key)
        )
        resp = send_main_command_(req)
        if resp.HasField("get_cache"):
            data = resp.get_cache.data
            if data:
                msg = proto_class()
                msg.ParseFromString(data)
                return msg
        return None

    def set_cache(
        self,
        key: str,
        data: Message,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        kwargs = {
            "key": key,
            "data": data.SerializeToString(),
        }
        if ttl_seconds is not None:
            kwargs["ttl_seconds"] = ttl_seconds
        req = extensions_pb2.MainCommand(
            set_cache=extensions_pb2.SetCacheRequest(**kwargs)
        )
        resp = send_main_command_(req)
        return resp.set_cache.success

    def add_songs(self, songs: List[songs_pb2.Song]) -> List[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(
            add_songs=extensions_pb2.AddSongsRequest(songs=songs)
        )
        resp = send_main_command_(req)
        return list(resp.add_songs.songs)

    def remove_song(self, song: songs_pb2.Song) -> bool:
        req = extensions_pb2.MainCommand(
            remove_song=extensions_pb2.RemoveSongRequest(song=song)
        )
        resp = send_main_command_(req)
        return resp.remove_song.success

    def update_song(self, song: songs_pb2.Song) -> songs_pb2.Song:
        req = extensions_pb2.MainCommand(
            update_song=extensions_pb2.UpdateSongRequest(song=song)
        )
        resp = send_main_command_(req)
        return resp.update_song.song

    def add_playlist(self, playlist: songs_pb2.Playlist) -> str:
        req = extensions_pb2.MainCommand(
            add_playlist=extensions_pb2.AddPlaylistRequest(playlist=playlist)
        )
        resp = send_main_command_(req)
        return resp.add_playlist.playlist_id

    def add_to_playlist(self, playlist_id: str, songs: List[songs_pb2.Song]) -> bool:
        req = extensions_pb2.MainCommand(
            add_to_playlist=extensions_pb2.AddToPlaylistRequest(
                playlist_id=playlist_id, songs=songs
            )
        )
        resp = send_main_command_(req)
        return resp.add_to_playlist.success

    def register_oauth(self, url: str) -> bool:
        req = extensions_pb2.MainCommand(
            register_oauth=extensions_pb2.RegisterOauthRequest(url=url)
        )
        resp = send_main_command_(req)
        return resp.register_oauth.success

    def open_external_url(self, url: str) -> bool:
        req = extensions_pb2.MainCommand(
            open_external_url=extensions_pb2.OpenExternalUrlRequest(url=url)
        )
        resp = send_main_command_(req)
        return resp.open_external_url.success

    def set_account(self, account: extensions_pb2.ExtensionAccountDetail) -> None:
        req = extensions_pb2.MainCommand(
            set_account=extensions_pb2.SetAccountRequest(account=account)
        )
        resp = send_main_command_(req)
        if not resp.HasField("set_account"):
            raise Exception("Failed to set account")

    def register_user_preferences(self, prefs: List[preferences_pb2.PreferenceItem]) -> bool:
        req = extensions_pb2.MainCommand(
            register_user_preference=extensions_pb2.RegisterUserPreferenceRequest(
                prefs=prefs
            )
        )
        resp = send_main_command_(req)
        return resp.register_user_preference.success

    def unregister_user_preferences(self, keys: List[str]) -> bool:
        req = extensions_pb2.MainCommand(
            unregister_user_preference=extensions_pb2.UnregisterUserPreferenceRequest(
                keys=keys
            )
        )
        resp = send_main_command_(req)
        return resp.unregister_user_preference.success


Extension.api = Api()








# Import extension module at the end to avoid circular dependency issues
# and ensure SDK classes are defined before extension tries to use them.
# The extension module is expected to be named 'main' (main.py).
extension_module = None
try:
    import sdk_main as extension_module
except ImportError as e:
    print(f"WARNING: Could not import 'main' module: {e}")


@extism.plugin_fn
def entry():
    sys.stdout = CustomPrint()
    print("PYTHON: entry() called")
    if extension_module:
        if hasattr(extension_module, "entry"):
            print("PYTHON: Calling extension_module.entry()")
            extension_module.entry()
        else:
            print("WARNING: 'main' module does not have an 'entry' function")
    else:
        raise Exception("Extension module not loaded")


def duration_to_proto(td: timedelta) -> Duration:
    """Convert datetime.timedelta to google.protobuf.Duration."""
    duration = Duration()
    duration.seconds = int(td.total_seconds())
    duration.nanos = int((td.microseconds % 1000000) * 1000)
    return duration


def parse_lrc(lrc_text: str) -> songs_pb2.Lyrics:
    """Parses standard LRC content into a Lyrics proto."""
    import re
    trimmed = lrc_text.strip()
    if not trimmed:
        raise ValueError("Empty LRC text")

    lines = []
    has_timestamps = False

    time_re = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")

    for raw_line in trimmed.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matches = list(time_re.finditer(line))
        if matches:
            has_timestamps = True
            last_match = matches[-1]
            text = line[last_match.end():].strip()

            for m in matches:
                minutes = int(m.group(1))
                seconds = int(m.group(2))
                frac_str = m.group(3) or "0"
                if len(frac_str) == 1:
                    millis = int(frac_str) * 100
                elif len(frac_str) == 2:
                    millis = int(frac_str) * 10
                elif len(frac_str) == 3:
                    millis = int(frac_str)
                else:
                    millis = int(frac_str[:3])

                time_ms = minutes * 60000 + seconds * 1000 + millis
                lines.append(songs_pb2.LyricLine(text=text, time_ms=time_ms))
        elif not has_timestamps:
            if not line.startswith("[") or not line.endswith("]"):
                lines.append(songs_pb2.LyricLine(text=line, time_ms=0))

    if has_timestamps:
        lines.sort(key=lambda l: l.time_ms)

    return songs_pb2.Lyrics(lines=lines, is_synced=has_timestamps)
