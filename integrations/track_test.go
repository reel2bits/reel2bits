package integrations

import (
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)


func TestUploadTrack(t *testing.T) {
	Convey("Test Login User A and creating public album", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		trackName := "Test public track name 1"
		trackDesc := "Test public track description 1"

		// Get CSRF
		req := NewRequest(t, "GET", "/track/upload")
		resp := session.MakeRequest(t, req, http.StatusOK)
		csrf := NewHTMLParser(t, resp.Body)

		opts := map[string]string{
			"_csrf": csrf.GetCSRF(),
			"title": trackName,
			"description":  trackDesc,
			"album": "0",
			"licence": "0",
			"is_private": "",
			"show_dl_link": "true",
		}

		req = NewRequestWithBodyAndFile(t, "POST", "/track/upload", opts, "file", "integrations/STE-013.mp3")
		resp = session.MakeRequest(t, req, http.StatusFound)

		So(resp.Headers.Get("Location"), ShouldContainSubstring, "/t/usera")

		// Test list
		req = NewRequest(t, "GET", "/t/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, trackName)
		So(string(resp.Body), ShouldContainSubstring, "Please wait, song metadatas are processing...")
		So(string(resp.Body), ShouldNotContainSubstring, "Error ! Please see track page for information.")

	})
}
