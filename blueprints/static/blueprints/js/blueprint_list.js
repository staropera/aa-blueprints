/* global blueprintsDataTableSettings */

$(document).ready(function () {
    "use strict";

    var listDataUrl = blueprintsDataTableSettings.listDataUrl;
    var createRequestUrl = blueprintsDataTableSettings.createRequestUrl;
    var createRequestModalUrl =
        blueprintsDataTableSettings.createRequestModalUrl;
    var dataTablesPageLength = blueprintsDataTableSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsDataTableSettings.dataTablesPaging;
    var csrfToken = blueprintsDataTableSettings.csrfToken;
    /* dataTable def */
    $("#table-blueprints").DataTable({
        ajax: {
            url: listDataUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "type_icon" },
            { data: "type_name" },
            {
                className: "right-column",
                data: "quantity",
            },
            { data: "owner" },
            { data: "material_efficiency" },
            { data: "time_efficiency" },
            { data: "original" },
            { data: "runs" },
            { data: "blueprint_id" },
            // hidden columns
            { data: "location" },
            { data: "filter_is_original" },
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 2, 8] },
            { visible: false, targets: [9, 10] },
            {
                render: function (data, type, row) {
                    if (type === "display") {
                        if (row["original"] != "") {
                            return (
                                '<button class="btn btn-success" data-toggle="modal" data-target="#modalCreateRequestContainer" data-ajax_url="' +
                                createRequestModalUrl +
                                "?blueprint_id=" +
                                data +
                                '" aria-label="Create Request"><span class="fas fa-copy"></span></button>'
                            );
                        } else {
                            return "";
                        }
                    }

                    return data;
                },
                targets: [8],
            },
        ],

        order: [
            [9, "asc"],
            [1, "asc"],
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 9,
                    title:
                        blueprintsDataTableSettings.translation.filterLocation,
                },
                { idx: 3 },
                { idx: 4 },
                { idx: 5 },
                {
                    idx: 10,
                    title:
                        blueprintsDataTableSettings.translation
                            .filterIsOriginal,
                },
            ],
            autoSize: false,
            bootstrap: true,
        },

        drawCallback: function (settings) {
            var api = this.api();
            var rows = api.rows({ page: "current" }).nodes();
            var last = null;

            api.column(9, { page: "current" })
                .data()
                .each(function (group, i) {
                    if (last !== group) {
                        $(rows)
                            .eq(i)
                            .before(
                                '<tr class="tr-group"><td colspan="9">' +
                                    group +
                                    "</td></tr>"
                            );

                        last = group;
                    }
                });
        },
    });
});
