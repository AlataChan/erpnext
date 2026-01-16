# Copyright (c) 2026, Dechuan Team and contributors
# Mold Profit Analysis - Multi-dimensional profit analysis

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart(data, filters)
	
	return columns, data, None, chart

def get_columns(filters):
	group_by = filters.get("group_by", "customer")
	
	group_label = {
		"customer": _("客户"),
		"company_entity": _("公司主体"),
		"mold_type": _("模具类型"),
		"month": _("月份")
	}.get(group_by, _("分组"))
	
	return [
		{
			"fieldname": "group_field",
			"label": group_label,
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "project_count",
			"label": _("项目数"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "total_sales",
			"label": _("销售额"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total_cost",
			"label": _("总成本"),
			"fieldtype": "Currency",
			"width": 130
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
			"fieldname": "gross_profit",
			"label": _("毛利"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "gross_margin",
			"label": _("毛利率 %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]

def get_data(filters):
	group_by = filters.get("group_by", "customer")
	conditions = get_conditions(filters)
	
	# Map group_by to SQL field
	group_field_map = {
		"customer": "mp.customer",
		"company_entity": "mp.company_entity",
		"mold_type": "COALESCE(mp.mold_type, 'Unspecified')",
		"month": "DATE_FORMAT(mp.creation, '%Y-%m')"
	}
	
	group_field = group_field_map.get(group_by, "mp.customer")
	
	# Get grouped mold projects
	grouped_data = frappe.db.sql("""
		SELECT 
			{group_field} as group_field,
			COUNT(mp.name) as project_count,
			GROUP_CONCAT(mp.name) as mold_projects,
			SUM(COALESCE(so.grand_total, 0)) as total_sales
		FROM `tabMold Project` mp
		LEFT JOIN `tabSales Order` so ON so.name = mp.sales_order AND so.docstatus = 1
		WHERE 1=1 {conditions}
		GROUP BY {group_field}
		ORDER BY total_sales DESC
	""".format(group_field=group_field, conditions=conditions), filters, as_dict=True)
	
	data = []
	for row in grouped_data:
		# Get costs for all mold projects in this group
		mold_list = row.mold_projects.split(",") if row.mold_projects else []
		costs = get_group_costs(mold_list)
		
		total_cost = sum(costs.values())
		gross_profit = (row.total_sales or 0) - total_cost
		gross_margin = (gross_profit / row.total_sales * 100) if row.total_sales else 0
		
		data.append({
			"group_field": row.group_field or "N/A",
			"project_count": row.project_count,
			"total_sales": row.total_sales or 0,
			"total_cost": total_cost,
			"material_cost": costs.get("Material", 0),
			"labor_cost": costs.get("Labor", 0),
			"gross_profit": gross_profit,
			"gross_margin": gross_margin
		})
	
	return data

def get_group_costs(mold_projects):
	"""Get aggregated costs for a list of mold projects."""
	if not mold_projects:
		return {}
	
	placeholders = ", ".join(["%s"] * len(mold_projects))
	
	cost_data = frappe.db.sql("""
		SELECT cost_type, SUM(amount) as total
		FROM `tabMold Cost Ledger`
		WHERE mold_project IN ({placeholders})
		GROUP BY cost_type
	""".format(placeholders=placeholders), tuple(mold_projects), as_dict=True)
	
	costs = {}
	for row in cost_data:
		costs[row.cost_type] = row.total
	
	return costs

def get_conditions(filters):
	conditions = ""
	
	if filters.get("customer"):
		conditions += " AND mp.customer = %(customer)s"
	
	if filters.get("company_entity"):
		conditions += " AND mp.company_entity = %(company_entity)s"
	
	if filters.get("from_date"):
		conditions += " AND mp.creation >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND mp.creation <= %(to_date)s"
	
	return conditions

def get_chart(data, filters):
	if not data:
		return None
	
	labels = [d["group_field"][:20] for d in data[:10]]  # Truncate long names
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("销售额"),
					"values": [d["total_sales"] for d in data[:10]]
				},
				{
					"name": _("毛利"),
					"values": [d["gross_profit"] for d in data[:10]]
				}
			]
		},
		"type": "bar"
	}
