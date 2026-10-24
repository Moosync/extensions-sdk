"""
Provider scope constants for Moosync extensions matching ExtensionProviderScope proto.
"""

PROVIDER_SCOPES = struct(
    SEARCH = "search",
    PLAYLISTS = "playlists",
    PLAYLIST_SONGS = "playlist_songs",
    ARTIST_SONGS = "artist_songs",
    ALBUM_SONGS = "album_songs",
    RECOMMENDATIONS = "recommendations",
    SCROBBLE = "scrobble",
    PLAYLIST_FROM_URL = "playlist_from_url",
    PLAYBACK_DETAILS = "playback_details",
    ACCOUNT_DETAILS = "account_details",
    ACCOUNTS = "accounts",
    LYRICS = "lyrics",
    SONG_FROM_URL = "song_from_url",
    SONG_CONTEXT_MENU = "song_context_menu",
    PLAYLIST_CONTEXT_MENU = "playlist_context_menu",
    DATABASE_SONG_EVENTS = "database_song_events",
    DATABASE_PLAYLIST_EVENTS = "database_playlist_events",
    PLAYER_UI_EVENTS = "player_ui_events",
    PLAYER_DATA_EVENTS = "player_data_events",
)
