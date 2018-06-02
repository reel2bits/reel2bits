// Copyright 2017 The Gitea Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

// /!\ Warning /!\
// While the rest of the app does use URLFor from Macaron Context
// We don't use it in the integration test
// Maybe we can manage to add it but for now, reflect any URL change to the integrations
// tips: use some syntax like in a comment: "// URLName: XXXHERE" if the route is defined with ".Name("XXXHERE")"
//       to search easily a route to change or whatever.
// /!\ Warning /!\

package integrations

import (
	"bytes"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/routes"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"encoding/json"
	"fmt"
	"github.com/go-testfixtures/testfixtures"
	"github.com/stretchr/testify/assert"
	"gopkg.in/macaron.v1"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"strings"
	"testing"
)

var mac *macaron.Macaron

func TestMain(m *testing.M) {
	initIntegrationTest()
	mac = routes.NewMacaron()
	routes.RegisterRoutes(mac)

	var helper testfixtures.Helper
	if setting.UseMySQL {
		helper = &testfixtures.MySQL{}
	} else if setting.UsePostgreSQL {
		helper = &testfixtures.PostgreSQL{}
	} else if setting.UseSQLite3 {
		helper = &testfixtures.SQLite{}
	} else {
		fmt.Println("Unsupported RDBMS for integration tests")
		os.Exit(1)
	}

	appRoot := os.Getenv("APP_ROOT")
	if appRoot == "" {
		fmt.Println("Environment variable $APP_ROOT is not set")
		os.Exit(1)
	}

	err := models.InitFixtures(helper, path.Join(appRoot, "models/fixtures/"))
	if err != nil {
		fmt.Printf("Error initializing test database: %v\n", err)
		os.Exit(1)
	}
	os.Exit(m.Run())
}

func initIntegrationTest() {
	appRoot := os.Getenv("APP_ROOT")
	if appRoot == "" {
		fmt.Println("Environment variable $APP_ROOT is not set")
		os.Exit(1)
	}
	setting.AppPath = path.Join(appRoot, "integrations")

	appConf := os.Getenv("APP_CONF")
	if appConf == "" {
		fmt.Println("Environment variable $APP_CONF is not set")
		os.Exit(1)
	} else if !path.IsAbs(appConf) {
		setting.CustomConf = path.Join(appRoot, appConf)
	} else {
		setting.CustomConf = appConf
	}

	setting.InitConfig()
	models.InitDb()
	routes.GlobalInit()
}

func prepareTestEnv(t testing.TB) {
	assert.NoError(t, models.LoadFixtures())
	assert.NoError(t, os.RemoveAll(setting.Storage.Path))
}

type TestSession struct {
	jar http.CookieJar
}

func (s *TestSession) GetCookie(name string) *http.Cookie {
	baseURL, err := url.Parse(setting.AppURL)
	if err != nil {
		return nil
	}

	for _, c := range s.jar.Cookies(baseURL) {
		if c.Name == name {
			return c
		}
	}
	return nil
}

func (s *TestSession) MakeRequest(t testing.TB, req *http.Request, expectedStatus int) *TestResponse {
	baseURL, err := url.Parse(setting.AppURL)
	assert.NoError(t, err)
	for _, c := range s.jar.Cookies(baseURL) {
		req.AddCookie(c)
	}
	resp := MakeRequest(t, req, expectedStatus)

	ch := http.Header{}
	ch.Add("Cookie", strings.Join(resp.Headers["Set-Cookie"], ";"))
	cr := http.Request{Header: ch}
	s.jar.SetCookies(baseURL, cr.Cookies())

	return resp
}

const userPassword = "password"

var loginSessionCache = make(map[string]*TestSession, 10)

func loginUser(t testing.TB, userName string) *TestSession {
	if session, ok := loginSessionCache[userName]; ok {
		return session
	}
	session := loginUserWithPassword(t, userName, userPassword)
	loginSessionCache[userName] = session
	return session
}

func loginUserWithPassword(t testing.TB, userName, password string) *TestSession {
	req := NewRequest(t, "GET", "/user/login")
	resp := MakeRequest(t, req, http.StatusOK)

	doc := NewHTMLParser(t, resp.Body)
	req = NewRequestWithValues(t, "POST", "/user/login", map[string]string{
		"_csrf":     doc.GetCSRF(),
		"user_name": userName,
		"password":  password,
	})
	resp = MakeRequest(t, req, http.StatusFound)

	ch := http.Header{}
	ch.Add("Cookie", strings.Join(resp.Headers["Set-Cookie"], ";"))
	cr := http.Request{Header: ch}

	jar, err := cookiejar.New(nil)
	assert.NoError(t, err)
	baseURL, err := url.Parse(setting.AppURL)
	assert.NoError(t, err)
	jar.SetCookies(baseURL, cr.Cookies())

	return &TestSession{jar: jar}
}

type TestResponseWriter struct {
	HeaderCode int
	Writer     io.Writer
	Headers    http.Header
}

func (w *TestResponseWriter) Header() http.Header {
	return w.Headers
}

func (w *TestResponseWriter) Write(b []byte) (int, error) {
	return w.Writer.Write(b)
}

func (w *TestResponseWriter) WriteHeader(n int) {
	w.HeaderCode = n
}

type TestResponse struct {
	HeaderCode int
	Body       []byte
	Headers    http.Header
}

func NewRequest(t testing.TB, method, urlStr string) *http.Request {
	return NewRequestWithBody(t, method, urlStr, nil)
}

func NewRequestf(t testing.TB, method, urlFormat string, args ...interface{}) *http.Request {
	return NewRequest(t, method, fmt.Sprintf(urlFormat, args...))
}

func NewRequestWithValues(t testing.TB, method, urlStr string, values map[string]string) *http.Request {
	urlValues := url.Values{}
	for key, value := range values {
		urlValues[key] = []string{value}
	}
	req := NewRequestWithBody(t, method, urlStr, bytes.NewBufferString(urlValues.Encode()))
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	return req
}

func NewRequestWithJSON(t testing.TB, method, urlStr string, v interface{}) *http.Request {
	jsonBytes, err := json.Marshal(v)
	assert.NoError(t, err)
	req := NewRequestWithBody(t, method, urlStr, bytes.NewBuffer(jsonBytes))
	req.Header.Add("Content-Type", "application/json")
	return req
}

func NewRequestWithBody(t testing.TB, method, urlStr string, body io.Reader) *http.Request {
	request, err := http.NewRequest(method, urlStr, body)
	assert.NoError(t, err)
	request.RequestURI = urlStr
	return request
}

func NewRequestWithBodyAndFile(t testing.TB, method, urlStr string, values map[string]string, paramName string, filePath string) *http.Request {
	urlValues := url.Values{}
	for key, value := range values {
		urlValues[key] = []string{value}
	}

	file, err := os.Open(filePath)
	assert.NoError(t, err)
	defer file.Close()

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, err := writer.CreateFormFile(paramName, filepath.Base(filePath))
	assert.NoError(t, err)
	_, err = io.Copy(part, file)

	for key, val := range values {
		_ = writer.WriteField(key, val)
	}
	err = writer.Close()
	assert.NoError(t, err)

	req, err := http.NewRequest(method, urlStr, body)
	assert.NoError(t, err)
	req.RequestURI = urlStr
	req.Header.Set("Content-Type", writer.FormDataContentType())
	return req
}

const NoExpectedStatus = -1

func MakeRequest(t testing.TB, req *http.Request, expectedStatus int) *TestResponse {
	buffer := bytes.NewBuffer(nil)
	respWriter := &TestResponseWriter{
		Writer:  buffer,
		Headers: make(map[string][]string),
	}
	mac.ServeHTTP(respWriter, req)
	if expectedStatus != NoExpectedStatus {
		assert.EqualValues(t, expectedStatus, respWriter.HeaderCode)
	}
	return &TestResponse{
		HeaderCode: respWriter.HeaderCode,
		Body:       buffer.Bytes(),
		Headers:    respWriter.Headers,
	}
}

func DecodeJSON(t testing.TB, resp *TestResponse, v interface{}) {
	decoder := json.NewDecoder(bytes.NewBuffer(resp.Body))
	assert.NoError(t, decoder.Decode(v))
}

func GetCSRF(t testing.TB, session *TestSession, urlStr string) string {
	req := NewRequest(t, "GET", urlStr)
	resp := session.MakeRequest(t, req, http.StatusOK)
	doc := NewHTMLParser(t, resp.Body)
	return doc.GetCSRF()
}

func RedirectURL(t testing.TB, resp *TestResponse) string {
	urlSlice := resp.Headers["Location"]
	assert.NotEmpty(t, urlSlice, "No redirect URL founds")
	return urlSlice[0]
}
