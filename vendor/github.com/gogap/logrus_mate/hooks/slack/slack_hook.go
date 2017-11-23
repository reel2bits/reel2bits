package slack

import (
	"github.com/sirupsen/logrus"
	"github.com/johntdyer/slackrus"

	"github.com/gogap/logrus_mate"
)

type SlackHookConfig struct {
	URL      string
	Levels   []string
	Channel  string
	Emoji    string
	Username string
}

func init() {
	logrus_mate.RegisterHook("slack", NewSlackHook)
}

func NewSlackHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	conf := SlackHookConfig{}

	if config != nil {
		conf.URL = config.GetString("url")
		conf.Levels = config.GetStringList("levels")
		conf.Channel = config.GetString("channel")
		conf.Emoji = config.GetString("emoji")
		conf.Username = config.GetString("username")
	}

	levels := []logrus.Level{}

	if conf.Levels != nil {
		for _, level := range conf.Levels {
			if lv, e := logrus.ParseLevel(level); e != nil {
				err = e
				return
			} else {
				levels = append(levels, lv)
			}
		}
	}

	if len(levels) == 0 && conf.Levels != nil {
		levels = append(levels, logrus.ErrorLevel, logrus.PanicLevel, logrus.FatalLevel)
	}

	hook = &slackrus.SlackrusHook{
		HookURL:        conf.URL,
		AcceptedLevels: levels,
		Channel:        conf.Channel,
		IconEmoji:      conf.Emoji,
		Username:       conf.Username,
	}

	return
}
