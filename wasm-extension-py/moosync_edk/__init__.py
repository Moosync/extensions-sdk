import sys
import extism
from typing import Optional, List, Union, Any, cast
from core.types.protos import extensions_pb2
from core.types.protos import songs_pb2
from core.types.protos import ui_pb2
from core.types.protos import themes_pb2

# Re-export protos
from core.types.protos.extensions_pb2 import *
from core.types.protos.songs_pb2 import *
from core.types.protos.ui_pb2 import *
from core.types.protos.themes_pb2 import *

# Fix module split issue when running as entry point
if "moosync_edk" not in sys.modules:
    sys.modules["moosync_edk"] = sys.modules[__name__]


@extism.import_fn("extism:host/user", "open_clientfd")
def open_sock(path: str) -> int: ...

@extism.import_fn("extism:host/user", "write_sock")
def write_sock(sock_id:int, buf: bytes) -> int: ...

@extism.import_fn("extism:host/user", "read_sock")
def read_sock(sock_id: int, read_len: int) -> bytes: ...

@extism.import_fn("extism:host/user", "hash")
def hash(hash_type: str, data: bytes) -> bytes: ...

@extism.import_fn("extism:host/user", "send_main_command")
def send_main_command(data: int) -> int: ...

class CustomPrint():
    buf = ""

    def write(self, text):
        self.buf += text
        self.flush()

    def flush(self):
        extism.log(extism.LogLevel.Debug, self.buf)
        self.buf = ""

def http_request(url: str, method: str = "GET", body: Optional[Union[bytes, str]] = None, headers: Optional[dict] = None) -> Any:
    return extism.Http.request(url, method, body, headers)

def send_main_command_(cmd: extensions_pb2.MainCommand) -> extensions_pb2.MainCommandResponse:
    data = cmd.SerializeToString()
    mem = extism.memory.alloc(data)
    res_offset = send_main_command(mem.offset)
    
    res_mem_handle = extism.memory.find(res_offset)
    if res_mem_handle is None:
        raise Exception(f"Failed to find memory for response at offset {res_offset}")
        
    res_bytes = extism.memory.bytes(res_mem_handle)
    
    extism.memory.free(mem)
    
    resp = extensions_pb2.MainCommandResponse()
    resp.ParseFromString(res_bytes)
    return resp

class Api:
    def get_song(self, options: songs_pb2.GetSongOptions) -> List[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(get_song=extensions_pb2.GetSongRequest(options=options))
        resp = send_main_command_(req)
        return list(resp.get_song.songs)

    def get_current_song(self) -> Optional[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(get_current_song=extensions_pb2.GetCurrentSongRequest())
        resp = send_main_command_(req)
        if resp.HasField("get_current_song"):
             if resp.get_current_song.HasField("song"):
                 return resp.get_current_song.song
        return None

    def get_player_state(self) -> extensions_pb2.PlayerState:
        req = extensions_pb2.MainCommand(get_player_state=extensions_pb2.GetPlayerStateRequest())
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

    def get_queue(self) -> Any: # Returns Struct
        req = extensions_pb2.MainCommand(get_queue=extensions_pb2.GetQueueRequest())
        resp = send_main_command_(req)
        return resp.get_queue.queue

    def get_preference(self, data: extensions_pb2.PreferenceData) -> extensions_pb2.PreferenceData:
        req = extensions_pb2.MainCommand(get_preference=extensions_pb2.GetPreferenceRequest(data=data))
        resp = send_main_command_(req)
        return resp.get_preference.data

    def get_secure(self, data: extensions_pb2.PreferenceData) -> extensions_pb2.PreferenceData:
        req = extensions_pb2.MainCommand(get_secure=extensions_pb2.GetSecureRequest(data=data))
        resp = send_main_command_(req)
        return resp.get_secure.data

    def set_preference(self, data: extensions_pb2.PreferenceData) -> bool:
        req = extensions_pb2.MainCommand(set_preference=extensions_pb2.SetPreferenceRequest(data=data))
        resp = send_main_command_(req)
        return resp.set_preference.success

    def set_secure(self, data: extensions_pb2.PreferenceData) -> bool:
        req = extensions_pb2.MainCommand(set_secure=extensions_pb2.SetSecureRequest(data=data))
        resp = send_main_command_(req)
        return resp.set_secure.success

    def add_songs(self, songs: List[songs_pb2.Song]) -> List[songs_pb2.Song]:
        req = extensions_pb2.MainCommand(add_songs=extensions_pb2.AddSongsRequest(songs=songs))
        resp = send_main_command_(req)
        return list(resp.add_songs.songs)

    def remove_song(self, song: songs_pb2.Song) -> bool:
        req = extensions_pb2.MainCommand(remove_song=extensions_pb2.RemoveSongRequest(song=song))
        resp = send_main_command_(req)
        return resp.remove_song.success

    def update_song(self, song: songs_pb2.Song) -> songs_pb2.Song:
        req = extensions_pb2.MainCommand(update_song=extensions_pb2.UpdateSongRequest(song=song))
        resp = send_main_command_(req)
        return resp.update_song.song

    def add_playlist(self, playlist: songs_pb2.Playlist) -> str:
        req = extensions_pb2.MainCommand(add_playlist=extensions_pb2.AddPlaylistRequest(playlist=playlist))
        resp = send_main_command_(req)
        return resp.add_playlist.playlist_id

    def add_to_playlist(self, playlist_id: str, songs: List[songs_pb2.Song]) -> bool:
        req = extensions_pb2.MainCommand(
            add_to_playlist=extensions_pb2.AddToPlaylistRequest(playlist_id=playlist_id, songs=songs)
        )
        resp = send_main_command_(req)
        return resp.add_to_playlist.success

    def register_oauth(self, url: str) -> bool:
        req = extensions_pb2.MainCommand(register_oauth=extensions_pb2.RegisterOauthRequest(url=url))
        resp = send_main_command_(req)
        return resp.register_oauth.success

    def open_external_url(self, url: str) -> bool:
        req = extensions_pb2.MainCommand(open_external_url=extensions_pb2.OpenExternalUrlRequest(url=url))
        resp = send_main_command_(req)
        return resp.open_external_url.success

    def update_accounts(self, account: Optional[str] = None) -> bool:
        req = extensions_pb2.MainCommand(update_accounts=extensions_pb2.UpdateAccountsRequest(account=account))
        resp = send_main_command_(req)
        return resp.update_accounts.success

    def register_user_preferences(self, prefs: List[ui_pb2.PreferenceUiData]) -> bool:
        req = extensions_pb2.MainCommand(register_user_preference=extensions_pb2.RegisterUserPreferenceRequest(prefs=prefs))
        resp = send_main_command_(req)
        return resp.register_user_preference.success
    
    def unregister_user_preferences(self, keys: List[str]) -> bool:
        req = extensions_pb2.MainCommand(unregister_user_preference=extensions_pb2.UnregisterUserPreferenceRequest(keys=keys))
        resp = send_main_command_(req)
        return resp.unregister_user_preference.success

class Extension:
    api = Api()

    def get_provider_scopes(self, _: extensions_pb2.GetProviderScopesRequest) -> extensions_pb2.GetProviderScopesResponse:
        return extensions_pb2.GetProviderScopesResponse()

    def get_playlists(self, req: extensions_pb2.RequestedPlaylistsRequest) -> extensions_pb2.RequestedPlaylistsResponse:
        raise NotImplementedError()

    def get_playlist_content(self, req: extensions_pb2.RequestedPlaylistSongsRequest) -> extensions_pb2.RequestedPlaylistSongsResponse:
        raise NotImplementedError()

    def get_playlist_from_url(self, req: extensions_pb2.RequestedPlaylistFromUrlRequest) -> extensions_pb2.RequestedPlaylistFromUrlResponse:
        raise NotImplementedError()

    def get_playback_details(self, req: extensions_pb2.PlaybackDetailsRequestedRequest) -> extensions_pb2.PlaybackDetailsRequestedResponse:
        raise NotImplementedError()

    def get_search(self, req: extensions_pb2.RequestedSearchResultRequest) -> extensions_pb2.RequestedSearchResultResponse:
        raise NotImplementedError()

    def get_recommendations(self, req: extensions_pb2.RequestedRecommendationsRequest) -> extensions_pb2.RequestedRecommendationsResponse:
        raise NotImplementedError()

    def get_song_from_url(self, req: extensions_pb2.RequestedSongFromUrlRequest) -> extensions_pb2.RequestedSongFromUrlResponse:
        raise NotImplementedError()

    def handle_custom_request(self, req: extensions_pb2.CustomRequest) -> extensions_pb2.CustomRequestResponse:
        raise NotImplementedError()

    def get_artist_songs(self, req: extensions_pb2.RequestedArtistSongsRequest) -> extensions_pb2.RequestedArtistSongsResponse:
        raise NotImplementedError()

    def get_album_songs(self, req: extensions_pb2.RequestedAlbumSongsRequest) -> extensions_pb2.RequestedAlbumSongsResponse:
        raise NotImplementedError()

    def get_song_from_id(self, req: extensions_pb2.RequestedSongFromIdRequest) -> extensions_pb2.RequestedSongFromIdResponse:
        raise NotImplementedError()

    def on_queue_changed(self, req: extensions_pb2.SongQueueChangedRequest) -> extensions_pb2.SongQueueChangedResponse:
        raise NotImplementedError()

    def on_volume_changed(self, req: extensions_pb2.VolumeChangedRequest) -> extensions_pb2.VolumeChangedResponse:
        raise NotImplementedError()

    def on_player_state_changed(self, req: extensions_pb2.PlayerStateChangedRequest) -> extensions_pb2.PlayerStateChangedResponse:
        raise NotImplementedError()

    def on_song_changed(self, req: extensions_pb2.SongChangedRequest) -> extensions_pb2.SongChangedResponse:
        raise NotImplementedError()

    def on_seeked(self, req: extensions_pb2.SeekedRequest) -> extensions_pb2.SeekedResponse:
        raise NotImplementedError()

    def on_preferences_changed(self, req: extensions_pb2.PreferenceChangedRequest) -> extensions_pb2.PreferenceChangedResponse:
        raise NotImplementedError()

    def on_song_added(self, req: extensions_pb2.SongAddedRequest) -> extensions_pb2.SongAddedResponse:
        raise NotImplementedError()

    def on_song_removed(self, req: extensions_pb2.SongRemovedRequest) -> extensions_pb2.SongRemovedResponse:
        raise NotImplementedError()

    def on_playlist_added(self, req: extensions_pb2.PlaylistAddedRequest) -> extensions_pb2.PlaylistAddedResponse:
        raise NotImplementedError()

    def on_playlist_removed(self, req: extensions_pb2.PlaylistRemovedRequest) -> extensions_pb2.PlaylistRemovedResponse:
        raise NotImplementedError()

    def get_accounts(self, req: extensions_pb2.GetAccountsRequest) -> extensions_pb2.GetAccountsResponse:
        return extensions_pb2.GetAccountsResponse()

    def perform_account_login(self, req: extensions_pb2.PerformAccountLoginRequest) -> extensions_pb2.PerformAccountLoginResponse:
        raise NotImplementedError()

    def scrobble(self, req: extensions_pb2.ScrobbleRequest) -> extensions_pb2.ScrobbleResponse:
        raise NotImplementedError()

    def oauth_callback(self, req: extensions_pb2.OauthCallbackRequest) -> extensions_pb2.OauthCallbackResponse:
        raise NotImplementedError()

    def get_song_context_menu(self, req: extensions_pb2.RequestedSongContextMenuRequest) -> extensions_pb2.RequestedSongContextMenuResponse:
        raise NotImplementedError()

    def get_playlist_context_menu(self, req: extensions_pb2.RequestedPlaylistContextMenuRequest) -> extensions_pb2.RequestedPlaylistContextMenuResponse:
        raise NotImplementedError()

    def on_context_menu_action(self, req: extensions_pb2.ContextMenuActionRequest) -> extensions_pb2.ContextMenuActionResponse:
        raise NotImplementedError()

    def get_lyrics(self, req: extensions_pb2.RequestedLyricsRequest) -> extensions_pb2.RequestedLyricsResponse:
        raise NotImplementedError()

extension_instance: Optional[Extension] = None
def register_extension(extension: Extension):
    global extension_instance
    extension_instance = extension

def ensure_extension_instance() -> Extension:
    if extension_instance is None:
        raise Exception("Extension instance is not initialized")
    return extension_instance


@extism.plugin_fn
def handle_extension_command():
    input_data = extism.input_bytes()
    cmd = extensions_pb2.ExtensionCommand()
    cmd.ParseFromString(input_data)
    
    instance = ensure_extension_instance()
    response = extensions_pb2.ExtensionCommandResponse()
    
    which = cmd.WhichOneof("event")
    if which is None:
        return 0

    field_descriptor = cmd.DESCRIPTOR.fields_by_name[which]
    number = field_descriptor.number
    
    if number == extensions_pb2.ExtensionCommand.GET_PROVIDER_SCOPES_FIELD_NUMBER:
        response.get_provider_scopes.CopyFrom(instance.get_provider_scopes(cmd.get_provider_scopes))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_PLAYLISTS_FIELD_NUMBER:
        response.requested_playlists.CopyFrom(instance.get_playlists(cmd.requested_playlists))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_PLAYLIST_SONGS_FIELD_NUMBER:
        response.requested_playlist_songs.CopyFrom(instance.get_playlist_content(cmd.requested_playlist_songs))
    elif number == extensions_pb2.ExtensionCommand.OAUTH_CALLBACK_FIELD_NUMBER:
        response.oauth_callback.CopyFrom(instance.oauth_callback(cmd.oauth_callback))
    elif number == extensions_pb2.ExtensionCommand.SONG_QUEUE_CHANGED_FIELD_NUMBER:
        response.song_queue_changed.CopyFrom(instance.on_queue_changed(cmd.song_queue_changed))
    elif number == extensions_pb2.ExtensionCommand.SEEKED_FIELD_NUMBER:
        response.seeked.CopyFrom(instance.on_seeked(cmd.seeked))
    elif number == extensions_pb2.ExtensionCommand.VOLUME_CHANGED_FIELD_NUMBER:
        response.volume_changed.CopyFrom(instance.on_volume_changed(cmd.volume_changed))
    elif number == extensions_pb2.ExtensionCommand.PLAYER_STATE_CHANGED_FIELD_NUMBER:
        response.player_state_changed.CopyFrom(instance.on_player_state_changed(cmd.player_state_changed))
    elif number == extensions_pb2.ExtensionCommand.SONG_CHANGED_FIELD_NUMBER:
        response.song_changed.CopyFrom(instance.on_song_changed(cmd.song_changed))
    elif number == extensions_pb2.ExtensionCommand.PREFERENCE_CHANGED_FIELD_NUMBER:
        response.preference_changed.CopyFrom(instance.on_preferences_changed(cmd.preference_changed))
    elif number == extensions_pb2.ExtensionCommand.PLAYBACK_DETAILS_REQUESTED_FIELD_NUMBER:
        response.playback_details_requested.CopyFrom(instance.get_playback_details(cmd.playback_details_requested))
    elif number == extensions_pb2.ExtensionCommand.CUSTOM_REQUEST_FIELD_NUMBER:
        response.custom_request.CopyFrom(instance.handle_custom_request(cmd.custom_request))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_SONG_FROM_URL_FIELD_NUMBER:
        response.requested_song_from_url.CopyFrom(instance.get_song_from_url(cmd.requested_song_from_url))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_PLAYLIST_FROM_URL_FIELD_NUMBER:
        response.requested_playlist_from_url.CopyFrom(instance.get_playlist_from_url(cmd.requested_playlist_from_url))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_SEARCH_RESULT_FIELD_NUMBER:
        response.requested_search_result.CopyFrom(instance.get_search(cmd.requested_search_result))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_RECOMMENDATIONS_FIELD_NUMBER:
        response.requested_recommendations.CopyFrom(instance.get_recommendations(cmd.requested_recommendations))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_LYRICS_FIELD_NUMBER:
        response.requested_lyrics.CopyFrom(instance.get_lyrics(cmd.requested_lyrics))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_ARTIST_SONGS_FIELD_NUMBER:
        response.requested_artist_songs.CopyFrom(instance.get_artist_songs(cmd.requested_artist_songs))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_ALBUM_SONGS_FIELD_NUMBER:
        response.requested_album_songs.CopyFrom(instance.get_album_songs(cmd.requested_album_songs))
    elif number == extensions_pb2.ExtensionCommand.SONG_ADDED_FIELD_NUMBER:
        response.song_added.CopyFrom(instance.on_song_added(cmd.song_added))
    elif number == extensions_pb2.ExtensionCommand.SONG_REMOVED_FIELD_NUMBER:
        response.song_removed.CopyFrom(instance.on_song_removed(cmd.song_removed))
    elif number == extensions_pb2.ExtensionCommand.PLAYLIST_ADDED_FIELD_NUMBER:
        response.playlist_added.CopyFrom(instance.on_playlist_added(cmd.playlist_added))
    elif number == extensions_pb2.ExtensionCommand.PLAYLIST_REMOVED_FIELD_NUMBER:
        response.playlist_removed.CopyFrom(instance.on_playlist_removed(cmd.playlist_removed))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_SONG_FROM_ID_FIELD_NUMBER:
        response.requested_song_from_id.CopyFrom(instance.get_song_from_id(cmd.requested_song_from_id))
    elif number == extensions_pb2.ExtensionCommand.SCROBBLE_FIELD_NUMBER:
        response.scrobble.CopyFrom(instance.scrobble(cmd.scrobble))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_SONG_CONTEXT_MENU_FIELD_NUMBER:
        response.requested_song_context_menu.CopyFrom(instance.get_song_context_menu(cmd.requested_song_context_menu))
    elif number == extensions_pb2.ExtensionCommand.REQUESTED_PLAYLIST_CONTEXT_MENU_FIELD_NUMBER:
        response.requested_playlist_context_menu.CopyFrom(instance.get_playlist_context_menu(cmd.requested_playlist_context_menu))
    elif number == extensions_pb2.ExtensionCommand.CONTEXT_MENU_ACTION_FIELD_NUMBER:
        response.context_menu_action.CopyFrom(instance.on_context_menu_action(cmd.context_menu_action))
    elif number == extensions_pb2.ExtensionCommand.GET_ACCOUNTS_FIELD_NUMBER:
        response.get_accounts.CopyFrom(instance.get_accounts(cmd.get_accounts))
    elif number == extensions_pb2.ExtensionCommand.PERFORM_ACCOUNT_LOGIN_FIELD_NUMBER:
        response.perform_account_login.CopyFrom(instance.perform_account_login(cmd.perform_account_login))
        
    
    extism.output_bytes(response.SerializeToString())

# Import extension module at the end to avoid circular dependency issues
# and ensure SDK classes are defined before extension tries to use them.
# The extension module is expected to be named 'main' (main.py).
extension_module = None
try:
    import main as extension_module
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
