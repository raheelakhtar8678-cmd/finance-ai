# src/analysis/chart_decider.py

def should_generate_chart(metric_name, df, metric_metadata):
    """
    Determines whether a chart should be generated for a metric.
    Returns: (bool, chart_type)
    """

    meta = metric_metadata.get(metric_name)
    if not meta:
        return False, None

    chart_type = meta.get("chart")

    # No chart defined → scalar metric
    if not chart_type:
        return False, None

    # Check numeric columns
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) < 1:
        return False, None

    return True, chart_type