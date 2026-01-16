// Copyright (c) 2026, Dechuan Team and contributors
// Mold Cost Sheet Report Filters

frappe.query_reports["Mold Cost Sheet"] = {
    "filters": [
        {
            "fieldname": "mold_project",
            "label": __("模具项目"),
            "fieldtype": "Link",
            "options": "Mold Project"
        },
        {
            "fieldname": "customer",
            "label": __("客户"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "mold_status",
            "label": __("状态"),
            "fieldtype": "Select",
            "options": "\n立项\n设计\n采购\n加工\n试模\n整改\n出货\n完结"
        },
        {
            "fieldname": "from_date",
            "label": __("起始日期"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
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
                value = "<span style='color:red'>" + value + "</span>";
            } else if (data.gross_margin > 30) {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }

        if (column.fieldname == "gross_profit" && data.gross_profit < 0) {
            value = "<span style='color:red'>" + value + "</span>";
        }

        return value;
    }
};
