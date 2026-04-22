// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Rental Register"] = {
    "filters": [
		{
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "vehicle_status",
            label: "Vehicle Status",
            fieldtype: "Select",
            options: "\nAvailable\nOn Rent\nIn Workshop\nReserved\nRetired\nBlocked"
        },
        {
            fieldname: "vehicle",
            label: "Vehicle",
            fieldtype: "Link",
            options: "Vehicle Master"
        }
    ]
};
