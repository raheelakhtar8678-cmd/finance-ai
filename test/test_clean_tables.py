import pandas as pd
from src.processing.clean_tables import (
    strip_commas,
    parentheses_to_negative,
    normalize_headers
)


def test_strip_commas():
    df = pd.DataFrame({"revenue": ["1,000", "2,500"]})
    cleaned = strip_commas(df)
    assert cleaned["revenue"][0] == "1000"


def test_parentheses_to_negative():
    df = pd.DataFrame({"loss": ["(1,200)", "300"]})
    cleaned = parentheses_to_negative(df)
    assert cleaned["loss"][0] == -1200.0
    assert cleaned["loss"][1] == "300"


def test_normalize_headers():
    df = pd.DataFrame({"Revenue (Millions)": [10, 20]})
    cleaned = normalize_headers(df)
    assert "revenue_(millions)" in cleaned.columns