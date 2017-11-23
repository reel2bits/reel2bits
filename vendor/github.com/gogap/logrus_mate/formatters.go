package logrus_mate

import (
	"errors"
	"sort"
	"sync"

	"github.com/sirupsen/logrus"
)

var (
	formattersLocker  = sync.Mutex{}
	newFormatterFuncs = make(map[string]NewFormatterFunc)
)

var (
	errFormatterNotRegistered = errors.New("formatter not registerd")
)

type NewFormatterFunc func(Configuration) (formatter logrus.Formatter, err error)

func RegisterFormatter(name string, newFormatterFunc NewFormatterFunc) {
	formattersLocker.Lock()
	formattersLocker.Unlock()

	if name == "" {
		panic("logurs mate: Register formatter name is empty")
	}

	if newFormatterFunc == nil {
		panic("logurs mate: Register formatter is nil")
	}

	if _, exist := newFormatterFuncs[name]; exist {
		panic("logurs mate: Register called twice for formatter " + name)
	}

	newFormatterFuncs[name] = newFormatterFunc
}

func Formatters() []string {
	formattersLocker.Lock()
	defer formattersLocker.Unlock()
	var list []string
	for name := range newFormatterFuncs {
		list = append(list, name)
	}
	sort.Strings(list)
	return list
}

func NewFormatter(name string, config Configuration) (formatter logrus.Formatter, err error) {
	formattersLocker.Lock()
	defer formattersLocker.Unlock()

	if newFormatterFunc, exist := newFormatterFuncs[name]; !exist {
		err = errFormatterNotRegistered
		return
	} else {
		formatter, err = newFormatterFunc(config)
	}

	return
}

func prefixFieldClashes(data logrus.Fields) {
	if t, ok := data["time"]; ok {
		data["fields.time"] = t
	}

	if m, ok := data["msg"]; ok {
		data["fields.msg"] = m
	}

	if l, ok := data["level"]; ok {
		data["fields.level"] = l
	}
}
