
import frappe
from frappe import _

def create_mold_project_on_submit(doc, method):
    """
    Hook triggered when Sales Order is submitted.
    Creates a Mold Project for each item in the Sales Order if not already exists.
    """
    company_entity = "德川"
    
    # Check for custom field 'company_entity' (added via hooks/custom_fields)
    if hasattr(doc, "company_entity") and doc.company_entity:
        company_entity = doc.company_entity
    elif doc.company:
        if "裕霖" in doc.company:
            company_entity = "裕霖"
        elif "德川" in doc.company:
            company_entity = "德川"
    
    # Iterate through Sales Order items
    for item in doc.items:
        # Check if Mold Project already exists for this SO and Item
        # Uses 'sales_order' field and 'project_name' (Item Name) to check uniqueness vaguely
        # Better if Mold Project had 'sales_order_item' field, but it doesn't.
        # We will check if any Mold Project linked to this SO has the same project name.
        
        exists = frappe.db.exists("Mold Project", {
            "sales_order": doc.name,
            "project_name": item.item_name
        })
        
        if exists:
            continue
            
        # Create new Mold Project
        mold_project = frappe.new_doc("Mold Project")
        mold_project.project_name = item.item_name
        mold_project.customer = doc.customer
        mold_project.company_entity = company_entity
        mold_project.mold_status = "立项"
        mold_project.sales_order = doc.name
        
        if item.delivery_date:
            mold_project.planned_delivery_date = item.delivery_date
        elif doc.delivery_date:
            mold_project.planned_delivery_date = doc.delivery_date
            
        # Optional: Map other fields if available in Item
        # mold_project.mold_type = ...
        
        mold_project.insert(ignore_permissions=True)
        frappe.msgprint(_("Mold Project {0} created for Item {1}").format(mold_project.name, item.item_name))

