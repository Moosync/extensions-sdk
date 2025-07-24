package api

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"

	"github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/types"
	"github.com/extism/go-pdk"
	pdkhttp "github.com/extism/go-pdk/http"
)

type Extension interface {
	GetAccounts() ([]types.ExtensionAccountDetail, error)
	PerformAccountLogin(args types.AccountLoginArgs) (string, error)
	OauthCallback(code string) error
	OnSongAdded(song types.Song) error
	OnSongRemoved(song types.Song) error
	OnPlaylistAdded(playlist types.QueryablePlaylist) error
	OnPlaylistRemoved(playlist types.QueryablePlaylist) error
	OnPreferencesChanged(args types.PreferenceArgs) error
	OnQueueChanged(queue types.Value) error
	OnVolumeChanged() error
	OnPlayerStateChanged() error
	OnSongChanged() error
	OnSeeked(time float64) error
	GetProviderScopes() ([]types.ExtensionProviderScope, error)
	GetPlaylists() ([]types.QueryablePlaylist, error)
	GetPlaylistContent(id string, nextPageToken string) ([]types.Song, error)
	GetPlaylistFromURL(url string) (types.QueryablePlaylist, error)
	GetPlaybackDetails(song types.Song) (types.PlaybackDetailsReturnType, error)
	Search(term string) (types.SearchResult, error)
	GetRecommendations() ([]types.Song, error)
	GetSongFromURL(url string) (types.Song, error)
	HandleCustomRequest(url string) (types.CustomRequestReturnType, error)
	GetArtistSongs(artist types.QueryableArtist, nextPageToken string) ([]types.Song, error)
	GetAlbumSongs(album types.QueryableAlbum, nextPageToken string) ([]types.Song, error)
	GetSongFromID(id string) (types.Song, error)
	Scrobble(song types.Song) error
	GetLyrics(song types.Song) (string, error)
	GetSongContextMenu(songs []types.Song) ([]types.ContextMenuReturnType, error)
	GetPlaylistContextMenu(playlist types.QueryablePlaylist) ([]types.ContextMenuReturnType, error)
	OnContextMenuAction(action string) error
}

type DefaultExtension struct{}

func (DefaultExtension) GetAccounts() ([]types.ExtensionAccountDetail, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) PerformAccountLogin(args types.AccountLoginArgs) (string, error) {
	return "", errors.New("Not implemented")
}

func (DefaultExtension) OauthCallback(code string) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongAdded(song types.Song) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongRemoved(song types.Song) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlaylistAdded(playlist types.QueryablePlaylist) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlaylistRemoved(playlist types.QueryablePlaylist) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPreferencesChanged(args types.PreferenceArgs) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnQueueChanged(queue types.Value) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnVolumeChanged() error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnPlayerStateChanged() error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSongChanged() error {
	return errors.New("Not implemented")
}

func (DefaultExtension) OnSeeked(time float64) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) GetProviderScopes() ([]types.ExtensionProviderScope, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylists() ([]types.QueryablePlaylist, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistContent(id string, nextPageToken string) ([]types.Song, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistFromURL(url string) (types.QueryablePlaylist, error) {
	var qp types.QueryablePlaylist
	return qp, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaybackDetails(song types.Song) (types.PlaybackDetailsReturnType, error) {
	var pd types.PlaybackDetailsReturnType
	return pd, errors.New("Not implemented")
}

func (DefaultExtension) Search(term string) (types.SearchResult, error) {
	var sr types.SearchResult
	return sr, errors.New("Not implemented")
}

func (DefaultExtension) GetRecommendations() ([]types.Song, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetSongFromURL(url string) (types.Song, error) {
	var s types.Song
	return s, errors.New("Not implemented")
}

func (DefaultExtension) HandleCustomRequest(url string) (types.CustomRequestReturnType, error) {
	var crt types.CustomRequestReturnType
	return crt, errors.New("Not implemented")
}

func (DefaultExtension) GetArtistSongs(artist types.QueryableArtist, nextPageToken string) ([]types.Song, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetAlbumSongs(album types.QueryableAlbum, nextPageToken string) ([]types.Song, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetSongFromID(id string) (types.Song, error) {
	var s types.Song
	return s, errors.New("Not implemented")
}

func (DefaultExtension) Scrobble(song types.Song) error {
	return errors.New("Not implemented")
}

func (DefaultExtension) GetLyrics(song types.Song) (string, error) {
	return "", errors.New("Not implemented")
}

func (DefaultExtension) GetSongContextMenu(songs []types.Song) ([]types.ContextMenuReturnType, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) GetPlaylistContextMenu(playlist types.QueryablePlaylist) ([]types.ContextMenuReturnType, error) {
	return nil, errors.New("Not implemented")
}

func (DefaultExtension) OnContextMenuAction(action string) error {
	return errors.New("Not implemented")
}

func RegisterExtension(newExtension Extension) {
	if extension != nil {
		pdk.Log(pdk.LogError, "Extension cannot be re-registered")
		panic("Extension cannot be re-registered")
	}
	extension = newExtension
}

func sendMainCommand[T any](command string, args ...any) (t T, err error) {
	data := make(map[string]any)

	if len(args) == 1 {
		data[command] = args[0]
	} else if len(args) == 0 {
		data[command] = [...]any{}
	} else {
		data[command] = args
	}

	jsonString, err := json.Marshal(data)
	pdk.Log(pdk.LogInfo, string(jsonString))

	if err != nil {
		return
	}

	pdk.Log(pdk.LogInfo, "Got json "+string(jsonString))

	mem := pdk.AllocateBytes(jsonString)
	defer mem.Free()

	rPtr := send_main_command(mem.Offset())
	rMem := pdk.FindMemory(rPtr)
	resp := rMem.ReadBytes()

	err = json.Unmarshal(resp, &t)
	if err != nil {
		return
	}

	return
}

func sendMainCommandOptional(command string, args ...any) (err error) {
	data := make(map[string]any)
	if len(args) == 1 {
		data[command] = args[0]
	} else if len(args) == 0 {
		data[command] = [...]any{}
	} else {
		data[command] = args
	}

	jsonString, err := json.Marshal(data)
	if err != nil {
		return
	}
	mem := pdk.AllocateBytes(jsonString)
	defer mem.Free()

	send_main_command(mem.Offset())
	return
}

// GetSong returns a list of songs based on options.
func GetSong(options types.GetSongOptions) ([]types.Song, error) {
	resp, err := sendMainCommand[[]types.Song]("GetSong", options)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// GetCurrentSong returns the current playing song.
func GetCurrentSong() (*types.Song, error) {
	resp, err := sendMainCommand[*types.Song]("GetCurrentSong")
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// GetPlayerState returns the current player state.
func GetPlayerState() (types.PlayerState, error) {
	resp, err := sendMainCommand[types.PlayerState]("GetPlayerState")
	if err != nil {
		return types.PlayerStateStopped, err
	}
	return resp, nil
}

// GetVolume returns the current volume level.
func GetVolume() (float64, error) {
	resp, err := sendMainCommand[float64]("GetVolume")
	if err != nil {
		return 0, err
	}
	return resp, nil
}

// GetTime returns the current playback time.
func GetTime() (float64, error) {
	resp, err := sendMainCommand[float64]("GetTime")
	if err != nil {
		return 0, err
	}
	return resp, nil
}

// GetQueue returns the current queue of songs.
func GetQueue() (any, error) {
	resp, err := sendMainCommand[any]("GetQueue")
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// GetPreference retrieves a preference based on the provided data.
func GetPreference(data types.PreferenceData) (any, error) {
	// We assume sendMainCommand returns a JSON string.
	resp, err := sendMainCommand[string]("GetPreference", data)
	if err != nil {
		return nil, err
	}
	var result any
	if err := json.Unmarshal([]byte(resp), &result); err != nil {
		return nil, err
	}
	return result, nil
}

// GetSecure retrieves encrypted preference data.
func GetSecure(data types.PreferenceData) (any, error) {
	resp, err := sendMainCommand[string]("GetSecure", data)
	if err != nil {
		return nil, err
	}
	var result any
	if err := json.Unmarshal([]byte(resp), &result); err != nil {
		return nil, err
	}
	return result, nil
}

// SetPreference sets a preference using the provided data.
func SetPreference(data types.PreferenceData) error {
	err := sendMainCommandOptional("SetPreference", data)
	return err
}

// SetSecure sets encrypted preference data.
func SetSecure(data types.PreferenceData) error {
	err := sendMainCommandOptional("SetSecure", data)
	return err
}

// AddSongs adds a list of songs to the library.
func AddSongs(songs []types.Song) error {
	err := sendMainCommandOptional("AddSongs", songs)
	return err
}

// RemoveSong removes a song from the library.
func RemoveSong(song types.Song) error {
	err := sendMainCommandOptional("RemoveSong", song)
	return err
}

// UpdateSong updates a song in the library.
func UpdateSong(song types.Song) error {
	err := sendMainCommandOptional("UpdateSong", song)
	return err
}

// AddPlaylist adds a playlist to the library and returns its ID.
func AddPlaylist(playlist types.QueryablePlaylist) (string, error) {
	resp, err := sendMainCommand[string]("AddPlaylist", playlist)
	if err != nil {
		return "", err
	}
	return resp, nil
}

// AddToPlaylist adds songs to a playlist.
func AddToPlaylist(req types.AddToPlaylistRequest) error {
	err := sendMainCommandOptional("AddToPlaylist", req)
	return err
}

// RegisterOAuth registers an OAuth callback using the given token.
func RegisterOAuth(token string) error {
	err := sendMainCommandOptional("RegisterOAuth", token)
	return err
}

// OpenExternalUrl opens a URL in the default browser.
func OpenExternalUrl(url string) error {
	err := sendMainCommandOptional("OpenExternalUrl", url)
	return err
}

func RegisterUserPreference(prefs []types.PreferenceUIData) error {
	err := sendMainCommandOptional("RegisterUserPreference", prefs)
	return err
}

func UnregisterUserPreference(prefs []string) error {
	err := sendMainCommandOptional("UnregisterUserPreference", prefs)
	return err
}

// UpdateAccounts updates the accounts status.
func UpdateAccounts(packageName string) error {
	err := sendMainCommandOptional("UpdateAccounts", packageName)
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
