// Copyright 2014 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package auth

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"strings"

	"github.com/go-macaron/session"
	log "github.com/sirupsen/logrus"
	"gopkg.in/macaron.v1"
)

// IsAPIPath or not ?
func IsAPIPath(url string) bool {
	return strings.HasPrefix(url, "/api/")
}

// SignedInID returns the id of signed in user.
func SignedInID(ctx *macaron.Context, sess session.Store) uint {
	if !models.HasEngine {
		return 0
	}

	uid := sess.Get("uid")
	if uid == nil {
		return 0
	}
	if id, ok := uid.(uint); ok {
		if _, err := models.GetUserByID(id); err != nil {
			if !errors.IsUserNotExist(err) {
				log.Errorf("GetUserByID: %v", err)
			}
			return 0
		}
		return id
	}
	return 0
}

// SignedInUser returns the user object of signed user.
// It returns a bool value to indicate whether user uses basic auth or not.
func SignedInUser(ctx *macaron.Context, sess session.Store) (user models.User, basicAuth bool) {
	if !models.HasEngine {
		return user, false
	}

	uid := SignedInID(ctx, sess)

	if uid <= 0 {
		return user, false
	}

	u, err := models.GetUserByID(uid)
	if err != nil {
		log.Errorf("GetUserById: %v", err)
		return u, false
	}
	return u, false
}
