package form

import (
	"github.com/go-macaron/binding"
	"gopkg.in/macaron.v1"
)

// UpdateSettingsProfile fields
type UpdateSettingsProfile struct {
	Email string `binding:"Required;Email;MaxSize(254)"`
}

// Validate the form
func (f *UpdateSettingsProfile) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}
