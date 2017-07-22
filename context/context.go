package context

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/auth"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/go-macaron/cache"
	"github.com/go-macaron/csrf"
	"github.com/go-macaron/i18n"
	"github.com/go-macaron/session"
	log "gopkg.in/clog.v1"
	"gopkg.in/macaron.v1"
	"html/template"
	"io"
	"net/http"
	"strings"
	"time"
)

// Context represents context of a request.
type Context struct {
	*macaron.Context
	Cache   cache.Cache
	csrf    csrf.CSRF
	Flash   *session.Flash
	Session session.Store

	User *models.User // logged in user

	IsLogged    bool
	IsBasicAuth bool
}

// Title sets "Title" field in template data.
func (c *Context) Title(locale string) {
	c.Data["Title"] = c.Tr(locale) + " - " + setting.AppName
}

// PageIs sets "PageIsxxx" field in template data.
func (c *Context) PageIs(name string) {
	c.Data["PageIs"+name] = true
}

// HTML responses template with given status.
func (c *Context) HTML(status int, name string) {
	log.Trace("Template: %s", name)
	c.Context.HTML(status, name)
}

// Success responses template with status http.StatusOK.
func (c *Context) Success(name string) {
	c.HTML(http.StatusOK, name)
}

// JSONSuccess responses JSON with status http.StatusOK.
func (c *Context) JSONSuccess(data interface{}) {
	c.JSON(http.StatusOK, data)
}

// SubURLFor returns AppSubURL + URLFor
func (c *Context) SubURLFor(name string, pairs ...string) string {
	return fmt.Sprintf("%s%s", strings.TrimSuffix(setting.AppSubURL, "/"), c.URLFor(name, pairs...))
}

// HasError returns true if error occurs in form validation.
func (c *Context) HasError() bool {
	hasErr, ok := c.Data["HasError"]
	if !ok {
		return false
	}
	c.Flash.ErrorMsg = c.Data["ErrorMsg"].(string)
	c.Data["Flash"] = c.Flash
	return hasErr.(bool)
}

// RenderWithErr used for page has form validation but need to prompt error to users.
func (c *Context) RenderWithErr(msg, tpl string, f interface{}) {
	if f != nil {
		form.Assign(f, c.Data)
	}
	c.Flash.ErrorMsg = msg
	c.Data["Flash"] = c.Flash
	c.HTML(http.StatusOK, tpl)
}

// Handle handles and logs error by given status.
func (c *Context) Handle(status int, title string, err error) {
	switch status {
	case http.StatusNotFound:
		c.Data["Title"] = c.Tr("error.page_not_found")
	case http.StatusInternalServerError:
		c.Data["Title"] = c.Tr("internal_server_error")
		log.Error(2, "%s: %v", title, err)
	}
	c.HTML(status, fmt.Sprintf("status/%d", status))
}

// HandleText and not unicorns
func (c *Context) HandleText(status int, title string) {
	c.PlainText(status, []byte(title))
}

// NotFound renders the 404 page.
func (c *Context) NotFound() {
	c.Handle(http.StatusNotFound, "", nil)
}

// ServerError renders the 500 page.
func (c *Context) ServerError(title string, err error) {
	c.Handle(http.StatusInternalServerError, title, err)
}

// SubURLRedirect responses redirection wtih given location and status.
// It prepends setting.AppSubURL to the location string.
func (c *Context) SubURLRedirect(location string, status ...int) {
	c.Redirect(setting.AppSubURL + location)
}

// NotFoundOrServerError use error check function to determine if the error
// is about not found. It responses with 404 status code for not found error,
// or error context description for logging purpose of 500 server error.
func (c *Context) NotFoundOrServerError(title string, errck func(error) bool, err error) {
	if errck(err) {
		c.NotFound()
		return
	}
	c.ServerError(title, err)
}

// ServeContent serve contents, right
func (c *Context) ServeContent(name string, r io.ReadSeeker, params ...interface{}) {
	modtime := time.Now()
	for _, p := range params {
		switch v := p.(type) {
		case time.Time:
			modtime = v
		}
	}
	c.Resp.Header().Set("Content-Description", "File Transfer")
	c.Resp.Header().Set("Content-Type", "application/octet-stream")
	c.Resp.Header().Set("Content-Disposition", "attachment; filename="+name)
	c.Resp.Header().Set("Content-Transfer-Encoding", "binary")
	c.Resp.Header().Set("Expires", "0")
	c.Resp.Header().Set("Cache-Control", "must-revalidate")
	c.Resp.Header().Set("Pragma", "public")
	http.ServeContent(c.Resp, c.Req.Request, name, modtime, r)
}

// ServeContentNoDownload no download requested from browser
func (c *Context) ServeContentNoDownload(name string, mime string, r io.ReadSeeker, params ...interface{}) {
	modtime := time.Now()
	for _, p := range params {
		switch v := p.(type) {
		case time.Time:
			modtime = v
		}
	}
	c.Resp.Header().Set("Content-Description", "File Content")
	c.Resp.Header().Set("Content-Type", mime)
	c.Resp.Header().Set("Expires", "0")
	c.Resp.Header().Set("Cache-Control", "must-revalidate")
	c.Resp.Header().Set("Pragma", "public")
	http.ServeContent(c.Resp, c.Req.Request, name, modtime, r)
}

// Contexter initializes a classic context for a request.
func Contexter() macaron.Handler {
	return func(c *macaron.Context, l i18n.Locale, cache cache.Cache, sess session.Store, f *session.Flash, x csrf.CSRF) {
		ctx := &Context{
			Context: c,
			Cache:   cache,
			csrf:    x,
			Flash:   f,
			Session: sess,
		}

		if len(setting.HTTP.AccessControlAllowOrigin) > 0 {
			ctx.Header().Set("Access-Control-Allow-Origin", setting.HTTP.AccessControlAllowOrigin)
			ctx.Header().Set("'Access-Control-Allow-Credentials' ", "true")
			ctx.Header().Set("Access-Control-Max-Age", "3600")
			ctx.Header().Set("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
		}

		// Compute current URL for real-time change language.
		ctx.Data["Link"] = setting.AppSubURL + strings.TrimSuffix(ctx.Req.URL.Path, "/")

		ctx.Data["PageStartTime"] = time.Now()

		// Get user from session if logined.
		ctx.User, ctx.IsBasicAuth = auth.SignedInUser(ctx.Context, ctx.Session)

		if ctx.User != nil {
			ctx.IsLogged = true
			ctx.Data["IsLogged"] = ctx.IsLogged
			ctx.Data["UserIsAdmin"] = ctx.User.IsAdmin
			ctx.Data["LoggedUser"] = ctx.User
			ctx.Data["LoggedUserID"] = ctx.User.ID
			ctx.Data["LoggedUserName"] = ctx.User.UserName
		} else {
			ctx.IsLogged = false
			ctx.Data["IsLogged"] = ctx.IsLogged
			ctx.Data["LoggedUserID"] = 0
			ctx.Data["LoggedUserName"] = ""
		}

		ctx.Data["CSRFToken"] = x.GetToken()
		ctx.Data["CSRFTokenHTML"] = template.HTML(`<input type="hidden" name="_csrf" value="` + x.GetToken() + `">`)
		log.Trace("Session ID: %s", sess.ID())
		log.Trace("CSRF Token: %v", ctx.Data["CSRFToken"])

		c.Map(ctx)
	}
}
