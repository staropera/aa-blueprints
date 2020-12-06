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
            // { data: 'location'},
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
            //{ "visible": false, "targets": [6] }
        ],

        order: [
            [1, "asc"],
            [2, "asc"],
        ],
        /*
        filterDropDown:
        {
            columns: [
                {
                    idx: 6,
                    title: titleCorporation
                },

            ],
            bootstrap: true
        }

        createdRow: function (row, data, dataIndex) {
            if (data['is_reinforced']) {
                $(row).addClass('danger');
            }
        }*/
    });
});
