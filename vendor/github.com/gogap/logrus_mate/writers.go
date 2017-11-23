package logrus_mate

import (
	"errors"
	"io"
	"sort"
	"sync"
)

var (
	writersLocker  = sync.Mutex{}
	newWriterFuncs = make(map[string]NewWriterFunc)
)

var (
	errWriterNotRegistered = errors.New("writer not registerd")
)

type NewWriterFunc func(Configuration) (writer io.Writer, err error)

func RegisterWriter(name string, newWriterFunc NewWriterFunc) {
	writersLocker.Lock()
	writersLocker.Unlock()

	if name == "" {
		panic("logurs mate: Register writer name is empty")
	}

	if newWriterFunc == nil {
		panic("logurs mate: Register writer is nil")
	}

	if _, exist := newWriterFuncs[name]; exist {
		panic("logurs mate: Register called twice for writer " + name)
	}

	newWriterFuncs[name] = newWriterFunc
}

func Writers() []string {
	writersLocker.Lock()
	defer writersLocker.Unlock()
	var list []string
	for name := range newWriterFuncs {
		list = append(list, name)
	}
	sort.Strings(list)
	return list
}

func NewWriter(name string, config Configuration) (writer io.Writer, err error) {
	writersLocker.Lock()
	defer writersLocker.Unlock()

	if newWriterFunc, exist := newWriterFuncs[name]; !exist {
		err = errWriterNotRegistered
		return
	} else {
		writer, err = newWriterFunc(config)
	}

	return
}
