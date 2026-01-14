
import sys
import traceback
sys.path.insert(0, '.')
import pandas as pd
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables
from src.analysis.financial_reasoning import MetricReasoner

pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"

print("Loading tables...")
tables = ingest_any_file(pdf_path)
cleaned_tables = clean_all_tables(tables)
print(f"Loaded {len(cleaned_tables)} tables.")

print("\n" + "="*50)
print("DUMPING TABLES 1-6 (Looking for Operations)")
print("="*50)

for i in range(1, 7):
    if i >= len(cleaned_tables): break
    t = cleaned_tables[i]
    df = t['df']
    print(f"\n📋 TABLE {i} (Page {t.get('page')})")
    print(f"Columns: {df.columns.tolist()}")
    print("First 10 Rows:")
    print(df.head(10).to_string())
    
    # Check for keywords row by row (using combined logic simulation)
    print("   Scanning for 'Net Sales'...")
    text_cols = df.select_dtypes(include="object").columns
    if not text_cols.empty:
        col0 = text_cols[0]
        cols = df.columns.tolist()
        col1 = cols[cols.index(col0) + 1] if (cols.index(col0) + 1 < len(cols)) else None
        
        for idx, row in df.iterrows():
            val0 = str(row[col0]).lower().strip()
            val1 = str(row[col1]).lower().strip() if col1 else ""
            combined = (val0 + " " + val1).strip()
            
            if "net" in combined and "sales" in combined:
                 print(f"   🎯 MATCH ROW {idx}: Combined='{combined}' | Val0='{val0}' Val1='{val1}'")

# Re-run computation with verbose output
reasoner = MetricReasoner(cleaned_tables, question="What are the results for the three months ended?")
print("\n" + "="*50)
print("RE-COMPUTING REVENUE (Verbose Check)")
print("="*50)
try:
    res = reasoner.compute_with_formula("revenue")
    print(f"RESULT: {res}")
except:
    traceback.print_exc()

# Check Operating Income keyword
print("\n" + "="*50)
print("RE-COMPUTING OPERATING INCOME")
print("="*50)
try:
    res = reasoner.compute_with_formula("operating_income")
    print(f"RESULT: {res}")
except:
    traceback.print_exc()
