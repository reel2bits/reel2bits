package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"fmt"
	"github.com/go-xorm/xorm"
	"github.com/gosimple/slug"
	log "gopkg.in/clog.v1"
	"time"
)

// Album database structure
type Album struct {
	ID     int64 `xorm:"pk autoincr"`
	UserID int64

	Name        string
	Description string `xorm:"TEXT"`
	Slug        string

	// Permissions
	IsPrivate bool `xorm:"DEFAULT 0"`

	Created     time.Time `xorm:"-"`
	CreatedUnix int64
	Updated     time.Time `xorm:"-"`
	UpdatedUnix int64

	// Relations
	// 	UserID
}

// BeforeInsert set times and default states
func (album *Album) BeforeInsert() {
	album.CreatedUnix = time.Now().Unix()
	album.UpdatedUnix = album.CreatedUnix
	album.Slug = slug.Make(album.Name)

}

// BeforeUpdate set times
func (album *Album) BeforeUpdate() {
	album.UpdatedUnix = time.Now().Unix()
	album.Slug = slug.Make(album.Name)
}

// AfterSet set times
func (album *Album) AfterSet(colName string, _ xorm.Cell) {
	switch colName {
	case "created_unix":
		album.Created = time.Unix(album.CreatedUnix, 0).Local()
	case "updated_unix":
		album.Updated = time.Unix(album.UpdatedUnix, 0).Local()
	}
}

func (album *Album) getTracksCount(e Engine) (int64, error) {
	return e.Where("album_id=?", album.ID).Count(new(Track))
}

// GetTracksCount 1+1=2
func (album *Album) GetTracksCount() (int64, error) {
	return album.getTracksCount(x)
}

func isAlbumNameAlreadyExist(name string, userID int64) (bool, error) {
	if len(name) == 0 {
		return true, fmt.Errorf("name is empty")
	}
	if userID < 0 {
		return true, fmt.Errorf("wtf are you doing ?")
	}

	exists, err := x.Get(&Album{UserID: userID, Name: name})
	if err != nil {
		return true, err
	}

	if exists {
		return true, nil
	}

	return false, nil
}

// CreateAlbum or error
func CreateAlbum(a *Album) (err error) {
	albumNameAlreadyExist, err := isAlbumNameAlreadyExist(a.Name, a.UserID)
	if err != nil {
		return err
	}
	if albumNameAlreadyExist {
		return ErrAlbumNameAlreadyExist{}
	}

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Insert(a); err != nil {
		return err
	}

	return sess.Commit()
}

func updateAlbum(e Engine, a *Album) error {
	_, err := e.Id(a.ID).AllCols().Update(a)
	return err
}

// UpdateAlbum Update an Album
func UpdateAlbum(a *Album) error {
	return updateAlbum(x, a)
}

func getAlbumByID(e Engine, id int64) (*Album, error) {
	t := new(Album)
	has, err := e.Id(id).Get(t)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.AlbumNotExist{id, ""}
	}
	return t, nil
}

// GetAlbumByID or error
func GetAlbumByID(id int64) (*Album, error) {
	return getAlbumByID(x, id)
}

// GetAlbumBySlugAndUserID or error
func GetAlbumBySlugAndUserID(id int64, slug string) (*Album, error) {
	album := &Album{Slug: slug, UserID: id}
	has, err := x.Get(album)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.AlbumNotExist{id, ""}
	}
	return album, nil
}

// AlbumOptions structure
type AlbumOptions struct {
	UserID      int64
	WithPrivate bool
	GetAll      bool
	Page        int
	PageSize    int
}

// GetAlbums or nothing
func GetAlbums(opts *AlbumOptions) (albums []*Album, _ int64, _ error) {
	if opts.Page <= 0 {
		opts.Page = 1
	}
	albums = make([]*Album, 0, opts.PageSize)

	sess := x.Where("is_private=?", false)

	if opts.WithPrivate && !opts.GetAll {
		sess.Or("is_private=?", true)
	}

	if !opts.GetAll {
		sess.And("user_id=?", opts.UserID)
	}

	sess.Desc("album.created_unix")

	var countSess xorm.Session
	countSess = *sess
	count, err := countSess.Count(new(Album))
	if err != nil {
		return nil, 0, fmt.Errorf("Count: %v", err)
	}

	sess.Table(&Album{})

	return albums, count, sess.Limit(opts.PageSize, (opts.Page-1)*opts.PageSize).Find(&albums)
}

func getTracksAndDeassociate(albumID int64) error {
	tracks, err := GetAlbumTracks(albumID, false)
	if err != nil {
		return err
	}
	for _, track := range tracks {
		track.Track.AlbumID = -1
		track.Track.AlbumOrder = -1
		err := UpdateTrack(&track.Track)
		if err != nil {
			log.Error(2, "Deassociating album %d from track %d: %s", albumID, track.Track.ID, err)
		}
	}
	return nil
}

// DeleteAlbum delete album
func DeleteAlbum(albumID int64, userID int64) error {
	// Get album
	album := &Album{ID: albumID, UserID: userID}
	hasAlbum, err := x.Get(album)
	if err != nil {
		return err
	} else if !hasAlbum {
		return errors.AlbumNotExist{albumID, ""}
	}

	if err = getTracksAndDeassociate(album.ID); err != nil {
		log.Error(2, "Error while deassociating tracks of album %d: %s", albumID, err)
	}

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Delete(&Album{ID: albumID}); err != nil {
		return fmt.Errorf("sess.Delete Album: %v", err)
	}

	if err = sess.Commit(); err != nil {
		return fmt.Errorf("Commit: %v", err)
	}

	log.Info("Deleted album for %d/%s", album.ID, album.Name)

	return nil
}

// GetMapNameIDOfAlbums returns a []Album of albums
func GetMapNameIDOfAlbums(userID int64) (sets []Album, err error) {
	err = x.Table(&Album{}).Cols("id", "name").Where("user_id=?", userID).Find(&sets)
	if err != nil {
		log.Error(2, "Cannot get albums for user id %d: %s", userID, err)
	}
	return sets, err
}

// GetCountOfAlbumTracks to be used when album.CountTracksblahblah() cannot be used
// To be deprecated at some point
func GetCountOfAlbumTracks(albumID int64) (count int64, err error) {
	track := new(Track)
	count, err = x.Where("album_id=?", albumID).Count(track)
	return
}
