package context

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"github.com/go-macaron/csrf"
	log "github.com/sirupsen/logrus"
	"gopkg.in/macaron.v1"
	"net/url"
)

// ToggleOptions struct used with Toggle
type ToggleOptions struct {
	SignInRequired  bool
	SignOutRequired bool
	AdminRequired   bool
	DisableCSRF     bool
}

// Toggle is used to switch some options before the request arrives in the router
func Toggle(options *ToggleOptions) macaron.Handler {
	return func(ctx *Context) {
		// Redirect non-login pages from logged in user
		if options.SignOutRequired && ctx.IsLogged && ctx.Req.RequestURI != "/" {
			ctx.SubURLRedirect(ctx.URLFor("home"))
			return
		}

		log.Debugf("SignOutRequired: %s, DisableCSRF: %s, Req Method: %s", options.SignOutRequired, options.DisableCSRF, ctx.Req.Method)
		if !options.SignOutRequired && !options.DisableCSRF && ctx.Req.Method == "POST" {
			log.Debug("Validating CSRF")
			csrf.Validate(ctx.Context, ctx.csrf)
			if ctx.Written() {
				return
			}
		}

		if options.SignInRequired {
			if !ctx.IsLogged {
				ctx.SetCookie("redirect_to", url.QueryEscape(setting.AppSubURL+ctx.Req.RequestURI), 0, setting.AppSubURL)
				ctx.SubURLRedirect(ctx.URLFor("user_login")) // maybe not need appsuburl
				return
			} else if !ctx.User.IsActive() {
				ctx.Title("auth.activate_your_account")
				ctx.HTML(200, "user/auth/activate")
				return
			}
		}

		// Redirect to login page if auto-sign provided and not signed in
		if !options.SignOutRequired && !ctx.IsLogged && len(ctx.GetCookie(setting.CookieUserName)) > 0 {
			ctx.SetCookie("redirect_to", url.QueryEscape(setting.AppSubURL+ctx.Req.RequestURI), 0, setting.AppSubURL)
			ctx.SubURLRedirect(ctx.URLFor("user_login")) // maybe not need appsuburl
			return
		}

		if options.AdminRequired {
			if !ctx.User.IsAdmin() {
				ctx.Error(403)
				return
			}
			ctx.Data["PageIsAdmin"] = true
		}
	}
}
