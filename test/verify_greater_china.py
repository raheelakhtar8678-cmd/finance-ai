import sys
import os
import pandas as pd

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.ingestion.pymupdf_extractor import extract_tables_pymupdf

pdf_path = r"e:\finance-ai\data\uploads\db2bb6ec-b906-4923-b718-b767cab60dd8_2025_report.pdf"

print("🧪 Starting Greater China Verification...")

# 1. Extract tables manually to pass to reasoner
tables = extract_tables_pymupdf(pdf_path)
print(f"📊 Extracted {len(tables)} tables.")

# 2. Test Net Sales for Greater China
print("\n--- TEST: GREATER CHINA NET SALES ---")
res_ns = compute_metric_with_reasoning("revenue", tables, "What is the net sales for Greater China?", segment_filter="Greater China")

print(f"DEBUG REASONING:\n{res_ns.get('reasoning')}\n")

if res_ns.get("success"):
    val_2025 = res_ns.get("result")
    val_2024 = res_ns.get("prior")
    print(f"✅ 2025 Net Sales: ${val_2025/1e6:,.0f}M (Expected: 16,002)")
    print(f"✅ 2024 Net Sales: ${val_2024/1e6:,.0f}M (Expected: 16,372)")
    
    if abs(val_2025 - 16002000000) < 1e6 and abs(val_2024 - 16372000000) < 1e6:
        print("🎉 Net Sales extraction PERFECT!")
    else:
        print("❌ Net Sales extraction MISMATCH!")
else:
    print(f"❌ Net Sales extraction FAILED: {res_ns.get('reasoning')}")

# 3. Test Operating Income for Greater China
print("\n--- TEST: GREATER CHINA OPERATING INCOME ---")
res_oi = compute_metric_with_reasoning("operating_income", tables, "What is the operating income for Greater China?", segment_filter="Greater China")

if res_oi.get("success"):
    val_2025 = res_oi.get("result")
    val_2024 = res_oi.get("prior")
    print(f"✅ 2025 Operating Income: ${val_2025/1e6:,.0f}M (Expected: 6,626)")
    print(f"✅ 2024 Operating Income: ${val_2024/1e6:,.0f}M (Expected: 6,700)")
    
    if abs(val_2025 - 6626000000) < 1e6 and abs(val_2024 - 6700000000) < 1e6:
        print("🎉 Operating Income extraction PERFECT!")
    else:
        print("❌ Operating Income extraction MISMATCH!")
else:
    print(f"❌ Operating Income extraction FAILED: {res_oi.get('reasoning')}")

print("\n🚀 Verification logic complete.")
