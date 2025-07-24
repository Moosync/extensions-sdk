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

pub use extism_pdk::{config, error, http, info, log, warn, HttpRequest, HttpResponse};
use extism_pdk::{plugin_fn, FnResult, Json};
use handler::{
    get_accounts, get_album_songs, get_artist_songs, get_lyrics, get_playback_details,
    get_playlist_content, get_playlist_context_menu, get_playlist_from_url, get_playlists,
    get_provider_scopes, get_recommendations, get_song_context_menu, get_song_from_id,
    get_song_from_url, handle_custom_request, oauth_callback, on_context_menu_action,
    on_player_state_changed, on_playlist_added, on_playlist_removed, on_preferences_changed,
    on_queue_changed, on_seeked, on_song_added, on_song_changed, on_song_removed,
    on_volume_changed, perform_account_login, scrobble, search,
};
use serde_json::Value;

pub use types::{
    entities::*, errors::*, extensions::*, preferences::*, songs::*, ui::extensions::*,
    ui::player_details::PlayerState,
};

pub mod api;
pub mod handler;

extern "C" {
    fn init();
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn entry() -> FnResult<()> {
    unsafe {
        init();
    }
    Ok(())
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_provider_scopes_wrapper() -> FnResult<Json<Vec<ExtensionProviderScope>>> {
    let ret = get_provider_scopes()?;
    Ok(Json(ret))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_playlists_wrapper() -> FnResult<Json<PlaylistReturnType>> {
    let ret = get_playlists()?;
    Ok(Json(PlaylistReturnType { playlists: ret }))
}

#[tracing::instrument(level = "debug", skip(id))]
#[plugin_fn]
pub fn get_playlist_content_wrapper(
    Json((id, token)): Json<(String, Option<String>)>,
) -> FnResult<Json<SongsWithPageTokenReturnType>> {
    let ret = get_playlist_content(id, token)?;
    Ok(Json(SongsWithPageTokenReturnType {
        songs: ret,
        next_page_token: None,
    }))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_playlist_from_url_wrapper(
    Json(url): Json<String>,
) -> FnResult<Json<PlaylistAndSongsReturnType>> {
    let ret = get_playlist_from_url(url)?;
    Ok(Json(PlaylistAndSongsReturnType {
        playlist: ret,
        songs: None,
    }))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_playback_details_wrapper(
    Json(song): Json<Song>,
) -> FnResult<Json<PlaybackDetailsReturnType>> {
    let ret = get_playback_details(song)?;
    Ok(Json(ret))
}

#[tracing::instrument(level = "debug", skip(term))]
#[plugin_fn]
pub fn search_wrapper(Json(term): Json<String>) -> FnResult<Json<SearchReturnType>> {
    let ret = search(term)?;
    Ok(Json(SearchReturnType {
        songs: ret.songs,
        playlists: ret.playlists,
        artists: ret.artists,
        albums: ret.albums,
    }))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_recommendations_wrapper() -> FnResult<Json<RecommendationsReturnType>> {
    let ret = get_recommendations()?;
    Ok(Json(RecommendationsReturnType { songs: ret }))
}

#[tracing::instrument(level = "debug", skip(url))]
#[plugin_fn]
pub fn get_song_from_url_wrapper(Json(url): Json<String>) -> FnResult<Json<SongReturnType>> {
    let ret = get_song_from_url(url)?;
    Ok(Json(SongReturnType { song: ret }))
}

#[tracing::instrument(level = "debug", skip(url))]
#[plugin_fn]
pub fn handle_custom_request_wrapper(
    Json(url): Json<String>,
) -> FnResult<Json<CustomRequestReturnType>> {
    let ret = handle_custom_request(url)?;
    Ok(Json(ret))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_artist_songs_wrapper(
    Json((artist, token)): Json<(QueryableArtist, Option<String>)>,
) -> FnResult<Json<SongsWithPageTokenReturnType>> {
    let ret = get_artist_songs(artist, token)?;
    Ok(Json(SongsWithPageTokenReturnType {
        songs: ret,
        next_page_token: None,
    }))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_album_songs_wrapper(
    Json((album, token)): Json<(QueryableAlbum, Option<String>)>,
) -> FnResult<Json<SongsWithPageTokenReturnType>> {
    let ret = get_album_songs(album, token)?;
    Ok(Json(SongsWithPageTokenReturnType {
        songs: ret,
        next_page_token: None,
    }))
}

#[tracing::instrument(level = "debug", skip(id))]
#[plugin_fn]
pub fn get_song_from_id_wrapper(Json(id): Json<String>) -> FnResult<Json<SongReturnType>> {
    let ret = get_song_from_id(id)?;
    Ok(Json(SongReturnType { song: ret }))
}

// PlayerEvents trait wrappers
#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_queue_changed_wrapper(Json(queue): Json<Value>) -> FnResult<Json<()>> {
    on_queue_changed(queue)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_volume_changed_wrapper() -> FnResult<Json<()>> {
    on_volume_changed()?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_player_state_changed_wrapper() -> FnResult<Json<()>> {
    on_player_state_changed()?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_song_changed_wrapper() -> FnResult<Json<()>> {
    on_song_changed()?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip(time))]
#[plugin_fn]
pub fn on_seeked_wrapper(Json(time): Json<f64>) -> FnResult<Json<()>> {
    on_seeked(time)?;
    Ok(Json(()))
}

// PreferenceEvents trait wrapper
#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_preferences_changed_wrapper(Json(args): Json<PreferenceArgs>) -> FnResult<Json<()>> {
    on_preferences_changed(args)?;
    Ok(Json(()))
}

// DatabaseEvents trait wrappers
#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_song_added_wrapper(Json(song): Json<Song>) -> FnResult<Json<()>> {
    on_song_added(song)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_song_removed_wrapper(Json(song): Json<Song>) -> FnResult<Json<()>> {
    on_song_removed(song)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_playlist_added_wrapper(Json(playlist): Json<QueryablePlaylist>) -> FnResult<Json<()>> {
    on_playlist_added(playlist)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_playlist_removed_wrapper(Json(playlist): Json<QueryablePlaylist>) -> FnResult<Json<()>> {
    on_playlist_removed(playlist)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_accounts_wrapper() -> FnResult<Json<Vec<ExtensionAccountDetail>>> {
    let ret = get_accounts()?;
    Ok(Json(ret))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn perform_account_login_wrapper(Json(args): Json<AccountLoginArgs>) -> FnResult<Json<String>> {
    let ret = perform_account_login(args)?;
    Ok(Json(ret))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn scrobble_wrapper(Json(args): Json<Song>) -> FnResult<Json<()>> {
    scrobble(args)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn oauth_callback_wrapper(Json(args): Json<String>) -> FnResult<Json<()>> {
    oauth_callback(args)?;
    Ok(Json(()))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_song_context_menu_wrapper(
    Json(songs): Json<Vec<Song>>,
) -> FnResult<Json<Vec<ContextMenuReturnType>>> {
    Ok(Json(get_song_context_menu(songs)?))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_playlist_context_menu_wrapper(
    Json(playlist): Json<QueryablePlaylist>,
) -> FnResult<Json<Vec<ContextMenuReturnType>>> {
    Ok(Json(get_playlist_context_menu(playlist)?))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn on_context_menu_action_wrapper(Json(action): Json<String>) -> FnResult<Json<()>> {
    Ok(Json(on_context_menu_action(action)?))
}

#[tracing::instrument(level = "debug", skip())]
#[plugin_fn]
pub fn get_lyrics_wrapper(Json(song): Json<Song>) -> FnResult<Json<String>> {
    Ok(Json(get_lyrics(song)?))
}
