# Ye file manually likhi gayi hai - hume pata hai in files mein kaunse
# issues actually maujood hai (ground truth), jisse hum agent ki accuracy naap sakte hai.

GROUND_TRUTH = {
    "data/sample_code.py": {
        "static_issues": [
            "unused-import",       # os
            "unused-import",       # sys
            "unused-variable",     # x
            "invalid-name",        # userManager
            "missing-module-docstring",
            "missing-class-docstring",
            "missing-function-docstring",
        ],
        "security_issues": []  # is file mein koi security issue nahi hai
    },
    "data/insecure_code.py": {
        "static_issues": [],
        "security_issues": [
            "hardcoded_password",
            "subprocess_shell_true",
        ]
    }
}