# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, today

class MoldProject(Document):
	def autoname(self):
		# Determine prefix based on Company Entity
		if self.company_entity == "德川":
			prefix = "DC"
		elif self.company_entity == "裕霖":
			prefix = "YL"
		else:
			prefix = "XX"
		
		# Get current year
		year = getdate(today()).year
		
		# Generate name: PREFIX + YYYY + 3-digit series
		# Example: DC2026001
		self.name = make_autoname(f'format:{prefix}{year}{{###}}')

	def before_insert(self):
		# company_entity_code logic is now handled in autoname, 
		# but we can keep it if needed for other purposes, or remove it.
		# For now, we removing the redundant attribute setting unless needed by client script.
		pass

	def validate(self):
		self.update_status_based_on_drawings()

	def update_status_based_on_drawings(self):
		"""根据图纸状态自动更新项目状态的逻辑示例"""
		# Only update if status implies we are in design phase
		if self.mold_status == "设计" and self.drawing_status == "已确认":
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
