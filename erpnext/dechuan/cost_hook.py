
import frappe
from frappe import _

def create_cost_ledger_entry(doc, method):
    """
    Hook triggered on Purchase Receipt / Purchase Invoice Submit.
    Creates a Mold Cost Ledger entry if the document is linked to a Mold Project.
    """
    
    # 1. Check if linked to Mold Project
    mold_project = doc.get("mold_project")
    if not mold_project:
        return

    # 2. Determine Cost Type based on Document Type
    # Typically PR is Material, but could be Subcontracting (Outsourcing)
    # This logic can be refined. For now, we assume "Material" for PR, "Outsourcing" if is_subcontracted
    
    cost_type = "Material"
    if doc.doctype == "Purchase Receipt" and doc.is_subcontracted:
        cost_type = "Outsourcing"
    # Additional logic for Purchase Invoice (e.g. Service PI -> Overhead?)
    
    # 3. Calculate Total Amount relevant to this Project
    # Since we linked at Header, we assume all items belong to this project.
    total_amount = doc.grand_total # Using Grand Total (incl. taxes? Usually cost excludes recoverable taxes, but keeping simple)
    
    # 4. Create Ledger Entry
    ledger_entry = frappe.new_doc("Mold Cost Ledger")
    ledger_entry.mold_project = mold_project
    ledger_entry.cost_type = cost_type
    ledger_entry.amount = total_amount
    ledger_entry.voucher_type = doc.doctype
    ledger_entry.voucher_no = doc.name
    ledger_entry.posting_date = doc.posting_date
    ledger_entry.description = f"Auto-created from {doc.doctype} {doc.name}"
    
    ledger_entry.insert(ignore_permissions=True)
    
    frappe.msgprint(_("Mold Cost Ledger Entry created: {0}").format(ledger_entry.name))

def on_cancel_cost_ledger_entry(doc, method):
    """
    Hook triggered on Cancel.
    Cancels the associated Mold Cost Ledger entry.
    """
    entries = frappe.get_all("Mold Cost Ledger", 
                             filters={"voucher_type": doc.doctype, "voucher_no": doc.name})
    
    for entry in entries:
        frappe.delete_doc("Mold Cost Ledger", entry.name)
        frappe.msgprint(_("Mold Cost Ledger Entry deleted: {0}").format(entry.name))
