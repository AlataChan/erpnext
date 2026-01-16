# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DechuanSettings(Document):
	pass

def get_settings():
	"""Get Dechuan Settings singleton."""
	return frappe.get_single("Dechuan Settings")

def is_wechat_enabled():
	"""Check if WeChat Work integration is enabled."""
	settings = get_settings()
	return settings.wechat_work_enabled if settings else False

def get_confirmation_timeout():
	"""Get confirmation timeout in hours."""
	settings = get_settings()
	return settings.confirmation_timeout_hours or 24

def get_collection_reminder_days():
	"""Get collection reminder threshold days as list."""
	settings = get_settings()
	days_str = settings.collection_reminder_days or "30,60,90"
	return [int(d.strip()) for d in days_str.split(",") if d.strip().isdigit()]
