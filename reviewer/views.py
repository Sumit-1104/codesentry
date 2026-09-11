from django.shortcuts import render
from core.orchestrator import graph
from reviewer.language_utils import detect_language, is_analyzable
from reviewer.generic_reviewer import generate_generic_review
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def analyze_single_file(filepath, directory):
    """
    Ye function ek single file ko analyze karta hai (language detect karke),
    aur uska result return karta hai. Thread pool mein parallel call hota hai.
    """
    language = detect_language(filepath)
    relative_name = os.path.relpath(filepath, directory)
    
    if language == "python":
        result = graph.invoke({"filepath": filepath})
        return {
            "filename": relative_name,
            "language": "python",
            "static_results": result.get("static_results", []),
            "security_results": result.get("security_results", []),
            "doc_results": result.get("doc_results", ""),
            "test_results": result.get("test_results", ""),
        }
    else:
        review = generate_generic_review(filepath)
        return {
            "filename": relative_name,
            "language": "other",
            "generic_review": review,
        }


def analyze_directory(directory):
    """
    Ye function ek folder ke andar ke saare analyzable files dhoondh ke
    unhe PARALLEL mein (thread pool se) analyze karta hai, taaki fast ho.
    """
    filepaths = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__", ".git", "node_modules")]
        for file in files:
            filepath = os.path.join(root, file)
            if is_analyzable(filepath):
                filepaths.append(filepath)
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_filepath = {
            executor.submit(analyze_single_file, fp, directory): fp
            for fp in filepaths
        }
        
        for future in as_completed(future_to_filepath):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                filepath = future_to_filepath[future]
                all_results.append({
                    "filename": os.path.relpath(filepath, directory),
                    "language": "other",
                    "generic_review": f"Error analyzing this file: {str(e)}"
                })
    
    return all_results


def review_report(request):
    """
    3 tarike se input le sakta hai: single file, .zip file, ya GitHub URL.
    Har language ki file analyze hoti hai (Python: full agents, others: LLM review).
    """
    
    if request.method == "POST":
        extract_dir = os.path.join("data", "extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, onerror=remove_readonly)
        
        all_results = []
        
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
        
        elif request.FILES.get("code_file"):
            os.makedirs(extract_dir, exist_ok=True)
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
                temp_path = os.path.join(extract_dir, uploaded_file.name)
                with open(temp_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                all_results = analyze_directory(extract_dir)
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