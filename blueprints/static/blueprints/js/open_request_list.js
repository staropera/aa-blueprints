/* global blueprintsDataTableSettings */

$(document).ready(function () {
    "use strict";

    var openRequestListUrl = blueprintsDataTableSettings.openRequestListUrl;
    var openRequestUrl = blueprintsDataTableSettings.openRequestUrl;
    var cancelRequestUrl = blueprintsDataTableSettings.cancelRequestUrl;
    var fulfillRequestUrl = blueprintsDataTableSettings.fulfillRequestUrl;
    var inProgressRequestUrl = blueprintsDataTableSettings.inProgressRequestUrl;
    var viewRequestModalUrl = blueprintsDataTableSettings.viewRequestModalUrl;
    var dataTablesPageLength = blueprintsDataTableSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsDataTableSettings.dataTablesPaging;
    var csrfToken = blueprintsDataTableSettings.csrfToken;
    /* dataTable def */
    $("#table-open-requests").DataTable({
        ajax: {
            url: openRequestListUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "type_icon" },
            { data: "type_name" },
            { data: "runs" },
            { data: "requestor" },
            { data: "requestee" },
            {
                className: "right-column",
                data: "request_id",
            },
            {
                data: "status",
            },
            {
                data: "status_display",
            },
            // hidden columns
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 5] },
            { visible: false, targets: [6, 7] },
            {
                // The `data` parameter refers to the data for the cell (defined by the
                // `data` option, which defaults to the column being worked with, in
                // this case `data: 0`.
                render: function (data, type, row) {
                    if (type === "display") {
                        if (row["status"] == "OP") {
                            var buttons =
                                '<button class="btn btn-info" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                                viewRequestModalUrl +
                                "?request_id=" +
                                data +
                                '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                            buttons +=
                                '<form class="inline" method="post" action="' +
                                cancelRequestUrl +
                                '">' +
                                csrfToken +
                                '<input type="hidden" name="request_id" value="' +
                                data +
                                '" /><button type="submit" class="btn btn-danger" aria-label="Cancel Request"><span class="fas fa-trash"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' +
                                inProgressRequestUrl +
                                '">' +
                                csrfToken +
                                '<input type="hidden" name="request_id" value="' +
                                data +
                                '" /><button type="submit" class="btn btn-info" aria-label="Claim Request"><span class="fas fa-clipboard-check"></span></button></form>';
                            return buttons;
                        } else if (row["status"] == "IP") {
                            var buttons =
                                '<button class="btn btn-info" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                                viewRequestModalUrl +
                                "?request_id=" +
                                data +
                                '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                            buttons +=
                                '<form class="inline" method="post" action="' +
                                openRequestUrl +
                                '">' +
                                csrfToken +
                                '<input type="hidden" name="request_id" value="' +
                                data +
                                '" /><button type="submit" class="btn btn-warning" aria-label="Re-Open Request"><span class="fas fa-undo"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' +
                                cancelRequestUrl +
                                '">' +
                                csrfToken +
                                '<input type="hidden" name="request_id" value="' +
                                data +
                                '" /><button type="submit" class="btn btn-danger" aria-label="Cancel Request"><span class="fas fa-trash"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' +
                                fulfillRequestUrl +
                                '">' +
                                csrfToken +
                                '<input type="hidden" name="request_id" value="' +
                                data +
                                '" /><button type="submit" class="btn btn-success" aria-label="Fulfill Request"><span class="fas fa-clipboard-check"></span></button></form>';
                            return buttons;
                        } else {
                            return "";
                        }
                    }

                    return data;
                },
                targets: [5],
            },
        ],

        order: [
            [6, "asc"],
            [1, "asc"],
        ],

        drawCallback: function (settings) {
            var api = this.api();
            var rows = api.rows({ page: "current" }).nodes();
            var last = null;

            api.column(7, { page: "current" })
                .data()
                .each(function (group, i) {
                    if (last !== group) {
                        $(rows)
                            .eq(i)
                            .before(
                                '<tr class="tr-group"><td colspan="6">' +
                                    group +
                                    "</td></tr>"
                            );

                        last = group;
                    }
                });
        },
    });
});
