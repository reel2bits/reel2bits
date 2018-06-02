package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"fmt"
	"github.com/gosimple/slug"
	"github.com/jinzhu/gorm"
	log "github.com/sirupsen/logrus"
)

// Album database structure
type Album struct {
	gorm.Model

	UserID uint
	User   User

	Name        string
	Description string `gorm:"TEXT"`
	Slug        string

	// Permissions
	Private uint `gorm:"DEFAULT:2"` // see models.BoolFalse
}

// IsPrivate from FakeBool
func (album Album) IsPrivate() bool {
	realBool, _ := isABool(album.Private, BoolFalse)
	return realBool
}

// AfterSave Create slug
func (album *Album) AfterSave(tx *gorm.DB) (err error) {
	if album.ID == 0 {
		return // Ignore if we have nothing useful to do
	}
	log.Infof("AfterSave ID %d", album.ID)
	nameSlug := slug.Make(fmt.Sprintf("%d-%s", album.ID, album.Name))
	tx.Model(&Album{}).Where("id = ?", album.ID).Update("slug", nameSlug)
	return
}

func (album *Album) getTracksCount(onlyPublic bool) (count int64, err error) {
	tx := db.Model(&Track{}).Select("id").Where("album_id = ?", album.ID)
	if onlyPublic {
		tx = tx.Where("private = ?", boolToFake(false))
	}
	tx.Count(&count)
	return
}

// GetTracksCount 1+1=2
func (album *Album) GetTracksCount(onlyPublic bool) (int64, error) {
	return album.getTracksCount(onlyPublic)
}

func isAlbumNameAlreadyExist(db *gorm.DB, name string, userID uint) (exist bool, err error) {
	if len(name) == 0 {
		return true, fmt.Errorf("name is empty")
	}
	if userID < 0 {
		return true, fmt.Errorf("wtf are you doing")
	}

	album := Album{}
	err = db.Where(&Album{UserID: userID, Name: name}).First(&album).Error
	if gorm.IsRecordNotFoundError(err) || album.ID == 0 {
		return false, nil
	} else if err != nil {
		return false, nil
	}
	return true, nil
}

// CreateAlbum or error
func CreateAlbum(a *Album) (err error) {
	albumNameAlreadyExist, err := isAlbumNameAlreadyExist(db, a.Name, a.UserID)
	if err != nil {
		return err
	}
	if albumNameAlreadyExist {
		return ErrAlbumNameAlreadyExist{}
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

	if err := tx.Create(a).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

func updateAlbum(db *gorm.DB, a *Album) (err error) {
	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if tx.Error != nil {
		return err
	}

	if err := tx.Save(a).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

// UpdateAlbum Update an Album
func UpdateAlbum(a *Album) error {
	return updateAlbum(db, a)
}

func getAlbumByID(id uint) (album Album, err error) {
	err = db.Preload("User").Where("id = ?", id).First(&album).Error
	if gorm.IsRecordNotFoundError(err) || album.ID == 0 {
		return album, errors.AlbumNotExist{AlbumID: id, Name: ""}
	} else if err != nil {
		return album, err
	}
	return
}

// GetAlbumByID or error
func GetAlbumByID(id uint) (Album, error) {
	return getAlbumByID(id)
}

// GetAlbumBySlugAndUserID or error
func GetAlbumBySlugAndUserID(id uint, slug string) (album Album, err error) {
	err = db.Where(&Album{UserID: id, Slug: slug}).First(&album).Error
	if gorm.IsRecordNotFoundError(err) || album.ID == 0 {
		return album, errors.AlbumNotExist{AlbumID: id, Name: ""}
	} else if err != nil {
		return album, err
	}
	return
}

// AlbumOptions structure
type AlbumOptions struct {
	UserID      uint
	WithPrivate bool
	GetAll      bool
	Page        int
	PageSize    int
}

// GetAlbums or nothing
func GetAlbums(opts *AlbumOptions) (albums []Album, itemsCount int64, err error) {
	if opts.Page <= 0 {
		opts.Page = 1
	}

	albums = make([]Album, 0, opts.PageSize)

	tx := db.Model(&Album{}).Preload("User").Order("created_at DESC").Offset((opts.Page - 1) * opts.PageSize).Limit(opts.PageSize)

	if opts.WithPrivate && !opts.GetAll {
		tx = tx.Or("private = ?", BoolTrue)
	} else if !opts.WithPrivate && !opts.GetAll {
		tx = tx.Where("private = ?", BoolFalse)
	}

	if !opts.GetAll {
		tx = tx.Where("user_id = ?", opts.UserID)
	}

	err = tx.Find(&albums).Error
	tx.Count(&itemsCount)

	return albums, itemsCount, err
}

func getTracksAndDeassociate(albumID uint) error {
	tracks, err := GetAlbumTracks(albumID, false)
	if err != nil {
		return err
	}
	// 0 should be considered as "deassociated"
	for _, track := range tracks {
		track.AlbumID = 0
		track.AlbumOrder = 0
		err := UpdateTrack(&track)
		if err != nil {
			log.WithFields(log.Fields{
				"album ID": albumID,
				"track ID": track.ID,
			}).Errorf("Deassociating album from track: %v", err)
		}
	}
	return nil
}

// DeleteAlbum delete album
func DeleteAlbum(albumID uint, userID uint) (err error) {
	// Get album
	album := &Album{}
	err = db.Preload("User").Where("id = ? AND user_id = ?", albumID, userID).First(&album).Error
	if gorm.IsRecordNotFoundError(err) || album.ID == 0 {
		return errors.AlbumNotExist{AlbumID: albumID, Name: ""}
	} else if err != nil {
		return err
	}

	if err = getTracksAndDeassociate(album.ID); err != nil {
		log.WithFields(log.Fields{
			"album ID": albumID,
		}).Errorf("Deassociating album tracks: %v", err)
	}

	log.WithFields(log.Fields{
		"album ID":   album.ID,
		"track name": album.Name,
	}).Infof("Album deleted")

	return db.Delete(album).Error
}

// GetMapNameIDOfAlbums returns a []Album of albums
func GetMapNameIDOfAlbums(userID uint) (sets []Album, err error) {
	err = db.Model(&Album{}).Select("id, name").Where("user_id = ?", userID).Find(&sets).Error
	return
}

// GetCountOfAlbumTracks to be used when album.CountTracksblahblah() cannot be used
// To be deprecated at some point
func GetCountOfAlbumTracks(albumID uint) (count int64, err error) {
	err = db.Model(&Track{}).Where("album_id = ?", albumID).Count(&count).Error
	return
}
