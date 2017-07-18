package user

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/models"
)

const (
	settingsProfile = "user/settings/profile"
)

// Settings [GET]
func Settings(ctx *context.Context) {
	ctx.Title("settings.title")
	ctx.PageIs("SettingsProfile")
	ctx.Data["email"] = ctx.User.Email
	ctx.Success(settingsProfile)
}

// SettingsPost [POST]
func SettingsPost(ctx *context.Context, f form.UpdateSettingsProfile) {
	ctx.Title("settings.title")
	ctx.PageIs("SettingsProfile")
	ctx.Data["origin_name"] = ctx.User.UserName

	if ctx.HasError() {
		ctx.Success(settingsProfile)
		return
	}

	ctx.User.Email = f.Email
	if err := models.UpdateUser(ctx.User); err != nil {
		ctx.ServerError("UpdateUser", err)
		return
	}

	ctx.Flash.Success(ctx.Tr("settings.update_profile_success"))
	ctx.SubURLRedirect("/user/settings")
}
