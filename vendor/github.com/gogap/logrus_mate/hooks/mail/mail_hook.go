package mail

import (
	"github.com/sirupsen/logrus"
	"github.com/zbindenren/logrus_mail"

	"github.com/gogap/logrus_mate"
)

type MailHookConfig struct {
	AppName  string
	Host     string
	Port     int
	From     string
	To       string
	Username string
	Password string
}

func init() {
	logrus_mate.RegisterHook("mail", NewMailHook)
}

func NewMailHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	conf := MailHookConfig{}
	if config != nil {
		conf.AppName = config.GetString("app-name")
		conf.Host = config.GetString("host")
		conf.Port = int(config.GetInt32("port"))
		conf.From = config.GetString("from")
		conf.To = config.GetString("to")
		conf.Username = config.GetString("username")
		conf.Password = config.GetString("password")
	}

	hook, err = logrus_mail.NewMailAuthHook(
		conf.AppName,
		conf.Host,
		conf.Port,
		conf.From,
		conf.To,
		conf.Username,
		conf.Password)

	return
}
