// Copyright 2016 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style license

package tool_test

import (
	. "github.com/smartystreets/goconvey/convey"

	. "dev.sigpipe.me/dashie/myapp/pkg/tool"
	"testing"
)

func Test_MD5(t *testing.T) {
	Convey("Validate MD5", t, func() {
		testCases := []struct {
			src  string
			hash string
		}{
			{"coincoin", "3dc6862aaced087142142587cba2123e"},
			{"e3rj3h8j10yg8sj03sh313t387yryt91y3hg39", "3662553c4630d15aa8ce1307ba8fe1af"},
			{"ˆ&#@#$ˆ&%ˆ#&@$#$ˆ", "8bd92940c0ea4ad4413991f2d0e3159b"},
		}

		for _, tc := range testCases {
			So(MD5(tc.src), ShouldEqual, tc.hash)
		}
	})
}

func Test_SHA1(t *testing.T) {
	Convey("Validate SHA1", t, func() {
		testCases := []struct {
			src  string
			hash string
		}{
			{"coincoin", "0f78ee98759868a8b5d5aeb6b9dbd2106b14e965"},
			{"e3rj3h8j10yg8sj03sh313t387yryt91y3hg39", "75fa1f977e62fba66de7c14988d28d7007a42730"},
			{"ˆ&#@#$ˆ&%ˆ#&@$#$ˆ", "28f0b6a36b6ed5cb2f45614288d4659974c4659d"},
		}

		for _, tc := range testCases {
			So(SHA1(tc.src), ShouldEqual, tc.hash)
		}
	})
}

func Test_ShortSHA1(t *testing.T) {
	Convey("Validate SHA1", t, func() {
		testCases := []struct {
			src  string
			hash string
		}{
			{"0aadb9081430eb80435b9a442484387f9a443a65", "0aadb90814"},
			{"75fa1f977e62fba66de7c14988d28d7007a42730", "75fa1f977e"},
			{"39e74f1d108f4988e51cdb1c58cfe046ec87c735", "39e74f1d10"},
		}

		for _, tc := range testCases {
			So(ShortSHA1(tc.src), ShouldEqual, tc.hash)
		}
	})
}

func Test_RandomString(t *testing.T) {
	Convey("Test random string size 5", t, func() {
		for i := 0; i < 10; i++ {
			r1, _ := RandomString(5)
			r2, _ := RandomString(5)
			So(r1, ShouldNotEqual, r2)
		}
	})

	Convey("Test random string size 10", t, func() {
		for i := 0; i < 10; i++ {
			r1, _ := RandomString(10)
			r2, _ := RandomString(10)
			So(r1, ShouldNotEqual, r2)
		}
	})

	Convey("Test random string size 20", t, func() {
		for i := 0; i < 10; i++ {
			r1, _ := RandomString(20)
			r2, _ := RandomString(20)
			So(r1, ShouldNotEqual, r2)
		}
	})
}
