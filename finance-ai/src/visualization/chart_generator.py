# src/visualization/chart_generator.py

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.switch_backend("Agg")  # Ensure no GUI needed (server-safe)

class ChartGenerator:
    """
    Creates financial charts (line, bar, trends) from cleaned DataFrames.
    Saves PNG files for use in UI or reports.
    """

    def __init__(self, output_dir="data/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------
    # Auto-detect numerical columns
    # ---------------------------------------------------
    @staticmethod
    def _numeric_columns(df: pd.DataFrame):
        numeric_cols = df.select_dtypes(include=['number', 'float', 'int']).columns.tolist()
        return numeric_cols

    # ---------------------------------------------------
    # LINE CHART
    # ---------------------------------------------------
    def line_chart(self, df: pd.DataFrame, column: str, title: str = None, filename: str = None):
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")

        plt.figure(figsize=(10, 5))
        plt.plot(df[column], marker="o")
        plt.title(title or f"Trend of {column}")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.grid(True)

        filename = filename or f"{column}_line.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        plt.close()

        return filepath

    # ---------------------------------------------------
    # BAR CHART
    # ---------------------------------------------------
    def bar_chart(self, df: pd.DataFrame, column: str, title: str = None, filename: str = None):
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")

        plt.figure(figsize=(10, 5))
        plt.bar(df.index.astype(str), df[column])
        plt.title(title or f"{column} Bar Chart")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.xticks(rotation=45)

        filename = filename or f"{column}_bar.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        plt.close()

        return filepath

    # ---------------------------------------------------
    # MULTI-COLUMN TREND CHART
    # ---------------------------------------------------
    def multi_trend_chart(self, df: pd.DataFrame, columns: list, title="Multiple Trends", filename="multi_trend.png"):
        plt.figure(figsize=(12, 6))

        for col in columns:
            if col in df.columns:
                plt.plot(df[col], marker="o", label=col)

        plt.title(title)
        plt.xlabel("Index")
        plt.ylabel("Values")
        plt.legend()
        plt.grid(True)

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        plt.close()

        return filepath