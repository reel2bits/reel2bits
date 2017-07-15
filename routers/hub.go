package routers

import "dev.sigpipe.me/dashie/reel2bits/context"

func NotFound(ctx *context.Context) {
	ctx.Title(ctx.Tr("error.page_not_found"))
	ctx.Handle(404, "home.NotFound", nil)
}

func Home(ctx *context.Context) {
	ctx.Title("Home page")
	ctx.PageIs("hub.home")
	ctx.Success("home")
}
