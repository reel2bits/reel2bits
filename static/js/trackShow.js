$(document).on("click", "a.delete_link", function(e) {
    // Delete link actions : Ajax with CSRF
    e.preventDefault();

    let $this = $(this);

    let rUser = $this.data("user");
    let rTrack = $this.data("track");

    if (confirm("Are you sure ?") === true) {
        $.ajax({
            type: "POST",
            url: $this.data('url'),
            data: {"_csrf": csrf, "user": rUser, "track": rTrack},
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
    }
});