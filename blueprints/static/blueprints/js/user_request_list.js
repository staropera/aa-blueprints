/* global blueprintsDataTableSettings */

$(document).ready(function () {
    "use strict";

    var userRequestListUrl = blueprintsDataTableSettings.userRequestListUrl;
    var deleteRequestUrl = blueprintsDataTableSettings.deleteRequestUrl;
    var dataTablesPageLength = blueprintsDataTableSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsDataTableSettings.dataTablesPaging;
    var csrfToken = blueprintsDataTableSettings.csrfToken;
    var viewRequestModalUrl = blueprintsDataTableSettings.viewRequestModalUrl;
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
            { data: "requestee" },
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
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 4] },
            { visible: false, targets: [5, 6] },
            {
                // The `data` parameter refers to the data for the cell (defined by the
                // `data` option, which defaults to the column being worked with, in
                // this case `data: 0`.
                render: function (data, type, row) {
                    if (type === "display") {
                        var buttons =
                            '<button class="btn btn-info" data-toggle="modal" data-target="#modalViewRequestContainer" data-ajax_url="' +
                            viewRequestModalUrl +
                            "?request_id=" +
                            data +
                            '" aria-label="Request Info"><span class="fas fa-info-circle"></span></button>';
                        buttons +=
                            '<form method="post" class="inline" action="' +
                            deleteRequestUrl +
                            '">' +
                            csrfToken +
                            '<input type="hidden" name="request_id" value="' +
                            data +
                            '" /><button type="submit" class="btn btn-danger"><span class="fas fa-trash"></span> </form> ';
                        return buttons;
                    }

                    return data;
                },
                targets: [4],
            },
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
                            .before(
                                '<tr class="tr-group"><td colspan="5">' +
                                    group +
                                    "</td></tr>"
                            );

                        last = group;
                    }
                });
        },
    });
});
