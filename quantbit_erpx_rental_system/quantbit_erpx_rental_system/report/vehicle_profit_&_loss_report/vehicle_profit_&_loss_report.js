// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Your Company
// Vehicle Profit & Loss Report — Filters
// File path: your_app/your_app/report/vehicle_profit_and_loss_report/vehicle_profit_and_loss_report.js

frappe.query_reports["Vehicle Profit & Loss Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date (Date Out)"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date (Date Out)"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "vehicle",
			label: __("Vehicle / Plate"),
			fieldtype: "Link",
			options: "Vehicle Master",
		},
		{
			fieldname: "vehicle_category",
			label: __("Vehicle Category"),
			fieldtype: "Data",
			// If you have a Vehicle Category doctype, change to:
			// fieldtype: "Link", options: "Vehicle Category",
		},
		{
			fieldname: "contract_type",
			label: __("Contract Type"),
			fieldtype: "Select",
			options: "\nDaily\nWeekly\nMonthly\nCorporate",
		},
		{
			fieldname: "contract_status",
			label: __("Contract Status"),
			fieldtype: "Select",
			options: "\nActive\nExtended\nPending Return\nClosed\nCancelled",
			default: "Closed",   // P&L makes most sense on closed/completed contracts
		},
	],

	// ── Highlight the TOTAL row bold at the bottom ──────────────────────────
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.bold) {
			value = `<strong>${value}</strong>`;
		}

		// Highlight gross_revenue green, net_due orange if > 0
		if (data && !data.bold) {
			if (column.fieldname === "gross_revenue" && data.gross_revenue > 0) {
				value = `<span style="color:#2E7D32;font-weight:600;">${value}</span>`;
			}
			if (column.fieldname === "net_due" && data.net_due > 0) {
				value = `<span style="color:#E65100;font-weight:600;">${value}</span>`;
			}
			if (column.fieldname === "rev_per_day" && data.rev_per_day > 0) {
				value = `<span style="color:#1565C0;font-weight:500;">${value}</span>`;
			}
		}

		return value;
	},

	// ── On load: auto-run with defaults ─────────────────────────────────────
	onload: function (report) {
		report.page.add_inner_button(__("Export to Excel"), function () {
			report.export_report("Excel");
		});
	},
};