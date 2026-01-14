
import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.financial_reasoning import compute_metric_with_reasoning

def test_row_based_revenue():
    print("\nTesting Row-Based Revenue Extraction...")
    
    # Mocking a 10-Q Income Statement
    # Column matching 'revenue' is NOT present in headers.
    # Instead, "Net sales" is in the first column.
    
    df = pd.DataFrame({
        "Category": ["Net sales", "Cost of sales", "Gross margin"],
        "Three Months Ended Dec 30, 2023": ["$119,575,000", "$64,000,000", "$55,000,000"],
        "Three Months Ended Dec 31, 2022": ["$117,154,000", "$63,000,000", "$54,000,000"]
    })
    
    # Simulate table dictionary structure
    tables = [{"df": df, "source": "page_3", "page": 3}]
    question = "What is the revenue?"
    
    result = compute_metric_with_reasoning("revenue", tables, question)
    
    if result["success"]:
        print(f"✅ Revenue extracted: ${result['result']:,.0f}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Confidence: {result['confidence']}")
    else:
        print("❌ Failed to extract revenue from row.")
        print(f"Reasoning: {result['reasoning']}")

if __name__ == "__main__":
    test_row_based_revenue()
