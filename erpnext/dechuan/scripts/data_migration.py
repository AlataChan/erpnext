# Copyright (c) 2026, Dechuan Team and contributors
# Data Migration and Test Fixtures Script

import frappe
import csv
import os
from frappe.utils import getdate, today, add_days, add_months

def import_customers(csv_path):
    """
    Import customers from CSV.
    CSV Header: customer_name, customer_type, default_company_entity, reconciliation_habit
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return 0

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('customer_name')
            if not name:
                continue
            
            if frappe.db.exists("Customer", {"customer_name": name}):
                print(f"Skipping {name}: Already exists.")
                continue
            
            try:
                doc = frappe.new_doc("Customer")
                doc.customer_name = name
                doc.customer_type = row.get('customer_type', 'Company')
                doc.default_company_entity = row.get('default_company_entity', '德川')
                doc.reconciliation_habit = row.get('reconciliation_habit', '月结30天')
                doc.insert()
                print(f"Created Customer: {doc.name}")
                count += 1
            except Exception as e:
                print(f"Failed: {name} - {str(e)}")
    
    if count > 0:
        frappe.db.commit()
    return count


def import_suppliers(csv_path):
    """
    Import suppliers from CSV.
    CSV Header: supplier_name, supplier_type, supplier_group
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return 0

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('supplier_name')
            if not name:
                continue
            
            if frappe.db.exists("Supplier", {"supplier_name": name}):
                print(f"Skipping {name}: Already exists.")
                continue
            
            try:
                doc = frappe.new_doc("Supplier")
                doc.supplier_name = name
                doc.supplier_type = row.get('supplier_type', 'Company')
                doc.supplier_group = row.get('supplier_group', 'All Supplier Groups')
                doc.insert()
                print(f"Created Supplier: {doc.name}")
                count += 1
            except Exception as e:
                print(f"Failed: {name} - {str(e)}")
    
    if count > 0:
        frappe.db.commit()
    return count


def create_test_fixtures():
    """
    Create test data for development/UAT.
    Usage: bench execute erpnext.dechuan.scripts.data_migration.create_test_fixtures
    """
    print("Creating test fixtures...")
    
    # 1. Create test customers
    test_customers = [
        {"name": "测试客户A", "entity": "德川", "habit": "月结30天"},
        {"name": "测试客户B", "entity": "裕霖", "habit": "月结60天"},
        {"name": "测试客户C", "entity": "德川", "habit": "货到付款"},
    ]
    
    for cust in test_customers:
        if not frappe.db.exists("Customer", {"customer_name": cust["name"]}):
            doc = frappe.new_doc("Customer")
            doc.customer_name = cust["name"]
            doc.customer_type = "Company"
            doc.default_company_entity = cust["entity"]
            doc.reconciliation_habit = cust["habit"]
            doc.insert()
            print(f"Created Customer: {doc.name}")
    
    # 2. Create test Mold Projects
    test_molds = [
        {"name": "测试模具-001", "customer": "测试客户A", "entity": "德川", "status": "设计"},
        {"name": "测试模具-002", "customer": "测试客户B", "entity": "裕霖", "status": "采购"},
        {"name": "测试模具-003", "customer": "测试客户A", "entity": "德川", "status": "试模"},
    ]
    
    for mold in test_molds:
        if not frappe.db.exists("Mold Project", {"project_name": mold["name"]}):
            doc = frappe.new_doc("Mold Project")
            doc.project_name = mold["name"]
            doc.customer = frappe.db.get_value("Customer", {"customer_name": mold["customer"]}, "name")
            doc.company_entity = mold["entity"]
            doc.mold_status = mold["status"]
            doc.planned_delivery_date = add_days(today(), 30)
            doc.insert()
            print(f"Created Mold Project: {doc.name}")
    
    # 3. Create test Drawing Confirmations (for reminder agent testing)
    mold_projects = frappe.get_all("Mold Project", limit=3)
    for mp in mold_projects:
        if not frappe.db.exists("Drawing Confirmation", {"mold_project": mp.name}):
            doc = frappe.new_doc("Drawing Confirmation")
            doc.mold_project = mp.name
            doc.drawing_type = "Formal Drawing"
            doc.status = "待工程确认"
            doc.insert()
            print(f"Created Drawing Confirmation: {doc.name}")
    
    frappe.db.commit()
    print("Test fixtures created successfully!")


def validate_data_integrity():
    """
    Validate data integrity before go-live.
    Usage: bench execute erpnext.dechuan.scripts.data_migration.validate_data_integrity
    """
    print("=" * 50)
    print("Data Integrity Validation Report")
    print("=" * 50)
    
    issues = []
    
    # 1. Check Mold Projects without customers
    orphan_molds = frappe.db.sql("""
        SELECT name, project_name FROM `tabMold Project` 
        WHERE customer IS NULL OR customer = ''
    """, as_dict=True)
    if orphan_molds:
        issues.append(f"Mold Projects without customer: {len(orphan_molds)}")
        for m in orphan_molds[:5]:
            print(f"  - {m.name}: {m.project_name}")
    
    # 2. Check Purchase Orders without Mold Project
    unlinked_pos = frappe.db.sql("""
        SELECT name FROM `tabPurchase Order` 
        WHERE docstatus = 1 AND (mold_project IS NULL OR mold_project = '')
    """, as_dict=True)
    if unlinked_pos:
        issues.append(f"Purchase Orders without Mold Project link: {len(unlinked_pos)}")
    
    # 3. Check Drawing Confirmations stuck in pending
    stuck_confirmations = frappe.db.sql("""
        SELECT name, status, DATEDIFF(NOW(), modified) as days_stuck
        FROM `tabDrawing Confirmation`
        WHERE status LIKE '待%' AND DATEDIFF(NOW(), modified) > 7
    """, as_dict=True)
    if stuck_confirmations:
        issues.append(f"Drawing Confirmations stuck > 7 days: {len(stuck_confirmations)}")
    
    # 4. Summary
    print("\n" + "=" * 50)
    if issues:
        print(f"Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print("✓ No data integrity issues found!")
    
    print("=" * 50)
    return len(issues)
