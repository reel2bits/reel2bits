package logrus_mate

import (
	"io"
	"os"
)

func init() {
	RegisterWriter("stdout", NewStdoutWriter)
	RegisterWriter("stderr", NewStderrWriter)
}

func NewStdoutWriter(Configuration) (writer io.Writer, err error) {
	writer = os.Stdout
	return
}

func NewStderrWriter(Configuration) (writer io.Writer, err error) {
	writer = os.Stderr
	return
}
