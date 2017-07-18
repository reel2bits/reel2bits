// Copyright 2015 Unknwon
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

package paginater

import (
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

func Test_Paginater(t *testing.T) {
	Convey("Basic logics", t, func() {
		p := New(0, -1, -1, 0)
		So(p.PagingNum(), ShouldEqual, 1)
		So(p.IsFirst(), ShouldBeTrue)
		So(p.HasPrevious(), ShouldBeFalse)
		So(p.Previous(), ShouldEqual, 1)
		So(p.HasNext(), ShouldBeFalse)
		So(p.Next(), ShouldEqual, 1)
		So(p.IsLast(), ShouldBeTrue)
		So(p.Total(), ShouldEqual, 0)

		p = New(1, 10, 2, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeTrue)
		So(p.HasPrevious(), ShouldBeFalse)
		So(p.HasNext(), ShouldBeFalse)
		So(p.IsLast(), ShouldBeTrue)

		p = New(10, 10, 1, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeTrue)
		So(p.HasPrevious(), ShouldBeFalse)
		So(p.HasNext(), ShouldBeFalse)
		So(p.IsLast(), ShouldBeTrue)

		p = New(11, 10, 1, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeTrue)
		So(p.HasPrevious(), ShouldBeFalse)
		So(p.HasNext(), ShouldBeTrue)
		So(p.Next(), ShouldEqual, 2)
		So(p.IsLast(), ShouldBeFalse)

		p = New(11, 10, 2, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeFalse)
		So(p.HasPrevious(), ShouldBeTrue)
		So(p.Previous(), ShouldEqual, 1)
		So(p.HasNext(), ShouldBeFalse)
		So(p.IsLast(), ShouldBeTrue)

		p = New(20, 10, 2, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeFalse)
		So(p.HasPrevious(), ShouldBeTrue)
		So(p.HasNext(), ShouldBeFalse)
		So(p.IsLast(), ShouldBeTrue)

		p = New(25, 10, 2, 0)
		So(p.PagingNum(), ShouldEqual, 10)
		So(p.IsFirst(), ShouldBeFalse)
		So(p.HasPrevious(), ShouldBeTrue)
		So(p.HasNext(), ShouldBeTrue)
		So(p.IsLast(), ShouldBeFalse)
	})

	Convey("Generate pages", t, func() {
		Convey("No page is showing", func() {
			p := New(0, 10, 1, 0)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 0)
		})

		Convey("Only current page", func() {
			p := New(0, 10, 1, 1)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 1)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)

			p = New(1, 10, 1, 1)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 1)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)
		})

		Convey("Total page number is less or equal", func() {
			p := New(1, 10, 1, 2)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 1)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)

			p = New(11, 10, 1, 2)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 2)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeFalse)

			p = New(11, 10, 2, 2)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 2)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)

			p = New(25, 10, 2, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 3)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
		})

		Convey("Has more previous pages ", func() {
			// ... 2
			p := New(11, 10, 2, 1)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 2)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)

			// ... 2 3
			p = New(21, 10, 2, 2)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 3)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)

			// ... 2 3 4
			p = New(31, 10, 3, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 4)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeTrue)
			So(pages[3].Num(), ShouldEqual, 4)
			So(pages[3].IsCurrent(), ShouldBeFalse)

			// ... 3 4 5
			p = New(41, 10, 4, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 4)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 3)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, 4)
			So(pages[2].IsCurrent(), ShouldBeTrue)
			So(pages[3].Num(), ShouldEqual, 5)
			So(pages[3].IsCurrent(), ShouldBeFalse)

			// ... 4 5 6 7 8 9 10
			p = New(100, 10, 9, 7)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 8)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 4)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, 5)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, 6)
			So(pages[3].IsCurrent(), ShouldBeFalse)
			So(pages[4].Num(), ShouldEqual, 7)
			So(pages[4].IsCurrent(), ShouldBeFalse)
			So(pages[5].Num(), ShouldEqual, 8)
			So(pages[5].IsCurrent(), ShouldBeFalse)
			So(pages[6].Num(), ShouldEqual, 9)
			So(pages[6].IsCurrent(), ShouldBeTrue)
			So(pages[7].Num(), ShouldEqual, 10)
			So(pages[7].IsCurrent(), ShouldBeFalse)
		})

		Convey("Has more next pages", func() {
			// 1 ...
			p := New(21, 10, 1, 1)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 2)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)
			So(pages[1].Num(), ShouldEqual, -1)
			So(pages[1].IsCurrent(), ShouldBeFalse)

			// 1 2 ...
			p = New(21, 10, 1, 2)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 3)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, -1)
			So(pages[2].IsCurrent(), ShouldBeFalse)

			// 1 2 3 ...
			p = New(31, 10, 2, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 4)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, -1)
			So(pages[3].IsCurrent(), ShouldBeFalse)

			// 1 2 3 ...
			p = New(41, 10, 2, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 4)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, -1)
			So(pages[3].IsCurrent(), ShouldBeFalse)

			// 1 2 3 4 5 6 7 ...
			p = New(100, 10, 1, 7)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 8)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeTrue)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, 4)
			So(pages[3].IsCurrent(), ShouldBeFalse)
			So(pages[4].Num(), ShouldEqual, 5)
			So(pages[4].IsCurrent(), ShouldBeFalse)
			So(pages[5].Num(), ShouldEqual, 6)
			So(pages[5].IsCurrent(), ShouldBeFalse)
			So(pages[6].Num(), ShouldEqual, 7)
			So(pages[6].IsCurrent(), ShouldBeFalse)
			So(pages[7].Num(), ShouldEqual, -1)
			So(pages[7].IsCurrent(), ShouldBeFalse)

			// 1 2 3 4 5 6 7 ...
			p = New(100, 10, 2, 7)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 8)
			So(pages[0].Num(), ShouldEqual, 1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, 4)
			So(pages[3].IsCurrent(), ShouldBeFalse)
			So(pages[4].Num(), ShouldEqual, 5)
			So(pages[4].IsCurrent(), ShouldBeFalse)
			So(pages[5].Num(), ShouldEqual, 6)
			So(pages[5].IsCurrent(), ShouldBeFalse)
			So(pages[6].Num(), ShouldEqual, 7)
			So(pages[6].IsCurrent(), ShouldBeFalse)
			So(pages[7].Num(), ShouldEqual, -1)
			So(pages[7].IsCurrent(), ShouldBeFalse)
		})

		Convey("Has both more previous and next pages", func() {
			// ... 2 3 ...
			p := New(35, 10, 2, 2)
			pages := p.Pages()
			So(len(pages), ShouldEqual, 4)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeTrue)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeFalse)
			So(pages[3].Num(), ShouldEqual, -1)
			So(pages[3].IsCurrent(), ShouldBeFalse)

			// ... 2 3 4 ...
			p = New(49, 10, 3, 3)
			pages = p.Pages()
			So(len(pages), ShouldEqual, 5)
			So(pages[0].Num(), ShouldEqual, -1)
			So(pages[0].IsCurrent(), ShouldBeFalse)
			So(pages[1].Num(), ShouldEqual, 2)
			So(pages[1].IsCurrent(), ShouldBeFalse)
			So(pages[2].Num(), ShouldEqual, 3)
			So(pages[2].IsCurrent(), ShouldBeTrue)
			So(pages[3].Num(), ShouldEqual, 4)
			So(pages[3].IsCurrent(), ShouldBeFalse)
			So(pages[4].Num(), ShouldEqual, -1)
			So(pages[4].IsCurrent(), ShouldBeFalse)
		})
	})
}
