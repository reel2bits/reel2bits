package integrations

import (
	"dev.sigpipe.me/dashie/reel2bits/workers"
	"github.com/davecgh/go-spew/spew"
	"github.com/gosimple/slug"
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)

func createTrack(name string, desc string, public bool, dlLink bool, album int, licence int, t *testing.T, session *TestSession) (response *TestResponse) {
	// Get CSRF
	req := NewRequest(t, "GET", "/track/upload")
	resp := session.MakeRequest(t, req, http.StatusOK)
	csrf := NewHTMLParser(t, resp.Body)

	opts := map[string]string{
		"_csrf":       csrf.GetCSRF(),
		"title":       name,
		"description": desc,
		"album":       string(album),
		"licence":     string(licence),
	}

	if !public {
		opts["is_private"] = "true"
	}
	if dlLink {
		opts["show_dl_link"] = "true"
	}

	req = NewRequestWithBodyAndFile(t, "POST", "/track/upload", opts, "file", "integrations/STE-013.mp3")
	resp = session.MakeRequest(t, req, http.StatusFound)

	So(resp.Headers.Get("Location"), ShouldContainSubstring, "/t/usera")

	return resp
}

func deleteTrack(body []byte, t *testing.T, session *TestSession) {
	// Get track URL
	doc := NewHTMLParser(t, body)
	url, exists := doc.doc.Find("div.container div.single_track_list div.col-lg-12 a").Attr("href")
	So(exists, ShouldBeTrue)
	So(url, ShouldNotBeEmpty)

	// Direct access
	req := NewRequest(t, "GET", url)
	resp := session.MakeRequest(t, req, http.StatusOK)

	// Get delete url
	doc = NewHTMLParser(t, resp.Body)
	urlDelete, exists := doc.doc.Find("a.delete_btn").Attr("data-url")
	So(exists, ShouldBeTrue)
	So(urlDelete, ShouldNotBeEmpty)
	trackDataTrack, exists := doc.doc.Find("a.delete_btn").Attr("data-url")
	So(exists, ShouldBeTrue)
	So(trackDataTrack, ShouldNotBeEmpty)

	// Delete the Track
	// Get CSRF
	req = NewRequest(t, "GET", "/track/upload")
	resp = session.MakeRequest(t, req, http.StatusOK)
	csrf := NewHTMLParser(t, resp.Body)

	opts := map[string]string{
		"_csrf": csrf.GetCSRF(),
		"track": trackDataTrack,
		"user":  "usera",
	}

	spew.Dump(opts)

	req = NewRequestWithValues(t, "POST", urlDelete, opts)
	resp = session.MakeRequest(t, req, http.StatusOK)
}

func TestUploadTrack(t *testing.T) {
	Convey("Test Login User A and creating public album", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		trackName := "Test public track name 1"
		trackDesc := "Test public track description 1"

		resp := createTrack(trackName, trackDesc, true, true, 0, 0, t, session)

		// Test list
		req := NewRequest(t, "GET", "/t/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, trackName)
		So(string(resp.Body), ShouldContainSubstring, "Please wait, song metadatas are processing...")
		So(string(resp.Body), ShouldNotContainSubstring, "Error ! Please see track page for information.")

		// Now delete the track
		deleteTrack(resp.Body, t, session)
	})
}

func TestProcessTrack(t *testing.T) {
	Convey("Test Login User A and creating public album", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		trackName := "Test public track name 2"
		trackDesc := "Test public track description 2"

		resp := createTrack(trackName, trackDesc, true, true, 0, 0, t, session)

		workers.TranscodingWatchdog()
		workers.TranscodeAndFetchInfos(2)

		req := NewRequest(t, "GET", "/t/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, trackName)
		So(string(resp.Body), ShouldContainSubstring, slug.Make(trackName)+"/waveform")
		So(string(resp.Body), ShouldNotContainSubstring, "Please wait, song metadatas are processing...")
		So(string(resp.Body), ShouldNotContainSubstring, "Error ! Please see track page for information.")

		// Now delete the track
		deleteTrack(resp.Body, t, session)
	})
}
