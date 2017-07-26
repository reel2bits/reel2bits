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
	"dev.sigpipe.me/dashie/reel2bits/routers/album"
	"dev.sigpipe.me/dashie/reel2bits/routers/track"
	"dev.sigpipe.me/dashie/reel2bits/routers/user"
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

	funcMap := template.NewFuncMap(m)
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
			{
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
	m.Get("/", routers.Home).Name("home")

	// START USER
	m.Group("/user", func() {
		m.Combo("/login").Get(user.Login).Post(bindIgnErr(form.Login{}), user.LoginPost).Name("user_login")
		m.Combo("/register").Get(user.Register).Post(csrf.Validate, bindIgnErr(form.Register{}), user.RegisterPost).Name("user_register")
		m.Combo("/reset_password").Get(user.ResetPasswd).Post(user.ResetPasswdPost).Name("user_reset_passwd")
	}, reqSignOut)

	m.Group("/user/settings", func() {
		m.Combo("").Get(user.Settings).Post(csrf.Validate, bindIgnErr(form.UpdateSettingsProfile{}), user.SettingsPost).Name("user_settings")
	}, reqSignIn, func(ctx *context.Context) {
		ctx.Data["PageIsUserSettings"] = true
	})

	m.Group("/user", func() {
		m.Get("/logout", user.Logout).Name("user_logout")
	}, reqSignIn)

	m.Group("/user", func() {
		m.Combo("/forget_password").Get(user.ForgotPasswd).Post(user.ForgotPasswdPost).Name("user_forget_password")
	})
	// END USER

	// START TRACK
	m.Group("/track/upload", func() {
		m.Combo("").Get(track.Upload).Post(csrf.Validate, bindIgnErr(form.TrackUpload{}), track.UploadPost).Name("track_upload")
	}, reqSignIn)

	m.Get("/t/:userSlug", track.ListUserTracks).Name("track_list")

	m.Group("/t/:userSlug/:trackSlug", func() {
		m.Get("", track.Show).Name("track_show")
		m.Combo("/edit", reqSignIn).Get(track.Edit).Post(csrf.Validate, bindIgnErr(form.TrackEdit{}), track.EditPost).Name("track_edit")
		m.Post("/delete", reqSignIn, csrf.Validate, bindIgnErr(form.TrackDelete{}), track.DeleteTrack).Name("track_delete")
		m.Get(".json", track.GetJSONWaveform).Name("track_infos_json")
		m.Get("/reorder").Name("track_reorder")
	})
	// END TRACK

	// START ALBUM
	m.Group("/albums", func() {
		m.Combo("/new", reqSignIn).Get(album.New).Post(csrf.Validate, bindIgnErr(form.Album{}), album.NewPost).Name("album_new")
	})

	m.Get("/a/:userSlug", album.ListFromUser).Name("album_list")

	m.Group("/a/:userSlug/:albumSlug", func() {
		m.Get("", album.Show).Name("album_show")
		m.Combo("/edit", reqSignIn).Get(album.Edit).Post(csrf.Validate, bindIgnErr(form.Album{}), album.EditPost).Name("album_edit")
		m.Post("/delete", reqSignIn, csrf.Validate, bindIgnErr(form.AlbumDelete{}), album.DeleteAlbum).Name("album_delete")
	})
	// END ALBUM

	// In prod this should be served by Nginx or another reverse proxy for a lot of performances reasons
	m.Group("/medias/track/:userSlug/:trackSlug", func() {
		m.Get("/stream/:type", track.DevGetMediaTrack).Name("media_track_stream")
		m.Get("/download/:type", track.DevGetMediaDownload).Name("media_track_download")
		m.Get("/waveform", track.DevGetMediaPngWf).Name("media_track_waveform")
	})
	/* Admin part */

	m.Group("/admin", func() {
		m.Get("", adminReq, admin.Dashboard).Name("admin_dashboard")
	}, adminReq)

	if setting.NeedsImpressum {
		m.Get("/impressum", routers.Impressum).Name("impressum")
	}

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
		listener, err = net.ListenUnix("unix", &net.UnixAddr{Name: listenAddr, Net: "unix"})
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
