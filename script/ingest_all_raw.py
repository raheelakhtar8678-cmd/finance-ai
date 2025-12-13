from pathlib import Path
from typing import Dict, List
import pandas as pd

from src.ingestion.table_ingester import ingest_any_file


SUPPORTED_EXTS = {".pdf", ".xlsx", ".xls", ".csv"}


def ingest_all_raw_files(raw_dir: str | Path) -> Dict[str, List[pd.DataFrame]]:
    """
    Ingest all supported raw files in a directory.
    
    Returns:
      {
        "test.pdf": [df1, df2],
        "income.xlsx": [df1],
      }
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    results: Dict[str, List[pd.DataFrame]] = {}

    for file in raw_dir.iterdir():
        if file.suffix.lower() not in SUPPORTED_EXTS:
            continue

        try:
            tables = ingest_any_file(str(file))
            if tables:
                results[file.name] = tables
                print(f"✔ Ingested {len(tables)} tables from {file.name}")
            else:
                print(f"⚠ No tables found in {file.name}")
        except Exception as e:
            print(f"❌ Failed ingesting {file.name}: {e}")

    return results