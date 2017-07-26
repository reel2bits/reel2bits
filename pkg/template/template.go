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
	"github.com/dustin/go-humanize"
	"gopkg.in/macaron.v1"
)

// NewFuncMap because you don't want an older
func NewFuncMap(m *macaron.Macaron) []template.FuncMap {
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
		"Unescape": func(str string) template.JS {
			str = strings.Replace(str, "\n","",-1)
			return template.JS(str)
		},
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
		"DurationToHuman": DurationToHuman,
		"ElapsedToHuman": ElapsedToHuman,
		"URLFor": func(name string, pairs ...string) string {
			return fmt.Sprintf("%s%s", strings.TrimSuffix(setting.AppURL, "/"), m.URLFor(name, pairs...))
		},
		"URLForRelative": m.URLFor,
		"NeedsImpressum": func() bool { return setting.NeedsImpressum},
	}}
}

// Safe safe
func Safe(raw string) template.HTML {
	return template.HTML(raw)
}

// List list
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

// Sha1 sha one
func Sha1(str string) string {
	return tool.SHA1(str)
}

// EscapePound escape the pound
func EscapePound(str string) string {
	return strings.NewReplacer("%", "%25", "#", "%23", " ", "%20", "?", "%3F").Replace(str)
}

// Str2html String to HTML
func Str2html(raw string) template.HTML {
	return template.HTML(markup.Sanitize(raw))
}

// ElapsedToHuman to get "xx days ago"
func ElapsedToHuman(dateUnix int64) string {
	date := time.Unix(dateUnix, 0).Local()
	return humanize.Time(date)
}

// No float32 or float64 possible :(
func divmod(m, n int) (q, r int) {
	q = m / n
	r = m % n
	return
}

// DurationToHuman transforms "125" in "2 minutes"
func DurationToHuman(duration float64) string {
	if duration < 0 {
		return "error"
	}

	minutes, seconds := divmod(int(duration), 60)
	hours, minutes := divmod(minutes, 60)
	days, hours := divmod(hours, 24)
	years, days := divmod(days, 365) // orig: 365.242199

	minutes = int(minutes)
	hours = int(hours)
	days = int(days)
	years = int(years)

	if years > 0 {
		if years != 1 {
			return fmt.Sprintf("%d years", years)
		}
		return fmt.Sprintf("%d year", years)
	} else if days > 0 {
		if days != 1 {
			return fmt.Sprintf("%d days", days)
		}
		return fmt.Sprintf("%d day", days)
	} else if hours > 0 {
		if hours != 1 {
			return fmt.Sprintf("%d hours", hours)
		}
		return fmt.Sprintf("%d hour", hours)
	} else if minutes > 0 {
		if minutes != 1 {
			return fmt.Sprintf("%d minutes", minutes)
		}
		return fmt.Sprintf("%d minute", minutes)
	} else {
		if minutes != 1 {
			return fmt.Sprintf("%.2d secs", seconds)
		}
		return fmt.Sprintf("%.2d sec", seconds)
	}
}