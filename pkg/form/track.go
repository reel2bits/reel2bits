package form

import (
	"github.com/go-macaron/binding"
	"gopkg.in/macaron.v1"
	"mime/multipart"
)

// TrackUpload fields
type TrackUpload struct {
	Title       string `form:"title" binding:"Required;MaxSize(255)"`
	Description string `form:"description"`
	IsPrivate   bool
	ShowDlLink  bool
	Album       uint
	File        *multipart.FileHeader `form:"file" binding:"Required;OnlyAudioFile"`
}

// Validate the form
func (f *TrackUpload) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}

// TrackDelete fields
type TrackDelete struct {
	Track string `binding:"Required"`
	User  string `binding:"Required"`
}

// Validate the form
func (f *TrackDelete) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}

// TrackEdit fields
type TrackEdit struct {
	Title       string `form:"title" binding:"Required;MaxSize(255)"`
	Description string `form:"description"`
	IsPrivate   bool
	ShowDlLink  bool
	Album       uint
}

// Validate the form
func (f *TrackEdit) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}
