# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.
# handover_checklist.py  —  Pre-Delivery & Post-Return with damage comparison

import frappe
from frappe.model.document import Document
from frappe.utils import today, flt


# ─────────────────────────────────────────────────────────────────────────────
#  ACCESSORY FIELDS  — all 12 check fields on the checklist
#  Used for pre→post comparison to detect missing items
# ─────────────────────────────────────────────────────────────────────────────
ACCESSORY_FIELDS = [
    ("acc_tyre_tread",      "Tyre Tread"),
    ("acc_spare_tyre",      "Spare Tyre"),
    ("acc_tools_jack",      "Tools & Jack"),
    ("acc_car_documents",   "Car Documents"),
    ("acc_radio",           "Radio / Infotainment"),
    ("acc_ac_working",      "A/C Working"),
    ("acc_floor_mats",      "Floor Mats"),
    ("acc_sunshade",        "Sunshade"),
    ("acc_usb_charger",     "USB Charger"),
    ("acc_vehicle_manual",  "Vehicle Manual"),
    ("acc_fuel_card",       "Fuel Card"),
    ("acc_parking_card",    "Parking Card"),
]

# Panel fields — used to detect new damage between pre and post
PANEL_FIELDS = [
    "panel_front_bumper", "panel_rear_bumper",
    "panel_left_front_door", "panel_left_rear_door",
    "panel_right_front_door", "panel_right_rear_door",
    "panel_bonnet", "panel_boot",
    "panel_front_windscreen", "panel_rear_windscreen",
    "panel_left_mirror", "panel_right_mirror",
    "panel_roof", "panel_left_sills", "panel_right_sills",
    "panel_interior_cabin",
]

OK_VALUES = {"OK"}   # values that count as "no damage"


class HandoverChecklist(Document):

    # ─────────────────────────────────────────────
    #  VALIDATE
    # ─────────────────────────────────────────────
    def validate(self):
        self._block_duplicate()
        if self.checklist_type == "Post-Return":
            self._compare_with_pre_delivery()

    def _block_duplicate(self):
        """One submitted checklist of each type per contract."""
        if frappe.db.exists("Handover Checklist", {
            "rental_contract": self.rental_contract,
            "checklist_type": self.checklist_type,
            "docstatus": 1,
            "name": ["!=", self.name],
        }):
            frappe.throw(
                f"❌ A submitted {self.checklist_type} checklist already exists "
                f"for contract {self.rental_contract}. Cannot create another.",
                title="Duplicate Checklist"
            )

    def _compare_with_pre_delivery(self):
        """
        Compare post-return accessories & panels against the pre-delivery checklist.
        Populate:
          • missing_accessories  — text list of items present at handover but now missing
          • new_damage_panels    — text list of panels with new damage since handover
          • missing_item_count   — integer count (drives per-item charge calculation)
          • missing_accessories_charge — auto-calculated if contract has a per-item rate
        """
        pre = frappe.db.get_value(
            "Handover Checklist",
            {
                "rental_contract": self.rental_contract,
                "checklist_type": "Pre-Delivery (Handover)",
                "docstatus": 1,
            },
            ["name"] + [f[0] for f in ACCESSORY_FIELDS] + PANEL_FIELDS,
            as_dict=True,
        )

        if not pre:
            # No pre-delivery checklist found — warn but don't block
            frappe.msgprint(
                "⚠️ No submitted Pre-Delivery Checklist found for this contract. "
                "Missing-item and new-damage comparison cannot be performed.",
                indicator="orange"
            )
            return

        # ── Accessories: was present at handover but missing now ──
        missing = []
        for fieldname, label in ACCESSORY_FIELDS:
            was_present = pre.get(fieldname)
            is_present  = self.get(fieldname)
            if was_present and not is_present:
                missing.append(label)

        self.missing_accessories   = ", ".join(missing) if missing else "None — all accessories present ✅"
        self.missing_item_count    = len(missing)

        # Auto-calculate missing-accessory charge from contract setting
        # Only auto-calculate if not already manually entered by user
        if missing:
            if not flt(self.missing_accessories_charge):
                per_item_rate = flt(frappe.db.get_value(
                    "Rental Contract", self.rental_contract, "missing_accessory_charge"
                ) or 0)
                self.missing_accessories_charge = per_item_rate * len(missing)
            # else: user has manually set a value — preserve it
        else:
            self.missing_accessories_charge = 0

        # ── Panels: detect new damage (status got worse since handover) ──
        new_damage = []
        for fieldname in PANEL_FIELDS:
            pre_val  = pre.get(fieldname) or "OK"
            post_val = self.get(fieldname) or "OK"
            if pre_val in OK_VALUES and post_val not in OK_VALUES:
                label = self.meta.get_field(fieldname).label
                new_damage.append(f"{label}: {post_val}")

        self.new_damage_panels = "\n".join(new_damage) if new_damage else "No new damage detected ✅"

    # ─────────────────────────────────────────────
    #  ON SUBMIT
    # ─────────────────────────────────────────────
    def on_submit(self):
        if not self.rental_contract:
            frappe.throw(
                "❌ Rental Contract is not linked. "
                "Please link the contract before submitting.",
                title="Missing Contract"
            )

        contract_status = frappe.db.get_value(
            "Rental Contract", self.rental_contract, "docstatus"
        )

        if self.checklist_type == "Pre-Delivery (Handover)":
            self._handle_pre_delivery(contract_status)
        elif self.checklist_type == "Post-Return":
            self._handle_post_return(contract_status)

    def _handle_pre_delivery(self, contract_status):
        frappe.db.set_value(
            "Rental Contract", self.rental_contract,
            "handover_checklist", self.name
        )
        frappe.msgprint(
            f"✅ Pre-Delivery Checklist submitted and linked to "
            f"<b>{self.rental_contract}</b>. You can now submit the Rental Contract.",
            title="Checklist Linked",
            indicator="green"
        )

    def _handle_post_return(self, contract_status):
        from frappe.utils import now_datetime, flt

        # ── Fetch current return date ─────────────────────────────
        actual_return_date = frappe.db.get_value(
            "Rental Contract", self.rental_contract, "actual_return_date"
        )

        update_dict = {
            "return_checklist": self.name
        }

        # 🔥 AUTO SET return date if not already set
        if not actual_return_date:
            update_dict["actual_return_date"] = now_datetime()

        # ── Missing accessory charge logic ────────────────────────
        if self.missing_accessories_charge and self.missing_accessories_charge > 0:
            existing_damage = flt(frappe.db.get_value(
                "Rental Contract", self.rental_contract, "damage_charges"
            ) or 0)

            if existing_damage == 0:
                update_dict["damage_charges"] = flt(self.missing_accessories_charge)

        # ── Update contract ───────────────────────────────────────
        frappe.db.set_value("Rental Contract", self.rental_contract, update_dict)

        # 🔥 IMPORTANT: Trigger contract logic (invoice + status update)
        contract_doc = frappe.get_doc("Rental Contract", self.rental_contract)
        contract_doc.save(ignore_permissions=True)

        # ── User message ──────────────────────────────────────────
        msg_parts = [
            f"✅ Post-Return Checklist submitted and linked to <b>{self.rental_contract}</b>."
        ]

        if not actual_return_date:
            msg_parts.append("<br>📅 <b>Return Date auto-set</b> by system.")

        if self.missing_item_count:
            msg_parts.append(
                f"<br>⚠️ <b>{self.missing_item_count} accessory item(s) missing</b>: "
                f"{self.missing_accessories}. "
                f"Charge of OMR {flt(self.missing_accessories_charge):,.3f} "
                f"has been set on the contract."
            )

        if self.new_damage_panels and "No new damage" not in self.new_damage_panels:
            msg_parts.append(
                f"<br>🔴 <b>New damage detected</b>:<br>{self.new_damage_panels}"
            )

        frappe.msgprint(
            "".join(msg_parts),
            title="Return Checklist Linked",
            indicator="orange" if self.missing_item_count else "green"
        )