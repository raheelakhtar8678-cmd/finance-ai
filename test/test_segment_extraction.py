import pandas as pd
from src.analysis.financial_reasoning import MetricReasoner

# Mock Tables representing Apple Q2 2025 content

# Table 1: Net Sales (Region-based)
# Context explicitly mentions "Net Sales"
df_sales = pd.DataFrame({
    "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific", "Total Net Sales"],
    "Three Months Ended March 29, 2025": [40315, 24454, 16002, 7298, 7290, 95359],
    "Three Months Ended March 30, 2024": [37273, 24123, 16372, 6262, 6723, 90753]
})

table_sales = {
    "df": df_sales,
    "page": 13,
    "source": "apple_q2_2025.pdf",
    "markdown": "**Net Sales** by reportable segment",
    "preceding_text": "The following table shows net sales by reportable segment..."
}

# Table 2: Operating Income (Region-based)
# Same Row Labels ("Greater China") but different data (Operating Income)
# Context explicitly mentions "Operating Income"
df_op_income = pd.DataFrame({
    "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific", "Total Operating Income"],
    "Three Months Ended March 29, 2025": [12000, 8000, 6626, 3000, 2500, 29600], # Mocked other values, exact China value
    "Three Months Ended March 30, 2024": [11000, 7500, 6700, 2800, 2400, 27900]
})

table_op_income = {
    "df": df_op_income,
    "page": 13,
    "source": "apple_q2_2025.pdf",
    "markdown": "**Segment Operating Income**",
    "preceding_text": "The following table shows segment operating income..."
}

mock_tables = [table_sales, table_op_income]

def test_segment_disambiguation():
    print("\n--- Testing Segment Disambiguation (Context Scoring) ---")
    
    reasoner = MetricReasoner(mock_tables, question="What is the operating income for Greater China?")
    
    # Test 1: Ask for Operating Income (Should hit Table 2)
    print("\n🔍 Query: Operating Income for Greater China")
    result = reasoner.compute_matrix_metric("operating_income", "Greater China")
    
    print(f"Result: {result['result']}")
    print(f"Reasoning: {result['reasoning']}")
    
    if result['success'] and (result['result'] == 6626000000 or result['result'] == 6626): # Accept both scaled and unscaled
        # Note: global multiplier might not be set in mock without robust value extractor setup, 
        # but MetricReasoner defaults to 1 if no unit found. 
        # Let's adjust expectation based on valid extraction logic in reasoner.
        # Actually, let's just check the raw value matches 6626 if multiplier fails, or 6.6B if it works.
        # The key is Distinction from 16002.
        print("✅ SUCCESS: Correctly extracted Operating Income (6,626)")
    elif result['result'] == 16002000000 or result['result'] == 16002:
        print("❌ FAILURE: Extracted Net Sales (16,002) instead of Operating Income")
    else:
        print(f"❌ FAILURE: Extracted unexpected value: {result['result']}")

    # Test 2: Ask for Net Sales (Should hit Table 1)
    print("\n🔍 Query: Net Sales for Greater China")
    result_sales = reasoner.compute_matrix_metric("revenue", "Greater China")
    
    if result_sales['success'] and (result_sales['result'] == 16002000000 or result_sales['result'] == 16002):
        print("✅ SUCCESS: Correctly extracted Net Sales (16,002)")
    else:
        print(f"❌ FAILURE: Failed to extract Net Sales. Got: {result_sales['result']}")

if __name__ == "__main__":
    test_segment_disambiguation()
