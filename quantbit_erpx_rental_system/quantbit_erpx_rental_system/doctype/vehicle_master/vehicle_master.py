# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today, getdate


class VehicleMaster(Document):

    def validate(self):
        self.validate_plate()  # validate plate number
        self.validate_duplicate_plate()  # 🔥 prevent duplicate
        self.validate_year()  # validate year
        self.validate_odometer()  # validate km
        self.validate_dates()  # expiry checks
        self.validate_finance()  # loan validation

    # ---------------- PLATE ---------------- #

    def validate_plate(self):
        if not self.plate_number:
            frappe.throw(_("Plate Number is required"))

        # clean spaces
        self.plate_number = self.plate_number.strip().upper()

    # 🔥 prevent duplicate vehicle
    def validate_duplicate_plate(self):
        if self.plate_number:
            existing = frappe.db.exists(
                "Vehicle Master",
                {
                    "plate_number": self.plate_number,
                    "name": ["!=", self.name]
                }
            )

            if existing:
                frappe.throw(_("Vehicle with this Plate Number already exists"))

    # ---------------- YEAR ---------------- #

    def validate_year(self):
        if self.year_of_manufacture:
            current_year = getdate(today()).year

            if self.year_of_manufacture > current_year:
                frappe.throw(_("Invalid manufacturing year"))

            if self.year_of_manufacture < 1980:
                frappe.throw(_("Year seems too old, please verify"))

    # ---------------- ODOMETER ---------------- #

    def validate_odometer(self):
        if self.current_odometer_km is not None and self.current_odometer_km < 0:
            frappe.throw(_("Odometer cannot be negative"))

    # ---------------- DATES ---------------- #

    def validate_dates(self):
        today_date = getdate(today())

        if self.mulkiya_expiry_date:
            if getdate(self.mulkiya_expiry_date) < today_date:
                frappe.msgprint(_("Mulkiya expired"))

        if self.insurance_expiry_date:
            if getdate(self.insurance_expiry_date) < today_date:
                frappe.msgprint(_("Insurance expired"))

    # ---------------- FINANCE ---------------- #

    def validate_finance(self):
        if self.loan_start_date and self.loan_end_date:
            if getdate(self.loan_end_date) <= getdate(self.loan_start_date):
                frappe.throw(_("Loan end date must be after start date"))