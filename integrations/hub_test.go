package integrations

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/Unknwon/i18n"
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)

func TestHome(t *testing.T) {
	Convey("Test Home page", t, func() {
		prepareTestEnv(t)

		req := NewRequest(t, "GET", "/")
		resp := MakeRequest(t, req, http.StatusOK)

		title := fmt.Sprintf("<title>%s - %s</title>", i18n.Tr("en", "app.home_title"), setting.AppName)

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
