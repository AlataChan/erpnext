# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WeeklyPlan(Document):
	def validate(self):
		self.calculate_summary()

	def calculate_summary(self):
		"""Calculate summary fields from tasks."""
		projects = set()
		total_hours = 0
		
		for task in self.tasks or []:
			if task.mold_project:
				projects.add(task.mold_project)
			total_hours += task.planned_hours or 0
		
		self.total_projects = len(projects)
		self.total_hours_planned = total_hours

	@frappe.whitelist()
	def publish_plan(self):
		"""Publish the weekly plan and notify assigned workers."""
		if self.status == "Draft":
			self.status = "Published"
			self.save()
			self.notify_workers()
			frappe.msgprint("周计划已发布")

	def notify_workers(self):
		"""Send notifications to all assigned workers."""
		workers = set()
		for task in self.tasks or []:
			if task.assigned_to:
				workers.add(task.assigned_to)
		
		for worker in workers:
			frappe.get_doc({
				"doctype": "ToDo",
				"allocated_to": worker,
				"reference_type": "Weekly Plan",
				"reference_name": self.name,
				"description": f"周计划 {self.name} 已发布，请查看您的任务安排。",
				"priority": "Medium",
				"status": "Open"
			}).insert(ignore_permissions=True)
