// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rental Contract', {

    vehicle: function(frm) {
        if (frm.doc.vehicle) {
            frappe.db.get_value('Vehicle Master', frm.doc.vehicle, 'vehicle_status')
                .then(r => {
                    if (r.message) {
                        frm.set_value('vehicle_status_at_contract', r.message.vehicle_status);

                        if (r.message.vehicle_status !== "Available") {
                            frappe.msgprint("⚠ Vehicle is not available");
                        }
                    }
                });
        }
    },

    rate_card: function(frm) {
        frm.trigger("map_rate_card");
    },

    contract_type: function(frm) {
        if (frm.doc.rate_card) {
            frm.trigger("map_rate_card");
        }
    },

    km_return: function(frm) {
        frm.trigger("recalculate");
    },

    actual_return_date: function(frm) {
        frm.trigger("recalculate");
    },

    // 🔹 Custom triggers
    map_rate_card: function(frm) {
        if (!frm.doc.rate_card || !frm.doc.contract_type) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Rate Card",
                name: frm.doc.rate_card
            },
            callback: function(r) {
                if (!r.message) return;

                let rc = r.message;

                if (frm.doc.contract_type === "Daily") {
                    frm.set_value("rate", rc.daily_rate || 0);
                    frm.set_value("free_km_per_day", rc.free_km_per_day || 0);
                    frm.set_value("excess_km_charge_daily", rc.excess_km_charge_daily || 0);
                }

                else if (frm.doc.contract_type === "Weekly") {
                    frm.set_value("rate", rc.weekly_rate || 0);
                    frm.set_value("free_km_per_week", rc.free_km_per_week || 0);
                    frm.set_value("excess_km_charge_daily", rc.excess_km_charge_daily || 0);
                }

                else if (frm.doc.contract_type === "Monthly") {
                    frm.set_value("rate", rc.monthly_rate || 0);
                    frm.set_value("free_km_per_month", rc.free_km_per_month || 0);
                    frm.set_value("excess_km_charge_monthly", rc.excess_km_charge_monthly || 0);
                }
            }
        });
    }});