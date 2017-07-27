package integrations

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/Unknwon/i18n"
	. "github.com/smartystreets/goconvey/convey"
	"net/http"
	"testing"
)

func TestLogin(t *testing.T) {
	Convey("Test Login User A and access to settings page", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		// then test settings page
		req := NewRequest(t, "GET", "/user/settings")
		resp := session.MakeRequest(t, req, http.StatusOK)

		title := fmt.Sprintf("<title>%s - %s</title>", i18n.Tr("en", "settings.title"), setting.AppName)

		So(string(resp.Body), ShouldContainSubstring, title)
		So(string(resp.Body), ShouldContainSubstring, "userA")
	})
}

func TestLogout(t *testing.T) {
	Convey("Test Login User A and then logout", t, func() {
		prepareTestEnv(t)

		session := loginUser(t, "userA")

		req := NewRequest(t, "GET", "/user/logout")
		resp := session.MakeRequest(t, req, http.StatusFound)

		var found = "<a href=\"/\">Found</a>"

		So(string(resp.Body), ShouldContainSubstring, found)
	})
}

func TestRegister(t *testing.T) {
	Convey("Test register user C", t, func() {
		prepareTestEnv(t)

		req := NewRequest(t, "GET", "/user/register")
		resp := MakeRequest(t, req, http.StatusOK)

		// For CSRF
		doc := NewHTMLParser(t, resp.Body)

		// Register
		req = NewRequestWithValues(t, "POST", "/user/register", map[string]string{
			"_csrf":     doc.GetCSRF(),
			"user_name": "userC",
			"email":     "userc@example.com",
			"password":  "password",
			"repeat":    "password",
		})
		MakeRequest(t, req, http.StatusFound)

		// Login
		session := loginUser(t, "userC")

		// then test settings page
		req = NewRequest(t, "GET", "/user/settings")
		resp = session.MakeRequest(t, req, http.StatusOK)

		title := fmt.Sprintf("<title>%s - %s</title>", i18n.Tr("en", "settings.title"), setting.AppName)

		So(string(resp.Body), ShouldContainSubstring, title)
		So(string(resp.Body), ShouldContainSubstring, "userC")
	})
}
