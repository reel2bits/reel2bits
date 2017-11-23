package graylog

import (
	"github.com/sirupsen/logrus"
	"gopkg.in/gemnasium/logrus-graylog-hook.v2"

	"github.com/gogap/logrus_mate"
)

type GraylogHookConfig struct {
	Address string
	Extra   map[string]interface{}
}

func init() {
	logrus_mate.RegisterHook("graylog", NewGraylogHook)
}

func NewGraylogHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	conf := GraylogHookConfig{}

	if config != nil {
		conf.Address = config.GetString("address")

		extraConf := config.GetConfig("extra")

		if extraConf != nil {
			keys := extraConf.Keys()
			extra := make(map[string]interface{}, len(keys))

			for i := 0; i < len(keys); i++ {
				extra[keys[i]] = extraConf.GetString(keys[i])
			}

			conf.Extra = extra
		}
	}

	hook = graylog.NewAsyncGraylogHook(
		conf.Address,
		conf.Extra)

	return
}
