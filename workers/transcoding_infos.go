package workers

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/krig/go-sox"
	"github.com/wtolson/go-taglib"
	log "gopkg.in/clog.v1"
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
		log.Error(2, "check(): "+test+" failed")
	}
}

func fetchMetadatasAndCommit(idx int64) (int64, error) {
	timeStart := time.Now().Unix()

	track, err := models.GetTrackByID(idx)
	if err != nil {
		log.Error(2, "Cannot get Track from index %d: %s", idx, err)
		return 0, err
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.Error(2, "Cannot get User from ID %d: %s", track.UserID, err)
		return 0, err
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)

	// Metadatas
	md, err := taglib.Read(fName)
	if err != nil {
		log.Error(2, "Cannot open file %s for taglib reading: %s", fName, err)
		return 0, err
	}

	ti := models.TrackInfo{
		TrackID: track.ID,
		Hash:    track.Hash,

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
		log.Error(2, "Cannot create TrackInfo: %s", err)
		return 0, err
	}

	return ti.ID, nil
}

func generateWaveforms(trackID int64) (waveform string, err error) {
	if _, err := os.Stat(setting.AudiowaveformBin); os.IsNotExist(err) {
		log.Error(2, "Error: %s doesn't exists", setting.AudiowaveformBin)
		return "", fmt.Errorf("Error: %s doesn't exists", setting.AudiowaveformBin)
	}

	track, err := models.GetTrackByID(trackID)
	if err != nil {
		log.Error(2, "Cannot get Track from index %d: %s", trackID, err)
		return "", err
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.Error(2, "Cannot get User from ID %d: %s", track.UserID, err)
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
		log.Error(2, "JSON: Can't execute Audiowaveform: %s", err)
		return "", err
	}

	if strings.Contains(string(out), "Can't generate") {
		log.Error(2, "JSON: Audiowaveform returned Can't generate. Output: %s", out)
		return "", fmt.Errorf("JSON: Audiowaveform returned Can't generate. Output: %s", out)
	}

	// Get back the json
	wf, err := ioutil.ReadFile(fJSON)
	if err != nil {
		log.Error(2, "JSON: Cannot open %s: %s", fJSON, err)
		return "", err
	}
	waveform = string(wf)

	// Png
	out, err = exec.Command(setting.AudiowaveformBin, "-i", fName, "--width", "384", "--height", "64", "--no-axis-labels", "-o", fPNG).Output()
	if err != nil {
		log.Error(2, "PNG: Can't execute Audiowaveform: %s", err)
		return waveform, err
	}

	if strings.Contains(string(out), "Can't generate") {
		log.Error(2, "PNG: Audiowaveform returned Can't generate. Output: %s", out)
		return waveform, fmt.Errorf("PNG: Audiowaveform returned Can't generate. Output: %s", out)
	}

	return waveform, nil
}

func generateTranscode(trackID int64) (err error) {
	startTime := time.Now().Unix()

	track, err := models.GetTrackByID(trackID)
	if err != nil {
		log.Error(2, "Cannot get Track from index %d: %s", trackID, err)
		return err
	}

	// No transcode needed ? right!
	if !track.TranscodeNeeded {
		return nil
	}

	user, err := models.GetUserByID(track.UserID)
	if err != nil {
		log.Error(2, "Cannot get User from ID %d: %s", track.UserID, err)
		return err
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)

	// sox -i
	// AUDIO FILE FORMATS: 8svx aif aifc aiff aiffc al amb amr-nb amr-wb anb au avr awb caf cdda cdr cvs cvsd cvu dat dvms f32 f4 f64 f8 fap flac fssd gsm gsrt hcom htk ima ircam la lpc lpc10 lu mat mat4 mat5 maud mp2 mp3 nist ogg paf prc pvf raw s1 s16 s2 s24 s3 s32 s4 s8 sb sd2 sds sf sl sln smp snd sndfile sndr sndt sou sox sph sw txw u1 u16 u2 u24 u3 u32 u4 u8 ub ul uw vms voc vorbis vox w64 wav wavpcm wv wve xa xi
	// Check for mp3, flac, vorbis, wav
	// TODO

	// Do some transcoding here from <fName> to <fName>-ext.mp3
	if !sox.Init() {
		log.Error(2, "Cannot init SOX library")
		return fmt.Errorf("Cannot init SOX library")
	}
	// Make sure to call Quit before terminating
	defer sox.Quit()

	var input *sox.Format
	var output *sox.Format
	samples := make([]sox.Sample, maxSamples)

	input = sox.OpenRead(fName)
	if input == nil {
		log.Error(2, "Cannot open file %s for read", fName)
		return fmt.Errorf("Cannot open file %s for read", fName)
	}

	// TODO 256CBR fixed for output mp3

	dfName := fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
	output = sox.OpenWrite(dfName, input.Signal(), input.Encoding(), nil)
	if output == nil {
		log.Error(2, "Cannot open file %s for write", dfName)
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
	track.TranscodeNeeded = false // it's now done
	track.TranscodeState = models.ProcessingFinished
	err = models.UpdateTrack(track)
	if err != nil {
		log.Error(2, "Cannot update Track %d: %s", trackID, err)
		return err
	}

	return nil
}

// TranscodeAndFetchInfos will do all the processing in one func
func TranscodeAndFetchInfos(trackID int64) error {
	log.Trace("Starting processing track %d", trackID)

	_, err := models.GetTrackByID(trackID)
	if err != nil {
		log.Trace("Track deleted before we run the job, exiting this job.")
		return nil
	}

	// Fetch metadatas
	trackInfoID, err := fetchMetadatasAndCommit(trackID)
	if err != nil {
		log.Error(2, "Cannot create TrackInfo: %s", err)
		// We cannot update the state here 'cause if we get nil the record could probably not be inserted
		return err
	}

	// Fetch the created TrackInfo
	ti, err := models.GetTrackInfoByID(trackInfoID)
	if err != nil {
		log.Error(2, "Cannot get TrackInfo id %d: %s", trackInfoID, err)
		// TODO state
		return err
	}

	// Generate transcode file
	err = generateTranscode(trackID)
	if err != nil {
		log.Error(2, "Cannot transcode %d: %s", trackID, err)
		return err
	}

	// After transcoding, else we won't be able to transcode !mp3
	// Generate Waveforms
	wf, err := generateWaveforms(trackID)
	if err != nil {
		log.Error(2, "Cannot create Waveforms: %s", err)
		ti.ProcessedWaveform = models.ProcessingFailed
		ti.WaveformErr = fmt.Sprintf("%s", err)
	} else {
		ti.ProcessedWaveform = models.ProcessingFinished
		ti.Waveform = wf
	}

	// Update TrackInfo
	ti.ProcessingStopUnix = time.Now().Unix()
	err = models.UpdateTrackInfo(ti)
	if err != nil {
		log.Error(2, "Cannot update TrackInfo %d: %s", trackInfoID, err)
		return err
	}

	// Track is now ready
	models.SetTrackReadyness(trackID, true)

	return nil
}
