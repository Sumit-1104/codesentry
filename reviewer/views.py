from django.shortcuts import render
from core.orchestrator import graph
import os
import zipfile
import shutil


def review_report(request):
    """
    GET request pe: upload form dikhata hai.
    POST request pe: uploaded zip ko extract karke, andar ke saare
    .py files ko ek-ek karke analyze karta hai.
    """
    
    if request.method == "POST" and request.FILES.get("code_file"):
        uploaded_file = request.FILES["code_file"]
        
        # Purana extraction folder saaf karo (agar hai)
        extract_dir = os.path.join("data", "extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        all_results = []
        
        if uploaded_file.name.endswith(".zip"):
            # Zip file ko temporarily save karo
            zip_path = os.path.join("data", "temp_upload.zip")
            with open(zip_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Zip ko extract karo
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Andar ke saare .py files dhoondo (skip venv/pycache folders)
            for root, dirs, files in os.walk(extract_dir):
                dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__", ".git")]
                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        result = graph.invoke({"filepath": filepath})
                        all_results.append({
                            "filename": os.path.relpath(filepath, extract_dir),
                            "static_results": result.get("static_results", []),
                            "security_results": result.get("security_results", []),
                            "doc_results": result.get("doc_results", ""),
                            "test_results": result.get("test_results", ""),
                        })
        else:
            # Single .py file ka purana wala flow
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
        
        return render(request, "reviewer/report.html", {
            "all_results": all_results,
            "show_results": True,
        })
    
    return render(request, "reviewer/report.html", {"show_results": False})