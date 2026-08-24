import {
  GetProviderScopesResponse,
  RequestedSearchResultResponse,
  ScrobbleResponse,
  getApi,
} from "wasm-extension-js";

export { handle_extension_command } from "wasm-extension-js";

// ANCHOR: first_extension
export function entry(): number {
  const api = getApi();

  console.log("Initialized sample extension");
  return 0;
}
// ANCHOR_END: first_extension

// ANCHOR: provider
export function registerProviderHandlers() {
  const api = getApi();

  api.on("getProviderScopes", () => {
    return new GetProviderScopesResponse({
      scopes: [
        13 as any // ExtensionProviderScope.SEARCH
      ]
    });
  });

  api.on("requestedSearchResult", async (req) => {
    console.log("Search query:", req.query);

    const url = `https://api.spotify.com/v1/search?q=${encodeURIComponent(req.query)}&type=track`;
    const resp = await api.fetch(url);
    if (resp.ok) {
      const text = await resp.text();
      console.log("Search response:", text);
    }

    return new RequestedSearchResultResponse({
      songs: []
    });
  });
}
// ANCHOR_END: provider

// ANCHOR: api_usage
export function registerApiUsage() {
  const api = getApi();

  api.on("scrobble", async (req) => {
    const song = await api.getCurrentSong();
    if (song && song.song && song.song.title) {
      console.log("Currently playing song:", song.song.title);
    }
    return new ScrobbleResponse();
  });
}
// ANCHOR_END: api_usage

// ANCHOR: http_usage
export async function searchAndFetchDetails(query: string) {
  const api = getApi();

  const url = `https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track`;
  const resp = await api.fetch(url);
  if (resp.ok) {
    const text = await resp.text();
    console.log("Search response:", text);
  }

  const postResp = await api.fetch({
    url: "https://api.spotify.com/v1/playlists",
    method: "POST",
    headers: { Authorization: "Bearer token123" },
    body: JSON.stringify({ name: "My Playlist" }),
    timeoutMs: 5000,
  });
  console.log("Create playlist status:", postResp.status);

  const responses = await api.batchFetch([
    "https://api.spotify.com/v1/tracks/1",
    "https://api.spotify.com/v1/tracks/2",
  ]);
  for (const r of responses) {
    console.log("Track status:", r.status);
  }
}
// ANCHOR_END: http_usage
