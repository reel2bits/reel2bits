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
	ProcessingWaiting   = 1 // a.k.a ProcessingNeeded
	ProcessingStarted   = 2
	ProcessingFailed    = 3
	ProcessingFinished  = 4
	ProcessingNotNeeded = 5
	ProcessingRetrying  = 6
)

// Select between transcoding or metadatas state
const (
	TrackTranscoding = 1
	TrackMetadatas   = 2
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
	TranscodeNeeded uint // See models.BoolFalse
	TranscodeState  int
	MetadatasState  int

	TranscodeStart     time.Time `gorm:"-"`
	TranscodeStartUnix int64
	TranscodeStop      time.Time `gorm:"-"`
	TranscodeStopUnix  int64

	TrackInfoID uint `gorm:"INDEX"`
	TrackInfo   TrackInfo

	Ready uint `gorm:"DEFAULT:2"` // See models.BoolFalse

	// Permissions
	Private    uint `gorm:"DEFAULT:2"` // See models.BoolFalse
	ShowDlLink uint `gorm:"DEFAULT:1"` // See models.BoolTrue
}

// IsTranscodeNeeded from FakeBool
func (track Track) IsTranscodeNeeded() bool {
	realBool, _ := isABool(track.Private, BoolFalse) // in reality the defaultBool should be unused
	return realBool
}

// IsReady from FakeBool
func (track Track) IsReady() bool {
	realBool, _ := isABool(track.Ready, BoolFalse)
	return realBool
}

// IsPrivate from FakeBool
func (track Track) IsPrivate() bool {
	realBool, _ := isABool(track.Private, BoolFalse)
	return realBool
}

// CanShowDlLink from FakeBool
func (track Track) CanShowDlLink() bool {
	realBool, _ := isABool(track.ShowDlLink, BoolTrue)
	return realBool
}

// BeforeSave set default states
func (track *Track) BeforeSave() (err error) {
	track.Slug = slug.Make(track.Title)

	if track.IsTranscodeNeeded() {
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
		return false, nil
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
	t.Ready = boolToFake(state)

	err = db.Model(&Track{}).Update(t).Error
	if err != nil {
		return err
	}
	return nil
}

// GetTrackWithInfoBySlugAndUserID or error
func GetTrackWithInfoBySlugAndUserID(id uint, slug string) (track Track, err error) {
	err = db.Preload("TrackInfo").Preload("User").Where("user_id = ? AND slug = ?", id, slug).Find(&track).Error
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
func GetFirstTrackOfAlbum(albumID uint, onlyPublic bool) (track Track, err error) {
	tx := db.Preload("TrackInfo").Preload("User").Where("album_id = ?", albumID)

	if onlyPublic {
		tx = tx.Where("ready = ? AND private = ?", BoolTrue, BoolFalse)
	}

	err = tx.Order("album_order ASC").First(&track).Error
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

	tx := db.Model(&Track{}).Preload("TrackInfo").Preload("User").Order("created_at DESC").Offset((opts.Page - 1) * opts.PageSize).Limit(opts.PageSize)

	tx = tx.Where("private = ?", BoolFalse)

	if opts.WithPrivate && !opts.GetAll {
		tx = tx.Or("private = ?", BoolTrue)
	}

	if !opts.GetAll {
		tx = tx.Where("user_id = ?", opts.UserID)
	}
	if opts.OnlyReady {
		tx = tx.Where("ready = ?", BoolTrue)
	}

	err = tx.Find(&tracks).Error
	tx.Count(&count)

	return tracks, count, err
}

// GetNotReadyTracks and only that
func GetNotReadyTracks() (tracks []Track, err error) {
	err = db.Model(&Track{}).Where("ready = ?", BoolFalse).Find(&tracks).Error
	if err != nil {
		log.Errorf("Cannot get un-ready tracks: %s", err)
	}
	return tracks, err
}

// GetAlbumTracks will get album tracks
func GetAlbumTracks(albumID uint, onlyPublic bool) (tracks []Track, err error) {
	tracks = make([]Track, 0)

	tx := db.Preload("User").Where("album_id = ?", albumID)

	if onlyPublic {
		tx = tx.Where("ready = ? AND private = ?", BoolTrue, BoolFalse)
	}

	tx = tx.Order("album_order ASC")

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
	err = db.Where("id = ?", track.TrackInfoID).First(&trackInfo).Error
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
		return fmt.Errorf("delete track: %v", err)
	}

	// Don't do any delete if the trackInfo was not found (ID == 0)
	if trackInfo.ID > 0 {
		err = db.Delete(trackInfo).Error
		if err != nil {
			return fmt.Errorf("delete track info: %v", err)
		}
	}

	log.Infof("Deleted track record for %d/%s", track.ID, track.Title)

	removeTrackFiles(trackTranscoded, trackFilename, trackUser.Slug)

	return nil
}
