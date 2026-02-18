import frappe


@frappe.whitelist()
def sync_workspace_icons():
    """Sync the Workspace Icons table with current public workspaces."""
    from monocore_theme.install import KNOWN_ICONS

    settings = frappe.get_single("Monocore Theme Settings")

    site_workspaces = set(
        frappe.get_all("Workspace", filters={"public": 1}, pluck="name")
    )

    existing = {}
    for row in settings.workspace_icons:
        existing[row.workspace] = row.icon_class

    settings.workspace_icons = []
    for ws in sorted(site_workspaces):
        settings.append("workspace_icons", {
            "workspace": ws,
            "icon_class": existing.get(ws, "") or KNOWN_ICONS.get(ws, ""),
        })

    settings.save()
    frappe.db.commit()
    return "ok"


@frappe.whitelist(allow_guest=False)
def get_workspace_icons():
    """Return the workspace → icon class map from Monocore Theme Settings."""
    icons = frappe.get_all(
        "Workspace Icon",
        filters={"parent": "Monocore Theme Settings"},
        fields=["workspace", "icon_class"],
        order_by="idx asc",
    )
    return {row["workspace"]: row["icon_class"] for row in icons}
