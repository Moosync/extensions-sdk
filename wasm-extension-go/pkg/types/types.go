package types

import (
	"encoding/json"
)

type Value any
type EntityInfo any

type AccountLoginArgs struct {
	PackageName string `json:"packageName"`
	AccountID   string `json:"accountId"`
	LoginStatus bool   `json:"loginStatus"`
}

type ExtensionDetail struct {
	PackageName string `json:"packageName"`
}

type ExtensionAccountDetail struct {
	ID          string  `json:"id"`
	PackageName string  `json:"packageName"`
	Name        string  `json:"name"`
	BgColor     string  `json:"bgColor"`
	Icon        string  `json:"icon"`
	LoggedIn    bool    `json:"loggedIn"`
	Username    *string `json:"username"`
}

type PreferenceArgs struct {
	Key   string `json:"key"`
	Value any    `json:"value"`
}

type PlaylistReturnType struct {
	Playlists []QueryablePlaylist `json:"playlists"`
}

type SongsReturnType struct {
	Songs []Song `json:"songs"`
}

type SongsWithPageTokenReturnType struct {
	Songs         []Song           `json:"songs"`
	NextPageToken *json.RawMessage `json:"nextPageToken,omitempty"`
}

type SearchReturnType struct {
	Songs     []Song              `json:"songs"`
	Playlists []QueryablePlaylist `json:"playlists"`
	Artists   []QueryableArtist   `json:"artists"`
	Albums    []QueryableAlbum    `json:"albums"`
}

type PlaybackDetailsReturnType struct {
	Duration uint32 `json:"duration"`
	URL      string `json:"url"`
}

type CustomRequestReturnType struct {
	MimeType    string `json:"mimeType,omitempty"`
	Data        []byte `json:"data,omitempty"`
	RedirectURL string `json:"redirectUrl,omitempty"`
}

type SongReturnType struct {
	Song *Song `json:"song"`
}

type PlaylistAndSongsReturnType struct {
	Playlist *QueryablePlaylist `json:"playlist"`
	Songs    []Song             `json:"songs"`
}

type RecommendationsReturnType struct {
	Songs []Song `json:"songs"`
}

type AddToPlaylistRequest struct {
	PlaylistID string `json:"playlistID"`
	Songs      []Song `json:"songs"`
}

type PreferenceData struct {
	Key          string `json:"key"`
	Value        any    `json:"value"`
	DefaultValue any    `json:"defaultValue"`
}

type SearchableSong struct {
	ID                string   `json:"_id,omitempty"`
	Path              string   `json:"path,omitempty"`
	Title             string   `json:"title,omitempty"`
	SampleRate        *float64 `json:"sample_rate,omitempty"`
	Hash              string   `json:"hash,omitempty"`
	Type              SongType `json:"type_,omitempty"`
	URL               string   `json:"url,omitempty"`
	PlaybackURL       string   `json:"playback_url,omitempty"`
	ProviderExtension string   `json:"provider_extension,omitempty"`
	ShowInLibrary     bool     `json:"show_in_library,omitempty"`
}

type PackageNameArgs struct {
	PackageName string `json:"packageName"`
}

type ContextMenuReturnType struct {
	Name     string `json:"name"`
	Icon     string `json:"icon"`
	ActionID string `json:"actionId"`
}

type ExtensionProviderScope string

const (
	ScopeSearch              ExtensionProviderScope = "search"
	ScopePlaylists           ExtensionProviderScope = "playlists"
	ScopePlaylistSongs       ExtensionProviderScope = "playlistSongs"
	ScopeArtistSongs         ExtensionProviderScope = "artistSongs"
	ScopeAlbumSongs          ExtensionProviderScope = "albumSongs"
	ScopeRecommendations     ExtensionProviderScope = "recommendations"
	ScopeScrobbles           ExtensionProviderScope = "scrobbles"
	ScopePlaylistFromUrl     ExtensionProviderScope = "playlistFromUrl"
	ScopeSongFromUrl         ExtensionProviderScope = "songFromUrl"
	ScopeSearchAlbum         ExtensionProviderScope = "searchAlbum"
	ScopeSearchArtist        ExtensionProviderScope = "searchArtist"
	ScopePlaybackDetails     ExtensionProviderScope = "playbackDetails"
	ScopeLyrics              ExtensionProviderScope = "lyrics"
	ScopeSongContextMenu     ExtensionProviderScope = "songContextMenu"
	ScopePlaylistContextMenu ExtensionProviderScope = "playlistContextMenu"
	ScopeAccounts            ExtensionProviderScope = "accounts"
)

type Song struct {
	QueryableSong
	Album   *QueryableAlbum   `json:"album"`
	Artists []QueryableArtist `json:"artists"`
	Genre   []QueryableGenre  `json:"genre"`
}

type QueryableSong struct {
	ID                string   `json:"_id"`
	Path              string   `json:"path,omitempty"`
	Size              *float64 `json:"size,omitempty"`
	Inode             string   `json:"inode,omitempty"`
	DeviceNo          string   `json:"deviceno,omitempty"`
	Title             string   `json:"title,omitempty"`
	Date              string   `json:"date,omitempty"`
	Year              string   `json:"year,omitempty"`
	Lyrics            string   `json:"lyrics,omitempty"`
	ReleaseType       string   `json:"releaseType,omitempty"`
	Bitrate           *float64 `json:"bitrate,omitempty"`
	Codec             string   `json:"codec,omitempty"`
	Container         string   `json:"container,omitempty"`
	Duration          *float64 `json:"duration,omitempty"`
	SampleRate        *float64 `json:"sampleRate,omitempty"`
	Hash              string   `json:"hash,omitempty"`
	Type              SongType `json:"type"`
	URL               string   `json:"url,omitempty"`
	SongCoverPathHigh string   `json:"song_coverPath_high,omitempty"`
	PlaybackURL       string   `json:"playbackUrl,omitempty"`
	SongCoverPathLow  string   `json:"song_coverPath_low,omitempty"`
	DateAdded         *int64   `json:"date_added,omitempty"`
	Icon              string   `json:"icon,omitempty"`
	TrackNo           *float64 `json:"track_no,omitempty"`
}

type GetSongOptions struct {
	Song      *SearchableSong    `json:"song"`
	Artist    *QueryableArtist   `json:"artist"`
	Album     *QueryableAlbum    `json:"album"`
	Genre     *QueryableGenre    `json:"genre"`
	Playlist  *QueryablePlaylist `json:"playlist"`
	Inclusive *bool              `json:"inclusive"`
}

type QueryablePlaylist struct {
	PlaylistID    string `json:"playlist_id,omitempty"`
	PlaylistName  string `json:"playlist_name,omitempty"`
	PlaylistCover string `json:"playlist_coverpath,omitempty"`
}

type QueryableAlbum struct {
	AlbumID            string   `json:"album_id"`
	AlbumName          string   `json:"album_name,omitempty"`
	AlbumArtist        string   `json:"album_artist,omitempty"`
	AlbumCoverPathHigh string   `json:"albumCoverPath_high,omitempty"`
	AlbumSongCount     *float64 `json:"album_song_count,omitempty"`
	Year               string   `json:"year,omitempty"`
	AlbumCoverPathLow  string   `json:"albumCoverPath_low,omitempty"`
	AlbumExtraInfo     any      `json:"album_extra_info,omitempty"`
}

type QueryableArtist struct {
	ArtistID        string      `json:"artist_id"`
	ArtistMBID      string      `json:"artist_mbid,omitempty"`
	ArtistName      string      `json:"artist_name,omitempty"`
	ArtistCoverPath string      `json:"artist_coverPath,omitempty"`
	ArtistSongCount *float64    `json:"artist_song_count,omitempty"`
	ArtistExtraInfo *EntityInfo `json:"artist_extra_info,omitempty"`
}

type QueryableGenre struct {
	GenreID        string   `json:"genre_id"`
	GenreName      string   `json:"genre_name,omitempty"`
	GenreSongCount *float64 `json:"genre_song_count,omitempty"`
}

type SearchResult struct {
	Songs     []Song              `json:"songs"`
	Artists   []QueryableArtist   `json:"artists"`
	Playlists []QueryablePlaylist `json:"playlists"`
	Albums    []QueryableAlbum    `json:"albums"`
	Genres    []QueryableGenre    `json:"genres"`
}

type SongType string

const (
	SongTypeLocal   SongType = "LOCAL"
	SongTypeURL     SongType = "URL"
	SongTypeSpotify SongType = "SPOTIFY"
	SongTypeDASH    SongType = "DASH"
	SongTypeHLS     SongType = "HLS"
)

// PlayerState represents the state of the player.
type PlayerState string

const (
	PlayerStatePlaying PlayerState = "PLAYING"
	PlayerStatePaused  PlayerState = "PAUSED"
	PlayerStateStopped PlayerState = "STOPPED"
	PlayerStateLoading PlayerState = "LOADING"
)

type PreferenceTypes string

const (
	DirectoryGroup PreferenceTypes = "DirectoryGroup"
	EditText       PreferenceTypes = "EditText"
	FilePicker     PreferenceTypes = "FilePicker"
	CheckboxGroup  PreferenceTypes = "CheckboxGroup"
	ThemeSelector  PreferenceTypes = "ThemeSelector"
	Extensions     PreferenceTypes = "Extensions"
	ButtonGroup    PreferenceTypes = "ButtonGroup"
	ProgressBar    PreferenceTypes = "ProgressBar"
	TextField      PreferenceTypes = "TextField"
	InfoField      PreferenceTypes = "InfoField"
	Dropdown       PreferenceTypes = "Dropdown"
)

type InputType string

const (
	Text   InputType = "text"
	Number InputType = "number"
)

type CheckboxItems struct {
	Title string `json:"title"`
	Key   string `json:"key"`
}

type PreferenceUIData struct {
	Type        PreferenceTypes  `json:"type"`
	Title       string           `json:"title"`
	Key         string           `json:"key"`
	Description string           `json:"description"`
	InputType   *InputType       `json:"inputType,omitempty"`
	Single      *bool            `json:"single,omitempty"`
	Items       *[]CheckboxItems `json:"items,omitempty"`
	Default     any              `json:"default,omitempty"`
	Mobile      *bool            `json:"mobile,omitempty"`
}
