# Copyright (c) 2026, Dechuan Team and contributors
# Collection Reminder Agent - Monitors A/R aging and triggers payment reminders

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, date_diff, add_days

# Configuration: Aging thresholds and escalation levels
AGING_THRESHOLDS = [
    {"days": 30, "level": "Level 1", "action": "reminder"},
    {"days": 60, "level": "Level 2", "action": "escalate"},
    {"days": 90, "level": "Level 3", "action": "urgent"},
]

def run_collection_reminder():
    """
    Scheduler Entry Point: Scan overdue Sales Invoices and trigger reminders.
    """
    frappe.logger().info("Running Collection Reminder Agent...")
    
    # Get all unpaid/partially paid Sales Invoices that are overdue
    overdue_invoices = frappe.db.sql("""
        SELECT 
            si.name,
            si.customer,
            si.posting_date,
            si.due_date,
            si.grand_total,
            si.outstanding_amount,
            DATEDIFF(CURDATE(), si.due_date) as days_overdue
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.outstanding_amount > 0
          AND si.due_date < CURDATE()
        ORDER BY days_overdue DESC
    """, as_dict=True)
    
    reminders_sent = 0
    
    for invoice in overdue_invoices:
        days_overdue = invoice.days_overdue
        
        # Determine escalation level
        escalation_level = determine_escalation_level(days_overdue)
        
        if should_send_reminder(invoice.name, escalation_level):
            send_collection_reminder(invoice, escalation_level)
            log_reminder_sent(invoice.name, escalation_level)
            reminders_sent += 1
    
    frappe.logger().info(f"Collection Reminder Agent: Processed {len(overdue_invoices)} overdue invoices, sent {reminders_sent} reminders.")
    return reminders_sent


def determine_escalation_level(days_overdue):
    """Determine escalation level based on days overdue."""
    level = None
    for threshold in AGING_THRESHOLDS:
        if days_overdue >= threshold["days"]:
            level = threshold
    return level or AGING_THRESHOLDS[0]


def should_send_reminder(invoice_name, escalation_level):
    """
    Check if we should send a reminder (avoid spamming).
    Only send if no reminder at this level has been sent in the last 7 days.
    """
    last_reminder = frappe.db.get_value(
        "Comment",
        filters={
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice_name,
            "content": ["like", f"%{escalation_level['level']}%"]
        },
        fieldname="creation",
        order_by="creation desc"
    )
    
    if last_reminder:
        days_since = date_diff(getdate(), getdate(last_reminder))
        if days_since < 7:
            return False
    
    return True


def send_collection_reminder(invoice, escalation_level):
    """
    Send collection reminder based on escalation level.
    """
    customer = invoice.customer
    invoice_name = invoice.name
    days_overdue = invoice.days_overdue
    outstanding = invoice.outstanding_amount
    level = escalation_level["level"]
    action = escalation_level["action"]
    
    message = f"""
【收款催办 - {level}】

客户: {customer}
发票号: {invoice_name}
到期日: {invoice.due_date}
逾期天数: {days_overdue} 天
未付金额: ¥{outstanding:,.2f}

请及时跟进！
"""
    
    # 1. Create ToDo for Sales/Accounts team
    sales_users = get_responsible_users(customer, action)
    for user in sales_users:
        create_collection_todo(user, invoice_name, message, escalation_level)
    
    # 2. Log the reminder
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Sales Invoice",
        "reference_name": invoice_name,
        "content": f"收款催办 ({level}): 逾期 {days_overdue} 天, 欠款 ¥{outstanding:,.2f}"
    }).insert(ignore_permissions=True)
    
    # 3. (Optional) Push to WeChat Work
    # push_to_wechat(message, sales_users)


def get_responsible_users(customer, action):
    """Get users responsible for collection for this customer."""
    # Try to get the sales person linked to the customer
    sales_team = frappe.get_all(
        "Sales Team",
        filters={"parenttype": "Customer", "parent": customer},
        fields=["sales_person"]
    )
    
    users = []
    for st in sales_team:
        # Get user linked to sales person
        user = frappe.db.get_value("Sales Person", st.sales_person, "user_id")
        if user:
            users.append(user)
    
    # If no specific sales person, assign to Accounts/Finance role
    if not users:
        accounts_users = frappe.get_all(
            "Has Role",
            filters={"role": "Accounts User", "parenttype": "User"},
            fields=["parent"]
        )
        users = [u.parent for u in accounts_users if u.parent not in ["Administrator", "Guest"]][:3]
    
    # Escalation: Add manager if Level 2+
    if action in ["escalate", "urgent"]:
        managers = frappe.get_all(
            "Has Role",
            filters={"role": "Accounts Manager", "parenttype": "User"},
            fields=["parent"]
        )
        users.extend([m.parent for m in managers if m.parent not in ["Administrator", "Guest"]])
    
    return list(set(users))


def create_collection_todo(user, invoice_name, description, escalation_level):
    """Create collection ToDo."""
    priority = "High" if escalation_level["action"] == "urgent" else "Medium"
    
    # Avoid duplicate open ToDos
    if not frappe.db.exists("ToDo", {
        "reference_name": invoice_name,
        "allocated_to": user,
        "status": "Open"
    }):
        frappe.get_doc({
            "doctype": "ToDo",
            "allocated_to": user,
            "reference_type": "Sales Invoice",
            "reference_name": invoice_name,
            "description": description,
            "priority": priority,
            "status": "Open"
        }).insert(ignore_permissions=True)


def log_reminder_sent(invoice_name, escalation_level):
    """Log that a reminder was sent."""
    frappe.logger().debug(f"Collection reminder sent: {invoice_name} ({escalation_level['level']})")


@frappe.whitelist()
def get_aging_summary(customer=None):
    """
    API: Get A/R aging summary, optionally filtered by customer.
    """
    filters = {"docstatus": 1}
    if customer:
        filters["customer"] = customer
    
    invoices = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount"]
    )
    
    today = getdate()
    buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    
    for inv in invoices:
        if inv.outstanding_amount <= 0:
            continue
        
        days = date_diff(today, inv.due_date)
        
        if days <= 0:
            buckets["current"] += inv.outstanding_amount
        elif days <= 30:
            buckets["1_30"] += inv.outstanding_amount
        elif days <= 60:
            buckets["31_60"] += inv.outstanding_amount
        elif days <= 90:
            buckets["61_90"] += inv.outstanding_amount
        else:
            buckets["over_90"] += inv.outstanding_amount
    
    return {
        "customer": customer or "All",
        "aging": buckets,
        "total_outstanding": sum(buckets.values())
    }
