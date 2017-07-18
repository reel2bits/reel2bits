package cmd

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/cron"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/pkg/mailer"
	"dev.sigpipe.me/dashie/reel2bits/pkg/template"
	"dev.sigpipe.me/dashie/reel2bits/routers"
	"dev.sigpipe.me/dashie/reel2bits/routers/admin"
	"dev.sigpipe.me/dashie/reel2bits/routers/user"
	"dev.sigpipe.me/dashie/reel2bits/routers/track"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/go-macaron/binding"
	"github.com/go-macaron/cache"
	"github.com/go-macaron/csrf"
	"github.com/go-macaron/i18n"
	"github.com/go-macaron/session"
	"github.com/go-macaron/toolbox"
	"github.com/urfave/cli"
	log "gopkg.in/clog.v1"
	"gopkg.in/macaron.v1"
	"net"
	"net/http"
	"net/http/fcgi"
	"os"
	"path"
	"strings"
)

// Web cli target
var Web = cli.Command{
	Name:        "web",
	Usage:       "Start web server",
	Description: "It starts a web server, great no ?",
	Action:      runWeb,
	Flags: []cli.Flag{
		stringFlag("port, p", "3000", "Server port"),
		stringFlag("config, c", "config/app.ini", "Custom config file path"),
	},
}

func newMacaron() *macaron.Macaron {
	m := macaron.New()
	if !setting.DisableRouterLog {
		m.Use(macaron.Logger())
	}

	m.Use(macaron.Recovery())

	if setting.Protocol == setting.SchemeFcgi {
		m.SetURLPrefix(setting.AppSubURL)
	}

	m.Use(macaron.Static(
		path.Join(setting.StaticRootPath, "static"),
		macaron.StaticOptions{
			SkipLogging: setting.DisableRouterLog,
		},
	))

	funcMap := template.NewFuncMap()
	m.Use(macaron.Renderer(macaron.RenderOptions{
		Directory:  path.Join(setting.StaticRootPath, "templates"),
		Funcs:      funcMap,
		IndentJSON: macaron.Env != macaron.PROD,
	}))
	mailer.InitMailRender(path.Join(setting.StaticRootPath, "templates/mail"), funcMap)

	m.Use(i18n.I18n(i18n.Options{
		SubURL: setting.AppSubURL,
		//Files:           localFiles,
		Langs:       setting.Langs,
		Names:       setting.Names,
		DefaultLang: "en-US",
		Redirect:    true,
	}))

	m.Use(cache.Cacher(cache.Options{
		Adapter:       setting.CacheAdapter,
		AdapterConfig: setting.CacheConn,
		Interval:      setting.CacheInterval,
	}))

	m.Use(session.Sessioner(setting.SessionConfig))

	m.Use(csrf.Csrfer(csrf.Options{
		Secret:     setting.SecretKey,
		Cookie:     setting.CSRFCookieName,
		SetCookie:  true,
		Header:     "X-Csrf-Token",
		CookiePath: setting.AppSubURL,
	}))

	m.Use(toolbox.Toolboxer(m, toolbox.Options{
		HealthCheckFuncs: []*toolbox.HealthCheckFuncDesc{
			&toolbox.HealthCheckFuncDesc{
				Desc: "Database connection",
				Func: models.Ping,
			},
		},
	}))

	m.Use(context.Contexter())

	return m

}

func runWeb(ctx *cli.Context) error {
	if ctx.IsSet("config") {
		setting.CustomConf = ctx.String("config")
	}

	setting.InitConfig()
	models.InitDb()
	cron.NewContext()
	mailer.NewContext()

	m := newMacaron()

	if setting.ProdMode {
		macaron.Env = macaron.PROD
		macaron.ColorLog = false
	} else {
		macaron.Env = macaron.DEV
	}
	log.Info("Run Mode: %s", strings.Title(macaron.Env))

	reqSignIn := context.Toggle(&context.ToggleOptions{SignInRequired: true})
	reqSignOut := context.Toggle(&context.ToggleOptions{SignOutRequired: true})
	adminReq := context.Toggle(&context.ToggleOptions{SignInRequired: true, AdminRequired: true})
	bindIgnErr := binding.BindIgnErr

	// HOME PAGE
	m.Get("/", routers.Home)

	// START USER
	m.Group("/user", func() {
		m.Group("/login", func() {
			m.Combo("").Get(user.Login).Post(bindIgnErr(form.Login{}), user.LoginPost)
		})
		m.Get("/register", user.Register)
		m.Post("/register", csrf.Validate, bindIgnErr(form.Register{}), user.RegisterPost)
		m.Get("/reset_password", user.ResetPasswd)
		m.Post("/reset_password", user.ResetPasswdPost)
	}, reqSignOut)

	m.Group("/user/settings", func() {
		m.Get("", user.Settings)
		m.Post("", csrf.Validate, bindIgnErr(form.UpdateSettingsProfile{}), user.SettingsPost)
	}, reqSignIn, func(ctx *context.Context) {
		ctx.Data["PageIsUserSettings"] = true
	})

	m.Group("/user", func() {
		m.Get("/logout", user.Logout)
	}, reqSignIn)

	m.Group("/user", func() {
		m.Get("/forget_password", user.ForgotPasswd)
		m.Post("/forget_password", user.ForgotPasswdPost)
	})
	// END USER

	// START TRACK
	m.Group("/track/upload", func() {
		m.Get("", track.Upload)
		m.Post("", csrf.Validate, bindIgnErr(form.TrackUpload{}), track.UploadPost)
	}, reqSignIn)

	m.Get("/u/:userSlug", track.ListUserTracks)
	m.Get("/u/:userSlug/:trackSlug", track.Show)
	m.Get("/u/:userSlug/:trackSlug/edit")
	m.Post("/u/:userSlug/:trackSlug/delete", csrf.Validate, bindIgnErr(form.TrackDelete{}), track.DeleteTrack)
	// END TRACK

	// In prod this should be served by Nginx or another reverse proxy for a lot of performances reasons
	if macaron.Env == macaron.DEV {
		m.Get("/medias/track/stream/:userSlug/:trackSlug", track.DevGetMediaTrack)
		m.Get("/medias/track/download/:userSlug/:trackSlug")
		m.Get("/medias/track/waveform/:userSlug/:trackSlug", track.DevGetMediaPngWf)
	}

	/* Admin part */

	m.Group("/admin", func() {
		m.Get("", adminReq, admin.Dashboard)
	}, adminReq)

	// robots.txt
	m.Get("/robots.txt", func(ctx *context.Context) {
		if setting.HasRobotsTxt {
			ctx.ServeFileContent(setting.RobotsTxtPath)
		} else {
			ctx.Error(404)
		}
	})

	m.NotFound(routers.NotFound)

	if ctx.IsSet("port") {
		setting.AppURL = strings.Replace(setting.AppURL, setting.HTTPPort, ctx.String("port"), 1)
		setting.HTTPPort = ctx.String("port")
	}

	var listenAddr string
	if setting.Protocol == setting.SchemeUnixSocket {
		listenAddr = fmt.Sprintf("%s", setting.HTTPAddr)
	} else {
		listenAddr = fmt.Sprintf("%s:%s", setting.HTTPAddr, setting.HTTPPort)
	}
	log.Info("Listen: %v://%s%s", setting.Protocol, listenAddr, setting.AppSubURL)

	var err error
	switch setting.Protocol {
	case setting.SchemeHTTP:
		err = http.ListenAndServe(listenAddr, m)
	case setting.SchemeHTTPS:
		log.Fatal(2, "https not supported")
	case setting.SchemeFcgi:
		err = fcgi.Serve(nil, m)
	case setting.SchemeUnixSocket:
		os.Remove(listenAddr)

		var listener *net.UnixListener
		listener, err = net.ListenUnix("unix", &net.UnixAddr{listenAddr, "unix"})
		if err != nil {
			break // Handle error after switch
		}

		// FIXME: add proper implementation of signal capture on all protocols
		// execute this on SIGTERM or SIGINT: listener.Close()
		if err = os.Chmod(listenAddr, os.FileMode(setting.UnixSocketPermission)); err != nil {
			log.Fatal(4, "Failed to set permission of unix socket: %v", err)
		}
		err = http.Serve(listener, m)
	default:
		log.Fatal(4, "Invalid protocol: %s", setting.Protocol)
	}

	if err != nil {
		log.Fatal(4, "Fail to start server: %v", err)
	}

	return nil
}
