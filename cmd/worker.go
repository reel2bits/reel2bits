package cmd

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/mailer"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"dev.sigpipe.me/dashie/reel2bits/workers"
	log "github.com/sirupsen/logrus"
	"github.com/urfave/cli"
	"os"
)

// Worker cli target
var Worker = cli.Command{
	Name:        "worker",
	Usage:       "Start workers",
	Description: "It starts the reel2bits workers",
	Action:      runWorker,
	Flags: []cli.Flag{
		stringFlag("config, c", "config/app.ini", "Custom config file path"),
	},
}

func checkAudiowaveformBinary() (err error) {
	if _, err := os.Stat(setting.AudiowaveformBin); os.IsNotExist(err) {
		log.WithFields(log.Fields{"path": setting.AudiowaveformBin}).Errorf("Audiowaveform binary doesn't exist at specified path")
		log.Info("Check for Audiowaveform config in settings file")
		log.Info("Or see the README to make sure that Audiowaveform is correctly installed")
		return err
	}
	return nil
}

func runWorker(ctx *cli.Context) error {
	if ctx.IsSet("config") {
		setting.CustomConf = ctx.String("config")
	}

	setting.InitConfig()
	models.InitDb()
	mailer.NewContext()

	err := checkAudiowaveformBinary()
	if err != nil {
		log.Errorf("Error checking for audiowaveform binary: %v", err)
		return err
	}

	server, err := workers.CreateServer()
	if err != nil {
		return err
	}

	worker := server.NewWorker("transcoding_infos", 0)
	err = worker.Launch()
	if err != nil {
		log.Errorf("Launching worker transcoding_infos error: %s", err)
		return err
	}

	return nil
}
