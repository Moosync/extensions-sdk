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

import { callListener } from "./api";

export namespace Exports {
  async function handleWrapper(event: string) {
    const input = Host.inputString();
    let params = undefined;
    if (input) {
      params = JSON.parse(input);
    }

    try {
      let resp = await callListener(event, params);
      if (typeof resp !== "undefined" || resp !== null) {
        Host.outputString(JSON.stringify(resp));
      } else {
        Host.outputString(JSON.stringify(null));
      }
    } catch (err) {
      console.error("caught err", err);
      Host.outputString(JSON.stringify(null));
      return;
    }
  }

  export function get_provider_scopes_wrapper() {
    handleWrapper("getProviderScopes");
  }
  export function get_playlists_wrapper() {
    handleWrapper("getPlaylists");
  }
  export function get_playlist_content_wrapper() {
    handleWrapper("getPlaylistContent");
  }
  export function get_playlist_from_url_wrapper() {
    handleWrapper("getPlaylistFromUrl");
  }
  export function get_playback_details_wrapper() {
    handleWrapper("getPlaybackDetails");
  }
  export function search_wrapper() {
    handleWrapper("search");
  }
  export function get_recommendations_wrapper() {
    handleWrapper("getRecommendations");
  }
  export function get_song_from_url_wrapper() {
    handleWrapper("getSongFromUrl");
  }
  export function handle_custom_request_wrapper() {
    handleWrapper("handleCustomRequest");
  }
  export function get_artist_songs_wrapper() {
    handleWrapper("getArtistSongs");
  }
  export function get_album_songs_wrapper() {
    handleWrapper("getAlbumSongs");
  }
  export function get_song_from_id_wrapper() {
    handleWrapper("getSongFromId");
  }
  export function on_queue_changed_wrapper() {
    handleWrapper("onQueueChanged");
  }
  export function on_volume_changed_wrapper() {
    handleWrapper("onVolumeChanged");
  }
  export function on_player_state_changed_wrapper() {
    handleWrapper("onPlayerStateChanged");
  }
  export function on_song_changed_wrapper() {
    handleWrapper("onSongChanged");
  }
  export function on_seeked_wrapper() {
    handleWrapper("onSeeked");
  }
  export function on_preferences_changed_wrapper() {
    handleWrapper("onPreferencesChanged");
  }
  export function on_song_added_wrapper() {
    handleWrapper("onSongAdded");
  }
  export function on_song_removed_wrapper() {
    handleWrapper("onSongRemoved");
  }
  export function on_playlist_added_wrapper() {
    handleWrapper("onPlaylistAdded");
  }
  export function on_playlist_removed_wrapper() {
    handleWrapper("onPlaylistRemoved");
  }
  export function get_accounts_wrapper() {
    handleWrapper("getAccounts");
  }
  export function perform_account_login_wrapper() {
    handleWrapper("performAccountLogin");
  }
  export function scrobble_wrapper() {
    handleWrapper("scrobble");
  }
  export function oauth_callback_wrapper() {
    handleWrapper("oauthCallback");
  }
  export function get_song_context_menu_wrapper() {
    handleWrapper("getSongContextMenu");
  }
  export function get_playlist_context_menu_wrapper() {
    handleWrapper("getPlaylistContextMenu");
  }
  export function on_context_menu_action_wrapper() {
    handleWrapper("onContextMenuAction");
  }
  export function get_lyrics_wrapper() {
    handleWrapper("getLyrics");
  }
}
