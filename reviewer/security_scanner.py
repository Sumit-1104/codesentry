import subprocess
import json


def scan_file(filepath):
    """
    Ye function bandit ko chalata hai ek Python file pe,
    aur security vulnerabilities dhoondta hai.
    """
    
    result = subprocess.run(
        ["bandit", "-f", "json", filepath],
        capture_output=True,
        text=True
    )
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {}
    
    clean_issues = []
    for issue in data.get("results", []):
        clean_issues.append({
            "line": issue.get("line_number"),
            "severity": issue.get("issue_severity"),
            "confidence": issue.get("issue_confidence"),
            "message": issue.get("issue_text")
        })
    
    return clean_issues


if __name__ == "__main__":
    results = scan_file("data/insecure_code.py")
    for issue in results:
        print(f"Line {issue['line']} [{issue['severity']}]: {issue['message']}")