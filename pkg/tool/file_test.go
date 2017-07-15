// Copyright 2016 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style license

package tool_test

import (
	. "github.com/smartystreets/goconvey/convey"

	. "dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"testing"
)

func Test_FileSize(t *testing.T) {
	Convey("File size to human", t, func() {
		testCases := []struct {
			size  int64
			human string
		}{
			{6, "6 B"},
			{1024, "1.0 KB"},
			{2000, "2.0 KB"},
			{4328472, "4.1 MB"},
			{3219783132, "3.0 GB"},
			{98429482394823942, "87 PB"},
		}

		for _, tc := range testCases {
			So(FileSize(tc.size), ShouldEqual, tc.human)
		}
	})
}
