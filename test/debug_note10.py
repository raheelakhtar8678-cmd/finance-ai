"""
Debug script to examine Note 10 table structure from live PDF
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

from src.ingestion.table_extractor import extract_tables

PDF_PATH = r"e:\finance-ai\data\uploads\119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"

print("="*80)
print("DEBUG: Note 10 Table Structure")
print("="*80)

tables = extract_tables(PDF_PATH)

# Find tables on pages 13-15 (where Note 10 usually is)
for table in tables:
    page = table.get("page", 0)
    if 12 <= page <= 16:
        df = table.get("df")
        md = table.get("markdown", "")
        preceding = table.get("preceding_text", "")[:200]
        
        # Check if this might be segment table
        df_str = df.to_string().lower() if df is not None else ""
        
        if "china" in df_str or "segment" in preceding.lower() or "operating income" in df_str:
            print(f"\n{'='*60}")
            print(f"📊 TABLE on Page {page}")
            print(f"Preceding: {preceding}")
            print(f"Columns: {list(df.columns)}")
            print(f"Shape: {df.shape}")
            print(f"\nFirst 10 rows:")
            print(df.head(10).to_string())
            print(f"\n--- Looking for 'Greater China' row ---")
            
            # Check each row for "china"
            for idx, row in df.iterrows():
                row_str = " ".join([str(v) for v in row.values]).lower()
                if "china" in row_str:
                    print(f"Row {idx}: {row.values}")
