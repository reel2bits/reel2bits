// Copyright 2017 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package markup_test

import (
	"strings"
	"testing"

	. "github.com/smartystreets/goconvey/convey"

	. "dev.sigpipe.me/dashie/reel2bits/pkg/markup"
)

func Test_IsReadmeFile(t *testing.T) {
	Convey("Detect README file extension", t, func() {
		testCases := []struct {
			ext   string
			match bool
		}{
			{"readme", true},
			{"README", true},
			{"readme.md", true},
			{"readme.markdown", true},
			{"readme.mdown", true},
			{"readme.mkd", true},
			{"readme.org", true},
			{"readme.rst", true},
			{"readme.asciidoc", true},
			{"readme_ZH", true},
		}

		for _, tc := range testCases {
			So(IsReadmeFile(tc.ext), ShouldEqual, tc.match)
		}
	})
}

func Test_FindAllMentions(t *testing.T) {
	Convey("Find all mention patterns", t, func() {
		testCases := []struct {
			content string
			matches string
		}{
			{"@Unknwon, what do you think?", "Unknwon"},
			{"@Unknwon what do you think?", "Unknwon"},
			{"Hi @Unknwon, sounds good to me", "Unknwon"},
			{"cc/ @Unknwon @User", "Unknwon,User"},
		}

		for _, tc := range testCases {
			So(strings.Join(FindAllMentions(tc.content), ","), ShouldEqual, tc.matches)
		}
	})
}
