#![no_main]

use moosync_edk::{
    api::{
        host_api::get_current_song, Accounts, ContextMenu, DatabaseEvents, Extension,
        GetCurrentSongRequest, PlayerEvents, PlayerProvider, PreferenceEvents, Provider,
        RequestedSearchResultRequest, RequestedSearchResultResponse, ScrobbleRequest,
    },
    handler::register_extension,
    info, MoosyncResult,
};

// ANCHOR: first_extension
struct SampleExtension;

impl Extension for SampleExtension {}
impl Accounts for SampleExtension {}
impl ContextMenu for SampleExtension {}
impl PlayerEvents for SampleExtension {}
impl DatabaseEvents for SampleExtension {}
impl PreferenceEvents for SampleExtension {}
impl PlayerProvider for SampleExtension {}

impl Provider for SampleExtension {
// ANCHOR: provider
    fn requested_search_result(
        &self,
        req: RequestedSearchResultRequest,
    ) -> MoosyncResult<RequestedSearchResultResponse> {
        info!("Search requested for query: {}", req.query);

        let url = format!("https://api.spotify.com/v1/search?q={}&type=track", req.query);
        let resp = moosync_edk::http::get(&url, None)?;
        if resp.is_success() {
            info!("Search API response: {}", resp.text().unwrap_or_default());
        }

        Ok(RequestedSearchResultResponse {
            songs: vec![],
            artists: vec![],
            playlists: vec![],
            albums: vec![],
        })
    }
// ANCHOR_END: provider

// ANCHOR: api_usage
    fn scrobble(&self, _req: ScrobbleRequest) -> MoosyncResult<()> {
        let resp = get_current_song(GetCurrentSongRequest {})?;
        if let Some(song) = resp.song.and_then(|s| s.song).and_then(|i| i.title) {
            info!("Currently playing song: {}", song);
        }
        Ok(())
    }
// ANCHOR_END: api_usage
}

#[unsafe(no_mangle)]
pub extern "C" fn init() {
    info!("Initializing SampleExtension");
    register_extension(Box::new(SampleExtension)).unwrap();
    info!("Initialized SampleExtension");
}
// ANCHOR_END: first_extension

// ANCHOR: http_usage
pub fn search_and_fetch_details(query: &str) -> MoosyncResult<()> {
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
