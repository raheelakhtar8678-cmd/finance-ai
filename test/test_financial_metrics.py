# src/analysis/financial_metrics.py

import pandas as pd
import numpy as np
import re


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names for financial detection.
    Example: 'Total Revenue (USD)' → 'revenue'
             'Gross Profit %' → 'gross_profit'
    """
    def clean(name):
        name = name.strip().lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        return name

    df = df.copy()
    df.columns = [clean(c) for c in df.columns]
    return df


def _find_column(df: pd.DataFrame, patterns: list[str]) -> str | None:
    """
    Utility to find a column by multiple possible pattern names.
    Example: revenue, total_revenue, sales, turnover
    """
    for col in df.columns:
        for p in patterns:
            if re.search(p, col):
                return col
    return None


def compute_financial_metrics(df: pd.DataFrame) -> dict:
    """
    Compute key financial ratios from a cleaned financial table.

    Returns:
        dict with computed metrics (missing ones are ignored).
    """
    if df.empty:
        return {}

    df = _normalize_column_names(df)

    metrics = {}

    # ---------------------------
    # 1. Revenue & YoY Growth
    # ---------------------------
    revenue_col = _find_column(df, [
        r"revenue", r"sales", r"turnover", r"top_line"
    ])

    if revenue_col:
        revenue = pd.to_numeric(df[revenue_col], errors="coerce")

        metrics["revenue_latest"] = revenue.iloc[-1]
        if len(revenue) > 1 and revenue.iloc[-2] != 0:
            metrics["revenue_yoy_growth"] = (
                (revenue.iloc[-1] - revenue.iloc[-2]) / abs(revenue.iloc[-2])
            )
        else:
            metrics["revenue_yoy_growth"] = None

    # ---------------------------
    # 2. Gross Margin
    # ---------------------------
    gross_profit_col = _find_column(df, [r"gross_profit"])
    cogs_col = _find_column(df, [r"cogs", r"cost_of_goods", r"cost_of_sales"])

    if gross_profit_col and revenue_col:
        gp = pd.to_numeric(df[gross_profit_col], errors="coerce")
        rev = pd.to_numeric(df[revenue_col], errors="coerce")
        metrics["gross_margin"] = (gp / rev).iloc[-1]

    elif cogs_col and revenue_col:
        cogs = pd.to_numeric(df[cogs_col], errors="coerce")
        rev = pd.to_numeric(df[revenue_col], errors="coerce")
        metrics["gross_margin"] = ((rev - cogs) / rev).iloc[-1]

    # ---------------------------
    # 3. Operating Margin
    # ---------------------------
    operating_income_col = _find_column(df, [
        r"operating_income", r"ebit", r"operating_profit"
    ])

    if operating_income_col and revenue_col:
        op = pd.to_numeric(df[operating_income_col], errors="coerce")
        rev = pd.to_numeric(df[revenue_col], errors="coerce")
        metrics["operating_margin"] = (op / rev).iloc[-1]

    # ---------------------------
    # 4. Net Margin
    # ---------------------------
    net_income_col = _find_column(df, [
        r"net_income", r"net_profit", r"bottom_line"
    ])

    if net_income_col and revenue_col:
        ni = pd.to_numeric(df[net_income_col], errors="coerce")
        rev = pd.to_numeric(df[revenue_col], errors="coerce")
        metrics["net_margin"] = (ni / rev).iloc[-1]

    # ---------------------------
    # 5. Liquidity Ratios
    # ---------------------------
    current_assets_col = _find_column(df, [r"current_assets"])
    current_liabilities_col = _find_column(df, [r"current_liabilities"])

    if current_assets_col and current_liabilities_col:
        ca = pd.to_numeric(df[current_assets_col], errors="coerce").iloc[-1]
        cl = pd.to_numeric(df[current_liabilities_col], errors="coerce").iloc[-1]
        if cl:
            metrics["current_ratio"] = ca / cl

    quick_assets_col = _find_column(df, [r"quick_assets", r"cash", r"cash_equivalents"])

    if quick_assets_col and current_liabilities_col:
        qa = pd.to_numeric(df[quick_assets_col], errors="coerce").iloc[-1]
        cl = pd.to_numeric(df[current_liabilities_col], errors="coerce").iloc[-1]
        if cl:
            metrics["quick_ratio"] = qa / cl

    # ---------------------------
    # 6. Debt-to-Equity
    # ---------------------------
    total_debt_col = _find_column(df, [r"total_debt", r"loans", r"borrowings"])
    equity_col = _find_column(df, [r"equity", r"shareholder_equity", r"net_worth"])

    if total_debt_col and equity_col:
        debt = pd.to_numeric(df[total_debt_col], errors="coerce").iloc[-1]
        eq = pd.to_numeric(df[equity_col], errors="coerce").iloc[-1]
        if eq:
            metrics["debt_to_equity"] = debt / eq

    # ---------------------------
    # Final Cleanup
    # ---------------------------
    # Convert floats into python-native types (for JSON export & AI compatibility)
    cleaned_metrics = {}
    for key, value in metrics.items():
        if isinstance(value, (np.floating, np.float64, np.float32)):
            cleaned_metrics[key] = float(value)
        else:
            cleaned_metrics[key] = value

    return cleaned_metrics