"""Debug script to inspect Balance Sheet table structure"""
import sys
sys.path.insert(0, '.')
import pandas as pd

from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables

# Use latest uploaded Apple 10-Q
pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"

print("="*60)
print("LOADING TABLES FROM PDF...")
print("="*60)

tables = ingest_any_file(pdf_path)
cleaned_tables = clean_all_tables(tables)

print(f"\n✅ Found {len(cleaned_tables)} tables")

# Look for Balance Sheet
found = False
for i, table in enumerate(cleaned_tables):
    df = table["df"]
    page = table.get("page", "?")
    
    # Flatten text to search
    table_text = " ".join([str(c) for c in df.columns] + [str(x) for x in df.values.flatten()]).lower()
    
    # 🔍 ALWAYS PRINT FIRST 5 TABLES to inspect extraction quality
    if i < 5:
        print(f"\n{'='*60}")
        print(f"📋 RAW TABLE {i} (Page {page})")
        print(f"{'='*60}")
        print(f"COLUMNS: {list(df.columns)}")
        print(f"TEXT SAMPLE: {table_text[:200]}...")
        print("FIRST 5 ROWS:")
        print(df.head(5).to_string())

    if "inventori" in table_text or "balance sheet" in table_text:
        found = True
        print(f"\n{'='*60}")
        print(f"🎯 POTENTIAL MATCH: TABLE {i} (Page {page})")
        print(f"{'='*60}")
        print(f"COLUMNS: {list(df.columns)}")
        print(f"\nFULL TABLE DATA:")
        print(df.to_string())
