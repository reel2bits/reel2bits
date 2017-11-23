package airbrake

import (
	"github.com/sirupsen/logrus"
	"gopkg.in/gemnasium/logrus-airbrake-hook.v2"

	"github.com/gogap/logrus_mate"
)

type AirbrakeHookConfig struct {
	ProjectId int64
	APIKey    string
	Env       string
}

func init() {
	logrus_mate.RegisterHook("airbrake", NewAirbrakeHook)
}

func NewAirbrakeHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {

	conf := AirbrakeHookConfig{}
	if config != nil {
		conf.ProjectId = config.GetInt64("project-id")
		conf.APIKey = config.GetString("api-key")
		conf.Env = config.GetString("env")
	}

	hook = airbrake.NewHook(
		conf.ProjectId,
		conf.APIKey,
		conf.Env,
	)

	return
}
