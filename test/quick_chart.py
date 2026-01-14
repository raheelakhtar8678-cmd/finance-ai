
from src.visualization.chart_generator import generate_chart
import pandas as pd
import json

def test_chart_gen():
    print("Testing Chart Generator...")
    
    # Mock data for comparison
    df = pd.DataFrame([
        {"Segment": "Greater China", "Metric": "Operating Income", "Value": 6626, "Period": "2025"},
        {"Segment": "Greater China", "Metric": "Operating Income", "Value": 6700, "Period": "2024"},
    ])
    
    try:
        # Test 1: Comparison Bar Chart
        print("\n1. Generating Comparison Chart:")
        chart_json = generate_chart(df, x_col="Period", y_col="Value", title="Comparison of Greater China Operating Income")
        if chart_json and "success" in chart_json:
            print("   ✅ Chart generated successfully")
        else:
            print(f"   ❌ Chart generation failed: {chart_json}")
            
        # Test 2: Trend Line Chart
        print("\n2. Generating Trend Chart:")
        df_trend = pd.DataFrame([
            {"Date": "2024-01-01", "Value": 100},
            {"Date": "2024-04-01", "Value": 120},
            {"Date": "2024-07-01", "Value": 115},
        ])
        chart_json_2 = generate_chart(df_trend, x_col="Date", y_col="Value", title="Revenue Trend")
        if chart_json_2 and "success" in chart_json_2:
            print("   ✅ Trend chart generated successfully")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_chart_gen()
