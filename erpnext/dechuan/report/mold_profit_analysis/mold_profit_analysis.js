// Copyright (c) 2026, Dechuan Team and contributors
// Mold Profit Analysis Report Filters

frappe.query_reports["Mold Profit Analysis"] = {
    "filters": [
        {
            "fieldname": "group_by",
            "label": __("分组维度"),
            "fieldtype": "Select",
            "options": "customer\ncompany_entity\nmold_type\nmonth",
            "default": "customer",
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": __("客户"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "company_entity",
            "label": __("公司主体"),
            "fieldtype": "Select",
            "options": "\n德川\n裕霖"
        },
        {
            "fieldname": "from_date",
            "label": __("起始日期"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -12)
        },
        {
            "fieldname": "to_date",
            "label": __("截止日期"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "gross_margin") {
            if (data.gross_margin < 0) {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            } else if (data.gross_margin < 15) {
                value = "<span style='color:orange'>" + value + "</span>";
            } else if (data.gross_margin > 30) {
                value = "<span style='color:green;font-weight:bold'>" + value + "</span>";
            }
        }

        return value;
    }
};
