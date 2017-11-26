package routes

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"dev.sigpipe.me/dashie/reel2bits/models"
	"github.com/Unknwon/paginater"
	log "github.com/sirupsen/logrus"
)

const (
	tmplTimeline  = "timeline"
	tmplImpressum = "impressum"
)

// NotFound [GET]
func NotFound(ctx *context.Context) {
	ctx.Title(ctx.Tr("error.page_not_found"))
	ctx.Handle(404, "home.NotFound", nil)
}

// Impressum [GET]
func Impressum(ctx *context.Context) {
	ctx.Title(ctx.Tr("impressum.title"))
	ctx.Success(tmplImpressum)
}

// Home [GET]
func Home(ctx *context.Context) {
	ctx.Title("app.home_title")
	ctx.PageIs("HubHome")

	page := ctx.QueryInt("page")
	if page <= 0 {
		page = 1
	}
	ctx.Data["PageNumber"] = page

	opts := &models.TimelineItemsOpts{
		PageSize: 10, // TODO: put this in config
		Page:     page,
	}

	listOfItems, itemsCount, err := models.GetTimelineItems(opts)
	if err != nil {
		log.Warnf("Cannot get TimelineItems with opts %v, %s", opts, err)
		ctx.Flash.Error(ctx.Tr("track_list.error_getting_list"))
		ctx.Handle(500, "ListTimelineItems", err)
		return
	}

	ctx.Data["items"] = listOfItems
	ctx.Data["items_count"] = itemsCount

	ctx.Data["Total"] = itemsCount
	ctx.Data["Page"] = paginater.New(int(itemsCount), opts.PageSize, page, 5)

	ctx.Success(tmplTimeline)
}
