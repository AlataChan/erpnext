# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class DrawingConfirmation(Document):
	def validate(self):
		pass

	def confirm_engineering(self, user):
		if self.status != "待工程确认":
			frappe.throw("当前状态不允许工程确认")
		self.eng_confirmed_by = user
		self.eng_confirm_time = now_datetime()
		self.status = "待生产确认"
		self.save()

	def confirm_production(self, user):
		if self.status != "待生产确认":
			frappe.throw("当前状态不允许生产确认")
		self.prod_confirmed_by = user
		self.prod_confirm_time = now_datetime()
		self.status = "待业务确认"
		self.save()

	def confirm_sales(self, user):
		if self.status != "待业务确认":
			frappe.throw("当前状态不允许业务确认")
		self.sales_confirmed_by = user
		self.sales_confirm_time = now_datetime()
		self.status = "待客户确认"
		self.save()

	def confirm_customer(self, customer_name, feedback=""):
		if self.status != "待客户确认":
			frappe.throw("当前状态不允许客户确认")
		self.customer_confirmed_by = customer_name
		self.customer_confirm_time = now_datetime()
		self.customer_feedback = feedback
		self.status = "已确认"
		self.update_mold_project()
		self.save()
	
	def update_mold_project(self):
		if self.mold_project:
			mp = frappe.get_doc("Mold Project", self.mold_project)
			mp.drawing_status = "已确认"
			mp.save()
