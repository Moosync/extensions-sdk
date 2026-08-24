package main

import (
	extensions "github.com/moosync/moosync/types/extensions"
	songs "github.com/moosync/moosync/types/songs"

	"github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/api"
)

// ANCHOR: first_extension
type SampleExtension struct {
	api.DefaultExtension
}

//go:wasmexport entry
func entry() {
	extension := &SampleExtension{}
	api.RegisterExtension(extension)
}

func main() {}
// ANCHOR_END: first_extension

// ANCHOR: provider
func (s *SampleExtension) GetProviderScopes() ([]extensions.ExtensionProviderScope, error) {
	return []extensions.ExtensionProviderScope{
		extensions.ExtensionProviderScope_SEARCH,
	}, nil
}

func (s *SampleExtension) Search(req *extensions.RequestedSearchResultRequest) (*songs.SearchResult, error) {
	api.LogInfo("Search called with query: %s", req.GetQuery())

	url := "https://api.spotify.com/v1/search?q=" + req.GetQuery() + "&type=track"
	resp, err := api.HttpGet(url, nil)
	if err != nil {
		return nil, err
	}
	if resp.OK() {
		api.LogInfo("Search response: %s", resp.Text())
	}

	return &songs.SearchResult{
		Songs:     []*songs.Song{},
		Playlists: []*songs.Playlist{},
		Artists:   []*songs.Artist{},
		Albums:    []*songs.Album{},
		Genres:    []*songs.Genre{},
	}, nil
}
// ANCHOR_END: provider

// ANCHOR: api_usage
func (s *SampleExtension) Scrobble(req *extensions.ScrobbleRequest) error {
	song, err := api.GetCurrentSong()
	if err != nil {
		return err
	}
	if song != nil && song.GetSong() != nil {
		api.LogInfo("Currently playing song: %s", song.GetSong().GetTitle())
	}
	return nil
}
// ANCHOR_END: api_usage

// ANCHOR: http_usage
func searchAndFetchDetails(query string) error {
	url := "https://api.spotify.com/v1/search?q=" + query + "&type=track"
	resp, err := api.HttpGet(url, nil)
	if err != nil {
		return err
	}
	if resp.OK() {
		api.LogInfo("Search response: %s", resp.Text())
	}

	postReq := api.HttpRequest{
		URL:       "https://api.spotify.com/v1/playlists",
		Method:    "POST",
		Headers:   map[string]string{"Authorization": "Bearer token123"},
		Body:      []byte(`{"name":"My Playlist"}`),
		TimeoutMs: 5000,
	}
	postResp, err := api.SendHttpRequest(postReq)
	if err != nil {
		return err
	}
	api.LogInfo("Create playlist status: %d", postResp.StatusCode)

	trackURLs := []string{
		"https://api.spotify.com/v1/tracks/1",
		"https://api.spotify.com/v1/tracks/2",
	}
	resps, errs := api.BatchHttpGet(trackURLs, nil)
	if len(errs) > 0 {
		return errs[0]
	}
	for _, r := range resps {
		api.LogInfo("Track status: %d", r.StatusCode)
	}
	return nil
}
// ANCHOR_END: http_usage
