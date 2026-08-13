import frappe


REPORT_NAME = "Project Profitability"


def execute():
    if not frappe.db.exists("Workspace Sidebar", "Jobs"):
        return

    sidebar = frappe.get_doc("Workspace Sidebar", "Jobs")
    if any(
        row.link_type == "Report" and row.link_to == REPORT_NAME
        for row in sidebar.items
    ):
        return

    sidebar.append(
        "items",
        {
            "label": REPORT_NAME,
            "link_type": "Report",
            "link_to": REPORT_NAME,
            "type": "Link",
        },
    )
    sidebar.save(ignore_permissions=True)
