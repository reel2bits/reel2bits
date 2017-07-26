package workers

import (
	"dev.sigpipe.me/dashie/reel2bits/pkg/sync"
	log "gopkg.in/clog.v1"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"github.com/RichardKnop/machinery/v1/tasks"
	"strings"
	"fmt"
)

var taskStatusTable = sync.NewStatusTable()
const (
	transcodingWatchdog = "transcoding_watchdog"
)

// TranscodingWatchdog take care to add un-ready tracsk to the worker queue if not ready and not found in it
// The track statuses are not updated, only by the worker when processed
// I don't think we really care to set the flag to "processing" "wait" etc. since this watchdog is mainly
// only for the case of redis unavailable when the track is uploaded, and this sould not happens lot of times.
func TranscodingWatchdog() {
	if taskStatusTable.IsRunning(transcodingWatchdog) {
		return
	}
	taskStatusTable.Start(transcodingWatchdog)
	defer taskStatusTable.Stop(transcodingWatchdog)

	log.Trace("Running cron: TranscodingWatchdog")

	// First case : empty workers list
	server, err := CreateServer()
	if err != nil {
		log.Error(2, "Cannot initiate the worker connection, please retry again.")
	}

	queueTranscodingInfos, _ := server.GetBroker().GetPendingTasks("reel2bits_queue")

	// get all un-ready tracks
	tracks, err := models.GetNotReadyTracks()
	if err != nil {
		log.Error(2, "Cannot get un-ready tracks: %s", err)
	}
	if len(tracks) <= 0 {
		return
	}

	if len(queueTranscodingInfos) <= 0 {
		log.Info("Workers queue is empty, checking for un-ready tracks.")
		log.Info("Found %d un-ready tracks to process.", len(tracks))
		// Add them to the worker queue
		for _, t := range tracks {
			sig := &tasks.Signature{
				Name: "TranscodeAndFetchInfos",
				Args: []tasks.Arg{{Type: "int64", Value: t.ID, }, },
			}

			_, err = server.SendTask(sig)
			if err != nil {
				log.Error(2, "Cannot push the worker job for %d, please retry again. %s", t.ID, err)
			}
		}
		return
	}

	// Second case : we have some worker elements to process, but there is un-processed tracks not in list
	for _, t := range tracks {
		trackFound := false
		// check if we find the track in the queue
		for _, qi := range queueTranscodingInfos {
			arg := qi.Args[0]

			var argValue int64

			if strings.HasPrefix(fmt.Sprintf("%T", arg.Value), "float") {
				n, ok := arg.Value.(float64)
				if !ok {
					log.Error(2, "Cannot convert to float64")
					continue
				}
				argValue = int64(n)
			}

			if t.ID == argValue {
				trackFound = true
			}
		}

		// Found it ?
		if !trackFound {
			log.Trace("Cannot found track %d in transcoding queue", t.ID)
			// Add it
			sig := &tasks.Signature{
				Name: "TranscodeAndFetchInfos",
				Args: []tasks.Arg{{Type: "int64", Value: t.ID, }, },
			}

			_, err = server.SendTask(sig)
			if err != nil {
				log.Error(2, "Cannot push the worker job for %d, please retry again. %s", t.ID, err)
			}
		}
	}

}