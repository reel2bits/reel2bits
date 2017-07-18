// Copyright 2014 The Macaron Authors
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

package cache

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	. "github.com/smartystreets/goconvey/convey"
	"gopkg.in/macaron.v1"

	"github.com/go-macaron/cache"
)

func Test_PostgresCacher(t *testing.T) {
	Convey("Test postgres cache adapter", t, func() {
		opt := cache.Options{
			Adapter:       "postgres",
			AdapterConfig: "user=jiahuachen dbname=macaron port=5432 sslmode=disable",
		}

		Convey("Basic operations", func() {
			m := macaron.New()
			m.Use(cache.Cacher(opt))

			m.Get("/", func(c cache.Cache) {
				So(c.Put("uname", "unknwon", 1), ShouldBeNil)
				So(c.Put("uname2", "unknwon2", 1), ShouldBeNil)
				So(c.IsExist("uname"), ShouldBeTrue)

				So(c.Get("404"), ShouldBeNil)
				So(c.Get("uname").(string), ShouldEqual, "unknwon")

				time.Sleep(1 * time.Second)
				So(c.Get("uname"), ShouldBeNil)
				time.Sleep(1 * time.Second)
				So(c.Get("uname2"), ShouldBeNil)

				So(c.Put("uname", "unknwon", 0), ShouldBeNil)
				So(c.Delete("uname"), ShouldBeNil)
				So(c.Get("uname"), ShouldBeNil)

				So(c.Put("uname", "unknwon", 0), ShouldBeNil)
				So(c.Flush(), ShouldBeNil)
				So(c.Get("uname"), ShouldBeNil)

				So(c.Put("struct", opt, 0), ShouldBeNil)
			})

			resp := httptest.NewRecorder()
			req, err := http.NewRequest("GET", "/", nil)
			So(err, ShouldBeNil)
			m.ServeHTTP(resp, req)
		})

		Convey("Increase and decrease operations", func() {
			m := macaron.New()
			m.Use(cache.Cacher(opt))

			m.Get("/", func(c cache.Cache) {
				// Escape GC at the momment.
				time.Sleep(1 * time.Second)

				So(c.Incr("404"), ShouldNotBeNil)
				So(c.Decr("404"), ShouldNotBeNil)

				So(c.Put("int", 0, 0), ShouldBeNil)
				So(c.Put("int32", int32(0), 0), ShouldBeNil)
				So(c.Put("int64", int64(0), 0), ShouldBeNil)
				So(c.Put("uint", uint(0), 0), ShouldBeNil)
				So(c.Put("uint32", uint32(0), 0), ShouldBeNil)
				So(c.Put("uint64", uint64(0), 0), ShouldBeNil)
				So(c.Put("string", "hi", 0), ShouldBeNil)

				So(c.Decr("uint"), ShouldNotBeNil)
				So(c.Decr("uint32"), ShouldNotBeNil)
				So(c.Decr("uint64"), ShouldNotBeNil)

				So(c.Incr("int"), ShouldBeNil)
				So(c.Incr("int32"), ShouldBeNil)
				So(c.Incr("int64"), ShouldBeNil)
				So(c.Incr("uint"), ShouldBeNil)
				So(c.Incr("uint32"), ShouldBeNil)
				So(c.Incr("uint64"), ShouldBeNil)

				So(c.Decr("int"), ShouldBeNil)
				So(c.Decr("int32"), ShouldBeNil)
				So(c.Decr("int64"), ShouldBeNil)
				So(c.Decr("uint"), ShouldBeNil)
				So(c.Decr("uint32"), ShouldBeNil)
				So(c.Decr("uint64"), ShouldBeNil)

				So(c.Incr("string"), ShouldNotBeNil)
				So(c.Decr("string"), ShouldNotBeNil)

				So(c.Get("int"), ShouldEqual, 0)
				So(c.Get("int32"), ShouldEqual, 0)
				So(c.Get("int64"), ShouldEqual, 0)
				So(c.Get("uint"), ShouldEqual, 0)
				So(c.Get("uint32"), ShouldEqual, 0)
				So(c.Get("uint64"), ShouldEqual, 0)

				So(c.Flush(), ShouldBeNil)
			})

			resp := httptest.NewRecorder()
			req, err := http.NewRequest("GET", "/", nil)
			So(err, ShouldBeNil)
			m.ServeHTTP(resp, req)
		})
	})
}
