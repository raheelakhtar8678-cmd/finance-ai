import pandas as pd
from src.analysis.query_controller import route_query
from src.visualization.chart_generator import generate_chart

# Mock data for two different files
df1 = pd.DataFrame({
    "Category": ["Net Income"],
    "March 30, 2024": ["23,636"]
})

df2 = pd.DataFrame({
    "Category": ["Net Profit"],
    "Dec 31, 2023": ["33,916"]
})

tables = [
    {"df": df1, "source": "apple_q2.pdf", "page": 4},
    {"df": df2, "source": "apple_q1.xlsx", "page": 1}
]

print("--- Testing Cross-Document Comparison ---")
# Query that triggers comparison
question = "compare net income between apple_q2.pdf and apple_q1.xlsx"

answer, chart_path = route_query(
    question=question,
    tables=tables,
    chart_gen=generate_chart
)

print(f"\nFINAL ANSWER:\n{answer}")
print(f"\nCHART PRODUCED: {chart_path}")
