package form

import (
	"gopkg.in/macaron.v1"
	"github.com/go-macaron/binding"
)

// Album fields
type Album struct {
	Name	string	`form:"name" binding:"Required;MaxSize(255)"`
	Description	string	`form:"description"`
	IsPrivate	bool
}

// Validate the form
func (f *Album) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}

// AlbumDelete fields
type AlbumDelete struct {
	Album   string   `binding:"Required"`
	User    string   `binding:"Required"`
}

// Validate the form
func (f *AlbumDelete) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}
