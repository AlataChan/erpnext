
import frappe
import sys
# Ensure the path is in python path if running standalone, though likely run via 'bench execute'
from erpnext.dechuan.ai_agents.progress_agent import query_mold_progress

def main(keyword=None):
    """
    Run the AI Agent to query mold progress.
    Can be run via 'bench execute erpnext.dechuan.ai_agents.run_agent.main --args "keyword"'
    """
    if not keyword:
        # If running interactively or no arg provided
        try:
            keyword = sys.argv[1]
        except IndexError:
            print("Please provide a keyword to query.")
            return

    print(f"Querying Agent for: {keyword}")
    result = query_mold_progress(keyword)
    print("------------------------------------------------")
    print(result.get("text"))
    print("------------------------------------------------")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        # Interactive mode if possible, but usually environment needs setup
        print("Usage: bench execute erpnext.dechuan.ai_agents.run_agent.main --args 'MOLD_ID'")
