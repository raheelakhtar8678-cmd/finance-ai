"""
Demo: Temporal Comparison with Greater China Operating Income
This demonstrates the exact query mentioned by the user.
"""

import pandas as pd
from src.analysis.query_controller import route_query
from src.visualization.chart_generator import generate_chart

# Simulate Apple Q2 2025 10-Q segment data
df_operating_income = pd.DataFrame({
    "Segment": [
        "Americas - Operating Income",
        "Europe - Operating Income", 
        "Greater China - Operating Income",
        "Japan - Operating Income",
        "Rest of Asia Pacific - Operating Income"
    ],
    "Three Months Ended March 29, 2025": [
        "12,453",
        "8,234",
        "6,626",  # Current period
        "3,123",
        "2,234"
    ],
    "Three Months Ended March 30, 2024": [
        "11,453",
        "7,234",
        "5,626",  # Prior period  
        "2,923",
        "1,934"
    ]
})

df_net_sales = pd.DataFrame({
    "Segment": [
        "Americas",
        "Europe",
        "Greater China",
        "Japan",
        "Rest of Asia Pacific",
        "Total Net Sales"
    ],
    "Three Months Ended March 29, 2025": [
        "37,264",
        "24,123",
        "16,002",
        "8,564",
        "6,047",
        "94,753"
    ],
    "Three Months Ended March 30, 2024": [
        "34,264",
        "22,123",
        "15,002",
        "7,564",
        "5,047",
        "90,753"
    ]
})

tables = [
    {"df": df_operating_income, "source": "Apple_Q2_2025.pdf", "page": 4},
    {"df": df_net_sales, "source": "Apple_Q2_2025.pdf", "page": 3}
]

print("=" * 70)
print("TEMPORAL COMPARISON DEMO: Greater China Operating Income")
print("=" * 70)
print()

# The exact type of query the user mentioned
query = "What was the operating income for Greater China for three months ended March 30, 2024 and March 29, 2025?"

print(f"Query: {query}\n")
print("-" * 70)

try:
    answer, chart_path = route_query(
        question=query,
        tables=tables,
        chart_gen=generate_chart,
        session_id="demo_session"
    )
    
    print("\n" + "=" * 70)
    print("ANSWER:")
    print("=" * 70)
    print(answer)
    
    if chart_path:
        print(f"\n📊 Chart generated: {chart_path}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Temporal period detection (March 2024 vs March 2025)")
    print("  ✓ Segment filtering (Greater China)")
    print("  ✓ Multi-period metric extraction")
    print("  ✓ Variance calculation (absolute & percentage)")
    print("  ✓ CFO strategic insights generation")
    print("  ✓ Comparison chart generation")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
