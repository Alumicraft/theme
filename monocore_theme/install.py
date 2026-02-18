import frappe


# Known icons for common ERPNext workspaces
KNOWN_ICONS = {
    "Home": "ph-house",
    "Projects": "ph-folder-simple",
    "Sales": "ph-arrow-up-right",
    "Purchases": "ph-shopping-cart",
    "Items": "ph-package",
    "Manufacturing": "ph-factory",
    "Customers": "ph-users",
    "Accounting": "ph-coins",
    "Users": "ph-user-plus",
    "Terminal": "ph-terminal-window",
    "Stock": "ph-warehouse",
    "Assets": "ph-buildings",
    "HR": "ph-identification-badge",
    "Payroll": "ph-money",
    "CRM": "ph-handshake",
    "Support": "ph-headset",
    "Quality": "ph-seal-check",
    "Website": "ph-globe",
    "Settings": "ph-gear",
}


def after_install():
    """Seed Monocore Theme Settings and clean up module workspace."""
    # Remove the auto-generated module workspace from the sidebar
    if frappe.db.exists("Workspace", "Monocore Theme"):
        frappe.delete_doc("Workspace", "Monocore Theme", ignore_permissions=True)
        frappe.db.commit()

    try:
        settings = frappe.get_single("Monocore Theme Settings")
    except Exception:
        # DocType may not have synced yet during migration
        return

    if not settings.workspace_icons:
        workspaces = frappe.get_all("Workspace", filters={"public": 1}, pluck="name")
        for ws in sorted(workspaces):
            settings.append("workspace_icons", {
                "workspace": ws,
                "icon_class": KNOWN_ICONS.get(ws, ""),
            })
        settings.flags.ignore_validate = True
        settings.save()
        frappe.db.commit()
