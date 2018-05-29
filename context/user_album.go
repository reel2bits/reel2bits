package context

import (
	"dev.sigpipe.me/dashie/reel2bits/models"
	log "github.com/sirupsen/logrus"
	"gopkg.in/macaron.v1"
)

// AssignURLUser from the slug in URL
func AssignURLUser() macaron.Handler {
	return func(ctx *Context) {
		userName := ctx.Params(":userSlug")

		user, err := models.GetUserBySlug(userName)
		if err != nil {
			log.WithFields(log.Fields{
				"user slug": userName,
			}).Errorf("Cannot get User from slug: %v", err)

			ctx.Flash.Error("Unknown user.")
			ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			return
		}

		ctx.URLUser = user
	}
}

// AssignURLAlbum from the slug in URL
func AssignURLAlbum() macaron.Handler {
	return func(ctx *Context) {
		albumSlug := ctx.Params(":albumSlug")

		album, err := models.GetAlbumBySlugAndUserID(ctx.URLUser.ID, albumSlug)
		if err != nil {
			log.WithFields(log.Fields{
				"album slug": albumSlug,
				"userID":     ctx.URLUser.ID,
			}).Errorf("Cannot get Album from slug and user: %v", err)

			ctx.Flash.Error("Unknown album.")
			ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			return
		}

		ctx.URLAlbum = album
	}
}

// AssignURLTrack without extras from the slug in URL
func AssignURLTrack() macaron.Handler {
	return func(ctx *Context) {
		trackSlug := ctx.Params(":trackSlug")

		track, err := models.GetTrackBySlugAndUserID(ctx.URLUser.ID, trackSlug)
		if err != nil {
			log.WithFields(log.Fields{
				"track slug": trackSlug,
				"userID":     ctx.URLUser.ID,
			}).Errorf("Cannot get Track from slug and user: %v", err)

			ctx.Flash.Error("Unknown track.")
			ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			return
		}

		ctx.URLTrack = track
	}
}

// AssignURLTrackWI with extra informations from the slug in URL
func AssignURLTrackWI() macaron.Handler {
	return func(ctx *Context) {
		trackSlug := ctx.Params(":trackSlug")

		track, err := models.GetTrackWithInfoBySlugAndUserID(ctx.URLUser.ID, trackSlug)
		if err != nil {
			log.WithFields(log.Fields{
				"track slug": trackSlug,
				"userID":     ctx.URLUser.ID,
			}).Errorf("Cannot get Track from slug and user: %v", err)

			ctx.Flash.Error("Unknown track.")
			ctx.SubURLRedirect(ctx.URLFor("home"), 404)
			return
		}

		ctx.URLTrack = track
	}
}
