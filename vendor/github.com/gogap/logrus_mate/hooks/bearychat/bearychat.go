package bearychat

import (
	"fmt"

	"github.com/sirupsen/logrus"
	"github.com/gogap/bearychat"
	"github.com/gogap/logrus_mate"
)

var allLevels = []logrus.Level{
	logrus.DebugLevel,
	logrus.InfoLevel,
	logrus.WarnLevel,
	logrus.ErrorLevel,
	logrus.FatalLevel,
	logrus.PanicLevel,
}

type BearyChatHookConfig struct {
	Url      string
	Levels   []string
	Channel  string
	User     string
	Markdown bool
	Async    bool
}

func init() {
	logrus_mate.RegisterHook("bearychat", NewBearyChatHook)
}

func NewBearyChatHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	conf := BearyChatHookConfig{}

	if config != nil {
		conf.Url = config.GetString("url")
		conf.Levels = config.GetStringList("levels")
		conf.Channel = config.GetString("channel")
		conf.User = config.GetString("user")
		conf.Markdown = config.GetBoolean("markdown")
		conf.Async = config.GetBoolean("async", true)
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

	hook = &BearyChatHook{
		Url:            conf.Url,
		AcceptedLevels: levels,
		Channel:        conf.Channel,
		User:           conf.User,
		Markdown:       conf.Markdown,
		Async:          conf.Async,
		cli:            bearychat.NewIncomingClient(),
	}

	return
}

type BearyChatHook struct {
	AcceptedLevels []logrus.Level
	Url            string
	Channel        string
	User           string
	Markdown       bool
	Async          bool

	cli *bearychat.IncomingClient
}

// Levels sets which levels to sent to slack
func (p *BearyChatHook) Levels() []logrus.Level {
	if p.AcceptedLevels == nil {
		return allLevels
	}
	return p.AcceptedLevels
}

// Fire -  Sent event to slack
func (p *BearyChatHook) Fire(e *logrus.Entry) (err error) {
	color := ""
	switch e.Level {
	case logrus.DebugLevel:
		color = "#FDFEFE"
	case logrus.InfoLevel:
		color = "#5DADE2"
	case logrus.ErrorLevel, logrus.FatalLevel, logrus.PanicLevel:
		color = "#FF0000"
	default:
		color = "#FFFF00"
	}

	req := &bearychat.Message{
		Text:     e.Message,
		Markdown: p.Markdown,
		Channel:  p.Channel,
		User:     p.User,
	}

	var attachs []bearychat.Attachment

	if len(e.Data) > 0 {

		for k, v := range e.Data {
			attach := bearychat.Attachment{}

			attach.Title = k
			attach.Text = fmt.Sprint(v)
			attach.Color = color

			attachs = append(attachs, attach)
		}
	}

	req.Attachments = attachs

	if p.Async {
		go p.cli.Send(p.Url, req)
		return
	}

	_, err = p.cli.Send(p.Url, req)
	return
}
