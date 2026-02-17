// Monocore Theme - Shortcut Group Block
// Workspace integration, add/edit dialog, and persistence

frappe.provide("monocore_theme");

// ─── Workspace Integration ──────────────────────────────────────────────────

$(document).on("page-change", function () {
    setTimeout(monocore_theme.loadShortcutGroups, 800);
    setTimeout(monocore_theme.loadShortcutGroups, 2000);
});

monocore_theme.loadShortcutGroups = function () {
    var route = frappe.get_route();
    if (!route) return;

    var workspaceName = null;
    if (route[0] === "Workspaces" && route.length > 1) {
        workspaceName = route.slice(1).join("/");
    }
    if (!workspaceName) return;

    // Already rendered for this workspace
    if ($('.shortcut-groups-container[data-workspace="' + workspaceName + '"]').length) {
        return;
    }

    frappe
        .xcall("monocore_theme.api.get_shortcut_groups", {
            workspace: workspaceName,
        })
        .then(function (groups) {
            if (!groups || !groups.length) return;

            // Already rendered (race condition guard)
            if ($('.shortcut-groups-container[data-workspace="' + workspaceName + '"]').length) {
                return;
            }

            // Find insertion point in workspace
            var $target = $(".workspace-main-section .widget-group").first();
            var $container = $(
                '<div class="shortcut-groups-container" data-workspace="' + workspaceName + '">'
            );

            if ($target.length) {
                $target.before($container);
            } else {
                $(".workspace-main-section").prepend($container);
            }

            for (var i = 0; i < groups.length; i++) {
                new monocore_theme.ShortcutGroupRenderer(groups[i], $container);
            }
        })
        .catch(function () {
            // Silently fail — DocType may not exist yet after fresh install
        });
};

// ─── Refresh helper ─────────────────────────────────────────────────────────

monocore_theme._refreshShortcutGroups = function () {
    $(".shortcut-groups-container").remove();
    setTimeout(monocore_theme.loadShortcutGroups, 300);
};

// ─── Edit / Add entry points ────────────────────────────────────────────────

monocore_theme.editShortcutGroup = function (name) {
    frappe
        .xcall("frappe.client.get", {
            doctype: "Shortcut Group",
            name: name,
        })
        .then(function (doc) {
            monocore_theme.showShortcutGroupDialog(doc.workspace, doc);
        });
};

monocore_theme.addShortcutGroup = function (workspace) {
    monocore_theme.showShortcutGroupDialog(workspace, null);
};

// ─── Dialog ─────────────────────────────────────────────────────────────────

monocore_theme.showShortcutGroupDialog = function (workspace, existingDoc) {
    var isEdit = !!existingDoc;
    var links = [];

    if (existingDoc && existingDoc.links) {
        for (var i = 0; i < existingDoc.links.length; i++) {
            var l = existingDoc.links[i];
            links.push({
                label: l.label || "",
                link_to: l.link_to || "",
                doctype_view: l.doctype_view || "List",
                color: l.color || "Grey",
                filters_json: l.filters_json || "",
            });
        }
    }

    if (!links.length) {
        links.push({
            label: "",
            link_to: "",
            doctype_view: "List",
            color: "Grey",
            filters_json: "",
        });
    }

    var d = new frappe.ui.Dialog({
        title: isEdit ? __("Edit Shortcut Group") : __("Add Shortcut Group"),
        size: "large",
        fields: [
            {
                fieldname: "label",
                fieldtype: "Data",
                label: __("Group Title"),
                reqd: 1,
                default: existingDoc ? existingDoc.label : "",
            },
            {
                fieldname: "links_section",
                fieldtype: "Section Break",
                label: __("Shortcuts"),
            },
            {
                fieldname: "links_html",
                fieldtype: "HTML",
            },
        ],
        primary_action_label: isEdit ? __("Update") : __("Add"),
        primary_action: function (values) {
            var rows = monocore_theme._collectDialogRows(d);
            if (!rows.length) {
                frappe.msgprint(__("Add at least one shortcut."));
                return;
            }

            var payload = {
                label: values.label,
                workspace: workspace,
                links: rows,
            };
            if (isEdit) {
                payload.name = existingDoc.name;
            }

            frappe
                .xcall("monocore_theme.api.save_shortcut_group", {
                    data: payload,
                })
                .then(function () {
                    d.hide();
                    frappe.show_alert({
                        message: isEdit ? __("Updated") : __("Added"),
                        indicator: "green",
                    });
                    monocore_theme._refreshShortcutGroups();
                })
                .catch(function (err) {
                    frappe.msgprint(__("Error: {0}", [err.message || err]));
                });
        },
    });

    d.show();

    // Render shortcut rows inside the dialog
    var $wrapper = d.fields_dict.links_html.$wrapper;
    $wrapper.empty();
    monocore_theme._renderDialogRows($wrapper, links);
};

// ─── Dialog row helpers ─────────────────────────────────────────────────────

monocore_theme._renderDialogRows = function ($wrapper, links) {
    var $rows = $('<div class="sg-dialog-rows">');
    $wrapper.append($rows);

    for (var i = 0; i < links.length; i++) {
        monocore_theme._addDialogRow($rows, links[i]);
    }

    var $addBtn = $(
        '<button class="btn btn-sm btn-default mt-3">' + __("+ Add Shortcut") + "</button>"
    );
    $addBtn.on("click", function () {
        monocore_theme._addDialogRow($rows, {
            label: "",
            link_to: "",
            doctype_view: "List",
            color: "Grey",
            filters_json: "",
        });
    });
    $wrapper.append($addBtn);
};

monocore_theme._addDialogRow = function ($container, link) {
    var viewOptions = ["List", "Report Builder", "Dashboard", "New"];
    var colorOptions = ["Grey", "Green", "Red", "Orange", "Pink", "Yellow", "Blue", "Cyan"];

    var viewSelect = "";
    for (var i = 0; i < viewOptions.length; i++) {
        var sel = link.doctype_view === viewOptions[i] ? " selected" : "";
        viewSelect += "<option" + sel + ">" + viewOptions[i] + "</option>";
    }

    var colorSelect = "";
    for (var j = 0; j < colorOptions.length; j++) {
        var sel2 = link.color === colorOptions[j] ? " selected" : "";
        colorSelect += "<option" + sel2 + ">" + colorOptions[j] + "</option>";
    }

    var $row = $(
        '<div class="sg-dialog-row">' +
            '<div class="row">' +
                '<div class="col-md-5">' +
                    '<label class="control-label">' + __("Label") + "</label>" +
                    '<input type="text" class="form-control form-control-sm sg-input-label" ' +
                        'value="' + frappe.utils.escape_html(link.label) + '" ' +
                        'placeholder="e.g. Open Quotes">' +
                "</div>" +
                '<div class="col-md-5">' +
                    '<label class="control-label">' + __("Link To (DocType)") + "</label>" +
                    '<input type="text" class="form-control form-control-sm sg-input-link-to" ' +
                        'value="' + frappe.utils.escape_html(link.link_to) + '" ' +
                        'placeholder="e.g. Quotation">' +
                "</div>" +
                '<div class="col-md-2 d-flex align-items-end">' +
                    '<button class="btn btn-xs btn-danger sg-remove-row">' + __("Remove") + "</button>" +
                "</div>" +
            "</div>" +
            '<div class="row mt-2">' +
                '<div class="col-md-3">' +
                    '<label class="control-label">' + __("View") + "</label>" +
                    '<select class="form-control form-control-sm sg-input-view">' + viewSelect + "</select>" +
                "</div>" +
                '<div class="col-md-3">' +
                    '<label class="control-label">' + __("Badge Color") + "</label>" +
                    '<select class="form-control form-control-sm sg-input-color">' + colorSelect + "</select>" +
                "</div>" +
                '<div class="col-md-6">' +
                    '<label class="control-label">' + __("Filters JSON") + "</label>" +
                    '<input type="text" class="form-control form-control-sm sg-input-filters" ' +
                        "value='" + frappe.utils.escape_html(link.filters_json || "") + "' " +
                        'placeholder=\'{"status":"Open"}\'>' +
                "</div>" +
            "</div>" +
        "</div>"
    );

    $row.find(".sg-remove-row").on("click", function () {
        $row.fadeOut(200, function () {
            $row.remove();
        });
    });

    $container.append($row);
};

monocore_theme._collectDialogRows = function (dialog) {
    var rows = [];
    dialog.$wrapper.find(".sg-dialog-row").each(function () {
        var $r = $(this);
        var label = $r.find(".sg-input-label").val().trim();
        var linkTo = $r.find(".sg-input-link-to").val().trim();

        if (!label || !linkTo) return;

        rows.push({
            label: label,
            link_to: linkTo,
            doctype_view: $r.find(".sg-input-view").val(),
            color: $r.find(".sg-input-color").val(),
            filters_json: $r.find(".sg-input-filters").val().trim() || "{}",
        });
    });
    return rows;
};
