# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.

import frappe
from frappe.model.document import Document
from frappe import _


class RateCard(Document):

    def validate(self):
        self.validate_rates()          # at least one rate required
        self.validate_km()             # km validation
        self.validate_charges()        # extra km charges validation
        self.validate_rate_km_mapping()  # 🔥 consistency check
        self.validate_duplicate()      # 🔥 prevent duplicates

    # ---------------- RATE VALIDATION ---------------- #

    def validate_rates(self):
        if not (self.daily_rate or self.weekly_rate or self.monthly_rate):
            frappe.throw(_("At least one rate (Daily/Weekly/Monthly) must be set"))

    # ---------------- KM VALIDATION ---------------- #

    def validate_km(self):
        if self.free_km_per_day is not None and self.free_km_per_day < 0:
            frappe.throw(_("Invalid KM per day"))

        if self.free_km_per_week is not None and self.free_km_per_week < 0:
            frappe.throw(_("Invalid KM per week"))

        if self.free_km_per_month is not None and self.free_km_per_month < 0:
            frappe.throw(_("Invalid KM per month"))

    # ---------------- CHARGES VALIDATION ---------------- #

    def validate_charges(self):
        if self.excess_km_charge_daily is not None and self.excess_km_charge_daily < 0:
            frappe.throw(_("Invalid daily excess charge"))

        if self.excess_km_charge_weekly is not None and self.excess_km_charge_weekly < 0:
            frappe.throw(_("Invalid weekly excess charge"))

        if self.excess_km_charge_monthly is not None and self.excess_km_charge_monthly < 0:
            frappe.throw(_("Invalid monthly excess charge"))

    # 🔥 IMPORTANT: rate + km consistency
    def validate_rate_km_mapping(self):

        if self.daily_rate and self.free_km_per_day is None:
            frappe.throw(_("Set Free KM per Day for Daily Rate"))

        if self.weekly_rate and self.free_km_per_week is None:
            frappe.throw(_("Set Free KM per Week for Weekly Rate"))

        if self.monthly_rate and self.free_km_per_month is None:
            frappe.throw(_("Set Free KM per Month for Monthly Rate"))

    # 🔥 prevent duplicate rate card per category
    def validate_duplicate(self):

        if self.vehicle_category:
            existing = frappe.db.exists(
                "Rate Card",
                {
                    "vehicle_category": self.vehicle_category,
                    "name": ["!=", self.name]
                }
            )

            if existing:
                frappe.throw(_("Rate Card already exists for this Vehicle Category"))