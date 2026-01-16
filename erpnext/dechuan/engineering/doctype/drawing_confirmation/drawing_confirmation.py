# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, time_diff_in_hours

class DrawingConfirmation(Document):
	def validate(self):
		self.set_pending_since()

	def set_pending_since(self):
		"""Track when the current status started, for timeout calculations."""
		if self.has_value_changed("status"):
			self.db_set("status_changed_at", now_datetime(), update_modified=False)

	def on_update(self):
		"""After save, update status_changed_at if status changed."""
		pass

	# --- Confirmation Methods (Called via API) ---
	
	@frappe.whitelist()
	def confirm_engineering(self):
		"""API: Engineering confirms the drawing."""
		user = frappe.session.user
		if self.status != "待工程确认":
			frappe.throw("当前状态不允许工程确认")
		self.eng_confirmed_by = user
		self.eng_confirm_time = now_datetime()
		self.status = "待生产确认"
		self.save()
		frappe.msgprint(f"工程确认完成，已流转至生产确认")

	@frappe.whitelist()
	def confirm_production(self):
		"""API: Production confirms the drawing."""
		user = frappe.session.user
		if self.status != "待生产确认":
			frappe.throw("当前状态不允许生产确认")
		self.prod_confirmed_by = user
		self.prod_confirm_time = now_datetime()
		self.status = "待业务确认"
		self.save()
		frappe.msgprint(f"生产确认完成，已流转至业务确认")

	@frappe.whitelist()
	def confirm_sales(self):
		"""API: Sales/Business confirms the drawing."""
		user = frappe.session.user
		if self.status != "待业务确认":
			frappe.throw("当前状态不允许业务确认")
		self.sales_confirmed_by = user
		self.sales_confirm_time = now_datetime()
		self.status = "待客户确认"
		self.save()
		frappe.msgprint(f"业务确认完成，已流转至客户确认")

	@frappe.whitelist()
	def confirm_customer(self, customer_name, feedback=""):
		"""API: Record customer confirmation (manual entry)."""
		if self.status != "待客户确认":
			frappe.throw("当前状态不允许客户确认")
		self.customer_confirmed_by = customer_name
		self.customer_confirm_time = now_datetime()
		self.customer_feedback = feedback
		self.status = "已确认"
		self.update_mold_project_status()
		self.save()
		frappe.msgprint(f"客户已确认，图纸确认流程完成")

	@frappe.whitelist()
	def reject(self, reason=""):
		"""API: Reject drawing at any stage."""
		self.status = "已拒绝"
		self.customer_feedback = f"拒绝原因: {reason}" if reason else self.customer_feedback
		self.save()
		frappe.msgprint(f"图纸已拒绝")
	
	def update_mold_project_status(self):
		"""Update the parent Mold Project's drawing status."""
		if self.mold_project:
			mp = frappe.get_doc("Mold Project", self.mold_project)
			mp.drawing_status = "已确认"
			mp.save(ignore_permissions=True)

	# --- Helper for Reminder Agent ---
	def get_pending_hours(self):
		"""Calculate how many hours the document has been in current pending status."""
		status_changed_at = self.get("status_changed_at")
		if not status_changed_at:
			# Fallback to modified time
			status_changed_at = self.modified
		return time_diff_in_hours(now_datetime(), get_datetime(status_changed_at))
