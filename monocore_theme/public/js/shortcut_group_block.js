// Monocore Theme - Shortcut Group Block
// EditorJS tool + workspace integration + dialog

frappe.provide("monocore_theme");

// ─── EditorJS Tool Class ────────────────────────────────────────────────────

monocore_theme.ShortcutGroupTool = class {
    static get toolbox() {
        return {
            title: "Shortcut Group",
            icon: '<svg width="17" height="15" viewBox="0 0 17 15" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="0.5" y="0.5" width="16" height="3.5" rx="1"/><rect x="0.5" y="5.75" width="16" height="3.5" rx="1"/><rect x="0.5" y="11" width="16" height="3.5" rx="1"/></svg>',
        };
    }

    static get isReadOnlySupported() {
        return true;
    }

    constructor({ data, api, readOnly }) {
        this.data = data || {};
        this.api = api;
        this.readOnly = readOnly;
        this.wrapper = null;
    }

    render() {
        this.wrapper = document.createElement("div");
        this.wrapper.classList.add("shortcut-group-editor-block");

        if (this.data.shortcut_group_name) {
            this._loadAndRender();
        } else if (!this.readOnly) {
            this._promptCreate();
        }

        return this.wrapper;
    }

    save() {
        return {
            shortcut_group_name: this.data.shortcut_group_name || "",
        };
    }

    _loadAndRender() {
        var self = this;
        frappe
            .xcall("frappe.client.get", {
                doctype: "Shortcut Group",
                name: this.data.shortcut_group_name,
            })
            .then(function (doc) {
                self.wrapper.innerHTML = "";
                new monocore_theme.ShortcutGroupRenderer(
                    {
                        name: doc.name,
                        label: doc.label,
                        links: (doc.links || []).map(function (l) {
                            return {
                                label: l.label,
                                link_to: l.link_to,
                                doctype_view: l.doctype_view || "List",
                                color: l.color || "Grey",
                                format: l.format || "",
                                filters_json: l.filters_json || "{}",
                            };
                        }),
                    },
                    self.wrapper
                );
            })
            .catch(function () {
                self.wrapper.innerHTML =
                    '<div style="padding:1rem;color:var(--text-muted);">Shortcut Group not found</div>';
            });
    }

    _promptCreate() {
        var self = this;
        var route = frappe.get_route();
        var workspace = route && route.length > 1 ? route.slice(1).join("/") : "";

        monocore_theme.showShortcutGroupDialog(workspace, null, function (name) {
            self.data.shortcut_group_name = name;
            self._loadAndRender();
        });
    }
};

// ─── Patch Workspace editor to register our tool ────────────────────────────
// Frappe v15 hardcodes the EditorJS tools list in initialize_editorjs().
// EditorJS is imported as a module so window.EditorJS patching doesn't work.
// Instead, we override initialize_editorjs to inject our tool before the
// EditorJS instance is created.

(function () {
    function patchWorkspace() {
        if (!frappe.views || !frappe.views.Workspace) return false;
        var proto = frappe.views.Workspace.prototype;
        if (proto._sgPatched) return true;

        var origInit = proto.initialize_editorjs;
        proto.initialize_editorjs = function (blocks) {
            var self = this;

            // Intercept the this.tools assignment via a property setter.
            // When the original code does `this.tools = { ... }`, our setter
            // injects shortcut_group before EditorJS reads the object.
            Object.defineProperty(this, "tools", {
                set: function (val) {
                    val.shortcut_group = {
                        class: monocore_theme.ShortcutGroupTool,
                        config: { page_data: self.page_data || [] },
                    };
                    // Store on a backing field
                    Object.defineProperty(self, "tools", {
                        value: val,
                        writable: true,
                        configurable: true,
                    });
                },
                get: function () {
                    return undefined;
                },
                configurable: true,
            });

            // Call original — it sets this.tools (triggering our setter)
            // then creates the EditorJS instance with the augmented tools
            origInit.call(this, blocks);
        };

        // Also patch prepare_editorjs so our tool's page_data stays current
        // on subsequent workspace navigations
        var origPrepare = proto.prepare_editorjs;
        proto.prepare_editorjs = function () {
            var self = this;
            if (this.editor) {
                this.editor.isReady.then(function () {
                    if (
                        self.editor.configuration &&
                        self.editor.configuration.tools &&
                        self.editor.configuration.tools.shortcut_group
                    ) {
                        self.editor.configuration.tools.shortcut_group.config.page_data =
                            self.page_data;
                    }
                });
            }
            origPrepare.call(this);
        };

        proto._sgPatched = true;
        return true;
    }

    if (!patchWorkspace()) {
        var iv = setInterval(function () {
            if (patchWorkspace()) clearInterval(iv);
        }, 200);
        setTimeout(function () {
            clearInterval(iv);
        }, 30000);
    }
})();

// ─── Also render saved groups on workspace view (non-edit) ──────────────────

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

    // Skip if already rendered or if editor blocks handle it
    if ($('.shortcut-groups-container[data-workspace="' + workspaceName + '"]').length) return;
    if ($(".shortcut-group-editor-block").length) return;

    frappe
        .xcall("monocore_theme.api.get_shortcut_groups", {
            workspace: workspaceName,
        })
        .then(function (groups) {
            if (!groups || !groups.length) return;
            if ($('.shortcut-groups-container[data-workspace="' + workspaceName + '"]').length) return;
            if ($(".shortcut-group-editor-block").length) return;

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
        .catch(function () {});
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

monocore_theme.showShortcutGroupDialog = function (workspace, existingDoc, callback) {
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
                .then(function (name) {
                    d.hide();
                    frappe.show_alert({
                        message: isEdit ? __("Updated") : __("Added"),
                        indicator: "green",
                    });
                    monocore_theme._refreshShortcutGroups();

                    // Notify EditorJS block if created via the block tool
                    if (callback) callback(name);
                })
                .catch(function (err) {
                    frappe.msgprint(__("Error: {0}", [err.message || err]));
                });
        },
    });

    d.show();

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
