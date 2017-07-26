package form

import (
	"github.com/go-macaron/binding"
	"gopkg.in/macaron.v1"
)

// Register fields
type Register struct {
	UserName string `binding:"Required;AlphaDashDot;MaxSize(35)"`
	Email    string `binding:"Required;Email;MaxSize(254)"`
	Password string `binding:"Required;MaxSize(255)"`
	Repeat   string
}

// Validate the form
func (f *Register) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}

// Login fields
type Login struct {
	UserName string `binding:"Required;MaxSize(254)"`
	Password string `binding:"Required;MaxSize(255)"`
	Remember bool
}

// Validate the form
func (f *Login) Validate(ctx *macaron.Context, errs binding.Errors) binding.Errors {
	return validate(errs, ctx.Data, f, ctx.Locale)
}
