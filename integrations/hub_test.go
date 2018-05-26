package integrations

import (
	"fmt"
	"github.com/leonelquinteros/gotext"
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)

func TestHome(t *testing.T) {
	Convey("Test Home page", t, func() {
		prepareTestEnv(t)

		req := NewRequest(t, "GET", "/")
		resp := MakeRequest(t, req, http.StatusOK)

		title := fmt.Sprintf("<title>%s - reel2bits</title>", gotext.Get("Home Page"))

		So(string(resp.Body), ShouldContainSubstring, title)
	})
}

func TestImpressum(t *testing.T) {
	Convey("Test Impressum not enabled", t, func() {
		// disabled by default
		prepareTestEnv(t)

		req := NewRequest(t, "GET", "/impressum")
		resp := MakeRequest(t, req, http.StatusNotFound)

		So(resp.HeaderCode, ShouldEqual, 404)
	})
}
