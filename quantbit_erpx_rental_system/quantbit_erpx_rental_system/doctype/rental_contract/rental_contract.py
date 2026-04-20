# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.

import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff


class RentalContract(Document):

    def validate(self):
        self.set_customer_kyc()
        self.set_vehicle_status_snapshot()
        self.set_rate_from_card()

        self.validate_customer_kyc()
        self.validate_licence()
        self.validate_vehicle()
        self.validate_dates()
        self.validate_km()
        self.validate_rate_card()

        self.set_total_days()
        self.set_km_used()
        self.calculate_charges()

        self.update_contract_status()
        self.set_flags()
        self.set_rate_type()

    # ---------------- BASIC ---------------- #

    def set_customer_kyc(self):
        # Auto link customer KYC
        if self.customer and not self.customer_kyc:
            self.customer_kyc = frappe.db.get_value("Customer KYC", {"customer": self.customer}, "name")

    def set_vehicle_status_snapshot(self):
        # Capture vehicle status at contract time
        if self.vehicle:
            self.vehicle_status_at_contract = frappe.db.get_value("Vehicle Master", self.vehicle, "vehicle_status")

    # ---------------- RATE ---------------- #

    def set_rate_from_card(self):
        # Set rate based on contract type
        if not self.contract_type or not self.rate_card:
            return

        rc = frappe.get_doc("Rate Card", self.rate_card)

        if self.contract_type == "Daily":
            self.rate = rc.daily_rate or 0

        elif self.contract_type == "Weekly":
            self.rate = rc.weekly_rate or 0

        elif self.contract_type == "Monthly":
            self.rate = rc.monthly_rate or 0

    # ---------------- VALIDATIONS (SOFT) ---------------- #

    def validate_customer_kyc(self): pass
    def validate_licence(self): pass
    def validate_vehicle(self): pass
    def validate_dates(self): pass
    def validate_km(self): pass
    def validate_rate_card(self): pass

    # ---------------- CALCULATIONS ---------------- #

    def set_total_days(self):
        # Calculate rental duration
        if self.date_out:
            end_date = self.actual_return_date or self.date_return
            if end_date:
                self.total_days = date_diff(end_date, self.date_out) + 1

    def set_km_used(self):
        # Calculate KM used
        if self.km_out is not None and self.km_return is not None:
            self.km_used = self.km_return - self.km_out

    def calculate_charges(self):
        # Main billing logic
        rate = self.rate or 0
        total_days = self.total_days or 0

        self.base_rental_amount = rate * total_days  # Base rental

        self.excess_km_charges = 0

        # Daily logic
        if self.contract_type == "Daily":
            free_km = (self.free_km_per_day or 0) * total_days
            extra_km_rate = self.excess_km_charge_daily or 0

        # Weekly logic
        elif self.contract_type == "Weekly":
            weeks = total_days // 7
            free_km = (self.free_km_per_week or 0) * weeks
            extra_km_rate = self.excess_km_charge_daily or 0

        # Monthly logic
        elif self.contract_type == "Monthly":
            months = total_days // 30
            free_km = (self.free_km_per_month or 0) * months
            extra_km_rate = self.excess_km_charge_monthly or 0

        else:
            free_km = 0
            extra_km_rate = 0

        # Excess KM calculation
        if self.km_used is not None and self.km_used > free_km:
            self.excess_km_charges = (self.km_used - free_km) * extra_km_rate

        # Final totals
        self.gross_amount = self.base_rental_amount + self.excess_km_charges
        vat = self.get_vat_rate()
        self.vat_amount = (self.gross_amount * vat) / 100
        self.total_amount = self.gross_amount + self.vat_amount

    # ---------------- STATUS ---------------- #

    def update_contract_status(self):
        # Update contract lifecycle
        if self.actual_return_date and self.km_return is not None:
            self.contract_status = "Closed"
        else:
            self.contract_status = "Active"

    def set_flags(self):
        # Set flags for UI logic
        self.is_active = 1 if self.contract_status == "Active" else 0
        self.is_closed = 1 if self.contract_status == "Closed" else 0

    def set_rate_type(self):
        # Store rate type used
        self.rate_type_used = self.contract_type

    # ---------------- VAT ---------------- #

    def get_vat_rate(self):
        # Fetch VAT from configuration
        vat = frappe.db.get_value(
            "VAT Configuration",
            {"company": self.company, "is_active": 1},
            "vat_rate"
        )
        return vat or 0

    # ---------------- EVENTS ---------------- #

    def on_submit(self):
        # Mark vehicle as rented
        frappe.db.set_value("Vehicle Master", self.vehicle, {
            "vehicle_status": "On Rent",
            "current_contract": self.name
        })

    def on_update_after_submit(self):
        # Handle return and invoice creation
        self.update_contract_status()
        self.db_set("contract_status", self.contract_status)

        frappe.msgprint(f"Contract Status: {self.contract_status}")

        if self.contract_status == "Closed":

            frappe.db.set_value("Vehicle Master", self.vehicle, {
                "vehicle_status": "Available",
                "current_contract": None
            })

            if not self.sales_invoice:
                frappe.msgprint("Creating Sales Invoice...")
                self.create_sales_invoice()

    def on_cancel(self):
        # Reset vehicle on cancel
        frappe.db.set_value("Vehicle Master", self.vehicle, {
            "vehicle_status": "Available",
            "current_contract": None
        })
        self.contract_status = "Cancelled"

    # ---------------- INVOICE ---------------- #

    def create_sales_invoice(self):
        # Create ERPNext Sales Invoice
        try:
            si = frappe.new_doc("Sales Invoice")
            si.customer = self.customer
            si.company = self.company
            si.posting_date = today()
            si.rental_contract = self.name
            # Fetch income account
            income_account = frappe.db.get_value(
                "Account",
                {"company": self.company, "root_type": "Income", "is_group": 0},
                "name"
            )
            if not income_account:
                frappe.throw("No Income Account found")

            # Fetch VAT account
            vat_account = frappe.db.get_value(
                "Account",
                {"company": self.company, "account_type": "Tax", "is_group": 0},
                "name"
            )

            # Rental item
            si.append("items", {
                "item_name": "Vehicle Rental",
                "qty": self.total_days or 1,
                "rate": self.rate or 0,
                "income_account": income_account
            })

            # Extra KM item
            if self.excess_km_charges:
                si.append("items", {
                    "item_name": "Extra KM",
                    "qty": 1,
                    "rate": self.excess_km_charges,
                    "income_account": income_account
                })

            # VAT tax
            vat = self.get_vat_rate()
            if vat and vat_account:
                si.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": vat_account,
                    "rate": vat,
                    "description": f"VAT @ {vat}%"
                })

            # Insert + submit
            si.insert(ignore_permissions=True)
            si.submit()

            frappe.db.commit()

            # Link invoice to contract
            self.sales_invoice = si.name
            self.save(ignore_permissions=True)
            self.reload()

            frappe.msgprint(f"✅ Invoice Created: {si.name}")

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Rental Invoice Error")
            frappe.throw(f"Invoice Creation Failed: {str(e)}")