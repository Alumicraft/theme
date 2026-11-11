import importlib
import sys
from decimal import Decimal
from types import ModuleType, SimpleNamespace

import pytest


class InvalidSource(Exception):
    pass


@pytest.fixture
def review(monkeypatch):
    frappe = ModuleType("frappe")
    frappe._ = lambda message: message
    frappe.whitelist = lambda **kwargs: lambda method: method

    def throw(message, exc=InvalidSource):
        raise exc(message)

    frappe.throw = throw
    monkeypatch.setitem(sys.modules, "frappe", frappe)
    name = "backdesk.backdesk.page.backdesk_stripe_receipt_review.backdesk_stripe_receipt_review"
    monkeypatch.delitem(sys.modules, name, raising=False)
    return importlib.import_module(name)


def test_read_source_accepts_receipts_saved_from_the_workbook(review):
    source = (
        "\ufeffAlumicraft Stripe receipts\n"
        + ",".join(review.SOURCE_COLUMNS)
        + '\n2026-10-02,in_Sample,pi_Sample,ACC-PRQ-2026-00001,"1,203.48",-\n'
    )

    assert review.read_source(source) == [{
        "paid_date": "2026-10-02", "invoice": "in_Sample", "intent": "pi_Sample",
        "request": "ACC-PRQ-2026-00001", "gross": Decimal("1203.48"), "fee": Decimal("0"),
    }]


def test_read_source_rejects_one_payment_intent_claimed_by_two_invoices(review):
    source = ",".join(review.SOURCE_COLUMNS) + (
        "\n2026-10-02,in_First,pi_Sample,,200,6"
        "\n2026-10-02,in_Second,pi_Sample,,200,6\n"
    )

    with pytest.raises(InvalidSource, match="row 3 repeats"):
        review.read_source(source)


def test_two_submitted_receipts_need_review_even_when_the_total_matches(review, monkeypatch):
    company = "Example Accounting"
    frappe = review.frappe
    role_checks = []
    frappe.only_for = role_checks.append
    frappe.has_permission = lambda *_: True
    frappe.get_meta = lambda _: SimpleNamespace(has_field=lambda _: False)
    frappe.get_all = lambda *args, **kwargs: []

    def get_list(doctype, *, filters, fields, limit_page_length, or_filters=None):
        assert limit_page_length == 0
        if doctype == "Company":
            assert filters["name"] == company
            return [SimpleNamespace(default_currency="USD")]
        assert filters["company"] == company
        if doctype == "Account":
            return [SimpleNamespace(name="Clearing"), SimpleNamespace(name="Fees")]
        if doctype == "Payment Request":
            return [SimpleNamespace(name="PR-1", docstatus=1, get=lambda _: None)]
        if doctype == "Payment Entry":
            assert filters["docstatus"] == 1
            assert filters["reference_no"] == ["in", ["in_Sample", "pi_Sample"]]
            return [
                SimpleNamespace(name="PE-1", reference_no="in_Sample", posting_date="2026-10-02"),
                SimpleNamespace(name="PE-2", reference_no="pi_Sample", posting_date="2026-10-02"),
            ]
        if doctype == "Journal Entry":
            assert {row[0] for row in or_filters} == {"user_remark", "remark"}
            return []
        assert doctype == "GL Entry"
        assert filters["is_cancelled"] == 0
        return [
            SimpleNamespace(voucher_no="PE-1", account="Clearing", debit=100, credit=0),
            SimpleNamespace(voucher_no="PE-2", account="Clearing", debit=100, credit=0),
        ]

    monkeypatch.setattr(frappe, "get_list", get_list, raising=False)
    source = ",".join(review.SOURCE_COLUMNS) + "\n2026-10-02,in_Sample,pi_Sample,PR-1,200,0\n"
    result, = review.review_receipts(company, "Clearing", "Fees", source)

    assert role_checks == ["Accounts Manager"]
    assert result["gross_posted"] == 200
    assert [payment["name"] for payment in result["payments"]] == ["PE-1", "PE-2"]
    assert result["issues"] == ["Multiple submitted Payment Entries match this Stripe receipt."]


@pytest.mark.parametrize("clearing_debit", [200, 0])
def test_finds_receipt_with_bank_reference_through_the_stripe_payment_request(review, clearing_debit):
    frappe = review.frappe
    frappe.only_for = lambda _: None
    frappe.has_permission = lambda *_: True
    frappe.get_meta = lambda doctype: SimpleNamespace(has_field={
        "Payment Request": {"stripe_invoice_id"}, "Payment Entry Reference": {"payment_request"},
    }[doctype].__contains__)
    request = SimpleNamespace(
        name="PR-1", docstatus=1, stripe_invoice_id="in_Sample", reference_doctype="Sales Invoice",
        reference_name="SI-1", get=lambda field: "in_Sample" if field == "stripe_invoice_id" else None,
    )
    payment = SimpleNamespace(
        name="PE-1", reference_no="4270465600", payment_type="Receive", posting_date="2026-10-27",
    )
    allocation = SimpleNamespace(
        parent="PE-1", payment_request="PR-1", reference_doctype="Sales Invoice", reference_name="SI-1",
        allocated_amount=200,
    )

    def get_list(doctype, *, filters, **kwargs):
        if doctype == "Company":
            return [SimpleNamespace(default_currency="USD")]
        if doctype == "Account":
            return [SimpleNamespace(name="Clearing"), SimpleNamespace(name="Fees")]
        if doctype == "Payment Request":
            return [request]
        if doctype == "Payment Entry":
            assert filters["docstatus"] == 1
            return [payment] if "PE-1" in filters.get("name", ["in", []])[1] else []
        if doctype == "Journal Entry":
            return []
        assert doctype == "GL Entry"
        assert filters["voucher_no"] == ["in", ["PE-1"]]
        return [SimpleNamespace(voucher_no="PE-1", account="Clearing", debit=clearing_debit, credit=0)]

    frappe.get_list = get_list
    frappe.get_all = lambda doctype, **kwargs: [allocation]
    source = ",".join(review.SOURCE_COLUMNS) + "\n2026-10-27,in_Sample,pi_Sample,PR-1,200,0\n"

    result, = review.review_receipts("Alumicraft", "Clearing", "Fees", source)

    assert result["payments"] == [{"name": "PE-1", "date": "2026-10-27"}]
    assert result["gross_posted"] == clearing_debit
    assert bool(result["issues"]) == (clearing_debit == 0)
