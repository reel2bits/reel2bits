// Copyright 2016 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style license

package sanitize_test

import (
	"testing"

	. "github.com/smartystreets/goconvey/convey"

	. "dev.sigpipe.me/dashie/reel2bits/pkg/sanitize"
)

func Test_Accents(t *testing.T) {
	Convey("Replacing accents", t, func() {
		testCases := []struct {
			src string
			new string
		}{
			{"test", "test"},
			{"élèves", "eleves"},
			{"señor", "senor"},
			{"œdipe", "oedipe"},
		}

		for _, tc := range testCases {
			So(Accents(tc.src), ShouldEqual, tc.new)
		}
	})
}

func Test_SanitizeFilename(t *testing.T) {
	Convey("Filename sanitization", t, func() {
		testCases := []struct {
			src string
			new string
		}{
			{"/etc/coin", "/etc/coin"},
			{"/../../etc/passwd", "/etc/passwd"},
			{"../coin", "/coin"},
			{"test", "test"},
			{"/somewhere/../../etc/passwd;test", "/somewhere/etc/passwdtest"},
		}

		for _, tc := range testCases {
			So(Filename(tc.src), ShouldEqual, tc.new)
		}
	})
}
