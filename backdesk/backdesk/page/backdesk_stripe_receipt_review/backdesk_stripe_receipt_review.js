frappe.pages["backdesk-stripe-receipt-review"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Stripe Receipt Review"),
		single_column: true,
	});
	const company = page.add_field({
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		default: frappe.defaults.get_user_default("Company"),
	});
	const account_fields = [
		["clearing_account", __("Stripe Clearing Account")],
		["fee_account", __("Stripe Fee Expense Account")],
	].map(([fieldname, label]) =>
		page.add_field({
			fieldname,
			label,
			fieldtype: "Link",
			options: "Account",
			get_query: () => ({ filters: { company: company.get_value(), is_group: 0 } }),
		})
	);
	for (const field of [company, ...account_fields]) {
		field.$input.attr("aria-label", field.df.label);
	}

	const body = $("<div>").addClass("standard-padding").appendTo(page.main);
	$("<p>")
		.text(__("Choose a USD Stripe receipts CSV and the two accounts used for Stripe in this company. The review finds submitted receipts by Stripe ID or linked Payment Request and checks their ledger amounts."))
		.appendTo(body);
	const file = $("<input>", {
		id: "stripe-receipts-source",
		type: "file",
		accept: ".csv,text/csv",
	}).addClass("form-control-file").appendTo(
		$("<div>").addClass("form-group").appendTo(body)
	);
	$("<label>", { for: "stripe-receipts-source" })
		.text(__("Stripe receipts CSV"))
		.insertBefore(file);
	const button = $("<button>", { type: "button" })
		.addClass("btn btn-primary mb-3")
		.text(__("Review Receipts"))
		.appendTo(body);
	const summary = $("<p>", { role: "status" }).appendTo(body);
	const results = $("<div>").addClass("table-responsive").appendTo(body);
	const clear = () => {
		summary.empty();
		results.empty();
	};
	for (const field of [company, ...account_fields]) {
		field.$input.on("change", clear);
	}
	company.$input.on("change", () => account_fields.forEach((field) => field.set_value("")));
	file.on("change", clear);

	button.on("click", async () => {
		clear();
		const selected = file[0].files[0];
		const [clearing_account, fee_account] = account_fields.map((field) => field.get_value());
		const company_name = company.get_value();
		if (!selected || !company_name || !clearing_account || !fee_account) {
			summary.text(__("Select the company, both accounts, and the CSV file."));
			return;
		}
		if (selected.size > 500000) {
			summary.text(__("Select a CSV file up to 500 KB."));
			return;
		}

		button.prop("disabled", true);
		try {
			const { message } = await frappe.call({
				method: "backdesk.backdesk.page.backdesk_stripe_receipt_review.backdesk_stripe_receipt_review.review_receipts",
				args: { company: company_name, clearing_account, fee_account, source: await selected.text() },
				freeze: true,
				freeze_message: __("Checking Stripe receipts against the ledger"),
			});
			render_results(message);
		} catch {
			summary.text(__("The review could not run. Check the file and account selection."));
		} finally {
			button.prop("disabled", false);
		}
	});

	function render_results(rows) {
		const review_count = rows.filter((row) => row.issues.length).length;
		const checked = rows.length === 1 ? __("Checked 1 receipt.") : __("Checked {0} receipts.", [rows.length]);
		summary.text(checked + " " + __("{0} to review.", [review_count]));
		const table = $("<table>").addClass("table table-bordered").appendTo(results);
		const headers = $("<tr>").appendTo($("<thead>").appendTo(table));
		for (const label of ["Paid Date", "Stripe Invoice", "Payment Request", "Payment Entries",
			"Journals", "Gross (Stripe / Matched Ledger)", "Fee (Stripe / Ledger)", "Result"]) {
			$("<th>", { scope: "col" }).text(__(label)).appendTo(headers);
		}
		const tbody = $("<tbody>").appendTo(table);
		const usd = (amount) => format_currency(amount, "USD");
		for (const row of rows) {
			const tr = $("<tr>").appendTo(tbody);
			$("<td>").text(row.paid_date).appendTo(tr);
			const stripe = $("<td>").text(row.invoice).appendTo(tr);
			if (row.intent) $("<div>").text(row.intent).appendTo(stripe);
			const request = $("<td>").appendTo(tr);
			if (row.has_request) append_links(request, "Payment Request", [row.request]);
			else request.text(row.request);
			const entries = $("<td>").appendTo(tr);
			for (const payment of row.payments) {
				append_links(entries, "Payment Entry", [payment.name]);
				$("<div>").addClass("text-muted").text(payment.date).appendTo(entries);
			}
			for (const payment of row.payment_candidates ?? []) {
				append_links(entries, "Payment Entry", [payment.name]);
				$("<div>").addClass("text-muted").text(__("Possible receipt from Sales Order · {0} · {1}", [
					payment.date, usd(payment.allocated),
				])).appendTo(entries);
			}
			append_links($("<td>").appendTo(tr), "Journal Entry", [...row.surcharge_journals, ...row.fee_journals]);
			$("<td>").text(usd(row.gross) + " / " + usd(row.gross_posted)).appendTo(tr);
			$("<td>").text(usd(row.fee) + " / " + usd(row.fee_posted)).appendTo(tr);
			$("<td>").text(row.issues.length ? row.issues.join(" ") : __("Matched")).appendTo(tr);
		}
	}

	function append_links(cell, doctype, names) {
		for (const name of names) {
			$("<a>", { href: frappe.utils.get_form_link(doctype, name) })
				.addClass("d-block")
				.text(name)
				.appendTo(cell);
		}
	}
};
