package cron

import (
	"github.com/gogits/cron"
	log "gopkg.in/clog.v1"
	"time"
	"dev.sigpipe.me/dashie/reel2bits/workers"
)

var c = cron.New()

// NewContext initiate the cron thing
func NewContext() {
	var (
		entry *cron.Entry
		err   error
	)

	// Add crons here

	log.Trace("Enabling TranscodingWatchdog")
	entry, err = c.AddFunc("Transcoding Watchdog", "@every 5m", workers.TranscodingWatchdog)
	if err != nil {
		log.Fatal(2, "Cron.(transcoding watchdog): %v", err)
	}
	entry.Next = time.Now().Add(1 * time.Minute)

	c.Start()
}

// ListTasks returns all running cron tasks.
func ListTasks() []*cron.Entry {
	return c.Entries()
}
