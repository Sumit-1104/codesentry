import sys
sys.path.append(".")

from reviewer.security_scanner import scan_file


def test_scan_file_returns_list():
    """Test kar ki scan_file hamesha ek list return kare."""
    result = scan_file("data/insecure_code.py")
    assert isinstance(result, list)


def test_scan_file_detects_shell_true():
    """
    Test kar ki insecure_code.py mein jo shell=True wala
    dangerous pattern hai, wo pakड़a jaye.
    """
    result = scan_file("data/insecure_code.py")
    messages = [issue["message"] for issue in result]
    assert any("shell=True" in msg for msg in messages)


def test_scan_file_clean_code_has_no_high_severity():
    """
    Test kar ki clean file (sample_code.py) mein koi
    HIGH severity security issue na ho.
    """
    result = scan_file("data/sample_code.py")
    high_severity = [issue for issue in result if issue.get("severity") == "HIGH"]
    assert len(high_severity) == 0