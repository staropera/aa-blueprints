/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var userRequestListUrl = blueprintsSettings.userRequestListUrl;
    function cancelRequestUrl(id) {
        return blueprintsSettings.cancelRequestUrl.replace("12345",id);
    }
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var csrfToken = blueprintsSettings.csrfToken;
    var viewRequestModalUrl = blueprintsSettings.viewRequestModalUrl;
    var markRequestCancelledText = blueprintsSettings.translation.markRequestCancelled;

    /* dataTable def */
    $("#table-user-requests").DataTable({
        ajax: {
            url: userRequestListUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "type_icon" },
            { data: "type_name" },
            { data: "runs" },
            { data: "owner_name" },
            {
                className: "right-column",
                data: "request_id",
            },
            // hidden columns,
            {
                data: "status",
            },
            {
                data: "status_display",
            },
            {
                data: "owner_type",
            },
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 4] },
            { visible: false, targets: [5, 6, 7] },
            {
                // The `data` parameter refers to the data for the cell (defined by the
                // `data` option, which defaults to the column being worked with, in
                // this case `data: 0`.
                render: function (data, type, row) {
                    if (type === "display") {
                        var buttons =
                            '<button class="btn btn-info btn-sm btn-square" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                            viewRequestModalUrl +
                            "?request_id=" +
                            data +
                            '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                        buttons +=
                            '<form method="post" class="inline" action="' + cancelRequestUrl(data) + '">' +
                            csrfToken +
                            '<button type="submit" class="btn btn-danger btn-sm btn-square" aria-label="' + markRequestCancelledText + '" title="' + markRequestCancelledText + '"><span class="fas fa-trash"></span></button></form>';
                            return buttons;
                    }

                    return data;
                },
                targets: [4],
            },
            {
                render: function (data, type, row) {
                    if (type === "display") {
                        if (row.owner_type === "corporation") {
                            return '<span class="fas fa-briefcase"></span> ' + data;
                        } else if (row.owner_type === "character") {
                            return '<span class="fas fa-user"></span> ' + data;
                        } else {
                            return "";
                        }
                    }

                    return data;
                },
                targets: [3],
            }
        ],

        order: [
            [5, "asc"],
            [1, "asc"],
        ],
        drawCallback: function (settings) {
            var api = this.api();
            var rows = api.rows({ page: "current" }).nodes();
            var last = null;

            api.column(6, { page: "current" })
                .data()
                .each(function (group, i) {
                    if (last !== group) {
                        $(rows)
                            .eq(i)
                            .before('<tr class="tr-group"><td colspan="5">' + group + "</td></tr>");

                        last = group;
                    }
                });
        },
    });
});
