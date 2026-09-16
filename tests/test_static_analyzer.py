import sys
sys.path.append(".")

from reviewer.static_analyzer import analyze_file


def test_analyze_file_returns_list():
    """
    Test kar ki analyze_file hamesha ek list return kare,
    chahe koi bhi file diya jaye.
    """
    result = analyze_file("data/sample_code.py")
    assert isinstance(result, list)


def test_analyze_file_detects_unused_import():
    """
    Test kar ki humari sample_code.py mein jo jaanbujh kar
    unused import daala tha (os), wo pakड़a jaye.
    """
    result = analyze_file("data/sample_code.py")
    symbols = [issue["symbol"] for issue in result]
    assert "unused-import" in symbols


def test_analyze_file_each_issue_has_required_fields():
    """
    Test kar ki har issue mein zaroori fields (line, type, message) hai.
    """
    result = analyze_file("data/sample_code.py")
    for issue in result:
        assert "line" in issue
        assert "type" in issue
        assert "message" in issue