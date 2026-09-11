# Ye file batati hai ki ek file kis programming language mein hai,
# file extension dekh kar.

PYTHON_EXTENSIONS = {".py"}


def detect_language(filepath):
    """
    Simple extension-based detection.
    Return 'python' ya 'other'.
    """
    if any(filepath.endswith(ext) for ext in PYTHON_EXTENSIONS):
        return "python"
    return "other"


def is_analyzable(filepath):
    """
    Kuch files bilkul analyze karne layak nahi hoti (images, binaries, etc.)
    Ye function unhe filter karta hai.
    """
    skip_extensions = (
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".pyc",
        ".lock", ".lnk", ".map", ".sqlite3", ".db"
    )
    return not filepath.lower().endswith(skip_extensions)