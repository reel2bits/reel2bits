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
	IsPrivate bool `gorm:"DEFAULT 0"`
}

// BeforeSave Create slug
func (album *Album) BeforeSave() (err error) {
	album.Slug = slug.Make(album.Name)
	return nil
}

// BeforeUpdate Update slug
func (album *Album) BeforeUpdate() (err error) {
	album.Slug = slug.Make(album.Name)
	return nil
}

func (album *Album) getTracksCount(db *gorm.DB) (count int64, err error) {
	db.Model(&Track{}).Select("id").Where("album_id = ?", album.ID).Count(&count)
	return
}

// GetTracksCount 1+1=2
func (album *Album) GetTracksCount() (int64, error) {
	return album.getTracksCount(db)
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

	tx := db.Preload("User").Order("created_at ASC").Offset((opts.Page - 1) * opts.PageSize).Limit(opts.PageSize)

	if opts.WithPrivate && !opts.GetAll {
		tx = tx.Or("is_private = ?", true)
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
			log.Errorf("Deassociating album %d from track %d: %s", albumID, track.ID, err)
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
		log.Errorf("Error while deassociating tracks of album %d: %s", albumID, err)
	}

	log.Infof("Deleted album %d/%s", album.ID, album.Name)
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
