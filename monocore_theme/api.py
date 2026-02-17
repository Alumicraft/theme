import frappe
import json


@frappe.whitelist()
def get_shortcut_groups(workspace):
    """Get all shortcut groups for a workspace with their items."""
    groups = frappe.get_all(
        "Shortcut Group",
        filters={"workspace": workspace},
        fields=["name", "label"],
        order_by="creation asc",
    )

    for group in groups:
        group["links"] = frappe.get_all(
            "Shortcut Group Item",
            filters={"parent": group["name"]},
            fields=["label", "link_to", "doctype_view", "color", "format", "filters_json"],
            order_by="idx asc",
        )

    return groups


@frappe.whitelist()
def save_shortcut_group(data):
    """Create or update a shortcut group."""
    if isinstance(data, str):
        data = json.loads(data)

    if data.get("name"):
        doc = frappe.get_doc("Shortcut Group", data["name"])
        doc.label = data["label"]
        doc.workspace = data["workspace"]
        doc.set("links", [])
        for link in data.get("links", []):
            doc.append("links", {
                "label": link["label"],
                "link_to": link["link_to"],
                "doctype_view": link.get("doctype_view", "List"),
                "color": link.get("color", "Grey"),
                "format": link.get("format", ""),
                "filters_json": link.get("filters_json", "{}"),
            })
        doc.save()
    else:
        doc = frappe.get_doc({
            "doctype": "Shortcut Group",
            "label": data["label"],
            "workspace": data["workspace"],
            "links": [
                {
                    "doctype": "Shortcut Group Item",
                    "label": link["label"],
                    "link_to": link["link_to"],
                    "doctype_view": link.get("doctype_view", "List"),
                    "color": link.get("color", "Grey"),
                    "format": link.get("format", ""),
                    "filters_json": link.get("filters_json", "{}"),
                }
                for link in data.get("links", [])
            ],
        })
        doc.insert()

    frappe.db.commit()
    return doc.name


@frappe.whitelist()
def delete_shortcut_group(name):
    """Delete a shortcut group."""
    frappe.delete_doc("Shortcut Group", name)
    frappe.db.commit()
    return "ok"


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
