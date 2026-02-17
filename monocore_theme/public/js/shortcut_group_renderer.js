// Monocore Theme - Shortcut Group Renderer
// Renders a shortcut group card with badge counts and navigation

frappe.provide("monocore_theme");

monocore_theme.ShortcutGroupRenderer = class {
    constructor(config, container) {
        this.config = config;
        this.$container = $(container);
        this.render();
    }

    render() {
        var self = this;
        var name = frappe.utils.escape_html(this.config.name || "");
        var label = frappe.utils.escape_html(this.config.label || "");

        this.$card = $('<div class="shortcut-group-block" data-name="' + name + '">');

        // Edit / Delete buttons (top-right, visible on hover)
        this.$card.append(
            '<div class="sg-edit-actions">' +
                '<button class="btn-action sg-edit-btn" title="Edit">' +
                    '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M8.5 1.5l2 2-6.5 6.5H2V8l6.5-6.5z" stroke="currentColor" fill="none" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
                '</button>' +
                '<button class="btn-action sg-delete-btn" title="Delete">' +
                    '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 3l6 6M9 3l3 9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>' +
                '</button>' +
            '</div>'
        );

        // Header
        this.$card.append('<div class="sg-header">' + label + '</div>');

        // Rows
        var links = this.config.links || [];
        for (var i = 0; i < links.length; i++) {
            this.renderRow(links[i]);
        }

        // Wire up edit/delete
        this.$card.find(".sg-edit-btn").on("click", function (e) {
            e.stopPropagation();
            monocore_theme.editShortcutGroup(self.config.name);
        });

        this.$card.find(".sg-delete-btn").on("click", function (e) {
            e.stopPropagation();
            frappe.confirm(
                __('Delete shortcut group "{0}"?', [self.config.label]),
                function () {
                    frappe.xcall("monocore_theme.api.delete_shortcut_group", {
                        name: self.config.name,
                    }).then(function () {
                        self.$card.fadeOut(200, function () {
                            self.$card.remove();
                        });
                        frappe.show_alert({ message: __("Deleted"), indicator: "green" });
                    });
                }
            );
        });

        this.$container.append(this.$card);
    }

    renderRow(link) {
        var badgeColor = (link.color || "grey").toLowerCase();
        var label = frappe.utils.escape_html(link.label || "");

        var $row = $(
            '<div class="sg-row">' +
                '<span class="sg-row-label">' + label + '</span>' +
                '<span class="sg-row-arrow">' +
                    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none">' +
                        '<path d="M4 10L10 4M10 4H5.5M10 4V8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>' +
                    '</svg>' +
                '</span>' +
                '<span class="sg-row-badge sg-badge-' + badgeColor + '">-</span>' +
            '</div>'
        );

        // Click → navigate to filtered view
        $row.on("click", function () {
            var filters = {};
            try {
                if (link.filters_json) {
                    filters = JSON.parse(link.filters_json);
                }
            } catch (e) {
                filters = {};
            }

            if (link.doctype_view === "New") {
                frappe.new_doc(link.link_to);
                return;
            }

            frappe.route_options = filters;

            if (link.doctype_view === "Report Builder") {
                frappe.set_route("List", link.link_to, "Report");
            } else if (link.doctype_view === "Dashboard") {
                frappe.set_route("List", link.link_to, "Dashboard");
            } else {
                frappe.set_route("List", link.link_to);
            }
        });

        this.$card.append($row);

        // Fetch badge count
        if (link.doctype_view !== "New" && link.link_to) {
            var filters = {};
            try {
                if (link.filters_json) {
                    filters = JSON.parse(link.filters_json);
                }
            } catch (e) {
                /* ignore */
            }

            frappe
                .xcall("frappe.client.get_count", {
                    doctype: link.link_to,
                    filters: filters,
                })
                .then(function (count) {
                    var text = count || 0;
                    if (link.format) {
                        text = link.format.replace("{}", text);
                    }
                    $row.find(".sg-row-badge").text(text);
                })
                .catch(function () {
                    $row.find(".sg-row-badge").text("\u2014");
                });
        } else {
            $row.find(".sg-row-badge").hide();
        }
    }
};
