// Copyright 2016 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style license

package markup_test

import (
	"strings"
	"testing"

	. "github.com/smartystreets/goconvey/convey"

	. "dev.sigpipe.me/dashie/myapp/pkg/markup"
	"dev.sigpipe.me/dashie/myapp/setting"
)

func Test_IsMarkdownFile(t *testing.T) {
	setting.Markdown.FileExtensions = strings.Split(".md,.markdown,.mdown,.mkd", ",")
	Convey("Detect Markdown file extension", t, func() {
		testCases := []struct {
			ext   string
			match bool
		}{
			{".md", true},
			{".markdown", true},
			{".mdown", true},
			{".mkd", true},
			{".org", false},
			{".rst", false},
			{".asciidoc", false},
		}

		for _, tc := range testCases {
			So(IsMarkdownFile(tc.ext), ShouldEqual, tc.match)
		}
	})
}

func Test_Markdown(t *testing.T) {
}
