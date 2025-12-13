import pytest
import pandas as pd
from pathlib import Path
from src.ingestion.table_extractor import extract_tables


# Use a single consistent test PDF path
TEST_PDF = Path("data/raw/test.pdf")


def test_extract_tables_function_exists():
    """Ensure the function is importable."""
    assert callable(extract_tables)


def test_extract_tables_returns_list():
    """Test that the function returns a list when given a valid PDF."""
    
    # Skip if PDF does not exist (helpful for CI)
    if not TEST_PDF.exists():
        pytest.skip(f"Test PDF not found at {TEST_PDF}")
    
    result = extract_tables(str(TEST_PDF))
    assert isinstance(result, list)


def test_extracted_items_are_dataframes():
    """Ensure extracted tables are pandas DataFrames."""
    
    if not TEST_PDF.exists():
        pytest.skip(f"Test PDF not found at {TEST_PDF}")
    
    tables = extract_tables(str(TEST_PDF))
    
    # Ensure we extracted at least 1 table
    assert len(tables) > 0
    
    # Ensure each extracted result is a non-empty DataFrame
    for table in tables:
        assert isinstance(table, pd.DataFrame)
        assert not table.empty