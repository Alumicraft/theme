import frappe


HIDDEN_WORKSPACES = ["Buying", "Selling"]


def after_install():
    """Remove the auto-generated app workspace and hide replaced workspaces."""
    # Remove the auto-generated module workspace from the sidebar
    if frappe.db.exists("Workspace", "Backdesk"):
        frappe.delete_doc("Workspace", "Backdesk", ignore_permissions=True)
        frappe.db.commit()

    # Hide workspaces that have been replaced by custom ones (e.g. Buying -> Sales)
    for ws in HIDDEN_WORKSPACES:
        if frappe.db.exists("Workspace", ws):
            frappe.db.set_value("Workspace", ws, "public", 0)
    frappe.db.commit()
