package track

import (
	"bytes"
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"dev.sigpipe.me/dashie/reel2bits/workers"
	"encoding/json"
	"fmt"
	"github.com/RichardKnop/machinery/v1/tasks"
	"github.com/Unknwon/paginater"
	log "github.com/sirupsen/logrus"
	"io/ioutil"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

const (
	tmplUpload     = "track/upload"
	tmplShow       = "track/show"
	tmplShowWait   = "track/show_wait"
	tmplTracksList = "tracks_list"
	tmplEdit       = "track/edit"
)

// Upload [GET]
func Upload(ctx *context.Context) {
	ctx.Title("track.title_upload")
	ctx.PageIs("TrackUpload")

	albums, _ := models.GetMapNameIDOfAlbums(ctx.User.ID)

	ctx.Data["albums"] = albums
	ctx.Data["LicencesMapping"] = ctx.URLTrack.LicencesMapping()

	ctx.HTML(200, tmplUpload)
}

// UploadPost [POST]
func UploadPost(ctx *context.Context, f form.TrackUpload) {
	ctx.Title("track.title_upload")
	ctx.PageIs("TrackUpload")

	if ctx.HasError() {
		ctx.Data["LicencesMapping"] = ctx.URLTrack.LicencesMapping()
		ctx.Success(tmplUpload)
		return
	}

	fileHash := models.GenerateHash(f.Title, ctx.User.ID)

	t := &models.Track{
		UserID:       ctx.User.ID,
		Title:        f.Title,
		Description:  f.Description,
		Private:      models.BoolToFake(f.IsPrivate),
		ShowDlLink:   models.BoolToFake(f.ShowDlLink),
		Filename:     fmt.Sprintf("%s%s", fileHash, filepath.Ext(f.File.Filename)), // .Ext returns the dot
		FilenameOrig: strings.TrimSuffix(f.File.Filename, filepath.Ext(f.File.Filename)),
		Hash:         fileHash,
		Licence:      f.Licence,
	}

	if f.Album > 0 {
		album, err := models.GetAlbumByID(f.Album)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": f.Album,
			}).Errorf("Cannot get album by ID: %v", err)
		} else {
			t.AlbumID = f.Album
			albumTracksCount, err := models.GetCountOfAlbumTracks(album.ID)
			if err != nil {
				log.WithFields(log.Fields{
					"albumID": f.Album,
				}).Errorf("Cannot get count for album: %v", err)
				albumTracksCount = 0 // well, yes
			}
			t.AlbumOrder = albumTracksCount + 1 // if zero it will be Track 1, etc.
		}
	}

	mimetype, err := models.SaveTrackFile(f.File, t.Filename, ctx.User.Slug)
	if err != nil {
		log.Errorf("Cannot save track file: %v", err)
		ctx.Flash.Error("Cannot save track file, please retry")
		ctx.RenderWithErr(ctx.Gettext("file is invalid"), tmplUpload, &f)
		return
	}

	t.Mimetype = mimetype
	if mimetype != "audio/mpeg" {
		t.TranscodeNeeded = models.BoolToFake(true)
	}

	if err := models.CreateTrack(t); err != nil {
		switch {
		case models.IsErrTrackTitleAlreadyExist(err):
			ctx.Data["Err_Title"] = true
			ctx.RenderWithErr(ctx.Gettext("track title already exists"), tmplUpload, &f)
		default:
			ctx.Handle(500, "CreateTrack", err)
		}

		// Deleting the file
		storDir := filepath.Join(setting.Storage.Path, "tracks", ctx.User.Slug)
		fName := filepath.Join(storDir, t.Filename)
		err := os.RemoveAll(fName)
		if err != nil {
			log.WithFields(log.Fields{
				"file": fName,
			}).Errorf("Cannot remove temp file: %v", err)
		} else {
			log.WithFields(log.Fields{
				"file": fName,
			}).Infof("File removed")
		}
		return
	}
	log.WithFields(log.Fields{
		"trackID":     t.ID,
		"track title": t.Title,
	}).Debugf("Track created")

	sig := &tasks.Signature{
		Name: "TranscodeAndFetchInfofs",
		Args: []tasks.Arg{{Type: "int64", Value: t.ID}},
	}
	server, err := workers.CreateServer()
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Cannot initiate the worker connection, please retry again."))
		if t.IsTranscodeNeeded() {
			err = models.UpdateTrackState(t.ID, &models.Track{TranscodeState: models.ProcessingWaiting}, models.TrackTranscoding)
			if err != nil {
				log.WithFields(log.Fields{
					"trackID": t.ID,
				}).Errorf("CreateServer: Error setting TranscodeState to ProcessingRetry of track: %v", err)
			}
		}

		err = models.UpdateTrackState(t.ID, &models.Track{MetadatasState: models.ProcessingWaiting}, models.TrackMetadatas)
		if err != nil {
			log.WithFields(log.Fields{
				"trackID": t.ID,
			}).Errorf("CreateServer: Error setting MetadatasState to ProcessingRetry of track: %v", err)
		}
	}
	_, err = server.SendTask(sig)
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Cannot push the worker job, the watchdog should take care of it."))
		if t.IsTranscodeNeeded() {
			err = models.UpdateTrackState(t.ID, &models.Track{TranscodeState: models.ProcessingWaiting}, models.TrackTranscoding)
			if err != nil {
				log.WithFields(log.Fields{
					"trackID": t.ID,
				}).Errorf("SendTask: Error setting TranscodeState to ProcessingRetry of track: %v", err)
			}
		}
		err = models.UpdateTrackState(t.ID, &models.Track{MetadatasState: models.ProcessingWaiting}, models.TrackMetadatas)
		if err != nil {
			log.WithFields(log.Fields{
				"trackID": t.ID,
			}).Errorf("SendTask: Error setting MetadatasState to ProcessingRetry of track: %v", err)
		}
	}

	ctx.Flash.Success(ctx.Gettext("Track uploaded"))
	ctx.SubURLRedirect(ctx.URLFor("track_show", ":userSlug", ctx.User.Slug, ":trackSlug", t.Slug))
}

// Show [GET]
func Show(ctx *context.Context) {
	if (ctx.User.ID != ctx.URLUser.ID) && ctx.URLTrack.IsPrivate() {
		ctx.Flash.Error("Access forbidden.")
		ctx.SubURLRedirect(ctx.URLFor("home"), http.StatusForbidden)
		return
	}
	// TODO check for track.ready

	ctx.Data["track"] = ctx.URLTrack
	ctx.Data["user"] = ctx.URLUser
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", ctx.URLTrack.Title, ctx.URLUser.UserName, setting.AppName)
	ctx.PageIs("TrackShow")

	if ctx.URLTrack.AlbumID > 0 && ctx.URLTrack.AlbumOrder > 0 {
		album, err := models.GetAlbumByID(ctx.URLTrack.AlbumID)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": ctx.URLTrack.AlbumID,
				"trackID": ctx.URLTrack.ID,
			}).Errorf("Cannot get album for track: %v", err)

			ctx.Flash.Error(ctx.Gettext("Invalid album."))
			//ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			ctx.Data["album"] = nil
		} else {
			ctx.Data["album"] = album
		}
	}

	if !ctx.URLTrack.IsReady() {
		ctx.HTML(200, tmplShowWait)
		return
	}

	ctx.HTML(200, tmplShow)
}

// DevGetMediaTrack [GET] DEV ONLY !
func DevGetMediaTrack(ctx *context.Context) {
	storDir := filepath.Join(setting.Storage.Path, "tracks", ctx.URLUser.Slug)
	fName := filepath.Join(storDir, ctx.URLTrack.Filename)
	mimeType := ctx.URLTrack.Mimetype

	if ctx.Params(":type") == "mp3" {
		fName = fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
		mimeType = "audio/mpeg"
	}

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.WithFields(log.Fields{
			"file": fName,
		}).Errorf("Cannot read file: %v", err)

		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContentNoDownload(fmt.Sprintf("%s%s", strings.TrimSuffix(ctx.URLTrack.Filename, filepath.Ext(ctx.URLTrack.Filename)), filepath.Ext(fName)), mimeType, bytes.NewReader(content))

}

// DevGetMediaPngWf [GET] DEV ONLY !
func DevGetMediaPngWf(ctx *context.Context) {
	storDir := filepath.Join(setting.Storage.Path, "tracks", ctx.URLUser.Slug)
	fName := filepath.Join(storDir, fmt.Sprintf("%s.png", ctx.URLTrack.Filename))

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.WithFields(log.Fields{
			"file": fName,
		}).Errorf("Cannot read file: %v", err)

		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContentNoDownload(ctx.URLTrack.Filename, "image/png", bytes.NewReader(content))

}

// DevGetMediaDownload [GET] DEV ONLY !
func DevGetMediaDownload(ctx *context.Context) {
	storDir := filepath.Join(setting.Storage.Path, "tracks", ctx.URLUser.Slug)
	fName := filepath.Join(storDir, ctx.URLTrack.Filename)

	if ctx.Params(":type") == "mp3" {
		fName = fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
	}

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.WithFields(log.Fields{
			"file": fName,
		}).Errorf("Cannot read file: %v", err)

		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContent(fmt.Sprintf("%s__by__%s%s", ctx.URLTrack.Slug, ctx.URLUser.Slug, filepath.Ext(fName)), bytes.NewReader(content))
}

// ListUserTracks [GET]
func ListUserTracks(ctx *context.Context) {
	ctx.Data["Title"] = fmt.Sprintf("Tracks of %s - %s", ctx.URLUser.UserName, setting.AppName)
	ctx.PageIs("UserListTracks")

	page := ctx.QueryInt("page")
	if page <= 0 {
		page = 1
	}
	ctx.Data["PageNumber"] = page

	opts := &models.TrackOptions{
		PageSize:    10, // TODO: put this in config
		Page:        page,
		GetAll:      false,
		UserID:      ctx.URLUser.ID,
		WithPrivate: false,
		OnlyReady:   true,
	}

	if ctx.Data["LoggedUserID"] == ctx.URLUser.ID {
		opts.WithPrivate = true
		opts.OnlyReady = false
	}

	listOfTracks, tracksCount, err := models.GetTracks(opts)
	if err != nil {
		log.WithFields(log.Fields{
			"opts": opts,
		}).Errorf("Cannot get Track with options: %v", err)

		ctx.Flash.Error(ctx.Gettext("Error getting list of tracks"))
		ctx.Handle(500, "ListTracks", err)
		return
	}

	ctx.Data["user"] = ctx.URLUser
	ctx.Data["tracks"] = listOfTracks
	ctx.Data["tracks_count"] = tracksCount

	ctx.Data["Total"] = tracksCount
	ctx.Data["Page"] = paginater.New(int(tracksCount), opts.PageSize, page, 5)

	ctx.Success(tmplTracksList)
}

// DeleteTrack [POST]
// FIXME: why is the form not used ?
func DeleteTrack(ctx *context.Context, f form.TrackDelete) {
	if ctx.HasError() {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Data["ErrorMsg"],
			"redirect": false,
		})
		return
	}

	if ctx.Data["LoggedUserID"] != ctx.URLTrack.UserID {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Gettext("Unauthorized"),
			"redirect": false,
		})
		return
	}

	err := models.DeleteTrack(ctx.URLTrack.ID, ctx.URLTrack.UserID)
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Error deleting track"))
		log.Warnf("DeleteTrack.Delete: %v", err)
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Gettext("Error deleting track"),
			"redirect": false,
		})
		return
	}

	ctx.Flash.Success(ctx.Gettext("Track deleted"))
	ctx.JSONSuccess(map[string]interface{}{
		"error":    nil,
		"redirect": ctx.SubURLFor("track_list", ":userSlug", ctx.URLUser.Slug),
	})
	return
}

// GetJSONWaveform [GET]
func GetJSONWaveform(ctx *context.Context) {
	if ctx.URLTrack.TrackInfo.Waveform != "" && ctx.URLTrack.TrackInfo.WaveformErr == "" {
		// MERGE json from .TrackInfo.Waveform
		var w models.Waveform
		err := json.Unmarshal([]byte(ctx.URLTrack.TrackInfo.Waveform), &w)

		if err != nil {
			log.Errorf("Cannot unmarshal waveform: %v", err)
			ctx.JSONSuccess(map[string]interface{}{
				"error": "Cannot unmarshal Waveform",
			})
			return
		}

		soundType := "orig"
		if ctx.URLTrack.Mimetype != "audio/mpeg" {
			soundType = "mp3"
		}
		ctx.JSONSuccess(map[string]interface{}{
			"waveform":    w,
			"track_url":   ctx.URLFor("media_track_stream", ":userSlug", ctx.URLUser.Slug, ":trackSlug", ctx.URLTrack.Slug, ":type", soundType),
			"wf_png":      ctx.URLFor("media_track_waveform", ":userSlug", ctx.URLUser.Slug, ":trackSlug", ctx.URLTrack.Slug),
			"title":       ctx.URLTrack.Title,
			"description": ctx.URLTrack.Description,
		})
		return
	}

	ctx.JSONSuccess(map[string]interface{}{
		"error": "Cannot get Waveform",
	})
	return

}

// Edit [GET]
func Edit(ctx *context.Context) {
	if !ctx.IsLogged {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	if ctx.Data["LoggedUserID"] != ctx.URLUser.ID {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	albums, err := models.GetMapNameIDOfAlbums(ctx.User.ID)
	if err != nil {
		log.WithFields(log.Fields{
			"userID": ctx.User.ID,
		}).Errorf("Cannot get album list for user: %v", err)

	}

	ctx.Data["albums"] = albums
	ctx.Data["description"] = ctx.URLTrack.Description
	ctx.Data["is_private"] = ctx.URLTrack.IsPrivate()
	ctx.Data["show_dl_link"] = ctx.URLTrack.CanShowDlLink()
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", ctx.URLTrack.Title, ctx.URLUser.UserName, setting.AppName)
	ctx.Data["title"] = ctx.URLTrack.Title
	ctx.Data["cur_album"] = ctx.URLTrack.AlbumID
	ctx.Data["licence"] = ctx.URLTrack.Licence
	ctx.Data["LicencesMapping"] = ctx.URLTrack.LicencesMapping()
	ctx.PageIs("TrackEdit")

	if !ctx.URLTrack.IsReady() {
		ctx.Data["user"] = ctx.URLUser
		ctx.Data["track"] = ctx.URLTrack
		ctx.HTML(200, tmplShowWait)
		return
	}

	ctx.HTML(200, tmplEdit)
}

// EditPost [POST]
func EditPost(ctx *context.Context, f form.TrackEdit) {
	if !ctx.IsLogged {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	if ctx.Data["LoggedUserID"] != ctx.URLUser.ID {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	if ctx.HasError() {
		ctx.Success(tmplUpload)
		return
	}

	// Previous private state
	var previouslyPrivate = false

	if ctx.URLTrack.IsPrivate() {
		previouslyPrivate = true
	}
	// Previous album ID
	var previouslyAlbum = ctx.URLTrack.AlbumID

	ctx.URLTrack.Title = f.Title
	ctx.URLTrack.Description = f.Description
	ctx.URLTrack.Private = models.BoolToFake(f.IsPrivate)
	ctx.URLTrack.ShowDlLink = models.BoolToFake(f.ShowDlLink)
	ctx.URLTrack.Licence = f.Licence

	album, err := models.GetAlbumByID(f.Album)
	if err != nil {
		log.WithFields(log.Fields{
			"albumID": f.Album,
		}).Errorf("Cannot get album by ID: %v", err)
		// zero is considered as "unassociated"
		ctx.URLTrack.AlbumID = 0
		ctx.URLTrack.AlbumOrder = 0

	} else {
		ctx.URLTrack.AlbumID = album.ID
		albumTracksCount, err := album.GetTracksCount(false)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": f.Album,
			}).Errorf("Cannot get count of album: %v", err)

			albumTracksCount = 0 // well, yes
		}
		ctx.URLTrack.AlbumOrder = albumTracksCount + 1 // if zero it will be Track 1, etc.
	}

	// Update the track in DB
	err = models.UpdateTrack(&ctx.URLTrack)
	if err != nil {
		switch {
		default:
			ctx.Handle(500, "EditTrack", err)
		}
		return
	}

	// Timeline Item handling

	// Urgh
	const (
		TliDoNothing = 1
		TliAdd       = 2
		TliRm        = 3
	)

	// Track have been publicized, add timelineItem
	if previouslyPrivate && !f.IsPrivate {
		if !ctx.URLTrack.IsPrivate() {
			tli := &models.TimelineItem{
				TrackID: ctx.URLTrack.ID,
				UserID:  ctx.URLTrack.UserID,
			}
			err := models.CreateTimelineItem(tli)
			if err != nil {
				log.WithFields(log.Fields{
					"track": ctx.URLTrack.ID,
				}).Errorf("Cannot add track to timeline: %v", err)
			}
		}
	}

	// Track have been privatized, remove timeline item
	if !previouslyPrivate && f.IsPrivate {
		err = models.DeleteTimelineItem(ctx.URLUser.ID, ctx.URLTrack.ID, 0)
		if err != nil {
			log.WithFields(log.Fields{
				"trackID": ctx.URLTrack.ID,
				"userID":  ctx.URLUser.ID,
			}).Errorf("Cannot delete timelineItem: %v", err)
		}
	}

	var TliAlbum = TliDoNothing

	// Did we changed the album from X to Y ?
	// Meaning we have to do something
	if previouslyAlbum != f.Album {
		logFields := make(log.Fields)

		// Check if Album.ID > 0 -> we are going to use a real album
		log.WithFields(log.Fields{"previous ID": previouslyAlbum, "new ID": album.ID}).Info("Track album ID changed")
		if album.ID > 0 {
			TliAlbum = TliAdd

			// Handle the album privacy
			if album.IsPrivate() {
				TliAlbum = TliRm
				logFields["albumPrivate"] = true
			} else {
				TliAlbum = TliAdd
				logFields["albumPrivate"] = false
			}

			// Handle the track count
			publicTracksCount, err := album.GetTracksCount(true)
			if err != nil {
				log.WithFields(log.Fields{
					"albumID": f.Album,
				}).Errorf("Cannot get count of album: %v", err)
			}
			if publicTracksCount >= 1 {
				TliAlbum = TliAdd
				logFields["publicTracksCount"] = publicTracksCount
			} else {
				TliAlbum = TliRm
				logFields["publicTracksCount"] = publicTracksCount
			}
		}

		// Now do the real work
		if TliAlbum == TliAdd { // Add album to Timeline
			log.WithFields(logFields).Info("Going to add a timeline album")
			tli := &models.TimelineItem{
				UserID:  ctx.URLTrack.UserID,
				AlbumID: album.ID,
			}
			err := models.CreateTimelineItem(tli)
			if err != nil {
				log.WithFields(log.Fields{
					"album": album.ID,
				}).Errorf("Cannot add album to timeline: %v", err)
			}
		} else if TliAlbum == TliRm { // Remove album from Timeline
			log.WithFields(logFields).Info("Going to remove a timeline album")
			err = models.DeleteTimelineItem(ctx.URLUser.ID, 0, album.ID)
			if err != nil {
				log.WithFields(log.Fields{
					"albumID": album.ID,
					"userID":  ctx.URLUser.ID,
				}).Errorf("Cannot delete timelineItem: %v", err)
			}
		}

		// Reset the flag
		TliAlbum = TliDoNothing

		// We have to handle the previous album too
		// But only if the previous album is not 0
		if previouslyAlbum > 0 {
			log.WithFields(log.Fields{"trackID": ctx.URLTrack.ID}).Info("The track doesn't have an album associated anymore")
			previousAlbum, err := models.GetAlbumByID(previouslyAlbum)
			if err != nil {
				log.WithFields(log.Fields{
					"albumID": previouslyAlbum,
				}).Errorf("Cannot get album by ID: %v", err)
			} else {
				// Check if the previous album have enough tracks
				previousPublicTracksCount, err := previousAlbum.GetTracksCount(true)
				if err != nil {
					log.WithFields(log.Fields{
						"albumID": previousAlbum.ID,
					}).Errorf("Cannot get count of album: %v", err)
				}

				if previousPublicTracksCount < 1 {
					TliAlbum = TliRm
				}

				// Now do the real work for the old album
				if TliAlbum == TliRm { // Remove album from Timeline
					err = models.DeleteTimelineItem(ctx.URLUser.ID, 0, previousAlbum.ID)
					if err != nil {
						log.WithFields(log.Fields{
							"albumID": previousAlbum.ID,
							"userID":  ctx.URLUser.ID,
						}).Errorf("Cannot delete timelineItem: %v", err)
					}
				}
			}
		}
	}

	ctx.Flash.Success(ctx.Gettext("Track edited"))
	ctx.SubURLRedirect(ctx.URLFor("track_show", ":userSlug", ctx.URLUser.Slug, ":trackSlug", ctx.URLTrack.Slug))
}
