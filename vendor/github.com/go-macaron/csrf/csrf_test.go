// Copyright 2013 Martini Authors
// Copyright 2014 The Macaron Authors
//
// Licensed under the Apache License, Version 2.0 (the "License"): you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

package csrf

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/Unknwon/com"
	"github.com/go-macaron/session"
	. "github.com/smartystreets/goconvey/convey"
	"gopkg.in/macaron.v1"
)

func Test_Version(t *testing.T) {
	Convey("Check package version", t, func() {
		So(Version(), ShouldEqual, _VERSION)
	})
}

func Test_GenerateToken(t *testing.T) {
	Convey("Generate token", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer())

		// Simulate login.
		m.Get("/login", func(sess session.Store, x CSRF) {
			sess.Set("uid", "123456")
		})

		// Generate token.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)
	})
}

func Test_GenerateCookie(t *testing.T) {
	Convey("Generate token to Cookie", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			SetCookie: true,
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", 123456)
		})

		// Generate cookie.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Header().Get("Set-Cookie"), ShouldContainSubstring, "_csrf")
	})

	Convey("Generate token to custom Cookie", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			Cookie:    "custom",
			SetCookie: true,
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", int64(123456))
		})

		// Generate cookie.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Header().Get("Set-Cookie"), ShouldContainSubstring, "custom")
	})
}

func Test_GenerateHeader(t *testing.T) {
	Convey("Generate token to header", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			SetHeader: true,
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", "123456")
		})

		// Generate HTTP header.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Header().Get("X-CSRFToken"), ShouldNotBeEmpty)
	})

	Convey("Generate token to header with origin", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			SetHeader: true,
			Origin:    true,
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", "123456")
		})

		// Generate HTTP header.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		req.Header.Set("Origin", "https://www.example.com")
		m.ServeHTTP(resp, req)

		So(resp.Header().Get("X-CSRFToken"), ShouldBeEmpty)
	})

	Convey("Generate token to custom header", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			Header:    "X-Custom",
			SetHeader: true,
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", "123456")
		})

		// Generate HTTP header.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Header().Get("X-Custom"), ShouldNotBeEmpty)
	})
}

func Test_Validate(t *testing.T) {
	Convey("Validate token", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer())

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", 123456)
		})

		// Generate token.
		m.Get("/private", func(x CSRF) string {
			return x.GetToken()
		})

		m.Post("/private", Validate, func() {})

		// Login to set session.
		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		// Get a new token.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		token := resp.Body.String()

		// Post using _csrf form value.
		data := url.Values{}
		data.Set("_csrf", token)

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", bytes.NewBufferString(data.Encode()))
		So(err, ShouldBeNil)

		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		req.Header.Set("Content-Length", com.ToStr(len(data.Encode())))
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldNotEqual, http.StatusBadRequest)

		// Post using X-CSRFToken HTTP header.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("X-CSRFToken", token)
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldNotEqual, http.StatusBadRequest)
	})

	Convey("Validate custom token", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			Header: "X-Custom",
			Form:   "_custom",
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", 123456)
		})

		// Generate token.
		m.Get("/private", func(x CSRF) string {
			return x.GetToken()
		})

		m.Post("/private", Validate, func() {})

		// Login to set session.
		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		// Get a new token.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		token := resp.Body.String()

		// Post using _csrf form value.
		data := url.Values{}
		data.Set("_custom", token)

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", bytes.NewBufferString(data.Encode()))
		So(err, ShouldBeNil)

		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		req.Header.Set("Content-Length", com.ToStr(len(data.Encode())))
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldNotEqual, http.StatusBadRequest)

		// Post using X-Custom HTTP header.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("X-Custom", token)
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldNotEqual, http.StatusBadRequest)
	})

	Convey("Validate token with custom error func", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer(Options{
			ErrorFunc: func(w http.ResponseWriter) {
				http.Error(w, "custom error", 422)
			},
		}))

		// Simulate login.
		m.Get("/login", func(sess session.Store) {
			sess.Set("uid", 123456)
		})

		// Generate token.
		m.Get("/private", func(x CSRF) string {
			return x.GetToken()
		})

		m.Post("/private", Validate, func() {})

		// Login to set session.
		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		// Get a new token.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		// Post using _csrf form value.
		data := url.Values{}
		data.Set("_csrf", "invalid")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", bytes.NewBufferString(data.Encode()))
		So(err, ShouldBeNil)

		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		req.Header.Set("Content-Length", com.ToStr(len(data.Encode())))
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldEqual, 422)
		So(resp.Body.String(), ShouldEqual, "custom error\n")

		// Post using X-CSRFToken HTTP header.
		resp = httptest.NewRecorder()
		req, err = http.NewRequest("POST", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("X-CSRFToken", "invalid")
		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldEqual, 422)
		So(resp.Body.String(), ShouldEqual, "custom error\n")
	})
}

func Test_Invalid(t *testing.T) {
	Convey("Invalid session data type", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer())

		// Simulate login.
		m.Get("/login", func(sess session.Store, x CSRF) {
			sess.Set("uid", true)
		})

		// Generate token.
		m.Get("/private", func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		cookie := resp.Header().Get("Set-Cookie")

		resp = httptest.NewRecorder()
		req, err = http.NewRequest("GET", "/private", nil)
		So(err, ShouldBeNil)

		req.Header.Set("Cookie", cookie)
		m.ServeHTTP(resp, req)
	})

	Convey("Invalid request", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer())

		// Simulate login.
		m.Get("/login", Validate, func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldEqual, http.StatusBadRequest)
	})

	Convey("Invalid token", t, func() {
		m := macaron.New()
		m.Use(session.Sessioner())
		m.Use(Csrfer())

		// Simulate login.
		m.Get("/login", Validate, func() {})

		resp := httptest.NewRecorder()
		req, err := http.NewRequest("GET", "/login", nil)
		So(err, ShouldBeNil)

		req.Header.Set("X-CSRFToken", "invalid")
		m.ServeHTTP(resp, req)

		So(resp.Code, ShouldEqual, http.StatusBadRequest)
	})
}
