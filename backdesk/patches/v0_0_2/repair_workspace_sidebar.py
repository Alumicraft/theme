import json

import frappe


PRODUCT_LINKS = (
    {
        "label": "Sales Workflow",
        "link_type": "DocType",
        "icon": "sell",
        "type": "Section Break",
    },
    {"label": "Quotations", "link_type": "DocType", "type": "Link", "link_to": "Quotation"},
    {"label": "Sales Orders", "link_type": "DocType", "type": "Link", "link_to": "Sales Order"},
    {"label": "Sales Invoices", "link_type": "DocType", "type": "Link", "link_to": "Sales Invoice"},
)

OVERVIEW_NUMBER_CARDS = (
    {"label": "Active Builds", "number_card_name": "Build Count"},
    {"label": "Active Service / Parts", "number_card_name": "Service/Parts Count"},
    {"label": "Receivables Due", "number_card_name": "Receivables"},
    {"label": "Payables Due", "number_card_name": "Payables Due"},
)

OVERVIEW_CHARTS = (
    {"label": "Profit and Loss", "chart_name": "Profit and Loss New"},
)

OVERVIEW_CONTENT = [
    {
        "id": "backdesk-overview-operations",
        "type": "header",
        "data": {"text": '<span class="h4"><b>Operations</b></span>', "col": 12},
    },
    {
        "id": "backdesk-overview-builds",
        "type": "number_card",
        "data": {"number_card_name": "Active Builds", "col": 3},
    },
    {
        "id": "backdesk-overview-service",
        "type": "number_card",
        "data": {"number_card_name": "Active Service / Parts", "col": 3},
    },
    {
        "id": "backdesk-overview-receivables",
        "type": "number_card",
        "data": {"number_card_name": "Receivables Due", "col": 3},
    },
    {
        "id": "backdesk-overview-payables",
        "type": "number_card",
        "data": {"number_card_name": "Payables Due", "col": 3},
    },
    {"id": "backdesk-overview-spacer", "type": "spacer", "data": {"col": 12}},
    {
        "id": "backdesk-overview-finance",
        "type": "header",
        "data": {"text": '<span class="h4"><b>Financial Performance</b></span>', "col": 12},
    },
    {
        "id": "backdesk-overview-pnl",
        "type": "chart",
        "data": {"chart_name": "Profit and Loss New", "col": 12},
    },
]


def execute():
    repair_finance()
    repair_access()
    add_product_workflow_links()
    repair_operational_number_cards()
    build_overview_dashboard()


def get_sidebar(name):
    if not frappe.db.exists("Workspace Sidebar", name):
        return None
    return frappe.get_doc("Workspace Sidebar", name)


def save_if_changed(doc, changed):
    if changed:
        doc.save(ignore_permissions=True)


def repair_finance():
    doc = get_sidebar("Finance")
    if not doc:
        return

    changed = False
    for item in doc.items:
        if item.label == "Recievables":
            item.label = "Receivables"
            changed = True
        if item.label == "Sales Orders" and item.link_to != "Sales Order":
            item.link_type = "DocType"
            item.link_to = "Sales Order"
            changed = True
        if item.label == "Payment Requests" and item.link_to != "Payment Request":
            item.link_type = "DocType"
            item.link_to = "Payment Request"
            changed = True

    save_if_changed(doc, changed)


def repair_access():
    doc = get_sidebar("Access")
    if not doc:
        return

    changed = False
    for item in list(doc.items):
        if item.label == "User Permissions" and item.link_to == "Role":
            item.link_type = "DocType"
            item.link_to = "User Permission"
            changed = True
        elif item.link_to in {"Permission Inspector", "permission-inspector"}:
            if frappe.db.exists("Page", "permission-inspector"):
                item.label = "Permission Inspector"
                item.link_type = "Page"
                item.link_to = "permission-inspector"
            else:
                doc.remove(item)
            changed = True

    save_if_changed(doc, changed)


def add_product_workflow_links():
    doc = get_sidebar("Products")
    if not doc:
        return

    existing_labels = {item.label for item in doc.items if item.label}
    changed = False
    for values in PRODUCT_LINKS:
        if values["label"] in existing_labels:
            continue
        doc.append("items", values)
        existing_labels.add(values["label"])
        changed = True

    save_if_changed(doc, changed)


def repair_operational_number_cards():
    filters_by_card = {
        "Build Count": [
            ["Project", "project_type", "=", "Build"],
            ["Project", "status", "not in", ["Completed", "Cancelled", "Canceled"]],
        ],
        "Service/Parts Count": [
            ["Project", "project_type", "!=", "Build"],
            ["Project", "status", "not in", ["Completed", "Cancelled", "Canceled"]],
        ],
    }
    for name, filters in filters_by_card.items():
        if not frappe.db.exists("Number Card", name):
            continue
        doc = frappe.get_doc("Number Card", name)
        filters_json = json.dumps(filters, separators=(",", ":"))
        if doc.filters_json == filters_json:
            continue
        doc.filters_json = filters_json
        doc.save(ignore_permissions=True)


def build_overview_dashboard():
    if not frappe.db.exists("Workspace", "Overview"):
        return

    doc = frappe.get_doc("Workspace", "Overview")
    changed = False

    existing_cards = {row.label for row in doc.number_cards if row.label}
    for values in OVERVIEW_NUMBER_CARDS:
        if values["label"] in existing_cards:
            continue
        doc.append("number_cards", values)
        existing_cards.add(values["label"])
        changed = True

    existing_charts = {row.label for row in doc.charts if row.label}
    for values in OVERVIEW_CHARTS:
        if values["label"] in existing_charts:
            continue
        doc.append("charts", values)
        existing_charts.add(values["label"])
        changed = True

    if not doc.content or doc.content == "[]":
        doc.content = json.dumps(OVERVIEW_CONTENT, separators=(",", ":"))
        changed = True

    save_if_changed(doc, changed)
