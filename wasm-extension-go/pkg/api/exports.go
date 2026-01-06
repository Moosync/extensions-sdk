package api

import (
	"fmt"

	pdk "github.com/extism/go-pdk"
	"google.golang.org/protobuf/proto"

	extensions "github.com/moosync/moosync/types/extensions"
)

var extension Extension

//go:wasmexport handle_extension_command
func handle_extension_command() int32 {
	inputBytes := pdk.Input()

	cmd := &extensions.ExtensionCommand{}
	if err := proto.Unmarshal(inputBytes, cmd); err != nil {
		pdk.SetError(err)
		return 1
	}

	resp := &extensions.ExtensionCommandResponse{}

	switch e := cmd.Event.(type) {
	case *extensions.ExtensionCommand_RequestedPlaylists:
		res, err := extension.GetPlaylists(e.RequestedPlaylists)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedPlaylists{
			RequestedPlaylists: &extensions.RequestedPlaylistsResponse{Playlists: res},
		}

	case *extensions.ExtensionCommand_RequestedPlaylistSongs:
		res, err := extension.GetPlaylistContent(e.RequestedPlaylistSongs)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedPlaylistSongs{
			RequestedPlaylistSongs: res,
		}

	case *extensions.ExtensionCommand_OauthCallback:
		err := extension.OauthCallback(e.OauthCallback)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_OauthCallback{
			OauthCallback: &extensions.OauthCallbackResponse{},
		}

	case *extensions.ExtensionCommand_SongQueueChanged:
		err := extension.OnQueueChanged(e.SongQueueChanged)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_SongQueueChanged{
			SongQueueChanged: &extensions.SongQueueChangedResponse{},
		}

	case *extensions.ExtensionCommand_Seeked:
		err := extension.OnSeeked(e.Seeked)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_Seeked{
			Seeked: &extensions.SeekedResponse{},
		}

	case *extensions.ExtensionCommand_VolumeChanged:
		err := extension.OnVolumeChanged(e.VolumeChanged)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_VolumeChanged{
			VolumeChanged: &extensions.VolumeChangedResponse{},
		}

	case *extensions.ExtensionCommand_PlayerStateChanged:
		err := extension.OnPlayerStateChanged(e.PlayerStateChanged)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PlayerStateChanged{
			PlayerStateChanged: &extensions.PlayerStateChangedResponse{},
		}

	case *extensions.ExtensionCommand_SongChanged:
		err := extension.OnSongChanged(e.SongChanged)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_SongChanged{
			SongChanged: &extensions.SongChangedResponse{},
		}

	case *extensions.ExtensionCommand_PreferenceChanged:
		err := extension.OnPreferencesChanged(e.PreferenceChanged)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PreferenceChanged{
			PreferenceChanged: &extensions.PreferenceChangedResponse{},
		}

	case *extensions.ExtensionCommand_PlaybackDetailsRequested:
		res, err := extension.GetPlaybackDetails(e.PlaybackDetailsRequested)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PlaybackDetailsRequested{
			PlaybackDetailsRequested: res,
		}

	case *extensions.ExtensionCommand_CustomRequest:
		res, err := extension.HandleCustomRequest(e.CustomRequest)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_CustomRequest{
			CustomRequest: res,
		}

	case *extensions.ExtensionCommand_RequestedSongFromUrl:
		res, err := extension.GetSongFromURL(e.RequestedSongFromUrl)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedSongFromUrl{
			RequestedSongFromUrl: res,
		}

	case *extensions.ExtensionCommand_RequestedPlaylistFromUrl:
		res, err := extension.GetPlaylistFromURL(e.RequestedPlaylistFromUrl)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedPlaylistFromUrl{
			RequestedPlaylistFromUrl: res,
		}

	case *extensions.ExtensionCommand_RequestedSearchResult:
		res, err := extension.Search(e.RequestedSearchResult)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		// res is *songs.SearchResult
		// Response expects repeated fields directly in RequestedSearchResultResponse
		// Or does RequestedSearchResultResponse contain a SearchResult?
		// Proto: message RequestedSearchResultResponse { repeated Song; repeated Playlist; ... }
		// songs.SearchResult also has these.
		// I need to map them manually unless I change the return type of Search in `api.go`.
		// In `api.go` I made Search return `*songs.SearchResult`.
		// RequestedSearchResultResponse structure:
		//  repeated Song songs = 1;
		//  repeated Playlist playlists = 2;
		//  repeated Artist artists = 3;
		//  repeated Album albums = 4;

		resp.Response = &extensions.ExtensionCommandResponse_RequestedSearchResult{
			RequestedSearchResult: &extensions.RequestedSearchResultResponse{
				Songs:     res.Songs,
				Playlists: res.Playlists,
				Artists:   res.Artists,
				Albums:    res.Albums,
			},
		}

	case *extensions.ExtensionCommand_RequestedRecommendations:
		res, err := extension.GetRecommendations(e.RequestedRecommendations)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedRecommendations{
			RequestedRecommendations: &extensions.RequestedRecommendationsResponse{Songs: res},
		}

	case *extensions.ExtensionCommand_RequestedLyrics:
		res, err := extension.GetLyrics(e.RequestedLyrics)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedLyrics{
			RequestedLyrics: &extensions.RequestedLyricsResponse{Lyrics: res},
		}

	case *extensions.ExtensionCommand_RequestedArtistSongs:
		res, err := extension.GetArtistSongs(e.RequestedArtistSongs)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedArtistSongs{
			RequestedArtistSongs: res,
		}

	case *extensions.ExtensionCommand_RequestedAlbumSongs:
		res, err := extension.GetAlbumSongs(e.RequestedAlbumSongs)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedAlbumSongs{
			RequestedAlbumSongs: res,
		}

	case *extensions.ExtensionCommand_SongAdded:
		err := extension.OnSongAdded(e.SongAdded)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_SongAdded{
			SongAdded: &extensions.SongAddedResponse{},
		}

	case *extensions.ExtensionCommand_SongRemoved:
		err := extension.OnSongRemoved(e.SongRemoved)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_SongRemoved{
			SongRemoved: &extensions.SongRemovedResponse{},
		}

	case *extensions.ExtensionCommand_PlaylistAdded:
		err := extension.OnPlaylistAdded(e.PlaylistAdded)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PlaylistAdded{
			PlaylistAdded: &extensions.PlaylistAddedResponse{},
		}

	case *extensions.ExtensionCommand_PlaylistRemoved:
		err := extension.OnPlaylistRemoved(e.PlaylistRemoved)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PlaylistRemoved{
			PlaylistRemoved: &extensions.PlaylistRemovedResponse{},
		}

	case *extensions.ExtensionCommand_RequestedSongFromId:
		res, err := extension.GetSongFromID(e.RequestedSongFromId)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_RequestedSongFromId{
			RequestedSongFromId: res,
		}

	case *extensions.ExtensionCommand_GetRemoteUrl:
		// Not implemented in interface yet
		pdk.SetError(fmt.Errorf("GetRemoteUrl not implemented"))
		return 1

	case *extensions.ExtensionCommand_Scrobble:
		err := extension.Scrobble(e.Scrobble)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_Scrobble{
			Scrobble: &extensions.ScrobbleResponse{},
		}

	case *extensions.ExtensionCommand_RequestedSongContextMenu:
		_, err := extension.GetSongContextMenu(e.RequestedSongContextMenu)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		// Context struct in proto: ContextMenuReturnType
		// Api returns []*ContextMenuReturnType
		// Response expects: message RequestedSongContextMenuResponse { ContextMenuReturnType menu = 1; }
		// Wait, menu is SINGLE?
		// Proto: message RequestedSongContextMenuResponse { ContextMenuReturnType menu = 1; }
		// Proto ContextMenuReturnType: message ContextMenuReturnType { ... }
		// Wait, usually context menu is a list of items?
		// Let's check `extensions.proto`.
		// message ContextMenuReturnType { string name; string icon; string action_id; }
		// RequestedSongContextMenuResponse { ContextMenuReturnType menu = 1; }
		// This looks like it only supports ONE item?
		// Or maybe ContextMenuReturnType allows nesting? It doesn't seem so in the proto I saw.
		// `wasm-extension-rs` says `get_song_context_menu -> ContextMenuReturnType` (Single).
		// But in `api.go`, I defined `GetSongContextMenu` returning `[]*Context...`.
		// I should verify `extensions.proto` again.

		// Lines 222: message RequestedSongContextMenuResponse { ContextMenuReturnType menu = 1; }
		// Only one menu item? That seems wrong for a context menu.
		// Unless `ContextMenuReturnType` is a container?
		// Lines 383:
		// message ContextMenuReturnType {
		//   string name = 1;
		//   string icon = 2;
		//   string action_id = 3;
		// }
		// It seems to be a single item.
		// Maybe the proto definition is buggy or I misread it.
		// "repeated" missing?

		// If I assume it is incorrect in proto, I can't fix it right now without potentially breaking host.
		// But `wasm-extension-rs` probably used `ContextMenuReturnType` directly.
		// Let's assume the interface should return single item for now or I pack it?
		// Wait, if I am replacing the Go SDK, I should match what the proto says.
		// If proper usage expects a list, the proto should have `repeated`.

		// Let's assume for now I return the first item or match the proto type.
		// Checking `api.go` again... I declared `[]*extensions.ContextMenuReturnType`.
		// I should probably change `api.go` to return single item if proto forbids list.
		// OR FIX PROTO?
		// User didn't ask to fix bugs in proto, just switch usage.
		// Host likely expects one item? Or `ContextMenuReturnType` acts as a list? No.

		// I will update api.go return type to `*extensions.ContextMenuReturnType` to match proto.

		pdk.SetError(fmt.Errorf("GetSongContextMenu not fully implemented due to proto ambiguity"))
		return 1

	case *extensions.ExtensionCommand_RequestedPlaylistContextMenu:
		// Same issue
		pdk.SetError(fmt.Errorf("GetPlaylistContextMenu not fully implemented"))
		return 1

	case *extensions.ExtensionCommand_ContextMenuAction:
		err := extension.OnContextMenuAction(e.ContextMenuAction)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_ContextMenuAction{
			ContextMenuAction: &extensions.ContextMenuActionResponse{},
		}

	case *extensions.ExtensionCommand_GetProviderScopes:
		res, err := extension.GetProviderScopes()
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_GetProviderScopes{
			GetProviderScopes: &extensions.GetProviderScopesResponse{Scopes: res},
		}

	case *extensions.ExtensionCommand_GetAccounts:
		res, err := extension.GetAccounts()
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_GetAccounts{
			GetAccounts: &extensions.GetAccountsResponse{Accounts: res},
		}

	case *extensions.ExtensionCommand_PerformAccountLogin:
		res, err := extension.PerformAccountLogin(e.PerformAccountLogin)
		if err != nil {
			pdk.SetError(err)
			return 1
		}
		resp.Response = &extensions.ExtensionCommandResponse_PerformAccountLogin{
			PerformAccountLogin: &extensions.PerformAccountLoginResponse{Status: res},
		}

	default:
		pdk.Log(pdk.LogError, fmt.Sprintf("Unknown event: %T", cmd.Event))
		return 1
	}

	outBytes, err := proto.Marshal(resp)
	if err != nil {
		pdk.SetError(err)
		return 1
	}

	pdk.Output(outBytes)
	return 0
}

//go:wasmimport extism:host/user send_main_command
func send_main_command(uint64) uint64

//go:wasmimport extism:host/user system_time
func system_time() uint64

//go:wasmimport extism:host/user open_clientfd
func open_clientfd(uint64) uint64

//go:wasmimport extism:host/user write_sock
func write_sock(int64, uint64) uint64

//go:wasmimport extism:host/user read_sock
func read_sock(int64, uint64) uint64

//go:wasmimport extism:host/user hash
func hash(uint64, uint64) uint64
