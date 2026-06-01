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

    make_payment_request_status_filterable()


def make_payment_request_status_filterable():
    """Allow route/list filters to exclude paid Payment Requests by status."""
    if not frappe.db.exists("DocType", "Payment Request"):
        return
    if not frappe.db.exists(
        "DocField",
        {
            "parent": "Payment Request",
            "fieldname": "status",
        },
    ):
        return

    name = "Payment Request-status-in_standard_filter"
    values = {
        "doctype_or_field": "DocField",
        "doc_type": "Payment Request",
        "field_name": "status",
        "property": "in_standard_filter",
        "property_type": "Check",
        "value": "1",
    }

    filters = {
        "doctype_or_field": "DocField",
        "doc_type": "Payment Request",
        "field_name": "status",
        "property": "in_standard_filter",
    }
    existing = frappe.db.exists("Property Setter", filters)
    if existing:
        doc = frappe.get_doc("Property Setter", existing)
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Property Setter",
                "name": name,
                **values,
            }
        )
        doc.insert(ignore_permissions=True)

    frappe.clear_cache(doctype="Payment Request")
    frappe.db.commit()
