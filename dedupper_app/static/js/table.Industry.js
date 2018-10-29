/*
 * Editor client script for DB table Industry
 * Created by http://editor.datatables.net/generator
 */

(function ($) {

    $(document).ready(function () {
        var editor = new $.fn.dataTable.Editor({
            ajax: '/industry/',
            table: '#Industry',
            fields: [
                {
                    "label": "Title:",
                    "name": "title"
                },
                {
                    "label": "Link:",
                    "name": "link"
                },
                {
                    "label": "Description:",
                    "name": "description",
                    "type": "textarea"
                },
                {
                    "label": "Created On:",
                    "name": "created_on",
                    "type": "datetime",
                    "format": "YYYY-MM-DD HH:mm:ss"
                },
                {
                    "label": "Archived:",
                    "name": "archived",
                    "type": "radio",
                    "options": [
                        "True",
                        " False"
                    ]
                }
            ]
        });

        new $.fn.dataTable.Buttons(table, [
            {extend: "create", editor: editor},
            {extend: "edit", editor: editor},
            {extend: "remove", editor: editor}
        ]);

        table.buttons().container()
            .appendTo($('.col-md-6:eq(0)', table.table().container()));
    });

}(jQuery));

