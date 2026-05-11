import frappe


def execute():
    """Delete the Backdesk workspace from the sidebar."""
    if frappe.db.exists("Workspace", "Backdesk"):
        frappe.delete_doc("Workspace", "Backdesk", ignore_permissions=True)
        frappe.db.commit()
