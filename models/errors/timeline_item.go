package errors

import (
	"fmt"
)

// TimelineItemAlreadyExist struct
type TimelineItemAlreadyExist struct{}

// IsTimelineItemAlreadyExist bool
func IsTimelineItemAlreadyExist(err error) bool {
	_, ok := err.(TimelineItemAlreadyExist)
	return ok
}

func (err TimelineItemAlreadyExist) Error() string {
	return "TimelineItem already exists"
}

// TimelineItemNotExist struct
type TimelineItemNotExist struct {
	UserID  int64
	TrackID int64
	AlbumID int64
}

func (err TimelineItemNotExist) Error() string {
	return fmt.Sprintf("timeline item does not exist [userID: %d, trackID: %d, albumID: %d]",
		err.UserID,
		err.TrackID,
		err.AlbumID)
}
