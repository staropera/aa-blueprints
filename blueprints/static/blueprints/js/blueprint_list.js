/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var listDataUrl = blueprintsSettings.listDataUrl;
    var viewBlueprintModalUrl = blueprintsSettings.viewBlueprintModalUrl;
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var viewBlueprintText = blueprintsSettings.translation.viewBlueprint;

    /* dataTable def */
    $("#table-blueprints").DataTable({
        ajax: {
            url: listDataUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "icn" },
            { data: "nme" },
            {
                className: "right-column",
                data: "qty",
            },
            { data: "on" },
            { data: "me" },
            { data: "te" },
            { data: "og" },
            { data: "rns" },
            { data: "pk" },
            // hidden columns
            { data: "loc" },
            { data: "iog" },
            { data: "use" }
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [0, 2, 8] },
            { visible: false, targets: [9, 10, 11] },
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
            {
                render: function (data, type, row) {
                    if (type === "display") {
                        if (row.ot === "corporation") {
                            return '<span class="fas fa-briefcase"></span> ' + data;
                        } else if (row.ot === "character") {
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
            [9, "asc"],
            [1, "asc"],
        ],

        filterDropDown: {
            columns: [
                {
                    idx: 9,
                    title:
                        blueprintsSettings.translation.filterLocation,
                },
                { idx: 3 },
                { idx: 4 },
                { idx: 5 },
                {
                    idx: 10,
                    title:
                        blueprintsSettings.translation
                            .filterIsOriginal,
                },
            ],
            autoSize: false,
            bootstrap: true,
        },

        drawCallback: function(settings) {
            var api = this.api();
            var rows = api.rows({ page: "current" }).nodes();
            var last = null;

            api.column(9, { page: "current" })
                .data()
                .each(function(group, i) {
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
        createdRow: function( row, data, dataIndex ) {
            if (data.use === true) {
                $(row).addClass('info');
            }
        },
    });
});
