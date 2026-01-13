
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from erpnext.dechuan.custom_fields import get_dechuan_custom_fields

def update_fields():
    """
    Applies the custom fields defined in erpnext.dechuan.custom_fields to the database immediately.
    Usage: bench execute erpnext.dechuan.scripts.install_custom_fields.update_fields
    """
    custom_fields = get_dechuan_custom_fields()
    print("Updating Custom Fields...")
    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()
    print("Custom Fields Updated Successfully.")
