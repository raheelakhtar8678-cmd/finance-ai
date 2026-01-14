import sys
import os
import json
import datetime

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set persistent local paths (matches app.py)
os.environ["HF_HOME"] = os.path.abspath("data/cache/hf")
os.environ["CHROMA_DB_PATH"] = os.path.abspath("data/db/chroma")

from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.ingestion.pymupdf_extractor import extract_tables_pymupdf
from src.analysis.query_controller import route_query

pdf_path = r"e:/finance-ai/data/uploads/db2bb6ec-b906-4923-b718-b767cab60dd8_2025_report.pdf"

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

log("🏆 STARTING ELITE FINANCIAL AI BENCHMARKS 🏆")

# 1. Load Tables
tables = extract_tables_pymupdf(pdf_path)
log(f"📊 Extracted {len(tables)} tables.\n")

def print_benchmark_result(name, question, result):
    print(f"--- BENCHMARK: {name} ---")
    print(f"QUESTION: {question}")
    
    # Handle if result is a tuple (answer, chart)
    if isinstance(result, tuple):
        answer = result[0]
    else:
        answer = result.get('result_text', result.get('result', 'N/A'))
        
    print(f"RESULT: {answer}")
    
    # For reasoning, we need to inspect the result dict
    reasoning = ""
    if isinstance(result, dict):
        reasoning = result.get('reasoning', '')
    
    print(f"REASONING SNIPPET: {reasoning[:300]}...")
    print("-" * 50 + "\n")

# --- BENCHMARK 1: METRIC INTEGRITY ---
log("🚀 Running Benchmark 1: Metric Integrity...")
res1a = compute_metric_with_reasoning("revenue", tables, "What is the total consolidated net sales for 2025?")
res1b = compute_metric_with_reasoning("operating_income", tables, "What is the total segment operating income for 2025?")

val1a = res1a.get('result', 0)
val1b = res1b.get('result', 0)

log(f"Consolidated Net Sales: ${val1a/1e6:,.0f}M (Expected: 90,753)")
log(f"Total Segment Operating Income: ${val1b/1e6:,.0f}M (Expected: 40,136)")

if val1a == 90753000000 and val1b == 40136000000:
    log("✅ Benchmark 1: PERFECT DISTINCTION\n")
else:
    log("⚠️ Benchmark 1: DISCREPANCY DETECTED (Logic might be using RAG fallback)\n")

# --- BENCHMARK 2: FOOTNOTE EXTRACTION ---
log("🚀 Running Benchmark 2: Footnote Extraction...")
q2 = "How much revenue was recognized in Q2 2024 that was previously in deferred revenue?"
res2 = route_query(q2, tables)
print_benchmark_result("Footnote Extraction", q2, res2)

# --- BENCHMARK 3: CONTEXTUAL REASONING ---
log("🚀 Running Benchmark 3: Contextual Reasoning...")
q3 = "Explain why total segment operating income is higher than consolidated operating income in Q2 2025."
res3 = route_query(q3, tables)
print_benchmark_result("Contextual Reasoning", q3, res3)

log("🏁 BENCHMARKING COMPLETE")
