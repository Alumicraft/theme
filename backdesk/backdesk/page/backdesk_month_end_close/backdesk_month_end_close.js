frappe.pages["backdesk-month-end-close"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Month-end Close"),
		single_column: true,
	});
	const company_field = page.add_field({
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		default: frappe.defaults.get_user_default("Company"),
	});
	const close_date_field = page.add_field({
		fieldname: "close_date",
		label: __("Closing Date"),
		fieldtype: "Date",
		default: frappe.datetime.add_days(frappe.datetime.month_start(), -1),
	});
	company_field.$input.attr("aria-label", __("Company"));
	close_date_field.$input.attr("aria-label", __("Closing Date"));

	function selected_close() {
		const company = company_field.get_value();
		const to_date = close_date_field.get_value();
		if (!company || !to_date) {
			frappe.msgprint(__("Select a company and closing date."));
			return;
		}
		return { company, from_date: to_date.slice(0, 7) + "-01", to_date };
	}

	async function open_report(report) {
		const close = selected_close();
		if (!close) return;
		const { company, from_date, to_date } = close;
		const filters = { company };
		switch (report) {
			case "Bank Reconciliation Statement": {
				const { message } = await frappe.db.get_value("Company", company, "default_bank_account");
				Object.assign(filters, { report_date: to_date, account: message?.default_bank_account || "" });
				break;
			}
			case "Accounts Receivable":
			case "Accounts Receivable Summary":
				Object.assign(filters, { report_date: to_date, for_revaluation_journals: 1 });
				if (report === "Accounts Receivable Summary") filters.show_gl_balance = 1;
				break;
			case "Accounts Payable":
				filters.report_date = to_date;
				break;
			case "Trial Balance": {
				const [fiscal_year] = await frappe.xcall("erpnext.accounts.utils.get_fiscal_year", {
					date: to_date,
					company,
				});
				Object.assign(filters, { fiscal_year, from_date, to_date });
				break;
			}
			case "General Ledger":
				Object.assign(filters, { from_date, to_date });
				break;
			case "Profit and Loss Statement":
			case "Balance Sheet":
			case "Cash Flow":
				Object.assign(filters, {
					filter_based_on: "Date Range",
					period_start_date: from_date,
					period_end_date: to_date,
					periodicity: "Monthly",
				});
				if (report === "Cash Flow") filters.show_opening_and_closing_balance = 1;
				break;
		}
		frappe.route_options = filters;
		frappe.set_route("query-report", report);
	}

	const steps = [
		{
			title: __("Reconcile bank, card, and clearing accounts"),
			instruction: __(
				"Use the same month-end date across the reconciliation. Map Transaction ID when the statement supplies it. Match Stripe payouts to the bank and use Stripe's Balance report to verify funds awaiting payout, standalone fees, and bank debits. For transfers that clear in different months, match each dated entry through the bookkeeper's cash-in-transit account. Document refunds and unmatched lines."
			),
			links: [
				[__("Bank Statement Import"), ["List", "Bank Statement Import"]],
				[__("Bank Transactions"), ["List", "Bank Transaction"]],
				[__("Bank Reconciliation"), ["Form", "Bank Reconciliation Tool", "Bank Reconciliation Tool"]],
				[__("Bank Reconciliation Statement"), ["query-report", "Bank Reconciliation Statement"]],
				...(frappe.user_roles.includes("Accounts Manager")
					? [[__("Stripe Receipt Review"), ["backdesk-stripe-receipt-review"]]] : []),
			],
		},
		{
			title: __("Tie customer and supplier balances to the ledger"),
			instruction: __(
				"Compare receivables and payables aging to their control accounts. Review unapplied payments, customer deposits, and supplier credits."
			),
			links: [
				[__("Receivables Aging"), ["query-report", "Accounts Receivable"]],
				[__("Receivables Ledger Comparison"), ["query-report", "Accounts Receivable Summary"]],
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
	];

	const checklist = $("<div>").addClass("standard-padding").appendTo(page.main);
	$("<p>")
		.addClass("text-muted")
		.text(__("Report links use the selected company and the month through the closing date."))
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
				.on("click", async (event) => {
					if (route[0] !== "query-report") {
						frappe.set_route(...route);
						return;
					}
					const button = $(event.currentTarget).prop("disabled", true);
					try {
						await open_report(route[1]);
					} finally {
						button.prop("disabled", false);
					}
				})
				.appendTo(links);
		}
	}

	if (!frappe.model.can_read("Accounting Period")) return;
	const close_section = $("<section>").addClass("border-top py-3").appendTo(checklist);
	$("<h3>").addClass("h5").text(__("Record sign-off and protect the period")).appendTo(close_section);
	$("<p>")
		.text(__(
			"Attach reconciliations and approved adjustments to the Accounting Period. Assign the reviewer and record their sign-off in Comments. Leave a new period Disabled during review. After approval, verify which document types are marked Closed, then clear Disabled and save."
		))
		.appendTo(close_section);
	const find_button = $("<button>", { type: "button" })
		.addClass("btn btn-default btn-sm mb-2")
		.text(__("Find Accounting Period"))
		.appendTo(close_section);
	const period_status = $("<p>", { role: "status" }).addClass("text-muted mb-2").appendTo(close_section);
	const period_actions = $("<div>").appendTo(close_section);
	const clear_period_results = () => {
		period_status.empty();
		period_actions.empty();
	};
	for (const field of [company_field, close_date_field]) {
		field.$input.on("change", clear_period_results);
	}

	find_button.on("click", async () => {
		const close = selected_close();
		if (!close) return;
		const { company, from_date, to_date } = close;
		clear_period_results();
		period_status.text(__("Looking for Accounting Periods"));
		find_button.prop("disabled", true);
		try {
			const periods = await frappe.xcall("frappe.client.get_list", {
				doctype: "Accounting Period",
				fields: ["name", "start_date", "end_date"],
				filters: { company, start_date: ["<=", to_date], end_date: [">=", from_date] },
				order_by: "start_date asc",
				limit_page_length: 0,
			}, "GET");
			if (company !== company_field.get_value() || to_date !== close_date_field.get_value()) return;
			const exact = periods.find((period) => period.start_date === from_date && period.end_date === to_date);
			if (exact) {
				clear_period_results();
				frappe.set_route("Form", "Accounting Period", exact.name);
				return;
			}

			if (periods.length) {
				period_status.text(__("Existing Accounting Periods overlap this close. Review their dates before making changes."));
				for (const period of periods) {
					$("<button>", { type: "button" })
						.addClass("btn btn-default btn-sm mr-2 mb-2")
						.text(__("{0} ({1} to {2})", [period.name, period.start_date, period.end_date]))
						.on("click", () => {
							clear_period_results();
							frappe.set_route("Form", "Accounting Period", period.name);
						})
						.appendTo(period_actions);
				}
				return;
			}

			period_status.text(__("No visible Accounting Period overlaps this close."));
			if (!frappe.model.can_create("Accounting Period")) return;
			if (to_date > frappe.datetime.get_today()) {
				period_status.text(__("Choose a closing date on or before today to start an Accounting Period."));
				return;
			}
			$("<button>", { type: "button" })
				.addClass("btn btn-default btn-sm mb-2")
				.text(__("New Accounting Period"))
				.on("click", () => {
					clear_period_results();
					frappe.new_doc("Accounting Period", { company, start_date: from_date, end_date: to_date, disabled: 1 });
				})
				.appendTo(period_actions);
		} catch {
			period_status.text(__("The Accounting Period lookup failed. Try again."));
		} finally {
			find_button.prop("disabled", false);
		}
	});
};
