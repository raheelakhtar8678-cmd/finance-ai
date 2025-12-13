# src/ingestion/table_saver.py
from pathlib import Path
import pandas as pd

def save_tables(tables, output_dir="data/processed"):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for i, df in enumerate(tables):
        file_path = output / f"table_{i}.csv"
        df.to_csv(file_path, index=False)
        saved_files.append(str(file_path))  # Return string paths (more portable)
    return saved_files