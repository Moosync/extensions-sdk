#![no_main]

use moosync_edk::{
    ExtensionProviderScope, RequestedSearchResultRequest, ScrobbleRequest, SearchResult,
    api::{
        self, Accounts, ContextMenu, DatabaseEvents, Extension, PlayerEvents, PreferenceEvents,
        Provider, extension_api::get_current_song,
    },
    handler::register_extension,
    info,
};

// ANCHOR: first_extension
struct SampleExtension;

impl Extension for SampleExtension {}
impl Accounts for SampleExtension {}
impl DatabaseEvents for SampleExtension {}
impl PlayerEvents for SampleExtension {}
impl PreferenceEvents for SampleExtension {}
impl ContextMenu for SampleExtension {}

#[unsafe(no_mangle)]
pub extern "C" fn init() {
    info!("Initializing SampleExtension");
    register_extension(Box::new(SampleExtension)).unwrap();
    info!("Initialized SampleExtension");
}
// ANCHOR_END: first_extension

impl Provider for SampleExtension {
// ANCHOR: provider
    fn get_provider_scopes(&self) -> api::MoosyncResult<Vec<ExtensionProviderScope>> {
        Ok(vec![ExtensionProviderScope::Search])
    }

    fn search(&self, req: RequestedSearchResultRequest) -> api::MoosyncResult<SearchResult> {
        info!("Search requested for query: {}", req.query);

        let url = format!("https://api.spotify.com/v1/search?q={}&type=track", req.query);
        let resp = moosync_edk::http::get(&url, None)?;
        if resp.is_success() {
            info!("Search API response: {}", resp.text().unwrap_or_default());
        }

        Ok(SearchResult {
            songs: vec![],
            artists: vec![],
            playlists: vec![],
            albums: vec![],
            genres: vec![],
        })
    }
// ANCHOR_END: provider

// ANCHOR: api_usage
    fn scrobble(&self, _req: ScrobbleRequest) -> api::MoosyncResult<()> {
        let song = get_current_song()?;
        if let Some(song) = song {
            if let Some(inner) = song.song {
                if let Some(title) = inner.title {
                    info!("Currently playing song: {}", title);
                }
            }
        }
        Ok(())
    }
// ANCHOR_END: api_usage
}

// ANCHOR: http_usage
pub fn search_and_fetch_details(query: &str) -> api::MoosyncResult<()> {
    use moosync_edk::http::{self, HttpRequest};

    let url = format!("https://api.spotify.com/v1/search?q={}&type=track", query);
    let resp = http::get(&url, None)?;
    if resp.is_success() {
        info!("Search response: {}", resp.text().unwrap_or_default());
    }

    let post_req = HttpRequest::post("https://api.spotify.com/v1/playlists")
        .header("Authorization", "Bearer token123")
        .body(r#"{"name":"My Playlist"}"#.as_bytes().to_vec())
        .timeout_ms(5000);
    let post_resp = http::request(&post_req)?;
    info!("Create playlist status: {}", post_resp.status_code);

    let track_urls = vec![
        "https://api.spotify.com/v1/tracks/1",
        "https://api.spotify.com/v1/tracks/2",
    ];
    let responses = http::batch_get(&track_urls, None)?;
    for r in responses {
        info!("Track status: {}", r.status_code);
    }
    Ok(())
}
// ANCHOR_END: http_usage
