package cmd

import (
	"dev.sigpipe.me/dashie/reel2bits/routes"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	log "github.com/sirupsen/logrus"
	"github.com/urfave/cli"
	"net"
	"net/http"
	"net/http/fcgi"
	"os"
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

func runWeb(ctx *cli.Context) error {
	if ctx.IsSet("config") {
		setting.CustomConf = ctx.String("config")
	}

	routes.GlobalInit()

	m := routes.NewMacaron()
	routes.RegisterRoutes(m)

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
