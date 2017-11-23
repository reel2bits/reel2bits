package logstash

import (
	"github.com/sirupsen/logrus"
	"github.com/bshuster-repo/logrus-logstash-hook"
	"github.com/gogap/logrus_mate"
)

type LogstashHookConfig struct {
	AppName          string
	Protocol         string
	Address          string
	AlwaysSentFields logrus.Fields
	Prefix           string
}

func init() {
	logrus_mate.RegisterHook("logstash", NewLogstashHook)
}

func NewLogstashHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	conf := LogstashHookConfig{}

	if config != nil {
		conf.AppName = config.GetString("app-name")
		conf.Protocol = config.GetString("protocol")
		conf.Address = config.GetString("address")
		conf.Prefix = config.GetString("prefix")

		alwaysSentFieldsConf := config.GetConfig("always-sent-fields")
		keys := alwaysSentFieldsConf.Keys()
		fields := make(logrus.Fields, len(keys))

		for i := 0; i < len(keys); i++ {
			fields[keys[i]] = alwaysSentFieldsConf.GetString(keys[i])
		}

		conf.AlwaysSentFields = fields
	}

	hook, err = logrus_logstash.NewHookWithFieldsAndPrefix(
		conf.Protocol,
		conf.Address,
		conf.AppName,
		conf.AlwaysSentFields,
		conf.Prefix,
	)

	return
}
