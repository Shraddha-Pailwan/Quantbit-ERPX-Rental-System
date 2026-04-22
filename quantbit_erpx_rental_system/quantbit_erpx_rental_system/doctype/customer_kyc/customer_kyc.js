// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd.
frappe.ui.form.on('Customer KYC', {

    refresh: function(frm) {
        toggle_fields(frm);  // toggle fields on load
    },

    customer_type: function(frm) {
        toggle_fields(frm);  // toggle when type changes
    },

    kyc_status: function(frm) {
        if (frm.doc.kyc_status === "Blacklisted" && !frm.doc.blacklist_reason) {
            frappe.msgprint("⚠️ Please select Blacklist Reason");
        }
    },

    customer: function(frm) {
        if (frm.doc.customer && !frm.doc.full_name) {
            frappe.db.get_value('Customer', frm.doc.customer, 'customer_name')
                .then(r => {
                    if (r.message) {
                        frm.set_value('full_name', r.message.customer_name);
                    }
                });
        }
    }

});


// 🔹 Dynamic field visibility
function toggle_fields(frm) {

    const is_corporate = ["Corporate", "Broker / Travel Agency"].includes(frm.doc.customer_type);
    const is_broker = frm.doc.customer_type === "Broker / Travel Agency";

    // corporate fields
    frm.toggle_display("company_name", is_corporate);
    frm.toggle_display("cr_number", is_corporate);
    frm.toggle_display("vat_registration_number", is_corporate);

    // broker fields
    frm.toggle_display("commission_type", is_broker);
    frm.toggle_display("commission_rate", is_broker);
    frm.toggle_display("commission_gl_account", is_broker);
}


function toggle_fields(frm) {

    const is_corporate = ["Corporate", "Broker / Travel Agency"].includes(frm.doc.customer_type);
    const is_broker = frm.doc.customer_type === "Broker / Travel Agency";

    // corporate fields
    frm.toggle_display("company_name", is_corporate);
    frm.toggle_display("cr_number", is_corporate);
    frm.toggle_display("vat_registration_number", is_corporate);

    // broker fields
    frm.toggle_display("commission_type", is_broker);
    frm.toggle_display("commission_rate", is_broker);
    frm.toggle_display("commission_gl_account", is_broker);
}

frappe.ui.form.on('Customer KYC', {

    residential_address: function(frm) {
        set_address(frm, 'residential_address', 'residential_address_descriptive');
    },

    work_address: function(frm) {
        set_address(frm, 'work_address', 'workoffice_address_descriptive');
    },

    refresh: function(frm) {
        set_address(frm, 'residential_address', 'residential_address_descriptive');
        set_address(frm, 'work_address', 'workoffice_address_descriptive');
    }
});


function set_address(frm, link_field, text_field) {

    let address_name = frm.doc[link_field];

    if (!address_name) {
        frm.set_value(text_field, "");
        return;
    }

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Address",
            name: address_name
        },
        callback: function(r) {

            if (!r.message) return;

            let a = r.message;
            let lines = [];

            // 🔹 Split address_line1 (fix comma issue)
            if (a.address_line1) {
                lines.push(...a.address_line1.split(","));
            }

            // 🔹 Split address_line2
            if (a.address_line2) {
                lines.push(...a.address_line2.split(","));
            }

            // 🔹 City + State
            let city_line = [a.city, a.state].filter(Boolean).join(", ");
            if (city_line) lines.push(city_line);

            // 🔹 Pincode
            if (a.pincode) lines.push(a.pincode);

            // 🔹 Country
            if (a.country) lines.push(a.country);

            // 🔹 Clean lines
            lines = lines.map(l => l.trim()).filter(l => l);

            // 🔥 FINAL OUTPUT (multiline text)
            frm.set_value(text_field, lines.join("\n"));
        }
    });
}