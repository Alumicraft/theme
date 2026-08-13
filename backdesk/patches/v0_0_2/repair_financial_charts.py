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


QUARTERLY_PROFIT_AND_LOSS_REPORT = "Quarterly Profit and Loss Dashboard"

# Match the default series order and colors shipped by Frappe Charts.
FRAPPE_CHART_COLORS = {
    "pink": "#F683AE",
    "blue": "#318AD8",
    "green": "#48BB74",
}

QUARTERLY_PROFIT_AND_LOSS_QUERY = """SELECT
  CONCAT('Q', QUARTER(gle.posting_date)) AS "Quarter:Data:90",
  ROUND(
    SUM(CASE WHEN account.root_type = 'Income'
      THEN gle.credit - gle.debit ELSE 0 END),
    2
  ) AS "Income:Currency:140",
  ROUND(
    SUM(CASE WHEN account.root_type = 'Expense'
      THEN gle.debit - gle.credit ELSE 0 END),
    2
  ) AS "Expense:Currency:140",
  ROUND(
    SUM(
      CASE
        WHEN account.root_type = 'Income' THEN gle.credit - gle.debit
        WHEN account.root_type = 'Expense' THEN gle.credit - gle.debit
        ELSE 0
      END
    ),
    2
  ) AS "Profit:Currency:140"
FROM `tabGL Entry` gle
INNER JOIN `tabAccount` account ON account.name = gle.account
WHERE gle.company = 'Alumicraft'
  AND gle.is_cancelled = 0
  AND EXISTS (
    SELECT 1
    FROM `tabFiscal Year` fiscal_year
    WHERE CURDATE() BETWEEN fiscal_year.year_start_date AND fiscal_year.year_end_date
      AND gle.posting_date BETWEEN fiscal_year.year_start_date AND fiscal_year.year_end_date
  )
GROUP BY QUARTER(gle.posting_date)
ORDER BY QUARTER(gle.posting_date)"""


def execute():
    repair_profit_and_loss_charts()
    repair_profit_and_loss_dashboard_source()
    repair_worst_projects_report()
    repair_worst_projects_chart()
    repair_finance_customer_deposits_card()


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


def repair_profit_and_loss_dashboard_source():
    report_name = QUARTERLY_PROFIT_AND_LOSS_REPORT
    if frappe.db.exists("Report", report_name):
        report = frappe.get_doc("Report", report_name)
    else:
        report = frappe.new_doc("Report")
        report.report_name = report_name

    report.ref_doctype = "GL Entry"
    report.report_type = "Query Report"
    report.is_standard = "No"
    report.module = "Accounts"
    report.query = QUARTERLY_PROFIT_AND_LOSS_QUERY
    report.save(ignore_permissions=True)

    legacy_chart_name = "Profit and Loss New"
    chart_name = "Quarterly Profit and Loss"
    if frappe.db.exists("Dashboard Chart", chart_name):
        chart = frappe.get_doc("Dashboard Chart", chart_name)
    else:
        chart = frappe.new_doc("Dashboard Chart")
        chart.chart_name = chart_name

    expected_axis = [
        ("income", FRAPPE_CHART_COLORS["pink"]),
        ("expense", FRAPPE_CHART_COLORS["blue"]),
        ("profit", FRAPPE_CHART_COLORS["green"]),
    ]
    chart.module = "Accounts"
    chart.is_public = 1
    chart.chart_type = "Report"
    chart.report_name = report_name
    chart.use_report_chart = 0
    chart.x_field = "quarter"
    chart.filters_json = "{}"
    chart.dynamic_filters_json = "{}"
    chart.type = "Bar"
    chart.currency = "USD"
    chart.show_values_over_chart = 1
    chart.set("y_axis", [])
    for y_field, color in expected_axis:
        chart.append("y_axis", {"y_field": y_field, "color": color})
    chart.save(ignore_permissions=True)

    for row in frappe.get_all(
        "Workspace Chart",
        filters={"chart_name": ["in", [legacy_chart_name, chart_name]]},
        fields=["name"],
    ):
        frappe.db.set_value(
            "Workspace Chart",
            row.name,
            {"label": chart_name, "chart_name": chart_name},
            update_modified=False,
        )

    for workspace in frappe.get_all("Workspace", fields=["name", "content"]):
        if legacy_chart_name not in (workspace.content or ""):
            continue
        frappe.db.set_value(
            "Workspace",
            workspace.name,
            "content",
            workspace.content.replace(legacy_chart_name, chart_name),
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
    expected_axis = [("recognized_gross_margin", FRAPPE_CHART_COLORS["pink"])]
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


def repair_finance_customer_deposits_card():
    workspace_name = "Finance"
    card_name = "Customer Deposits"
    if not (
        frappe.db.exists("Workspace", workspace_name)
        and frappe.db.exists("Number Card", card_name)
    ):
        return

    workspace = frappe.get_doc("Workspace", workspace_name)
    changed = False

    if not any(row.number_card_name == card_name for row in workspace.number_cards):
        workspace.append(
            "number_cards",
            {"label": card_name, "number_card_name": card_name},
        )
        changed = True

    try:
        content = json.loads(workspace.content or "[]")
    except (TypeError, ValueError):
        content = []

    has_card_block = any(
        isinstance(block, dict)
        and block.get("type") == "number_card"
        and (block.get("data") or {}).get("number_card_name") == card_name
        for block in content
    )
    if not has_card_block:
        card_block = {
            "id": "backdesk-finance-customer-deposits",
            "type": "number_card",
            "data": {"number_card_name": card_name, "col": 3},
        }
        insert_at = next(
            (
                index
                for index, block in enumerate(content)
                if isinstance(block, dict) and block.get("type") == "spacer"
            ),
            len(content),
        )
        content.insert(insert_at, card_block)
        workspace.content = json.dumps(content, separators=(",", ":"))
        changed = True

    if changed:
        workspace.save(ignore_permissions=True)
