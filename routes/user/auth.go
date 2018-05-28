package user

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/pkg/mailer"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	log "github.com/sirupsen/logrus"
	"net/url"
)

const (
	tmplLogin          = "user/auth/login"
	tmplRegister       = "user/auth/register"
	tmplForgotPassword = "user/auth/forgot_password"
	tmplResetPassword  = "user/auth/reset_password"
)

// isValidRedirect returns false if the URL does not redirect to same site.
// False: //url, http://url
// True: /url
func isValidRedirect(url string) bool {
	return len(url) >= 2 && url[0] == '/' && url[1] != '/'
}

// AutoLogin reads cookie and try to auto-login.
func AutoLogin(c *context.Context) (bool, error) {
	if !models.HasEngine {
		return false, nil
	}

	uname := c.GetCookie(setting.CookieUserName)
	if len(uname) == 0 {
		return false, nil
	}

	isSucceed := false
	defer func() {
		if !isSucceed {
			log.Debugf("auto-login cookie cleared: %s", uname)
			c.SetCookie(setting.CookieUserName, "", -1, setting.AppSubURL)
			c.SetCookie(setting.CookieRememberName, "", -1, setting.AppSubURL)
			c.SetCookie(setting.LoginStatusCookieName, "", -1, setting.AppSubURL)
		}
	}()

	u, err := models.GetUserByName(uname)
	if err != nil {
		if !errors.IsUserNotExist(err) {
			return false, fmt.Errorf("GetUserByName: %v", err)
		}
		return false, nil
	}

	if val, ok := c.GetSuperSecureCookie(u.Rands+u.Password, setting.CookieRememberName); !ok || val != u.UserName {
		return false, nil
	}

	isSucceed = true
	c.Session.Set("uid", u.ID)
	c.Session.Set("uname", u.UserName)
	c.SetCookie(setting.CSRFCookieName, "", -1, setting.AppSubURL)
	if setting.EnableLoginStatusCookie {
		c.SetCookie(setting.LoginStatusCookieName, "true", 0, setting.AppSubURL)
	}
	return true, nil
}

// Login GET
func Login(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Sign In"))

	// check for auto-login
	isSucceed, err := AutoLogin(ctx)
	if err != nil {
		ctx.Handle(500, "AutoLogin", err)
		return
	}

	redirectTo := ctx.Query("redirect_to")
	if len(redirectTo) > 0 {
		ctx.SetCookie("redirect_to", redirectTo, 0, setting.AppSubURL)
	} else {
		redirectTo, _ = url.QueryUnescape(ctx.GetCookie("redirect_to"))
	}
	ctx.SetCookie("redirect_to", "", -1, setting.AppSubURL)

	if isSucceed {
		if isValidRedirect(redirectTo) {
			ctx.Redirect(redirectTo)
		} else {
			ctx.Redirect(setting.AppSubURL + "/")
		}
		return
	}

	ctx.HTML(200, tmplLogin)
}

// LoginPost POST
func LoginPost(ctx *context.Context, f form.Login) {
	ctx.Title(ctx.Gettext("Sign In"))

	if ctx.HasError() {
		ctx.Success(tmplLogin)
		return
	}

	u, err := models.UserLogin(f.UserName, f.Password)
	if err != nil {
		if errors.IsUserNotExist(err) {
			ctx.RenderWithErr(ctx.Gettext("Invalid username or password"), tmplLogin, &f)
		} else {
			ctx.ServerError("UserSignIn", err)
		}
		return
	}

	afterLogin(ctx, u, f.Remember)
	return
}

// After login func, may be useful with Two-Factor
func afterLogin(ctx *context.Context, u *models.User, remember bool) {
	if remember {
		days := 86400 * setting.LoginRememberDays
		ctx.SetCookie(setting.CookieUserName, u.UserName, days, setting.AppSubURL, "", setting.CookieSecure, true)
		ctx.SetSuperSecureCookie(u.Rands+u.Password, setting.CookieRememberName, u.UserName, days, setting.AppSubURL, "", setting.CookieSecure, true)
	}

	ctx.Session.Set("uid", u.ID)
	ctx.Session.Set("uname", u.UserName)

	// Clear CSRF and force regenerate one
	ctx.SetCookie(setting.CSRFCookieName, "", -1, setting.AppSubURL)
	if setting.EnableLoginStatusCookie {
		ctx.SetCookie(setting.LoginStatusCookieName, "true", 0, setting.AppSubURL)
	}

	redirectTo, _ := url.QueryUnescape(ctx.GetCookie("redirect_to"))
	ctx.SetCookie("redirect_to", "", -1, setting.AppSubURL)
	if isValidRedirect(redirectTo) {
		ctx.Redirect(redirectTo)
		return
	}

	ctx.Redirect(setting.AppSubURL + "/")
}

// Register GET
func Register(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Register"))
	if !setting.CanRegister {
		ctx.Flash.Error(ctx.Gettext("Registration not allowed"))
		ctx.Redirect(setting.AppSubURL + "/")
		return
	}

	ctx.HTML(200, tmplRegister)
}

// RegisterPost POST
func RegisterPost(ctx *context.Context, f form.Register) {
	ctx.Title(ctx.Gettext("Register"))

	if !setting.CanRegister {
		ctx.Flash.Error(ctx.Gettext("Registration not allowed"))
		ctx.Redirect(setting.AppSubURL + "/")
		return
	}

	if ctx.HasError() {
		ctx.HTML(200, tmplRegister)
		return
	}

	if f.Password != f.Repeat {
		ctx.Data["Err_Password"] = true
		ctx.Data["Err_Retype"] = true
		ctx.RenderWithErr(ctx.Gettext("Passwords doesn't match"), tmplRegister, &f)
		return
	}

	u := &models.User{
		UserName: f.UserName,
		Email:    f.Email,
		Password: f.Password,
		Active:   models.BoolToFake(true), // FIXME: implement user activation by email
	}
	if err := models.CreateUser(u); err != nil {
		switch {
		case models.IsErrUserAlreadyExist(err):
			ctx.Data["Err_UserName"] = true
			ctx.RenderWithErr(ctx.Gettext("Username already taken, sorry"), tmplRegister, &f)
		case models.IsErrNameReserved(err):
			ctx.Data["Err_UserName"] = true
			ctx.RenderWithErr(ctx.Gettext("Username reserved, please choose another username"), tmplRegister, &f)
		case models.IsErrNamePatternNotAllowed(err):
			ctx.Data["Err_UserName"] = true
			ctx.RenderWithErr(ctx.Gettext("Invalid username pattern"), tmplRegister, &f)
		default:
			ctx.Handle(500, "CreateUser", err)
		}
		return
	}
	log.Debugf("Account created: %d/%s", u.ID, u.UserName)

	// Auto set Admin if first user
	if models.CountUsers() == 1 {
		u.Admin = models.BoolToFake(true)
		u.Active = models.BoolToFake(true) // bypass email activation
		if err := models.UpdateUser(u); err != nil {
			ctx.Handle(500, "UpdateUser", err)
			return
		}
	}

	// TODO: send activation email

	ctx.Flash.Success(ctx.Gettext("Register succesfull"))
	ctx.Redirect(setting.AppSubURL + "/user/login")
}

// Logout GET
func Logout(ctx *context.Context) {
	ctx.Session.Delete("uid")
	ctx.Session.Delete("uname")
	ctx.SetCookie(setting.CookieUserName, "", -1, setting.AppSubURL)
	ctx.SetCookie(setting.CookieRememberName, "", -1, setting.AppSubURL)
	ctx.SetCookie(setting.CSRFCookieName, "", -1, setting.AppSubURL)
	ctx.Redirect(setting.AppSubURL + "/")
}

// ResetPasswd GET
func ResetPasswd(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Reset Your Password"))
	code := ctx.Query("code")
	if len(code) == 0 {
		ctx.Error(404)
		return
	}
	ctx.Data["Code"] = code
	ctx.Data["IsResetForm"] = true
	ctx.HTML(200, tmplResetPassword)
}

// ResetPasswdPost POST
func ResetPasswdPost(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Reset Your Password"))

	code := ctx.Query("code")
	if len(code) == 0 {
		ctx.Error(404)
		return
	}
	ctx.Data["Code"] = code

	if u := models.VerifyUserActiveCode(code); u.ID > 0 {
		// Validate password length.
		passwd := ctx.Query("password")
		if len(passwd) < 6 {
			ctx.Data["IsResetForm"] = true
			ctx.Data["Err_Password"] = true
			ctx.RenderWithErr(ctx.Gettext("Password length cannot be less then 6."), tmplResetPassword, nil)
			return
		}

		u.Password = passwd
		var err error
		if u.Rands, err = models.GetUserSalt(); err != nil {
			ctx.Handle(500, "UpdateUser", err)
			return
		}
		if u.Salt, err = models.GetUserSalt(); err != nil {
			ctx.Handle(500, "UpdateUser", err)
			return
		}
		u.EncodePasswd()
		if err := models.UpdateUser(&u); err != nil {
			ctx.Handle(500, "UpdateUser", err)
			return
		}

		log.Debugf("User password reset: %s", u.UserName)
		ctx.Redirect(setting.AppSubURL + "/user/login")
		return
	}
	ctx.Data["IsResetFailed"] = true
	ctx.HTML(200, tmplResetPassword)
}

// ForgotPasswd GET
func ForgotPasswd(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Forgot Password"))

	if setting.MailService == nil {
		ctx.Data["IsResetDisable"] = true
		ctx.HTML(200, tmplForgotPassword)
		return
	}

	ctx.Data["IsResetRequest"] = true

	ctx.HTML(200, tmplForgotPassword)
}

// ForgotPasswdPost POST
func ForgotPasswdPost(ctx *context.Context) {
	ctx.Title(ctx.Gettext("Forgot Password"))

	if setting.MailService == nil {
		ctx.Handle(403, "ForgotPasswdPost", nil)
		return
	}
	ctx.Data["IsResetRequest"] = true

	email := ctx.Query("email")
	ctx.Data["Email"] = email

	u, err := models.GetUserByEmail(email)
	if err != nil {
		if errors.IsUserNotExist(err) {
			// HARDCODED
			ctx.Data["Hours"] = 180 / 60
			ctx.Data["IsResetSent"] = true
			log.Debug("User doesn't exists")
			ctx.HTML(200, tmplForgotPassword)
			return
		}

		ctx.Handle(500, "user.ResetPasswd(check existence)", err)
		return
	}

	if ctx.Cache.IsExist("MailResendLimit_" + u.LowerName) {
		log.Debug("Mail Resend limited")
		ctx.Data["ResendLimited"] = true
		ctx.HTML(200, tmplForgotPassword)
		return
	}

	mailer.SendResetPasswordMail(ctx.Context, models.NewMailerUser(&u))
	if err = ctx.Cache.Put("MailResendLimit_"+u.LowerName, u.LowerName, 180); err != nil {
		log.Errorf("Set cache(MailResendLimit) fail: %v", err)
	}

	// HARDCODED
	ctx.Data["Hours"] = 180 / 60
	ctx.Data["IsResetSent"] = true
	ctx.HTML(200, tmplForgotPassword)
}
