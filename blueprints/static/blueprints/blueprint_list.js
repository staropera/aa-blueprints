$(document).ready(function () {
  /* retrieve generated data from HTML page */
  var elem = document.getElementById("dataExport");
  var listDataUrl = elem.getAttribute("data-listDataUrl");
  var titleAlliance = elem.getAttribute("data-titleAlliance");
  var titleCorporation = elem.getAttribute("data-titleCorporation");
  var titleRegion = elem.getAttribute("data-titleRegion");
  var titleSolarSystem = elem.getAttribute("data-titleSolarSystem");
  var titleCategory = elem.getAttribute("data-titleCategory");
  var titleGroup = elem.getAttribute("data-titleGroup");
  var Reinforced = elem.getAttribute("data-Reinforced");
  var State = elem.getAttribute("data-State");
  var PowerMode = elem.getAttribute("data-PowerMode");
  var dataTablesPageLength = elem.getAttribute("data-dataTablesPageLength");
  var dataTablesPaging = elem.getAttribute("data-dataTablesPaging") == "True";

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
