from pathlib import Path
import pandas as pd
from src.processing.clean_tables import (
    clean_all_tables, 
    strip_commas, 
    parentheses_to_negative, 
    normalize_headers,
    auto_detect_header
)


def test_clean_pipeline_end_to_end():
    """Test full cleaning pipeline"""
    # Simulate a CSV input
    df = pd.DataFrame({
        " Revenue (USD) ": ["1,234", "(567)", "890"],
        " Cost ": ["(100)", "200", "300"]
    })

    cleaned = clean_all_tables([df])[0]

    # --- Assertions ---
    # headers cleaned
    assert list(cleaned.columns) == ["revenue_usd", "cost"]

    # values cleaned
    assert cleaned.iloc[0, 0] == 1234.0
    assert cleaned.iloc[1, 0] == -567.0


def test_auto_detect_header():
    """Test header detection from numbered columns"""
    # Create DataFrame with numbered columns (like from PDFs)
    df = pd.DataFrame({
        0: ["Name", "Alice", "Bob"],
        1: ["Age", "30", "25"],
        2: ["City", "NYC", "LA"]
    })
    
    cleaned = auto_detect_header(df)
    
    # First row should become headers
    assert list(cleaned.columns) == ["Name", "Age", "City"]
    # Data should start from second row
    assert cleaned.iloc[0, 0] == "Alice"
    assert len(cleaned) == 2  # Only 2 data rows


def test_strip_commas():
    """Test comma removal"""
    df = pd.DataFrame({"amount": ["1,000", "2,500,000"]})
    cleaned = strip_commas(df)
    assert cleaned["amount"][0] == "1000"
    assert cleaned["amount"][1] == "2500000"


def test_parentheses_to_negative():
    """Test negative number conversion (after comma stripping)"""
    df = pd.DataFrame({"loss": ["(1,200)", "300", "(50)"]})
    
    # Apply in correct order: strip commas FIRST, then convert parentheses
    cleaned = strip_commas(df)
    cleaned = parentheses_to_negative(cleaned)
    
    assert cleaned["loss"][0] == "-1200"
    assert cleaned["loss"][1] == "300"
    assert cleaned["loss"][2] == "-50"


def test_normalize_headers():
    """Test header normalization"""
    df = pd.DataFrame({
        "Revenue (USD)": [100],
        " Cost Per Unit ": [50],
        "Gross-Margin%": [25]
    })
    cleaned = normalize_headers(df)
    assert list(cleaned.columns) == ["revenue_usd", "cost_per_unit", "gross_margin"]