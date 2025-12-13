# metric_registry.py

# Assuming burn_rate and revenue_growth are functions defined in metric_executor.py
from src.analysis.metric_executor import burn_rate, revenue_growth 

# This registry maps metric names (lowercase) to their executable functions.
# The `handle_query` function will use this dictionary.
METRIC_REGISTRY_FUNCTIONS = {
    "burn rate": burn_rate,
    "revenue growth": revenue_growth,
}

# NOTE: The metadata you provided previously (formula, keywords, required_columns) 
# is typically used by the 'resolve_intent' pipeline. If that data is still needed
# by other parts of the system, it should be kept, possibly under a different name,
# but since you only provided a partial structure for it, I'm focusing on the 
# executable functions you explicitly asked to add.

# Metadata from your sources (if needed elsewhere in the project):
METRIC_METADATA = {
    "burn_rate": {
        "keywords": ["burn rate", "cash burn", "runway"],
        "formula": "cash / monthly_expenses",
        "required_columns": ["cash", "expenses"],
        "chart": "line",
        "description": "Cash runway in months"
    },
    "revenue_growth": {
        "keywords": ["revenue growth", "yoy revenue", "sales growth"],
        "formula": "(revenue_t2 - revenue_t1) / revenue_t1",
        "required_columns": ["revenue"],
        "chart": "line",
        "description": "Year-over-year revenue growth"
    },
}