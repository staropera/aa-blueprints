/* global blueprintsDataTableSettings */

$(document).ready(function () {
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
            { data: "location" },
            { data: "owner" },
            { data: "material_efficiency" },
            { data: "time_efficiency" },
            { data: "original" },
            { data: "runs" },
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0] },
            { visible: false, targets: [2] },
        ],

        order: [
            [2, "asc"],
            [1, "asc"],
        ],
        drawCallback: function (settings) {
            var api = this.api();
            var rows = api.rows({ page: "current" }).nodes();
            var last = null;

            api.column(2, { page: "current" })
                .data()
                .each(function (group, i) {
                    if (last !== group) {
                        $(rows)
                            .eq(i)
                            .before(
                                '<tr class="group"><td colspan="7">' +
                                    group +
                                    "</td></tr>"
                            );

                        last = group;
                    }
                });
        },
    });
});
