# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TrialReport(Document):
	def validate(self):
		self.validate_verdict()

	def validate_verdict(self):
		if self.visual_check == "合格" and self.dimension_check == "合格" and self.function_check == "合格":
			if self.final_verdict == "不合格":
				frappe.msgprint("警告：全部分项合格，但综合判定为不合格")
		
		if self.disposition == "出货" and self.final_verdict != "合格":
			frappe.throw("只有综合判定合格才允许选择'出货'")
	
	def on_submit(self):
		# 可以在此处触发自动通知或流转
		pass
