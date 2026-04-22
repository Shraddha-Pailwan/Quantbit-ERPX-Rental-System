# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Customer Type", "fieldname": "customer_type", "width": 150},
        {"label": "KYC Status", "fieldname": "kyc_status", "width": 130},
        {"label": "Full Name", "fieldname": "full_name", "width": 160},
        {"label": "Mobile", "fieldname": "mobile_number", "width": 130},
        {"label": "Email", "fieldname": "email_address", "width": 180},
        {"label": "Nationality", "fieldname": "nationality", "width": 130},
        {"label": "Licence No", "fieldname": "licence_number", "width": 140},
        {"label": "Licence Expiry", "fieldname": "licence_expiry_date", "fieldtype": "Date", "width": 130},
        {"label": "Company Name", "fieldname": "company_name", "width": 160},
        {"label": "CR Number", "fieldname": "cr_number", "width": 140},
    ]


def get_conditions(filters):
    conditions = ""

    if filters:
        if filters.get("customer"):
            conditions += " AND ck.customer = %(customer)s"

        if filters.get("customer_type"):
            conditions += " AND ck.customer_type = %(customer_type)s"

        if filters.get("kyc_status"):
            conditions += " AND ck.kyc_status = %(kyc_status)s"

    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    query = f"""
        SELECT
            ck.customer,
            ck.customer_type,
            ck.kyc_status,
            ck.full_name,
            ck.mobile_number,
            ck.email_address,
            ck.nationality,
            ck.licence_number,
            ck.licence_expiry_date,
            ck.company_name,
            ck.cr_number

        FROM `tabCustomer KYC` ck

        WHERE ck.docstatus < 2
        {conditions}

        ORDER BY ck.customer ASC
    """

    return frappe.db.sql(query, filters, as_dict=1)