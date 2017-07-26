package workers

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/RichardKnop/machinery/v1"
	"github.com/RichardKnop/machinery/v1/config"
	log "gopkg.in/clog.v1"
)

// CreateServer initiate the machinery server
func CreateServer() (*machinery.Server, error) {
	cnf := config.Config{
		Broker:             fmt.Sprintf("redis://%s:%s/%s", setting.Worker.RedisHost, setting.Worker.RedisPort, setting.Worker.RedisDb),
		ResultBackend:      fmt.Sprintf("redis://%s:%s/%s", setting.Worker.RedisHost, setting.Worker.RedisPort, setting.Worker.RedisDb),
		MaxWorkerInstances: 0,
		DefaultQueue:       "reel2bits_queue",
	}

	server, err := machinery.NewServer(&cnf)
	if err != nil {
		log.Error(2, "Workers error: %s", err)
		return nil, err
	}

	server.RegisterTasks(map[string]interface{}{
		"TranscodeAndFetchInfos": TranscodeAndFetchInfos,
	})

	return server, err
}
