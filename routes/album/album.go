package album

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"dev.sigpipe.me/dashie/reel2bits/pkg/form"
	"dev.sigpipe.me/dashie/reel2bits/setting"
	"fmt"
	"github.com/Unknwon/paginater"
	log "github.com/sirupsen/logrus"
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
		Private:     models.BoolToFake(f.IsPrivate),
	}

	if err := models.CreateAlbum(a); err != nil {
		switch {
		case models.IsErrTrackTitleAlreadyExist(err):
			ctx.Data["Err_Title"] = true
			ctx.RenderWithErr(ctx.Gettext("track title already exists"), tmplNew, &f)
		default:
			ctx.Handle(500, "CreateTrack", err)
		}

		return
	}

	log.WithFields(log.Fields{
		"albumID":    a.ID,
		"album name": a.Name,
	}).Debugf("Album created")

	ctx.Flash.Success(ctx.Gettext("Album created"))
	ctx.SubURLRedirect(ctx.URLFor("album_show", ":userSlug", ctx.User.Slug, ":albumSlug", a.Slug))
}

// ListFromUser [GET]
func ListFromUser(ctx *context.Context) {
	ctx.Title("album.title_list")
	ctx.PageIs("AlbumListFromUser")

	ctx.Data["Title"] = fmt.Sprintf("Albums of %s - %s", ctx.URLUser.UserName, setting.AppName)

	page := ctx.QueryInt("page")
	if page <= 0 {
		page = 1
	}
	ctx.Data["PageNumber"] = page

	opts := &models.AlbumOptions{
		PageSize:    10, // TODO: put this in config
		Page:        page,
		GetAll:      false,
		UserID:      ctx.URLUser.ID,
		WithPrivate: false,
	}

	if ctx.Data["LoggedUserID"] == ctx.URLUser.ID {
		opts.WithPrivate = true
	}

	listOfAlbums, albumsCount, err := models.GetAlbums(opts)
	if err != nil {
		log.WithFields(log.Fields{
			"opts": opts,
		}).Warnf("Cannot get Albums with options: %v", err)

		ctx.Flash.Error(ctx.Gettext("Error getting list of albums"))
		ctx.Handle(500, "ListAlbums", err)
		return
	}

	ctx.Data["user"] = ctx.URLUser
	ctx.Data["albums"] = listOfAlbums
	ctx.Data["albums_count"] = albumsCount

	ctx.Data["Total"] = albumsCount
	ctx.Data["Page"] = paginater.New(int(albumsCount), opts.PageSize, page, 5)

	ctx.HTML(200, tmplAlbumList)
}

// Show [GET]
func Show(ctx *context.Context) {
	albumCount, err := ctx.URLAlbum.GetTracksCount()
	if err != nil {
		ctx.Flash.Error("Cannot get album tracks count")
		ctx.Data["album_sounds_count"] = 0
	}

	ctx.Data["album"] = ctx.URLAlbum
	ctx.Data["album_sounds_count"] = albumCount

	onlyReady := !(ctx.User.ID == ctx.URLAlbum.UserID)

	sound, err := models.GetFirstTrackOfAlbum(ctx.URLAlbum.ID, onlyReady)
	if err != nil {
		//ctx.Flash.Warning("Album is empty.")
		log.WithFields(log.Fields{
			"albumID": ctx.URLAlbum.ID,
		}).Errorf("Cannot get Album track at order 1: %v", err)

		//ctx.SubURLRedirect(ctx.URLFor("home"), 404)
		//return
		ctx.Data["sound"] = nil
	} else {
		ctx.Data["sound"] = sound
	}

	tracks, err := models.GetAlbumTracks(ctx.URLAlbum.ID, onlyReady)
	if err != nil {
		log.WithFields(log.Fields{
			"albumID": ctx.URLAlbum.ID,
		}).Errorf("Cannot get album tracks: %v", err)

		ctx.Flash.Error("Cannot get album tracks.")
		ctx.SubURLRedirect(ctx.URLFor("home"), 503)
		return
	}
	ctx.Data["tracks"] = tracks

	ctx.Data["user"] = ctx.URLUser
	ctx.Data["Title"] = fmt.Sprintf("%s by %s - %s", ctx.URLAlbum.Name, ctx.URLUser.UserName, setting.AppName)
	ctx.PageIs("AlbumShow")

	ctx.HTML(200, tmplShow)
}

// Edit [GET]
func Edit(ctx *context.Context) {
	ctx.Data["name"] = ctx.URLAlbum.Name
	ctx.Data["is_private"] = ctx.URLAlbum.IsPrivate()
	ctx.Data["description"] = ctx.URLAlbum.Description

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

	previouslyPrivate := ctx.URLAlbum.IsPrivate()

	ctx.URLAlbum.Name = f.Name
	ctx.URLAlbum.Description = f.Description
	ctx.URLAlbum.Private = models.BoolToFake(f.IsPrivate)

	err := models.UpdateAlbum(&ctx.URLAlbum)
	if err != nil {
		switch {
		default:
			ctx.Handle(500, "EditAlbum", err)
		}
		return
	}

	if previouslyPrivate && !f.IsPrivate {
		albumTracksCount, err := models.GetCountOfAlbumTracks(ctx.URLAlbum.ID)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": ctx.URLAlbum.ID,
			}).Errorf("Cannot get count of album: %v", err)

			albumTracksCount = 0 // well, yes
		}
		if albumTracksCount >= 1 {
			tli := &models.TimelineItem{
				AlbumID: ctx.URLAlbum.ID,
				UserID:  ctx.URLAlbum.UserID,
			}
			err := models.CreateTimelineItem(tli)
			if err != nil {
				log.WithFields(log.Fields{
					"userID": ctx.URLAlbum.ID,
					"album": ctx.URLAlbum.ID,
				}).Errorf("Cannot add track to timeline: %v", err)
			}
		}
	}

	if !previouslyPrivate && f.IsPrivate {
		err = models.DeleteTimelineItem(ctx.URLUser.ID, 0, ctx.URLAlbum.ID)
		if err != nil {
			log.WithFields(log.Fields{
				"albumID": ctx.URLAlbum.ID,
				"userID":  ctx.URLUser.ID,
			}).Errorf("Cannot delete timelineItem: %v", err)
		}
	}

	ctx.Flash.Success(ctx.Gettext("Album edited"))
	ctx.SubURLRedirect(ctx.URLFor("album_show", ":userSlug", ctx.URLUser.Slug, ":albumSlug", ctx.URLAlbum.Slug))

}

// DeleteAlbum [POST]
// FIXME also check using the f orm
func DeleteAlbum(ctx *context.Context, f form.AlbumDelete) {
	if ctx.HasError() {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Data["ErrorMsg"],
			"redirect": false,
		})
		return
	}

	if ctx.Data["LoggedUserID"] != ctx.URLAlbum.UserID {
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Gettext("Unauthorized"),
			"redirect": false,
		})
	}

	err := models.DeleteAlbum(ctx.URLAlbum.ID, ctx.URLAlbum.UserID)
	if err != nil {
		ctx.Flash.Error(ctx.Gettext("Error deleting album"))
		log.Warnf("DeleteAlbum.Delete: %v", err)
		ctx.JSONSuccess(map[string]interface{}{
			"error":    ctx.Gettext("Error deleting album"),
			"redirect": false,
		})
		return
	}

	ctx.Flash.Success(ctx.Gettext("Album deleted"))
	ctx.JSONSuccess(map[string]interface{}{
		"error":    nil,
		"redirect": ctx.SubURLFor("album_list", ":userSlug", ctx.URLUser.Slug),
	})
	return
}
