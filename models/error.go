// Copyright 2015 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package models

import (
	"fmt"
)

// ErrNameReserved struct
type ErrNameReserved struct {
	Name string
}

// IsErrNameReserved bool
func IsErrNameReserved(err error) bool {
	_, ok := err.(ErrNameReserved)
	return ok
}

func (err ErrNameReserved) Error() string {
	return fmt.Sprintf("name is reserved [name: %s]", err.Name)
}

// ErrNamePatternNotAllowed struct
type ErrNamePatternNotAllowed struct {
	Pattern string
}

// IsErrNamePatternNotAllowed bool
func IsErrNamePatternNotAllowed(err error) bool {
	_, ok := err.(ErrNamePatternNotAllowed)
	return ok
}

func (err ErrNamePatternNotAllowed) Error() string {
	return fmt.Sprintf("name pattern is not allowed [pattern: %s]", err.Pattern)
}

//  ____ ___
// |    |   \______ ___________
// |    |   /  ___// __ \_  __ \
// |    |  /\___ \\  ___/|  | \/
// |______//____  >\___  >__|
//              \/     \/

// ErrUserAlreadyExist struct
type ErrUserAlreadyExist struct {
	Name string
}

// IsErrUserAlreadyExist bool
func IsErrUserAlreadyExist(err error) bool {
	_, ok := err.(ErrUserAlreadyExist)
	return ok
}

func (err ErrUserAlreadyExist) Error() string {
	return fmt.Sprintf("user already exists [name: %s]", err.Name)
}

// ErrEmailAlreadyUsed struct
type ErrEmailAlreadyUsed struct {
	Email string
}

// IsErrEmailAlreadyUsed bool
func IsErrEmailAlreadyUsed(err error) bool {
	_, ok := err.(ErrEmailAlreadyUsed)
	return ok
}

func (err ErrEmailAlreadyUsed) Error() string {
	return fmt.Sprintf("e-mail has been used [email: %s]", err.Email)
}

// ErrTrackTitleAlreadyExist struct
type ErrTrackTitleAlreadyExist struct {
	Title string
}

// IsErrTrackTitleAlreadyExist bool
func IsErrTrackTitleAlreadyExist(err error) bool {
	_, ok := err.(ErrTrackTitleAlreadyExist)
	return ok
}
func (err ErrTrackTitleAlreadyExist) Error() string {
	return fmt.Sprintf("title already exists [title: %s]", err.Title)
}

// ErrAlbumNameAlreadyExist struct
type ErrAlbumNameAlreadyExist struct {
	Title string
}

// IsErrAlbumNameAlreadyExist bool
func IsErrAlbumNameAlreadyExist(err error) bool {
	_, ok := err.(ErrAlbumNameAlreadyExist)
	return ok
}
func (err ErrAlbumNameAlreadyExist) Error() string {
	return fmt.Sprintf("name already exists [name: %s]", err.Title)
}