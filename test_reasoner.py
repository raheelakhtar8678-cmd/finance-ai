import pandas as pd
from src.analysis.financial_reasoning import MetricReasoner

# Mock data
df = pd.DataFrame({
    "Category": ["Net Income", "Revenue"],
    "March 30, 2024": ["23,636", "90,753"],
    "April 1, 2023": ["23,010", "94,836"]
})

tables = [{"df": df, "source": "test.pdf", "page": 4}]
reasoner = MetricReasoner(tables)

print("--- Testing Profit/Loss ---")
res = reasoner.compute_profit_loss()
print(f"Result: {res.get('result')}")
print(f"Prior: {res.get('prior_result')}")
print(f"Period: {res.get('period_date')}")
print(f"Prior Date: {res.get('prior_date')}")
print(f"Reasoning: {res.get('reasoning')}")

print("\n--- Testing Revenue ---")
rev = reasoner.compute_revenue_value()
print(f"Rev: {rev.get('result')}")
print(f"Prior Rev: {rev.get('prior_result')}")
print(f"Reasoning: {rev.get('reasoning')}")
