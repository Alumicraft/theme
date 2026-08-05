import json

import frappe

from backdesk.patches.v0_0_2.repair_workspace_sidebar import OVERVIEW_CONTENT


OLD_EMPLOYEE_LABEL = """CONCAT(
    SUBSTRING_INDEX(e.employee_name, ' ', -1),
    ', ',
    SUBSTRING_INDEX(e.employee_name, ' ', 1)
  ) AS `Employee`"""

NEW_EMPLOYEE_LABEL = """CONCAT_WS(
    ', ',
    NULLIF(e.last_name, ''),
    NULLIF(e.first_name, '')
  ) AS `Employee`"""


def execute():
    repair_overview_content()
    repair_weekly_time_employee_names()


def repair_overview_content():
    if not frappe.db.exists("Workspace", "Overview"):
        return

    doc = frappe.get_doc("Workspace", "Overview")
    try:
        content = json.loads(doc.content or "[]")
    except (TypeError, ValueError):
        content = []

    ids = {block.get("id") for block in content if isinstance(block, dict)}
    required_ids = {block["id"] for block in OVERVIEW_CONTENT}
    if required_ids.issubset(ids):
        return

    doc.content = json.dumps(OVERVIEW_CONTENT, separators=(",", ":"))
    doc.save(ignore_permissions=True)


def repair_weekly_time_employee_names():
    name = "Weekly Time by Person"
    if not frappe.db.exists("Report", name):
        return

    doc = frappe.get_doc("Report", name)
    query = doc.query or ""
    updated = query.replace(OLD_EMPLOYEE_LABEL, NEW_EMPLOYEE_LABEL)
    updated = updated.replace(
        "e.name, e.employee_name",
        "e.name, e.last_name, e.first_name",
    )
    updated = updated.replace(
        "SUBSTRING_INDEX(e.employee_name, ' ', -1),\n  SUBSTRING_INDEX(e.employee_name, ' ', 1)",
        "e.last_name,\n  e.first_name",
    )

    if updated == query:
        return

    # This legacy report contains client-side JavaScript in its ``script``
    # field. Frappe 16 validates that field as Python when the full document is
    # saved, even though this patch only changes the SQL query. Update the
    # query directly so the unrelated legacy script cannot block migration.
    frappe.db.set_value("Report", name, "query", updated, update_modified=True)
