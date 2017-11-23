package bugsnag

import (
	"github.com/Shopify/logrus-bugsnag"
	"github.com/sirupsen/logrus"
	"github.com/bugsnag/bugsnag-go"

	"github.com/gogap/logrus_mate"
)

func init() {
	logrus_mate.RegisterHook("bugsnag", NewBugsnagHook)
}

func NewBugsnagHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {

	if config != nil {
		bugsnag.Configure(
			bugsnag.Configuration{
				Endpoint:     config.GetString("endpoint"),
				ReleaseStage: config.GetString("release-stage"),
				APIKey:       config.GetString("api-key"),
				Synchronous:  config.GetBoolean("synchronous"),
			})
	}

	hook, err = logrus_bugsnag.NewBugsnagHook()
	return
}
