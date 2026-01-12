# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MoldProject(Document):
	def before_insert(self):
		self.set_company_code()

	def set_company_code(self):
		# 用于 autoname 格式化
		if self.company_entity == "德川":
			self.company_entity_code = "DC"
		elif self.company_entity == "裕霖":
			self.company_entity_code = "YL"
		else:
			self.company_entity_code = "XX"

	def validate(self):
		self.update_status_based_on_drawings()

	def update_status_based_on_drawings(self):
		"""根据图纸状态自动更新项目状态的逻辑示例"""
		if self.drawing_status == "已确认" and self.mold_status == "设计":
			self.mold_status = "采购"

	def get_progress_summary(self):
		"""供 AI Agent 调用的进度摘要方法"""
		return {
			"mold_number": self.name,
			"project_name": self.project_name,
			"status": self.mold_status,
			"delivery_date": self.planned_delivery_date,
			"drawing_status": self.drawing_status
		}
