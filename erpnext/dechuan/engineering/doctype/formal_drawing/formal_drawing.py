# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FormalDrawing(Document):
	def validate(self):
		self.ensure_unique_current_version()

	def ensure_unique_current_version(self):
		if self.is_current:
			# Uncheck 'is_current' for other versions of the same drawing in this project
			frappe.db.sql("""
				UPDATE `tabFormal Drawing`
				SET is_current = 0
				WHERE mold_project = %s 
				  AND formal_drawing_code = %s
				  AND name != %s
			""", (self.mold_project, self.formal_drawing_code, self.name))
