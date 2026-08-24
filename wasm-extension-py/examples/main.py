from moosync_edk import Extension, register_extension
from core.types.protos import extensions_pb2, songs_pb2

# ANCHOR: first_extension
class SampleExtension(Extension):
    def __init__(self):
        super().__init__()

def entry():
    print("Initializing SampleExtension")
    register_extension(SampleExtension())
# ANCHOR_END: first_extension

# ANCHOR: provider
class SearchProviderExtension(Extension):
    def get_provider_scopes(self, req):
        return extensions_pb2.GetProviderScopesResponse(
            scopes=[extensions_pb2.ExtensionProviderScope.SEARCH]
        )

    def search(self, req):
        print(f"Search query: {req.query}")

        url = f"https://api.spotify.com/v1/search?q={req.query}&type=track"
        resp = http_get(url)
        if resp.ok:
            print(f"Search response: {resp.text}")

        return songs_pb2.SearchResult(
            songs=[],
            artists=[],
            playlists=[],
            albums=[],
            genres=[]
        )
# ANCHOR_END: provider

# ANCHOR: api_usage
class ScrobbleExtension(Extension):
    def scrobble(self, req):
        song = self.api.get_current_song()
        if song and song.song:
            print(f"Currently playing: {song.song.title}")
# ANCHOR_END: api_usage

# ANCHOR: http_usage
from moosync_edk import http_get, http_request, http_batch_get

def search_and_fetch_details(query):
    url = f"https://api.spotify.com/v1/search?q={query}&type=track"
    resp = http_get(url)
    if resp.ok:
        print(f"Search response: {resp.text}")

    post_resp = http_request(
        url="https://api.spotify.com/v1/playlists",
        method="POST",
        headers={"Authorization": "Bearer token123"},
        body='{"name": "My Playlist"}',
        timeout_ms=5000,
    )
    print(f"Create playlist status: {post_resp.status_code}")

    track_urls = [
        "https://api.spotify.com/v1/tracks/1",
        "https://api.spotify.com/v1/tracks/2",
    ]
    resps = http_batch_get(track_urls)
    for r in resps:
        print(f"Track status: {r.status_code}")
# ANCHOR_END: http_usage
