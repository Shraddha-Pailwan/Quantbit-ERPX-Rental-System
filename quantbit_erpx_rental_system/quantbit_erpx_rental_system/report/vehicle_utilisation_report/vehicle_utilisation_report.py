# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, date_diff, getdate


def execute(filters=None):
    filters = filters or {}
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data, filters)
    return columns, data, None, chart, report_summary


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
def validate_filters(filters):
    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters["from_date"]) > getdate(filters["to_date"]):
            frappe.throw(_("From Date cannot be greater than To Date"))


# ─────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────
def get_columns():
    return [
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
            "label": _("Branch"),
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 110,
        },
        {
            "label": _("Period Days"),
            "fieldname": "period_days",
            "fieldtype": "Int",
            "width": 105,
        },
        {
            "label": _("Contracts"),
            "fieldname": "contract_count",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Days Rented"),
            "fieldname": "days_rented",
            "fieldtype": "Float",
            "width": 110,
        },
        {
            "label": _("Idle Days"),
            "fieldname": "idle_days",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": _("Utilisation %"),
            "fieldname": "utilisation_pct",
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "label": _("Gross Revenue (OMR)"),
            "fieldname": "gross_revenue",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150,
        },
        {
            "label": _("RevPAD (OMR)"),           # Revenue Per Available Day
            "fieldname": "revpad",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "label": _("RevPRD (OMR)"),           # Revenue Per Rented Day
            "fieldname": "revprd",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "label": _("Total KM Driven"),
            "fieldname": "total_km",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Avg KM / Contract"),
            "fieldname": "avg_km_per_contract",
            "fieldtype": "Float",
            "width": 145,
        },
        {
            "label": _("Extensions"),
            "fieldname": "extensions",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": _("Status"),
            "fieldname": "utilisation_status",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
def get_data(filters):
    period_days = (
        date_diff(filters.get("to_date"), filters.get("from_date")) + 1
        if filters.get("from_date") and filters.get("to_date")
        else 30
    )

    conditions = build_conditions(filters)

    query = """
        SELECT
            rc.vehicle,
            rc.vehicle_make_model,
            rc.vehicle_category,
            rc.branch,
            COUNT(rc.name)                                      AS contract_count,
            SUM(IFNULL(rc.total_days, 0))                       AS days_rented,
            SUM(IFNULL(rc.km_return, 0) - IFNULL(rc.km_out, 0)) AS total_km,
            SUM(IFNULL(rc.base_rental_amount, 0))               AS base_rental_amount,
            SUM(IFNULL(rc.excess_km_charges, 0))                AS excess_km_charges,
            SUM(IFNULL(rc.late_return_charge, 0))               AS late_return_charge,
            SUM(IFNULL(rc.damage_charges, 0))                   AS damage_charges,
            SUM(IFNULL(rc.total_fines_on_contract, 0))          AS traffic_fines_total,
            SUM(IFNULL(rc.delivery_charge, 0))                  AS delivery_charge,
            SUM(
                CASE WHEN rc.extension_1_date IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN rc.extension_2_date IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN rc.extension_3_date IS NOT NULL THEN 1 ELSE 0 END
            )                                                   AS extensions
        FROM
            `tabRental Contract` rc
        WHERE
            rc.docstatus = 1
            {conditions}
        GROUP BY
            rc.vehicle, rc.vehicle_make_model, rc.vehicle_category, rc.branch
        ORDER BY
            SUM(IFNULL(rc.total_days, 0)) DESC
    """.format(conditions=conditions)

    rows = frappe.db.sql(query, filters, as_dict=True)

    result = []
    total_row = {
        "vehicle": "TOTAL",
        "vehicle_make_model": "",
        "vehicle_category": "",
        "branch": "",
        "period_days": period_days,
        "contract_count": 0,
        "days_rented": 0,
        "idle_days": 0,
        "utilisation_pct": 0,
        "gross_revenue": 0,
        "revpad": 0,
        "revprd": 0,
        "total_km": 0,
        "avg_km_per_contract": 0,
        "extensions": 0,
        "utilisation_status": "",
        "bold": 1,
    }

    for row in rows:
        days_rented = flt(row.days_rented)
        idle_days = max(0, period_days - days_rented)
        utilisation_pct = (days_rented / period_days * 100) if period_days > 0 else 0

        gross = (
            flt(row.base_rental_amount)
            + flt(row.excess_km_charges)
            + flt(row.late_return_charge)
            + flt(row.damage_charges)
            + flt(row.traffic_fines_total)
            + flt(row.delivery_charge)
        )
        revpad = gross / period_days if period_days > 0 else 0
        revprd = gross / days_rented if days_rented > 0 else 0
        avg_km = flt(row.total_km) / flt(row.contract_count) if flt(row.contract_count) > 0 else 0

        # Status flag
        if utilisation_pct >= 80:
            status = "🟢 High"
        elif utilisation_pct >= 50:
            status = "🟡 Medium"
        elif utilisation_pct > 0:
            status = "🔴 Low"
        else:
            status = "⚫ Idle"

        row.update({
            "period_days": period_days,
            "idle_days": idle_days,
            "utilisation_pct": utilisation_pct,
            "gross_revenue": gross,
            "revpad": revpad,
            "revprd": revprd,
            "avg_km_per_contract": avg_km,
            "utilisation_status": status,
        })
        result.append(row)

        # Accumulate totals
        for key in ["contract_count", "days_rented", "total_km", "extensions"]:
            total_row[key] += flt(row.get(key, 0))
        total_row["gross_revenue"] += gross
        total_row["idle_days"] += idle_days

    # Fleet-level averages
    vehicle_count = len(rows)
    if vehicle_count > 0:
        total_available = period_days * vehicle_count
        total_row["utilisation_pct"] = (
            total_row["days_rented"] / total_available * 100
        ) if total_available > 0 else 0
        total_row["revpad"] = (
            total_row["gross_revenue"] / total_available
        ) if total_available > 0 else 0
        total_row["revprd"] = (
            total_row["gross_revenue"] / total_row["days_rented"]
        ) if total_row["days_rented"] > 0 else 0
        total_row["avg_km_per_contract"] = (
            total_row["total_km"] / total_row["contract_count"]
        ) if total_row["contract_count"] > 0 else 0

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

    if filters.get("company"):
        conditions += " AND rc.company = %(company)s"

    return conditions


# ─────────────────────────────────────────────
# CHART — Utilisation % per vehicle (top 15)
# ─────────────────────────────────────────────
def get_chart(data):
    rows = [r for r in data if r.get("vehicle") != "TOTAL"][:15]
    labels = [r["vehicle"] for r in rows]
    utilisation = [flt(r["utilisation_pct"]) for r in rows]
    revpad = [flt(r["revpad"]) for r in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Utilisation %"), "values": utilisation, "chartType": "bar"},
                {"name": _("RevPAD (OMR)"), "values": revpad, "chartType": "line"},
            ],
        },
        "type": "axis-mixed",
        "fieldtype": "Float",
        "colors": ["#1565C0", "#E65100"],
        "axisOptions": {
            "yAxes": [
                {"id": "left", "title": "Utilisation %"},
                {"id": "right", "title": "RevPAD (OMR)"},
            ]
        },
    }


# ─────────────────────────────────────────────
# SUMMARY CARDS
# ─────────────────────────────────────────────
def get_report_summary(data, filters):
    total_row = next((r for r in data if r.get("vehicle") == "TOTAL"), {})
    period_days = (
        date_diff(filters.get("to_date"), filters.get("from_date")) + 1
        if filters.get("from_date") and filters.get("to_date")
        else 30
    )

    return [
        {
            "value": flt(total_row.get("utilisation_pct"), 1),
            "label": _("Fleet Utilisation %"),
            "datatype": "Percent",
            "indicator": "Green" if flt(total_row.get("utilisation_pct")) >= 70 else "Orange",
        },
        {
            "value": flt(total_row.get("days_rented")),
            "label": _("Total Days Rented"),
            "datatype": "Float",
            "indicator": "Blue",
        },
        {
            "value": flt(total_row.get("idle_days")),
            "label": _("Total Idle Days"),
            "datatype": "Float",
            "indicator": "Red",
        },
        {
            "value": flt(total_row.get("gross_revenue")),
            "label": _("Total Gross Revenue (OMR)"),
            "datatype": "Currency",
            "currency": "OMR",
            "indicator": "Green",
        },
        {
            "value": flt(total_row.get("revpad")),
            "label": _("Fleet RevPAD (OMR)"),
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
    ]
