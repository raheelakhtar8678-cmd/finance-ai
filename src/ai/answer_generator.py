def generate_answer(metric_name, result, variables):
    explanation = f"""
Metric: {metric_name.replace('_', ' ').title()}

Calculation:
"""

    for k, v in variables.items():
        explanation += f"- {k}: {v:.2f}\n"

    explanation += f"\nFinal Result: {result:.2f}\n"
    explanation += "\nThis result is derived directly from extracted financial tables."

    return explanation.strip()