"""Add accounting routes to the site's existing Finance sidebar."""

import frappe


FINANCE_GROUPS = (
    (
        "Receivables",
        (
            ("Report", "Accounts Receivable", "Receivables Aging"),
            ("DocType", "Payment Reconciliation", "Payment Reconciliation"),
            ("Report", "Customer Deposit Ledger", "Customer Deposit Ledger"),
        ),
    ),
    (
        "Payables & Expenses",
        (
            ("DocType", "Purchase Invoice", "Purchase Invoices"),
            ("Report", "Accounts Payable", "Payables Aging"),
            ("DocType", "Vendor Credit", "QuickBooks Vendor Credits"),
            ("DocType", "Journal Entry", "Journal Entries"),
        ),
    ),
    (
        "Banking",
        (
            ("DocType", "Bank Statement Import", "Bank Statement Import"),
            ("DocType", "Bank Transaction", "Bank Transactions"),
            ("DocType", "Bank Reconciliation Tool", "Bank Reconciliation"),
            ("Report", "Bank Reconciliation Statement", "Bank Reconciliation Statement"),
        ),
    ),
    (
        "Imports",
        (
            ("Report", "QuickBooks Import Review", "QuickBooks Import Review"),
            ("DocType", "Quickbook Settings", "QuickBooks Settings"),
        ),
    ),
    (
        "Reports",
        (
            ("Report", "General Ledger", "General Ledger"),
            ("Report", "Trial Balance", "Trial Balance"),
            ("Report", "Profit and Loss Statement", "Profit and Loss"),
            ("Report", "Balance Sheet", "Balance Sheet"),
            ("Report", "Cash Flow", "Cash Flow"),
            ("Report", "Project Profitability", "Project Profitability"),
        ),
    ),
    (
        "Month-end Close",
        (
            ("Page", "backdesk-month-end-close", "Close Checklist"),
            ("DocType", "Accounting Period", "Accounting Period"),
            ("DocType", "Period Closing Voucher", "Period Closing Voucher"),
            ("DocType", "Account", "Chart of Accounts"),
        ),
    ),
)


def execute():
    sidebar = get_finance_sidebar()
    if not sidebar:
        return

    destinations = {
        (item.link_type, item.link_to) for item in sidebar.items if item.type == "Link"
    }
    changed = False
    for group, links in FINANCE_GROUPS:
        additions = [
            (link_type, target, label)
            for link_type, target, label in links
            if (link_type, target) not in destinations and frappe.db.exists(link_type, target)
        ]
        if not additions:
            continue

        position = section_end(sidebar.items, group)
        if position is None:
            sidebar.append("items", {"type": "Section Break", "label": group})
            position = len(sidebar.items)

        for link_type, target, label in additions:
            sidebar.append(
                "items",
                {
                    "type": "Link",
                    "label": label,
                    "link_type": link_type,
                    "link_to": target,
                },
                position=position,
            )
            position += 1
            destinations.add((link_type, target))
        changed = True

    if changed:
        for position, item in enumerate(sidebar.items, start=1):
            item.idx = position
        sidebar.save(ignore_permissions=True)


def get_finance_sidebar():
    # Current Frappe v16 serves Sidebar. Earlier builds use Workspace Sidebar.
    if frappe.db.exists("DocType", "Sidebar"):
        doctype = "Sidebar"
    else:
        doctype = "Workspace Sidebar"
    if frappe.db.exists("DocType", doctype) and frappe.db.exists(doctype, "Finance"):
        return frappe.get_doc(doctype, "Finance")
    return None


def section_end(items, label):
    start = next(
        (
            index
            for index, item in enumerate(items)
            if item.type == "Section Break" and item.label == label
        ),
        None,
    )
    if start is None:
        return None
    return next(
        (index for index in range(start + 1, len(items)) if items[index].type == "Section Break"),
        len(items),
    )
