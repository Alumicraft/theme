import importlib
import sys
from types import ModuleType, SimpleNamespace


class Sidebar:
    def __init__(self, *rows):
        self.items = list(rows)
        self.saves = 0

    def append(self, fieldname, values, position=-1):
        assert fieldname == "items"
        row = SimpleNamespace(**values)
        if position == -1:
            self.items.append(row)
        else:
            self.items.insert(position, row)

    def save(self, *, ignore_permissions):
        assert ignore_permissions
        self.saves += 1


def load_patch(monkeypatch, records):
    frappe = ModuleType("frappe")
    frappe.db = SimpleNamespace(exists=lambda doctype, name: (doctype, name) in records)
    frappe.get_doc = lambda doctype, name: records[doctype, name]
    monkeypatch.setitem(sys.modules, "frappe", frappe)

    name = "backdesk.patches.v0_0_2.add_finance_accounting_links"
    monkeypatch.delitem(sys.modules, name, raising=False)
    return importlib.import_module(name)


def test_finance_links_preserve_existing_routes_and_can_be_applied_again(monkeypatch):
    existing_invoice = SimpleNamespace(
        type="Link", label="Outstanding Invoices", link_type="DocType",
        link_to="Sales Invoice", filters='[["status", "!=", "Paid"]]',
    )
    existing_bank = SimpleNamespace(
        type="Link", label="Our Bank Transactions", link_type="DocType",
        link_to="Bank Transaction",
    )
    sidebar = Sidebar(
        SimpleNamespace(type="Section Break", label="Receivables"),
        existing_invoice,
        SimpleNamespace(type="Section Break", label="Banking"),
        existing_bank,
    )
    patch = load_patch(
        monkeypatch,
        {
            ("DocType", "Workspace Sidebar"): True,
            ("Workspace Sidebar", "Finance"): sidebar,
            ("Report", "Accounts Receivable"): True,
            ("Report", "Accounts Payable"): True,
            ("DocType", "Bank Transaction"): True,
            ("Report", "Bank Reconciliation Statement"): True,
            ("DocType", "Accounting Period"): True,
        },
    )

    patch.execute()
    patch.execute()

    assert [item.label for item in sidebar.items] == [
        "Receivables",
        "Outstanding Invoices",
        "Receivables Aging",
        "Banking",
        "Our Bank Transactions",
        "Bank Reconciliation Statement",
        "Payables & Expenses",
        "Payables Aging",
        "Month-end Close",
        "Accounting Period",
    ]
    assert sidebar.items[1] is existing_invoice
    assert existing_invoice.filters == '[["status", "!=", "Paid"]]'
    assert sidebar.items[4] is existing_bank
    assert [item.idx for item in sidebar.items] == list(range(1, 11))
    assert sidebar.saves == 1


def test_finance_links_use_current_sidebar_when_legacy_archive_exists(monkeypatch):
    active = Sidebar()
    archive = Sidebar()
    patch = load_patch(
        monkeypatch,
        {
            ("DocType", "Sidebar"): True,
            ("Sidebar", "Finance"): active,
            ("DocType", "Workspace Sidebar"): True,
            ("Workspace Sidebar", "Finance"): archive,
            ("Report", "General Ledger"): True,
        },
    )

    patch.execute()

    assert [(item.label, item.type) for item in active.items] == [
        ("Reports", "Section Break"),
        ("General Ledger", "Link"),
    ]
    assert not archive.items


def test_no_finance_sidebar_leaves_other_sites_alone(monkeypatch):
    patch = load_patch(
        monkeypatch,
        {("DocType", "Workspace Sidebar"): True, ("Report", "Accounts Receivable"): True},
    )

    patch.execute()
