// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Your Company
// Vehicle Utilisation Report — Filters
// File path: your_app/your_app/report/vehicle_utilisation_report/vehicle_utilisation_report.js

frappe.query_reports["Vehicle Utilisation Report"] = {
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
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
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
		},
		{
			fieldname: "contract_type",
			label: __("Contract Type"),
			fieldtype: "Select",
			options: "\nDaily\nWeekly\nMonthly\nCorporate",
		},
	],

	// ── Row colour coding based on utilisation status ────────────────────────
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.bold) {
			// Total row — bold everything
			value = `<strong>${value}</strong>`;
			return value;
		}

		if (!data) return value;

		// Colour the utilisation % cell
		if (column.fieldname === "utilisation_pct") {
			const pct = data.utilisation_pct || 0;
			let color = "#C62828"; // red — low
			if (pct >= 80) color = "#2E7D32";       // green — high
			else if (pct >= 50) color = "#F57F17";  // amber — medium
			value = `<span style="color:${color};font-weight:700;">${value}</span>`;
		}

		// Colour idle days red if they are high
		if (column.fieldname === "idle_days" && data.idle_days > 15) {
			value = `<span style="color:#C62828;font-weight:600;">${value}</span>`;
		}

		// RevPAD — blue
		if (column.fieldname === "revpad" && data.revpad > 0) {
			value = `<span style="color:#1565C0;font-weight:600;">${value}</span>`;
		}

		return value;
	},

	onload: function (report) {
		// Quick-set buttons for common periods
		report.page.add_inner_button(__("This Month"), function () {
			const today = frappe.datetime.get_today();
			const from = frappe.datetime.month_start();
			report.set_filter_value("from_date", from);
			report.set_filter_value("to_date", today);
			report.refresh();
		});

		report.page.add_inner_button(__("Last Month"), function () {
			const from = frappe.datetime.add_months(frappe.datetime.month_start(), -1);
			const to = frappe.datetime.add_days(frappe.datetime.month_start(), -1);
			report.set_filter_value("from_date", from);
			report.set_filter_value("to_date", to);
			report.refresh();
		});

		report.page.add_inner_button(__("This Year"), function () {
			const from = frappe.datetime.year_start();
			const to = frappe.datetime.get_today();
			report.set_filter_value("from_date", from);
			report.set_filter_value("to_date", to);
			report.refresh();
		});

		report.page.add_inner_button(__("Export to Excel"), function () {
			report.export_report("Excel");
		});
	},
};
