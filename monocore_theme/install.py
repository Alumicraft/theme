import frappe


HIDDEN_WORKSPACES = ["Buying", "Selling"]


def after_install():
    """Seed Monocore Theme Settings and clean up module workspace."""
    # Remove the auto-generated module workspace from the sidebar
    if frappe.db.exists("Workspace", "Monocore Theme"):
        frappe.delete_doc("Workspace", "Monocore Theme", ignore_permissions=True)
        frappe.db.commit()

    # Hide workspaces that have been replaced by custom ones (e.g. Buying -> Sales)
    for ws in HIDDEN_WORKSPACES:
        if frappe.db.exists("Workspace", ws):
            frappe.db.set_value("Workspace", ws, "public", 0)
    frappe.db.commit()
