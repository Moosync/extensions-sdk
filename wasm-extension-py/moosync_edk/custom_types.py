from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Any, Literal
import inspect
from enum import Enum

ProviderScopes = Literal[
    "search",
    "playlists",
    "playlistSongs",
    "artistSongs",
    "albumSongs",
    "recommendations",
    "scrobbles",
    "playlistFromUrl",
    "songFromUrl",
    "searchAlbum",
    "searchArtist",
    "playbackDetails",
    "lyrics",
    "songContextMenu",
    "playlistContextMenu",
    "accounts"
]

@dataclass
class Album:
    album_id: Optional[str] = None  # The unique identifier for the album
    album_name: Optional[str] = None  # The name of the album
    album_coverPath_high: Optional[str] = None  # The high-resolution cover path for the album
    album_coverPath_low: Optional[str] = None  # The low-resolution cover path for the album
    album_song_count: Optional[int] = None  # The number of songs in the album
    album_artist: Optional[str] = None  # The artist of the album
    album_extra_info: Optional[str] = None  # Any extra information about the album
    year: Optional[int] = None  # The release year of the album

    @classmethod
    def from_dict(cls, data: dict) -> 'Album':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class ArtistExtraInfo:
    spotify: Optional[Dict[str, Optional[str]]] = field(default_factory=dict)  # Extra information from Spotify
    extensions: Optional[Dict[str, Dict[str, Optional[str]]]] = field(default_factory=dict)  # Additional extensions

    @classmethod
    def from_dict(cls, data: dict) -> 'ArtistExtraInfo':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class Artist:
    artist_id: str  # The unique identifier for the artist
    artist_name: Optional[str] = None  # The name of the artist
    artist_mbid: Optional[str] = None  # The MusicBrainz ID of the artist
    artist_coverPath: Optional[str] = None  # The cover path for the artist
    artist_song_count: Optional[int] = None  # The number of songs by the artist
    artist_extra_info: Optional[ArtistExtraInfo] = None  # Extra information about the artist

    @classmethod
    def from_dict(cls, data: dict) -> 'Artist':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class Genre:
    genre_id: str  # The unique identifier for the genre
    genre_name: str  # The name of the genre
    genre_song_count: int  # The number of songs in the genre

    @classmethod
    def from_dict(cls, data: dict) -> 'Genre':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class Playlist:
    playlist_id: str  # The unique identifier for the playlist
    playlist_name: str  # The name of the playlist
    playlist_desc: Optional[str] = None  # The description of the playlist
    playlist_coverPath: Optional[str] = None  # The cover path for the playlist
    playlist_song_count: Optional[int] = None  # The number of songs in the playlist
    playlist_path: Optional[str] = None  # The path to the playlist
    icon: Optional[str] = None  # The icon for the playlist
    extension: Optional[str] = None  # Any extension information for the playlist

    @classmethod
    def from_dict(cls, data: dict) -> 'Playlist':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

PlayerTypes = Literal["LOCAL", "SPOTIFY", "URL", "DASH", "HLS"]

@dataclass
class Song:
    _id: str  # The unique identifier for the song
    path: Optional[str] = None  # The file path of the song
    size: Optional[int] = None  # The size of the song file
    title: str = ""  # The title of the song
    song_coverPath_low: Optional[str] = None  # The low-resolution cover path for the song
    song_coverPath_high: Optional[str] = None  # The high-resolution cover path for the song
    album: Optional[Album] = None  # The album the song belongs to
    artists: List[Artist] = field(default_factory=list)  # The artists of the song
    date: Optional[str] = None  # The release date of the song
    year: Optional[Union[int, str]] = None  # The release year of the song
    genre: List[str] = field(default_factory=list)  # The genres of the song
    lyrics: Optional[str] = None  # The lyrics of the song
    releaseType: List[str] = field(default_factory=list)  # The release types of the song
    bitrate: Optional[int] = None  # The bitrate of the song
    codec: Optional[str] = None  # The codec used for the song
    container: Optional[str] = None  # The container format of the song
    duration: int = 0  # The duration of the song in seconds
    sampleRate: Optional[int] = None  # The sample rate of the song
    hash: Optional[str] = None  # The hash of the song file
    inode: Optional[str] = None  # The inode number of the song file
    deviceno: Optional[str] = None  # The device number of the song file
    url: Optional[str] = None  # The URL of the song
    playbackUrl: Optional[str] = None  # The playback URL of the song
    date_added: Optional[int] = None  # The date the song was added
    providerExtension: Optional[str] = None  # The provider extension for the song
    icon: Optional[str] = None  # The icon for the song
    type: PlayerTypes = "LOCAL"  # The type of player for the song
    playCount: Optional[int] = None  # The play count of the song
    showInLibrary: Optional[bool] = None  # Whether to show the song in the library
    track_no: Optional[int] = None  # The track number of the song

    @classmethod
    def from_dict(cls, data: dict) -> 'Song':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class SearchableSong:
    _id: Optional[str] = None  # The unique identifier for the searchable song
    path: Optional[str] = None  # The file path of the searchable song
    title: Optional[str] = None  # The title of the searchable song
    url: Optional[str] = None  # The URL of the searchable song
    playbackUrl: Optional[str] = None  # The playback URL of the searchable song
    hash: Optional[str] = None  # The hash of the searchable song file
    size: Optional[int] = None  # The size of the searchable song file
    inode: Optional[str] = None  # The inode number of the searchable song file
    deviceno: Optional[str] = None  # The device number of the searchable song file
    type: Optional[PlayerTypes] = None  # The type of player for the searchable song
    extension: Optional[Union[bool, str]] = None  # Any extension information for the searchable song
    showInLibrary: Optional[bool] = None  # Whether to show the searchable song in the library

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchableSong':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

PlayerState = Literal["PLAYING", "PAUSED", "STOPPED", "LOADING"]

@dataclass
class SongSortOptions:
    type: str  # The type of sorting, should be a key in Song
    asc: bool = True  # Whether the sorting is ascending

    @classmethod
    def from_dict(cls, data: dict) -> 'SongSortOptions':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class SongAPIOptions:
    song: Optional[SearchableSong] = None  # The searchable song options
    album: Optional[Album] = None  # The album options
    artist: Optional[Artist] = None  # The artist options
    genre: Optional[Genre] = None  # The genre options
    playlist: Optional[Playlist] = None  # The playlist options
    sortBy: Optional[Union[SongSortOptions, List[SongSortOptions]]] = None  # The sorting options
    inclusive: bool = False  # Whether the search is inclusive
    invert: bool = False  # Whether to invert the search results

    @classmethod
    def from_dict(cls, data: dict) -> 'SongAPIOptions':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class EntityApiOptions:
    inclusive: bool = False  # Whether the search is inclusive
    invert: bool = False  # Whether to invert the search results
    artist: Optional[Union[Artist, bool]] = None  # The artist options
    album: Optional[Union[Album, bool]] = None  # The album options
    genre: Optional[Union[Genre, bool]] = None  # The genre options
    playlist: Optional[Union[Playlist, bool]] = None  # The playlist options

    @classmethod
    def from_dict(cls, data: dict) -> 'EntityApiOptions':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class AccountDetails:
    id: str  # The unique identifier for the account
    packageName: str  # The package name of the account
    name: str  # The name of the account
    bgColor: str  # The background color of the account
    icon: str  # The icon of the account
    loggedIn: bool  # Whether the account is logged in
    username: Optional[str] = None  # The username of the account

    @classmethod
    def from_dict(cls, data: dict) -> 'AccountDetails':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class AccountLoginArgs:
    packageName: str  # The package name of the account
    accountId: str  # The unique identifier for the account
    loginStatus: bool  # The login status of the account

    @classmethod
    def from_dict(cls, data: dict) -> 'AccountLoginArgs':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class PreferenceArgs:
    key: str  # The key of the preference
    value: Any  # The value of the preference

    @classmethod
    def from_dict(cls, data: dict) -> 'PreferenceArgs':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class SearchReturnType:
    songs: List[Song]  # The list of songs returned by the search
    artists: List[Artist]  # The list of artists returned by the search
    playlists: List[Playlist]  # The list of playlists returned by the search
    albums: List[Album]  # The list of albums returned by the search
    genres: List[Genre]  # The list of genres returned by the search

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class RecommendationsReturnType:
    songs: List[Song]  # The list of recommended songs

    @classmethod
    def from_dict(cls, data: dict) -> 'RecommendationsReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class PlaylistsReturnType:
    playlists: List[Playlist]  # The list of playlists returned

    @classmethod
    def from_dict(cls, data: dict) -> 'PlaylistsReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class SongsWithPageTokenReturnType:
    songs: List[Song]  # The list of songs returned
    nextPageToken: Optional[Any] = None  # The token for the next page of results

    @classmethod
    def from_dict(cls, data: dict) -> 'SongsWithPageTokenReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class PlaybackDetailsReturnType:
    duration: int  # The duration of the playback in seconds
    url: str  # The URL for the playback

    @classmethod
    def from_dict(cls, data: dict) -> 'PlaybackDetailsReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class CustomRequestReturnType:
    mimeType: Optional[str] = None  # The MIME type of the custom request
    data: Optional[Any] = None  # The data of the custom request
    redirectUrl: Optional[str] = None  # The redirect URL of the custom request

    @classmethod
    def from_dict(cls, data: dict) -> 'CustomRequestReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class SongReturnType:
    song: Optional[Song] = None  # The song returned

    @classmethod
    def from_dict(cls, data: dict) -> 'SongReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class PlaylistAndSongsReturnType:
    playlist: Optional[Playlist] = None  # The playlist returned
    songs: Optional[List[Song]] = None  # The list of songs in the playlist

    @classmethod
    def from_dict(cls, data: dict) -> 'PlaylistAndSongsReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class ContextMenuReturnType:
    name: str = ""  # The name of the context menu item
    icon: str = ""  # The icon of the context menu item
    actionId: str = ""  # The action ID of the context menu item

    @classmethod
    def from_dict(cls, data: dict) -> 'ContextMenuReturnType':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class PreferenceData:
    key: str  # The key of the preference
    value: Optional[Any] = None  # The value of the preference
    defaultValue: Optional[Any] = None  # The default value of the preference

    @classmethod
    def from_dict(cls, data: dict) -> 'PreferenceData':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

@dataclass
class AddToPlaylistRequest:
    playlistID: str  # The unique identifier for the playlist
    songs: List[Song]  # The list of songs to add to the playlist

    @classmethod
    def from_dict(cls, data: dict) -> 'AddToPlaylistRequest':
        return cls(**{
            k: v for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })

class PreferenceTypes(Enum):
    DirectoryGroup = "DirectoryGroup"
    EditText = "EditText"
    FilePicker = "FilePicker"
    CheckboxGroup = "CheckboxGroup"
    ThemeSelector = "ThemeSelector"
    Extensions = "Extensions"
    ButtonGroup = "ButtonGroup"
    ProgressBar = "ProgressBar"
    TextField = "TextField"
    InfoField = "InfoField"
    Dropdown = "Dropdown"

class InputType(Enum):
    Text = "text"
    Number = "number"

@dataclass(frozen=True)
class CheckboxItems:
    title: str
    key: str

@dataclass
class PreferenceUIData:
    type: 'PreferenceTypes'  # Use string annotation for forward reference or import the actual class
    title: str
    key: str
    description: str
    inputType: Optional['InputType'] = None
    single: Optional[bool] = None
    items: Optional[List['CheckboxItems']] = None
    default: Optional[Any] = None  # Replace Any with the actual Value type if available
    mobile: Optional[bool] = None
