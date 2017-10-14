package models

import (
	"crypto/sha1"
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"dev.sigpipe.me/dashie/reel2bits/pkg/tool"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"encoding/hex"
	"fmt"
	"github.com/go-xorm/xorm"
	"github.com/gosimple/slug"
	log "gopkg.in/clog.v1"
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
	ID     int64  `xorm:"pk autoincr"`
	Hash   string `xorm:"UNIQUE NOT NULL"`
	UserID int64  `xorm:"INDEX"`

	Title       string
	Description string `xorm:"TEXT"`
	Slug        string

	Filename     string // crafted from hash, filename on filesystem, used for original file, with extension.
	FilenameOrig string // original filename without extension

	Mimetype string

	AlbumID    int64
	AlbumOrder int64

	// Transcode state is also used for the worker job to fetch infos
	TranscodeNeeded bool
	TranscodeState  int
	MetadatasState  int

	TranscodeStart     time.Time `xorm:"-"`
	TranscodeStartUnix int64
	TranscodeStop      time.Time `xorm:"-"`
	TranscodeStopUnix  int64

	Ready bool `xorm:"DEFAULT 0"` // ready means "can be shown to public, if not IsPrivate anyway

	// Permissions
	IsPrivate  bool `xorm:"DEFAULT 0"`
	ShowDlLink bool `xorm:"DEFAULT 1"`

	Created     time.Time `xorm:"-"`
	CreatedUnix int64
	Updated     time.Time `xorm:"-"`
	UpdatedUnix int64

	// Relations
	// 	UserID
	//  AlbumID
}

// TrackWithInfo to be used for JOINs
type TrackWithInfo struct {
	Track     `xorm:"extends"`
	TrackInfo `xorm:"extends"`
	User      `xorm:"extends"`
}

// BeforeInsert set times and default states
func (track *Track) BeforeInsert() {
	track.CreatedUnix = time.Now().Unix()
	track.UpdatedUnix = track.CreatedUnix
	track.Slug = slug.Make(track.Title)

	if track.TranscodeNeeded {
		track.TranscodeState = ProcessingWaiting
	} else {
		track.TranscodeState = ProcessingNotNeeded
	}
	track.MetadatasState = ProcessingWaiting
}

// BeforeUpdate set times
func (track *Track) BeforeUpdate() {
	track.UpdatedUnix = time.Now().Unix()
	track.Slug = slug.Make(track.Title)
}

// AfterSet set times
func (track *Track) AfterSet(colName string, _ xorm.Cell) {
	switch colName {
	case "created_unix":
		track.Created = time.Unix(track.CreatedUnix, 0).Local()
	case "updated_unix":
		track.Updated = time.Unix(track.UpdatedUnix, 0).Local()
	case "transcode_start_unix":
		track.TranscodeStart = time.Unix(track.TranscodeStartUnix, 0).Local()
	case "transcode_stop_unix":
		track.TranscodeStop = time.Unix(track.TranscodeStopUnix, 0).Local()
	}
}

// GenerateHash of the track
func GenerateHash(title string, userID int64) string {
	h := sha1.New()
	io.WriteString(h, fmt.Sprintf("%s %d %d", title, time.Now().Unix(), userID))
	return hex.EncodeToString(h.Sum(nil))
}

// SaveTrackFile to filesystem
func SaveTrackFile(file *multipart.FileHeader, filename string, username string) (string, error) {
	storDir := filepath.Join(setting.Storage.Path, "tracks", username)
	log.Trace("Track will be uploaded to to: %s", storDir)
	err := os.MkdirAll(storDir, os.ModePerm)
	if err != nil {
		log.Error(2, "Cannot create directory '%s': %s", storDir, err)
		return "", err
	}

	fPath := filepath.Join(storDir, filename)
	fw, err := os.Create(fPath)
	if err != nil {
		log.Error(2, "Error opening file '%s' to write track: %s", fPath, err)
		return "", err
	}
	defer fw.Close()

	fr, err := file.Open()
	if err != nil {
		log.Error(2, "Error opening uploaded file to read content: %s", err)
		return "", err
	}
	defer fr.Close()

	data, err := ioutil.ReadAll(fr)
	if err != nil {
		return "", fmt.Errorf("ioutil.ReadAll: %v", err)
	}

	_, err = fw.Write(data)
	if err != nil {
		log.Error(2, "Error writing data to track file %s: %s", fPath, err)
		return "", err
	}

	mimetype, err := tool.GetBlobMimeType(data)
	if err != nil {
		log.Error(2, "Error reading temp uploaded file: %s", err)
		return "", err
	}

	log.Info("Track saved to %s", fPath)
	return mimetype, nil
}

func isTrackTitleAlreadyExist(title string, userID int64) (bool, error) {
	if len(title) == 0 {
		return true, fmt.Errorf("title is empty")
	}
	if userID < 0 {
		return true, fmt.Errorf("wtf are you doing ?")
	}

	exists, err := x.Get(&Track{UserID: userID, Title: title})
	if err != nil {
		return true, err
	}

	if exists {
		return true, nil
	}

	return false, nil
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

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Insert(t); err != nil {
		return err
	}

	return sess.Commit()
}

func updateTrack(e Engine, t *Track) error {
	_, err := e.Id(t.ID).AllCols().Update(t)
	return err
}

// UpdateTrack Update a Track
func UpdateTrack(t *Track) error {
	return updateTrack(x, t)
}

// UpdateTrackState Update track states
func UpdateTrackState(t *Track, what int) error {
	switch what {
	case TrackTranscoding:
		_, err := x.Id(t.ID).Cols("transcode_state").Update(t)
		if err != nil {
			return err
		}
	case TrackMetadatas:
		_, err := x.Id(t.ID).Cols("metadatas_state").Update(t)
		if err != nil {
			return err
		}
	}
	return nil
}

func getTrackByID(e Engine, id int64) (*Track, error) {
	t := new(Track)
	has, err := e.Id(id).Get(t)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.TrackNotExist{id, ""}
	}
	return t, nil
}

// GetTrackByID or error
func GetTrackByID(id int64) (*Track, error) {
	return getTrackByID(x, id)
}

// SetTrackReadyness or not
func SetTrackReadyness(id int64, state bool) error {
	_, err := x.Id(id).Cols("ready").Update(&Track{Ready: state})
	if err != nil {
		return err
	}
	return nil
}

// GetTrackWithInfoBySlugAndUserID or error
func GetTrackWithInfoBySlugAndUserID(id int64, slug string) ([]TrackWithInfo, error) {
	track := make([]TrackWithInfo, 0)
	err := x.Table("track").Join("INNER", "track_info", "track_info.track_id = track.id").Where("track.user_id = ? AND track.slug = ?", id, slug).Find(&track)
	if err != nil {
		return nil, err
	}
	return track, nil
}

// GetTrackBySlugAndUserID or error
func GetTrackBySlugAndUserID(id int64, slug string) (*Track, error) {
	track := &Track{Slug: slug, UserID: id}
	has, err := x.Get(track)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.TrackNotExist{id, ""}
	}
	return track, nil
}

// GetTrackByAlbumIDAndOrder like it's said
func GetTrackByAlbumIDAndOrder(albumID int64, albumOrder int64) (*Track, error) {
	track := &Track{AlbumID: albumID, AlbumOrder: albumOrder}
	has, err := x.Get(track)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.TrackNotExist{albumID, ""}
	}
	return track, nil
}

// GetFirstTrackOfAlbum and not the last
func GetFirstTrackOfAlbum(albumID int64, onlyPublic bool) (*TrackWithInfo, error) {
	tracks := make([]*TrackWithInfo, 0)

	sess := x.Where("album_id=?", albumID)

	if onlyPublic {
		sess.And("ready=?", true).And("is_private=?", false)
	}

	sess.Asc("track.album_order")

	var countSess xorm.Session
	countSess = *sess
	count, err := countSess.Count(new(Track))
	if err != nil {
		return nil, fmt.Errorf("Count: %v", err)
	}

	sess.Table(&Track{}).Join("LEFT", "track_info", "track_info.track_id = track.id").Join(
		"LEFT", "user", "user.id = track.user_id")

	err = sess.Limit(1).Find(&tracks)

	if err != nil {
		return nil, fmt.Errorf("LimitFind: %v", err)
	}
	if count >= 1 {
		return tracks[0], nil
	}

	return nil, fmt.Errorf("Album is empty")
}

// TrackOptions structure
type TrackOptions struct {
	UserID      int64
	WithPrivate bool
	GetAll      bool
	Page        int
	PageSize    int
	OnlyReady   bool
}

// GetTracks or nothing
func GetTracks(opts *TrackOptions) (tracks []*TrackWithInfo, _ int64, _ error) {
	if opts.Page <= 0 {
		opts.Page = 1
	}
	tracks = make([]*TrackWithInfo, 0, opts.PageSize)

	sess := x.Where("is_private=?", false)

	if opts.WithPrivate && !opts.GetAll {
		sess.Or("is_private=?", true)
	}

	if !opts.GetAll {
		sess.And("user_id=?", opts.UserID)
	}
	if opts.OnlyReady {
		sess.And("ready=?", true)
	}

	sess.Desc("track.created_unix")

	var countSess xorm.Session
	countSess = *sess
	count, err := countSess.Count(new(Track))
	if err != nil {
		return nil, 0, fmt.Errorf("Count: %v", err)
	}

	sess.Table(&Track{}).Join("LEFT", "track_info", "track_info.track_id = track.id").Join(
		"LEFT", "user", "user.id = track.user_id")

	return tracks, count, sess.Limit(opts.PageSize, (opts.Page-1)*opts.PageSize).Find(&tracks)
}

// GetNotReadyTracks and only that
func GetNotReadyTracks() (tracks []*Track, err error) {
	err = x.Table(&Track{}).Cols("ID").Where("ready=?", false).Find(&tracks)
	if err != nil {
		log.Error(2, "Cannot get un-ready tracks: %s", err)
	}
	return tracks, err
}

// GetAlbumTracks will get album tracks
func GetAlbumTracks(albumID int64, onlyPublic bool) (tracks []*TrackWithInfo, err error) {
	tracks = make([]*TrackWithInfo, 0)

	sess := x.Where("album_id=?", albumID)

	if onlyPublic {
		sess.And("ready=?", true).And("is_private=?", false)
	}

	sess.Asc("track.album_order")

	sess.Table(&Track{}).Join("LEFT", "track_info", "track_info.track_id = track.id").Join(
		"LEFT", "user", "user.id = track.user_id")

	return tracks, sess.Find(&tracks)
}

func removeTrackFiles(transcode bool, trackFilename string, userSlug string) error {
	storDir := filepath.Join(setting.Storage.Path, "tracks", userSlug)
	fName := filepath.Join(storDir, trackFilename)
	fJSON := filepath.Join(storDir, trackFilename+".json")
	fPNG := filepath.Join(storDir, trackFilename+".png")

	err := os.RemoveAll(fName)
	if err != nil {
		log.Error(2, "Cannot remove orig file '%s': %s", fName, err)
	} else {
		log.Info("File removed: %s", fName)
	}

	err = os.RemoveAll(fJSON)
	if err != nil {
		log.Error(2, "Cannot remove json file '%s': %s", fJSON, err)
	} else {
		log.Info("File removed: %s", fJSON)
	}

	err = os.RemoveAll(fPNG)
	if err != nil {
		log.Error(2, "Cannot remove png file '%s': %s", fPNG, err)
	} else {
		log.Info("File removed: %s", fPNG)
	}

	if transcode {
		fTranscode := fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))

		err = os.RemoveAll(fTranscode)
		if err != nil {
			log.Error(2, "Cannot remove transcode file '%s': %s", fTranscode, err)
		} else {
			log.Info("File removed: %s", fTranscode)
		}
	}

	return nil
}

// DeleteTrack will delete a track
func DeleteTrack(trackID int64, userID int64) error {

	// With session

	// Delete TrackInfo

	// Future: Delete stats record

	// Delete Track

	// Commit

	// Get track
	track := &Track{ID: trackID, UserID: userID}
	hasTrack, err := x.Get(track)
	if err != nil {
		return err
	} else if !hasTrack {
		return errors.TrackNotExist{trackID, ""}
	}
	trackFilename := track.Filename
	trackTranscoded := track.TranscodeState != ProcessingNotNeeded

	// Get track info
	trackInfo := &TrackInfo{TrackID: track.ID}
	hasTrackInfo, err := x.Get(trackInfo)
	if err != nil {
		return err
	}
	// We don't care if the trackInfo does not exists

	trackUser, err := GetUserByID(userID)
	if err != nil {
		return fmt.Errorf("GetUserByID: %v", err)
	}

	sess := x.NewSession()
	defer sess.Close()
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Delete(&Track{ID: trackID}); err != nil {
		return fmt.Errorf("sess.Delete Track: %v", err)
	}

	if hasTrackInfo {
		if _, err = sess.Delete(&TrackInfo{ID: trackInfo.ID}); err != nil {
			return fmt.Errorf("sess.Delete TrackInfo: %v", err)
		}
	}

	if err = sess.Commit(); err != nil {
		return fmt.Errorf("Commit: %v", err)
	}

	log.Info("Deleted track record for %d/%s", track.ID, track.Title)

	removeTrackFiles(trackTranscoded, trackFilename, trackUser.Slug)

	return nil
}
