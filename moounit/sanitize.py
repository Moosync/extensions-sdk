from core.types.protos.extensions_pb2 import (
    ExtensionCommand,
    ExtensionCommandResponse,
    MainCommand,
)
from core.types.protos.songs_pb2 import (
    Album,
    Artist,
    Genre,
    Playlist,
    Song,
)


def sanitize_key(key: str, package_name: str) -> str:
    if not key or not package_name:
        return key
    prefix = f"{package_name}."
    if key.startswith(prefix):
        return key
    return f"{prefix}{key}"


def sanitize_id(entity_id: str | None, package_name: str) -> str | None:
    if not entity_id or not package_name:
        return entity_id
    prefix = f"{package_name}:"
    if entity_id.startswith(prefix):
        return entity_id
    return f"{prefix}{entity_id}"


def sanitize_album(
    album: Album,
    package_name: str,
    is_response: bool = False,
) -> None:
    if not package_name:
        return
    prefix = f"{package_name}:"
    if album.HasField("album_id") and album.album_id:
        if not album.album_id.startswith(prefix):
            album.album_id = f"{prefix}{album.album_id}"
    if is_response:
        album.extension = package_name


def sanitize_artist(
    artist: Artist,
    package_name: str,
    is_response: bool = False,
) -> None:
    if not package_name:
        return
    prefix = f"{package_name}:"
    if artist.HasField("artist_id") and artist.artist_id:
        if not artist.artist_id.startswith(prefix):
            artist.artist_id = f"{prefix}{artist.artist_id}"
    if is_response:
        artist.extension = package_name


def sanitize_genre(
    genre: Genre,
    package_name: str,
) -> None:
    if not package_name:
        return
    prefix = f"{package_name}:"
    if genre.HasField("genre_id") and genre.genre_id:
        if not genre.genre_id.startswith(prefix):
            genre.genre_id = f"{prefix}{genre.genre_id}"


def sanitize_playlist(
    playlist: Playlist,
    package_name: str,
    is_response: bool = False,
) -> None:
    if not package_name:
        return
    prefix = f"{package_name}:"
    if playlist.HasField("playlist_id") and playlist.playlist_id:
        if not playlist.playlist_id.startswith(prefix):
            playlist.playlist_id = f"{prefix}{playlist.playlist_id}"
    if is_response:
        playlist.extension = package_name


def sanitize_song(
    song: Song,
    package_name: str,
    is_response: bool = False,
) -> None:
    if not package_name:
        return
    if not song.HasField("song"):
        raise ValueError("Song cannot be empty")

    prefix = f"{package_name}:"
    if song.song.HasField("id") and song.song.id:
        if not song.song.id.startswith(prefix):
            song.song.id = f"{prefix}{song.song.id}"
    if is_response:
        song.song.extension = package_name

    if song.HasField("album"):
        sanitize_album(song.album, package_name, is_response=is_response)

    for artist in song.artists:
        sanitize_artist(artist, package_name, is_response=is_response)

    for genre in song.genre:
        sanitize_genre(genre, package_name)


def sanitize_main_command(command: MainCommand, package_name: str) -> None:
    if not package_name:
        return
    cmd_variant = command.WhichOneof("command")
    if cmd_variant in ("get_preference", "set_preference", "get_secure", "set_secure"):
        sub_req = getattr(command, cmd_variant)
        if sub_req.HasField("data"):
            sub_req.data.key = sanitize_key(sub_req.data.key, package_name)
    elif cmd_variant == "add_songs":
        for song in command.add_songs.songs:
            sanitize_song(song, package_name, is_response=False)
    elif cmd_variant == "remove_song":
        if command.remove_song.HasField("song"):
            sanitize_song(command.remove_song.song, package_name, is_response=False)
    elif cmd_variant == "update_song":
        if command.update_song.HasField("song"):
            sanitize_song(command.update_song.song, package_name, is_response=False)
    elif cmd_variant == "add_playlist":
        if command.add_playlist.HasField("playlist"):
            sanitize_playlist(
                command.add_playlist.playlist, package_name, is_response=False
            )
    elif cmd_variant == "add_to_playlist":
        for song in command.add_to_playlist.songs:
            sanitize_song(song, package_name, is_response=False)
    elif cmd_variant == "set_account":
        if command.set_account.HasField("account"):
            command.set_account.account.package_name = package_name


def sanitize_extension_response(
    response: ExtensionCommandResponse, package_name: str
) -> None:
    if not package_name:
        return
    resp_variant = response.WhichOneof("response")
    if resp_variant == "requested_playlists":
        for playlist in response.requested_playlists.playlists:
            sanitize_playlist(playlist, package_name, is_response=True)
    elif resp_variant in (
        "requested_playlist_songs",
        "requested_artist_songs",
        "requested_album_songs",
        "requested_recommendations",
    ):
        sub_resp = getattr(response, resp_variant)
        for song in sub_resp.songs:
            sanitize_song(song, package_name, is_response=True)
    elif resp_variant == "requested_search_result":
        search_resp = response.requested_search_result
        for song in search_resp.songs:
            sanitize_song(song, package_name, is_response=True)
        for playlist in search_resp.playlists:
            sanitize_playlist(playlist, package_name, is_response=True)
        for artist in search_resp.artists:
            sanitize_artist(artist, package_name, is_response=True)
        for album in search_resp.albums:
            sanitize_album(album, package_name, is_response=True)
    elif resp_variant in ("requested_song_from_url", "requested_song_from_id"):
        sub_resp = getattr(response, resp_variant)
        if sub_resp.HasField("song"):
            sanitize_song(sub_resp.song, package_name, is_response=True)
    elif resp_variant == "requested_playlist_from_url":
        pl_resp = response.requested_playlist_from_url
        if pl_resp.HasField("playlist"):
            sanitize_playlist(pl_resp.playlist, package_name, is_response=True)
        for song in pl_resp.songs:
            sanitize_song(song, package_name, is_response=True)


def sanitize_extension_command(command: ExtensionCommand, package_name: str) -> None:
    if not package_name:
        return
    if not command.package_name:
        command.package_name = package_name
