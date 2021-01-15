/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var listDataUrl = blueprintsSettings.listDataUrl;
    var listDataFddUrl = blueprintsSettings.listDataFddUrl;
    var viewBlueprintModalUrl = blueprintsSettings.viewBlueprintModalUrl;
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var viewBlueprintText = blueprintsSettings.translation.viewBlueprint;

    /* dataTable def */
    $("#table-blueprints").DataTable({
        ajax: {
            url: listDataUrl,
            cache: false,
        },

        "processing": true,
        "serverSide": true,
        columns: [
            {
                name: "eve_type_id",
                target: [0],
                data: "eve_type_id"
            },
            {
                name: "eve_type",
                target: [1],
                data: "eve_type"
            },
            {
                className: "right-column",
                name: "quantity",
                target: [2],
                data: 'quantity'
            },
            {
                name: "owner", target: [3], data: 'owner'
            },
            { name: "material_efficiency", target: [4], data: 'material_efficiency' },
            { name: "time_efficiency", target: [5], data: 'time_efficiency' },
            { name: "is_original", target: [6], data: 'is_original' },
            { name: "runs", target: [7], data: 'runs' },
            { name: "pk", target: [8], data: 'pk' },
            // hidden columns
            { name: "location", target: [9], data: 'location' },
            { name: "industryjob", target: [10], data: 'industryjob' },
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 2, 8] },
            { visible: false, targets: [9, 10,] },
            { searchable: false, targets: [0, 2, 3, 4, 5, 6, 7, 8, 9, 10] },
            {
                render: function (data, type, row) {
                    if (type === "display") {
                        return (
                            '<button class="btn btn-sm btn-info btn-square" ' +
                            'data-toggle="modal" ' +
                            'data-target="#modalViewBlueprintContainer" ' +
                            'data-ajax_url="' + viewBlueprintModalUrl + "?blueprint_id=" + data + '" ' +
                            'aria-label="' + viewBlueprintText + '" ' +
                            'title="' + viewBlueprintText + '">' +
                            '<span class="fas fa-info"></span>' +
                            '</button>'
                        );
                    }

                    return data;
                },
                targets: [8],
            },

        ],

        order: [
            [9, "asc"],
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 9,
                    title: blueprintsSettings.translation.filterLocation,
                },
                { idx: 4 },
                { idx: 5 },
                {
                    idx: 6,
                    title: blueprintsSettings.translation.filterIsOriginal,
                },
            ],
            ajax: listDataFddUrl,
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
        createdRow: function (row, data, dataIndex) {
            if (data.use === true) {
                $(row).addClass('info');
            }
        },
    });
});
