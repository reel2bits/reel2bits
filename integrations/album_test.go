package integrations

import (
	"github.com/gosimple/slug"
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)

// UserA create AlbumA / UserA remove AlbumA
//   Should disappears from /a/usera
//   Should disappears from /

func createAlbum(name string, desc string, public bool, t *testing.T, session *TestSession) (response *TestResponse) {
	req := NewRequest(t, "GET", "/albums/new")
	resp := session.MakeRequest(t, req, http.StatusOK)

	// For CSRF
	doc := NewHTMLParser(t, resp.Body)

	opts := map[string]string{
		"_csrf":       doc.GetCSRF(),
		"name":        name,
		"description": desc,
	}

	if !public {
		opts["is_private"] = "true"
	}

	req = NewRequestWithValues(t, "POST", "/albums/new", opts)
	resp = session.MakeRequest(t, req, http.StatusFound)

	So(resp.HeaderCode, ShouldEqual, 302)

	return resp
}

func TestCreateAlbum(t *testing.T) {
	Convey("Test Login User A and creating public album", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test public album name 1"
		albumDesc := "Test public album description 1"

		resp := createAlbum(albumName, albumDesc, true, t, session)

		// Check for album presence in album list
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Check if visible from / A.K.A The Timeline.
		// should not, since album is empty
		req = NewRequest(t, "GET", "/")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)

		// Check existence of the album from userB on userA album pages
		session = loginUser(t, "userB")
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userB")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Check if visible from / A.K.A The Timeline
		// should not, since album is empty
		req = NewRequest(t, "GET", "/")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userB")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
	})
}

func TestDirectAccessAlbum(t *testing.T) {
	Convey("Test Login User A and creating public album then direct access to it", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test public album name 2"
		albumDesc := "Test public album description 2"

		resp := createAlbum(albumName, albumDesc, true, t, session)

		// Get the URL
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		doc := NewHTMLParser(t, resp.Body)
		url, exists := doc.doc.Find("div.container div.album_single_list div.col-lg-6 a").Attr("href")
		So(exists, ShouldBeTrue)
		So(url, ShouldNotBeEmpty)

		// Make call to album page
		req = NewRequest(t, "GET", url)
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, albumName)
		So(string(resp.Body), ShouldContainSubstring, albumDesc)
		So(string(resp.Body), ShouldContainSubstring, "This album is empty.")
		So(string(resp.Body), ShouldContainSubstring, "si_btn_edit")
		So(string(resp.Body), ShouldContainSubstring, "si_btn_delete")

		// Switch to userB
		session = loginUser(t, "userB")

		// Make call to album page from userB, expected is no access because empty album
		req = NewRequest(t, "GET", url)
		resp = session.MakeRequest(t, req, http.StatusFound)

		var redirectTo = "<a href=\"/\">Found</a>"

		So(resp.HeaderCode, ShouldEqual, 302)
		So(string(resp.Body), ShouldContainSubstring, redirectTo)
	})
}

func TestCreatePrivateAlbum(t *testing.T) {
	Convey("Test Login User A and creating public album", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test private album name 3"
		albumDesc := "Test private album description 3"

		resp := createAlbum(albumName, albumDesc, false, t, session)

		// Check for album presence in album list
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Check if visible from / A.K.A The Timeline.
		// should not, since album is empty and private
		req = NewRequest(t, "GET", "/")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)

		// Check existence of the album from userB on userA album pages
		// It should not, because album is private
		session = loginUser(t, "userB")
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userB")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)

		// Check if visible from / A.K.A The Timeline
		// should not, since album is empty and private
		req = NewRequest(t, "GET", "/")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userB")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
	})
}

func TestCreateAndEditAlbum(t *testing.T) {
	Convey("Test Login User A and creating public album then editing", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test private album name 4"
		albumDesc := "Test private album description 4"

		resp := createAlbum(albumName, albumDesc, false, t, session)

		newAlbumName := "Supertest private album name 4"
		newAlbumDesc := "Supertest private album description 4"

		// Check for album presence in album list
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Get the album URL
		doc := NewHTMLParser(t, resp.Body)
		url, exists := doc.doc.Find("div.container div.album_single_list div.col-lg-6 a").Attr("href")
		So(exists, ShouldBeTrue)
		So(url, ShouldNotBeEmpty)

		// Then edit the album
		// Get CSRF
		req = NewRequest(t, "GET", url+"/edit")
		resp = session.MakeRequest(t, req, http.StatusOK)
		csrf := NewHTMLParser(t, resp.Body)

		opts := map[string]string{
			"_csrf":       csrf.GetCSRF(),
			"name":        newAlbumName,
			"description": newAlbumDesc,
		}

		req = NewRequestWithValues(t, "POST", url+"/edit", opts)
		resp = session.MakeRequest(t, req, http.StatusFound)

		So(resp.HeaderCode, ShouldEqual, 302)

		// Request again the album page and check new values
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
		So(string(resp.Body), ShouldContainSubstring, newAlbumName)

		// And direct access
		// Get new URL
		doc = NewHTMLParser(t, resp.Body)
		url, exists = doc.doc.Find("div.container div.album_single_list div.col-lg-6 a").Attr("href")
		So(exists, ShouldBeTrue)
		So(url, ShouldNotBeEmpty)

		req = NewRequest(t, "GET", url)
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
		So(string(resp.Body), ShouldNotContainSubstring, albumDesc)
		So(string(resp.Body), ShouldContainSubstring, newAlbumName)
		So(string(resp.Body), ShouldContainSubstring, newAlbumDesc)
	})
}

func TestAlbumPublicThenPrivate(t *testing.T) {
	Convey("Test Login User A and creating public album then editing", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test public album name 5"
		albumDesc := "Test public album description 5"

		resp := createAlbum(albumName, albumDesc, true, t, session)

		// Check for album presence in album list
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Get the album URL
		doc := NewHTMLParser(t, resp.Body)
		url, exists := doc.doc.Find("div.container div.album_single_list div.col-lg-6 a").Attr("href")
		So(exists, ShouldBeTrue)
		So(url, ShouldNotBeEmpty)

		// Then edit to switch private
		// Get CSRF
		req = NewRequest(t, "GET", url+"/edit")
		resp = session.MakeRequest(t, req, http.StatusOK)
		csrf := NewHTMLParser(t, resp.Body)

		opts := map[string]string{
			"_csrf":       csrf.GetCSRF(),
			"name":        albumName,
			"description": albumDesc,
			"is_private":  "true",
		}

		req = NewRequestWithValues(t, "POST", url+"/edit", opts)
		resp = session.MakeRequest(t, req, http.StatusFound)

		So(resp.HeaderCode, ShouldEqual, 302)

		// Now try to list
		// Check for album presence in album list
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// From userB
		// Check existence of the album from userB on userA album pages
		// It should not, because album is private
		session = loginUser(t, "userB")
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userB")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
	})
}

func TestAlbumDelete(t *testing.T) {
	Convey("Test Login User A and creating public album then editing", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		albumName := "Test public album name 6"
		albumDesc := "Test public album description 6"

		resp := createAlbum(albumName, albumDesc, true, t, session)

		// Check for album presence in album list
		req := NewRequest(t, "GET", resp.Headers.Get("Location"))
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldContainSubstring, albumName)

		// Get the album URL
		doc := NewHTMLParser(t, resp.Body)
		url, exists := doc.doc.Find("div.container div.album_single_list div.col-lg-6 a").Attr("href")
		So(exists, ShouldBeTrue)
		So(url, ShouldNotBeEmpty)

		// Delete it
		// Get CSRF
		req = NewRequest(t, "GET", url+"/edit")
		resp = session.MakeRequest(t, req, http.StatusOK)
		csrf := NewHTMLParser(t, resp.Body)

		opts := map[string]string{
			"_csrf": csrf.GetCSRF(),
			"album": slug.Make(albumName),
			"user":  "usera",
		}

		req = NewRequestWithValues(t, "POST", url+"/delete", opts)
		resp = session.MakeRequest(t, req, http.StatusOK)

		// Test list
		req = NewRequest(t, "GET", "/a/usera")
		resp = session.MakeRequest(t, req, http.StatusOK)

		So(string(resp.Body), ShouldContainSubstring, "Logged in as userA")
		So(string(resp.Body), ShouldNotContainSubstring, albumName)
	})
}
