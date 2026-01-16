# Copyright (c) 2026, Dechuan Team and contributors
# Confirmation Reminder Agent
# Scheduled task to monitor overdue Drawing Confirmations and send reminders

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, time_diff_in_hours

# Configuration: Hours before a confirmation is considered overdue
OVERDUE_HOURS = {
    "待工程确认": 24,  # 1 day
    "待生产确认": 24,  # 1 day
    "待业务确认": 48,  # 2 days
    "待客户确认": 72,  # 3 days
}

# Mapping of status to responsible role
STATUS_TO_ROLE = {
    "待工程确认": "Engineering User",  # Placeholder - should be configured
    "待生产确认": "Manufacturing User",
    "待业务确认": "Sales User",
    "待客户确认": "Sales User",  # Sales follows up with customer
}

def run_confirmation_reminder():
    """
    Scheduler Entry Point: Scan all pending Drawing Confirmations
    and send reminders for overdue ones.
    """
    frappe.logger().info("Running Confirmation Reminder Agent...")
    
    pending_statuses = ["待工程确认", "待生产确认", "待业务确认", "待客户确认"]
    
    confirmations = frappe.get_all(
        "Drawing Confirmation",
        filters={"status": ["in", pending_statuses]},
        fields=["name", "status", "mold_project", "project_name", "modified", "status_changed_at"]
    )
    
    reminders_sent = 0
    
    for conf in confirmations:
        pending_since = conf.status_changed_at or conf.modified
        hours_pending = time_diff_in_hours(now_datetime(), get_datetime(pending_since))
        threshold = OVERDUE_HOURS.get(conf.status, 24)
        
        if hours_pending > threshold:
            send_reminder(conf, hours_pending)
            reminders_sent += 1
    
    frappe.logger().info(f"Confirmation Reminder Agent: Sent {reminders_sent} reminders.")
    return reminders_sent


def send_reminder(confirmation, hours_pending):
    """
    Send a reminder notification for an overdue confirmation.
    Supports: Frappe Notification (System), WeChat Work (TODO), Email (TODO)
    """
    status = confirmation.status
    mold_project = confirmation.mold_project
    project_name = confirmation.project_name or mold_project
    doc_name = confirmation.name
    
    message = f"""
【图纸确认催办】

模具项目: {project_name} ({mold_project})
确认单号: {doc_name}
当前状态: {status}
已等待: {hours_pending:.1f} 小时

请尽快处理！
"""
    
    # 1. Create a ToDo for the responsible user/role
    role = STATUS_TO_ROLE.get(status, "System Manager")
    users = get_users_with_role(role)
    
    for user in users:
        create_todo(user, doc_name, message)
    
    # 2. (Optional) Push to WeChat Work / DingTalk
    # This requires external integration setup
    push_to_wechat_work(message, users)
    
    # 3. Log the reminder
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Drawing Confirmation",
        "reference_name": doc_name,
        "content": f"催办提醒已发送 (已等待 {hours_pending:.1f} 小时)"
    }).insert(ignore_permissions=True)


def get_users_with_role(role):
    """Get list of users with the specified role."""
    users = frappe.get_all(
        "Has Role",
        filters={"role": role, "parenttype": "User"},
        fields=["parent"]
    )
    return [u.parent for u in users if u.parent not in ["Administrator", "Guest"]]


def create_todo(user, reference_name, description):
    """Create a ToDo item for the user."""
    if not frappe.db.exists("ToDo", {"reference_name": reference_name, "allocated_to": user, "status": "Open"}):
        frappe.get_doc({
            "doctype": "ToDo",
            "allocated_to": user,
            "reference_type": "Drawing Confirmation",
            "reference_name": reference_name,
            "description": description,
            "priority": "High",
            "status": "Open"
        }).insert(ignore_permissions=True)


def push_to_wechat_work(message, users):
    """
    Push notification to WeChat Work (企业微信).
    Requires: WeChat Work App configuration with Agent ID.
    This is a placeholder - actual implementation needs WeChat Work API setup.
    """
    # Check if WeChat Work integration is configured
    wechat_settings = frappe.db.get_single_value("Dechuan Settings", "wechat_work_enabled") if frappe.db.exists("DocType", "Dechuan Settings") else False
    
    if not wechat_settings:
        frappe.logger().debug("WeChat Work integration not enabled, skipping push.")
        return
    
    # TODO: Implement actual WeChat Work API call
    # Example structure:
    # from erpnext.dechuan.integrations.wechat_work import send_text_message
    # send_text_message(user_ids=users, content=message)
    pass
