# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today

def execute(filters=None):
    if not filters:
        filters = {}

    # ✅ Default dates = TODAY
    if not filters.get("from_date"):
        filters["from_date"] = today()

    if not filters.get("to_date"):
        filters["to_date"] = today()

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Contract", "fieldname": "name", "fieldtype": "Link", "options": "Rental Contract", "width": 150},
        {"label": "Contract Date", "fieldname": "contract_date", "fieldtype": "Date", "width": 120},
        {"label": "Customer", "fieldname": "customer", "width": 150},
        {"label": "Vehicle", "fieldname": "vehicle", "width": 140},
        {"label": "Company", "fieldname": "company", "width": 150},
        {"label": "Branch", "fieldname": "branch", "width": 130},
        {"label": "Status", "fieldname": "contract_status", "width": 130},
        {"label": "Date Out", "fieldname": "date_out", "fieldtype": "Date", "width": 110},
        {"label": "Expected Return", "fieldname": "date_return", "fieldtype": "Date", "width": 130},
        {"label": "Actual Return", "fieldname": "actual_return_date", "fieldtype": "Date", "width": 130},
        {"label": "Total Amount", "fieldname": "total_amount", "width": 130},
        {"label": "Net Due", "fieldname": "net_due", "width": 130},
    ]


def get_conditions(filters):
    conditions = ""

    if filters.get("customer"):
        conditions += " AND rc.customer = %(customer)s"

    if filters.get("vehicle"):
        conditions += " AND rc.vehicle = %(vehicle)s"

    if filters.get("company"):
        conditions += " AND rc.company = %(company)s"

    if filters.get("branch"):
        conditions += " AND rc.branch = %(branch)s"

    if filters.get("contract_status"):
        conditions += " AND rc.contract_status = %(contract_status)s"

    # ✅ DATE FILTER LOGIC (MAIN)
    if filters.get("from_date"):
        conditions += " AND rc.contract_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND rc.contract_date <= %(to_date)s"

    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    query = f"""
        SELECT
            rc.name,
            rc.contract_date,
            rc.customer,
            rc.vehicle,
            rc.company,
            rc.branch,
            rc.contract_status,
            rc.date_out,
            rc.date_return,
            rc.actual_return_date,
            rc.total_amount,
            rc.net_due

        FROM `tabRental Contract` rc

        WHERE rc.docstatus < 2
        {conditions}

        ORDER BY rc.contract_date DESC
    """

    return frappe.db.sql(query, filters, as_dict=1)
