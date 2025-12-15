# src/analysis/metric_registry.py

from src.analysis.metric_executor import (
    burn_rate, 
    revenue_growth, 
    gross_margin, 
    net_profit_margin # ✅ Added this import
)

# -------------------------------------------------
# Executable metric functions (used by query routing)
# -------------------------------------------------
METRIC_REGISTRY_FUNCTIONS = {
    "burn rate": burn_rate,
    "revenue growth": revenue_growth,
    "gross margin": gross_margin,
    "net profit margin": net_profit_margin, # ✅ Added this entry
}

# -------------------------------------------------
# Metric metadata (used for routing & visualization)
# -------------------------------------------------
METRIC_METADATA = {
    "burn rate": {
        "keywords": ["burn rate", "cash burn", "runway", "months left"],
        "required_columns": ["cash", "monthly_expenses"],
        "formula": "cash / monthly_expenses",
        "chart": None,
        "chart_when_series": False,
        "description": "Cash runway in months"
    },
    "revenue growth": {
        "keywords": ["revenue growth", "yoy revenue", "sales growth", "revenue trend"],
        "required_columns": ["revenue"],
        "formula": "(revenue_current - revenue_previous) / revenue_previous * 100",
        "chart": "line",
        "chart_when_series": True,
        "description": "Year-over-year revenue growth"
    },
    "gross margin": {
        "keywords": ["gross margin", "gross profit margin"],
        "required_columns": ["revenue", "cogs"],
        "formula": "(revenue - cogs) / revenue * 100",
        "chart": None,
        "chart_when_series": False,
        "description": "Gross profit as percentage of revenue"
    },
    "net profit margin": {
        "keywords": ["net profit margin", "net margin", "profit margin"],
        "required_columns": ["revenue", "net_profit"],
        "formula": "net_profit / revenue * 100",
        "chart": None,
        "chart_when_series": False,
        "description": "Net profit as percentage of revenue"
    },
}

# Alias for backward compatibility
METRIC_REGISTRY = METRIC_METADATA