import frappe


def execute():
    """Delete the Monocore Theme workspace from the sidebar."""
    if frappe.db.exists("Workspace", "Monocore Theme"):
        frappe.delete_doc("Workspace", "Monocore Theme", ignore_permissions=True)
        frappe.db.commit()
