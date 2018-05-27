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

	ctx.HTML(200, tmplUpload)
}

// UploadPost [POST]
func UploadPost(ctx *context.Context, f form.TrackUpload) {
	ctx.Title("track.title_upload")
	ctx.PageIs("TrackUpload")

	if ctx.HasError() {
		ctx.Success(tmplUpload)
		return
	}

	fileHash := models.GenerateHash(f.Title, ctx.User.ID)

	t := &models.Track{
		UserID:       ctx.User.ID,
		Title:        f.Title,
		Description:  f.Description,
		IsPrivate:    f.IsPrivate,
		ShowDlLink:   f.ShowDlLink,
		Filename:     fmt.Sprintf("%s%s", fileHash, filepath.Ext(f.File.Filename)), // .Ext returns the dot
		FilenameOrig: strings.TrimSuffix(f.File.Filename, filepath.Ext(f.File.Filename)),
		Hash:         fileHash,
	}

	if f.Album > 0 {
		t.AlbumID = f.Album
		count, err := models.GetCountOfAlbumTracks(f.Album)
		if err != nil {
			log.Errorf("Cannot get count for album %d: %s", f.Album, err)
			count = 0 // well, yes
		}
		t.AlbumOrder = count + 1 // if zero it will be Track 1, etc.
	}

	mimetype, err := models.SaveTrackFile(f.File, t.Filename, ctx.User.Slug)
	if err != nil {
		log.Errorf("Cannot save track file: %s", err)
		ctx.Flash.Error("Cannot save track file, please retry")
		ctx.RenderWithErr(ctx.Gettext("file is invalid"), tmplUpload, &f)
		return
	}

	t.Mimetype = mimetype
	if mimetype != "audio/mpeg" {
		t.TranscodeNeeded = true
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
			log.Errorf("Cannot remove temp file '%s': %s", fName, err)
		} else {
			log.Infof("File removed: %s", fName)
		}
		return
	}
	log.Debugf("Track created: %d/%s", t.ID, t.Title)

	sig := &tasks.Signature{
		Name: "TranscodeAndFetchInfofs",
		Args: []tasks.Arg{{Type: "int64", Value: t.ID}},
	}
	server, err := workers.CreateServer()
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Cannot initiate the worker connection, please retry again."))
		if t.TranscodeNeeded {
			err = models.UpdateTrackState(t.ID, &models.Track{TranscodeState: models.ProcessingRetrying}, models.TrackTranscoding)
			if err != nil {
				log.Errorf("CreateServer: Error setting TranscodeState to ProcessingRetry for track %d: %s", t.ID, err)
			}
		}

		err = models.UpdateTrackState(t.ID, &models.Track{MetadatasState: models.ProcessingRetrying}, models.TrackMetadatas)
		if err != nil {
			log.Errorf("CreateServer: Error setting MetadatasState to ProcessingRetry for track %d: %s", t.ID, err)
		}
	}
	_, err = server.SendTask(sig)
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Cannot push the worker job, the watchdog should take care of it."))
		if t.TranscodeNeeded {
			err = models.UpdateTrackState(t.ID, &models.Track{TranscodeState: models.ProcessingRetrying}, models.TrackTranscoding)
			if err != nil {
				log.Errorf("SendTask: Error setting TranscodeState to ProcessingRetry for track %d: %s", t.ID, err)
			}
		}
		err = models.UpdateTrackState(t.ID, &models.Track{MetadatasState: models.ProcessingRetrying}, models.TrackMetadatas)
		if err != nil {
			log.Errorf("SendTask: Error setting MetadatasState to ProcessingRetry for track %d: %s", t.ID, err)
		}
	}

	ctx.Flash.Success(ctx.Gettext("Track uploaded"))
	ctx.SubURLRedirect(ctx.URLFor("track_show", ":userSlug", ctx.User.Slug, ":trackSlug", t.Slug))
}

// Show [GET]
func Show(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 500)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	track, err := models.GetTrackWithInfoBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track With Info from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	// TODO check for track.ready

	ctx.Data["track"] = track
	ctx.Data["user"] = user
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track.Title, user.UserName, setting.AppName)
	ctx.PageIs("TrackShow")

	if track.AlbumID > 0 && track.AlbumOrder > 0 {
		album, err := models.GetAlbumByID(track.AlbumID)
		if err != nil {
			log.Errorf("Cannot get album %d for track %d: %s", track.AlbumID, track.ID, err)
			ctx.Flash.Error(ctx.Gettext("Invalid album."))
			//ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			ctx.Data["album"] = nil
		} else {
			ctx.Data["album"] = album
		}
	}

	// TODO: handle tmplShowWait

	ctx.HTML(200, tmplShow)
}

// DevGetMediaTrack [GET] DEV ONLY !
func DevGetMediaTrack(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)
	mimeType := track.Mimetype

	if ctx.Params(":type") == "mp3" {
		fName = fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
		mimeType = "audio/mpeg"
	}

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.Errorf("Cannot read file %s", err)
		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContentNoDownload(fmt.Sprintf("%s%s", strings.TrimSuffix(track.Filename, filepath.Ext(track.Filename)), filepath.Ext(fName)), mimeType, bytes.NewReader(content))

}

// DevGetMediaPngWf [GET] DEV ONLY !
func DevGetMediaPngWf(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, fmt.Sprintf("%s.png", track.Filename))

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.Errorf("Cannot read file %s", err)
		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContentNoDownload(track.Filename, "image/png", bytes.NewReader(content))

}

// DevGetMediaDownload [GET] DEV ONLY !
func DevGetMediaDownload(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, track.Filename)

	if ctx.Params(":type") == "mp3" {
		fName = fmt.Sprintf("%s.mp3", strings.TrimSuffix(fName, filepath.Ext(fName)))
	}

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.Errorf("Cannot read file %s", err)
		ctx.ServerError("Cannot read file", err)
		return
	}

	ctx.ServeContent(fmt.Sprintf("%s__by__%s%s", track.Slug, user.Slug, filepath.Ext(fName)), bytes.NewReader(content))
}

// ListUserTracks [GET]
func ListUserTracks(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	ctx.Data["Title"] = fmt.Sprintf("Tracks of %s - %s", user.UserName, setting.AppName)
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
		UserID:      user.ID,
		WithPrivate: false,
		OnlyReady:   true,
	}

	if ctx.Data["LoggedUserID"] == user.ID {
		opts.WithPrivate = true
		opts.OnlyReady = false
	}

	listOfTracks, tracksCount, err := models.GetTracks(opts)
	if err != nil {
		log.Warnf("Cannot get Tracks with opts %v, %s", opts, err)
		ctx.Flash.Error(ctx.Gettext("Error getting list of tracks"))
		ctx.Handle(500, "ListTracks", err)
		return
	}

	ctx.Data["user"] = user
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

	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    "what about no ?",
			"redirect": false,
		})
		return
	}

	// Get user and track
	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	if ctx.Data["LoggedUserID"] != track.UserID {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Gettext("Unauthorized"),
			"redirect": false,
		})
	}

	err = models.DeleteTrack(track.ID, track.UserID)
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
		"redirect": ctx.SubURLFor("track_list", ":userSlug", user.Slug),
	})
	return
}

// GetJSONWaveform [GET]
func GetJSONWaveform(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	soundInfo, err := models.GetTrackWithInfoBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	if soundInfo.TrackInfo.Waveform != "" && soundInfo.TrackInfo.WaveformErr == "" {
		// MERGE json from .TrackInfo.Waveform
		var w models.Waveform
		err := json.Unmarshal([]byte(soundInfo.TrackInfo.Waveform), &w)

		if err != nil {
			log.Errorf("Cannot unmarshal waveform: %s", err)
			ctx.JSONSuccess(map[string]interface{}{
				"error": "Cannot unmarshal Waveform",
			})
			return
		}

		soundType := "orig"
		if soundInfo.Mimetype != "audio/mpeg" {
			soundType = "mp3"
		}
		ctx.JSONSuccess(map[string]interface{}{
			"waveform":    w,
			"track_url":   ctx.URLFor("media_track_stream", ":userSlug", user.Slug, ":trackSlug", soundInfo.Slug, ":type", soundType),
			"wf_png":      ctx.URLFor("media_track_waveform", ":userSlug", user.Slug, ":trackSlug", soundInfo.Slug),
			"title":       soundInfo.Title,
			"description": soundInfo.Description,
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
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 500)
		return
	}
	if !ctx.IsLogged {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	if ctx.Data["LoggedUserID"] != user.ID {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	track, err := models.GetTrackWithInfoBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track With Info from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	albums, err := models.GetMapNameIDOfAlbums(ctx.User.ID)
	if err != nil {
		log.Errorf("Error getting album list for user %d: %v", ctx.User.ID, err)
	}

	ctx.Data["albums"] = albums
	ctx.Data["description"] = track.Description
	ctx.Data["is_private"] = track.IsPrivate
	ctx.Data["show_dl_link"] = track.ShowDlLink
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track.Title, user.UserName, setting.AppName)
	ctx.Data["title"] = track.Title
	ctx.Data["cur_album"] = track.AlbumID
	ctx.PageIs("TrackEdit")

	// TODO: handle tmplShowWait

	ctx.HTML(200, tmplEdit)
}

// EditPost [POST]
func EditPost(ctx *context.Context, f form.TrackEdit) {
	if !ctx.IsLogged {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	if ctx.HasError() {
		ctx.Success(tmplUpload)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Errorf("Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Errorf("Cannot get Track from slug %s and user %d: %s", ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	track.Title = f.Title
	track.Description = f.Description
	track.IsPrivate = f.IsPrivate
	track.ShowDlLink = f.ShowDlLink

	if f.Album > 0 {
		track.AlbumID = f.Album
		count, err := models.GetCountOfAlbumTracks(f.Album)
		if err != nil {
			log.Errorf("Cannot get count for album %d: %s", f.Album, err)
			count = 0 // well, yes
		}
		track.AlbumOrder = count + 1 // if zero it will be Track 1, etc.
	} else {
		// zéro is considered as "unassociated"
		track.AlbumID = 0
		track.AlbumOrder = 0
	}

	err = models.UpdateTrack(&track)
	if err != nil {
		switch {
		default:
			ctx.Handle(500, "EditTrack", err)
		}
		return
	}

	ctx.Flash.Success(ctx.Gettext("Track edited"))
	ctx.SubURLRedirect(ctx.URLFor("track_show", ":userSlug", user.Slug, ":trackSlug", track.Slug))
}
