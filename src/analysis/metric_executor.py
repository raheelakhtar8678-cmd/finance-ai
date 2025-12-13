from src.analysis.calculator import safe_eval_expr


def execute_metric(metric_config, df):
    variables = {}

    for col in df.columns:
        key = col.lower().replace(" ", "_")
        if key in metric_config["required_columns"]:
            variables[key] = df[col].dropna().astype(float).mean()

    if len(variables) < len(metric_config["required_columns"]):
        raise ValueError("Insufficient data for metric")

    result = safe_eval_expr(metric_config["formula"], variables)
    return result, variables