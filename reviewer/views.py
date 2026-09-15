from django.shortcuts import render, redirect
from django.http import HttpResponse
from core.orchestrator import graph
from reviewer.language_utils import detect_language, is_analyzable
from reviewer.generic_reviewer import generate_generic_review
from reviewer.models import AnalysisHistory
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import zipfile
import shutil
import subprocess
import stat
import json
import io
import re
import markdown as md


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
        review_html = md.markdown(review, extensions=["tables"])
        return {
            "filename": relative_name,
            "language": "other",
            "generic_review": review_html,
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


def calculate_grade(total_issues, total_security, total_files):
    """
    Ye function issues count ke basis pe ek simple letter grade deta hai.
    Security issues zyada weight rakhte hai (2x) kyuki wo critical hote hai.
    """
    if total_files == 0:
        return "N/A"

    weighted_issues = total_issues + (total_security * 2)
    issues_per_file = weighted_issues / total_files

    if issues_per_file == 0:
        return "A+"
    elif issues_per_file < 2:
        return "A"
    elif issues_per_file < 4:
        return "B"
    elif issues_per_file < 7:
        return "C"
    else:
        return "D"


def strip_markdown(text):
    """
    Ye function markdown symbols (**, #, |, waghera) hata deta hai
    taaki PDF mein plain readable text dikhe.
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def generate_pdf(source_name, grade, total_files, total_issues, total_security, all_results):
    """
    Ye function poore analysis result ko ek professional PDF report
    mein convert karta hai, reportlab library use karke.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("CodeSentry Analysis Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Source: {source_name}", styles["Normal"]))
    story.append(Paragraph(f"Grade: {grade} | Files: {total_files} | Issues: {total_issues} | Security: {total_security}", styles["Normal"]))
    story.append(Spacer(1, 20))

    for file_result in all_results:
        story.append(Paragraph(file_result["filename"], styles["Heading2"]))

        if file_result.get("language") == "python":
            story.append(Paragraph("Static Analysis:", styles["Heading3"]))
            for issue in file_result.get("static_results", []):
                story.append(Paragraph(f"Line {issue['line']}: {issue['message']}", styles["Normal"]))

            story.append(Paragraph("Security:", styles["Heading3"]))
            for issue in file_result.get("security_results", []):
                story.append(Paragraph(f"Line {issue['line']} [{issue['severity']}]: {issue['message']}", styles["Normal"]))

            story.append(Paragraph("Suggested Docstrings:", styles["Heading3"]))
            doc_text = strip_markdown(file_result.get("doc_results", "") or "")
            story.append(Paragraph(doc_text.replace("\n", "<br/>"), styles["Normal"]))
        else:
            story.append(Paragraph("AI Code Review:", styles["Heading3"]))
            review_text = strip_markdown(file_result.get("generic_review", "") or "")
            story.append(Paragraph(review_text.replace("\n", "<br/>"), styles["Normal"]))

        story.append(Spacer(1, 16))

    doc.build(story)
    buffer.seek(0)
    return buffer


@login_required
def dashboard_view(request):
    """
    Home/landing page — user yaha se decide karta hai
    New Analysis karna hai ya History dekhni hai.
    """
    total_analyses = AnalysisHistory.objects.filter(user=request.user).count()
    return render(request, "reviewer/dashboard.html", {
        "total_analyses": total_analyses,
    })


@login_required
def review_report(request):
    """
    3 tarike se input le sakta hai: single file, .zip file, ya GitHub URL.
    Har language ki file analyze hoti hai (Python: full agents, others: LLM review).
    Result ko history mein bhi save karta hai, summary stats aur grade bhi bhejta hai.
    """

    if request.method == "POST":
        extract_dir = os.path.join("data", "extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, onerror=remove_readonly)

        all_results = []
        source_name = ""

        github_url = request.POST.get("github_url", "").strip()
        if github_url:
            source_name = github_url
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
            source_name = uploaded_file.name

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

        entry = AnalysisHistory.objects.create(
            user=request.user,
            source_name=source_name,
            results_json=json.dumps(all_results)
        )

        total_issues = sum(len(r.get("static_results", [])) for r in all_results)
        total_security = sum(len(r.get("security_results", [])) for r in all_results)
        grade = calculate_grade(total_issues, total_security, len(all_results))

        return render(request, "reviewer/report.html", {
            "all_results": all_results,
            "show_results": True,
            "total_files": len(all_results),
            "total_issues": total_issues,
            "total_security": total_security,
            "grade": grade,
            "history_id": entry.id,
        })

    return render(request, "reviewer/report.html", {"show_results": False})


def signup_view(request):
    """
    Naya user account banane ke liye. Django ka built-in
    UserCreationForm use karte hai (username + password).
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()

    return render(request, "reviewer/signup.html", {"form": form})


@login_required
def history_view(request):
    """
    Logged-in user ki saari purani analysis reports dikhata hai,
    jaise ChatGPT ka chat history sidebar.
    """
    history = AnalysisHistory.objects.filter(user=request.user)
    return render(request, "reviewer/history.html", {"history": history})


@login_required
def history_detail_view(request, history_id):
    """
    Ek specific purani report ka poora result dikhata hai.
    """
    entry = AnalysisHistory.objects.get(id=history_id, user=request.user)
    results = entry.get_results()

    total_issues = sum(len(r.get("static_results", [])) for r in results)
    total_security = sum(len(r.get("security_results", [])) for r in results)
    grade = calculate_grade(total_issues, total_security, len(results))

    return render(request, "reviewer/report.html", {
        "all_results": results,
        "show_results": True,
        "total_files": len(results),
        "total_issues": total_issues,
        "total_security": total_security,
        "grade": grade,
        "history_id": history_id,
    })


@login_required
def download_pdf_view(request, history_id):
    """
    Ek history entry ko PDF mein convert karke download karwata hai.
    """
    entry = AnalysisHistory.objects.get(id=history_id, user=request.user)
    results = entry.get_results()

    total_issues = sum(len(r.get("static_results", [])) for r in results)
    total_security = sum(len(r.get("security_results", [])) for r in results)
    grade = calculate_grade(total_issues, total_security, len(results))

    buffer = generate_pdf(entry.source_name, grade, len(results), total_issues, total_security, results)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="codesentry_report_{history_id}.pdf"'
    return response