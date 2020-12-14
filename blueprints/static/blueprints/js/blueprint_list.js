/* global blueprintsDataTableSettings */

$(document).ready(function () {
    "use strict";

    var listDataUrl = blueprintsDataTableSettings.listDataurl;
    var dataTablesPageLength = blueprintsDataTableSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsDataTableSettings.dataTablesPaging;

    /* dataTable def */
    $("#tab_blueprints").DataTable({
        ajax: {
            url: listDataUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "type_icon" },
            { data: "type" },
            { data: "quantity" },
            { data: "owner" },
            { data: "material_efficiency" },
            { data: "time_efficiency" },
            { data: "original" },
            { data: "runs" },

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
            { sortable: false, targets: [0, 2] },
            { visible: false, targets: [8, 9] },
        ],

        order: [
            [8, "asc"],
            [1, "asc"],
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 8,
                    title:
                        blueprintsDataTableSettings.translation.filterLocation,
                },
                { idx: 3 },
                { idx: 4 },
                { idx: 5 },
                {
                    idx: 9,
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

            api.column(8, { page: "current" })
                .data()
                .each(function (group, i) {
                    if (last !== group) {
                        $(rows)
                            .eq(i)
                            .before(
                                '<tr class="tr-group"><td colspan="8">' +
                                    group +
                                    "</td></tr>"
                            );

                        last = group;
                    }
                });
        },
    });
});
