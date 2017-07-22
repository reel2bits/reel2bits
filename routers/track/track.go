package track


import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/models"
	log "gopkg.in/clog.v1"
	"strings"
	"path/filepath"
	"fmt"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"os"
	"github.com/RichardKnop/machinery/v1/tasks"
	"dev.sigpipe.me/dashie/reel2bits/workers"
	"bytes"
	"io/ioutil"
	"github.com/Unknwon/paginater"
)

const (
	tmplUpload   = "track/upload"
	tmplShow     = "track/show"
	tmplShowWait = "track/show_wait"
	tmplTracksList = "tracks_list"
	tmplEdit = "track/edit"
)

// Upload [GET]
func Upload(ctx *context.Context) {
	ctx.Title("track.title_upload")
	ctx.PageIs("TrackUpload")

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
		UserID: ctx.User.ID,
		Title: f.Title,
		Description: f.Description,
		IsPrivate: f.IsPrivate,
		ShowDlLink: f.ShowDlLink,
		Filename: fmt.Sprintf("%s%s", fileHash, filepath.Ext(f.File.Filename)), // .Ext returns the dot
		FilenameOrig: strings.TrimSuffix(f.File.Filename, filepath.Ext(f.File.Filename)),
		Hash: fileHash,
	}

	mimetype, err := models.SaveTrackFile(f.File, t.Filename, ctx.User.UserName)
	if err != nil {
		log.Error(2, "Cannot save track file: %s", err)
		ctx.Flash.Error("Cannot save track file, please retry")
		ctx.RenderWithErr(ctx.Tr("form.track_file_error"), tmplUpload, &f)
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
			ctx.RenderWithErr(ctx.Tr("form.track_title_exists"), tmplUpload, &f)
		default:
			ctx.Handle(500, "CreateTrack", err)
		}

		// Deleting the file
		storDir := filepath.Join(setting.Storage.Path, "tracks", ctx.User.Slug)
		fName := filepath.Join(storDir, t.Filename)
		err := os.RemoveAll(fName)
		if err != nil {
			log.Error(2, "Cannot remove temp file '%s': %s", fName, err)
		} else {
			log.Info("File removed: %s", fName)
		}
		return
	}
	log.Trace("Track created: %d/%s", t.ID, t.Title)

	sig := &tasks.Signature{
		Name: "TranscodeAndFetchInfos",
		Args: []tasks.Arg{{Type: "int64", Value: t.ID,},},
	}
	server, err := workers.CreateServer()
	if err != nil {
		ctx.Flash.Error("Cannot initiate the worker connection, please retry again.")
		if t.TranscodeNeeded {
			err = models.UpdateTrackState(&models.Track{ID: t.ID, TranscodeState: models.ProcessingRetrying}, models.TrackTranscoding)
			if err != nil {
				log.Error(2, "CreateServer: Error setting TranscodeState to ProcessingRetry for track %d: %s", t.ID, err)
			}
		}

		err = models.UpdateTrackState(&models.Track{ID: t.ID, MetadatasState: models.ProcessingRetrying}, models.TrackMetadatas)
		if err != nil {
			log.Error(2, "CreateServer: Error setting MetadatasState to ProcessingRetry for track %d: %s", t.ID, err)
		}
	}
	_, err = server.SendTask(sig)
	if err != nil {
		ctx.Flash.Error("Cannot push the worker job, please retry again.")
		if t.TranscodeNeeded {
			err = models.UpdateTrackState(&models.Track{ID: t.ID, TranscodeState: models.ProcessingRetrying}, models.TrackTranscoding)
			if err != nil {
				log.Error(2, "SendTask: Error setting TranscodeState to ProcessingRetry for track %d: %s", t.ID, err)
			}
		}
		err = models.UpdateTrackState(&models.Track{ID: t.ID, MetadatasState: models.ProcessingRetrying}, models.TrackMetadatas)
		if err != nil {
			log.Error(2, "SendTask: Error setting MetadatasState to ProcessingRetry for track %d: %s", t.ID, err)
		}
	}

	ctx.Flash.Success(ctx.Tr("track.upload_success"))
	trackURI := fmt.Sprintf("%s/u/%s/%s", setting.AppSubURL, ctx.User.Slug, t.Slug)

	ctx.SubURLRedirect(trackURI)
}

// Show [GET]
func Show(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.Redirect(setting.AppSubURL + "/", 500)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	track, err := models.GetTrackWithInfoBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track With Info from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	// TODO check for track.ready

	if len(track) < 1 {
		track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
		if err != nil {
			log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
			ctx.Flash.Error("Unknown track.")
			ctx.Redirect(setting.AppSubURL + "/", 404)
			return
		}
		ctx.Data["track"] = track
		ctx.Data["user"] = user
		ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track.Title, user.UserName, setting.AppName)
		ctx.PageIs("TrackShowWait")

		ctx.HTML(200, tmplShowWait)
	} else {
		ctx.Data["track"] = track[0]
		ctx.Data["user"] = user
		ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track[0].Track.Title, user.UserName, setting.AppName)
		ctx.PageIs("TrackShow")

		ctx.HTML(200, tmplShow)
	}
}

// DevGetMediaTrack [GET] DEV ONLY !
func DevGetMediaTrack(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.ServerError("No.", nil)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
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
		log.Error(2, "Cannot read file %s", err)
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
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	storDir := filepath.Join(setting.Storage.Path, "tracks", user.Slug)
	fName := filepath.Join(storDir, fmt.Sprintf("%s.png", track.Filename))

	content, err := ioutil.ReadFile(fName)
	if err != nil {
		log.Error(2, "Cannot read file %s", err)
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
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
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
		log.Error(2, "Cannot read file %s", err)
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
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
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
		PageSize: 10,	// TODO: put this in config
		Page: page,
		GetAll: false,
		UserID: user.ID,
		WithPrivate: false,
		OnlyReady: true,
	}

	if ctx.Data["LoggedUserID"] == user.ID {
		opts.WithPrivate = true
		opts.OnlyReady = false
	}

	listOfTracks, tracksCount, err := models.GetTracks(opts)
	if err != nil {
		log.Warn("Cannot get Tracks with opts %v, %s", opts, err)
		ctx.Flash.Error(ctx.Tr("track_list.error_getting_list"))
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

func DeleteTrack(ctx *context.Context, f form.TrackDelete) {
	if ctx.HasError() {
		ctx.JSONSuccess(map[string]interface{}{
			"error": ctx.Data["ErrorMsg"],
			"redirect": false,
		})
		return
	}

	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.JSONSuccess(map[string]interface{}{
			"error": "what about no ?",
			"redirect": false,
		})
		return
	}

	// Get user and track
	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
		ctx.ServerError("Unknown track.", err)
		return
	}

	if ctx.Data["LoggedUserID"] != track.UserID {
		ctx.JSONSuccess(map[string]interface{}{
			"error": ctx.Tr("user.unauthorized"),
			"redirect": false,
		})
	}

	err = models.DeleteTrack(track.ID, track.UserID)
	if err != nil {
		ctx.Flash.Error(ctx.Tr("track_delete.error_deleting"))
		log.Warn("DeleteTrack.Delete: %v", err)
		ctx.JSONSuccess(map[string]interface{}{
			"error": ctx.Tr("track_delete.error_deleting"),
			"redirect": false,
		})
		return
	}

	ctx.JSONSuccess(map[string]interface{}{
		"error": nil,
		"redirect": setting.AppSubURL + "/u/" + user.Slug,
	})
	return
}

func Edit(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":trackSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.Redirect(setting.AppSubURL + "/", 500)
		return
	}
	if !ctx.IsLogged {
		ctx.Redirect(setting.AppSubURL + "/")
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	if ctx.Data["LoggedUserID"] != user.ID {
		ctx.Redirect(setting.AppSubURL + "/", 403)
		return
	}

	track, err := models.GetTrackWithInfoBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track With Info from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	if len(track) < 1 {
		track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
		if err != nil {
			log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
			ctx.Flash.Error("Unknown track.")
			ctx.Redirect(setting.AppSubURL + "/", 404)
			return
		}
		ctx.Data["track"] = track
		ctx.Data["user"] = user
		ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track.Title, user.UserName, setting.AppName)
		ctx.PageIs("TrackShowWait")

		ctx.HTML(200, tmplShowWait)
	} else {
		ctx.Data["title"] = track[0].Title
		ctx.Data["description"] = track[0].Description
		ctx.Data["is_private"] = track[0].IsPrivate
		ctx.Data["show_dl_link"] = track[0].ShowDlLink

		ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", track[0].Track.Title, user.UserName, setting.AppName)
		ctx.PageIs("TrackEdit")

		ctx.HTML(200, tmplEdit)
	}
}

func EditPost(ctx *context.Context, f form.TrackEdit) {
	if !ctx.IsLogged {
		ctx.Redirect(setting.AppSubURL + "/")
		return
	}

	if ctx.HasError() {
		ctx.Success(tmplUpload)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	track, err := models.GetTrackBySlugAndUserID(user.ID, ctx.Params(":trackSlug"))
	if err != nil {
		log.Error(2, "Cannot get Track from slug %s and user %d: %s",ctx.Params(":trackSlug"), user.ID, err)
		ctx.Flash.Error("Unknown track.")
		ctx.Redirect(setting.AppSubURL + "/", 404)
		return
	}

	track.Title = f.Title
	track.Description = f.Description
	track.IsPrivate = f.IsPrivate
	track.ShowDlLink = f.ShowDlLink

	err = models.UpdateTrack(track)
	if err != nil {
		switch {
		default:
			ctx.Handle(500, "EditTrack", err)
		}
		return
	}

	ctx.Redirect(setting.AppSubURL + "/u/" + user.Slug + "/" + track.Slug)
}