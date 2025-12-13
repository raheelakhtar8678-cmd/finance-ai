# src/visualization/chart_generator.py

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Set backend and apply a modern style for better aesthetics
plt.switch_backend("Agg")  
plt.style.use('seaborn-v0_8') 

class ChartGenerator:
    """
    Enhanced chart generator for multi-file usage.
    Auto-detects date columns, numeric columns, and avoids chart failures.
    """

    def __init__(self, output_dir="data/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Detect numeric columns
    # --------------------------------------------------------
    @staticmethod
    def _numeric_columns(df: pd.DataFrame):
        return df.select_dtypes(include=["number"]).columns.tolist()

    # --------------------------------------------------------
    # Detect date-like column (for timeseries charts)
    # --------------------------------------------------------
    @staticmethod
    def _detect_time_index(df: pd.DataFrame):
        for col in df.columns:
            if col.lower() in ["date", "month", "year", "period", "time"]:
                try:
                    # Attempt to convert the series to datetime objects
                    time_series = pd.to_datetime(df[col], errors='coerce')
                    # Check if conversion was successful for most values
                    if time_series.notna().sum() > len(df) * 0.5:
                        return time_series
                except Exception:
                    pass
        return None

    # --------------------------------------------------------
    # Safe index assignment for charts
    # --------------------------------------------------------
    def _prepare_index(self, df: pd.DataFrame):
        time_index = self._detect_time_index(df)
        if time_index is not None:
            df = df.copy()
            df.index = time_index
            return df

        # Fallback: use index
        df.index = df.index.astype(str)
        return df

    # --------------------------------------------------------
    # LINE CHART
    # --------------------------------------------------------
    def line_chart(self, df: pd.DataFrame, column: str, file_prefix: str = "", title: str = None):
        df = self._prepare_index(df)

        if column not in df.columns:
            return None

        plt.figure(figsize=(12, 6))
        # Use the default integer position index for plotting, regardless of what the real index is
        plt.plot(df.index, df[column], marker="o") 
        plt.title(title or f"Trend of {column}")
        plt.xlabel("Index / Date")
        plt.ylabel(column)
        plt.grid(True)
        
        # CRITICAL FIX: Sample X-axis Ticks for readability
        n_ticks = len(df.index)
        
        # Adjust step size dynamically to keep max ~15 readable labels
        step = max(1, n_ticks // 15) 
        
        # Select indices and corresponding labels to display
        # We sample the labels from the dataframe's actual index
        tick_indices = list(range(0, n_ticks, step))
        tick_labels = [df.index[i] for i in tick_indices]
        
        # Apply the sampled ticks
        # We need to set the location of the ticks (tick_indices) and their labels (tick_labels)
        plt.gca().set_xticks(tick_indices) # Set the positions for the ticks
        plt.gca().set_xticklabels(tick_labels, rotation=45, ha='right') # Set the labels and rotation
        
        plt.tight_layout() 

        filename = f"{file_prefix}_{column}_line.png".replace(" ", "_")
        filepath = self.output_dir / filename

        plt.savefig(filepath, dpi=220, bbox_inches="tight")
        plt.close()

        return filepath

    # --------------------------------------------------------
    # BAR CHART
    # --------------------------------------------------------
    def bar_chart(self, df: pd.DataFrame, column: str, file_prefix: str = "", title: str = None):
        df = self._prepare_index(df)

        if column not in df.columns:
            return None

        plt.figure(figsize=(12, 6)) 
        plt.bar(df.index.astype(str), df[column])
        plt.title(title or f"{column} Distribution")
        plt.xlabel("Index / Date")
        plt.ylabel(column)
        
        # CRITICAL FIX: Sample X-axis Ticks for readability
        n_ticks = len(df.index)
        step = max(1, n_ticks // 15)
        tick_indices = list(range(0, n_ticks, step))
        tick_labels = [df.index[i] for i in tick_indices]
        
        # Apply sampled ticks to the current axes (plt.gca())
        plt.gca().set_xticks(tick_indices)
        plt.gca().set_xticklabels(tick_labels, rotation=45, ha='right')
        
        plt.tight_layout() 

        filename = f"{file_prefix}_{column}_bar.png".replace(" ", "_")
        filepath = self.output_dir / filename

        plt.savefig(filepath, dpi=220, bbox_inches="tight")
        plt.close()

        return filepath

    # --------------------------------------------------------
    # MULTI-TREND CHART (e.g., Revenue + Profit vs Time)
    # --------------------------------------------------------
    def multi_trend_chart(self, df: pd.DataFrame, columns: list, file_prefix: str = "", title="Multiple Trends"):
        df = self._prepare_index(df)

        if not any(col in df.columns for col in columns):
            return None

        plt.figure(figsize=(12, 6))
        plotted = False

        for col in columns:
            if col in df.columns:
                plt.plot(df[col], marker="o", label=col)
                plotted = True

        if not plotted:
            return None

        plt.title(title)
        plt.xlabel("Index / Date")
        plt.ylabel("Values")
        plt.legend()
        plt.grid(True)

        # CRITICAL FIX: Sample X-axis Ticks for readability
        n_ticks = len(df.index)
        step = max(1, n_ticks // 15)
        tick_indices = list(range(0, n_ticks, step))
        tick_labels = [df.index[i] for i in tick_indices]
        
        plt.gca().set_xticks(tick_indices)
        plt.gca().set_xticklabels(tick_labels, rotation=45, ha='right')
        
        plt.tight_layout() 

        filename = f"{file_prefix}_multi_trend.png"
        filepath = self.output_dir / filename

        plt.savefig(filepath, dpi=220, bbox_inches="tight")
        plt.close()

        return filepath

    # --------------------------------------------------------
    # AUTO-GENERATE CHARTS FOR ANY FILE
    # --------------------------------------------------------
    def generate_all_charts(self, df: pd.DataFrame, file_prefix: str):
        """
        Called when user uploads 1–5 files.
        Produces:
            • Line charts for numeric columns
            • A multi-trend chart (first 3 numeric columns)
        """
        numeric_cols = self._numeric_columns(df)
        results = []

        if not numeric_cols:
            return results  # no numeric data

        # Generate line charts
        for col in numeric_cols:
            path = self.line_chart(df, col, file_prefix)
            if path:
                results.append(path)

        # Multi-column trend (up to 3 columns)
        if len(numeric_cols) >= 2:
            multi_cols = numeric_cols[:3]
            path = self.multi_trend_chart(df, multi_cols, file_prefix)
            if path:
                results.append(path)

        return results