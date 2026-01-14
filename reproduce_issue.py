import sys
from pathlib import Path
sys.path.append(r"e:\finance-ai")

from src.ingestion.table_extractor import extract_tables, get_value_with_provenance
from src.analysis.metric_registry import METRIC_REGISTRY
import pandas as pd

PDF_PATH = r"e:\finance-ai\data\uploads\119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"

def inspect_extraction():
    print(f"Extracting tables from {PDF_PATH}...")
    tables = extract_tables(PDF_PATH, track_provenance=True)
    
    print(f"Extracted {len(tables)} tables.")
    
    # Locate Segment Info Table (Note 10)
    segment_table_idx = -1
    for i, table in enumerate(tables):
        markdown = table.get("markdown", "")
        # Page-based search
        if table['page'] in [13, 14, 15]:
            print(f"\\nPotential Table found at index {i} (Page {table['page']}):")
            print(table['markdown'])
            
            # Print dataframe for clearer inspection
            print("DataFrame Content:")
            print(table['df'].to_string())

            
    if segment_table_idx == -1:
        print("Could not find Segment Information table.")

if __name__ == "__main__":
    inspect_extraction()
