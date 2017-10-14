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
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

func Test_Register(t *testing.T) {
	Convey("Register with nil function", t, func() {
		defer func() {
			err := recover()
			So(err, ShouldNotBeNil)
			So(err, ShouldEqual, "clog: register function is nil")
		}()
		Register("test", nil)
	})

	Convey("Register duplicated mode", t, func() {
		defer func() {
			err := recover()
			So(err, ShouldNotBeNil)
			So(err, ShouldEqual, "clog: register duplicated mode 'test'")
		}()
		Register("test", newConsole)
		Register("test", newConsole)
	})

	Convey("Create non-registered logger", t, func() {
		err := New(MODE("404"), nil)
		So(err, ShouldNotBeNil)
		So(err.Error(), ShouldContainSubstring, "unknown mode")
	})
}
