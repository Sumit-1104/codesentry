import subprocess
import json


def analyze_file(filepath):
    """
    Ye function pylint ko chalata hai ek Python file pe,
    aur usse jo issues milte hai unhe clean format mein return karta hai.
    """
    
    # pylint ko command line se chalate hai, JSON format mein output maangte hai
    result = subprocess.run(
        ["pylint", filepath, "--output-format=json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    
    # pylint ka output text hota hai, usko Python list/dict mein convert karte hai
    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        issues = []
    
    # Har issue ko simple, readable format mein badalte hai
    clean_issues = []
    for issue in issues:
        clean_issues.append({
            "line": issue.get("line"),
            "type": issue.get("type"),
            "message": issue.get("message"),
            "symbol": issue.get("symbol")
        })
    
    return clean_issues


if __name__ == "__main__":
    # Direct test karne ke liye (agar ye file seedha run kare)
    results = analyze_file("data/sample_code.py")
    for issue in results:
        print(f"Line {issue['line']} [{issue['type']}]: {issue['message']}")