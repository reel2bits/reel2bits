package i18n

import (
	"net/http"
	"net/http/httptest"
	"testing"

	. "github.com/smartystreets/goconvey/convey"
	"gopkg.in/macaron.v1"
)

func Test_Version(t *testing.T) {
	Convey("Check package version", t, func() {
		So(Version(), ShouldEqual, _VERSION)
	})
}

func Test_I18n(t *testing.T) {
	Convey("Use i18n middleware", t, func() {
		Convey("No langauge", func() {
			defer func() {
				So(recover(), ShouldBeNil)
			}()

			m := macaron.New()
			m.Use(I18n())
		})

		Convey("Languages and names not match", func() {
			defer func() {
				So(recover(), ShouldBeNil)
			}()

			m := macaron.New()
			m.Use(I18n(Options{
				Domain: "messages",
			}))
		})

		Convey("Invalid directory", func() {
			defer func() {
				So(recover(), ShouldBeNil)
			}()

			m := macaron.New()
			m.Use(I18n(Options{
				Directory: "404",
			}))
		})

		Convey("With correct options", func() {
			m := macaron.Classic()
			m.Use(I18n())

			m.Get("/foobar", func() {
			})

			resp := httptest.NewRecorder()
			req, err := http.NewRequest("GET", "/foobar", nil)
			So(err, ShouldBeNil)
			m.ServeHTTP(resp, req)
		})

		Convey("Set by redirect of URL parameter", func() {
			m := macaron.Classic()
			m.Use(I18n(Options{Parameter: "lang"}))
			m.Get("/foobar", func() {
			})

			resp := httptest.NewRecorder()
			req, err := http.NewRequest("GET", "/foobar?lang=en-us", nil)
			So(err, ShouldBeNil)
			req.RequestURI = "/foobar?lang=en-us"
			m.ServeHTTP(resp, req)
		})

		Convey("Set by Accept-Language", func() {
			m := macaron.Classic()
			m.Use(I18n(Options{}))
			m.Get("/foobar", func(l Locale) {
				So(l.Lang, ShouldEqual, "en-us")
			})

			resp := httptest.NewRecorder()
			req, err := http.NewRequest("GET", "/foobar", nil)
			So(err, ShouldBeNil)
			req.Header.Set("Accept-Language", "en-US")
			m.ServeHTTP(resp, req)
		})
	})
}
