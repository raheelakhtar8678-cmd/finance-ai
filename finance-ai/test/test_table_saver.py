import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.table_saver import save_tables_to_csv

def test_save_tables_to_csv(tmp_path):
    df = pd.DataFrame({"A":[1,2], "B":[3,4]})
    tables = [df]

    saved_files = save_tables_to_csv(tables, output_dir=tmp_path)

    assert len(saved_files) == 1
    assert Path(saved_files[0]).exists()