frappe.pages["backdesk-month-end-close"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Month-end Close"),
		single_column: true,
	});

	const steps = [
		{
			title: __("Reconcile bank, card, and clearing accounts"),
			instruction: __(
				"Use the same month-end date for each statement. Map Transaction ID when the statement supplies it. Resolve unmatched lines and document timing differences, transfers, fees, and refunds."
			),
			links: [
				[__("Bank Statement Import"), ["List", "Bank Statement Import"]],
				[__("Bank Transactions"), ["List", "Bank Transaction"]],
				[__("Bank Reconciliation"), ["Form", "Bank Reconciliation Tool", "Bank Reconciliation Tool"]],
				[__("Bank Reconciliation Statement"), ["query-report", "Bank Reconciliation Statement"]],
			],
		},
		{
			title: __("Tie customer and supplier balances to the ledger"),
			instruction: __(
				"Compare receivables and payables aging to their control accounts. Review unapplied payments, customer deposits, and supplier credits."
			),
			links: [
				[__("Receivables Aging"), ["query-report", "Accounts Receivable"]],
				[__("Payables Aging"), ["query-report", "Accounts Payable"]],
				[__("Payment Reconciliation"), ["Form", "Payment Reconciliation", "Payment Reconciliation"]],
			],
		},
		{
			title: __("Review adjustments and financial statements"),
			instruction: __(
				"Confirm job costs and required period adjustments with the bookkeeper. Review the statements and trace differences to the posted vouchers."
			),
			links: [
				[__("Trial Balance"), ["query-report", "Trial Balance"]],
				[__("General Ledger"), ["query-report", "General Ledger"]],
				[__("Profit and Loss"), ["query-report", "Profit and Loss Statement"]],
				[__("Balance Sheet"), ["query-report", "Balance Sheet"]],
				[__("Cash Flow"), ["query-report", "Cash Flow"]],
			],
		},
		{
			title: __("Record sign-off and protect the period"),
			instruction: __(
				"Retain the reconciliations, approved adjustments, and reviewer sign-off. After approval, open Accounting Period, confirm the company and dates, and check Closed for each document type you want to protect."
			),
			links: [[__("Accounting Period"), ["List", "Accounting Period"]]],
		},
	];

	const checklist = $("<div>").addClass("standard-padding").appendTo(page.main);
	$("<p>")
		.addClass("text-muted")
		.text(__("Use one company and reporting period across the close. Each link opens the native ERPNext tool."))
		.appendTo(checklist);

	for (const step of steps) {
		const section = $("<section>").addClass("border-top py-3").appendTo(checklist);
		$("<h3>").addClass("h5").text(step.title).appendTo(section);
		$("<p>").text(step.instruction).appendTo(section);
		const links = $("<div>").addClass("d-flex flex-wrap").appendTo(section);
		for (const [label, route] of step.links) {
			if ((route[0] === "List" || route[0] === "Form") && !frappe.model.can_read(route[1])) {
				continue;
			}
			$("<button>")
				.attr("type", "button")
				.addClass("btn btn-default btn-sm mr-2 mb-2")
				.text(label)
				.on("click", () => frappe.set_route(...route))
				.appendTo(links);
		}
	}
};
