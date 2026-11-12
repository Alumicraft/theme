import csv
import io
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

import frappe
from frappe import _


SOURCE_COLUMNS = (
    "Invoice paid date", "Stripe invoice ID", "PaymentIntent ID", "Backdesk Payment Request", "Gross", "Charge fee",
)


@frappe.whitelist(methods=["POST"])
def review_receipts(company: str, clearing_account: str, fee_account: str, source: str):
    frappe.only_for("Accounts Manager")
    for doctype in ("Payment Request", "Payment Entry", "Journal Entry", "GL Entry"):
        if not frappe.has_permission(doctype, "read"):
            frappe.throw(_("Read access to {0} is required.").format(doctype), frappe.PermissionError)

    validate_accounts(company, clearing_account, fee_account)
    receipts = read_source(source)
    invoice_ids = [receipt["invoice"] for receipt in receipts]
    references = invoice_ids + [receipt["intent"] for receipt in receipts if receipt["intent"]]
    request_fields = ["name", "docstatus", "reference_doctype", "reference_name", "currency", "grand_total"]
    if frappe.get_meta("Payment Request").has_field("stripe_invoice_id"):
        request_fields.append("stripe_invoice_id")
    requests = {
        request.name: request
        for request in visible_rows(
            "Payment Request", {"company": company, "name": ["in", [
                receipt["request"] for receipt in receipts if receipt["request"]
            ]]}, request_fields
        )
    }

    payments_by_reference = defaultdict(list)
    for payment in visible_rows(
        "Payment Entry",
        {"company": company, "docstatus": 1, "reference_no": ["in", references]},
        ["name", "reference_no", "payment_type", "posting_date"],
    ):
        payments_by_reference[payment.reference_no].append(payment)

    verified_requests = {
        request.name for receipt in receipts
        if (request := requests.get(receipt["request"]))
        and request.docstatus == 1 and request.get("stripe_invoice_id") == receipt["invoice"]
    }
    payments_by_request = defaultdict(list)
    if verified_requests and frappe.get_meta("Payment Entry Reference").has_field("payment_request"):
        links = frappe.get_all(
            "Payment Entry Reference",
            filters={"payment_request": ["in", sorted(verified_requests)], "parenttype": "Payment Entry",
                     "parentfield": "references", "allocated_amount": [">", 0]},
            fields=["parent", "payment_request"],
        )
        if links:
            linked_payments = {
                payment.name: payment for payment in visible_rows(
                    "Payment Entry", {"company": company, "docstatus": 1,
                                      "name": ["in", list(dict.fromkeys(link.parent for link in links))]},
                    ["name", "payment_type", "posting_date"],
                )
            }
            for link in links:
                if link.parent in linked_payments:
                    payments_by_request[link.payment_request].append(linked_payments[link.parent])

    receipts_without_match = [
        requests[receipt["request"]] for receipt in receipts
        if receipt["request"] in verified_requests
        and not payments_by_request[receipt["request"]]
        and not payments_by_reference[receipt["invoice"]]
        and not payments_by_reference[receipt["intent"]]
    ]
    advance_candidates = find_reallocated_advances(company, receipts_without_match)

    fee_remarks = {f"Stripe processing fee for invoice {invoice}": invoice for invoice in invoice_ids}
    surcharge_remarks = {
        f"Card processing fee income for invoice {invoice}": invoice for invoice in invoice_ids
    }
    fees, surcharges = defaultdict(list), defaultdict(list)
    tags = [*fee_remarks, *surcharge_remarks]
    for journal in frappe.get_list(
        "Journal Entry",
        filters={"company": company, "docstatus": 1},
        or_filters=[[field, "in", tags] for field in ("user_remark", "remark")],
        fields=["name", "user_remark", "remark"],
        limit_page_length=0,
    ):
        # Existing Stripe journals use user_remark. Desk exposes remark on v16.
        tag = journal.user_remark if journal.user_remark in tags else journal.remark
        if tag in fee_remarks:
            fees[fee_remarks[tag]].append(journal.name)
        elif tag in surcharge_remarks:
            surcharges[surcharge_remarks[tag]].append(journal.name)

    payment_names = list(dict.fromkeys(
        payment.name for groups in (payments_by_reference, payments_by_request)
        for group in groups.values() for payment in group
    ))
    journal_names = [name for groups in (fees, surcharges) for group in groups.values() for name in group]
    allocations = defaultdict(Decimal)
    if payment_names:
        # Parent names already passed Payment Entry read permissions above.
        for reference in frappe.get_all(
            "Payment Entry Reference",
            filters={"parent": ["in", payment_names], "parenttype": "Payment Entry",
                     "allocated_amount": [">", 0]},
            fields=["parent", "reference_doctype", "reference_name", "allocated_amount"],
        ):
            key = (reference.parent, reference.reference_doctype, reference.reference_name)
            allocations[key] += money(reference.allocated_amount)

    ledger = defaultdict(Decimal)
    for voucher_type, names in (("Payment Entry", payment_names), ("Journal Entry", journal_names)):
        if not names:
            continue
        for line in visible_rows(
            "GL Entry",
            {"company": company, "voucher_type": voucher_type, "voucher_no": ["in", names],
             "account": ["in", [clearing_account, fee_account]], "is_cancelled": 0},
            ["voucher_no", "account", "debit", "credit"],
        ):
            ledger[(line.voucher_no, line.account)] += money(line.debit) - money(line.credit)

    results = []
    for receipt in receipts:
        invoice = receipt["invoice"]
        request = requests.get(receipt["request"])
        matches = list({payment.name: payment for payment in (
            payments_by_reference[invoice] + payments_by_reference[receipt["intent"]]
            + payments_by_request[receipt["request"]]
        )}.values())
        payment_ids = [payment.name for payment in matches]
        fee_ids = fees[invoice]
        surcharge_ids = surcharges[invoice]
        gross_posted = sum((ledger[(name, clearing_account)] for name in payment_ids + surcharge_ids), Decimal(0))
        fee_posted = sum((ledger[(name, fee_account)] for name in fee_ids), Decimal(0))
        fee_clearing = sum((ledger[(name, clearing_account)] for name in fee_ids), Decimal(0))
        issues = []
        if not request or request.docstatus != 1:
            issues.append(_("No visible submitted Payment Request."))
        elif request.get("stripe_invoice_id") and request.stripe_invoice_id != invoice:
            issues.append(_("The Payment Request links to a different Stripe invoice."))

        candidates = advance_candidates.get(receipt["request"], [])
        if candidates:
            issues.append(_("Confirm the receipt against the original Sales Order."))
        elif not matches:
            issues.append(_("No visible submitted Payment Entry matches the Stripe IDs or verified Payment Request."))
        elif len(matches) > 1:
            issues.append(_("Multiple submitted Payment Entries match this Stripe receipt."))
        else:
            payment = matches[0]
            if payment.payment_type != "Receive":
                issues.append(_("The Payment Entry is not a customer receipt."))
            if str(payment.posting_date) != receipt["paid_date"]:
                issues.append(_("The receipt posting date differs from the Stripe paid date."))
            if request and request.reference_name:
                allocated = allocations[(payment.name, request.reference_doctype, request.reference_name)]
                if allocated <= 0 or allocated != ledger[(payment.name, clearing_account)]:
                    issues.append(_("Check the receipt allocation to the Payment Request reference."))

        if gross_posted != receipt["gross"]:
            issues.append(_("Receipt and surcharge postings to clearing differ from Stripe gross."))
        if len(surcharge_ids) > 1:
            issues.append(_("Multiple surcharge journals match this Stripe invoice."))
        if len(fee_ids) != int(receipt["fee"] > 0):
            issues.append(_("Check the number of submitted Stripe fee journals."))
        if fee_posted != receipt["fee"] or fee_clearing != -receipt["fee"]:
            issues.append(_("Fee expense or clearing differs from the Stripe charge fee."))

        results.append({
            **receipt, "has_request": bool(request),
            "payments": [{"name": payment.name, "date": payment.posting_date} for payment in matches],
            "payment_candidates": candidates,
            "fee_journals": fee_ids, "surcharge_journals": surcharge_ids,
            "gross_posted": gross_posted, "fee_posted": fee_posted, "issues": issues,
        })
    return results


def find_reallocated_advances(company, requests):
    order_requests = [
        request for request in requests
        if request.reference_doctype == "Sales Order" and request.reference_name and request.currency == "USD"
    ]
    if not order_requests:
        return {}
    meta = frappe.get_meta("Payment Entry Reference")
    if not all(meta.has_field(field) for field in ("payment_request", "advance_voucher_type", "advance_voucher_no")):
        return {}

    allocated = defaultdict(lambda: defaultdict(Decimal))
    for reference in frappe.get_all(
        "Payment Entry Reference",
        filters={"parenttype": "Payment Entry", "parentfield": "references",
                 "reference_doctype": "Sales Invoice", "payment_request": ["is", "not set"],
                 "advance_voucher_type": "Sales Order",
                 "advance_voucher_no": ["in", sorted({request.reference_name for request in order_requests})],
                 "allocated_amount": [">", 0]},
        fields=["parent", "advance_voucher_no", "allocated_amount"],
    ):
        allocated[reference.advance_voucher_no][reference.parent] += money(reference.allocated_amount)

    by_request = {
        request.name: {
            parent: amount for parent, amount in allocated[request.reference_name].items()
            if amount == money(request.grand_total)
        }
        for request in order_requests
    }
    names = list(dict.fromkeys(parent for candidates in by_request.values() for parent in candidates))
    if not names:
        return {}

    payments = visible_rows(
        "Payment Entry",
        {"company": company, "docstatus": 1, "payment_type": "Receive", "paid_from_account_currency": "USD",
         "name": ["in", names]},
        ["name", "posting_date"],
    )
    return {
        name: [{"name": payment.name, "date": payment.posting_date, "allocated": candidates[payment.name]}
               for payment in payments if payment.name in candidates]
        for name, candidates in by_request.items()
    }


def validate_accounts(company, clearing_account, fee_account):
    companies = visible_rows("Company", {"name": company}, ["name", "default_currency"])
    if not companies:
        frappe.throw(_("Select a company you can read."), frappe.PermissionError)
    if companies[0].default_currency != "USD":
        frappe.throw(_("Select a company whose ledger currency is USD for this Stripe export."))
    accounts = visible_rows(
        "Account", {"company": company, "name": ["in", [clearing_account, fee_account]], "is_group": 0},
        ["name"],
    )
    if len(accounts) != 2:
        frappe.throw(_("Select distinct clearing and fee accounts from the selected company."))


def visible_rows(doctype, filters, fields):
    return frappe.get_list(doctype, filters=filters, fields=fields, limit_page_length=0)


def money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def source_money(value):
    value = value.strip().replace(",", "").removeprefix("$")
    amount = Decimal(0) if value == "-" else Decimal(value)
    if not amount.is_finite() or amount < 0 or amount != money(amount):
        raise ValueError
    return amount


def read_source(source):
    if not isinstance(source, str) or len(source.encode("utf-8")) > 500_000:
        frappe.throw(_("Select a CSV file up to 500 KB."))
    columns = None
    invoice_ids, intent_ids = set(), set()
    receipts = []
    reader = csv.reader(io.StringIO(source.lstrip("\ufeff")), strict=True)
    try:
        for row in reader:
            if columns is None:
                header = [cell.strip() for cell in row]
                if all(field in header for field in SOURCE_COLUMNS):
                    columns = [header.index(field) for field in SOURCE_COLUMNS]
                continue
            if not any(cell.strip() for cell in row):
                continue
            paid_date, invoice, intent, request, gross, fee = [row[i].strip() for i in columns]
            if not re.fullmatch(r"in_[A-Za-z0-9]+", invoice) or (
                intent and not re.fullmatch(r"pi_[A-Za-z0-9]+", intent)
            ):
                raise ValueError
            if invoice in invoice_ids or intent and intent in intent_ids:
                frappe.throw(_("CSV row {0} repeats a Stripe invoice or PaymentIntent.").format(reader.line_num))
            invoice_ids.add(invoice)
            if intent:
                intent_ids.add(intent)
            receipts.append({
                "paid_date": date.fromisoformat(paid_date).isoformat(), "invoice": invoice, "intent": intent,
                "request": request, "gross": source_money(gross), "fee": source_money(fee),
            })
    except (csv.Error, IndexError, InvalidOperation, ValueError):
        frappe.throw(_("Check the date, Stripe IDs, and USD amounts on CSV row {0}.").format(reader.line_num or 1))
    if not receipts:
        frappe.throw(_("Select the Stripe receipts CSV with its header and receipt rows."))
    return receipts
