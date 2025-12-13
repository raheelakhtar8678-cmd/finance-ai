# src/analysis/trend_detector.py

import pandas as pd
import numpy as np


def detect_trend(series: pd.Series) -> str:
    """
    Detect overall trend of a numeric series.
    Returns: "up", "down", or "flat".
    """
    clean_series = series.dropna().astype(float)

    if len(clean_series) < 2:
        return "flat"

    if clean_series.iloc[-1] > clean_series.iloc[0]:
        return "up"
    elif clean_series.iloc[-1] < clean_series.iloc[0]:
        return "down"
    return "flat"


def percentage_change(series: pd.Series) -> float:
    """
    Calculate overall percentage change from first to last value.
    Example: [100, 150] → +50%
    """
    clean_series = series.dropna().astype(float)
    if len(clean_series) < 2:
        return 0.0

    start = clean_series.iloc[0]
    end = clean_series.iloc[-1]

    if start == 0:
        return 0.0

    return ((end - start) / start) * 100


def moving_average(series: pd.Series, window: int = 3) -> pd.Series:
    """
    Compute moving average for smoothing.
    """
    return series.astype(float).rolling(window=window).mean()


def detect_anomalies(series: pd.Series, z_threshold: float = 2.0) -> list:
    """
    Detect anomalies using Z-score threshold.
    Returns list of row indices that are anomalies.
    """
    clean_series = series.astype(float).fillna(0)

    mean = clean_series.mean()
    std = clean_series.std()

    if std == 0:
        return []

    z_scores = (clean_series - mean) / std
    return list(clean_series.index[np.abs(z_scores) > z_threshold])


def analyze_numeric_column(series: pd.Series) -> dict:
    """
    Master function — returns all trend insights for a numeric column.
    """

    return {
        "trend": detect_trend(series),
        "pct_change": round(percentage_change(series), 2),
        "moving_average": moving_average(series).tolist(),
        "anomalies": detect_anomalies(series)
    }


def analyze_table(df: pd.DataFrame) -> dict:
    """
    Analyze all numeric columns in a table.
    Returns:
      {
         "revenue": {...},
         "profit": {...},
         ...
      }
    """

    numeric_cols = []

    for col in df.columns:
        try:
            df[col].astype(float)
            numeric_cols.append(col)
        except:
            pass

    insights = {}

    for col in numeric_cols:
        insights[col] = analyze_numeric_column(df[col])

    return insights