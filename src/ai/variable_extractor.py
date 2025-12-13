# src/ai/variable_extractor.py
import re
import pandas as pd
from typing import Dict, List

def extract_variables_from_retrieved(retrieved_docs: List[Dict]) -> Dict[str, float]:
    """
    Extract numeric variables from RAG-retrieved context text.
    Example: "revenue_latest: 1234000" → {"revenue_latest": 1234000.0}
    """
    variables = {}
    for doc in retrieved_docs:
        text = doc.get("text", "")
        # Match patterns like "key: value" or "key = value"
        matches = re.findall(r"(\w+)[\s:=]+([+-]?\d[\d,.]*)", text)
        for key, val_str in matches:
            try:
                # Clean and convert to float
                clean_val = val_str.replace(",", "").replace("$", "")
                variables[key] = float(clean_val)
            except (ValueError, TypeError):
                continue
    return variables

def extract_variables_from_dataframe(df: pd.DataFrame) -> Dict[str, float]:
    """
    Extract variables directly from cleaned DataFrame columns.
    Example: last value of "revenue" → {"revenue_latest": 1234000.0}
    """
    variables = {}
    for col in df.columns:
        try:
            # Get last non-null numeric value
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            last_val = numeric_series.dropna().iloc[-1]
            variables[f"{col}_latest"] = float(last_val)
        except (IndexError, ValueError, TypeError):
            continue
    return variables