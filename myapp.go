package main

import (
	"os"
	"github.com/urfave/cli"
	"dev.sigpipe.me/dashie/reel2bits/cmd"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"github.com/getsentry/raven-go"
	"fmt"
)

const APP_VER = "0.2"

func init() {
	setting.AppVer = APP_VER
	if os.Getenv("USE_RAVEN") == "true" {
		raven.SetDSN(os.Getenv("RAVEN_DSN"))
		fmt.Printf("Using Raven with DSN: %s\r\n", os.Getenv("RAVEN_DSN"))
	} else {
		fmt.Println("Running without Raven/Sentry support.")
	}
}

func main() {
	app := cli.NewApp()
	app.Name = "reel2bits"
	app.Usage = "paste stuff to the interweb with git backend"
	app.Version = APP_VER
	app.Commands = []cli.Command{
		cmd.Web,
	}
	app.Flags = append(app.Flags, []cli.Flag{}...)
	app.Run(os.Args)
}
