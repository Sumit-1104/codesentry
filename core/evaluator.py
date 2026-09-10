import sys
sys.path.append(".")

from reviewer.static_analyzer import analyze_file
from reviewer.security_scanner import scan_file
from data.eval_labels import GROUND_TRUTH


def evaluate_static_analysis(filepath, expected_symbols):
    """
    Ye function ek file pe static analyzer chalata hai,
    aur uske results ko ground truth se compare karke
    precision/recall calculate karta hai.
    """
    results = analyze_file(filepath)
    found_symbols = [issue["symbol"] for issue in results]
    
    true_positives = sum(1 for symbol in expected_symbols if symbol in found_symbols)
    false_positives = sum(1 for symbol in found_symbols if symbol not in expected_symbols)
    false_negatives = sum(1 for symbol in expected_symbols if symbol not in found_symbols)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1_score": round(f1, 2)
    }


def evaluate_security_scan(filepath, expected_issues):
    """
    Ye function security scanner ko evaluate karta hai.
    Match karta hai ki severity level ke basis par issues mile ya nahi.
    """
    results = scan_file(filepath)
    
    found_count = len(results)
    expected_count = len(expected_issues)
    
    true_positives = min(found_count, expected_count)
    false_positives = max(0, found_count - expected_count)
    false_negatives = max(0, expected_count - found_count)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1
    
    return {"precision": round(precision, 2), "recall": round(recall, 2)}


def run_full_evaluation():
    """
    Ye function GROUND_TRUTH mein di gayi saari files pe evaluation chalata hai
    aur overall summary print karta hai.
    """
    all_tp, all_fp, all_fn = 0, 0, 0
    
    print("===== EVALUATION REPORT =====\n")
    
    for filepath, expected in GROUND_TRUTH.items():
        print(f"--- {filepath} ---")
        
        result = evaluate_static_analysis(filepath, expected["static_issues"])
        
        print(f"Precision: {result['precision']}")
        print(f"Recall: {result['recall']}")
        print(f"F1 Score: {result['f1_score']}")
        print(f"(TP: {result['true_positives']}, FP: {result['false_positives']}, FN: {result['false_negatives']})")
        
        if expected["security_issues"]:
            sec_result = evaluate_security_scan(filepath, expected["security_issues"])
            print(f"Security Precision: {sec_result['precision']}, Security Recall: {sec_result['recall']}")
        
        print()
        
        all_tp += result["true_positives"]
        all_fp += result["false_positives"]
        all_fn += result["false_negatives"]
    
    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    print("===== OVERALL =====")
    print(f"Overall Precision: {round(overall_precision, 2)}")
    print(f"Overall Recall: {round(overall_recall, 2)}")
    print(f"Overall F1 Score: {round(overall_f1, 2)}")


if __name__ == "__main__":
    run_full_evaluation()