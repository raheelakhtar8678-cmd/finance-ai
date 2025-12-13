# src/visualization/table_formatter.py

import pandas as pd

class TableFormatter:
    """
    Create clean, formatted tables for UI, dashboards, and reports.
    Supports:
    - Currency formatting
    - Percentage formatting
    - Column alignment
    - HTML + Markdown export
    """

    def __init__(self, currency_symbol="$", decimals=2):
        self.currency_symbol = currency_symbol
        self.decimals = decimals

    # -------------------------------------------------------
    # BASIC CLEAN FORMATTING
    # -------------------------------------------------------
    def format_currency(self, df: pd.DataFrame, columns: list):
        """
        Apply currency formatting to selected columns.
        """
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: f"{self.currency_symbol}{x:,.{self.decimals}f}"
                    if pd.notnull(x) and isinstance(x, (int, float))
                    else x
                )
        return df

    def format_percent(self, df: pd.DataFrame, columns: list):
        """
        Convert decimals to clean percentage strings.
        Example: 0.345 → 34.5%
        """
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: f"{x*100:.{self.decimals}f}%"
                    if pd.notnull(x) and isinstance(x, (int, float))
                    else x
                )
        return df

    # -------------------------------------------------------
    # SUMMARY TABLE BUILDER
    # -------------------------------------------------------
    def summary_table(self, df: pd.DataFrame, title="Summary"):
        """
        Adds total row + clean formatting.
        """
        summary = df.copy()

        # Numeric-only columns
        numeric_cols = summary.select_dtypes(include=['number']).columns

        # Add total row (bottom)
        if len(numeric_cols) > 0:
            totals = summary[numeric_cols].sum()
            totals_row = {col: totals.get(col, "") for col in summary.columns}
            summary.loc["Total"] = totals_row

        summary.index = summary.index.astype(str)
        summary.index.name = title
        return summary

    # -------------------------------------------------------
    # EXPORT FOR UI
    # -------------------------------------------------------
    def to_html(self, df: pd.DataFrame, classes="table table-striped table-bordered"):
        """
        Convert DataFrame into clean HTML table for UI (Streamlit/React/FastAPI).
        """
        return df.to_html(classes=classes, border=0)

    def to_markdown(self, df: pd.DataFrame):
        """
        Convert DataFrame into Markdown for PDF/PPT report export.
        """
        return df.to_markdown(index=True)