"""
Verification test for Comparison Engine and Chart Generator
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

import pandas as pd
from pathlib import Path

# Import components to test
from src.analysis.comparison_engine import (
    is_comparison_query, 
    extract_metric_from_query,
    compare_across_documents
)
from src.visualization.chart_generator import generate_chart

print("="*80)
print("VERIFICATION: Comparison Engine & Chart Generator")
print("="*80)

# ============================================
# TEST 1: Comparison Query Detection
# ============================================
print("\n## TEST 1: Comparison Query Detection")

test_queries = [
    ("Compare revenue across all files", True),
    ("What is the revenue?", False),
    ("Check profit across both documents", True),
    ("Compare revenue vs profit", False),  # Different metrics = triangulation
    ("Show net income difference between files", True),
]

all_passed = True
for query, expected in test_queries:
    result = is_comparison_query(query)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"  {status} '{query[:40]}...' -> {result} (expected {expected})")

print(f"\nTest 1 Result: {'PASSED' if all_passed else 'FAILED'}")

# ============================================
# TEST 2: Metric Extraction from Query
# ============================================
print("\n## TEST 2: Metric Extraction from Query")

metric_tests = [
    ("Compare revenue across files", "revenue"),
    ("Check net income difference", "net_income"),
    ("Operating income comparison", "operating_income"),
    ("Show EPS across documents", "eps"),
]

all_passed = True
for query, expected in metric_tests:
    result = extract_metric_from_query(query)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"  {status} '{query}' -> {result} (expected {expected})")

print(f"\nTest 2 Result: {'PASSED' if all_passed else 'FAILED'}")

# ============================================
# TEST 3: Chart Generator
# ============================================
print("\n## TEST 3: Chart Generator")

# Create test data
test_df = pd.DataFrame({
    "Period": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
    "Revenue": [20000, 22000, 21500, 25000]
})

# Ensure output directory exists
Path("data/static").mkdir(parents=True, exist_ok=True)

# Test bar chart
result = generate_chart(
    df=test_df,
    x_col="Period",
    y_col="Revenue",
    title="Quarterly Revenue Test",
    output_path="data/static/test_chart.png",
    chart_type="bar"
)

if result.get("success"):
    print(f"  ✅ Chart generated: {result.get('image_path')}")
    print(f"  ✅ Chart type: {result.get('chart_type')}")
else:
    print(f"  ❌ Chart generation failed: {result.get('error')}")

# Test auto-detection
result_auto = generate_chart(
    df=test_df,
    x_col="Period",
    y_col="Revenue",
    title="Auto-detected Chart Type",
    output_path="data/static/test_chart_auto.png"
)

if result_auto.get("success"):
    print(f"  ✅ Auto-detection worked: {result_auto.get('chart_type')}")
else:
    print(f"  ❌ Auto-detection failed")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
