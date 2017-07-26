// Copyright 2017 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package errors

import "fmt"

// AlbumAlreadyExist struct
type AlbumAlreadyExist struct{}

// IsAlbumAlreadyExist bool
func IsAlbumAlreadyExist(err error) bool {
	_, ok := err.(AlbumAlreadyExist)
	return ok
}

func (err AlbumAlreadyExist) Error() string {
	return "track already exists"
}

/* **** */

// AlbumNotExist struct
type AlbumNotExist struct {
	AlbumID int64
	Name    string
}

func (err AlbumNotExist) Error() string {
	return fmt.Sprintf("album does not exist [album_id: %d, name: %s]", err.AlbumID, err.Name)
}
