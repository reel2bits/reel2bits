package logrus_mate

import (
	"github.com/sirupsen/logrus"
)

type JSONFormatterConfig struct {
	TimestampFormat string `json:"timestamp_format"`
}

func init() {
	RegisterFormatter("json", NewJSONFormatter)
}

func NewJSONFormatter(config Configuration) (formatter logrus.Formatter, err error) {
	var format string
	if config != nil {
		format = config.GetString("timestamp_format")
	}
	formatter = &logrus.JSONFormatter{TimestampFormat: format}
	return
}
