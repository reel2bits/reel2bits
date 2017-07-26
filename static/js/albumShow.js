$(document).on("click", "a.delete_album_link", function(e) {
    // Delete link actions : Ajax with CSRF
    e.preventDefault();

    let $this = $(this);

    let rUser = $this.data("user");
    let rAlbum = $this.data("album");

    $.ajax({
        type: "POST",
        url: $this.data('url'),
        data: {"_csrf": csrf, "user": rUser, "album": rAlbum},
        dataType: "json",
        success: function(data) {
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log("Error, status = " + textStatus + ", " + "error thrown: " + errorThrown);

        }
    });
});