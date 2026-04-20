# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.

import frappe
from frappe.model.document import Document


class AdvancePaymentEntry(Document):

    def validate(self):
        self.validate_amount()  # check amount
        self.validate_customer()  # check customer
        self.validate_contract()  # check contract

    def validate_amount(self):
        if not self.advance_amount or self.advance_amount <= 0:
            frappe.throw("Advance amount must be greater than zero")  # amount check

    def validate_customer(self):
        if not self.customer:
            frappe.throw("Customer is required")  # customer check

    def validate_contract(self):
        if not self.rental_contract:
            frappe.throw("Rental Contract is required")  # contract check

    def on_submit(self):

        company = frappe.defaults.get_user_default("Company")  # get company

        if not self.bank_account:
            frappe.throw("Bank / Cash Account is required")  # validate bank

        je = frappe.new_doc("Journal Entry")  # create JE
        je.voucher_type = "Journal Entry"  # set type
        je.company = company  # set company
        je.posting_date = self.payment_date  # set date
        je.remark = f"Advance received for Rental Contract {self.rental_contract}"  # remark

        je.append("accounts", {
            "account": self.bank_account,
            "debit_in_account_currency": self.advance_amount,
            "credit_in_account_currency": 0
        })  # debit bank

        je.append("accounts", {
            "account": "Advance Rent Received",
            "party_type": "Customer",
            "party": self.customer,
            "credit_in_account_currency": self.advance_amount,
            "debit_in_account_currency": 0,
            "reference_type": "Rental Contract",
            "reference_name": self.rental_contract
        })  # credit liability

        je.insert(ignore_permissions=True)  # insert JE
        je.submit()  # submit JE

        self.gl_journal_entry = je.name  # link JE
        self.balance_remaining = self.advance_amount  # set balance