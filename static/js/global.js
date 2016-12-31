function show_message(name, title, message) {
    console.log("Showing message " + message);

    var $dialog_master = $('#dialog-master');
    var $dialog = $dialog_master.clone();
    $dialog.attr("id", "dialog-" + name);
    $dialog.attr("title", title);
    $dialog.html(message);

    $dialog_master.append($dialog);

    $dialog.dialog({
        close: function (event, ui) {
            $(this).dialog("close");
            $(this).remove();
        }
    });

}

function show_alert(type, title, message) {
    console.log('Alert: ' + type + ' - ' + title + ' - ' + message);
    // type null, danger, info, success
    msg = title + "<br/><small>" + message + "</small>";
    $.bootstrapGrowl(msg, {type: type})
}

$(document).ajaxError(function (event, request, settings) {
    console.log('triggered');
    if (request.status === 500) {
        return show_alert("danger", "Ajax query failed", "Error 500 :(");
    }
    if (request.responseJSON) {
        return show_alert("danger", "Ajax query failed", request.responseJSON.message);
    }
    show_alert("danger", "Ajax query failed", "Unknown error");
});

$("a.delete_link").click(function() {
    return confirm("Are you sure you want to delete this item ?");
});