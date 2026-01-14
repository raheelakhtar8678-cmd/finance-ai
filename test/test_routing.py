
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.question_router import resolve_intent

def test_routing():
    test_cases = [
        ("What is the revenue?", "revenue"),
        ("Is it making a profit?", "profit"),
        ("What product brings revenue?", None), # Should be exclusions
        ("Show me a breakdown of revenue", None), # Should be exclusions
        ("Which segment has highest sales?", None), # Should be exclusions
    ]
    
    print("🧪 Testing Router Logic...")
    for q, expected in test_cases:
        metric, _ = resolve_intent(q)
        status = "✅ PASS" if metric == expected else f"❌ FAIL (Got {metric}, Expected {expected})"
        print(f"{status} | Q: '{q}'")

if __name__ == "__main__":
    test_routing()
