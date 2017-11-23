package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"fmt"
	"github.com/go-xorm/xorm"
	log "github.com/sirupsen/logrus"
	"time"
)

// TimelineItem database structure
type TimelineItem struct {
	ID int64 `xorm:"pk autoincr"`

	UserID  int64 `xorm:"INDEX"`
	TrackID int64 `xorm:"INDEX"`
	AlbumID int64 `xorm:"INDEX"`

	Created     time.Time `xorm:"-"`
	CreatedUnix int64
	Updated     time.Time `xorm:"-"`
	UpdatedUnix int64
}

// BeforeInsert set times and slug
func (timelineItem *TimelineItem) BeforeInsert() {
	timelineItem.CreatedUnix = time.Now().Unix()
	timelineItem.UpdatedUnix = timelineItem.CreatedUnix
}

// BeforeUpdate set times
func (timelineItem *TimelineItem) BeforeUpdate() {
	timelineItem.UpdatedUnix = time.Now().Unix()
}

// AfterSet set times
func (timelineItem *TimelineItem) AfterSet(colName string, _ xorm.Cell) {
	switch colName {
	case "created_unix":
		timelineItem.Created = time.Unix(timelineItem.CreatedUnix, 0).Local()
	case "updated_unix":
		timelineItem.Updated = time.Unix(timelineItem.UpdatedUnix, 0).Local()
	}
}

func isTimelineItemAlreadyExist(userID int64, trackID int64, albumID int64) (bool, error) {
	exists, err := x.Get(&TimelineItem{UserID: userID, TrackID: trackID, AlbumID: albumID})
	if err != nil {
		return true, err
	}

	if exists {
		return true, nil
	}

	return false, nil
}

// CreateTimelineItem or error
func CreateTimelineItem(ti *TimelineItem) (err error) {
	timelineItemAlreadyExist, err := isTimelineItemAlreadyExist(ti.UserID, ti.TrackID, ti.AlbumID)
	if err != nil {
		return err
	}
	if timelineItemAlreadyExist {
		return ErrTimelineItemAlreadyExist{}
	}

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Insert(ti); err != nil {
		return err
	}

	return sess.Commit()
}

// DeleteTimelineItem delete an item from the timeline
func DeleteTimineItem(userID int64, trackID int64, albumID int64) error {
	timelineItem := &TimelineItem{UserID: userID, TrackID: trackID, AlbumID: albumID}
	hasTimelineItem, err := x.Get(timelineItem)
	if err != nil {
		return err
	} else if !hasTimelineItem {
		return errors.TimelineItemNotExist{UserID: userID, TrackID: trackID, AlbumID: albumID}
	}

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Delete(&TimelineItem{UserID: userID, TrackID: trackID, AlbumID: albumID}); err != nil {
		return fmt.Errorf("sess.Delete TimelineItem: %v", err)
	}

	if err = sess.Commit(); err != nil {
		return fmt.Errorf("Commit: %v", err)
	}

	log.WithFields(log.Fields{
		"UserID":  timelineItem.UserID,
		"TrackID": timelineItem.TrackID,
		"AlbumID": timelineItem.AlbumID,
	}).Info("Deleted timeline item")

	return nil
}

// GetTimelineItems
