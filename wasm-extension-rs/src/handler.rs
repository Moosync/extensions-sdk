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

use std::{cell::RefCell, rc::Rc};

use extism_pdk::FnResult;
use serde_json::Value;
use types::entities::{Playlist, Album, Artist, SearchResult};
use types::errors::Result as MoosyncResult;
use types::songs::Song;
use types::ui::extensions::{
    AccountLoginArgs, ContextMenuReturnType, CustomRequestReturnType, ExtensionAccountDetail,
    ExtensionProviderScope, PlaybackDetailsReturnType, PreferenceArgs,
    SongsWithPageTokenReturnType,
};

use crate::api::Extension;

macro_rules! generate_extension_methods {
    ($(
        $fn_name:ident (
            $( $arg_name:ident : $arg_type:ty ),*
        ) -> $ret_type:ty
    );* $(;)?) => {
        $(
            pub(crate) fn $fn_name($( $arg_name: $arg_type ),*) -> $ret_type {
                EXTENSION.with(|ext| {
                    if let Some(ext) = ext.borrow().as_ref() {
                        ext.$fn_name($( $arg_name ),*)
                    } else {
                        panic!("No extension registered");
                    }
                })
            }
        )*
    };
}

thread_local!(
    static EXTENSION: RefCell<Option<Rc<Box<dyn Extension>>>> = RefCell::new(None);
);

#[tracing::instrument(level = "debug", skip(extension))]
pub fn register_extension(extension: Box<dyn Extension>) -> FnResult<()> {
    EXTENSION.with(|ext| {
        ext.borrow_mut().replace(Rc::new(extension));
    });
    Ok(())
}

generate_extension_methods!(
    // Provider trait methods
    get_provider_scopes() -> MoosyncResult<Vec<ExtensionProviderScope>>;
    get_playlists() -> MoosyncResult<Vec<Playlist>>;
    get_playlist_content(id: String, next_page_token: Option<String>) -> MoosyncResult<SongsWithPageTokenReturnType>;
    get_playlist_from_url(url: String) -> MoosyncResult<Option<Playlist>>;
    get_playback_details(song: Song) -> MoosyncResult<PlaybackDetailsReturnType>;
    search(term: String) -> MoosyncResult<SearchResult>;
    get_recommendations() -> MoosyncResult<Vec<Song>>;
    get_song_from_url(url: String) -> MoosyncResult<Option<Song>>;
    handle_custom_request(url: String) -> MoosyncResult<CustomRequestReturnType>;
    get_artist_songs(artist: Artist, next_page_token: Option<String>) -> MoosyncResult<SongsWithPageTokenReturnType>;
    get_album_songs(album: Album, next_page_token: Option<String>) -> MoosyncResult<SongsWithPageTokenReturnType>;
    get_song_from_id(id: String) -> MoosyncResult<Option<Song>>;
    scrobble(song: Song) -> MoosyncResult<()>;
    oauth_callback(code: String) -> MoosyncResult<()>;
    get_lyrics(song: Song) -> MoosyncResult<String>;

    // PlayerEvents trait methods
    on_queue_changed(queue: Value) -> MoosyncResult<()>;
    on_volume_changed() -> MoosyncResult<()>;
    on_player_state_changed() -> MoosyncResult<()>;
    on_song_changed() -> MoosyncResult<()>;
    on_seeked(time: f64) -> MoosyncResult<()>;

    // PreferenceEvents trait methods
    on_preferences_changed(args: PreferenceArgs) -> MoosyncResult<()>;

    // DatabaseEvents trait methods
    on_song_added(song: Song) -> MoosyncResult<()>;
    on_song_removed(song: Song) -> MoosyncResult<()>;
    on_playlist_added(playlist: Playlist) -> MoosyncResult<()>;
    on_playlist_removed(playlist: Playlist) -> MoosyncResult<()>;

    // Account trait methods
    get_accounts() -> MoosyncResult<Vec<ExtensionAccountDetail>>;
    perform_account_login(args: AccountLoginArgs) -> MoosyncResult<String>;

    // ContextMenu trait methods
    get_song_context_menu(songs: Vec<Song>) -> MoosyncResult<Vec<ContextMenuReturnType>>;
    get_playlist_context_menu(playlist: Playlist) -> MoosyncResult<Vec<ContextMenuReturnType>>;
    on_context_menu_action(action: String) -> MoosyncResult<()>;
);
