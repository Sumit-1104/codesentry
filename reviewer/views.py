from django.shortcuts import render
from core.orchestrator import graph
import os
import zipfile
import shutil
import subprocess
import stat


def remove_readonly(func, path, excinfo):
    """
    Ye function un files ko delete karne mein madad karta hai
    jo read-only hai (jaise Git ki .git folder files Windows pe).
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def analyze_directory(directory):
    """
    Ye function ek folder ke andar ke saare .py files
    dhoondh ke unpe orchestrator chalata hai.
    """
    all_results = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__", ".git")]
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                result = graph.invoke({"filepath": filepath})
                all_results.append({
                    "filename": os.path.relpath(filepath, directory),
                    "static_results": result.get("static_results", []),
                    "security_results": result.get("security_results", []),
                    "doc_results": result.get("doc_results", ""),
                    "test_results": result.get("test_results", ""),
                })
    return all_results


def review_report(request):
    """
    3 tarike se input le sakta hai: single .py file, .zip file, ya GitHub URL.
    """
    
    if request.method == "POST":
        extract_dir = os.path.join("data", "extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, onerror=remove_readonly)
        os.makedirs(extract_dir)
        
        all_results = []
        
        # Case 1: GitHub URL diya gaya hai
        github_url = request.POST.get("github_url", "").strip()
        if github_url:
            try:
                result = subprocess.run(
                    ["git", "clone", github_url, extract_dir],
                    capture_output=True
                )
                if result.returncode != 0:
                    raise Exception(result.stderr.decode("utf-8", errors="ignore"))
                all_results = analyze_directory(extract_dir)
            except Exception as e:
                return render(request, "reviewer/report.html", {
                    "show_results": False,
                    "error": f"Could not clone repo: {str(e)}"
                })
        
        # Case 2: File upload hua hai (.py ya .zip)
        elif request.FILES.get("code_file"):
            uploaded_file = request.FILES["code_file"]
            
            if uploaded_file.name.endswith(".zip"):
                zip_path = os.path.join("data", "temp_upload.zip")
                with open(zip_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
                all_results = analyze_directory(extract_dir)
            else:
                temp_path = os.path.join("data", "uploaded_" + uploaded_file.name)
                with open(temp_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                result = graph.invoke({"filepath": temp_path})
                all_results.append({
                    "filename": uploaded_file.name,
                    "static_results": result.get("static_results", []),
                    "security_results": result.get("security_results", []),
                    "doc_results": result.get("doc_results", ""),
                    "test_results": result.get("test_results", ""),
                })
        else:
            return render(request, "reviewer/report.html", {
                "show_results": False,
                "error": "Please provide a GitHub URL or upload a file."
            })
        
        return render(request, "reviewer/report.html", {
            "all_results": all_results,
            "show_results": True,
        })
    
    return render(request, "reviewer/report.html", {"show_results": False})