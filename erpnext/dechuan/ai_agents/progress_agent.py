import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def query_mold_progress(keyword):
    """
    AI Agent 入口：查询模具进度
    """
    # 模拟简单的 NLP 意图识别
    if not keyword:
        return {"text": "请输入查询关键词，例如模具编号或客户名称"}

    # 1. 尝试按模具编号查询
    mold = frappe.db.get_value("Mold Project", {"mold_number": keyword, "project_name": keyword}, "name")
    
    if not mold:
        # 2. 尝试模糊搜索
        molds = frappe.get_all("Mold Project", filters={"project_name": ["like", f"%{keyword}%"]}, fields=["name", "project_name", "mold_status"])
        if len(molds) == 1:
            mold = molds[0].name
        elif len(molds) > 1:
            return {
                "text": f"找到多个相关模具，请明确编号：\n" + "\n".join([f"{m.name} ({m.project_name})" for m in molds])
            }
    
    if mold:
        doc = frappe.get_doc("Mold Project", mold)
        info = doc.get_progress_summary()
        return {
            "text": f"【查询结果】\n模具: {info['mold_number']}\n项目: {info['project_name']}\n状态: {info['status']}\n计划交期: {info['delivery_date']}\n图纸: {info['drawing_status']}"
        }
    
    return {"text": "未找到相关模具信息"}
