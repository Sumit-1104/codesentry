import subprocess
import sys
sys.path.append(".")

from core.orchestrator import graph


def get_changed_python_files():
    """
    Ye function git diff use karke pata karta hai ki PR mein
    kaunsi .py files change hui hai.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True,
        text=True
    )
    
    files = result.stdout.strip().split("\n")
    python_files = [f for f in files if f.endswith(".py") and f != ""]
    return python_files


def generate_markdown_report(filepath, result):
    """
    Ye function ek file ke result ko GitHub comment ke liye
    readable Markdown format mein banata hai.
    """
    md = f"### 📄 `{filepath}`\n\n"
    
    static_issues = result.get("static_results", [])
    if static_issues:
        md += "**Static Analysis Issues:**\n"
        for issue in static_issues[:5]:  # sirf top 5 dikhao, comment lamba na ho
            md += f"- Line {issue['line']}: {issue['message']}\n"
        md += "\n"
    
    security_issues = result.get("security_results", [])
    if security_issues:
        md += "**⚠️ Security Issues:**\n"
        for issue in security_issues:
            md += f"- Line {issue['line']} [{issue['severity']}]: {issue['message']}\n"
        md += "\n"
    
    if not static_issues and not security_issues:
        md += "✅ No issues found.\n\n"
    
    return md


def main():
    changed_files = get_changed_python_files()
    
    if not changed_files:
        report = "## 🤖 CodeSentry Review\n\nNo Python files changed in this PR."
    else:
        report = "## 🤖 CodeSentry Review\n\n"
        for filepath in changed_files:
            try:
                result = graph.invoke({"filepath": filepath})
                report += generate_markdown_report(filepath, result)
            except Exception as e:
                report += f"### 📄 `{filepath}`\n\nCould not analyze: {str(e)}\n\n"
    
    # Report ko ek file mein likho, taaki GitHub Action isse padh sake
    with open("pr_review_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("Report generated successfully.")


if __name__ == "__main__":
    main()