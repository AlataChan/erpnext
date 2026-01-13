
from frappe import _

def get_dechuan_custom_fields():
    return {
        "Customer": [
            {
                "fieldname": "default_company_entity",
                "label": _("Default Company Entity"),
                "fieldtype": "Select",
                "options": "德川\n裕霖",
                "insert_after": "customer_name",
                "description": "默认归属公司主体 (Sets the default entity for orders)"
            },
            {
                "fieldname": "reconciliation_habit",
                "label": _("Reconciliation Habit"),
                "fieldtype": "Select",
                "options": "月结30天\n月结60天\n月结90天\n当月结\n货到付款\n预付全款\n其他",
                "insert_after": "default_company_entity",
                "description": "客户的对账结算习惯"
            }
        ],
        "Sales Order": [
             {
                "fieldname": "company_entity",
                "label": _("Company Entity"),
                "fieldtype": "Select",
                "options": "德川\n裕霖",
                "insert_after": "customer",
                "fetch_from": "customer.default_company_entity",
                "description": "所属主体 (Auto-fetched from Customer)"
            }
        ]
    }
