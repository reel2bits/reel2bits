package errors

import "fmt"

// EmptyTitle struct
type EmptyTitle struct{}

// IsEmptyTitle bool
func IsEmptyTitle(err error) bool {
	_, ok := err.(EmptyTitle)
	return ok
}

func (err EmptyTitle) Error() string {
	return "empty title"
}

/* **** */

// TrackAlreadyExist struct
type TrackAlreadyExist struct{}

// IsTrackAlreadyExist bool
func IsTrackAlreadyExist(err error) bool {
	_, ok := err.(TrackAlreadyExist)
	return ok
}

func (err TrackAlreadyExist) Error() string {
	return "track already exists"
}

/* **** */

// TrackNotExist struct
type TrackNotExist struct {
	TrackID uint
	Title   string
}

func (err TrackNotExist) Error() string {
	return fmt.Sprintf("track does not exist [track_id: %d, title: %s]", err.TrackID, err.Title)
}

/* **** */

// TrackInfoNotExist struct
type TrackInfoNotExist struct {
	TrackInfoID uint
}

func (err TrackInfoNotExist) Error() string {
	return fmt.Sprintf("track info does not exist [track_info_id: %d]", err.TrackInfoID)
}
