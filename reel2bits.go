package main

import (
	"dev.sigpipe.me/dashie/reel2bits/cmd"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/getsentry/raven-go"
	"github.com/urfave/cli"
	"os"
)

// AppVersion is... guess what ?
const AppVersion = "0.2"

func init() {
	setting.AppVer = AppVersion
	if os.Getenv("USE_RAVEN") == "true" {
		raven.SetDSN(os.Getenv("RAVEN_DSN"))
		setting.UseRaven = true
		fmt.Printf("Using Raven with DSN: %s\r\n", os.Getenv("RAVEN_DSN"))
	} else {
		setting.UseRaven = false
		fmt.Println("Running without Raven/Sentry support.")
	}
}

func main() {
	app := cli.NewApp()
	app.Name = "reel2bits"
	app.Usage = "paste stuff to the interweb with git backend"
	app.Version = AppVersion
	app.Commands = []cli.Command{
		cmd.Web,
		cmd.Worker,
	}
	app.Flags = append(app.Flags, []cli.Flag{}...)
	app.Run(os.Args)
}
