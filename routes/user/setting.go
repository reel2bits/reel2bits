package user

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
)

const (
	tmplSettingsProfile = "user/settings/profile"
)

// Settings GET
func Settings(ctx *context.Context) {
	ctx.Title(ctx.Gettext("User settings"))
	ctx.PageIs("SettingsProfile")
	ctx.Data["email"] = ctx.User.Email
	ctx.Success(tmplSettingsProfile)
}

// SettingsPost POST
func SettingsPost(ctx *context.Context, f form.UpdateSettingsProfile) {
	ctx.Title(ctx.Gettext("User settings"))
	ctx.PageIs("SettingsProfile")
	ctx.Data["origin_name"] = ctx.User.UserName

	if ctx.HasError() {
		ctx.Success(tmplSettingsProfile)
		return
	}

	ctx.User.Email = f.Email
	if err := models.UpdateUser(&ctx.User); err != nil {
		ctx.ServerError("UpdateUser", err)
		return
	}

	ctx.Flash.Success(ctx.Gettext("Profile saved successfully"))
	ctx.SubURLRedirect(ctx.URLFor("user_settings"))
}
