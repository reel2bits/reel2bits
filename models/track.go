package models

import (
	"crypto/sha1"
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"encoding/hex"
	"fmt"
	"github.com/gosimple/slug"
	"github.com/jinzhu/gorm"
	log "github.com/sirupsen/logrus"
	"io"
	"io/ioutil"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Also used in TrackInfo, it's a generic state list
const (
	ProcessingWaiting   = 0
	ProcessingStarted   = 1
	ProcessingFailed    = 2
	ProcessingFinished  = 3
	ProcessingNotNeeded = 4
	ProcessingRetrying  = 5
)

// Select between transcoding or metadatas state
const (
	TrackTranscoding = 0
	TrackMetadatas   = 1
)

// Track database structure
type Track struct {
	gorm.Model

	Hash   string `gorm:"UNIQUE NOT NULL"`
	UserID uint   `gorm:"INDEX"`
	User   User

	Title       string
	Description string `gorm:"TEXT"`
	Slug        string

	Filename     string // crafted from hash, filename on filesystem, used for original file, with extension.
	FilenameOrig string // original filename without extension

	Mimetype string

	AlbumID    uint
	Album      Album
	AlbumOrder int64

	// Transcode state is also used for the worker job to fetch infos
	TranscodeNeeded bool
	TranscodeState  int
	MetadatasState  int

	TranscodeStart     time.Time `gorm:"-"`
	TranscodeStartUnix int64
	TranscodeStop      time.Time `gorm:"-"`
	TranscodeStopUnix  int64

	TrackInfoID uint `gorm:"INDEX"`
	TrackInfo   TrackInfo

	Ready bool `gorm:"DEFAULT 0"` // ready means "can be shown to public, if not IsPrivate anyway

	// Permissions
	IsPrivate  bool `gorm:"DEFAULT 0"`
	ShowDlLink bool `gorm:"DEFAULT 1"`
}

// BeforeSave set default states
func (track *Track) BeforeSave() (err error) {
	track.Slug = slug.Make(track.Title)

	if track.TranscodeNeeded {
		track.TranscodeState = ProcessingWaiting
	} else {
		track.TranscodeState = ProcessingNotNeeded
	}
	track.MetadatasState = ProcessingWaiting
	return
}

// BeforeUpdate set slug
func (track *Track) BeforeUpdate() {
	track.Slug = slug.Make(track.Title)
}

// AfterFind set times
func (track *Track) AfterFind() (err error) {
	track.TranscodeStart = time.Unix(track.TranscodeStartUnix, 0).Local()
	track.TranscodeStop = time.Unix(track.TranscodeStopUnix, 0).Local()
	return
}

// GenerateHash of the track
func GenerateHash(title string, userID uint) string {
	h := sha1.New()
	io.WriteString(h, fmt.Sprintf("%s %d %d", title, time.Now().Unix(), userID))
	return hex.EncodeToString(h.Sum(nil))
}

// SaveTrackFile to filesystem
func SaveTrackFile(file *multipart.FileHeader, filename string, username string) (string, error) {
	storDir := filepath.Join(setting.Storage.Path, "tracks", username)
	log.Debugf("Track will be uploaded to to: %s", storDir)
	err := os.MkdirAll(storDir, os.ModePerm)
	if err != nil {
		log.Errorf("Cannot create directory '%s': %s", storDir, err)
		return "", err
	}

	fPath := filepath.Join(storDir, filename)
	fw, err := os.Create(fPath)
	if err != nil {
		log.Errorf("Error opening file '%s' to write track: %s", fPath, err)
		return "", err
	}
	defer fw.Close()

	fr, err := file.Open()
	if err != nil {
		log.Errorf("Error opening uploaded file to read content: %s", err)
		return "", err
	}
	defer fr.Close()

	data, err := ioutil.ReadAll(fr)
	if err != nil {
		return "", fmt.Errorf("ioutil.ReadAll: %v", err)
	}

	_, err = fw.Write(data)
	if err != nil {
		log.Errorf("Error writing data to track file %s: %s", fPath, err)
		return "", err
	}

	mimetype, err := tool.GetBlobMimeType(data)
	if err != nil {
		log.Errorf("Error reading temp uploaded file: %s", err)
		return "", err
	}

	log.Infof("Track saved to %s", fPath)
	return mimetype, nil
}

func isTrackTitleAlreadyExist(title string, userID uint) (exist bool, err error) {
	if len(title) == 0 {
		return true, fmt.Errorf("title is empty")
	}
	if userID < 0 {
		return true, fmt.Errorf("wtf are you doing")
	}

	track := Track{}
	err = db.Where(&Track{UserID: userID, Title: title}).First(&track).Error
	if gorm.IsRecordNotFoundError(err) || track.ID == 0 {
		return false, ErrTrackTitleAlreadyExist{Title: title}
	} else if err != nil {
		return false, nil
	}
	return true, nil
}

// CreateTrack or error
func CreateTrack(t *Track) (err error) {
	trackTitleAlreadyExist, err := isTrackTitleAlreadyExist(t.Title, t.UserID)
	if err != nil {
		return err
	}
	if trackTitleAlreadyExist {
		return ErrTrackTitleAlreadyExist{}
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

	if err := tx.Create(t).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

func updateTrack(t *Track) (err error) {
	tx := db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	if tx.Error != nil {
		return err
	}

	if err := tx.Save(t).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Commit().Error; err != nil {
		return err
	}

	return err
}

// UpdateTrack Update a Track
func UpdateTrack(t *Track) error {
	return updateTrack(t)
}

// UpdateTrackState Update track states
func UpdateTrackState(trackID uint, t *Track, what int) (err error) {
	switch what {
	case TrackTranscoding:
		err = db.Model(&Track{}).Where("id = ?", trackID).UpdateColumn(t).Error
		if err != nil {
			return err
		}
	case TrackMetadatas:
		err = db.Model(&Track{}).Where("id = ?", trackID).UpdateColumn(t).Error
		if err != nil {
			return err
		}
	}
	return nil
}

func getTrackByID(id uint) (track Track, err error) {
	err = db.Where("id = ?", id).First(&track).Error
	if gorm.IsRecordNotFoundError(err) || track.ID == 0 {
		return track, errors.TrackNotExist{TrackID: id, Title: ""}
	} else if err != nil {
		return track, err
	}
	return
}

// GetTrackByID or error
func GetTrackByID(id uint) (Track, error) {
	return getTrackByID(id)
}

// SetTrackReadyness or not
func SetTrackReadyness(id uint, state bool) (err error) {
	t, err := getTrackByID(id)
	if err != nil {
		return err
	}
	t.Ready = state

	err = db.Model(&Track{}).Update(t).Error
	if err != nil {
		return err
	}
	return nil
}

// GetTrackWithInfoBySlugAndUserID or error
func GetTrackWithInfoBySlugAndUserID(id uint, slug string) (track Track, err error) {
	err = db.Preload("TrackInfo").Where("track.user_id = ? AND track.slug = ?", id, slug).Find(&track).Error
	return track, nil
}

// GetTrackBySlugAndUserID or error
func GetTrackBySlugAndUserID(id uint, slug string) (track Track, err error) {
	err = db.Where(&Album{UserID: id, Slug: slug}).First(&track).Error
	if gorm.IsRecordNotFoundError(err) || track.ID == 0 {
		return track, errors.TrackNotExist{TrackID: id, Title: ""}
	} else if err != nil {
		return track, err
	}
	return
}

// GetTrackByAlbumIDAndOrder like it's said
func GetTrackByAlbumIDAndOrder(albumID uint, albumOrder int64) (track Track, err error) {
	err = db.Where(&Track{AlbumID: albumID, AlbumOrder: albumOrder}).First(&track).Error
	if gorm.IsRecordNotFoundError(err) || track.ID == 0 {
		return track, errors.TrackNotExist{TrackID: albumID, Title: ""}
	} else if err != nil {
		return track, err
	}
	return
}

// GetFirstTrackOfAlbum and not the last
// IF the album is empty, an error will be thrown by the .Find()
func GetFirstTrackOfAlbum(albumID uint, onlyPublic bool) (track *Track, err error) {
	tx := db.Preload("track_info", "user").Where("album_id = ?", albumID)

	if onlyPublic {
		tx = tx.Where("ready = ? AND is_private = ?", true, false)
	}

	err = tx.Order("track.album_order ASC").Limit(1).Find(&track).Error
	return
}

// TrackOptions structure
type TrackOptions struct {
	UserID      uint
	WithPrivate bool
	GetAll      bool
	Page        int
	PageSize    int
	OnlyReady   bool
}

// GetTracks or nothing
func GetTracks(opts *TrackOptions) (tracks []Track, count int64, err error) {
	if opts.Page <= 0 {
		opts.Page = 1
	}
	tracks = make([]Track, 0, opts.PageSize)

	tx := db.Preload("track_info", "user").Order("track.created_at DESC").Offset((opts.Page - 1) * opts.PageSize).Limit(opts.PageSize)

	tx = tx.Where("is_private = ?", false)

	if opts.WithPrivate && !opts.GetAll {
		tx = tx.Or("is_private = ?", true)
	}

	if !opts.GetAll {
		tx = tx.Where("user_id = ?", opts.UserID)
	}
	if opts.OnlyReady {
		tx = tx.Where("ready = ?", true)
	}

	err = tx.Find(&tracks).Error
	tx.Count(&count)

	return tracks, count, err
}

// GetNotReadyTracks and only that
func GetNotReadyTracks() (tracks []Track, err error) {
	err = db.Model(&Track{}).Where("ready = ?", false).Find(&tracks).Error
	if err != nil {
		log.Errorf("Cannot get un-ready tracks: %s", err)
	}
	return tracks, err
}

// GetAlbumTracks will get album tracks
func GetAlbumTracks(albumID uint, onlyPublic bool) (tracks []Track, err error) {
	tracks = make([]Track, 0)

	tx := db.Preload("track_user", "user").Where("album_id = ?", albumID)

	if onlyPublic {
		tx = tx.Where("ready = ? AND is_private = ?", true, false)
	}

	tx = tx.Order("track.album_order ASC")

	err = tx.Find(&tracks).Error

	return tracks, err
}

func removeTrackFiles(transcode bool, trackFilename string, userSlug string) error {
	storDir := filepath.Join(setting.Storage.Path, "tracks", userSlug)
	fName := filepath.Join(storDir, trackFilename)
	fJSON := filepath.Join(storDir, trackFilename+".json")
	fPNG := filepath.Join(storDir, trackFilename+".png")

	err := os.RemoveAll(fName)
	if err != nil {
		log.Errorf("Cannot remove orig file '%s': %s", fName, err)
	} else {
		log.Infof("File removed: %s", fName)
	}

	err = os.RemoveAll(fJSON)
	if err != nil {
		log.Errorf("Cannot remove json file '%s': %s", fJSON, err)
	} else {
		log.Infof("File removed: %s", fJSON)
	}

	err = os.RemoveAll(fPNG)
	if err != nil {
		log.Errorf("Cannot remove png file '%s': %s", fPNG, err)
	} else {
		log.Infof("File removed: %s", fPNG)
	}

	if transcode {
		fTranscode := fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))

		err = os.RemoveAll(fTranscode)
		if err != nil {
			log.Errorf("Cannot remove transcode file '%s': %s", fTranscode, err)
		} else {
			log.Infof("File removed: %s", fTranscode)
		}
	}

	return nil
}

// DeleteTrack will delete a track
func DeleteTrack(trackID uint, userID uint) (err error) {

	// With session

	// Delete TrackInfo

	// Future: Delete stats record

	// Delete Track

	// Commit

	// Get track
	track := &Track{}
	err = db.Where("id = ?", trackID).First(&track).Error
	if gorm.IsRecordNotFoundError(err) || track.ID == 0 {
		return errors.TrackNotExist{TrackID: trackID, Title: ""}
	} else if err != nil {
		return err
	}

	trackFilename := track.Filename
	trackTranscoded := track.TranscodeState != ProcessingNotNeeded

	// Get track info
	trackInfo := &TrackInfo{}
	err = db.Where("track_id = ?", trackID).First(&trackInfo).Error
	if gorm.IsRecordNotFoundError(err) || trackInfo.ID == 0 {
		// do nothing
	} else if err != nil {
		return err
	}
	// We don't care if the trackInfo does not exists

	trackUser, err := GetUserByID(userID)
	if err != nil {
		return fmt.Errorf("GetUserByID: %v", err)
	}

	err = db.Delete(track).Error
	if err != nil {
		return fmt.Errorf("Delete track: %v", err)
	}

	err = db.Delete(trackInfo).Error
	if err != nil {
		return fmt.Errorf("Delete track info: %v", err)
	}

	log.Infof("Deleted track record for %d/%s", track.ID, track.Title)

	removeTrackFiles(trackTranscoded, trackFilename, trackUser.Slug)

	return nil
}
