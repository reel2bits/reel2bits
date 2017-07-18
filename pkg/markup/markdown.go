// Copyright 2014 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a license

package markup

import (
	"bytes"
	"path"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/russross/blackfriday"

	"dev.sigpipe.me/dashie/reel2bits/setting"
)

// IsMarkdownFile reports whether name looks like a Markdown file based on its extension.
func IsMarkdownFile(name string) bool {
	extension := strings.ToLower(filepath.Ext(name))
	for _, ext := range setting.Markdown.FileExtensions {
		if strings.ToLower(ext) == extension {
			return true
		}
	}
	return false
}

// MarkdownRenderer is a extended version of underlying Markdown render object.
type MarkdownRenderer struct {
	blackfriday.Renderer
	urlPrefix string
}

var validLinksPattern = regexp.MustCompile(`^[a-z][\w-]+://|^mailto:`)

// isLink reports whether link fits valid format.
func isLink(link []byte) bool {
	return validLinksPattern.Match(link)
}

// Link defines how formal links should be processed to produce corresponding HTML elements.
func (r *MarkdownRenderer) Link(out *bytes.Buffer, link []byte, title []byte, content []byte) {
	if len(link) > 0 && !isLink(link) {
		if link[0] != '#' {
			link = []byte(path.Join(r.urlPrefix, string(link)))
		}
	}

	r.Renderer.Link(out, link, title, content)
}

// AutoLink defines how auto-detected links should be processed to produce corresponding HTML elements.
// Reference for kind: https://github.com/russross/blackfriday/blob/master/markdown.go#L69-L76
func (r *MarkdownRenderer) AutoLink(out *bytes.Buffer, link []byte, kind int) {
	if kind != blackfriday.LINK_TYPE_NORMAL {
		r.Renderer.AutoLink(out, link, kind)
		return
	}

	r.Renderer.AutoLink(out, link, kind)
}

// ListItem defines how list items should be processed to produce corresponding HTML elements.
func (r *MarkdownRenderer) ListItem(out *bytes.Buffer, text []byte, flags int) {
	// Detect procedures to draw checkboxes.
	switch {
	case bytes.HasPrefix(text, []byte("[ ] ")):
		text = append([]byte(`<input type="checkbox" disabled="" />`), text[3:]...)
	case bytes.HasPrefix(text, []byte("[x] ")):
		text = append([]byte(`<input type="checkbox" disabled="" checked="" />`), text[3:]...)
	}
	r.Renderer.ListItem(out, text, flags)
}

// RawMarkdown renders Markdown to HTML without handling special links.
func RawMarkdown(body []byte, urlPrefix string) []byte {
	htmlFlags := 0
	htmlFlags |= blackfriday.HTML_SKIP_STYLE
	htmlFlags |= blackfriday.HTML_OMIT_CONTENTS

	if setting.Smartypants.Enabled {
		htmlFlags |= blackfriday.HTML_USE_SMARTYPANTS
		if setting.Smartypants.Fractions {
			htmlFlags |= blackfriday.HTML_SMARTYPANTS_FRACTIONS
		}
		if setting.Smartypants.Dashes {
			htmlFlags |= blackfriday.HTML_SMARTYPANTS_DASHES
		}
		if setting.Smartypants.LatexDashes {
			htmlFlags |= blackfriday.HTML_SMARTYPANTS_LATEX_DASHES
		}
		if setting.Smartypants.AngledQuotes {
			htmlFlags |= blackfriday.HTML_SMARTYPANTS_ANGLED_QUOTES
		}
	}

	renderer := &MarkdownRenderer{
		Renderer:  blackfriday.HtmlRenderer(htmlFlags, "", ""),
		urlPrefix: urlPrefix,
	}

	// set up the parser
	extensions := 0
	extensions |= blackfriday.EXTENSION_NO_INTRA_EMPHASIS
	extensions |= blackfriday.EXTENSION_TABLES
	extensions |= blackfriday.EXTENSION_FENCED_CODE
	extensions |= blackfriday.EXTENSION_AUTOLINK
	extensions |= blackfriday.EXTENSION_STRIKETHROUGH
	extensions |= blackfriday.EXTENSION_SPACE_HEADERS
	extensions |= blackfriday.EXTENSION_NO_EMPTY_LINE_BEFORE_BLOCK

	if setting.Markdown.EnableHardLineBreak {
		extensions |= blackfriday.EXTENSION_HARD_LINE_BREAK
	}

	body = blackfriday.Markdown(body, renderer, extensions)
	return body
}

// Markdown takes a string or []byte and renders to HTML in Markdown syntax with special links.
func Markdown(input interface{}, urlPrefix string) []byte {
	return Render(typeMarkdown, input, urlPrefix)
}
