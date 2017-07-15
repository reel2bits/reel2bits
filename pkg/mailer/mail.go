// Copyright 2016 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package mailer

import (
	"fmt"
	"html/template"

	log "gopkg.in/clog.v1"
	"gopkg.in/gomail.v2"
	"gopkg.in/macaron.v1"
)

const (
	MAIL_AUTH_ACTIVATE        = "auth/activate"
	MAIL_AUTH_ACTIVATE_EMAIL  = "auth/activate_email"
	MAIL_AUTH_RESET_PASSWORD  = "auth/reset_passwd"
)

type MailRender interface {
	HTMLString(string, interface{}, ...macaron.HTMLOptions) (string, error)
}

var mailRender MailRender

func InitMailRender(dir string, funcMap []template.FuncMap) {
	opt := &macaron.RenderOptions{
		Directory:         dir,
		Funcs:             funcMap,
		Extensions:        []string{".tmpl", ".html"},
	}
	ts := macaron.NewTemplateSet()
	ts.Set(macaron.DEFAULT_TPL_SET_NAME, opt)

	mailRender = &macaron.TplRender{
		TemplateSet: ts,
		Opt:         opt,
	}
}

func SendTestMail(email string) error {
	return gomail.Send(&Sender{}, NewMessage([]string{email}, "myapp Test Email!", "myapp Test Email!").Message)
}

/*
	Setup interfaces of used methods in mail to avoid cycle import.
*/

type User interface {
	ID() int64
	DisplayName() string
	Email() string
	GenerateActivateCode() string
	GenerateEmailActivateCode(string) string
}

func SendUserMail(c *macaron.Context, u User, tpl, code, subject, info string) {
	data := map[string]interface{}{
		"Username":          u.DisplayName(),
		"ActiveCodeLives":   180 / 60,
		"ResetPwdCodeLives": 180 / 60,
		"Code":              code,
	}
	body, err := mailRender.HTMLString(string(tpl), data)
	if err != nil {
		log.Error(3, "HTMLString: %v", err)
		return
	}

	msg := NewMessage([]string{u.Email()}, subject, body)
	msg.Info = fmt.Sprintf("UID: %d, %s", u.ID(), info)

	SendAsync(msg)
}

func SendActivateAccountMail(c *macaron.Context, u User) {
	SendUserMail(c, u, MAIL_AUTH_ACTIVATE, u.GenerateActivateCode(), c.Tr("mail.activate_account"), "activate account")
}

func SendResetPasswordMail(c *macaron.Context, u User) {
	SendUserMail(c, u, MAIL_AUTH_RESET_PASSWORD, u.GenerateActivateCode(), c.Tr("mail.reset_password"), "reset password")
}

// SendActivateAccountMail sends confirmation email.
func SendActivateEmailMail(c *macaron.Context, u User, email string) {
	data := map[string]interface{}{
		"Username":        u.DisplayName(),
		"ActiveCodeLives": 180 / 60,
		"Code":            u.GenerateEmailActivateCode(email),
		"Email":           email,
	}
	body, err := mailRender.HTMLString(string(MAIL_AUTH_ACTIVATE_EMAIL), data)
	if err != nil {
		log.Error(3, "HTMLString: %v", err)
		return
	}

	msg := NewMessage([]string{email}, c.Tr("mail.activate_email"), body)
	msg.Info = fmt.Sprintf("UID: %d, activate email", u.ID())

	SendAsync(msg)
}
