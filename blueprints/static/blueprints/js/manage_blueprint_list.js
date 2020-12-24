/* global blueprintsSettings */

$(document).ready(function () {
    "use strict";

    var listUserOwnerUrl = blueprintsSettings.listUserOwnerUrl;
    function removeOwnerUrl(id) {
        return blueprintsSettings.removeOwnerUrl.replace("12345",id);
    }
    var dataTablesPageLength = blueprintsSettings.dataTablesPageLength;
    var dataTablesPaging = blueprintsSettings.dataTablesPaging;
    var csrfToken = blueprintsSettings.csrfToken;
    var removeBlueprintsText = blueprintsSettings.translation.removeBlueprints;

    /* dataTable def */
    $("#table-manage-blueprints").DataTable({
        ajax: {
            url: listUserOwnerUrl,
            dataSrc: "",
            cache: false,
        },

        columns: [
            { data: "name" },
            {
                className: "right-column",
                data: "id",
            },
            // hidden columns,
            { data: "type" },
            { data: "type_display" },
        ],

        lengthMenu: [
            [10, 25, 50, 100, -1],
            [10, 25, 50, 100, "All"],
        ],

        paging: dataTablesPaging,

        pageLength: dataTablesPageLength,

        columnDefs: [
            { sortable: false, targets: [1] },
            { visible: false, targets: [2, 3] },
            {
                // The `data` parameter refers to the data for the cell (defined by the
                // `data` option, which defaults to the column being worked with, in
                // this case `data: 0`.
                render: function (data, type, row) {
                    if (type === "display") {
                        return '<form method="post" class="inline" action="' + removeOwnerUrl(data) + '">' +
                            csrfToken +
                            '<button type="submit" class="btn btn-danger btn-sm btn-square" aria-label="' + removeBlueprintsText + '" title="' + removeBlueprintsText  + '"><span class="fas fa-trash"></span></button></form>';
                    }

                    return data;
                },
                targets: [1],
            },
            {
                render: function (data, type, row) {
                    if (type === "display") {
                        var type_display = row.type_display;

                        if (row.type === "corporate") {
                            return '<span class="fas fa-briefcase" aria-label="' + type_display + '" title="' + type_display + '"></span> ' + data;
                        } else if (row.type === "personal") {
                            return '<span class="fas fa-user" aria-label="' + type_display + '" title="' + type_display + '"></span> ' + data;
                        } else {
                            return "";
                        }
                    }

                    return data;
                },
                targets: [0],
            }
        ],

        order: [
            [0, "asc"],
        ],
    });
});
