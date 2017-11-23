package logrus_file

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/sirupsen/logrus"
	"github.com/gogap/logrus_mate"

	"github.com/gogap/logrus_mate/hooks/utils/caller"
)

func init() {
	logrus_mate.RegisterHook("file", NewFileHook)
}

func NewFileHook(config logrus_mate.Configuration) (hook logrus.Hook, err error) {

	conf := FileLogConifg{}

	if config != nil {
		conf.Filename = config.GetString("filename")
		conf.Maxlines = int(config.GetInt64("max-lines"))
		conf.Maxsize = int(config.GetInt64("max-size"))
		conf.Daily = config.GetBoolean("daily")
		conf.Maxdays = config.GetInt64("max-days")
		conf.Rotate = config.GetBoolean("rotate")
		conf.Level = int(config.GetInt32("level"))
	}

	path := strings.Split(conf.Filename, "/")
	if len(path) > 1 {
		exec.Command("mkdir", path[0]).Run()
	}

	w := NewFileWriter()

	if err = w.Init(conf); err != nil {
		return
	}

	w.SetPrefix("[-] ")

	hook = &FileHook{W: w}

	return
}

type FileHook struct {
	W *FileLogWriter
}

func (p *FileHook) Fire(entry *logrus.Entry) (err error) {
	message, err := getMessage(entry)

	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to read entry, %v", err)
		return err
	}
	switch entry.Level {
	case logrus.PanicLevel:
		fallthrough
	case logrus.FatalLevel:
		fallthrough
	case logrus.ErrorLevel:
		return p.W.WriteMsg(fmt.Sprintf("[ERROR] %s", message), LevelError)
	case logrus.WarnLevel:
		return p.W.WriteMsg(fmt.Sprintf("[WARN] %s", message), LevelWarn)
	case logrus.InfoLevel:
		return p.W.WriteMsg(fmt.Sprintf("[INFO] %s", message), LevelInfo)
	case logrus.DebugLevel:
		return p.W.WriteMsg(fmt.Sprintf("[DEBUG] %s", message), LevelDebug)
	default:
		return nil
	}

	return
}

func (p *FileHook) Levels() []logrus.Level {
	return []logrus.Level{
		logrus.PanicLevel,
		logrus.FatalLevel,
		logrus.ErrorLevel,
		logrus.WarnLevel,
		logrus.InfoLevel,
		logrus.DebugLevel,
	}
}

func getMessage(entry *logrus.Entry) (message string, err error) {
	message = message + fmt.Sprintf("%s\n", entry.Message)
	for k, v := range entry.Data {
		if !strings.HasPrefix(k, "err_") {
			message = message + fmt.Sprintf("%v:%v\n", k, v)
		}
	}
	if errCode, exist := entry.Data["err_code"]; exist {

		ns, _ := entry.Data["err_ns"]
		ctx, _ := entry.Data["err_ctx"]
		id, _ := entry.Data["err_id"]
		tSt, _ := entry.Data["err_stack"]
		st, _ := tSt.(string)
		st = strings.Replace(st, "\n", "\n\t\t", -1)

		buf := bytes.NewBuffer(nil)
		buf.WriteString(fmt.Sprintf("\tid:\n\t\t%s#%d:%s\n", ns, errCode, id))
		buf.WriteString(fmt.Sprintf("\tcontext:\n\t\t%s\n", ctx))
		buf.WriteString(fmt.Sprintf("\tstacktrace:\n\t\t%s", st))

		message = message + fmt.Sprintf("%v", buf.String())
	} else {
		file, lineNumber := caller.GetCallerIgnoringLogMulti(2)
		if file != "" {
			sep := fmt.Sprintf("%s/src/", os.Getenv("GOPATH"))
			fileName := strings.Split(file, sep)
			if len(fileName) >= 2 {
				file = fileName[1]
			}
		}
		message = message + fmt.Sprintf("%s:%d", file, lineNumber)
	}

	return
}
