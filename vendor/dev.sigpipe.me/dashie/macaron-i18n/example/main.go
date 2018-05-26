package main

import (
	"github.com/chai2010/gettext-go/gettext"
	"github.com/go-martini/martini"
	"github.com/martini-contrib/render"
	"github.com/yetist/middleware/i18n"
	"html/template"
)

func __(msgid string) string {
	return gettext.PGettext("", msgid)
}

func main() {
	m := martini.Classic()
	m.Use(render.Renderer(render.Options{
		Directory: "templates",
		Funcs: []template.FuncMap{
			{
				"__": func(s string) string {
					return __(s)
				},
			},
		},
	}))
	m.Use(i18n.I18n(i18n.Options{
		Domain:    "example",
		Parameter: "lang",
	}))

	m.Get("/", func() string {
		return __("Hello world!")
	})

	// template
	m.Get("/hi", func(r render.Render) {
		r.HTML(200, "index", __("Hello world!"))
	})
	m.Run()
}
