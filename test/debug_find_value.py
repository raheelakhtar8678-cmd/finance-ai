
import sys
import pandas as pd
from src.ingestion.table_ingester import ingest_any_file
from src.processing.clean_tables import clean_all_tables

pdf_path = "data/uploads/fc8b6662-f6bc-4b6d-a25e-b4cf96218de6_4b7fbf86-37be-4e59-bed7-fda7ec8404ef.pdf"

print("Loading tables...")
tables = ingest_any_file(pdf_path)
cleaned_tables = clean_all_tables(tables)

print(f"\nSearching for '90753' or '90 753' in {len(cleaned_tables)} tables...")
targets = ["90753", "90 753", "90,753"]

for i, t in enumerate(cleaned_tables):
    df = t['df']
    # Search string representation of whole dataframe
    df_str = df.to_string().lower()
    
    found = False
    for tgt in targets:
        if tgt in df_str:
            found = True
            print(f"\n✅ FOUND '{tgt}' in TABLE {i} (Page {t.get('page')})")
            print(f"Columns: {df.columns.tolist()}")
            
            # Print specifically the row(s) containing the match
            for idx, row in df.iterrows():
                row_str = " ".join([str(x) for x in row.values]).lower()
                if tgt.replace(" ", "") in row_str.replace(" ", ""):
                     print(f"   ROW {idx}: {row.values}")
            
            # Print head to see context
            print("   Context Head:")
            print(df.head(5).to_string())
