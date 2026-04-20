# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.

import frappe
from frappe.model.document import Document
from frappe import _


class VATConfiguration(Document):

    def validate(self):
        self.validate_rate()  # check vat rate
        self.validate_accounts()  # check accounts
        self.validate_single_active()  # ensure one active config
        self.validate_country_rate_logic()  # country specific logic

    def validate_rate(self):
        if not self.vat_rate or self.vat_rate <= 0:
            frappe.throw(_("VAT rate must be greater than zero"))  # rate check

    def validate_accounts(self):
        if not self.vat_output_account:
            frappe.throw(_("VAT Output Account is required"))  # output account check

    def validate_single_active(self):
        if self.is_active:
            existing = frappe.db.exists(
                "VAT Configuration",
                {
                    "company": self.company,
                    "is_active": 1,
                    "name": ["!=", self.name]
                }
            )
            if existing:
                frappe.throw(_("Only one active VAT Configuration allowed per company"))  # single active

    def validate_country_rate_logic(self):
        if self.country == "Oman" and self.vat_rate != 5:
            frappe.msgprint(_("Oman standard VAT is 5%"))  # oman hint
        if self.country == "Saudi Arabia" and self.vat_rate != 15:
            frappe.msgprint(_("Saudi Arabia standard VAT is 15%"))  # saudi hint