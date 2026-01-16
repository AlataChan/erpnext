# Copyright (c) 2026, Dechuan Team and contributors
# Experience Agent - Provides historical experience when dispatching work

import frappe
from frappe import _

@frappe.whitelist()
def get_similar_mold_experience(mold_project):
    """
    AI Agent Entry Point: Find similar historical molds and extract experience notes.
    Called when dispatching a work order or when engineer needs reference.
    
    Args:
        mold_project: The current Mold Project name
    
    Returns:
        dict with 'experiences' list containing historical notes
    """
    if not mold_project:
        return {"experiences": [], "message": "请指定模具项目"}
    
    # Get current mold details
    current_mold = frappe.get_doc("Mold Project", mold_project)
    
    # Find similar molds by:
    # 1. Same customer
    # 2. Similar mold_type (if defined)
    # 3. Within the last 2 years
    
    filters = {
        "name": ["!=", mold_project],
        "docstatus": ["<", 2]  # Not cancelled
    }
    
    # Prefer same customer
    similar_molds = frappe.get_all(
        "Mold Project",
        filters={**filters, "customer": current_mold.customer},
        fields=["name", "project_name", "mold_type", "mold_status"],
        order_by="creation desc",
        limit=10
    )
    
    experiences = []
    
    for mold in similar_molds:
        # Get Trial Reports with issues
        trial_issues = get_trial_issues(mold.name)
        
        # Get any notes/comments
        notes = get_project_notes(mold.name)
        
        if trial_issues or notes:
            experiences.append({
                "mold_project": mold.name,
                "project_name": mold.project_name,
                "issues": trial_issues,
                "notes": notes
            })
    
    # Format response for AI/Human consumption
    if not experiences:
        return {
            "experiences": [],
            "message": f"未找到客户 {current_mold.customer} 的历史模具经验记录"
        }
    
    return {
        "experiences": experiences,
        "message": f"找到 {len(experiences)} 个相关历史项目的经验记录"
    }


def get_trial_issues(mold_project):
    """Get trial reports with issues for a mold."""
    trials = frappe.get_all(
        "Trial Report",
        filters={
            "mold_project": mold_project,
            "final_verdict": ["in", ["不合格", "待确认"]]
        },
        fields=["name", "trial_count", "final_verdict", "disposition", "disposition_note"]
    )
    
    issues = []
    for trial in trials:
        if trial.disposition_note:
            issues.append({
                "trial": trial.name,
                "verdict": trial.final_verdict,
                "disposition": trial.disposition,
                "note": trial.disposition_note
            })
    
    return issues


def get_project_notes(mold_project):
    """Get comments/notes attached to a mold project."""
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Mold Project",
            "reference_name": mold_project,
            "comment_type": ["in", ["Comment", "Info"]]
        },
        fields=["content", "creation"],
        order_by="creation desc",
        limit=5
    )
    
    return [c.content for c in comments if c.content]


@frappe.whitelist()
def get_experience_summary_text(mold_project):
    """
    Get a formatted text summary of experiences for display or AI prompt.
    """
    result = get_similar_mold_experience(mold_project)
    
    if not result["experiences"]:
        return result["message"]
    
    lines = ["【历史经验汇总】\n"]
    
    for exp in result["experiences"]:
        lines.append(f"▶ 参考项目: {exp['project_name']} ({exp['mold_project']})")
        
        if exp["issues"]:
            lines.append("  问题记录:")
            for issue in exp["issues"]:
                lines.append(f"    - 试模{issue['trial']}: {issue['note'][:100]}...")
        
        if exp["notes"]:
            lines.append("  备注:")
            for note in exp["notes"][:3]:
                lines.append(f"    - {note[:80]}...")
        
        lines.append("")
    
    return "\n".join(lines)
