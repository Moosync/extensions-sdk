// Moosync
// Copyright (C) 2024, 2025  Moosync <support@moosync.app>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

use extensions_proto::struct_proto::google::protobuf::Struct as ProtoStruct;
use extism_pdk::{Prost, host_fn};

pub use extensions_proto::moosync::types::{
    AddPlaylistRequest, AddSongsRequest, AddToPlaylistRequest, ContextMenuActionRequest,
    ContextMenuReturnType, CustomRequest, ExtensionAccountDetail, ExtensionProviderScope,
    GetCurrentSongRequest, GetEntityRequest, GetPlayerStateRequest, GetPreferenceRequest,
    GetQueueRequest, GetSecureRequest, GetSongRequest, GetTimeRequest, GetVolumeRequest,
    MainCommand, MainCommandResponse, OauthCallbackRequest, OpenExternalUrlRequest,
    PerformAccountLoginRequest, PlaybackDetailsRequestedRequest, PlayerState,
    PlayerStateChangedRequest, PlaylistAddedRequest, PlaylistRemovedRequest,
    PreferenceChangedRequest, PreferenceData, RegisterOauthRequest, RegisterUserPreferenceRequest,
    RemoveSongRequest, RequestedAlbumSongsRequest, RequestedArtistSongsRequest,
    RequestedLyricsRequest, RequestedPlaylistContextMenuRequest, RequestedPlaylistFromUrlRequest,
    RequestedPlaylistSongsRequest, RequestedPlaylistsRequest, RequestedRecommendationsRequest,
    RequestedSearchResultRequest, RequestedSongContextMenuRequest, RequestedSongFromIdRequest,
    RequestedSongFromUrlRequest, ScrobbleRequest, SeekedRequest, SetPreferenceRequest,
    SetSecureRequest, SongAddedRequest, SongChangedRequest, SongQueueChangedRequest,
    SongRemovedRequest, UnregisterUserPreferenceRequest, UpdateAccountsRequest, UpdateSongRequest,
    VolumeChangedRequest,
};
use extensions_proto::struct_proto::google::protobuf::Value as ProtoValue;
use songs_proto::moosync::types::{Playlist, SearchResult, Song, EntityResult};
use ui_proto::moosync::types::PreferenceUiData;

pub type MoosyncResult<T> = Result<T, crate::handler::MoosyncError>;
pub type AccountLoginArgs = PerformAccountLoginRequest;

#[allow(unused_variables)]
/// Trait for handling account-related events.
pub trait Accounts {
    /// Called when the main app requests the list of accounts.
    fn get_accounts(&self) -> MoosyncResult<Vec<ExtensionAccountDetail>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests to perform an account login.
    fn perform_account_login(&self, req: PerformAccountLoginRequest) -> MoosyncResult<String> {
        Err("Not implemented".into())
    }

    /// Called when the main app provides an OAuth callback code.
    fn oauth_callback(&self, req: OauthCallbackRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling database-related events.
pub trait DatabaseEvents {
    /// Called when a song is added to the database.
    fn on_song_added(&self, req: SongAddedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a song is removed from the database.
    fn on_song_removed(&self, req: SongRemovedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a playlist is added to the database.
    fn on_playlist_added(&self, req: PlaylistAddedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a playlist is removed from the database.
    fn on_playlist_removed(&self, req: PlaylistRemovedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling preference-related events.
pub trait PreferenceEvents {
    /// Called when preferences are changed.
    fn on_preferences_changed(&self, req: PreferenceChangedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling player-related events.
pub trait PlayerEvents {
    /// Called when the queue is changed.
    fn on_queue_changed(&self, req: SongQueueChangedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the volume is changed.
    fn on_volume_changed(&self, req: VolumeChangedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the player state is changed.
    fn on_player_state_changed(&self, req: PlayerStateChangedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the song is changed.
    fn on_song_changed(&self, req: SongChangedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the player is seeked to a specific time.
    fn on_seeked(&self, req: SeekedRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling provider-related events.
pub trait Provider {
    /// Called when the main app requests the provider scopes.
    fn get_provider_scopes(&self) -> MoosyncResult<Vec<ExtensionProviderScope>>;

    /// Called when the main app requests the list of playlists.
    fn get_playlists(&self, req: RequestedPlaylistsRequest) -> MoosyncResult<Vec<Playlist>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests the content of a specific playlist.
    fn get_playlist_content(
        &self,
        req: RequestedPlaylistSongsRequest,
    ) -> MoosyncResult<SongsWithPageTokenReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a playlist from a URL.
    fn get_playlist_from_url(
        &self,
        req: RequestedPlaylistFromUrlRequest,
    ) -> MoosyncResult<Option<Playlist>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests playback details for a song.
    fn get_playback_details(
        &self,
        req: PlaybackDetailsRequestedRequest,
    ) -> MoosyncResult<PlaybackDetailsReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app performs a search.
    fn search(&self, req: RequestedSearchResultRequest) -> MoosyncResult<SearchResult> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests recommendations.
    fn get_recommendations(
        &self,
        req: RequestedRecommendationsRequest,
    ) -> MoosyncResult<Vec<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a song from a URL.
    fn get_song_from_url(&self, req: RequestedSongFromUrlRequest) -> MoosyncResult<Option<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app handles a custom request.
    fn handle_custom_request(&self, req: CustomRequest) -> MoosyncResult<CustomRequestReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests songs of a specific artist.
    fn get_artist_songs(
        &self,
        req: RequestedArtistSongsRequest,
    ) -> MoosyncResult<SongsWithPageTokenReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests songs of a specific album.
    fn get_album_songs(
        &self,
        req: RequestedAlbumSongsRequest,
    ) -> MoosyncResult<SongsWithPageTokenReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a song from an ID.
    fn get_song_from_id(&self, req: RequestedSongFromIdRequest) -> MoosyncResult<Option<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests to scrobble a song.
    fn scrobble(&self, req: ScrobbleRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests lyrics for a song.
    fn get_lyrics(&self, req: RequestedLyricsRequest) -> MoosyncResult<String> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling context menu-related events.
pub trait ContextMenu {
    /// Called when the main app requests the context menu for songs.
    fn get_song_context_menu(
        &self,
        req: RequestedSongContextMenuRequest,
    ) -> MoosyncResult<Vec<ContextMenuReturnType>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests the context menu for a playlist.
    fn get_playlist_context_menu(
        &self,
        req: RequestedPlaylistContextMenuRequest,
    ) -> MoosyncResult<Vec<ContextMenuReturnType>> {
        Err("Not implemented".into())
    }

    /// Called when the main app performs an action from the context menu.
    fn on_context_menu_action(&self, req: ContextMenuActionRequest) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

/// Trait that combines all other traits for the extension.
pub trait Extension:
    Provider + PlayerEvents + PreferenceEvents + DatabaseEvents + Accounts + ContextMenu
{
}

#[derive(Debug)]
pub struct PlaybackDetailsReturnType {
    pub duration: u32,
    pub url: String,
}

#[derive(Debug)]
pub struct SongsWithPageTokenReturnType {
    pub songs: Vec<Song>,
    pub next_page_token: Option<String>,
}

#[derive(Debug)]
pub struct ContextMenuReturnTypeWrapper(pub ContextMenuReturnType);

#[derive(Debug)]
pub struct CustomRequestReturnType {
    pub mime_type: Option<String>,
    pub data: Option<Vec<u8>>,
    pub redirect_url: Option<String>,
}

#[derive(Debug)]
pub struct EntityInfo {} // Dummy definition just in case, wait, not needed.

#[host_fn]
extern "ExtismHost" {
    fn send_main_command(command: Prost<MainCommand>) -> Prost<MainCommandResponse>;
    fn system_time() -> u64;
    fn open_clientfd(path: String) -> i64;
    fn write_sock(sock_id: i64, buf: Vec<u8>) -> i64;
    fn read_sock(sock_id: i64, read_len: u64) -> Vec<u8>;
    fn hash(hash_type: String, data: Vec<u8>) -> Vec<u8>;
}

pub mod extension_api {
    use super::*;
    use crate::handler::MoosyncError;
    use crate::response_utils::Extract;
    use extensions_proto::moosync::types::main_command::Command as MainCommandEnum;
    use extensions_proto::moosync::types::main_command_response::Response as MainCommandResponseEnum;
    use songs_proto::moosync::types::{GetEntityOptions, GetSongOptions}; // Needed

    use super::{
        hash, open_clientfd, read_sock as read_sock_ext, send_main_command, system_time,
        write_sock as write_sock_ext,
    };

    macro_rules! create_api_fn {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $Variant:ident,
                $ReqType:ident,
                $RespType:ident
                $(, $arg_name:ident : $arg_type:ty )*
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name($( $arg_name: $arg_type ),*) -> MoosyncResult<$ret_type> {
                    unsafe {
                        let request = $ReqType {
                            $( $arg_name: Some($arg_name.into()) ),*
                        };
                        let cmd_enum = MainCommandEnum::$Variant(request);
                        let cmd = MainCommand { command: Some(cmd_enum) };

                        let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

                        if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                            return Err(MoosyncError::String(e.message.clone()));
                        }

                        if let Some(MainCommandResponseEnum::$Variant(data)) = res.response {
                            return Ok(data.extract());
                        }

                        Err(MoosyncError::String("Host returned invalid response".into()))
                    }
                }
            )*
        };
    }

    macro_rules! create_api_fn_no_resp {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $Variant:ident,
                $ReqType:ident
                $(, $arg_name:ident : $arg_type:ty )*
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name($( $arg_name: $arg_type ),*) -> MoosyncResult<$ret_type> {
                    unsafe {
                        let request = $ReqType {
                            $( $arg_name: Some($arg_name.into()) ),*
                        };
                         let cmd_enum = MainCommandEnum::$Variant(request);
                        let cmd = MainCommand { command: Some(cmd_enum) };

                        let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

                        if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                            return Err(MoosyncError::String(e.message.clone()));
                        }

                        if let Some(MainCommandResponseEnum::$Variant(_)) = res.response {
                            return Ok(());
                        }

                        Err(MoosyncError::String("Host returned invalid response".into()))
                    }
                }
            )*
        };
    }

    // Special macro for repeated fields or non-optional ones if pattern differs
    macro_rules! create_api_fn_repeated {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $Variant:ident,
                $ReqType:ident,
                $field:ident,
                $arg_name:ident : $arg_type:ty
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name( $arg_name: $arg_type ) -> MoosyncResult<$ret_type> {
                    unsafe {
                        let request = $ReqType {
                            $field: $arg_name, // Direct assignment for repeated
                        };
                         let cmd_enum = MainCommandEnum::$Variant(request);
                        let cmd = MainCommand { command: Some(cmd_enum) };

                        let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

                        if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                            return Err(MoosyncError::String(e.message.clone()));
                        }

                        if let Some(MainCommandResponseEnum::$Variant(_)) = res.response {
                            return Ok(());
                        }

                         Err(MoosyncError::String("Host returned invalid response".into()))
                    }
                }
            )*
        };
    }

    create_api_fn! {
        /// Retrieves a list of songs based on the provided options.
        get_song(GetSong, GetSongRequest, GetSongResponse, options: GetSongOptions) -> Vec<Song>;

        /// Retrieves the current song being played.
        get_current_song(GetCurrentSong, GetCurrentSongRequest, GetCurrentSongResponse) -> Option<Song>;

        get_entity(GetEntity, GetEntityRequest, GetEntityResponse, options: GetEntityOptions) -> Option<EntityResult>;

        /// Retrieves the current state of the player.
        get_player_state(GetPlayerState, GetPlayerStateRequest, GetPlayerStateResponse) -> PlayerState;

        /// Retrieves the current volume level.
        get_volume(GetVolume, GetVolumeRequest, GetVolumeResponse) -> f64;

        /// Retrieves the current playback time.
        get_time(GetTime, GetTimeRequest, GetTimeResponse) -> f64;

        /// Retrieves the current playback queue.
        get_queue(GetQueue, GetQueueRequest, GetQueueResponse) -> Option<ProtoStruct>;

        /// Retrieves a preference value based on the provided data.
        get_preference(GetPreference, GetPreferenceRequest, GetPreferenceResponse, data: PreferenceData) -> PreferenceData;

        /// Retrieves a secure preference value based on the provided data.
        get_secure(GetSecure, GetSecureRequest, GetSecureResponse, data: PreferenceData) -> PreferenceData;

        /// Adds a new playlist to the main app.
        add_playlist(AddPlaylist, AddPlaylistRequest, AddPlaylistResponse, playlist: Playlist) -> String;
    }

    create_api_fn_no_resp! {
        /// Sets a preference value based on the provided data.
        set_preference(SetPreference, SetPreferenceRequest, data: PreferenceData) -> ();

        /// Sets a secure preference value based on the provided data.
        set_secure(SetSecure, SetSecureRequest, data: PreferenceData) -> ();

        /// Removes a song from the main app.
        remove_song(RemoveSong, RemoveSongRequest, song: Song) -> ();

        /// Updates a song in the main app.
        update_song(UpdateSong, UpdateSongRequest, song: Song) -> ();
    }

    /// Updates the list of accounts in the main app.
    pub fn update_accounts(account: Option<String>) -> MoosyncResult<()> {
        unsafe {
            let request = UpdateAccountsRequest { account };
            let cmd_enum = MainCommandEnum::UpdateAccounts(request);
            let cmd = MainCommand {
                command: Some(cmd_enum),
            };

            let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

            if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                return Err(MoosyncError::String(e.message.clone()));
            }

            if let Some(MainCommandResponseEnum::UpdateAccounts(_)) = res.response {
                return Ok(());
            }

            Err(MoosyncError::String(
                "Host returned invalid response".into(),
            ))
        }
    }
    // If I pass the struct directly, I don't need to construct it.
    // I need a special macro for "Pass Through Request".

    // Pass-through request (argument IS the request)
    macro_rules! create_api_fn_pass_through {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $Variant:ident,
                $ReqType:ident,
                $arg_name:ident : $arg_type:ty
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name( $arg_name: $arg_type ) -> MoosyncResult<$ret_type> {
                    unsafe {
                        // Argument is the request itself
                         let cmd_enum = MainCommandEnum::$Variant($arg_name);
                        let cmd = MainCommand { command: Some(cmd_enum) };

                        let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

                        if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                            return Err(MoosyncError::String(e.message.clone()));
                        }

                        if let Some(MainCommandResponseEnum::$Variant(_)) = res.response {
                            return Ok(());
                        }

                        Err(MoosyncError::String("Host returned invalid response".into()))
                    }
                }
            )*
        };
    }

    create_api_fn_pass_through! {
         /// Adds a song to a playlist.
        add_to_playlist(AddToPlaylist, AddToPlaylistRequest, request: AddToPlaylistRequest) -> ();
    }

    create_api_fn_repeated! {
         /// Adds a list of songs to the main app.
        add_songs(AddSongs, AddSongsRequest, songs, songs: Vec<Song>) -> ();

        // RegisterUserPreferenceRequest has 'prefs' field (repeated).
        /// Registers user preferences with the main app.
        register_user_preferences(RegisterUserPreference, RegisterUserPreferenceRequest, prefs, prefs: Vec<PreferenceUiData>) -> ();

        // UnregisterUserPreferenceRequest has 'keys' field.
        /// Unregisters user preferences from the main app.
        unregister_user_preferences(UnregisterUserPreference, UnregisterUserPreferenceRequest, keys, keys: Vec<String>) -> ();
    }

    // RegisterOAuth: `url`. Request field `url`.
    // OpenExternalUrl: `url`. Request field `url`.

    pub fn register_oauth(url: String) -> MoosyncResult<()> {
        unsafe {
            let request = RegisterOauthRequest { url };
            let cmd_enum = MainCommandEnum::RegisterOauth(request);
            let cmd = MainCommand {
                command: Some(cmd_enum),
            };
            let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

            if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                return Err(MoosyncError::String(e.message.clone()));
            }
            if let Some(MainCommandResponseEnum::RegisterOauth(_)) = res.response {
                return Ok(());
            }
            // Ignore other responses or treat as success if no error?
            // Better to return Ok only on matching response or if we don't care about specific return
            Ok(())
        }
    }

    pub fn open_external_url(url: String) -> MoosyncResult<()> {
        unsafe {
            let request = OpenExternalUrlRequest { url };
            let cmd_enum = MainCommandEnum::OpenExternalUrl(request);
            let cmd = MainCommand {
                command: Some(cmd_enum),
            };
            let extism_pdk::Prost(res) = send_main_command(extism_pdk::Prost(cmd)).unwrap();

            if let Some(MainCommandResponseEnum::Error(e)) = res.response.as_ref() {
                return Err(MoosyncError::String(e.message.clone()));
            }
            // OpenExternalUrlResponse
            Ok(())
        }
    }

    // update_accounts needs rename in signature or macro usage?
    // Macro assumes arg matches field.
    // I will rename signature arg to 'account'.

    pub fn get_system_time() -> u64 {
        unsafe {
            if let Ok(time) = system_time() {
                return time;
            }
            0u64
        }
    }

    pub fn open_sock(path: String) -> MoosyncResult<i64> {
        let res = unsafe { open_clientfd(path) };
        res.map_err(|e| MoosyncError::String(e.to_string()))
    }

    pub fn write_sock(sock_id: i64, buf: Vec<u8>) -> MoosyncResult<i64> {
        let res = unsafe { write_sock_ext(sock_id, buf) };
        res.map_err(|e| MoosyncError::String(e.to_string()))
    }

    pub fn read_sock(sock_id: i64, read_len: u64) -> MoosyncResult<Vec<u8>> {
        let res = unsafe { read_sock_ext(sock_id, read_len) };
        res.map_err(|e| MoosyncError::String(e.to_string()))
    }

    pub fn gen_hash(hash_type: String, data: Vec<u8>) -> MoosyncResult<Vec<u8>> {
        let res = unsafe { hash(hash_type, data) };
        res.map_err(|e| MoosyncError::String(e.to_string()))
    }
}
