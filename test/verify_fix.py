
import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Testing imports...")
    from src.api.router import compute_metric_with_reasoning, route_query
    print("✅ Imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_revenue_extraction():
    print("\nTesting Revenue Extraction...")
    
    # Create a mock table with revenue data
    df = pd.DataFrame({
        "Year": [2021, 2022, 2023],
        "Revenue": [1000000.0, 5000000.0, 15000000.0]  # Values > 1M but < 100M (previously rejected if no billions)
    })
    
    tables = [{"df": df, "source": "test_table"}]
    question = "What is the revenue?"
    
    result = compute_metric_with_reasoning("revenue", tables, question)
    
    if result["success"]:
        print(f"✅ Revenue extraction successful: ${result['result']:,.0f}")
        print(f"Reasoning: {result['reasoning']}")
    else:
        print(f"❌ Revenue extraction failed: {result['reasoning']}")

if __name__ == "__main__":
    test_revenue_extraction()
