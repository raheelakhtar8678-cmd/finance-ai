# src/analysis/financial_reasoning.py
"""
Part C-3: Deterministic Financial Reasoning & Substitution Layer

This layer adds CFO-like intelligence WITHOUT using LLM:
- Understands financial synonyms (sales = revenue)
- Attempts deterministic substitutions
- Provides reasoned explanations when data is missing
- Maintains auditability and trust

This is NOT AI hallucination - it's financial domain knowledge.
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from src.analysis.calculator import safe_eval_expr

# =============================================================================
# FINANCIAL DOMAIN KNOWLEDGE (Curated by CFOs, Not AI)
# =============================================================================

# Column name substitutions (financial synonyms)
COLUMN_SYNONYMS = {
    "revenue": ["sales", "total_sales", "total_revenue", "net_revenue", 
                "gross_revenue", "turnover", "income_from_sales"],
    
    "cash": ["cash_and_cash_equivalents", "cash_balance", "total_cash",
             "available_cash", "cash_on_hand"],
    
    "expenses": ["operating_expenses", "total_expenses", "opex", "costs",
                 "operating_costs", "expenditures"],
    
    "cogs": ["cost_of_goods_sold", "cost_of_sales", "cost_of_revenue",
             "direct_costs"],
    
    "profit": ["net_income", "net_profit", "net_earnings", "bottom_line",
               "profit_after_tax"],
    
    "assets": ["total_assets", "current_assets"],
    
    "liabilities": ["total_liabilities", "current_liabilities"],
    
    "equity": ["shareholders_equity", "stockholders_equity", "owners_equity",
               "total_equity"],
}

# Derived metrics (can be computed from other columns)
DERIVED_METRICS = {
    "gross_profit": {
        "formula": "revenue - cogs",
        "requires": ["revenue", "cogs"],
        "description": "Revenue minus Cost of Goods Sold"
    },
    
    "operating_profit": {
        "formula": "revenue - cogs - operating_expenses",
        "requires": ["revenue", "cogs", "operating_expenses"],
        "description": "Gross profit minus operating expenses"
    },
    
    "working_capital": {
        "formula": "current_assets - current_liabilities",
        "requires": ["current_assets", "current_liabilities"],
        "description": "Current assets minus current liabilities"
    },
}

# =============================================================================
# COLUMN INTELLIGENCE
# =============================================================================

def find_column_with_reasoning(
    tables: List[dict],
    target_column: str,
    allow_synonyms: bool = True
) -> Tuple[Optional[pd.DataFrame], Optional[str], str]:
    """
    Find a column in tables with intelligent substitution.
    
    Returns:
        (dataframe, actual_column_name, reasoning_explanation)
    
    Example:
        df, col, reason = find_column_with_reasoning(tables, "revenue")
        # Returns: (df, "sales", "Using 'sales' as equivalent to 'revenue'")
    """
    
    # Step 1: Try exact match
    for table in tables:
        df = table.get("df")
        if df is None or df.empty:
            continue
        
        for col in df.columns:
            if str(col).lower().replace("_", " ") == target_column.lower().replace("_", " "):
                return df, col, f"Found exact match: '{col}'"
    
    # Step 2: Try synonyms if allowed
    if allow_synonyms and target_column in COLUMN_SYNONYMS:
        synonyms = COLUMN_SYNONYMS[target_column]
        
        for table in tables:
            df = table.get("df")
            if df is None or df.empty:
                continue
            
            for col in df.columns:
                col_normalized = str(col).lower().replace("_", " ").replace("-", " ")
                
                for synonym in synonyms:
                    synonym_normalized = synonym.lower().replace("_", " ")
                    
                    if synonym_normalized in col_normalized or col_normalized in synonym_normalized:
                        return df, col, f"Using '{col}' as financial equivalent of '{target_column}'"
    
    # Step 3: No match found
    return None, None, f"Column '{target_column}' not found (checked {len(tables)} tables)"

# =============================================================================
# METRIC REASONING ENGINE
# =============================================================================

class MetricReasoner:
    """
    Deterministic reasoning engine for financial metrics.
    
    This class attempts to compute metrics using:
    1. Exact columns
    2. Synonym substitution
    3. Derived computation
    4. Fallback explanation
    """
    
    def __init__(self, tables: List[dict]):
        self.tables = tables
        self.reasoning_log = []
    
    def _log_reasoning(self, step: str):
        """Track reasoning steps for auditability"""
        self.reasoning_log.append(step)
    
    def _extract_value(self, df: pd.DataFrame, column: str, method: str = 'last') -> Optional[float]:
        """Extract numeric value from a column"""
        try:
            series = pd.to_numeric(df[column], errors='coerce').dropna()
            if series.empty:
                return None
            
            if method == 'last':
                return float(series.iloc[-1])
            elif method == 'mean':
                return float(series.mean())
            elif method == 'sum':
                return float(series.sum())
            return float(series.iloc[-1])
        except:
            return None
    
    def compute_burn_rate(self) -> Dict[str, Any]:
        """
        Compute burn rate with intelligent reasoning.
        
        Returns:
            {
                "success": bool,
                "result": float or None,
                "reasoning": str,
                "calculation": str,
                "confidence": float
            }
        """
        self._log_reasoning("Attempting to compute burn rate (cash / monthly_expenses)")
        
        # Step 1: Find cash
        cash_df, cash_col, cash_reason = find_column_with_reasoning(self.tables, "cash")
        self._log_reasoning(cash_reason)
        
        if cash_df is None:
            return {
                "success": False,
                "result": None,
                "reasoning": "Cannot compute burn rate: No cash data found",
                "missing": ["cash"],
                "confidence": 0.0
            }
        
        cash_value = self._extract_value(cash_df, cash_col, method='last')
        
        # Step 2: Find expenses
        expense_df, expense_col, expense_reason = find_column_with_reasoning(self.tables, "expenses")
        self._log_reasoning(expense_reason)
        
        if expense_df is None:
            return {
                "success": False,
                "result": None,
                "reasoning": f"Found cash (${cash_value:,.0f}) but no expense data to compute burn rate",
                "missing": ["monthly_expenses"],
                "confidence": 0.3,
                "partial_data": {"cash": cash_value}
            }
        
        expense_value = self._extract_value(expense_df, expense_col, method='mean')
        
        # Step 3: Calculate
        if cash_value and expense_value and expense_value > 0:
            months = cash_value / expense_value
            
            calculation = f"${cash_value:,.0f} (cash) / ${expense_value:,.0f} (monthly expenses) = {months:.1f} months"
            
            reasoning = f"Burn rate calculated using '{cash_col}' and '{expense_col}'. "
            reasoning += f"At current spending rate, cash will last {months:.1f} months."
            
            self._log_reasoning(f"Successfully calculated: {calculation}")
            
            return {
                "success": True,
                "result": months,
                "reasoning": reasoning,
                "calculation": calculation,
                "confidence": 0.9,
                "variables": {
                    "cash": cash_value,
                    "monthly_burn": expense_value
                }
            }
        
        return {
            "success": False,
            "result": None,
            "reasoning": "Found cash and expense columns but could not extract numeric values",
            "confidence": 0.2
        }
    
    def compute_revenue_growth(self) -> Dict[str, Any]:
        """
        Compute revenue growth with intelligent reasoning.
        """
        self._log_reasoning("Attempting to compute revenue growth (YoY)")
        
        # Step 1: Find revenue
        revenue_df, revenue_col, revenue_reason = find_column_with_reasoning(self.tables, "revenue")
        self._log_reasoning(revenue_reason)
        
        if revenue_df is None:
            return {
                "success": False,
                "result": None,
                "reasoning": "Cannot compute revenue growth: No revenue/sales data found",
                "missing": ["revenue"],
                "confidence": 0.0
            }
        
        # Step 2: Extract time series
        try:
            revenue_series = pd.to_numeric(revenue_df[revenue_col], errors='coerce').dropna()
            
            if len(revenue_series) < 2:
                return {
                    "success": False,
                    "result": None,
                    "reasoning": f"Found revenue data (${float(revenue_series.iloc[0]):,.0f}) but need at least 2 periods for growth calculation",
                    "confidence": 0.4,
                    "partial_data": {"revenue_latest": float(revenue_series.iloc[0])}
                }
            
            # Calculate growth
            current = float(revenue_series.iloc[-1])
            previous = float(revenue_series.iloc[-2])
            
            if previous == 0:
                return {
                    "success": False,
                    "result": None,
                    "reasoning": "Cannot calculate growth: previous period revenue is zero",
                    "confidence": 0.3
                }
            
            growth_pct = ((current - previous) / previous) * 100
            growth_amount = current - previous
            
            calculation = f"(${current:,.0f} - ${previous:,.0f}) / ${previous:,.0f} × 100 = {growth_pct:+.1f}%"
            
            reasoning = f"Revenue growth calculated from '{revenue_col}': "
            reasoning += f"{'Increased' if growth_pct > 0 else 'Decreased'} by ${abs(growth_amount):,.0f} "
            reasoning += f"({growth_pct:+.1f}%) period-over-period."
            
            self._log_reasoning(f"Successfully calculated: {calculation}")
            
            return {
                "success": True,
                "result": growth_pct,
                "reasoning": reasoning,
                "calculation": calculation,
                "confidence": 0.95,
                "variables": {
                    "revenue_current": current,
                    "revenue_previous": previous,
                    "growth_amount": growth_amount
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "reasoning": f"Error extracting revenue data: {str(e)}",
                "confidence": 0.1
            }
    
    def compute_gross_margin(self) -> Dict[str, Any]:
        """
        Compute gross margin with intelligent reasoning.
        """
        self._log_reasoning("Attempting to compute gross margin: (revenue - cogs) / revenue")
        
        # Find revenue
        revenue_df, revenue_col, revenue_reason = find_column_with_reasoning(self.tables, "revenue")
        self._log_reasoning(revenue_reason)
        
        # Find COGS
        cogs_df, cogs_col, cogs_reason = find_column_with_reasoning(self.tables, "cogs")
        self._log_reasoning(cogs_reason)
        
        if revenue_df is None or cogs_df is None:
            missing = []
            if revenue_df is None:
                missing.append("revenue")
            if cogs_df is None:
                missing.append("cogs")
            
            return {
                "success": False,
                "result": None,
                "reasoning": f"Cannot compute gross margin: Missing {', '.join(missing)}",
                "missing": missing,
                "confidence": 0.0
            }
        
        # Extract values
        revenue_value = self._extract_value(revenue_df, revenue_col, method='last')
        cogs_value = self._extract_value(cogs_df, cogs_col, method='last')
        
        if revenue_value and cogs_value and revenue_value > 0:
            margin_pct = ((revenue_value - cogs_value) / revenue_value) * 100
            gross_profit = revenue_value - cogs_value
            
            calculation = f"(${revenue_value:,.0f} - ${cogs_value:,.0f}) / ${revenue_value:,.0f} × 100 = {margin_pct:.1f}%"
            
            reasoning = f"Gross margin calculated using '{revenue_col}' and '{cogs_col}': "
            reasoning += f"For every $1 in revenue, ${(gross_profit/revenue_value):.2f} is gross profit."
            
            return {
                "success": True,
                "result": margin_pct,
                "reasoning": reasoning,
                "calculation": calculation,
                "confidence": 0.95,
                "variables": {
                    "revenue": revenue_value,
                    "cogs": cogs_value,
                    "gross_profit": gross_profit
                }
            }
        
        return {
            "success": False,
            "result": None,
            "reasoning": "Found revenue and COGS columns but could not extract numeric values",
            "confidence": 0.2
        }
    
    def get_reasoning_log(self) -> List[str]:
        """Get full reasoning log for auditability"""
        return self.reasoning_log

# =============================================================================
# SIMPLE INTERFACE
# =============================================================================

def compute_metric_with_reasoning(
    metric_name: str,
    tables: List[dict]
) -> Dict[str, Any]:
    """
    Compute any financial metric with deterministic reasoning.
    
    Args:
        metric_name: "burn_rate", "revenue_growth", "gross_margin"
        tables: List of cleaned table dicts
    
    Returns:
        Full result with reasoning, confidence, and auditability
    """
    
    reasoner = MetricReasoner(tables)
    
    if metric_name == "burn_rate":
        result = reasoner.compute_burn_rate()
    elif metric_name == "revenue_growth":
        result = reasoner.compute_revenue_growth()
    elif metric_name == "gross_margin":
        result = reasoner.compute_gross_margin()
    else:
        return {
            "success": False,
            "result": None,
            "reasoning": f"Metric '{metric_name}' not yet implemented",
            "confidence": 0.0
        }
    
    # Add reasoning log for auditability
    result["reasoning_log"] = reasoner.get_reasoning_log()
    
    return result
