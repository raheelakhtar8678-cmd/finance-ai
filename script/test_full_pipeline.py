import os
import sys
sys.path.append(os.getcwd())

from pathlib import Path
import pandas as pd

# -------------------------
# Multi-file ingestion
# -------------------------
from script.ingest_all_raw import ingest_all_raw_files

# Cleaning
from src.processing.clean_tables import clean_table

# Analysis
from src.analysis.financial_metrics import compute_financial_metrics
from src.analysis.trend_detector import analyze_table

# RAG
from src.ai.rag_engine import index_dataframe_to_chroma, retrieve_context

# Visualization
from src.visualization.chart_generator import ChartGenerator
# FIX 2: Renamed import to match the new function name in kpi_generator.py
from src.visualization.kpi_generator import generate_df_summary_kpis

# Calculator
from src.analysis.calculator import safe_eval_expr


def main():
    print("\n🚀 STARTING FULL MULTI-FILE FINANCIAL AI PIPELINE\n")

    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed_pipeline_test")
    chart_dir = Path("data/charts_pipeline_test")

    processed_dir.mkdir(parents=True, exist_ok=True)
    chart_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # 1️⃣ INGEST ALL RAW FILES
    # -------------------------------------------------
    print("1️⃣ INGESTING ALL RAW FILES...")
    file_tables = ingest_all_raw_files(raw_dir)

    if not file_tables:
        print("❌ No valid raw files found. Abort.")
        return

    # -------------------------------------------------
    # 2️⃣ CLEAN ALL TABLES
    # -------------------------------------------------
    print("\n2️⃣ CLEANING TABLES...")
    cleaned_tables = []

    for filename, tables in file_tables.items():
        for i, df in enumerate(tables):
            cdf = clean_table(df.copy())
            if not cdf.empty:
                cleaned_tables.append({
                    "source": filename,
                    "table_id": i,
                    "df": cdf
                })
                out_csv = processed_dir / f"{filename}_table_{i}.csv"
                cdf.to_csv(out_csv, index=False)

    print(f"✔ Cleaned & saved {len(cleaned_tables)} tables")

    # -------------------------------------------------
    # 3️⃣ INDEX INTO RAG (WITH TRACEABILITY)
    # -------------------------------------------------
    print("\n3️⃣ INDEXING INTO RAG...")
    for t in cleaned_tables:
        index_dataframe_to_chroma(
            t["df"],
            # FIX 1: Change keyword argument 'source' to 'source_name'
            source_name=t["source"], 
            table_id=t["table_id"]
        )

    print("✔ All tables indexed")

    # -------------------------------------------------
    # 4️⃣ USER QUERY → RAG
    # -------------------------------------------------
    print("\n4️⃣ USER QUERY → RAG")
    query = "revenue growth year over year"
    contexts = retrieve_context(query, k=5)

    print(f"✔ Retrieved {len(contexts)} relevant chunks")

    # -------------------------------------------------
    # 5️⃣ METRICS + TRENDS (ONLY FOR RAG TABLES)
    # -------------------------------------------------
    print("\n5️⃣ FINANCIAL METRICS & TRENDS")
    metrics_store = {}
    trend_store = {}

    for t in cleaned_tables:
        key = f"{t['source']}::table_{t['table_id']}"
        df = t["df"]

        metrics_store[key] = compute_financial_metrics(df)
        trend_store[key] = analyze_table(df)

    print(f"✔ Metrics computed for {len(metrics_store)} tables")

    # -------------------------------------------------
    # 6️⃣ KPI GENERATION (FROM DATAFRAMES ✔)
    # -------------------------------------------------
    print("\n6️⃣ KPI GENERATION")
    kpi_store = {}

    for t in cleaned_tables:
        key = f"{t['source']}::table_{t['table_id']}"
        # FIX 2: Change function call to use the new name
        kpi_store[key] = generate_df_summary_kpis(t["df"])

    print("✔ KPIs generated")

    # -------------------------------------------------
    # 7️⃣ CHART GENERATION (NUMERIC-ONLY)
    # -------------------------------------------------
    print("\n7️⃣ CHART GENERATION")
    chart_gen = ChartGenerator(output_dir=str(chart_dir))
    charts = []

    for t in cleaned_tables:
        df = t["df"]
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            chart = chart_gen.line_chart(df, numeric_cols[0])
            charts.append(chart)

    print(f"✔ Generated {len(charts)} charts")

    # -------------------------------------------------
    # 8️⃣ DETERMINISTIC CALCULATOR (NO LLM)
    # -------------------------------------------------
    print("\n8️⃣ CALCULATOR CHECK")
    expr = "cash / monthly_expenses"
    variables = {"cash": 500000, "monthly_expenses": 120000}
    result = safe_eval_expr(expr, variables)
    print(f"✔ Burn rate = {result:.2f} months")

    # -------------------------------------------------
    print("\n✅ MULTI-FILE PIPELINE COMPLETE")
    print("Validated:")
    print(" • Multi-file ingestion")
    print(" • Cleaning & persistence")
    print(" • RAG indexing & retrieval")
    print(" • Metrics & trend analysis")
    print(" • KPI extraction (from data)")
    print(" • Chart generation")
    print(" • Deterministic finance calculator")

    print("\nNEXT → Part C-2: Query → Metric → Chart Routing")


if __name__ == "__main__":
    main()