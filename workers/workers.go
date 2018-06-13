package workers

import (
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/RichardKnop/machinery/v1"
	"github.com/RichardKnop/machinery/v1/config"
	mlog "github.com/RichardKnop/machinery/v1/log"
	log "github.com/sirupsen/logrus"
)

// CreateServer initiate the machinery server
func CreateServer() (*machinery.Server, error) {
	cnf := config.Config{
		Broker:        fmt.Sprintf("redis://%s:%s/%d", setting.Worker.RedisHost, setting.Worker.RedisPort, setting.Worker.RedisDb),
		ResultBackend: fmt.Sprintf("redis://%s:%s/%d", setting.Worker.RedisHost, setting.Worker.RedisPort, setting.Worker.RedisDb + 1),
		DefaultQueue:  "reel2bits_queue",
		ResultsExpireIn: 60,
	}

	mlog.Set(log.StandardLogger())

	server, err := machinery.NewServer(&cnf)
	if err != nil {
		log.Errorf("Workers error: %s", err)
		return nil, err
	}

	server.RegisterTasks(map[string]interface{}{
		"TranscodeAndFetchInfos": TranscodeAndFetchInfos,
	})

	return server, err
}
