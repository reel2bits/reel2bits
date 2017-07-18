// Copyright 2017 Unknwon
//
// Licensed under the Apache License, Version 2.0 (the "License"): you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

package clog

import (
	"bytes"
	"sync"
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

func Test_Version(t *testing.T) {
	Convey("Get version", t, func() {
		So(Version(), ShouldEqual, _VERSION)
	})
}

func Test_isValidLevel(t *testing.T) {
	Convey("Validate log level", t, func() {
		So(isValidLevel(LEVEL(-1)), ShouldBeFalse)
		So(isValidLevel(LEVEL(5)), ShouldBeFalse)
		So(isValidLevel(TRACE), ShouldBeTrue)
		So(isValidLevel(FATAL), ShouldBeTrue)
	})
}

const _MEMORY MODE = "memory"

type memoryConfig struct {
	// Minimum level of messages to be processed.
	Level LEVEL
	// Buffer size defines how many messages can be queued before hangs.
	BufferSize int64
}

var (
	buf bytes.Buffer
	wg  sync.WaitGroup
)

type memory struct {
	Adapter
}

func newMemory() Logger {
	return &memory{
		Adapter: Adapter{
			quitChan: make(chan struct{}),
		},
	}
}

func (m *memory) Level() LEVEL { return m.level }

func (m *memory) Init(v interface{}) error {
	cfg, ok := v.(memoryConfig)
	if !ok {
		return ErrConfigObject{"memoryConfig", v}
	}

	if !isValidLevel(cfg.Level) {
		return ErrInvalidLevel{}
	}
	m.level = cfg.Level

	m.msgChan = make(chan *Message, cfg.BufferSize)
	return nil
}

func (m *memory) ExchangeChans(errorChan chan<- error) chan *Message {
	m.errorChan = errorChan
	return m.msgChan
}

func (m *memory) write(msg *Message) {
	buf.WriteString(msg.Body)
	wg.Done()
}

func (m *memory) Start() {
LOOP:
	for {
		select {
		case msg := <-m.msgChan:
			m.write(msg)
		case <-m.quitChan:
			break LOOP
		}
	}

	for {
		if len(m.msgChan) == 0 {
			break
		}

		m.write(<-m.msgChan)
	}
	m.quitChan <- struct{}{} // Notify the cleanup is done.
}

func (m *memory) Destroy() {
	m.quitChan <- struct{}{}
	<-m.quitChan

	close(m.msgChan)
	close(m.quitChan)
}

func init() {
	Register(_MEMORY, newMemory)
}

func Test_Clog(t *testing.T) {
	Convey("In-memory logging", t, func() {
		So(New(_MEMORY, memoryConfig{}), ShouldBeNil)

		Convey("Basic logging", func() {
			buf.Reset()
			wg.Add(1)
			Trace("Level: %v", TRACE)
			wg.Wait()
			So(buf.String(), ShouldEqual, "[TRACE] Level: 0")

			buf.Reset()
			wg.Add(1)
			Info("Level: %v", INFO)
			wg.Wait()
			So(buf.String(), ShouldEqual, "[ INFO] Level: 1")

			buf.Reset()
			wg.Add(1)
			Warn("Level: %v", WARN)
			wg.Wait()
			So(buf.String(), ShouldEqual, "[ WARN] Level: 2")

			buf.Reset()
			wg.Add(1)
			Error(0, "Level: %v", ERROR)
			wg.Wait()
			So(buf.String(), ShouldEqual, "[ERROR] Level: 3")

			buf.Reset()
			wg.Add(1)
			Error(2, "Level: %v", ERROR)
			wg.Wait()
			So(buf.String(), ShouldContainSubstring, "clog_test.go")
		})
	})

	Convey("Skip logs has lower level", t, func() {
		So(New(_MEMORY, memoryConfig{
			Level: ERROR,
		}), ShouldBeNil)

		buf.Reset()
		Trace("Level: %v", TRACE)
		Trace("Level: %v", INFO)
		So(buf.String(), ShouldEqual, "")
	})
}
