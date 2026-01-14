"""
Robust financial value extraction with UNIT AWARENESS
Handles tables expressed in Millions / Billions correctly
"""

import re
import pandas as pd
from typing import Optional, List


UNIT_MULTIPLIERS = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}


def _detect_unit_multiplier(text: str) -> int:
    """Detects multiplier (Millions, Billions) from text headers/disclaimers."""
    text = text.lower()
    
    # Check for Billions first (higher priority)
    if any(m in text for m in ["billions", "in billions", "expressed in billions"]):
        return 1_000_000_000
    # Check for Millions
    if any(m in text for m in ["millions", "in millions", "expressed in millions"]):
        return 1_000_000
    # Thousands
    if any(m in text for m in ["thousands", "in thousands"]):
        return 1_000
        
    for unit, mult in UNIT_MULTIPLIERS.items():
        if unit in text:
            return mult
    return 1


def extract_financial_value(value: any, unit_hint: str | None = None) -> Optional[float]:
    """Extracts numeric value from string, handling currency, commas, and parentheses for negatives."""
    if pd.isna(value) or value is None:
        return None

    if isinstance(value, (int, float)):
        base = float(value)
    else:
        text = str(value).strip().replace(",", "")
        
        # Handle parentheses for negative numbers (common in financial reports)
        is_negative = False
        if (text.startswith("(") and text.endswith(")")) or (text.startswith("-")):
            is_negative = True
            text = text.replace("(", "").replace(")", "").replace("-", "")

        # Find numbers
        matches = re.findall(r"[\d.]+", text)
        if not matches:
            return None
        
        try:
            base = float(matches[0])
            if is_negative:
                base = -base
        except ValueError:
            return None

    multiplier = 1
    if unit_hint:
        multiplier = _detect_unit_multiplier(unit_hint)

    return base * multiplier


def extract_multiple_values(text: str) -> List[float]:
    if pd.isna(text):
        return []

    values = []
    pattern = r"[\d,]+\.?\d*"
    for m in re.findall(pattern, str(text)):
        try:
            values.append(float(m.replace(",", "")))
        except:
            pass
    return values


def smart_column_extraction(df: pd.DataFrame, col: str) -> Optional[float]:
    if col not in df.columns:
        return None

    series = df[col].dropna()
    if series.empty:
        return None

    # 🔑 Detect UNIT from column name
    unit_multiplier = _detect_unit_multiplier(col)

    # 🔑 Detect UNIT from dataframe metadata (if exists)
    table_text = " ".join(df.columns.astype(str))
    unit_multiplier = max(unit_multiplier, _detect_unit_multiplier(table_text))

    # Latest value
    raw = series.iloc[-1]
    val = extract_financial_value(raw, unit_hint=col)
    if val:
        return val

    # Fallback: largest scaled value
    vals = []
    for v in series:
        ev = extract_financial_value(v, unit_hint=col)
        if ev:
            vals.append(ev)

    return max(vals) if vals else None


def validate_financial_value(value: Optional[float], metric_name: str) -> tuple[bool, str]:
    if value is None:
        return False, "No value extracted"

    metric = metric_name.lower()

    # 🚫 Reject years
    if 1900 <= value <= 2100:
        return False, "Value looks like a year"

    # Revenue sanity
    if "revenue" in metric or "sales" in metric:
        if value < 10_000_000:
            return False, "Revenue too small to be realistic"
        if value > 20_000_000_000_000:
            return False, "Revenue exceeds realistic upper bound"

    return True, "Valid"
