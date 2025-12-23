# src/analysis/financial_reasoning.py
"""
Financial Reasoning Engine with Chart Generation Support
Handles synonym matching, calculations, and returns data for charts
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


# ==========================================
# COLUMN SYNONYMS (Expanded)
# ==========================================

COLUMN_SYNONYMS = {
    "revenue": ["sales", "total_sales", "total_revenue", "net_revenue", 
                "gross_revenue", "turnover", "income_from_sales", "top_line",
                "rev", "monthly_revenue", "annual_revenue"],
    
    "cash": ["cash_and_cash_equivalents", "cash_balance", "total_cash",
             "available_cash", "cash_on_hand", "liquid_assets", "bank_balance",
             "cash_at_bank", "ending_cash", "cash_and_equivalents"],
    
    "expenses": ["operating_expenses", "total_expenses", "opex", "costs",
                 "operating_costs", "expenditures", "burn", "monthly_burn", 
                 "outflow", "spend", "total_spend", "expenses_total",
                 "monthly_expenses", "operating_expenditure"],
    
    "profit": ["net_income", "net_profit", "net_earnings", "bottom_line",
               "profit_loss", "net_result", "earnings", "income"],
    
    "cogs": ["cost_of_goods_sold", "cost_of_sales", "direct_costs",
             "production_costs", "cogs_total"],
    
    "assets": ["total_assets", "current_assets", "fixed_assets",
               "asset_total", "balance_sheet_assets"],
    
    "liabilities": ["total_liabilities", "current_liabilities", "debt",
                    "obligations", "payables"],
    
    "equity": ["shareholder_equity", "stockholder_equity", "net_worth",
               "owner_equity", "equity_total"],
    
    "operating_income": ["ebit", "operating_profit", "operational_income",
                         "income_from_operations"],
    
    "cash_flow": ["cash_flow_from_operations", "operating_cash_flow",
                  "ocf", "cash_from_ops"],
}


# ==========================================
# COLUMN FINDER (With Synonym Matching)
# ==========================================

def find_column_with_reasoning(
    tables: List[dict], 
    metric_name: str
) -> Tuple[Optional[pd.DataFrame], Optional[str], float]:
    """
    Find column using synonym matching.
    
    Returns:
        (dataframe, column_name, confidence_score)
    """
    
    # Get synonyms for this metric
    synonyms = COLUMN_SYNONYMS.get(metric_name, [metric_name])
    
    for table_dict in tables:
        df = table_dict["df"]
        
        # Try exact match first
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Check against metric name
            if metric_name.lower() in col_lower:
                return df, col, 1.0
            
            # Check against all synonyms
            for synonym in synonyms:
                if synonym.lower() in col_lower:
                    return df, col, 0.9
    
    return None, None, 0.0


# ==========================================
# METRIC REASONER CLASS
# ==========================================

class MetricReasoner:
    """
    Deterministic financial metric calculator with reasoning logs
    """
    
    def __init__(self, tables: List[dict]):
        self.tables = tables
        self.reasoning_log = []
    
    def get_reasoning_log(self) -> List[str]:
        return self.reasoning_log
    
    def _log(self, message: str):
        self.reasoning_log.append(message)
        print(f"   📝 {message}")
    
    def _extract_value(self, df: pd.DataFrame, col: str) -> float:
        """Extract numeric value from column"""
        try:
            # Get last value (most recent)
            val = df[col].iloc[-1]
            return float(val)
        except:
            # Try first value
            try:
                val = df[col].iloc[0]
                return float(val)
            except:
                return 0.0
    
    def compute_burn_rate(self) -> Dict[str, Any]:
        """Calculate burn rate with reasoning"""
        
        self._log("Attempting to compute burn rate")
        
        # Find cash
        df_cash, col_cash, conf_cash = find_column_with_reasoning(self.tables, "cash")
        
        if df_cash is None:
            self._log("❌ Cash column not found")
            return {
                "success": False,
                "result": None,
                "reasoning": "Advisory: Required data (Cash) is missing.",
                "confidence": 0.0
            }
        
        # Find expenses
        df_exp, col_exp, conf_exp = find_column_with_reasoning(self.tables, "expenses")
        
        if df_exp is None:
            self._log("❌ Expenses column not found")
            return {
                "success": False,
                "result": None,
                "reasoning": "Advisory: Required data (Expenses) is missing.",
                "confidence": 0.0
            }
        
        # Extract values
        cash = self._extract_value(df_cash, col_cash)
        expenses = self._extract_value(df_exp, col_exp)
        
        if expenses == 0:
            return {
                "success": False,
                "result": None,
                "reasoning": "Cannot calculate: Monthly expenses are zero.",
                "confidence": 0.0
            }
        
        # Calculate
        months = cash / expenses
        
        self._log(f"✅ Burn rate calculated: {months:.1f} months")
        
        return {
            "success": True,
            "result": months,
            "reasoning": f"Cash runway: ${cash:,.0f} / ${expenses:,.0f} per month = {months:.1f} months",
            "confidence": min(conf_cash, conf_exp),
            "calculation": f"{cash} / {expenses}",
            "df": df_cash,  # For chart generation
            "col": col_cash
        }
    
    def compute_revenue_growth(self) -> Dict[str, Any]:
        """Calculate revenue growth with reasoning"""
        
        self._log("Attempting to compute revenue growth")
        
        # Find revenue
        df, col, conf = find_column_with_reasoning(self.tables, "revenue")
        
        if df is None:
            self._log("❌ Revenue column not found")
            return {
                "success": False,
                "result": None,
                "reasoning": "Revenue data not found in uploaded documents.",
                "confidence": 0.0
            }
        
        # Need at least 2 periods
        if len(df) < 2:
            self._log("❌ Insufficient historical data")
            return {
                "success": False,
                "result": None,
                "reasoning": "Insufficient historical revenue data (need at least 2 periods).",
                "confidence": 0.0,
                "df": df,  # Still return df for potential chart
                "col": col
            }
        
        # Get last two values
        current = float(df[col].iloc[-1])
        previous = float(df[col].iloc[-2])
        
        if previous == 0:
            return {
                "success": False,
                "result": None,
                "reasoning": "Cannot calculate growth: Previous period revenue is zero.",
                "confidence": 0.0
            }
        
        # Calculate growth
        growth = ((current - previous) / previous) * 100
        
        self._log(f"✅ Revenue growth calculated: {growth:+.1f}%")
        
        return {
            "success": True,
            "result": growth,
            "reasoning": f"Revenue grew from ${previous:,.0f} to ${current:,.0f} ({growth:+.1f}%)",
            "confidence": conf,
            "calculation": f"({current} - {previous}) / {previous} * 100",
            "df": df,  # For chart generation
            "col": col
        }
    
    def compute_simple_metric(self, metric_name: str) -> Dict[str, Any]:
        """
        Generic handler for simple column lookups (revenue, profit, etc.)
        Returns data suitable for chart generation
        """
        
        self._log(f"Looking up: {metric_name}")
        
        df, col, conf = find_column_with_reasoning(self.tables, metric_name)
        
        if df is None:
            self._log(f"❌ {metric_name} not found")
            return {
                "success": False,
                "result": None,
                "reasoning": f"{metric_name.title()} data not found in uploaded documents.",
                "confidence": 0.0
            }
        
        # Extract value
        val = self._extract_value(df, col)
        
        self._log(f"✅ Found {metric_name}: {val}")
        
        return {
            "success": True,
            "result": val,
            "reasoning": f"Found {metric_name} in column '{col}': ${val:,.2f}",
            "confidence": conf,
            "df": df,  # For chart generation
            "col": col
        }


# ==========================================
# MAIN ENTRY POINT
# ==========================================

def compute_metric_with_reasoning(metric_name: str, tables: List[dict]) -> Dict[str, Any]:
    """
    Main entry point for metric computation.
    
    Handles both complex calculations and simple lookups.
    Returns data suitable for chart generation.
    """
    
    reasoner = MetricReasoner(tables)
    
    # Handle specific calculations
    if metric_name == "burn_rate" or metric_name == "burn rate":
        result = reasoner.compute_burn_rate()
    
    elif metric_name == "revenue_growth" or metric_name == "revenue growth":
        result = reasoner.compute_revenue_growth()
    
    # Add other complex metrics here (gross_margin, net_profit_margin, etc.)
    
    # Fallback: Simple column lookup for base metrics
    else:
        result = reasoner.compute_simple_metric(metric_name)
    
    # Add reasoning log
    result["reasoning_log"] = reasoner.get_reasoning_log()
    
    # ✅ CHART INTEGRATION: Add chart generation if data found
    if result.get("success") and result.get("df") is not None and result.get("col") is not None:
        try:
            from src.visualization.chart_generator import generate_chart
            from pathlib import Path
            
            df = result["df"]
            col = result["col"]
            
            # Get x-axis column (date/period or index)
            x_col = None
            for potential_x in df.columns:
                if potential_x != col and str(potential_x).lower() in ['date', 'period', 'year', 'quarter', 'month']:
                    x_col = potential_x
                    break
            
            if x_col is None:
                # Use first non-numeric column or index
                non_numeric = df.select_dtypes(exclude='number').columns.tolist()
                x_col = non_numeric[0] if non_numeric else df.columns[0]
            
            # Generate chart
            output_path = f"data/static/{metric_name.replace(' ', '_')}.png"
            Path("data/static").mkdir(parents=True, exist_ok=True)
            
            chart_result = generate_chart(
                df=df,
                x_col=x_col,
                y_col=col,
                title=f"{metric_name.replace('_', ' ').title()} Analysis",
                output_path=output_path
            )
            
            if chart_result.get("success"):
                result["chart_path"] = chart_result.get("image_path")
                print(f"✅ Chart generated: {chart_result.get('image_path')}")
        
        except Exception as e:
            print(f"⚠️ Chart generation failed: {e}")
            result["chart_path"] = None
    
    return result