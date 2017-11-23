package expander

import (
	"github.com/gogap/errors"

	"github.com/sirupsen/logrus"
	"github.com/gogap/logrus_mate"
)

type ExpanderHook struct {
}

func init() {
	logrus_mate.RegisterHook("expander", NewExpanderHook)
}

func NewExpanderHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {
	hook = &ExpanderHook{}
	return
}

func (p *ExpanderHook) Fire(entry *logrus.Entry) (err error) {
	if v, exist := entry.Data[logrus.ErrorKey]; exist {
		if errCode, ok := v.(errors.ErrCode); ok {
			entry.Data["err_id"] = errCode.Id()
			entry.Data["err_code"] = errCode.Code()
			entry.Data["err_ns"] = errCode.Namespace()
			entry.Data["err_msg"] = errCode.Error()
			entry.Data["err_stack"] = errCode.StackTrace()
			entry.Data["err_ctx"] = errCode.Context().String()

			delete(entry.Data, logrus.ErrorKey)

			entry.Message = errCode.Error()
		}
	}

	return
}

func (p *ExpanderHook) Levels() []logrus.Level {
	return []logrus.Level{
		logrus.PanicLevel,
		logrus.FatalLevel,
		logrus.ErrorLevel,
		logrus.WarnLevel,
		logrus.InfoLevel,
		logrus.DebugLevel,
	}
}
