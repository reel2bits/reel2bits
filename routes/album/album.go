package album

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/Unknwon/paginater"
	log "gopkg.in/clog.v1"
)

const (
	tmplNew       = "album/new"
	tmplShow      = "album/show"
	tmplAlbumList = "album/list"
	tmplEdit      = "album/edit"
)

// New [GET]
func New(ctx *context.Context) {
	ctx.Title("album.title_new")
	ctx.PageIs("AlbumNew")

	ctx.HTML(200, tmplNew)
}

// NewPost [POST]
func NewPost(ctx *context.Context, f form.Album) {
	ctx.Title("album.title_new")
	ctx.PageIs("AlbumNew")

	if ctx.HasError() {
		ctx.Success(tmplNew)
		return
	}

	a := &models.Album{
		UserID:      ctx.User.ID,
		Name:        f.Name,
		Description: f.Description,
		IsPrivate:   f.IsPrivate,
	}

	if err := models.CreateAlbum(a); err != nil {
		switch {
		case models.IsErrTrackTitleAlreadyExist(err):
			ctx.Data["Err_Title"] = true
			ctx.RenderWithErr(ctx.Tr("form.track_title_exists"), tmplNew, &f)
		default:
			ctx.Handle(500, "CreateTrack", err)
		}

		return
	}
	log.Trace("Album created: %d/%s", a.ID, a.Name)

	ctx.Flash.Success(ctx.Tr("album.new_success"))
	ctx.SubURLRedirect(ctx.URLFor("album_show", ":userSlug", ctx.User.Slug, ":albumSlug", a.Slug))
}

// ListFromUser [GET]
func ListFromUser(ctx *context.Context) {
	ctx.Title("album.title_list")
	ctx.PageIs("AlbumListFromUser")

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

	ctx.Data["Title"] = fmt.Sprintf("Albums of %s - %s", user.UserName, setting.AppName)

	page := ctx.QueryInt("page")
	if page <= 0 {
		page = 1
	}
	ctx.Data["PageNumber"] = page

	opts := &models.AlbumOptions{
		PageSize:    10, // TODO: put this in config
		Page:        page,
		GetAll:      false,
		UserID:      user.ID,
		WithPrivate: false,
	}

	if ctx.Data["LoggedUserID"] == user.ID {
		opts.WithPrivate = true
	}

	listOfAlbums, albumsCount, err := models.GetAlbums(opts)
	if err != nil {
		log.Warn("Cannot get Albums with opts %v, %s", opts, err)
		ctx.Flash.Error(ctx.Tr("album_list.error_getting_list"))
		ctx.Handle(500, "ListAlbums", err)
		return
	}

	ctx.Data["user"] = user
	ctx.Data["albums"] = listOfAlbums
	ctx.Data["albums_count"] = albumsCount

	ctx.Data["Total"] = albumsCount
	ctx.Data["Page"] = paginater.New(int(albumsCount), opts.PageSize, page, 5)

	ctx.HTML(200, tmplAlbumList)
}

// Show [GET]
func Show(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":albumSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 500)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	album, err := models.GetAlbumBySlugAndUserID(user.ID, ctx.Params(":albumSlug"))
	if err != nil {
		log.Error(2, "Cannot get Album from slug %s and user %d: %s", ctx.Params(":albumSlug"), user.ID, err)
		ctx.Flash.Error("Unknown album.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	ctx.Data["album"] = album
	ctx.Data["album_sounds_count"], err = album.GetTracksCount()
	if err != nil {
		ctx.Flash.Error("Cannot get album tracks count")
		ctx.Data["album_sounds_count"] = 0
	}

	onlyReady := !(ctx.User.ID == album.UserID)

	sound, err := models.GetFirstTrackOfAlbum(album.ID, onlyReady)
	if err != nil {
		//ctx.Flash.Warning("Album is empty.")
		log.Error(2, "Album %d cannot get track at order 1: %s", err)
		//ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		//return
		ctx.Data["sound"] = nil
	} else {
		ctx.Data["sound"] = sound
	}

	tracks, err := models.GetAlbumTracks(album.ID, onlyReady)
	if err != nil {
		log.Error(2, "Cannot get album %d tracks: %s", album.ID, err)
		ctx.Flash.Error("Cannot get album tracks.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 503)
		return
	}
	ctx.Data["tracks"] = tracks

	ctx.Data["user"] = user
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", album.Name, user.UserName, setting.AppName)
	ctx.PageIs("AlbumShow")

	ctx.HTML(200, tmplShow)
}

// Edit [GET]
func Edit(ctx *context.Context) {
	if ctx.Params(":userSlug") == "" || ctx.Params(":albumSlug") == "" {
		ctx.Flash.Error("No.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 500)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	album, err := models.GetAlbumBySlugAndUserID(user.ID, ctx.Params(":albumSlug"))
	if err != nil {
		log.Error(2, "Cannot get Album from slug %s and user %d: %s", ctx.Params(":albumSlug"), user.ID, err)
		ctx.Flash.Error("Unknown album.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	ctx.Data["name"] = album.Name
	ctx.Data["is_private"] = album.IsPrivate
	ctx.Data["description"] = album.Description

	ctx.PageIs("AlbumEdit")
	ctx.HTML(200, tmplEdit)
}

// EditPost [POST]
func EditPost(ctx *context.Context, f form.Album) {
	if !ctx.IsLogged {
		ctx.SubURLRedirect(ctx.URLFor("home"), 403)
		return
	}

	if ctx.HasError() {
		ctx.Success(tmplEdit)
		return
	}

	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.Flash.Error("Unknown user.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	album, err := models.GetAlbumBySlugAndUserID(user.ID, ctx.Params(":albumSlug"))
	if err != nil {
		log.Error(2, "Cannot get Album from slug %s and user %d: %s", ctx.Params(":albumSlug"), user.ID, err)
		ctx.Flash.Error("Unknown album.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		return
	}

	album.Name = f.Name
	album.Description = f.Description
	album.IsPrivate = f.IsPrivate

	err = models.UpdateAlbum(album)
	if err != nil {
		switch {
		default:
			ctx.Handle(500, "EditAlbum", err)
		}
		return
	}

	ctx.Flash.Success(ctx.Tr("album.edit_success"))
	ctx.SubURLRedirect(ctx.URLFor("album_show", ":userSlug", user.Slug, ":albumSlug", album.Slug))

}

// DeleteAlbum [POST]
func DeleteAlbum(ctx *context.Context, f form.AlbumDelete) {
	if ctx.HasError() {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Data["ErrorMsg"],
			"redirect": false,
		})
		return
	}

	if ctx.Params(":userSlug") == "" || ctx.Params(":albumSlug") == "" {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    "what about no ?",
			"redirect": false,
		})
		return
	}

	// Get user and album
	user, err := models.GetUserBySlug(ctx.Params(":userSlug"))
	if err != nil {
		log.Error(2, "Cannot get User from slug %s: %s", ctx.Params(":userSlug"), err)
		ctx.ServerError("Unknown user.", err)
		return
	}

	album, err := models.GetAlbumBySlugAndUserID(user.ID, ctx.Params(":albumSlug"))
	if err != nil {
		log.Error(2, "Cannot get Album from slug %s and user %d: %s", ctx.Params(":albumSlug"), user.ID, err)
		ctx.ServerError("Unknown album.", err)
		return
	}

	if ctx.Data["LoggedUserID"] != album.UserID {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Tr("user.unauthorized"),
			"redirect": false,
		})
	}

	err = models.DeleteAlbum(album.ID, album.UserID)
	if err != nil {
		ctx.Flash.Error(ctx.Tr("album_delete.error_deleting"))
		log.Warn("DeleteAlbum.Delete: %v", err)
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Tr("album_delete.error_deleting"),
			"redirect": false,
		})
		return
	}

	ctx.Flash.Success(ctx.Tr("album.delete_success"))
	ctx.JSONSuccess(map[string]interface{}{
		"error":    nil,
		"redirect": ctx.SubURLFor("album_list", ":userSlug", user.Slug),
	})
	return
}
