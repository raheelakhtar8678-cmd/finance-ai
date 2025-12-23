# src/analysis/metric_registry.py

# -------------------------------------------------
# Metric metadata (used for routing & visualization)
# -------------------------------------------------
METRIC_METADATA = {
    # ✅ 1. BASE METRICS (The missing piece)
    "revenue": {
        "keywords": ["revenue", "sales", "turnover", "top line", "income", "total sales"],
        "required_columns": ["revenue"],
        "formula": "revenue", # Direct lookup
        "chart": "bar",
        "chart_when_series": True,
        "description": "Total revenue/sales for the period"
    },
    "expenses": {
        "keywords": ["expenses", "costs", "spending", "opex", "outflow", "expenditure"],
        "required_columns": ["expenses"],
        "formula": "expenses", # Direct lookup
        "chart": "bar",
        "chart_when_series": True,
        "description": "Total operating expenses"
    },
    "profit": {
        "keywords": ["profit", "net income", "earnings", "bottom line", "net profit"],
        "required_columns": ["net_profit"],
        "formula": "net_profit", # Direct lookup
        "chart": "bar",
        "chart_when_series": True,
        "description": "Net profit or loss"
    },

    # ✅ 2. CALCULATED METRICS (Your existing logic)
    "burn rate": {
        "keywords": ["burn rate", "cash burn", "runway", "months left"],
        "required_columns": ["cash", "monthly_expenses"],
        "formula": "cash / monthly_expenses",
        "chart": None,
        "chart_when_series": False,
        "description": "Cash runway in months"
    },
    "revenue_growth": {
        "keywords": ["revenue growth", "yoy revenue", "sales growth", "revenue trend", "growth"],
        "required_columns": ["revenue"],
        "formula": "(revenue_current - revenue_previous) / revenue_previous * 100",
        "chart": "line",
        "chart_when_series": True,
        "description": "Year-over-year revenue growth"
    },
    "gross_margin": {
        "keywords": ["gross margin", "gross profit margin"],
        "required_columns": ["revenue", "cogs"],
        "formula": "(revenue - cogs) / revenue * 100",
        "chart": None,
        "chart_when_series": False,
        "description": "Gross profit as percentage of revenue"
    },
    "net_profit_margin": {
        "keywords": ["net profit margin", "net margin", "profit margin"],
        "required_columns": ["revenue", "net_profit"],
        "formula": "net_profit / revenue * 100",
        "chart": None,
        "chart_when_series": False,
        "description": "Net profit as percentage of revenue"
    },
}

# Alias for compatibility with router
METRIC_REGISTRY = METRIC_METADATA

# -------------------------------------------------
# Executable functions (Optional: can be None for direct lookups)
# -------------------------------------------------
# The router uses this to map strings to functions. 
# For base metrics (revenue/expenses), the 'compute_metric_with_reasoning' 
# function handles them dynamically without needing a specific function here.
METRIC_REGISTRY_FUNCTIONS = {
    # We map these to None or specific handlers if you have them.
    # The reasoning engine handles direct column lookups automatically.
}