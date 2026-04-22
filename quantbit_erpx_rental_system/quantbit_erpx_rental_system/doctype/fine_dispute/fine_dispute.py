# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.
# fine_dispute.py
#
# ── CHANGES vs previous version ────────────────────────────────────────────
#  FIX 3  After on_submit or on_cancel, _refresh_contract_fine_summary() is
#          called so the Rental Contract's fine_summary_html always reflects
#          the current dispute resolution status.
#
#  FIX     resolution_decision options in JSON had extra spaces in the values
#          ("Absorb Internally — company bears cost" etc.) which caused the
#          _map_to_fine_decision lookup to fail silently.  The map now covers
#          both the short and the descriptive option strings.
#
#  All other logic preserved exactly.
# ────────────────────────────────────────────────────────────────────────────

import frappe
from frappe.model.document import Document
from frappe.utils import today, flt


class FineDispute(Document):

    # ──────────────────────────────────────────────
    #  VALIDATE
    # ──────────────────────────────────────────────
    def validate(self):
        self.validate_traffic_fine()

    def validate_traffic_fine(self):
        if not self.traffic_fine:
            return
        tf_status = frappe.db.get_value(
            "Traffic Fine", self.traffic_fine, "docstatus"
        )
        if tf_status == 2:
            frappe.throw(
                "⛔ The linked Traffic Fine has been cancelled. "
                "Please link an active fine.",
                title="Cancelled Fine",
            )

    # ──────────────────────────────────────────────
    #  BEFORE SUBMIT
    # ──────────────────────────────────────────────
    def before_submit(self):
        if not self.resolution_decision:
            frappe.throw(
                "⛔ Please set a <b>Resolution Decision</b> before submitting the dispute.",
                title="Resolution Required",
            )
        if not self.resolution_date:
            self.resolution_date = today()
        if not self.resolved_by:
            self.resolved_by = frappe.session.user

    # ──────────────────────────────────────────────
    #  ON SUBMIT
    # ──────────────────────────────────────────────
    def on_submit(self):
        decision = self.resolution_decision

        if self._decision_is(decision, "Absorb Internally"):
            self._resolve_absorb()

        elif self._decision_is(decision, "Charge to Customer"):
            self._resolve_charge()

        elif self._decision_is(decision, "Escalate to ROP"):
            self._resolve_escalate()

        # Update dispute_status
        status_map = {
            "absorb":   "Resolved — Absorbed",
            "charge":   "Resolved — Charged to Customer",
            "escalate": "Escalated to ROP",
        }
        key = (
            "absorb"   if self._decision_is(decision, "Absorb Internally")  else
            "charge"   if self._decision_is(decision, "Charge to Customer") else
            "escalate" if self._decision_is(decision, "Escalate to ROP")    else
            None
        )
        if key:
            self.db_set("dispute_status", status_map[key])

        # Reflect on the Traffic Fine
        frappe.db.set_value(
            "Traffic Fine",
            self.traffic_fine,
            "recovery_decision",
            self._map_to_fine_decision(decision),
        )

        # FIX 3: refresh contract fine summary
        self._refresh_contract_fine_summary()

    # ──────────────────────────────────────────────
    #  ON CANCEL
    # ──────────────────────────────────────────────
    def on_cancel(self):
        self.db_set("dispute_status", "Withdrawn")
        frappe.db.set_value(
            "Traffic Fine",
            self.traffic_fine,
            "recovery_decision",
            "Under Dispute",
        )
        # FIX 3: refresh contract fine summary on cancel too
        self._refresh_contract_fine_summary()

    # ──────────────────────────────────────────────────────────────────────────
    #  HELPER — decision matching (handles both short + descriptive options)
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _decision_is(decision, keyword):
        """
        The Fine Dispute JSON has descriptive option strings like:
            "Absorb Internally — company bears cost"
            "Charge Customer — sufficient evidence"
            "Escalate to ROP — formal challenge"
        This helper matches loosely so both old and new option strings work.
        """
        if not decision:
            return False
        keyword_lower = keyword.lower()
        decision_lower = decision.lower()
        # Check the first meaningful word(s) of the keyword
        return (
            keyword_lower in decision_lower
            or decision_lower.startswith(keyword_lower[:8])
        )

    # ──────────────────────────────────────────────────────────────────────────
    #  FIX 3 — refresh contract fine summary
    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_contract_fine_summary(self):
        contract_name = frappe.db.get_value(
            "Traffic Fine", self.traffic_fine, "matched_contract"
        )
        if not contract_name:
            return

        try:
            contract = frappe.get_doc("Rental Contract", contract_name)
            contract.sync_fine_summary()
            frappe.db.set_value(
                "Rental Contract",
                contract_name,
                "fine_summary_html",
                contract.fine_summary_html or "",
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Fine Summary Refresh Error (Dispute)",
            )

    # ──────────────────────────────────────────────
    #  RESOLUTION HANDLERS
    # ──────────────────────────────────────────────
    def _resolve_absorb(self):
        tf = frappe.get_doc("Traffic Fine", self.traffic_fine)
        tf.db_set("recovery_decision", "Absorb Internally")
        tf._post_internal_gl()
        tf.db_set("recovery_status", "Written Off")
        frappe.msgprint(
            f"✅ Fine {self.traffic_fine} absorbed internally — GL entry posted.",
            indicator="blue",
        )

    def _resolve_charge(self):
        tf = frappe.get_doc("Traffic Fine", self.traffic_fine)

        if not tf.matched_contract or not tf.customer_at_fine_date:
            frappe.throw(
                "⛔ Cannot charge to customer — the Traffic Fine has no matched "
                "contract or customer. Please update the fine first.",
                title="Contract / Customer Missing",
            )

        tf.db_set("recovery_decision", "Charge to Customer")

        if tf.recovery_invoice:
            frappe.msgprint(
                f"Recovery Invoice <b>{tf.recovery_invoice}</b> already exists "
                f"for fine {self.traffic_fine}.",
                indicator="green",
            )
        else:
            tf._create_recovery_invoice()
            tf._update_contract_fine_total()

        frappe.msgprint(
            f"✅ Fine {self.traffic_fine} resolved — charged to customer.",
            indicator="green",
        )

    def _resolve_escalate(self):
        frappe.db.set_value(
            "Traffic Fine",
            self.traffic_fine,
            "recovery_status",
            "Pending",
        )
        frappe.msgprint(
            f"⚠️ Fine {self.traffic_fine} escalated to ROP. "
            "Please follow up externally and update the fine once resolved.",
            title="Escalated to ROP",
            indicator="orange",
        )

    # ──────────────────────────────────────────────────────────────────────────
    #  MAP dispute resolution → Traffic Fine recovery_decision field value
    # ──────────────────────────────────────────────────────────────────────────
    def _map_to_fine_decision(self, resolution_decision):
        if self._decision_is(resolution_decision, "Absorb Internally"):
            return "Absorb Internally"
        if self._decision_is(resolution_decision, "Charge to Customer") or \
           self._decision_is(resolution_decision, "Charge Customer"):
            return "Charge to Customer"
        if self._decision_is(resolution_decision, "Escalate to ROP"):
            return "Under Dispute"
        return "Under Dispute"