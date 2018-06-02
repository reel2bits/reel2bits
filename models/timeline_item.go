package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"github.com/jinzhu/gorm"
	log "github.com/sirupsen/logrus"
)

// TimelineItem database structure
type TimelineItem struct {
	gorm.Model

	UserID  uint `gorm:"INDEX"`
	User    User
	TrackID uint `gorm:"INDEX"`
	Track   Track
	AlbumID uint `gorm:"INDEX"`
	Album   Album
}

func isTimelineItemAlreadyExist(userID uint, trackID uint, albumID uint) (exist bool, err error) {
	tli := TimelineItem{}
	err = db.Where(&TimelineItem{UserID: userID, TrackID: trackID, AlbumID: albumID}).First(&tli).Error
	if gorm.IsRecordNotFoundError(err) || tli.ID == 0 {
		return false, nil
	} else if err != nil {
		return false, nil
	}
	return true, nil
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

	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if tx.Error != nil {
		return err
	}

	if err := tx.Create(ti).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

// DeleteTimelineItem delete an item from the timeline
func DeleteTimelineItem(userID uint, trackID uint, albumID uint) (err error) {
	tli := TimelineItem{}
	err = db.Where(&TimelineItem{UserID: userID, TrackID: trackID, AlbumID: albumID}).First(&tli).Error
	if gorm.IsRecordNotFoundError(err) || tli.ID == 0 {
		return errors.TimelineItemNotExist{UserID: userID, TrackID: trackID, AlbumID: albumID}
	} else if err != nil {
		return err
	}

	log.WithFields(log.Fields{
		"UserID":  tli.UserID,
		"TrackID": tli.TrackID,
		"AlbumID": tli.AlbumID,
	}).Info("Deleted timeline item")

	return db.Delete(tli).Error
}

// TimelineItemsOpts structure
type TimelineItemsOpts struct {
	Page     int
	PageSize int
}

// GetTimelineItems with options for pagination
func GetTimelineItems(opts *TimelineItemsOpts) (timelineItems []TimelineItem, count int64, err error) {
	if opts.Page <= 0 {
		opts.Page = 1
	}
	timelineItems = make([]TimelineItem, 0, opts.PageSize)

	err = db.Preload("User").Preload("Track").Preload("Album").Preload("Track.TrackInfo").Order("created_at DESC").Offset((opts.Page - 1) * opts.PageSize).Limit(opts.PageSize).Find(&timelineItems).Error
	db.Model(&TimelineItem{}).Select("id").Count(&count)
	return timelineItems, count, err
}
