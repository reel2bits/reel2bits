package i18n

import (
	"github.com/leonelquinteros/gotext"
	"gopkg.in/macaron.v1"
	"strings"
	"sync"
)

const (
	_VERSION              = "0.0.1"
	_LANGUAGE_COOKIE_NAME = "_language"
	_LANGUAGE_PARAM_NAME  = "_language"
	_DEFAULT_DOMAIN       = "macaron"
	_DEFAULT_DIRECTORY    = "locale"
	_DEFAULT_LANGUAGE     = "en_US"
	_DEFAULT_TMPL_NAME    = "trans"
)

func Version() string {
	return _VERSION
}

// Options represents a struct for specifying configuration options for the i18n middleware.
type Options struct {
	Domain      string
	Directory   string
	ZipData     []byte
	DefaultLang string
	// Suburl of path. Default is empty.
	SubURL     string
	CookieName string
	// Name of language parameter name in URL. Default is "lang".
	Parameter string
	// Redirect when user uses get parameter to specify language.
	Redirect bool
	// Name that maps into template variable. Default is "i18n".
	TmplName string
	Inited   bool
}

func prepareOptions(options []Options) Options {
	var opt Options
	if len(options) > 0 {
		opt = options[0]
	}

	opt.SubURL = strings.TrimSuffix(opt.SubURL, "/")
	if len(opt.Domain) == 0 {
		opt.Domain = _DEFAULT_DOMAIN
	}
	if len(opt.Directory) == 0 {
		opt.Directory = _DEFAULT_DIRECTORY
	}
	if len(opt.DefaultLang) == 0 {
		opt.DefaultLang = _DEFAULT_LANGUAGE
	}
	if len(opt.CookieName) == 0 {
		opt.CookieName = _LANGUAGE_COOKIE_NAME
	}
	if len(opt.Parameter) == 0 {
		opt.Parameter = _LANGUAGE_PARAM_NAME
	}
	if len(opt.TmplName) == 0 {
		opt.TmplName = _DEFAULT_TMPL_NAME
	}
	if !opt.Redirect {
		opt.Redirect = true
	}

	return opt
}

type Locale struct {
	Lang string
}

func (locale *Locale) SetLang(lang string) {
	gotext.SetLanguage(toLocale(lang, false))
}

func (locale *Locale) Textdomain(domain string) {
	gotext.SetDomain(domain)
}

func initLocale(opt Options) {
	var once sync.Once
	onceBody := func() {
		gotext.Configure(opt.Directory, opt.DefaultLang, opt.Domain)
	}
	if !opt.Inited {
		once.Do(onceBody)
	}
}

func Gettext(msgid string) string {
	return gotext.Get(msgid)
}

// I18n is a middleware provides localization layer for your application.
// Paramenter langs must be in the form of "en-US", "zh-CN", etc.
// Otherwise it may not recognize browser input.
func I18n(options ...Options) macaron.Handler {
	opt := prepareOptions(options)
	initLocale(opt)
	return func(ctx *macaron.Context) {
		isNeedRedir := false
		hasCookie := false

		// 1. Check URL arguments.
		lang := ctx.Query(opt.Parameter)

		// 2. Get language information from cookies.
		if len(lang) == 0 {
			lang = ctx.GetCookie("lang")
			hasCookie = true
		} else {
			isNeedRedir = true
		}

		// Check again in case someone modify by purpose.
		//if !i18n.IsExist(lang) {
		//	lang = ""
		//	isNeedRedir = false
		//	hasCookie = false
		//}

		// 3. Get language information from 'Accept-Language'.
		if len(lang) == 0 {
			al := ctx.Req.Header.Get("Accept-Language")
			if len(al) > 4 {
				al = al[:5] // Only compare first 5 letters.
				lang = al
			}
		}

		// 4. Default language is the first element in the list.
		if len(lang) == 0 {
			lang = opt.DefaultLang
			isNeedRedir = false
		}
		curLang := toLanguage(lang)

		// Save language information in cookies.
		if !hasCookie {
			ctx.SetCookie("lang", curLang, 1<<31-1, "/"+strings.TrimPrefix(opt.SubURL, "/"))
		}
		gotext.SetLanguage(toLocale(lang, false))

		locale := Locale{Lang: curLang}
		ctx.Map(locale)
		//ctx.Locale = gotext.Locale
		ctx.Data["Lang"] = locale.Lang
		ctx.Data["LangName"] = toLanguage(locale.Lang)

		if opt.Redirect && isNeedRedir {
			ctx.Redirect(opt.SubURL + ctx.Req.RequestURI[:strings.Index(ctx.Req.RequestURI, "?")])
		}
	}
}

// Turns a language name (en-us) into a locale name (en_US). If 'to_lower' is
// True, the last component is lower-cased (en_us).
func toLocale(language string, to_lower bool) string {
	if p := strings.Index(language, "-"); p >= 0 {
		if to_lower {
			return strings.ToLower(language[:p]) + "_" + strings.ToLower(language[p+1:])
		} else {
			//# Get correct locale for sr-latn
			if len(language[p+1:]) > 2 {
				return strings.ToLower(language[:p]) + "_" + strings.ToUpper(string(language[p+1])) + strings.ToLower(language[p+2:])
			}
			return strings.ToLower(language[:p]) + "_" + strings.ToUpper(language[p+1:])
		}
	} else {
		return strings.ToLower(language)
	}
}

// Turns a locale name (en_US) into a language name (en-us).
func toLanguage(locale string) string {
	if p := strings.Index(locale, "_"); p >= 0 {
		return strings.ToLower(locale[:p]) + "-" + strings.ToLower(locale[p+1:])
	} else {
		return strings.ToLower(locale)
	}
}
