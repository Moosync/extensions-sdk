package api

import (
	"encoding/binary"
	"errors"
	"fmt"
	"net/http"

	pdk "github.com/extism/go-pdk"
	pdkhttp "github.com/extism/go-pdk/http"
	"google.golang.org/protobuf/proto"

	extensions "github.com/moosync/moosync/types/extensions"
	songs "github.com/moosync/moosync/types/songs"
	ui "github.com/moosync/moosync/types/ui"
)

type Extension interface {
	GetAccounts() ([]*extensions.ExtensionAccountDetail, error)
	PerformAccountLogin(req *extensions.PerformAccountLoginRequest) (string, error)
	OauthCallback(req *extensions.OauthCallbackRequest) error
	OnSongAdded(req *extensions.SongAddedRequest) error
	OnSongRemoved(req *extensions.SongRemovedRequest) error
	OnPlaylistAdded(req *extensions.PlaylistAddedRequest) error
	OnPlaylistRemoved(req *extensions.PlaylistRemovedRequest) error
	OnPreferencesChanged(req *extensions.PreferenceChangedRequest) error
	OnQueueChanged(req *extensions.SongQueueChangedRequest) error
	OnVolumeChanged(req *extensions.VolumeChangedRequest) error
	OnPlayerStateChanged(req *extensions.PlayerStateChangedRequest) error
	OnSongChanged(req *extensions.SongChangedRequest) error
	OnSeeked(req *extensions.SeekedRequest) error
	GetProviderScopes() ([]extensions.ExtensionProviderScope, error)
	GetPlaylists(req *extensions.RequestedPlaylistsRequest) ([]*songs.Playlist, error)
	GetPlaylistContent(req *extensions.RequestedPlaylistSongsRequest) (*extensions.RequestedPlaylistSongsResponse, error)
	GetPlaylistFromURL(req *extensions.RequestedPlaylistFromUrlRequest) (*extensions.RequestedPlaylistFromUrlResponse, error)
	GetPlaybackDetails(req *extensions.PlaybackDetailsRequestedRequest) (*extensions.PlaybackDetailsRequestedResponse, error)
	Search(req *extensions.RequestedSearchResultRequest) (*songs.SearchResult, error)
	GetRecommendations(req *extensions.RequestedRecommendationsRequest) ([]*songs.Song, error)
	GetSongFromURL(req *extensions.RequestedSongFromUrlRequest) (*extensions.RequestedSongFromUrlResponse, error)
	HandleCustomRequest(req *extensions.CustomRequest) (*extensions.CustomRequestResponse, error)
	GetArtistSongs(req *extensions.RequestedArtistSongsRequest) (*extensions.RequestedArtistSongsResponse, error)
	GetAlbumSongs(req *extensions.RequestedAlbumSongsRequest) (*extensions.RequestedAlbumSongsResponse, error)
	GetSongFromID(req *extensions.RequestedSongFromIdRequest) (*extensions.RequestedSongFromIdResponse, error)
	Scrobble(req *extensions.ScrobbleRequest) error
	GetLyrics(req *extensions.RequestedLyricsRequest) (string, error)
	GetSongContextMenu(req *extensions.RequestedSongContextMenuRequest) ([]*extensions.ContextMenuReturnType, error)
	GetPlaylistContextMenu(req *extensions.RequestedPlaylistContextMenuRequest) ([]*extensions.ContextMenuReturnType, error)
	OnContextMenuAction(req *extensions.ContextMenuActionRequest) error
}

type DefaultExtension struct{}

func (DefaultExtension) GetAccounts() ([]*extensions.ExtensionAccountDetail, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) PerformAccountLogin(req *extensions.PerformAccountLoginRequest) (string, error) {
	return "", errors.New("Not implemented")
}

func (DefaultExtension) OauthCallback(req *extensions.OauthCallbackRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongAdded(req *extensions.SongAddedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongRemoved(req *extensions.SongRemovedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlaylistAdded(req *extensions.PlaylistAddedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlaylistRemoved(req *extensions.PlaylistRemovedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPreferencesChanged(req *extensions.PreferenceChangedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnQueueChanged(req *extensions.SongQueueChangedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnVolumeChanged(req *extensions.VolumeChangedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlayerStateChanged(req *extensions.PlayerStateChangedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongChanged(req *extensions.SongChangedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSeeked(req *extensions.SeekedRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) GetProviderScopes() ([]extensions.ExtensionProviderScope, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylists(req *extensions.RequestedPlaylistsRequest) ([]*songs.Playlist, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistContent(req *extensions.RequestedPlaylistSongsRequest) (*extensions.RequestedPlaylistSongsResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistFromURL(req *extensions.RequestedPlaylistFromUrlRequest) (*extensions.RequestedPlaylistFromUrlResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaybackDetails(req *extensions.PlaybackDetailsRequestedRequest) (*extensions.PlaybackDetailsRequestedResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) Search(req *extensions.RequestedSearchResultRequest) (*songs.SearchResult, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetRecommendations(req *extensions.RequestedRecommendationsRequest) ([]*songs.Song, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetSongFromURL(req *extensions.RequestedSongFromUrlRequest) (*extensions.RequestedSongFromUrlResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) HandleCustomRequest(req *extensions.CustomRequest) (*extensions.CustomRequestResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetArtistSongs(req *extensions.RequestedArtistSongsRequest) (*extensions.RequestedArtistSongsResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetAlbumSongs(req *extensions.RequestedAlbumSongsRequest) (*extensions.RequestedAlbumSongsResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetSongFromID(req *extensions.RequestedSongFromIdRequest) (*extensions.RequestedSongFromIdResponse, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) Scrobble(req *extensions.ScrobbleRequest) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) GetLyrics(req *extensions.RequestedLyricsRequest) (string, error) {
	return "", errors.New("Not implemented")
}

func (DefaultExtension) GetSongContextMenu(req *extensions.RequestedSongContextMenuRequest) ([]*extensions.ContextMenuReturnType, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistContextMenu(req *extensions.RequestedPlaylistContextMenuRequest) ([]*extensions.ContextMenuReturnType, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) OnContextMenuAction(req *extensions.ContextMenuActionRequest) error {
	return errors.New("Not implemented")
}

func RegisterExtension(newExtension Extension) {
	if extension != nil {
		pdk.Log(pdk.LogError, "Extension cannot be re-registered")
		panic("Extension cannot be re-registered")
	}
	extension = newExtension
}

func sendMainCommand(cmd *extensions.MainCommand) (*extensions.MainCommandResponse, error) {
	inBytes, err := proto.Marshal(cmd)
	if err != nil {
		return nil, err
	}

	mem := pdk.AllocateBytes(inBytes)
	defer mem.Free()

	rPtr := send_main_command(mem.Offset())
	rMem := pdk.FindMemory(rPtr)
	respBytes := rMem.ReadBytes()

	resp := &extensions.MainCommandResponse{}
	err = proto.Unmarshal(respBytes, resp)
	if err != nil {
		return nil, err
	}

	if errProto := resp.GetError(); errProto != nil {
		return nil, errors.New(errProto.Message)
	}

	return resp, nil
}

// Helper functions for Main Commands

func GetSong(options *songs.GetSongOptions) ([]*songs.Song, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetSong{
			GetSong: &extensions.GetSongRequest{Options: options},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return nil, err
	}
	return resp.GetGetSong().GetSongs(), nil
}

func GetCurrentSong() (*songs.Song, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetCurrentSong{
			GetCurrentSong: &extensions.GetCurrentSongRequest{},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return nil, err
	}
	return resp.GetGetCurrentSong().GetSong(), nil
}

func GetPlayerState() (extensions.PlayerState, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetPlayerState{
			GetPlayerState: &extensions.GetPlayerStateRequest{},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return extensions.PlayerState_STOPPED, err
	}
	return resp.GetGetPlayerState().GetState(), nil
}

func GetVolume() (float64, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetVolume{
			GetVolume: &extensions.GetVolumeRequest{},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return 0, err
	}
	return resp.GetGetVolume().GetVolume(), nil
}

func GetTime() (float64, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetTime{
			GetTime: &extensions.GetTimeRequest{},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return 0, err
	}
	return resp.GetGetTime().GetTime(), nil
}

func GetQueue() (any, error) {
	// TODO: Queue is a google.protobuf.Struct. Need to convert or return Struct?
	// User expects generic any or struct?
	// Let's return *structpb.Struct for now.
	// The previous code returned 'any'.

	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetQueue{
			GetQueue: &extensions.GetQueueRequest{},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return nil, err
	}
	return resp.GetGetQueue().GetQueue(), nil
}

func GetPreference(data *extensions.PreferenceData) (*extensions.PreferenceData, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetPreference{
			GetPreference: &extensions.GetPreferenceRequest{Data: data},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return nil, err
	}
	return resp.GetGetPreference().GetData(), nil
}

func GetSecure(data *extensions.PreferenceData) (*extensions.PreferenceData, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_GetSecure{
			GetSecure: &extensions.GetSecureRequest{Data: data},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return nil, err
	}
	return resp.GetGetSecure().GetData(), nil
}

func SetPreference(data *extensions.PreferenceData) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_SetPreference{
			SetPreference: &extensions.SetPreferenceRequest{Data: data},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func SetSecure(data *extensions.PreferenceData) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_SetSecure{
			SetSecure: &extensions.SetSecureRequest{Data: data},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func AddSongs(s []*songs.Song) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_AddSongs{
			AddSongs: &extensions.AddSongsRequest{Songs: s},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func RemoveSong(s *songs.Song) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_RemoveSong{
			RemoveSong: &extensions.RemoveSongRequest{Song: s},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func UpdateSong(s *songs.Song) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_UpdateSong{
			UpdateSong: &extensions.UpdateSongRequest{Song: s},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func AddPlaylist(playlist *songs.Playlist) (string, error) {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_AddPlaylist{
			AddPlaylist: &extensions.AddPlaylistRequest{Playlist: playlist},
		},
	}
	resp, err := sendMainCommand(cmd)
	if err != nil {
		return "", err
	}
	return resp.GetAddPlaylist().GetPlaylistId(), nil
}

func AddToPlaylist(req *extensions.AddToPlaylistRequest) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_AddToPlaylist{
			AddToPlaylist: req,
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func RegisterOAuth(url string) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_RegisterOauth{
			RegisterOauth: &extensions.RegisterOauthRequest{Url: url},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func OpenExternalUrl(url string) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_OpenExternalUrl{
			OpenExternalUrl: &extensions.OpenExternalUrlRequest{Url: url},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func RegisterUserPreference(prefs []*ui.PreferenceUiData) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_RegisterUserPreference{
			RegisterUserPreference: &extensions.RegisterUserPreferenceRequest{Prefs: prefs},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func UnregisterUserPreference(keys []string) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_UnregisterUserPreference{
			UnregisterUserPreference: &extensions.UnregisterUserPreferenceRequest{Keys: keys},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func UpdateAccounts(account *string) error {
	cmd := &extensions.MainCommand{
		Command: &extensions.MainCommand_UpdateAccounts{
			UpdateAccounts: &extensions.UpdateAccountsRequest{Account: account},
		},
	}
	_, err := sendMainCommand(cmd)
	return err
}

func SystemTime() uint64 {
	rPtr := system_time()
	rMem := pdk.FindMemory(rPtr)
	return binary.LittleEndian.Uint64(rMem.ReadBytes())
}

func OpenSock(path string) int64 {
	mem := pdk.AllocateString(path)
	rPtr := open_clientfd(mem.Offset())
	rMem := pdk.FindMemory(rPtr)
	return int64(binary.LittleEndian.Uint64(rMem.ReadBytes()))
}

func WriteSock(sockId int64, buf []byte) int64 {
	mem := pdk.AllocateBytes(buf)
	rPtr := write_sock(sockId, mem.Offset())
	rMem := pdk.FindMemory(rPtr)
	return int64(binary.LittleEndian.Uint64(rMem.ReadBytes()))
}

func ReadSock(sockId int64, readLen uint64) []byte {
	rPtr := read_sock(sockId, readLen)
	rMem := pdk.FindMemory(rPtr)
	return rMem.ReadBytes()
}

type HashType string

const (
	HashSHA1   HashType = "SHA1"
	HashSHA256 HashType = "SHA256"
	HashSHA512 HashType = "SHA512"
)

func Hash(hashType HashType, data []byte) []byte {
	memType := pdk.AllocateString(string(hashType))
	memData := pdk.AllocateBytes(data)
	rPtr := hash(memType.Offset(), memData.Offset())
	rMem := pdk.FindMemory(rPtr)
	return rMem.ReadBytes()
}

func LogTrace(format string, args ...any) {
	pdk.Log(pdk.LogTrace, fmt.Sprintf(format, args...))
}

func LogDebug(format string, args ...any) {
	pdk.Log(pdk.LogDebug, fmt.Sprintf(format, args...))
}

func LogInfo(format string, args ...any) {
	pdk.Log(pdk.LogInfo, fmt.Sprintf(format, args...))
}

func LogWarn(format string, args ...any) {
	pdk.Log(pdk.LogWarn, fmt.Sprintf(format, args...))
}

func LogError(format string, args ...any) {
	pdk.Log(pdk.LogError, fmt.Sprintf(format, args...))
}

func EnableHttp() {
	http.DefaultTransport = &pdkhttp.HTTPTransport{}
}

func init() {
	// Force export of handle_extension_command to prevent dead code elimination
	_ = handle_extension_command
}
