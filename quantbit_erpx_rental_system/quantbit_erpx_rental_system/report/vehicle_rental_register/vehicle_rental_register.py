# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle Master", "width": 140},
        {"label": "Plate Number", "fieldname": "plate_number", "width": 130},
        {"label": "Vehicle Status", "fieldname": "vehicle_status", "width": 120},
        {"label": "Make", "fieldname": "make", "width": 120},
        {"label": "Model", "fieldname": "model", "width": 120},
        {"label": "Customer", "fieldname": "customer", "width": 150},
        {"label": "Latest Contract", "fieldname": "contract", "fieldtype": "Link", "options": "Rental Contract", "width": 150},
        {"label": "Expected Return", "fieldname": "expected_return_date", "fieldtype": "Date", "width": 130},
        {"label": "Odometer (KM)", "fieldname": "odometer", "width": 120},
    ]


def get_conditions(filters):
    conditions = ""

    if filters:
        if filters.get("vehicle"):
            conditions += " AND vm.name = %(vehicle)s"

        if filters.get("vehicle_status"):
            conditions += " AND vm.vehicle_status = %(vehicle_status)s"

    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    query = f"""
        SELECT
            vm.name as vehicle,
            vm.plate_number,
            vm.vehicle_status,
            vm.make,
            vm.model,
            rc.customer,
            rc.name as contract,
            vm.expected_return_date,
            vm.current_odometer_km as odometer

        FROM `tabVehicle Master` vm

        LEFT JOIN `tabRental Contract` rc
            ON rc.name = (
                SELECT rc2.name
                FROM `tabRental Contract` rc2
                WHERE rc2.vehicle = vm.name
                ORDER BY rc2.creation DESC
                LIMIT 1
            )

        WHERE vm.docstatus < 2
        {conditions}

        ORDER BY vm.name ASC
    """

    return frappe.db.sql(query, filters, as_dict=1)