package workers

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/krig/go-sox"
	log "github.com/sirupsen/logrus"
	"github.com/wtolson/go-taglib"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const (
	// maxSamples is the (maximum) number of samples that we shall read/write at a time;
	// chosen as a rough match to typical operating system I/O buffer size:
	maxSamples = 2048
)

func check(cond bool, test string) {
	if !cond {
		log.Errorf("check(): " + test + " failed")

	}
}

func fetchMetadatasAndCommit(idx uint) (uint, error) {
	timeStart := time.Now().Unix()

	track, err := models.GetTrackByID(idx)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": idx,
			"err":     err,
		}).Error("Cannot get Track from idx.")
		return 0, err
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": idx,
			"userID":  track.UserID,
			"err":     err,
		}).Error("Cannot get User from track.UserID.")
		return 0, err
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)

	// Metadatas
	md, err := taglib.Read(fName)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": idx,
			"fName":   fName,
			"err":     err,
		}).Error("Cannot open file for taglib reading.")
		return 0, err
	}

	ti := models.TrackInfo{
		Hash: track.Hash,

		Duration: md.Length().Seconds(),
		Rate:     md.Samplerate(),
		Channels: md.Channels(),
		Bitrate:  md.Bitrate(),

		ProcessedBasic:      models.ProcessingFinished,
		ProcessingStartUnix: timeStart,
	}

	switch track.Mimetype {
	case "audio/mpeg":
		ti.Type = "MP3"
		ti.TypeHuman = "Mpeg 3"
	case "audio/x-wav":
		ti.Type = "WAV"
		ti.TypeHuman = "WAV"
	case "audio/ogg":
		ti.Type = "OGG"
		ti.TypeHuman = "Ogg Vorbis"
	case "audio/x-flac":
	case "audio/flac":
		ti.Type = "FLAC"
		ti.TypeHuman = "FLAC"
	}

	/*
		FIXME or TODO if used ?
		Codec isn't managed, useful only for MP3 with encoder infos
		Bitrate from taglib seems to be an average of the file, not the real one
		BitrateMode isn't managed from taglib, could not determine CBR/VBR
		Format from WAV not managed by taglib too
	*/

	err = models.CreateTrackInfo(&ti)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": idx,
			"err":     err,
		}).Error("Cannot create TrackInfo.")
		return 0, err
	}

	// Update the Track to set the TrackInfoID
	track.TrackInfoID = ti.ID
	err = models.UpdateTrack(&track)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID":     track.ID,
			"err":         err,
			"trackInfoID": ti.ID,
		}).Error("Cannot update Track with TrackInfoID.")
		return 0, err
	}

	return ti.ID, nil
}

func generateWaveforms(trackID uint) (waveform string, err error) {
	if _, err := os.Stat(setting.AudiowaveformBin); os.IsNotExist(err) {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"bin":     setting.AudiowaveformBin,
			"err":     err,
		}).Error("Audiowaveform binary doesn't exists.")
		return "", fmt.Errorf("Error: %s doesn't exists", setting.AudiowaveformBin)
	}

	track, err := models.GetTrackByID(trackID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot get Track from index trackID.")
		return "", err
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"UserID":  track.UserID,
			"err":     err,
		}).Error("Cannot get User from track.UserID.")
		return "", err
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)
	// Different path if not mp3 : use the transcoded file
	if track.Mimetype != "audio/mpeg" {
		fName = fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
	}

	fJSON := filepath.Join(storDir, track.Filename+".json")
	fPNG := filepath.Join(storDir, track.Filename+".png")

	// Json
	out, err := exec.Command(setting.AudiowaveformBin, "-i", fName, "--pixels-per-second", "10", "-b", "8", "-o", fJSON).Output()
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("JSON: Can't execute Audiowaveform.")
		return "", err
	}

	if strings.Contains(string(out), "Can't generate") {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err_out": out,
		}).Error("JSON: Audiowaveform returned Can't generate.")
		return "", fmt.Errorf("JSON: Audiowaveform returned Can't generate. Output: %s", out)
	}

	// Get back the json
	wf, err := ioutil.ReadFile(fJSON)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"fJSON":   fJSON,
			"err":     err,
		}).Error("JSON: Cannot open file.")
		return "", err
	}
	waveform = string(wf)

	// Png
	out, err = exec.Command(setting.AudiowaveformBin, "-i", fName, "--width", "384", "--height", "64", "--no-axis-labels", "-o", fPNG).Output()
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("PNG: Can't execute Audiowaveform.")
		return waveform, err
	}

	if strings.Contains(string(out), "Can't generate") {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err_out": out,
		}).Error("PNG: Audiowaveform returned Can't generate.")
		return waveform, fmt.Errorf("PNG: Audiowaveform returned Can't generate. Output: %s", out)
	}

	return waveform, nil
}

func generateTranscode(trackID uint) (err error) {
	startTime := time.Now().Unix()

	track, err := models.GetTrackByID(trackID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot get Track from index trackID.")
		return err
	}

	// No transcode needed ? right!
	if !track.IsTranscodeNeeded() {
		return nil
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"userID":  track.UserID,
			"err":     err,
		}).Error("Cannot get User from Track.UserID")
		return err
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)

	// sox -i
	// AUDIO FILE FORMATS: 8svx aif aifc aiff aiffc al amb amr-nb amr-wb anb au avr awb caf cdda cdr cvs cvsd cvu dat
	// dvms f32 f4 f64 f8 fap flac fssd gsm gsrt hcom htk ima ircam la lpc lpc10 lu mat mat4 mat5 maud mp2 mp3 nist ogg
	// paf prc pvf raw s1 s16 s2 s24 s3 s32 s4 s8 sb sd2 sds sf sl sln smp snd sndfile sndr sndt sou sox sph sw txw u1
	// u16 u2 u24 u3 u32 u4 u8 ub ul uw vms voc vorbis vox w64 wav wavpcm wv wve xa xi
	// Check for mp3, flac, vorbis, wav
	// TODO

	// Do some transcoding here from <fName> to <fName>-ext.mp3
	if !sox.Init() {
		log.WithFields(log.Fields{
			"trackID": trackID,
		}).Error("Cannot init SOX library.")
		return fmt.Errorf("Cannot init SOX library")
	}
	// Make sure to call Quit before terminating
	defer sox.Quit()

	var input *sox.Format
	var output *sox.Format
	samples := make([]sox.Sample, maxSamples)

	input = sox.OpenRead(fName)
	if input == nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"file":    fName,
		}).Error("Cannot open file for read.")
		return fmt.Errorf("Cannot open file %s for read", fName)
	}

	// TODO 256CBR fixed for output mp3

	// Not sure the multiplier should always be nil...
	twoChSiginfo := sox.NewSignalInfo(input.Signal().Rate(), 2, input.Signal().Precision(), input.Signal().Length(), nil)

	dfName := fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
	output = sox.OpenWrite(dfName, twoChSiginfo, input.Encoding(), nil)
	if output == nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"file":    dfName,
		}).Error("Cannot open file for write.")
		return fmt.Errorf("Cannot open file %s for write", dfName)
	}
	defer output.Release()

	// now cycle
	for numberRead := input.Read(samples, maxSamples); numberRead > 0; numberRead = input.Read(samples, maxSamples) {
		check(output.Write(samples, uint(numberRead)) == numberRead, "write")
	}
	input.Release()

	// EOF
	track.TranscodeStartUnix = startTime
	track.TranscodeStopUnix = time.Now().Unix()
	track.TranscodeNeeded = models.BoolToFake(false) // it's now done
	track.TranscodeState = models.ProcessingFinished
	err = models.UpdateTrack(&track)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot update Track.")
		return err
	}

	return nil
}

// Used to change track to private, and set error if processing failed
func processingFailed(trackID uint, msg string) error {
	track, err := models.GetTrackByID(trackID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot get Track from index trackID.")
		return err
	}

	track.TranscodeState = models.ProcessingFailed
	track.TranscodeNeeded = models.BoolToFake(false)
	track.ProcessingError = msg
	track.Private = models.BoolToFake(true)

	err = models.UpdateTrack(&track)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot update Track.")
		return err
	}
	return nil
}

// TranscodeAndFetchInfos will do all the processing in one func
func TranscodeAndFetchInfos(trackID uint) error {
	log.WithFields(log.Fields{
		"trackID": trackID,
	}).Debug("Starting processing track.")

	trackInfosDb, err := models.GetTrackByID(trackID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
		}).Debug("Track deleted before we run the job, exiting this job.")
		return nil
	}

	// Fetch metadatas
	trackInfoID, err := fetchMetadatasAndCommit(trackID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID": trackID,
			"err":     err,
		}).Error("Cannot create TrackInfo")
		// We cannot update the state here 'cause if we get nil the record could probably not be inserted
		return err
	}

	// Fetch the created TrackInfo
	ti, err := models.GetTrackInfoByID(trackInfoID)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID":     trackID,
			"trackInfoID": trackInfoID,
			"err":         err,
		}).Error("Cannot get TrackInfo")
		// TODO state
		return err
	}

	// More than two channels are not handled
	if ti.Channels <= 2 {
		// Generate transcode file
		err = generateTranscode(trackID)
		if err != nil {
			log.WithFields(log.Fields{
				"trackID": trackID,
				"err":     err,
			}).Error("Cannot transcode")
			_ = processingFailed(trackID, "unable to create transcoded file")
			return err
		}

		// After transcoding, else we won't be able to transcode !mp3
		// Generate Waveforms
		wf, err := generateWaveforms(trackID)
		if err != nil {
			log.WithFields(log.Fields{
				"trackID": trackID,
				"err":     err,
			}).Error("Cannot create Waveforms")
			ti.ProcessedWaveform = models.ProcessingFailed
			ti.WaveformErr = fmt.Sprintf("%s", err)
		} else {
			ti.ProcessedWaveform = models.ProcessingFinished
			ti.Waveform = wf
		}
	}

	// Update TrackInfo
	ti.ProcessingStopUnix = time.Now().Unix()
	err = models.UpdateTrackInfo(&ti)
	if err != nil {
		log.WithFields(log.Fields{
			"trackID":     trackID,
			"trackInfoID": trackInfoID,
			"err":         err,
		}).Error("Cannot update TrackInfo")
		return err
	}

	if ti.Channels > 2 {
		log.WithFields(log.Fields{
			"channels": ti.Channels,
			"trackID":  trackID,
		}).Warnf("Cannot process files with more than two channels")
		models.SetTrackReadyness(trackID, false)

		err = processingFailed(trackID, "cannot process files with more than two channels")
		if err != nil {
			return err
		}

		return fmt.Errorf("cannot process files with more than two channels")
	}

	// Track is now ready
	models.SetTrackReadyness(trackID, true)

	// Push Track to Timeline if not private
	if !trackInfosDb.IsPrivate() {
		tli := &models.TimelineItem{
			TrackID: trackInfosDb.ID,
			UserID:  trackInfosDb.UserID,
		}
		err := models.CreateTimelineItem(tli)
		if err != nil {
			log.WithFields(log.Fields{
				"track": trackID,
			}).Errorf("Cannot add track to timeline: %v", err)
		}

		// Push the Album too if needed
		album, err := models.GetAlbumByID(trackInfosDb.AlbumID)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": trackInfosDb.AlbumID,
			}).Errorf("Cannot get album: %v", err)
		}

		if album.ID > 0 && !album.IsPrivate() {
			albumTracksCount, err := models.GetCountOfAlbumTracks(trackInfosDb.AlbumID)
			if err != nil {
				log.WithFields(log.Fields{
					"albumID": trackInfosDb.AlbumID,
				}).Errorf("Cannot get count for album: %v", err)
				albumTracksCount = 0 // well, yes
			}

			if albumTracksCount >= 1 {
				tli := &models.TimelineItem{
					UserID:  trackInfosDb.UserID,
					AlbumID: trackInfosDb.AlbumID,
				}
				err := models.CreateTimelineItem(tli)
				if err != nil {
					log.WithFields(log.Fields{
						"album": trackInfosDb.AlbumID,
					}).Errorf("Cannot add album to timeline: %v", err)
				}
			}
		}
	}

	return nil
}
