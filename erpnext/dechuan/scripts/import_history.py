
import frappe
import csv
import os

def import_mold_history(csv_path):
    """
    Import historical Mold Projects from a CSV file.
    CSV Header Expected: project_name, customer, company_entity, mold_status, delivery_date
    Usage: bench execute erpnext.dechuan.scripts.import_history.import_mold_history --args '/absolute/path/to/data.csv'
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Starting import from {csv_path}...")
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_name = row.get('project_name')
            if not project_name:
                continue

            # Check for existing project by name
            if frappe.db.exists("Mold Project", {"project_name": project_name}):
                print(f"Skipping {project_name}: Already exists.")
                continue

            try:
                doc = frappe.new_doc("Mold Project")
                doc.project_name = project_name
                doc.customer = row.get('customer')
                
                # Default entity if missing
                entity = row.get('company_entity')
                if not entity or entity not in ['德川', '裕霖']:
                    entity = '德川'
                doc.company_entity = entity
                
                doc.mold_status = row.get('mold_status') or '立项'
                
                if row.get('delivery_date'):
                    doc.planned_delivery_date = row.get('delivery_date')
                
                # Fill other fields if present in CSV and Model
                # doc.cavities = row.get('cavities')
                
                doc.insert()
                print(f"Created: {doc.name} ({project_name})")
                count += 1
            except Exception as e:
                print(f"Failed to create {project_name}: {str(e)}")
                # frappe.log_error(e, f"Import Error for {project_name}")

    if count > 0:
        frappe.db.commit()
    print(f"Import completed. {count} records created.")

