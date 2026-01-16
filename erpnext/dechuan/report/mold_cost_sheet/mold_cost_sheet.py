# Copyright (c) 2026, Dechuan Team and contributors
# Mold Cost Sheet Report - Aggregate costs by Mold Project

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	return [
		{
			"fieldname": "mold_project",
			"label": _("模具项目"),
			"fieldtype": "Link",
			"options": "Mold Project",
			"width": 120
		},
		{
			"fieldname": "project_name",
			"label": _("项目名称"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "customer",
			"label": _("客户"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"fieldname": "mold_status",
			"label": _("状态"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "material_cost",
			"label": _("材料成本"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "labor_cost",
			"label": _("人工成本"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "overhead_cost",
			"label": _("制造费用"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "outsourcing_cost",
			"label": _("外协成本"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_cost",
			"label": _("总成本"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "sales_amount",
			"label": _("销售金额"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "gross_profit",
			"label": _("毛利"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "gross_margin",
			"label": _("毛利率 %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	# Get all Mold Projects
	mold_projects = frappe.db.sql("""
		SELECT 
			mp.name as mold_project,
			mp.project_name,
			mp.customer,
			mp.mold_status,
			COALESCE(so.grand_total, 0) as sales_amount
		FROM `tabMold Project` mp
		LEFT JOIN `tabSales Order` so ON so.name = mp.sales_order AND so.docstatus = 1
		WHERE 1=1 {conditions}
		ORDER BY mp.creation DESC
	""".format(conditions=conditions), filters, as_dict=True)
	
	data = []
	for mp in mold_projects:
		# Get costs from Mold Cost Ledger
		costs = get_mold_costs(mp.mold_project)
		
		total_cost = sum(costs.values())
		sales_amount = mp.sales_amount or 0
		gross_profit = sales_amount - total_cost
		gross_margin = (gross_profit / sales_amount * 100) if sales_amount else 0
		
		data.append({
			"mold_project": mp.mold_project,
			"project_name": mp.project_name,
			"customer": mp.customer,
			"mold_status": mp.mold_status,
			"material_cost": costs.get("Material", 0),
			"labor_cost": costs.get("Labor", 0),
			"overhead_cost": costs.get("Overhead", 0),
			"outsourcing_cost": costs.get("Outsourcing", 0),
			"total_cost": total_cost,
			"sales_amount": sales_amount,
			"gross_profit": gross_profit,
			"gross_margin": gross_margin
		})
	
	return data

def get_mold_costs(mold_project):
	"""Get aggregated costs by type from Mold Cost Ledger."""
	cost_data = frappe.db.sql("""
		SELECT cost_type, SUM(amount) as total
		FROM `tabMold Cost Ledger`
		WHERE mold_project = %s
		GROUP BY cost_type
	""", mold_project, as_dict=True)
	
	costs = {}
	for row in cost_data:
		costs[row.cost_type] = row.total
	
	return costs

def get_conditions(filters):
	conditions = ""
	
	if filters.get("mold_project"):
		conditions += " AND mp.name = %(mold_project)s"
	
	if filters.get("customer"):
		conditions += " AND mp.customer = %(customer)s"
	
	if filters.get("mold_status"):
		conditions += " AND mp.mold_status = %(mold_status)s"
	
	if filters.get("from_date"):
		conditions += " AND mp.creation >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND mp.creation <= %(to_date)s"
	
	return conditions

def get_chart(data):
	if not data:
		return None
	
	labels = [d["mold_project"] for d in data[:10]]  # Limit to 10 for readability
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("材料成本"),
					"values": [d["material_cost"] for d in data[:10]]
				},
				{
					"name": _("人工成本"),
					"values": [d["labor_cost"] for d in data[:10]]
				},
				{
					"name": _("外协成本"),
					"values": [d["outsourcing_cost"] for d in data[:10]]
				}
			]
		},
		"type": "bar",
		"barOptions": {"stacked": 1}
	}

def get_summary(data):
	if not data:
		return []
	
	total_material = sum(d["material_cost"] for d in data)
	total_labor = sum(d["labor_cost"] for d in data)
	total_overhead = sum(d["overhead_cost"] for d in data)
	total_outsourcing = sum(d["outsourcing_cost"] for d in data)
	total_cost = sum(d["total_cost"] for d in data)
	total_sales = sum(d["sales_amount"] for d in data)
	total_profit = sum(d["gross_profit"] for d in data)
	avg_margin = (total_profit / total_sales * 100) if total_sales else 0
	
	return [
		{
			"value": total_material,
			"indicator": "Blue",
			"label": _("材料成本合计"),
			"datatype": "Currency",
			"currency": "CNY"
		},
		{
			"value": total_labor,
			"indicator": "Orange",
			"label": _("人工成本合计"),
			"datatype": "Currency",
			"currency": "CNY"
		},
		{
			"value": total_cost,
			"indicator": "Red",
			"label": _("总成本合计"),
			"datatype": "Currency",
			"currency": "CNY"
		},
		{
			"value": total_profit,
			"indicator": "Green",
			"label": _("毛利合计"),
			"datatype": "Currency",
			"currency": "CNY"
		},
		{
			"value": avg_margin,
			"indicator": "Green" if avg_margin > 20 else "Orange",
			"label": _("平均毛利率"),
			"datatype": "Percent"
		}
	]
