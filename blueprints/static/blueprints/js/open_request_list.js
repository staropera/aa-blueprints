/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var openRequestListUrl = blueprintsSettings.openRequestListUrl;
    function openRequestUrl(id) {
        return blueprintsSettings.openRequestUrl.replace("12345", id);
    }
    function cancelRequestUrl(id) {
        return blueprintsSettings.cancelRequestUrl.replace("12345", id);
    }
    function fulfillRequestUrl(id) {
        return blueprintsSettings.fulfillRequestUrl.replace("12345", id);
    }
    function inProgressRequestUrl(id) {
        return blueprintsSettings.inProgressRequestUrl.replace("12345", id);
    }
    var viewRequestModalUrl = blueprintsSettings.viewRequestModalUrl;
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var csrfToken = blueprintsSettings.csrfToken;
    var markRequestCancelledText = blueprintsSettings.translation.markRequestCancelled;
    var markRequestFulfilledText = blueprintsSettings.translation.markRequestFulfilled;
    var markRequestInProgressText = blueprintsSettings.translation.markRequestInProgress;
    var markRequestOpenText = blueprintsSettings.translation.markRequestOpen;
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
            { data: "owner_name" },
            {
                className: "right-column",
                data: "request_id",
            },
            // hidden columns
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
            { sortable: false, targets: [0, 5] },
            { visible: false, targets: [6, 7, 8] },
            {
                // The `data` parameter refers to the data for the cell (defined by the
                // `data` option, which defaults to the column being worked with, in
                // this case `data: 0`.
                render: function (data, type, row) {
                    if (type === "display") {
                        var buttons = '';

                        if (row.status === "OP") {
                            buttons +=
                                '<button class="btn btn-info btn-sm btn-square" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                                viewRequestModalUrl +
                                "?request_id=" +
                                data +
                                '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                            buttons +=
                                '<form class="inline" method="post" action="' + cancelRequestUrl(data) + '">' +
                                csrfToken +
                                '<button type="submit" class="btn btn-danger btn-sm btn-square" aria-label="' + markRequestCancelledText + '" title="' + markRequestCancelledText + '"><span class="fas fa-trash"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' + inProgressRequestUrl(data) + '">' +
                                csrfToken +
                                '<button type="submit" class="btn btn-primary btn-sm btn-square" aria-label="' + markRequestInProgressText + '" title="' + markRequestInProgressText + '"><span class="fas fa-clipboard-check"></span></button></form>';
                            return buttons;
                        } else if (row.status === "IP") {
                            buttons +=
                                '<button class="btn btn-info btn-sm btn-square" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                                viewRequestModalUrl +
                                "?request_id=" +
                                data +
                                '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                            buttons +=
                                '<form class="inline" method="post" action="' + openRequestUrl(data) + '">' +
                                csrfToken +
                                '<button type="submit" class="btn btn-warning btn-sm btn-square" aria-label="' + markRequestOpenText + '" title="' + markRequestOpenText + '"><span class="fas fa-undo"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' + cancelRequestUrl(data) + '">' +
                                csrfToken +
                                '<button type="submit" class="btn btn-danger btn-sm btn-square" aria-label="' + markRequestCancelledText + '" title="' + markRequestCancelledText + '"><span class="fas fa-trash"></span></button></form>';
                            buttons +=
                                '<form class="inline" method="post" action="' +fulfillRequestUrl(data) +'">' +
                                csrfToken +
                                '<button type="submit" class="btn btn-success btn-sm btn-square"  aria-label="' + markRequestFulfilledText + '" title="' + markRequestFulfilledText + '"><span class="fas fa-clipboard-check"></span></button></form>';
                            return buttons;
                        } else {
                            return "";
                        }
                    }

                    return data;
                },
                targets: [5],
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
                targets: [4],
            }
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
