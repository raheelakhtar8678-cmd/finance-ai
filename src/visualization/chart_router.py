# src/visualization/chart_router.py

import pandas as pd


def find_chartable_tables(tables):
    """
    Returns tables that contain at least one numeric column
    suitable for charting.
    """
    candidates = []

    for t in tables:
        df = t["df"]
        numeric_cols = df.select_dtypes(include="number").columns

        if len(numeric_cols) >= 1:
            candidates.append({
                "source": t.get("source"),
                "df": df,
                "cols": numeric_cols.tolist()
            })

    return candidates


def generate_metric_chart(chart_gen, df, metric_name):
    """
    Generates a chart for a metric using the provided ChartGenerator.
    Used AFTER metric execution.
    """

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return None

    # Use first numeric column by default
    y_col = numeric_cols[0]

    try:
        return chart_gen.line_chart(df, y_col)
    except Exception:
        return None


def generate_metric_chart(chart_gen, df, metric_name):
    """
    Compatibility layer used by query_controller.py
    Routes metric intent to an appropriate chart type.
    """
    try:
        metric_name = metric_name.lower()
        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        if not numeric_cols:
            return None

        y_col = numeric_cols[0]

        # Routing logic (minimal, deterministic)
        if "growth" in metric_name or "trend" in metric_name:
            return chart_gen.line_chart(df, y_col)

        if "rate" in metric_name or "margin" in metric_name:
            return chart_gen.bar_chart(df, y_col)

        # Fallback
        return chart_gen.bar_chart(df, y_col)

    except Exception as e:
        print(f"[ChartRouter] Chart generation failed: {e}")
        return None
