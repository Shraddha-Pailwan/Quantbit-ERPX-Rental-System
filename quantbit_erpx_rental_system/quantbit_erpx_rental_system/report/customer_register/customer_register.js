// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Register"] = {
    "filters": [
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "customer_type",
            label: "Customer Type",
            fieldtype: "Select",
            options: "\nIndividual\nCorporate\nBroker / Travel Agency"
        },
        {
            fieldname: "kyc_status",
            label: "KYC Status",
            fieldtype: "Select",
            options: "\nActive\nBlacklisted\nSuspended\nUnder Review"
        }
    ]
};