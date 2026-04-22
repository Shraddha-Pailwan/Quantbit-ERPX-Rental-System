// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Rental Summary"] = {
    "filters": [
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "vehicle",
            label: "Vehicle",
            fieldtype: "Link",
            options: "Vehicle Master"
        },
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "branch",
            label: "Branch",
            fieldtype: "Link",
            options: "Branch"
        },
        {
            fieldname: "contract_status",
            label: "Contract Status",
            fieldtype: "Select",
            options: "\nDraft\nActive\nExtended\nPending Return\nClosed\nCancelled"
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date"
        }
    ]
};