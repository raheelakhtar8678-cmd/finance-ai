import sys
import os
import pandas as pd

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.pymupdf_extractor import extract_tables_pymupdf

pdf_path = r"e:\finance-ai\data\uploads\db2bb6ec-b906-4923-b718-b767cab60dd8_2025_report.pdf"

print("DEBUGGING TABLE EXTRACTION...")
tables = extract_tables_pymupdf(pdf_path)

for i, t in enumerate(tables):
    print(f"\n--- TABLE {i} (Page {t['page']}) ---")
    md = t['markdown']
    
    if "greater china" in md.lower():
        print(f"MATCH: FOUND 'Greater China' in Table {i}")
        print(md)
    else:
        snip = md[:100].replace('\n', ' ')
        print(f"NO MATCH: 'Greater China' NOT in Table {i} (First 100: {snip})")

print("\n--- Summary ---")
found_count = sum(1 for t in tables if "greater china" in t['markdown'].lower())
print(f"Total tables: {len(tables)}")
print(f"Tables with 'Greater China': {found_count}")
