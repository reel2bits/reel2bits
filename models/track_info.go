package models

import (
	"dev.sigpipe.me/dashie/reel2bits/models/errors"
	"github.com/jinzhu/gorm"
	"time"
)

// TrackInfo database structure
type TrackInfo struct {
	gorm.Model

	Hash string `gorm:"UNIQUE NOT NULL"`

	Duration    float64
	Format      string // used only for wave, samplewidth * 8
	Rate        int    // samplerate, all
	Channels    int    // all
	Codec       string // WAV: PCM, Mp3: encoder infos
	Waveform    string `gorm:"TEXT"`
	WaveformErr string
	Bitrate     int    // 320, 128, etc.
	BitrateMode string // VBR, CBR, ... ?
	Type        string // MP3, OGG, FLAC, ...
	TypeHuman   string // Mpeg 3, Ogg Vorbis, ...

	// Theses two uses the ProcessingX const states
	ProcessedBasic    int `gorm:"DEFAULT 0"`
	ProcessedWaveform int `gorm:"DEFAULT 0"`

	ProcessingStart     time.Time `gorm:"-"`
	ProcessingStartUnix int64
	ProcessingStop      time.Time `gorm:"-"`
	ProcessingStopUnix  int64
}

// Waveform is the JSON reflected structure
type Waveform struct {
	SampleRate      int64
	SamplePerPixels int64
	Bits            int64
	Length          int64
	Data            []int64
}

// AfterFind set times
func (track *TrackInfo) AfterFind() {
	track.ProcessingStart = time.Unix(track.ProcessingStartUnix, 0).Local()
	track.ProcessingStop = time.Unix(track.ProcessingStopUnix, 0).Local()
	return
}

// CreateTrackInfo or error
func CreateTrackInfo(t *TrackInfo) (err error) {
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

func updateTrackInfo(t *TrackInfo) (err error) {
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

// UpdateTrackInfo a TrackInfo
func UpdateTrackInfo(t *TrackInfo) error {
	return updateTrackInfo(t)
}

func getTrackInfoByID(id uint) (trackInfo TrackInfo, err error) {
	err = db.Where("id = ?", id).First(&trackInfo).Error
	if gorm.IsRecordNotFoundError(err) || trackInfo.ID == 0 {
		return trackInfo, errors.TrackInfoNotExist{TrackInfoID: id}
	} else if err != nil {
		return trackInfo, err
	}
	return
}

// GetTrackInfoByID or error
func GetTrackInfoByID(id uint) (TrackInfo, error) {
	return getTrackInfoByID(id)
}
