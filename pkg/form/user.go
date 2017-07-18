package form

import (
	"gopkg.in/macaron.v1"
	"github.com/go-macaron/binding"
)

// UpdateSettingsProfile fields
type UpdateSettingsProfile struct {
	Email string `binding:"Required;Email;MaxSize(254)"`
}

// Validate the form
func (f *UpdateSettingsProfile) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}
