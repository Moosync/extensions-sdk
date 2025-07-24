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

/**
 * Represents an album entity in the system
 */
export interface Album {
  /** Unique identifier for the album */
  album_id?: string;
  /** Name of the album */
  album_name?: string;
  /** High resolution cover art path */
  album_coverPath_high?: string;
  /** Low resolution cover art path */
  album_coverPath_low?: string;
  /** Number of songs in the album */
  album_song_count?: number;
  /** Primary artist of the album */
  album_artist?: string;
  /** Additional information about the album */
  album_extra_info?: string;
}

/**
 * Represents an artist entity in the system
 */
export interface Artist {
  /** Unique identifier for the artist */
  artist_id: string;
  /** Name of the artist */
  artist_name?: string;
  /** Path to the artist's cover image */
  artist_coverPath?: string;
  /** Number of songs by this artist */
  artist_song_count?: number;
  /** Additional information about the artist from various services */
  artist_extra_info?: {
    /** Extension-specific data */
    extensions?: Record<string, Record<string, string | undefined> | undefined>;
  };
}

/**
 * Represents a genre entity in the system
 */
export interface Genre {
  /** Unique identifier for the genre */
  genre_id: string;
  /** Name of the genre */
  genre_name: string;
  /** Number of songs in this genre */
  genre_song_count: number;
}

/**
 * Represents a playlist entity in the system
 */
export interface Playlist {
  /** Unique identifier for the playlist */
  playlist_id: string;
  /** Name of the playlist */
  playlist_name: string;
  /** Path to the playlist's cover image */
  playlist_coverPath?: string | undefined;
  /** Number of songs in the playlist */
  playlist_song_count?: number;
  /** File path of the playlist */
  playlist_path?: string;
}

/**
 * Types of media players supported by the system
 */
export type PlayerTypes =
  | "LOCAL"
  | "YOUTUBE"
  | "SPOTIFY"
  | "URL"
  | "DASH"
  | "HLS";

/**
 * Represents a song entity in the system
 */
export interface Song {
  /** Unique identifier for the song */
  _id: string;
  /** File path of the song */
  path?: string;
  /** File size in bytes */
  size?: number;
  /** Title of the song */
  title: string;
  /** Low resolution cover art path */
  song_coverPath_low?: string;
  /** High resolution cover art path */
  song_coverPath_high?: string;
  /** Album information */
  album?: Album;
  /** Artists associated with the song */
  artists?: Artist[];
  /** Release date of the song */
  date?: string;
  /** Release year of the song */
  year?: number | string;
  /** Genres associated with the song */
  genre?: string[];
  /** Lyrics of the song */
  lyrics?: string;
  /** Type of release (e.g., single, album) */
  releaseType?: string[];
  /** Bitrate of the song in kbps */
  bitrate?: number;
  /** Audio codec used */
  codec?: string;
  /** Container format */
  container?: string;
  /** Duration of the song in seconds */
  duration: number;
  /** Sample rate in Hz */
  sampleRate?: number;
  /** MD5 hash of the file */
  hash?: string;
  /** Inode number (for local files) */
  inode?: string;
  /** Device number (for local files) */
  deviceno?: string;
  /** URL for streaming the song */
  url?: string;
  /** URL specifically for playback */
  playbackUrl?: string;
  /** Date when the song was added to the library */
  date_added?: number;
  /** Icon representing the song or its source */
  icon?: string;
  /** Type of player required for this song */
  type: PlayerTypes;
  /** Track number in its album */
  track_no?: number;
}

/**
 * Interface for song search parameters with minimal fields
 */
export interface SearchableSong {
  /** Unique identifier for the song */
  _id?: string;
  /** File path of the song */
  path?: string;
  /** Title of the song */
  title?: string;
  /** URL for streaming the song */
  url?: string;
  /** URL specifically for playback */
  playbackUrl?: string;

  /** MD5 hash of the file */
  hash?: string;

  /** File size in bytes */
  size?: number;
  /** Inode number (for local files) */
  inode?: string;
  /** Device number (for local files) */
  deviceno?: string;

  /** Type of player required for this song */
  type?: PlayerTypes;

  /** Extension providing this song */
  extension?: boolean | string;

  /** Whether the song should be shown in the library */
  showInLibrary?: boolean;
}

/**
 * States that the player can be in
 */
type PlayerState = "PLAYING" | "PAUSED" | "STOPPED" | "LOADING";

/**
 * Sort by key in Song.
 * If asc is true then results will be sorted in ascending otherwise descending
 */
type SongSortOptions = { type: keyof Song; asc: boolean };

/**
 * Options for searching songs from Database
 * To search for all tracks with a specific term, surround the term with %.
 * Eg. if the term is 'aaa', to get all songs containing 'aaa' in the title,
 * put the term as '%aaa%' in 'song.title'.
 */
export interface SongAPIOptions {
  /**
   * To search tracks by properties in song, specify this property.
   */
  song?: SearchableSong;

  /**
   * To search tracks by properties in album, specify this property.
   */
  album?: Partial<Album>;

  /**
   * To search tracks by properties in artists, specify this property.
   */
  artist?: Partial<Artist>;

  /**
   * To search tracks by properties in genre, specify this property.
   */
  genre?: Partial<Genre>;

  /**
   * To search tracks by properties in playlist, specify this property.
   */
  playlist?: Partial<Playlist>;

  /**
   * To sort the results, specify this property
   */
  sortBy?: SongSortOptions | SongSortOptions[];

  /**
   * If false, then the exact match of all options will be provided.
   * If true, then even if a track matches one of the options, it will be returned.
   * In terms of SQL, true will add 'AND' between where queries and false will add 'OR'.
   *
   * Eg. If song.title is 'aaa' and album.album_name is 'bbb'
   *
   * In this scenario if inclusive is true, then all tracks having title as 'aaa'
   * AND album_name as 'bbb' will be returned
   *
   * If inclusive is false then songs having title as 'aaa' OR album_name as 'bbb' will be returned
   *
   * False by default
   */
  inclusive?: boolean;

  /**
   * If true, then inverts the query. It will return all records which don't match the search criteria
   * If false, then it will return all records which match the search criteria
   *
   * false by default
   */
  invert?: boolean;
}

/**
 * Options for searching entities like Albums, Artists, Playlists or Genre
 */
export type EntityApiOptions<T extends Artist | Album | Genre | Playlist> = {
  /**
   * If false, then the exact match of all options will be provided.
   * If true, then even if an entity matches one of the options, it will be returned.
   * In terms of SQL, true will add 'AND' between where queries and false will add 'OR'.
   *
   * Eg. If album.album_name is 'aaa' and album.album_id is 'bbb'
   *
   * In this scenario if inclusive is false, then all albums having album_name as 'aaa'
   * AND album_id as 'bbb' will be returned
   *
   * If inclusive is false then albums having album_name as 'aaa' OR album_id as 'bbb' will be returned
   */
  inclusive?: boolean;

  /**
   * If true, then inverts the query. It will return all records which don't match the search criteria
   * If false, then it will return all records which match the search criteria
   *
   * false by default
   */
  invert?: boolean;
} & (T extends Artist
  ? {
      artist: Partial<Artist> | boolean;
    }
  : T extends Album
    ? {
        album: Partial<Album> | boolean;
      }
    : T extends Genre
      ? {
          genre: Partial<Genre> | boolean;
        }
      : T extends Playlist
        ? {
            playlist: Partial<Playlist> | boolean;
          }
        : Record<string, never>);

/**
 * Details of an account connected to the system
 */
export type AccountDetails = {
  /** Unique identifier for the account */
  id: string;
  /** Package name of the extension */
  packageName: string;
  /** Display name for the account */
  name: string;
  /** Background color for UI elements */
  bgColor: string;
  /** Icon for the account */
  icon: string;
  /** Whether the user is logged in */
  loggedIn: boolean;
  /** Username of the logged in user */
  username?: string;
};

/**
 * Arguments for account login events
 */
export interface AccountLoginArgs {
  /** Package name of the extension */
  packageName: string;
  /** Account identifier */
  accountId: string;
  /** Whether login was successful */
  loginStatus: boolean;
}

/**
 * Arguments for preference change events
 */
export interface PreferenceArgs {
  /** Preference key */
  key: string;
  /** Preference value */
  value: any;
}

/**
 * Supported scopes for provider extensions
 */
export type ProviderScope =
  | "search"
  | "playlists"
  | "playlistSongs"
  | "artistSongs"
  | "albumSongs"
  | "recommendations"
  | "scrobbles"
  | "playlistFromUrl"
  | "songFromUrl"
  | "searchAlbum"
  | "searchArtist"
  | "playbackDetails"
  | "lyrics"
  | "songContextMenu"
  | "playlistContextMenu"
  | "accounts";

/**
 * Return type for search operations
 */
export interface SearchReturnType {
  /** List of songs found */
  songs: Song[];
  /** List of artists found */
  artists: Artist[];
  /** List of playlists found */
  playlists: Playlist[];
  /** List of albums found */
  albums: Album[];
  /** List of genres found */
  genres: Genre[];
}

/**
 * Return type for recommendation operations
 */
export interface RecommendationsReturnType {
  /** List of recommended songs */
  songs: Song[];
}

/**
 * Return type for playlist operations
 */
export interface PlaylistsReturnType {
  /** List of playlists */
  playlists: Playlist[];
}

/**
 * Return type for operations that return songs with pagination
 */
export interface SongsWithPageTokenReturnType {
  /** List of songs */
  songs: Song[];
  /** Token for fetching the next page */
  nextPageToken?: unknown;
}

/**
 * Return type for playback detail operations
 */
export interface PlaybackDetailsReturnType {
  /** Duration of the song in seconds */
  duration: number;
  /** URL for playback */
  url: string;
}

/**
 * Return type for custom request operations
 */
export interface CustomRequestReturnType {
  /** MIME type of the response */
  mimeType?: string;
  /** Response data */
  data?: unknown;
  /** URL to redirect to */
  redirectUrl?: string;
}

/**
 * Return type for song retrieval operations
 */
export interface SongReturnType {
  /** Retrieved song */
  song?: Song;
}

/**
 * Return type for operations that return both a playlist and its songs
 */
export interface PlaylistAndSongsReturnType {
  /** Retrieved playlist */
  playlist?: Playlist;
  /** Songs in the playlist */
  songs?: Song[];
}

/**
 * Data structure for preference operations
 */
export interface PreferenceData<T = unknown> {
  /** Preference key */
  key: string;
  /** Preference value */
  value?: T;
  /** Default value if the preference doesn't exist */
  defaultValue?: T;
}

/**
 * Request structure for adding songs to a playlist
 */
export interface AddToPlaylistRequest {
  /** ID of the playlist to add songs to */
  playlistID: string;
  /** Songs to add to the playlist */
  songs: Song[];
}

/**
 * Return type for context menu operations
 */
export interface ContextMenuReturnType {
  /** Display name for the menu item */
  name: string;
  /** Icon for the menu item */
  icon: string;
  /** Unique identifier for the action */
  action_id: string;
}

export enum PreferenceTypes {
  DirectoryGroup = "DirectoryGroup",
  EditText = "EditText",
  FilePicker = "FilePicker",
  CheckboxGroup = "CheckboxGroup",
  ThemeSelector = "ThemeSelector",
  Extensions = "Extensions",
  ButtonGroup = "ButtonGroup",
  ProgressBar = "ProgressBar",
  TextField = "TextField",
  InfoField = "InfoField",
  Dropdown = "Dropdown",
}

export enum InputType {
  Text = "text",
  Number = "number",
}

export interface CheckboxItems {
  title: string;
  key: string;
}

export interface PreferenceUIData {
  type: PreferenceTypes;
  title: string;
  key: string;
  description: string;
  inputType?: InputType;
  single?: boolean;
  items?: CheckboxItems[];
  default?: any;
  mobile?: boolean;
}

/**
 * The API exposed to extensions
 */
export interface ExtensionAPI {
  /**
   * Called when the main app requests the list of accounts.
   * @param event Event name
   * @param cb Callback that returns the list of accounts
   */
  on(event: "getAccounts", cb: () => AccountDetails[]): void;

  /**
   * Called when the main app requests to perform an account login.
   * @param event Event name
   * @param cb Callback that handles the login request
   */
  on(
    event: "performAccountLogin",
    cb: (args: AccountLoginArgs) => string,
  ): void;

  /**
   * Called when the main app provides an OAuth callback code.
   * @param event Event name
   * @param cb Callback that handles the OAuth code
   */
  on(event: "oauthCallback", cb: (code: string) => void): void;

  /**
   * Called when the main app requests to scrobble a song.
   * @param event Event name
   * @param cb Callback that handles the scrobble request
   */
  on(event: "scrobble", cb: (song: Song) => void): void;

  /**
   * Called when a playlist is removed from the database.
   * @param event Event name
   * @param cb Callback that receives the removed playlist
   */
  on(event: "onPlaylistRemoved", cb: (playlist: Playlist) => void): void;

  /**
   * Called when a playlist is added to the database.
   * @param event Event name
   * @param cb Callback that receives the added playlist
   */
  on(event: "onPlaylistAdded", cb: (playlist: Playlist) => void): void;

  /**
   * Called when a song is removed from the database.
   * @param event Event name
   * @param cb Callback that receives the removed song
   */
  on(event: "onSongRemoved", cb: (song: Song) => void): void;

  /**
   * Called when a song is added to the database.
   * @param event Event name
   * @param cb Callback that receives the added song
   */
  on(event: "onSongAdded", cb: (song: Song) => void): void;

  /**
   * Called when preferences are changed.
   * @param event Event name
   * @param cb Callback that receives the changed preference
   */
  on(event: "onPreferencesChanged", cb: (args: PreferenceArgs) => void): void;

  /**
   * Called when the player is seeked to a specific time.
   * @param event Event name
   * @param cb Callback that receives the new playback time
   */
  on(event: "onSeeked", cb: (time: number) => void): void;

  /**
   * Called when the song is changed.
   * @param event Event name
   * @param cb Callback that receives the new song
   */
  on(event: "onSongChanged", cb: (song: Song | undefined) => void): void;

  /**
   * Called when the player state is changed.
   * @param event Event name
   * @param cb Callback that receives the new player state
   */
  on(event: "onPlayerStateChanged", cb: (state: PlayerState) => void): void;

  /**
   * Called when the queue is changed.
   * @param event Event name
   * @param cb Callback that receives the new queue
   */
  on(event: "onQueueChanged", cb: (queue: unknown) => void): void;

  /**
   * Called when the volume is changed.
   * @param event Event name
   * @param cb Callback that receives the new volume
   */
  on(event: "onVolumeChanged", cb: (volume: number) => void): void;

  /**
   * Called when the main app requests the provider scopes.
   * @param event Event name
   * @param cb Callback that returns the provider scopes
   */
  on(event: "getProviderScopes", cb: () => ProviderScope[]): void;

  /**
   * Called when the main app requests the list of playlists.
   * @param event Event name
   * @param cb Callback that returns the playlists
   */
  on(event: "getPlaylists", cb: () => Promise<PlaylistsReturnType>): void;

  /**
   * Called when the main app requests the content of a specific playlist.
   * @param event Event name
   * @param cb Callback that returns the playlist content
   */
  on(
    event: "getPlaylistContent",
    cb: (id: string, token?: string) => Promise<SongsWithPageTokenReturnType>,
  ): void;

  /**
   * Called when the main app requests a playlist from a URL.
   * @param event Event name
   * @param cb Callback that returns the playlist and its songs
   */
  on(
    event: "getPlaylistFromUrl",
    cb: (url: string) => Promise<PlaylistAndSongsReturnType>,
  ): void;

  /**
   * Called when the main app requests playback details for a song.
   * @param event Event name
   * @param cb Callback that returns the playback details
   */
  on(
    event: "getPlaybackDetails",
    cb: (song: Song) => Promise<PlaybackDetailsReturnType>,
  ): void;

  /**
   * Called when the main app performs a search.
   * @param event Event name
   * @param cb Callback that returns the search results
   */
  on(event: "search", cb: (term: string) => Promise<SearchReturnType>): void;

  /**
   * Called when the main app requests recommendations.
   * @param event Event name
   * @param cb Callback that returns the recommendations
   */
  on(
    event: "getRecommendations",
    cb: () => Promise<RecommendationsReturnType>,
  ): void;

  /**
   * Called when the main app requests a song from a URL.
   * @param event Event name
   * @param cb Callback that returns the song
   */
  on(
    event: "getSongFromUrl",
    cb: (url: string) => Promise<SongReturnType>,
  ): void;

  /**
   * Called when the main app handles a custom request.
   * @param event Event name
   * @param cb Callback that handles the custom request
   */
  on(
    event: "handleCustomRequest",
    cb: (url: string) => Promise<CustomRequestReturnType>,
  ): void;

  /**
   * Called when the main app requests songs of a specific artist.
   * @param event Event name
   * @param cb Callback that returns the artist's songs
   */
  on(
    event: "getArtistSongs",
    cb: (
      artist: Artist,
      token?: string,
    ) => Promise<SongsWithPageTokenReturnType>,
  ): void;

  /**
   * Called when the main app requests songs of a specific album.
   * @param event Event name
   * @param cb Callback that returns the album's songs
   */
  on(
    event: "getAlbumSongs",
    cb: (album: Album, token?: string) => Promise<SongsWithPageTokenReturnType>,
  ): void;

  /**
   * Called when the main app requests a song from an ID.
   * @param event Event name
   * @param cb Callback that returns the song
   */
  on(event: "getSongFromId", cb: (id: string) => Promise<SongReturnType>): void;

  /**
   * Called when the main app requests the context menu for songs.
   * @param event Event name
   * @param cb Callback that returns the context menu items
   */
  on(
    event: "getSongContextMenu",
    cb: (songs: Song[]) => Promise<ContextMenuReturnType>,
  ): void;

  /**
   * Called when the main app requests the context menu for a playlist.
   * @param event Event name
   * @param cb Callback that returns the context menu items
   */
  on(
    event: "getPlaylistContextMenu",
    cb: (playlist: Playlist) => Promise<ContextMenuReturnType>,
  ): void;

  /**
   * Called when the main app performs an action from the context menu.
   * @param event Event name
   * @param cb Callback that handles the action
   */
  on(event: "onContextMenuAction", cb: (action: string) => Promise<void>): void;

  /**
   * Called when the main app requests lyrics for a song.
   * @param event Event name
   * @param cb Callback that returns the lyrics
   */
  on(event: "getLyrics", cb: (song: Song) => Promise<string>): void;

  /**
   * Retrieves a list of songs based on the provided options.
   * @param options The options to filter the songs
   * @returns An array of Song objects
   */
  getSong(options: SongAPIOptions): Song[];

  /**
   * Retrieves the current song being played.
   * @returns The current song or undefined if no song is playing
   */
  getCurrentSong(): Song | undefined;

  /**
   * Retrieves the current state of the player.
   * @returns The current player state
   */
  getPlayerState(): PlayerState;

  /**
   * Retrieves the current volume level.
   * @returns The current volume level between 0 and 1
   */
  getVolume(): number;

  /**
   * Retrieves the current playback time.
   * @returns The current playback time in seconds
   */
  getTime(): number;

  /**
   * Retrieves the current playback queue.
   * @returns An array of songs in the current queue
   */
  getQueue(): Song[];

  /**
   * Retrieves a preference value based on the provided data.
   * @param data The preference data containing key and optional default value
   * @returns The preference value
   */
  getPreference<T>(data: PreferenceData<T>): T;

  /**
   * Retrieves a secure preference value based on the provided data.
   * @param data The preference data containing key and optional default value
   * @returns The secure preference value
   */
  getSecure<T>(data: PreferenceData<T>): T;

  /**
   * Sets a preference value based on the provided data.
   * @param data The preference data containing key and value
   */
  setPreference<T>(data: PreferenceData<T>): void;

  /**
   * Sets a secure preference value based on the provided data.
   * @param data The preference data containing key and value
   */
  setSecure<T>(data: PreferenceData<T>): void;

  /**
   * Adds a list of songs to the main app.
   * @param songs The songs to add
   */
  addSongs(songs: Song[]): void;

  /**
   * Removes a song from the main app.
   * @param song The song to remove
   */
  removeSong(song: Song): void;

  /**
   * Updates a song in the main app.
   * @param song The song to update
   */
  updateSong(song: Song): void;

  /**
   * Adds a new playlist to the main app.
   * @param playlist The playlist to add
   * @returns The ID of the added playlist
   */
  addPlaylist(playlist: Playlist): string;

  /**
   * Adds songs to a playlist.
   * @param req The request containing the playlist ID and songs
   */
  addToPlaylist(req: AddToPlaylistRequest): void;

  /**
   * Registers an OAuth token with the main app.
   * @param token The OAuth token to register
   */
  registerOAuth(token: string): void;

  /**
   * Opens an external URL.
   * @param url The URL to open
   */
  openExternalUrl(url: string): void;

  /**
   * Registers user preferences to show in settings.
   * @param prefs An array of PreferenceUIData objects representing the preferences to register
   */
  registerUserPreferences(prefs: PreferenceUIData[]): void;

  /**
   * Unregisters user preferences from the main app.
   * @param pref_keys An array of preference keys to unregister
   */
  unregisterUserPreferences(pref_keys: string[]): void;

  /**
   * Updates the list of accounts in the main app.
   */
  updateAccounts(): void;
}

declare type module = Object;
