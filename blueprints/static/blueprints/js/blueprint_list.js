/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var listDataUrl = blueprintsSettings.listDataUrl;
    var createRequestUrl = blueprintsSettings.createRequestUrl;
    var createRequestModalUrl =
        blueprintsSettings.createRequestModalUrl;
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var csrfToken = blueprintsSettings.csrfToken;
    var canAddBlueprints = blueprintsSettings.canAddBlueprints;
    var createRequestText = blueprintsSettings.translation.createRequest;
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
                        if (row.og !== "" && canAddBlueprints && !row.nme.endsWith(" Formula")) {
                            return (
                                '<button class="btn btn-success" data-toggle="modal" data-target="#modalCreateRequestContainer" data-ajax_url="' +
                                createRequestModalUrl +
                                "?blueprint_id=" +
                                data +
                                '" aria-label="' + createRequestText + '" title="' + createRequestText + '"><span class="fas fa-copy"></span></button>'
                            );
                        } else {
                            return "";
                        }
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
