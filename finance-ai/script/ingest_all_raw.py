# script/ingest_all_raw.py
"""
Ingest all supported files (PDF, XLSX, XLS, CSV) from data/raw/
and extract/save all tables to data/processed/.
"""

import os
from pathlib import Path
from src.ingestion.table_ingester import ingest_any_file
from src.ingestion.table_saver import save_tables

RAW_DIR = "data/raw"
PROCESSED_BASE = "data/processed"

def main():
    raw_path = Path(RAW_DIR)
    if not raw_path.exists():
        print(f"❌ Raw directory not found: {RAW_DIR}")
        return

    # Supported file extensions
    supported_ext = {".pdf", ".xlsx", ".xls", ".csv"}
    files = [
        f for f in raw_path.iterdir()
        if f.is_file() and f.suffix.lower() in supported_ext
    ]

    if not files:
        print(f"⚠️ No supported files found in {RAW_DIR}")
        print(f"   Supported: PDF, XLSX, XLS, CSV")
        return

    print(f"📁 Found {len(files)} file(s) to process:")
    for f in files:
        print(f"  - {f.name}")

    for file_path in files:
        print(f"\n📥 Processing: {file_path.name}")
        try:
            tables = ingest_any_file(str(file_path))
            if not tables:
                print(f"  → No tables found.")
                continue

            # Create safe output folder name (no spaces/special chars)
            safe_name = file_path.stem.replace(" ", "_").replace(".", "_")
            output_dir = f"{PROCESSED_BASE}/{safe_name}"
            saved = save_tables(tables, output_dir=output_dir)
            print(f"  → Saved {len(saved)} tables to: {output_dir}")

        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")

    print("\n✅ Ingestion complete.")

if __name__ == "__main__":
    main()