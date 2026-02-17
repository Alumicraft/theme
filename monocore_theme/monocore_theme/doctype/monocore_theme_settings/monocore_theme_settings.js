frappe.ui.form.on("Monocore Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Sync Workspaces"), () => {
            frappe.call({
                method: "monocore_theme.api.sync_workspace_icons",
                freeze: true,
                freeze_message: __("Syncing workspaces..."),
                callback() {
                    frm.reload_doc();
                },
            });
        });
    },
});
