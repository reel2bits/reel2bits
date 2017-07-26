package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"github.com/go-xorm/xorm"
	"time"
)

// TrackInfo database structure
type TrackInfo struct {
	ID      int64  `xorm:"pk autoincr"`
	Hash    string `xorm:"UNIQUE NOT NULL"`
	TrackID int64  `xorm:"INDEX"`

	Duration    float64
	Format      string // used only for wave, samplewidth * 8
	Rate        int    // samplerate, all
	Channels    int    // all
	Codec       string // WAV: PCM, Mp3: encoder infos
	Waveform    string `xorm:"TEXT"`
	WaveformErr string
	Bitrate     int    // 320, 128, etc.
	BitrateMode string // VBR, CBR, ... ?
	Type        string // MP3, OGG, FLAC, ...
	TypeHuman   string // Mpeg 3, Ogg Vorbis, ...

	// Theses two uses the ProcessingX const states
	ProcessedBasic    int `xorm:"DEFAULT 0"`
	ProcessedWaveform int `xorm:"DEFAULT 0"`

	ProcessingStart     time.Time `xorm:"-"`
	ProcessingStartUnix int64
	ProcessingStop      time.Time `xorm:"-"`
	ProcessingStopUnix  int64

	Created     time.Time `xorm:"-"`
	CreatedUnix int64
	Updated     time.Time `xorm:"-"`
	UpdatedUnix int64

	// Relations
	// 	TrackID
}

// Waveform is the JSON reflected structure
type Waveform struct {
	SampleRate      int64
	SamplePerPixels int64
	Bits            int64
	Length          int64
	Data            []int64
}

// BeforeInsert set times
func (track *TrackInfo) BeforeInsert() {
	track.CreatedUnix = time.Now().Unix()
	track.UpdatedUnix = track.CreatedUnix
}

// BeforeUpdate set times
func (track *TrackInfo) BeforeUpdate() {
	track.UpdatedUnix = time.Now().Unix()
}

// AfterSet set times
func (track *TrackInfo) AfterSet(colName string, _ xorm.Cell) {
	switch colName {
	case "created_unix":
		track.Created = time.Unix(track.CreatedUnix, 0).Local()
	case "updated_unix":
		track.Updated = time.Unix(track.UpdatedUnix, 0).Local()
	case "processing_start_unix":
		track.ProcessingStart = time.Unix(track.ProcessingStartUnix, 0).Local()
	case "processing_stop_unix":
		track.ProcessingStop = time.Unix(track.ProcessingStopUnix, 0).Local()
	}
}

// CreateTrackInfo or error
func CreateTrackInfo(t *TrackInfo) (err error) {
	sess := x.NewSession()
	defer sessionRelease(sess)
	if err = sess.Begin(); err != nil {
		return err
	}

	if _, err = sess.Insert(t); err != nil {
		return err
	}

	return sess.Commit()
}

func updateTrackInfo(e Engine, t *TrackInfo) error {
	_, err := e.Id(t.ID).AllCols().Update(t)
	return err
}

// UpdateTrackInfo a TrackInfo
func UpdateTrackInfo(t *TrackInfo) error {
	return updateTrackInfo(x, t)
}

func getTrackInfoByID(e Engine, id int64) (*TrackInfo, error) {
	t := new(TrackInfo)
	has, err := e.Id(id).Get(t)
	if err != nil {
		return nil, err
	} else if !has {
		return nil, errors.TrackInfoNotExist{id}
	}
	return t, nil
}

// GetTrackInfoByID or error
func GetTrackInfoByID(id int64) (*TrackInfo, error) {
	return getTrackInfoByID(x, id)
}
