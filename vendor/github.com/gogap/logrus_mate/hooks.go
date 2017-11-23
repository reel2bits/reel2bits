package logrus_mate

import (
	"errors"
	"sort"
	"sync"

	"github.com/sirupsen/logrus"
)

var (
	hooksLocker  = sync.Mutex{}
	newHookFuncs = make(map[string]NewHookFunc)
)

var (
	errHookNotRegistered = errors.New("logurs mate: hook not registerd")
)

type NewHookFunc func(Configuration) (hook logrus.Hook, err error)

func RegisterHook(name string, newHookFunc NewHookFunc) {
	hooksLocker.Lock()
	hooksLocker.Unlock()

	if name == "" {
		panic("logurs mate: Register hook name is empty")
	}

	if newHookFunc == nil {
		panic("logurs mate: Register hook is nil")
	}

	if _, exist := newHookFuncs[name]; exist {
		panic("logurs mate: Register called twice for hook " + name)
	}

	newHookFuncs[name] = newHookFunc
}

func Hooks() []string {
	hooksLocker.Lock()
	defer hooksLocker.Unlock()
	var list []string
	for name := range newHookFuncs {
		list = append(list, name)
	}
	sort.Strings(list)
	return list
}

func NewHook(name string, config Configuration) (hook logrus.Hook, err error) {
	hooksLocker.Lock()
	defer hooksLocker.Unlock()

	if newHookFunc, exist := newHookFuncs[name]; !exist {
		err = errHookNotRegistered
		return
	} else {
		hook, err = newHookFunc(config)
	}

	return
}
