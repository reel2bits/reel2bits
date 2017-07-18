package cron

import (
	"github.com/gogits/cron"
	//log "gopkg.in/clog.v1"
)

var c = cron.New()

// NewContext initiate the cron thing
func NewContext() {
	var (
	//entry *cron.Entry
	//err   error
	)

	// Add crons here

	c.Start()
}

// ListTasks returns all running cron tasks.
func ListTasks() []*cron.Entry {
	return c.Entries()
}
