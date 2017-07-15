package template

import (
	"container/list"
	"dev.sigpipe.me/dashie/reel2bits/pkg/markup"
	"dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/microcosm-cc/bluemonday"
	"html/template"
	"mime"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func NewFuncMap() []template.FuncMap {
	return []template.FuncMap{map[string]interface{}{
		"GoVer": func() string {
			return strings.Title(runtime.Version())
		},
		"AppName": func() string {
			return setting.AppName
		},
		"AppSubURL": func() string {
			return setting.AppSubURL
		},
		"AppURL": func() string {
			return setting.AppURL
		},
		"AppVer": func() string {
			return setting.AppVer
		},
		"AppDomain": func() string {
			return setting.Domain
		},
		"CanRegister": func() bool {
			return setting.CanRegister
		},
		"LoadTimes": func(startTime time.Time) string {
			return fmt.Sprint(time.Since(startTime).Nanoseconds()/1e6) + "ms"
		},
		"FileSize": tool.FileSize,
		"Safe":     Safe,
		"Sanitize": bluemonday.UGCPolicy().Sanitize,
		"Str2html": Str2html,
		"Add": func(a, b int) int {
			return a + b
		},
		"DateFmtLong": func(t time.Time) string {
			return t.Format(time.RFC1123Z)
		},
		"DateFmtShort": func(t time.Time) string {
			return t.Format("Jan 02, 2006")
		},
		"List": List,
		"SubStr": func(str string, start, length int) string {
			if len(str) == 0 {
				return ""
			}
			end := start + length
			if length == -1 {
				end = len(str)
			}
			if len(str) < end {
				return str
			}
			return str[start:end]
		},
		"Join":        strings.Join,
		"Sha1":        Sha1,
		"ShortSHA1":   tool.ShortSHA1,
		"MD5":         tool.MD5,
		"EscapePound": EscapePound,
		"FilenameIsImage": func(filename string) bool {
			mimeType := mime.TypeByExtension(filepath.Ext(filename))
			return strings.HasPrefix(mimeType, "image/")
		},
		"IsPdf": func(mime string) bool {
			return strings.EqualFold(mime, "application/pdf")
		},
	}}
}

func Safe(raw string) template.HTML {
	return template.HTML(raw)
}

func List(l *list.List) chan interface{} {
	e := l.Front()
	c := make(chan interface{})
	go func() {
		for e != nil {
			c <- e.Value
			e = e.Next()
		}
		close(c)
	}()
	return c
}

func Sha1(str string) string {
	return tool.SHA1(str)
}

func EscapePound(str string) string {
	return strings.NewReplacer("%", "%25", "#", "%23", " ", "%20", "?", "%3F").Replace(str)
}

func Str2html(raw string) template.HTML {
	return template.HTML(markup.Sanitize(raw))
}
