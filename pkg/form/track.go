package form

import (
	"gopkg.in/macaron.v1"
	"github.com/go-macaron/binding"
	"mime/multipart"
)

// TrackUpload fields
type TrackUpload struct {
	Title	string	`form:"title" binding:"Required;MaxSize(255)"`
	Description	string	`form:"description"`
	IsPrivate	bool
	ShowDlLink	bool
	File		*multipart.FileHeader	`form:"file" binding:"Required;OnlyAudioFile"`
}

// Validate the form
func (f *TrackUpload) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}

type TrackDelete struct {
	Track    string   `binding:"Required"`
	User    string   `binding:"Required"`
}

func (f *TrackDelete) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}