frappe.listview_settings["Payment Request"] = Object.assign(
	{},
	frappe.listview_settings["Payment Request"] || {},
	{
		filters: [["status", "!=", "Paid"]],
	}
);
