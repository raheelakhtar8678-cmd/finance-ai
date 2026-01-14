"""
End-to-end test for segment extraction with proper RAG indexing.
This script simulates the full upload + query flow.
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

from pathlib import Path
import shutil
import uuid

# 1. Simulate file upload and ingestion
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
from src.ai.rag_engine import index_dataframe_to_chroma
from src.analysis.query_controller import route_query
from src.visualization.chart_generator import generate_chart

PDF_PATH = r"e:\finance-ai\data\uploads\119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"

def test_full_flow():
    print("="*80)
    print("END-TO-END TEST: Segment Extraction with RAG Indexing")
    print("="*80)
    
    # Step 1: Ingest PDF
    print(f"\n📄 Step 1: Ingesting {PDF_PATH}...")
    tables = ingest_any_file(PDF_PATH)
    cleaned_tables = clean_all_tables(tables)
    print(f"   Extracted {len(cleaned_tables)} tables")
    
    # Step 2: Index into RAG
    print(f"\n📊 Step 2: Indexing tables into RAG vector store...")
    for table_idx, table in enumerate(cleaned_tables):
        df = table.get("df")
        if df is not None and not df.empty:
            index_dataframe_to_chroma(
                df=df,
                source_name="apple_q2_2025.pdf",
                table_id=table_idx,
                preceding_text=table.get("preceding_text", ""),
                following_text=table.get("following_text", "")
            )
    print(f"   ✅ Indexed {len(cleaned_tables)} tables")
    
    # Add source metadata (use actual filename so PyMuPDF fallback finds it)
    import os
    actual_filename = os.path.basename(PDF_PATH)
    for item in cleaned_tables:
        item["source"] = actual_filename
    
    # Step 3: Test queries
    print("\n"+"="*80)
    print("Step 3: Testing Segment Queries")
    print("="*80)
    
    test_queries = [
        "What is the operating income for Greater China in Q2 2025?",
        "What are the net sales for Greater China?",
        "Compare Greater China operating income 2024 vs 2025"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-"*60)
        
        answer, chart_path = route_query(
            question=query,
            tables=cleaned_tables,
            chart_gen=generate_chart,
            session_id="test-session"
        )
        
        # Check for success indicators
        has_value = any(val in answer.lower() for val in ["6,626", "6626", "6.6 billion", "$6.6"])
        has_failure = "not available" in answer.lower() or "could not find" in answer.lower()
        
        if has_value:
            print(f"   ✅ SUCCESS: Found correct value")
        elif has_failure:
            print(f"   ❌ FAILURE: Data not available")
        else:
            print(f"   ⚠️ UNCLEAR: Check answer below")
        
        print(f"   Answer Preview: {answer[:300]}...")

if __name__ == "__main__":
    test_full_flow()
