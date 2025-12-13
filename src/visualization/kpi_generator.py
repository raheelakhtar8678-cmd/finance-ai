# E:\finance-ai\src\visualization\kpi_generator.py

import os
from pathlib import Path
import pandas as pd
from src.analysis.financial_metrics import compute_financial_metrics
from typing import Dict, Any, List

# --- FUNCTION 1: Generates a Detailed KPI Report and Saves a CSV ---
def generate_kpi_report(df: pd.DataFrame, output_dir: str) -> Dict[str, Any]:
    """
    Generate a detailed KPI summary from a cleaned financial table, 
    compute complex financial metrics, and save the results to a CSV file.

    Args:
        df (pd.DataFrame): The cleaned financial data table.
        output_dir (str): The directory where the kpi_summary.csv will be saved.

    Returns:
        Dict[str, Any]: KPI name -> value dictionary.
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    # Compute metrics using the function from src.analysis
    metrics = compute_financial_metrics(df)

    kpi_output = {}

    for k, v in metrics.items():
        # Convert None into a readable format
        val = "N/A" if v is None else v
        kpi_output[k] = val

    # Save KPI CSV
    kpi_path = Path(output_dir) / "kpi_summary.csv"
    pd.DataFrame.from_dict(kpi_output, orient="index", columns=["value"]).to_csv(kpi_path)

    return kpi_output


# --- FUNCTION 2: Generates Simple Descriptive KPIs (Previously the one overwriting the first) ---
def generate_df_summary_kpis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates simple statistical KPIs (latest, mean, min, max) for all 
    numeric columns in a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, one for each numeric column.
    """
    kpis = []
    
    # Iterate only over numeric columns
    for col in df.select_dtypes("number").columns:
        series = df[col].dropna()
        
        # Skip if the column is empty after dropping NaNs
        if series.empty:
            continue
        
        # FIX: Correct indentation to place append inside the loop
        kpis.append({
            "name": col,
            "latest": series.iloc[-1],
            "mean": series.mean(),
            "min": series.min(),
            "max": series.max()
        })
        
    return kpis