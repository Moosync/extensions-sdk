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

use crate::api::Extension;
use extensions_proto::moosync::types::extension_command::Event;
use extensions_proto::moosync::types::extension_command_response::Response;
use extensions_proto::moosync::types::*;
use extism_pdk::FnResult;
use std::{cell::RefCell, rc::Rc};

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

#[derive(Debug)]
pub enum MoosyncError {
    String(String),
}

impl From<String> for MoosyncError {
    fn from(e: String) -> Self {
        MoosyncError::String(e)
    }
}
impl From<&str> for MoosyncError {
    fn from(s: &str) -> Self {
        MoosyncError::String(s.to_string())
    }
}

// Using a macro for dispatch significantly simplifies the repetitive match arms.
macro_rules! dispatch_command {
    ($ext:expr, $event:expr, {
        $($Variant:ident $(($($arg:pat),*))? => $method:ident $(($($param:expr),*))? => $res:ident in $RespVariant:ident $Body:tt),* $(,)?
    }) => {
        match $event {
            $(
                Event::$Variant($($($arg),*)?) => {
                     let $res = $ext.$method($($($param),*)?)
                        .map_err(|e| extism_pdk::Error::msg(format!("Error: {:?}", e)))?;

                    Response::$Variant($RespVariant $Body)
                }
            )*
             Event::GetRemoteUrl(_) => {
                 return Err(extism_pdk::Error::msg("Not implemented"));
             }
        }
    };
}

pub fn handle_command(
    cmd: ExtensionCommand,
) -> Result<ExtensionCommandResponse, extism_pdk::Error> {
    EXTENSION.with(|ext| {
        if let Some(ext) = ext.borrow().as_ref() {
            let mut response = ExtensionCommandResponse { response: None };

            if let Some(event) = cmd.event {
                let resp = dispatch_command!(ext, event, {
                    RequestedPlaylists(req) => get_playlists(req) => res in RequestedPlaylistsResponse { playlists: res },
                    RequestedPlaylistSongs(req) => get_playlist_content(req) => res in RequestedPlaylistSongsResponse {
                        songs: res.songs,
                        next_page_token: res.next_page_token,
                    },
                    OauthCallback(req) => oauth_callback(req) => _res in OauthCallbackResponse {},
                    SongQueueChanged(req) => on_queue_changed(req) => _res in SongQueueChangedResponse {},
                    Seeked(req) => on_seeked(req) => _res in SeekedResponse {},
                    VolumeChanged(req) => on_volume_changed(req) => _res in VolumeChangedResponse {},
                    PlayerStateChanged(req) => on_player_state_changed(req) => _res in PlayerStateChangedResponse {},
                    SongChanged(req) => on_song_changed(req) => _res in SongChangedResponse {},
                    PreferenceChanged(req) => on_preferences_changed(req) => _res in PreferenceChangedResponse {},
                    PlaybackDetailsRequested(req) => get_playback_details(req) => res in PlaybackDetailsRequestedResponse {
                        duration: res.duration,
                        url: res.url,
                    },
                    CustomRequest(req) => handle_custom_request(req) => res in CustomRequestResponse {
                         mime_type: res.mime_type,
                         data: res.data,
                         redirect_url: res.redirect_url,
                    },
                    RequestedSongFromUrl(req) => get_song_from_url(req) => res in RequestedSongFromUrlResponse { song: res },
                    RequestedPlaylistFromUrl(req) => get_playlist_from_url(req) => res in RequestedPlaylistFromUrlResponse {
                         playlist: res,
                         songs: vec![],
                    },
                    RequestedSearchResult(req) => search(req) => res in RequestedSearchResultResponse {
                         songs: res.songs,
                         playlists: res.playlists,
                         artists: res.artists,
                         albums: res.albums,
                    },
                    RequestedRecommendations(req) => get_recommendations(req) => res in RequestedRecommendationsResponse { songs: res },
                    RequestedLyrics(req) => get_lyrics(req) => res in RequestedLyricsResponse { lyrics: res },
                    RequestedArtistSongs(req) => get_artist_songs(req) => res in RequestedArtistSongsResponse {
                         songs: res.songs,
                         next_page_token: res.next_page_token,
                    },
                    RequestedAlbumSongs(req) => get_album_songs(req) => res in RequestedAlbumSongsResponse {
                         songs: res.songs,
                         next_page_token: res.next_page_token,
                    },
                    SongAdded(req) => on_song_added(req) => _res in SongAddedResponse {},
                    SongRemoved(req) => on_song_removed(req) => _res in SongRemovedResponse {},
                    PlaylistAdded(req) => on_playlist_added(req) => _res in PlaylistAddedResponse {},
                    PlaylistRemoved(req) => on_playlist_removed(req) => _res in PlaylistRemovedResponse {},
                    RequestedSongFromId(req) => get_song_from_id(req) => res in RequestedSongFromIdResponse { song: res },
                    Scrobble(req) => scrobble(req) => _res in ScrobbleResponse {},
                    RequestedSongContextMenu(req) => get_song_context_menu(req) => res in RequestedSongContextMenuResponse {
                         menu: res.into_iter().next(),
                    },
                    RequestedPlaylistContextMenu(req) => get_playlist_context_menu(req) => res in RequestedPlaylistContextMenuResponse {
                         menu: res.into_iter().next(),
                    },
                    ContextMenuAction(req) => on_context_menu_action(req) => _res in ContextMenuActionResponse {},
                    GetProviderScopes(_) => get_provider_scopes() => res in GetProviderScopesResponse {
                         scopes: res.into_iter().map(|s| s as i32).collect(),
                    },
                    GetAccounts(_) => get_accounts() => res in GetAccountsResponse { accounts: res },
                    PerformAccountLogin(req) => perform_account_login(req) => res in PerformAccountLoginResponse { status: res },
                });

                response.response = Some(resp);
            }

            Ok(response)
        } else {
            Err(extism_pdk::Error::msg("No extension registered"))
        }
    })
}
