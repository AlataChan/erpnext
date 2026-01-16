# Copyright (c) 2026, Dechuan Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class Reconciliation(Document):
	def validate(self):
		self.set_customer_abbr()
		self.calculate_totals()

	def set_customer_abbr(self):
		"""Set customer abbreviation for naming."""
		if self.customer and not self.customer_abbr:
			# Use first 4 chars of customer name or customer ID
			customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
			self.customer_abbr = (customer_name or self.customer)[:4].upper()

	def calculate_totals(self):
		"""Calculate total qty and amount from delivery notes."""
		total_qty = 0
		total_amount = 0
		
		for item in self.delivery_notes or []:
			total_qty += item.qty or 0
			total_amount += item.amount or 0
		
		self.total_qty = total_qty
		self.total_amount = total_amount

	@frappe.whitelist()
	def fetch_delivery_notes(self):
		"""
		Fetch un-reconciled Delivery Notes for the customer within date range.
		"""
		if not self.customer or not self.from_date or not self.to_date:
			frappe.throw("请先选择客户和日期范围")
		
		# Get Delivery Notes that are: submitted, not fully billed, within date range
		delivery_notes = frappe.get_all(
			"Delivery Note",
			filters={
				"customer": self.customer,
				"posting_date": ["between", [self.from_date, self.to_date]],
				"docstatus": 1,
				"status": ["not in", ["Closed", "Cancelled"]]
			},
			fields=["name", "posting_date", "grand_total", "total_qty"]
		)
		
		# Clear existing items
		self.delivery_notes = []
		
		for dn in delivery_notes:
			self.append("delivery_notes", {
				"delivery_note": dn.name,
				"posting_date": dn.posting_date,
				"qty": dn.total_qty,
				"amount": dn.grand_total
			})
		
		self.calculate_totals()
		frappe.msgprint(f"已加载 {len(delivery_notes)} 张送货单")

	@frappe.whitelist()
	def mark_confirmed(self, confirmed_by, confirm_date=None):
		"""Mark the reconciliation as confirmed by customer."""
		self.status = "Confirmed"
		self.confirmed_by_customer = confirmed_by
		self.confirm_date = confirm_date or getdate()
		self.save()
		frappe.msgprint("对账单已确认")

	@frappe.whitelist()
	def mark_disputed(self, notes=""):
		"""Mark as disputed by customer."""
		self.status = "Disputed"
		self.notes = notes
		self.save()
		frappe.msgprint("对账单已标记为有争议")
