import json

import frappe
from frappe.utils import nowdate


WORST_PROJECTS_QUERY = """SELECT
  p.name AS "Project",
  p.project_name AS "Project Name",
  p.customer AS "Customer",
  p.project_type AS "Project Type",
  ROUND(COALESCE(gl.recognized_revenue, 0), 2) AS "Recognized Revenue:Currency:130",
  ROUND(COALESCE(gl.gl_expense, 0), 2) AS "GL Expense:Currency:120",
  ROUND(
    COALESCE(p.total_costing_amount, 0)
    + COALESCE(p.total_purchase_cost, 0)
    + COALESCE(p.total_consumed_material_cost, 0),
    2
  ) AS "Project Cost Rollup:Currency:130",
  ROUND(
    GREATEST(
      COALESCE(gl.gl_expense, 0),
      COALESCE(p.total_costing_amount, 0)
      + COALESCE(p.total_purchase_cost, 0)
      + COALESCE(p.total_consumed_material_cost, 0)
    ),
    2
  ) AS "Recognized Cost:Currency:130",
  ROUND(
    COALESCE(gl.recognized_revenue, 0)
    - GREATEST(
      COALESCE(gl.gl_expense, 0),
      COALESCE(p.total_costing_amount, 0)
      + COALESCE(p.total_purchase_cost, 0)
      + COALESCE(p.total_consumed_material_cost, 0)
    ),
    2
  ) AS "Recognized Gross Margin:Currency:150"
FROM `tabProject` p
LEFT JOIN (
  SELECT
    gle.project,
    SUM(
      CASE WHEN account.root_type = 'Income'
        THEN gle.credit - gle.debit ELSE 0 END
    ) AS recognized_revenue,
    SUM(
      CASE WHEN account.root_type = 'Expense'
        THEN gle.debit - gle.credit ELSE 0 END
    ) AS gl_expense
  FROM `tabGL Entry` gle
  INNER JOIN `tabAccount` account ON account.name = gle.account
  WHERE gle.is_cancelled = 0
    AND IFNULL(gle.project, '') != ''
  GROUP BY gle.project
) gl ON gl.project = p.name
WHERE p.status = 'Open'
  AND p.name NOT IN ('INVENTORY', 'SHOP')
  AND (
    COALESCE(gl.recognized_revenue, 0) != 0
    OR COALESCE(gl.gl_expense, 0) != 0
    OR COALESCE(p.total_costing_amount, 0) != 0
    OR COALESCE(p.total_purchase_cost, 0) != 0
    OR COALESCE(p.total_consumed_material_cost, 0) != 0
  )
ORDER BY (
  COALESCE(gl.recognized_revenue, 0)
  - GREATEST(
    COALESCE(gl.gl_expense, 0),
    COALESCE(p.total_costing_amount, 0)
    + COALESCE(p.total_purchase_cost, 0)
    + COALESCE(p.total_consumed_material_cost, 0)
  )
) ASC
LIMIT 10"""


def execute():
    repair_profit_and_loss_charts()
    repair_worst_projects_report()
    repair_worst_projects_chart()


def repair_profit_and_loss_charts():
    old_name = "Profit and Loss"
    new_name = "Profit and Loss New"
    if not frappe.db.exists("Dashboard Chart", new_name):
        return

    current = frappe.db.get_value(
        "Dashboard Chart",
        new_name,
        ["filters_json", "type", "time_interval", "currency", "show_values_over_chart"],
        as_dict=True,
    )
    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ["<=", nowdate()],
            "year_end_date": [">=", nowdate()],
        },
        "name",
    )
    company = (
        frappe.defaults.get_global_default("company")
        or frappe.db.get_value("Company", {"company_name": "Alumicraft"}, "name")
    )
    if fiscal_year:
        current.filters_json = json.dumps(
            {
                "company": company,
                "filter_based_on": "Fiscal Year",
                "from_fiscal_year": fiscal_year,
                "to_fiscal_year": fiscal_year,
                "periodicity": "Quarterly",
                "presentation_currency": "USD",
                "show_account_details": "Summary",
                "selected_view": "Report",
                "accumulated_values": 0,
                "include_default_book_entries": 1,
                "show_zero_values": 0,
            },
            separators=(",", ":"),
        )
        frappe.db.set_value(
            "Dashboard Chart",
            new_name,
            current,
            update_modified=True,
        )
    if frappe.db.exists("Dashboard Chart", old_name):
        frappe.db.set_value(
            "Dashboard Chart",
            old_name,
            current,
            update_modified=True,
        )

    for row in frappe.get_all(
        "Workspace Chart",
        filters={"chart_name": old_name},
        fields=["name"],
    ):
        frappe.db.set_value(
            "Workspace Chart",
            row.name,
            "chart_name",
            new_name,
            update_modified=False,
        )

    for workspace in frappe.get_all("Workspace", fields=["name", "content"]):
        try:
            content = json.loads(workspace.content or "[]")
        except (TypeError, ValueError):
            continue
        changed = False
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "chart":
                continue
            data = block.get("data") or {}
            if data.get("chart_name") == old_name:
                data["chart_name"] = new_name
                changed = True
        if changed:
            frappe.db.set_value(
                "Workspace",
                workspace.name,
                "content",
                json.dumps(content, separators=(",", ":")),
                update_modified=True,
            )


def repair_worst_projects_report():
    report_name = "Worst Performing Projects by Gross Margin $"
    if not frappe.db.exists("Report", report_name):
        return
    frappe.db.set_value(
        "Report",
        report_name,
        "query",
        WORST_PROJECTS_QUERY,
        update_modified=True,
    )


def repair_worst_projects_chart():
    chart_name = "Worst Performing Projects by Gross Margin $"
    if not frappe.db.exists("Dashboard Chart", chart_name):
        return

    doc = frappe.get_doc("Dashboard Chart", chart_name)
    expected_axis = [("recognized_gross_margin", "#C97A40")]
    current_axis = [(row.y_field, row.color) for row in doc.y_axis]

    changed = False
    if doc.x_field != "project":
        doc.x_field = "project"
        changed = True
    if current_axis != expected_axis:
        doc.set("y_axis", [])
        for y_field, color in expected_axis:
            doc.append("y_axis", {"y_field": y_field, "color": color})
        changed = True
    if not doc.show_values_over_chart:
        doc.show_values_over_chart = 1
        changed = True
    if doc.currency != "USD":
        doc.currency = "USD"
        changed = True

    if changed:
        doc.save(ignore_permissions=True)
