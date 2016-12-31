$(function () {
    $("#name")
        .autocomplete({
            minLength: 1,
            source: "/autocomplete/parts/name",
            dataType: "jsonp",
            focus: function (event, ui) {
                $("#name").val(ui.item.Name);
                return false;
            },
            select: function (event, ui) {
                $("#name").val(ui.item.Name);
                return false;
            },
            create: function () {
                $(this).data('ui-autocomplete')._renderItem = function (ul, item) {
                    return $('<li>')
                        .append('<a><i class="fa fa-angle-double-right"></i> ' + item.Name + '<br><small>' + item.Description + '</small></a>')
                        .appendTo(ul);
                };
            }
        });

    $("#status")
        .autocomplete({
            minLength: 1,
            source: "/autocomplete/parts/status",
            dataType: "jsonp"
        });

    $("#condition")
        .autocomplete({
            minLength: 1,
            source: "/autocomplete/parts/condition",
            dataType: "jsonp"
        });
});