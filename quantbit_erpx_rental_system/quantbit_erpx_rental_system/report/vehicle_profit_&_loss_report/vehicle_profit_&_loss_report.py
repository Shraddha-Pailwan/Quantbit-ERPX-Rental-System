# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    return columns, data, None, chart, report_summary


# ─────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────
def get_columns(filters):
    cols = [
        {
            "label": _("Vehicle / Plate"),
            "fieldname": "vehicle",
            "fieldtype": "Link",
            "options": "Vehicle Master",
            "width": 130,
        },
        {
            "label": _("Make / Model"),
            "fieldname": "vehicle_make_model",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Category"),
            "fieldname": "vehicle_category",
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "label": _("Contracts"),
            "fieldname": "contract_count",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Total Days Rented"),
            "fieldname": "total_days",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Base Rental (OMR)"),
            "fieldname": "base_rental_amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Excess KM Rev (OMR)"),
            "fieldname": "excess_km_charges",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150,
        },
        {
            "label": _("Late Return Rev (OMR)"),
            "fieldname": "late_return_charge",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 155,
        },
        {
            "label": _("Damage / Penalty (OMR)"),
            "fieldname": "damage_charges",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 160,
        },
        {
            "label": _("Traffic Fines Recovered (OMR)"),
            "fieldname": "traffic_fines_total",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 195,
        },
        {
            "label": _("Delivery Revenue (OMR)"),
            "fieldname": "delivery_charge",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 160,
        },
        {
            "label": _("Gross Revenue (OMR)"),
            "fieldname": "gross_revenue",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150,
        },
        {
            "label": _("VAT Collected (OMR)"),
            "fieldname": "vat_amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 145,
        },
        {
            "label": _("Net Revenue ex-VAT (OMR)"),
            "fieldname": "net_revenue",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 175,
        },
        {
            "label": _("Advance Applied (OMR)"),
            "fieldname": "advance_applied",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 155,
        },
        {
            "label": _("Net Due (OMR)"),
            "fieldname": "net_due",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "label": _("Rev / Day (OMR)"),
            "fieldname": "rev_per_day",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
    ]
    return cols


# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
def get_data(filters):
    conditions = build_conditions(filters)

    query = """
        SELECT
            rc.vehicle,
            rc.vehicle_make_model,
            rc.vehicle_category,
            COUNT(rc.name)                              AS contract_count,
            SUM(IFNULL(rc.total_days, 0))               AS total_days,
            SUM(IFNULL(rc.base_rental_amount, 0))       AS base_rental_amount,
            SUM(IFNULL(rc.excess_km_charges, 0))        AS excess_km_charges,
            SUM(IFNULL(rc.late_return_charge, 0))       AS late_return_charge,
            SUM(IFNULL(rc.damage_charges, 0))           AS damage_charges,
            SUM(IFNULL(rc.total_fines_on_contract, 0))  AS traffic_fines_total,
            SUM(IFNULL(rc.delivery_charge, 0))          AS delivery_charge,
            SUM(IFNULL(rc.vat_amount, 0))               AS vat_amount,
            SUM(IFNULL(rc.advance_applied, 0))          AS advance_applied,
            SUM(IFNULL(rc.net_due, 0))                  AS net_due
        FROM
            `tabRental Contract` rc
        WHERE
            rc.docstatus = 1
            {conditions}
        GROUP BY
            rc.vehicle, rc.vehicle_make_model, rc.vehicle_category
        ORDER BY
            SUM(IFNULL(rc.base_rental_amount, 0)) DESC
    """.format(conditions=conditions)

    data = frappe.db.sql(query, filters, as_dict=True)

    result = []
    total_row = {
        "vehicle": "TOTAL",
        "vehicle_make_model": "",
        "vehicle_category": "",
        "contract_count": 0,
        "total_days": 0,
        "base_rental_amount": 0,
        "excess_km_charges": 0,
        "late_return_charge": 0,
        "damage_charges": 0,
        "traffic_fines_total": 0,
        "delivery_charge": 0,
        "gross_revenue": 0,
        "vat_amount": 0,
        "net_revenue": 0,
        "advance_applied": 0,
        "net_due": 0,
        "rev_per_day": 0,
        "bold": 1,
    }

    for row in data:
        gross = (
            flt(row.base_rental_amount)
            + flt(row.excess_km_charges)
            + flt(row.late_return_charge)
            + flt(row.damage_charges)
            + flt(row.traffic_fines_total)
            + flt(row.delivery_charge)
        )
        net_revenue = gross - flt(row.vat_amount)
        rev_per_day = gross / flt(row.total_days) if flt(row.total_days) > 0 else 0

        row.update(
            {
                "gross_revenue": gross,
                "net_revenue": net_revenue,
                "rev_per_day": rev_per_day,
            }
        )
        result.append(row)

        # accumulate totals
        for key in [
            "contract_count", "total_days", "base_rental_amount",
            "excess_km_charges", "late_return_charge", "damage_charges",
            "traffic_fines_total", "delivery_charge", "vat_amount",
            "advance_applied", "net_due",
        ]:
            total_row[key] += flt(row.get(key, 0))
        total_row["gross_revenue"] += gross
        total_row["net_revenue"] += net_revenue

    if total_row["total_days"] > 0:
        total_row["rev_per_day"] = total_row["gross_revenue"] / total_row["total_days"]

    result.append(total_row)
    return result


# ─────────────────────────────────────────────
# FILTERS → SQL CONDITIONS
# ─────────────────────────────────────────────
def build_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += " AND rc.date_out >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND rc.date_out <= %(to_date)s"

    if filters.get("branch"):
        conditions += " AND rc.branch = %(branch)s"

    if filters.get("vehicle"):
        conditions += " AND rc.vehicle = %(vehicle)s"

    if filters.get("vehicle_category"):
        conditions += " AND rc.vehicle_category = %(vehicle_category)s"

    if filters.get("contract_type"):
        conditions += " AND rc.contract_type = %(contract_type)s"

    if filters.get("contract_status"):
        conditions += " AND rc.contract_status = %(contract_status)s"

    if filters.get("company"):
        conditions += " AND rc.company = %(company)s"

    return conditions


# ─────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────
def get_chart(data):
    # exclude the TOTAL row
    rows = [r for r in data if r.get("vehicle") != "TOTAL"][:15]  # top 15

    labels = [r["vehicle"] for r in rows]
    base_rental = [flt(r["base_rental_amount"]) for r in rows]
    excess_km = [flt(r["excess_km_charges"]) for r in rows]
    late_return = [flt(r["late_return_charge"]) for r in rows]
    penalties = [flt(r["damage_charges"]) + flt(r["traffic_fines_total"]) for r in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Base Rental"), "values": base_rental},
                {"name": _("Excess KM"), "values": excess_km},
                {"name": _("Late Return"), "values": late_return},
                {"name": _("Penalties & Fines"), "values": penalties},
            ],
        },
        "type": "bar",
        "barOptions": {"stacked": True},
        "fieldtype": "Currency",
        "colors": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"],
    }


# ─────────────────────────────────────────────
# REPORT SUMMARY CARDS (top KPI tiles)
# ─────────────────────────────────────────────
def get_report_summary(data):
    total_row = next((r for r in data if r.get("vehicle") == "TOTAL"), {})

    return [
        {
            "value": flt(total_row.get("gross_revenue")),
            "label": _("Total Gross Revenue (OMR)"),
            "datatype": "Currency",
            "currency": "OMR",
            "indicator": "Green",
        },
        {
            "value": flt(total_row.get("net_revenue")),
            "label": _("Net Revenue ex-VAT (OMR)"),
            "datatype": "Currency",
            "currency": "OMR",
            "indicator": "Green",
        },
        {
            "value": flt(total_row.get("vat_amount")),
            "label": _("VAT Collected (OMR)"),
            "datatype": "Currency",
            "currency": "OMR",
            "indicator": "Blue",
        },
        {
            "value": int(total_row.get("contract_count", 0)),
            "label": _("Total Contracts"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": flt(total_row.get("total_days")),
            "label": _("Total Days Rented"),
            "datatype": "Float",
            "indicator": "Blue",
        },
        {
            "value": flt(total_row.get("rev_per_day")),
            "label": _("Avg Revenue / Day (OMR)"),
            "datatype": "Currency",
            "currency": "OMR",
            "indicator": "Green",
        },
    ]