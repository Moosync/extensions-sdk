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

use extism_pdk::host_fn;
use serde_json::Value;
use types::entities::{QueryableAlbum, QueryableArtist, QueryablePlaylist, SearchResult};
use types::errors::Result as MoosyncResult;
use types::extensions::MainCommand;
use types::songs::Song;
use types::ui::extensions::{
    AccountLoginArgs, ContextMenuReturnType, CustomRequestReturnType, ExtensionAccountDetail,
    ExtensionProviderScope, PlaybackDetailsReturnType, PreferenceArgs,
};

#[allow(unused_variables)]
/// Trait for handling account-related events.
pub trait Accounts {
    /// Called when the main app requests the list of accounts.
    fn get_accounts(&self) -> MoosyncResult<Vec<ExtensionAccountDetail>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests to perform an account login.
    fn perform_account_login(&self, args: AccountLoginArgs) -> MoosyncResult<String> {
        Err("Not implemented".into())
    }

    /// Called when the main app provides an OAuth callback code.
    fn oauth_callback(&self, code: String) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling database-related events.
pub trait DatabaseEvents {
    /// Called when a song is added to the database.
    fn on_song_added(&self, song: Song) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a song is removed from the database.
    fn on_song_removed(&self, song: Song) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a playlist is added to the database.
    fn on_playlist_added(&self, playlist: QueryablePlaylist) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when a playlist is removed from the database.
    fn on_playlist_removed(&self, playlist: QueryablePlaylist) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling preference-related events.
pub trait PreferenceEvents {
    /// Called when preferences are changed.
    fn on_preferences_changed(&self, args: PreferenceArgs) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling player-related events.
pub trait PlayerEvents {
    /// Called when the queue is changed.
    fn on_queue_changed(&self, queue: Value) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the volume is changed.
    fn on_volume_changed(&self) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the player state is changed.
    fn on_player_state_changed(&self) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the song is changed.
    fn on_song_changed(&self) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the player is seeked to a specific time.
    fn on_seeked(&self, time: f64) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling provider-related events.
pub trait Provider {
    /// Called when the main app requests the provider scopes.
    fn get_provider_scopes(&self) -> MoosyncResult<Vec<ExtensionProviderScope>>;

    /// Called when the main app requests the list of playlists.
    fn get_playlists(&self) -> MoosyncResult<Vec<QueryablePlaylist>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests the content of a specific playlist.
    fn get_playlist_content(
        &self,
        id: String,
        next_page_token: Option<String>,
    ) -> MoosyncResult<Vec<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a playlist from a URL.
    fn get_playlist_from_url(&self, url: String) -> MoosyncResult<Option<QueryablePlaylist>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests playback details for a song.
    fn get_playback_details(&self, song: Song) -> MoosyncResult<PlaybackDetailsReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app performs a search.
    fn search(&self, term: String) -> MoosyncResult<SearchResult> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests recommendations.
    fn get_recommendations(&self) -> MoosyncResult<Vec<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a song from a URL.
    fn get_song_from_url(&self, url: String) -> MoosyncResult<Option<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app handles a custom request.
    fn handle_custom_request(&self, url: String) -> MoosyncResult<CustomRequestReturnType> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests songs of a specific artist.
    fn get_artist_songs(
        &self,
        artist: QueryableArtist,
        next_page_token: Option<String>,
    ) -> MoosyncResult<Vec<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests songs of a specific album.
    fn get_album_songs(
        &self,
        album: QueryableAlbum,
        next_page_token: Option<String>,
    ) -> MoosyncResult<Vec<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests a song from an ID.
    fn get_song_from_id(&self, id: String) -> MoosyncResult<Option<Song>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests to scrobble a song.
    fn scrobble(&self, song: Song) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests lyrics for a song.
    fn get_lyrics(&self, song: Song) -> MoosyncResult<String> {
        Err("Not implemented".into())
    }
}

#[allow(unused_variables)]
/// Trait for handling context menu-related events.
pub trait ContextMenu {
    /// Called when the main app requests the context menu for songs.
    fn get_song_context_menu(&self, songs: Vec<Song>) -> MoosyncResult<Vec<ContextMenuReturnType>> {
        Err("Not implemented".into())
    }

    /// Called when the main app requests the context menu for a playlist.
    fn get_playlist_context_menu(
        &self,
        playlist: QueryablePlaylist,
    ) -> MoosyncResult<Vec<ContextMenuReturnType>> {
        Err("Not implemented".into())
    }

    /// Called when the main app performs an action from the context menu.
    fn on_context_menu_action(&self, action: String) -> MoosyncResult<()> {
        Err("Not implemented".into())
    }
}

/// Trait that combines all other traits for the extension.
pub trait Extension:
    Provider + PlayerEvents + PreferenceEvents + DatabaseEvents + Accounts + ContextMenu
{
}

#[host_fn]
extern "ExtismHost" {
    fn send_main_command(command: MainCommand) -> Option<Value>;
    fn system_time() -> u64;
    fn open_clientfd(path: String) -> i64;
    fn write_sock(sock_id: i64, buf: Vec<u8>) -> i64;
    fn read_sock(sock_id: i64, read_len: u64) -> Vec<u8>;
    fn hash(hash_type: String, data: Vec<u8>) -> Vec<u8>;
}

pub mod extension_api {
    use serde_json::Value;
    use types::entities::{GetEntityOptions, QueryablePlaylist};
    use types::errors::{MoosyncError, Result as MoosyncResult};
    use types::extensions::MainCommand;
    use types::songs::{GetSongOptions, Song};
    use types::ui::extensions::{AddToPlaylistRequest, PreferenceData};
    use types::ui::player_details::PlayerState;

    use super::{
        hash, open_clientfd, read_sock as read_sock_ext, send_main_command, system_time,
        write_sock as write_sock_ext,
    };

    macro_rules! create_api_fn {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $variant:ident,
                $( $arg_name:ident : $arg_type:ty ),*
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name($( $arg_name: $arg_type ),*) -> MoosyncResult<$ret_type> {
                    unsafe {
                        match send_main_command(MainCommand::$variant($($arg_name),*)) {
                            Ok(resp) => {
                                if let Some(resp) = resp {
                                    return Ok(serde_json::from_value(resp)?);
                                }
                                Err(MoosyncError::String("No response".into()))
                            }
                            Err(e) => Err(e.to_string().into()),
                        }
                    }
                }
            )*
        };
    }

    macro_rules! create_api_fn_no_resp {
        ($(
            $(#[doc = $doc:literal])*
            $fn_name:ident (
                $variant:ident,
                $( $arg_name:ident : $arg_type:ty ),*
            ) -> $ret_type:ty
        );* $(;)?) => {
            $(
                $(#[doc = $doc])*
                pub fn $fn_name($( $arg_name: $arg_type ),*) -> MoosyncResult<$ret_type> {
                    unsafe {
                        match send_main_command(MainCommand::$variant($($arg_name),*)) {
                            Ok(_) => {
                                return Ok(())
                            }
                            Err(e) => Err(e.to_string().into()),
                        }
                    }
                }
            )*
        };
    }

    create_api_fn! {
        /// Retrieves a list of songs based on the provided options.
        ///
        /// # Arguments
        ///
        /// * `options` - The options to filter the songs.
        ///
        /// # Returns
        ///
        /// A vector of `Song` objects.
        get_song(GetSong, options: GetSongOptions) -> Vec<Song>;

        /// Retrieves the current song being played.
        ///
        /// # Returns
        ///
        /// An optional `Song` object representing the current song.
        get_current_song(GetCurrentSong,) -> Option<Song>;

        get_entity(GetEntity, options: GetEntityOptions) -> Vec<Value>;

        /// Retrieves the current state of the player.
        ///
        /// # Returns
        ///
        /// A `PlayerState` object representing the current state of the player.
        get_player_state(GetPlayerState,) -> PlayerState;

        /// Retrieves the current volume level.
        ///
        /// # Returns
        ///
        /// A floating-point number representing the current volume level.
        get_volume(GetVolume,) -> f64;

        /// Retrieves the current playback time.
        ///
        /// # Returns
        ///
        /// A floating-point number representing the current playback time in seconds.
        get_time(GetTime,) -> f64;

        /// Retrieves the current playback queue.
        ///
        /// # Returns
        ///
        /// A vector of `Song` objects representing the current queue.
        get_queue(GetQueue,) -> Vec<Song>;

        /// Retrieves a preference value based on the provided data.
        ///
        /// # Arguments
        ///
        /// * `data` - The data to filter the preference.
        ///
        /// # Returns
        ///
        /// A `Value` object representing the preference.
        get_preference(GetPreference, data: PreferenceData) -> PreferenceData;

        /// Retrieves a secure preference value based on the provided data.
        ///
        /// # Arguments
        ///
        /// * `data` - The data to filter the secure preference.
        ///
        /// # Returns
        ///
        /// A `Value` object representing the secure preference.
        get_secure(GetSecure, data: PreferenceData) -> PreferenceData;

        /// Adds a new playlist to the main app.
        ///
        /// # Arguments
        ///
        /// * `playlist` - The playlist to be added.
        ///
        /// # Returns
        ///
        /// A string representing the ID of the added playlist.
        add_playlist(AddPlaylist, playlist: QueryablePlaylist) -> String;
    }

    create_api_fn_no_resp! {
        /// Sets a preference value based on the provided data.
        ///
        /// # Arguments
        ///
        /// * `data` - The data to set the preference.
        set_preference(SetPreference, data: PreferenceData) -> ();

        /// Sets a secure preference value based on the provided data.
        ///
        /// # Arguments
        ///
        /// * `data` - The data to set the secure preference.
        set_secure(SetSecure, data: PreferenceData) -> ();

        /// Adds a list of songs to the main app.
        ///
        /// # Arguments
        ///
        /// * `songs` - The list of songs to be added.
        add_songs(AddSongs, songs: Vec<Song>) -> ();

        /// Removes a song from the main app.
        ///
        /// # Arguments
        ///
        /// * `song` - The song to be removed.
        remove_song(RemoveSong, song: Song) -> ();

        /// Updates a song in the main app.
        ///
        /// # Arguments
        ///
        /// * `song` - The song to be updated.
        update_song(UpdateSong, song: Song) -> ();

        /// Adds a song to a playlist.
        ///
        /// # Arguments
        ///
        /// * `request` - The request containing the song and playlist details.
        add_to_playlist(AddToPlaylist, request: AddToPlaylistRequest) -> ();

        /// Registers an OAuth token with the main app.
        ///
        /// # Arguments
        ///
        /// * `token` - The OAuth token to be registered.
        register_oauth(RegisterOAuth, token: String) -> ();

        /// Opens an external URL.
        ///
        /// # Arguments
        ///
        /// * `url` - The URL to be opened.
        open_external_url(OpenExternalUrl, url: String) -> ();

        /// Updates the list of accounts in the main app.
        ///
        /// # Arguments
        ///
        /// * `package_name` - The optional package name to filter the accounts.
        update_accounts(UpdateAccounts, package_name: Option<String>) -> ();

        /// Registers user preferences with the main app.
        ///
        /// # Arguments
        ///
        /// * `prefs` - A vector of `PreferenceUIData` representing the user preferences to register.
        register_user_preferences(RegisterUserPreference, prefs: Vec<PreferenceUIData>) -> ();

        /// Unregisters user preferences from the main app.
        ///
        /// # Arguments
        ///
        /// * `pref_keys` - A vector of strings representing the keys of the preferences to unregister.
        unregister_user_preferences(UnregisterUserPreference, pref_keys: Vec<String>) -> ();
    }

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
