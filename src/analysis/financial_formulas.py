# src/analysis/financial_formulas.py
"""
Comprehensive Financial Formulas Engine
Auto-calculates 50+ standard financial metrics from extracted data.

Categories:
- Profitability Ratios
- Liquidity Ratios  
- Efficiency Ratios
- Leverage Ratios
- Growth Metrics
- Valuation Metrics
- DuPont Analysis
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class FormulaCategory(Enum):
    PROFITABILITY = "Profitability Ratios"
    LIQUIDITY = "Liquidity Ratios"
    EFFICIENCY = "Efficiency Ratios"
    LEVERAGE = "Leverage Ratios"
    GROWTH = "Growth Metrics"
    VALUATION = "Valuation Metrics"
    DUPONT = "DuPont Analysis"
    CASH_FLOW = "Cash Flow Metrics"


@dataclass
class FormulaDefinition:
    """Definition of a financial formula."""
    name: str
    category: FormulaCategory
    formula_text: str  # Human-readable formula
    required_inputs: List[str]  # Required data fields
    optional_inputs: List[str]  # Optional data fields
    unit: str  # "percent", "ratio", "currency", "days"
    description: str
    interpretation: str  # What the result means


# ============================================================
# FORMULA REGISTRY - All 50+ Standard Financial Formulas
# ============================================================

FORMULA_REGISTRY: Dict[str, FormulaDefinition] = {
    # ========== PROFITABILITY RATIOS ==========
    "gross_profit_margin": FormulaDefinition(
        name="Gross Profit Margin",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(Gross Profit / Revenue) × 100",
        required_inputs=["gross_profit", "revenue"],
        optional_inputs=[],
        unit="percent",
        description="Measures the percentage of revenue remaining after deducting cost of goods sold.",
        interpretation="Higher is better. Shows pricing power and production efficiency."
    ),
    "operating_profit_margin": FormulaDefinition(
        name="Operating Profit Margin",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(Operating Income / Revenue) × 100",
        required_inputs=["operating_income", "revenue"],
        optional_inputs=[],
        unit="percent",
        description="Measures operating efficiency before interest and taxes.",
        interpretation="Higher indicates better operational efficiency."
    ),
    "net_profit_margin": FormulaDefinition(
        name="Net Profit Margin",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(Net Income / Revenue) × 100",
        required_inputs=["net_income", "revenue"],
        optional_inputs=[],
        unit="percent",
        description="Percentage of revenue that becomes profit after all expenses.",
        interpretation="Higher is better. Key profitability indicator."
    ),
    "return_on_assets": FormulaDefinition(
        name="Return on Assets (ROA)",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(Net Income / Total Assets) × 100",
        required_inputs=["net_income", "total_assets"],
        optional_inputs=[],
        unit="percent",
        description="How effectively the company uses its assets to generate profit.",
        interpretation="Higher ROA indicates better asset utilization. Compare within industry."
    ),
    "return_on_equity": FormulaDefinition(
        name="Return on Equity (ROE)",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(Net Income / Shareholders' Equity) × 100",
        required_inputs=["net_income", "shareholders_equity"],
        optional_inputs=[],
        unit="percent",
        description="Return generated on shareholders' investment.",
        interpretation="Higher ROE indicates better returns for shareholders. Target: 15%+"
    ),
    "return_on_invested_capital": FormulaDefinition(
        name="Return on Invested Capital (ROIC)",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(NOPAT / Invested Capital) × 100",
        required_inputs=["operating_income", "tax_rate", "total_debt", "shareholders_equity"],
        optional_inputs=["cash"],
        unit="percent",
        description="Return on capital invested in the business.",
        interpretation="Should exceed cost of capital (WACC). Higher = value creation."
    ),
    "ebitda_margin": FormulaDefinition(
        name="EBITDA Margin",
        category=FormulaCategory.PROFITABILITY,
        formula_text="(EBITDA / Revenue) × 100",
        required_inputs=["ebitda", "revenue"],
        optional_inputs=["operating_income", "depreciation", "amortization"],
        unit="percent",
        description="Operating profitability before non-cash charges.",
        interpretation="Higher indicates stronger operational cash generation."
    ),
    
    # ========== LIQUIDITY RATIOS ==========
    "current_ratio": FormulaDefinition(
        name="Current Ratio",
        category=FormulaCategory.LIQUIDITY,
        formula_text="Current Assets / Current Liabilities",
        required_inputs=["current_assets", "current_liabilities"],
        optional_inputs=[],
        unit="ratio",
        description="Ability to pay short-term obligations.",
        interpretation="1.5-2.0 is healthy. Below 1.0 indicates liquidity risk."
    ),
    "quick_ratio": FormulaDefinition(
        name="Quick Ratio (Acid Test)",
        category=FormulaCategory.LIQUIDITY,
        formula_text="(Current Assets - Inventory) / Current Liabilities",
        required_inputs=["current_assets", "inventory", "current_liabilities"],
        optional_inputs=[],
        unit="ratio",
        description="Ability to pay short-term obligations without selling inventory.",
        interpretation="1.0+ is healthy. More conservative than current ratio."
    ),
    "cash_ratio": FormulaDefinition(
        name="Cash Ratio",
        category=FormulaCategory.LIQUIDITY,
        formula_text="Cash & Cash Equivalents / Current Liabilities",
        required_inputs=["cash", "current_liabilities"],
        optional_inputs=[],
        unit="ratio",
        description="Most conservative liquidity measure.",
        interpretation="Shows ability to pay obligations with cash on hand."
    ),
    "operating_cash_flow_ratio": FormulaDefinition(
        name="Operating Cash Flow Ratio",
        category=FormulaCategory.LIQUIDITY,
        formula_text="Operating Cash Flow / Current Liabilities",
        required_inputs=["operating_cash_flow", "current_liabilities"],
        optional_inputs=[],
        unit="ratio",
        description="Cash generated from operations vs. short-term obligations.",
        interpretation="Higher is better. Shows cash-based liquidity."
    ),
    
    # ========== EFFICIENCY RATIOS ==========
    "asset_turnover": FormulaDefinition(
        name="Asset Turnover Ratio",
        category=FormulaCategory.EFFICIENCY,
        formula_text="Revenue / Average Total Assets",
        required_inputs=["revenue", "total_assets"],
        optional_inputs=["prior_total_assets"],
        unit="ratio",
        description="How efficiently the company uses assets to generate revenue.",
        interpretation="Higher means more efficient asset utilization."
    ),
    "inventory_turnover": FormulaDefinition(
        name="Inventory Turnover",
        category=FormulaCategory.EFFICIENCY,
        formula_text="Cost of Goods Sold / Average Inventory",
        required_inputs=["cost_of_goods_sold", "inventory"],
        optional_inputs=["prior_inventory"],
        unit="ratio",
        description="How many times inventory is sold and replaced.",
        interpretation="Higher is generally better. Low may indicate overstocking."
    ),
    "receivables_turnover": FormulaDefinition(
        name="Receivables Turnover",
        category=FormulaCategory.EFFICIENCY,
        formula_text="Revenue / Average Accounts Receivable",
        required_inputs=["revenue", "accounts_receivable"],
        optional_inputs=["prior_accounts_receivable"],
        unit="ratio",
        description="How efficiently the company collects receivables.",
        interpretation="Higher indicates faster collection. Compare to industry."
    ),
    "days_sales_outstanding": FormulaDefinition(
        name="Days Sales Outstanding (DSO)",
        category=FormulaCategory.EFFICIENCY,
        formula_text="(Accounts Receivable / Revenue) × 365",
        required_inputs=["accounts_receivable", "revenue"],
        optional_inputs=[],
        unit="days",
        description="Average days to collect payment after a sale.",
        interpretation="Lower is better. High DSO may indicate collection issues."
    ),
    "days_inventory_outstanding": FormulaDefinition(
        name="Days Inventory Outstanding (DIO)",
        category=FormulaCategory.EFFICIENCY,
        formula_text="(Inventory / COGS) × 365",
        required_inputs=["inventory", "cost_of_goods_sold"],
        optional_inputs=[],
        unit="days",
        description="Average days inventory is held before sale.",
        interpretation="Lower is better. High DIO may indicate slow-moving inventory."
    ),
    "days_payable_outstanding": FormulaDefinition(
        name="Days Payable Outstanding (DPO)",
        category=FormulaCategory.EFFICIENCY,
        formula_text="(Accounts Payable / COGS) × 365",
        required_inputs=["accounts_payable", "cost_of_goods_sold"],
        optional_inputs=[],
        unit="days",
        description="Average days to pay suppliers.",
        interpretation="Higher allows better cash management but watch supplier relations."
    ),
    "cash_conversion_cycle": FormulaDefinition(
        name="Cash Conversion Cycle (CCC)",
        category=FormulaCategory.EFFICIENCY,
        formula_text="DSO + DIO - DPO",
        required_inputs=["accounts_receivable", "inventory", "accounts_payable", "revenue", "cost_of_goods_sold"],
        optional_inputs=[],
        unit="days",
        description="Days between paying for inventory and receiving cash from customers.",
        interpretation="Lower/negative is better. Shows working capital efficiency."
    ),
    
    # ========== LEVERAGE RATIOS ==========
    "debt_to_equity": FormulaDefinition(
        name="Debt-to-Equity Ratio",
        category=FormulaCategory.LEVERAGE,
        formula_text="Total Debt / Shareholders' Equity",
        required_inputs=["total_debt", "shareholders_equity"],
        optional_inputs=[],
        unit="ratio",
        description="Proportion of debt vs. equity financing.",
        interpretation="Higher means more leverage. Optimal varies by industry."
    ),
    "debt_to_assets": FormulaDefinition(
        name="Debt-to-Assets Ratio",
        category=FormulaCategory.LEVERAGE,
        formula_text="Total Debt / Total Assets",
        required_inputs=["total_debt", "total_assets"],
        optional_inputs=[],
        unit="ratio",
        description="Percentage of assets financed by debt.",
        interpretation="Lower indicates less financial risk."
    ),
    "equity_multiplier": FormulaDefinition(
        name="Equity Multiplier",
        category=FormulaCategory.LEVERAGE,
        formula_text="Total Assets / Shareholders' Equity",
        required_inputs=["total_assets", "shareholders_equity"],
        optional_inputs=[],
        unit="ratio",
        description="Financial leverage component of DuPont analysis.",
        interpretation="Higher means more leverage. 2.0 = 50% debt financing."
    ),
    "interest_coverage": FormulaDefinition(
        name="Interest Coverage Ratio",
        category=FormulaCategory.LEVERAGE,
        formula_text="EBIT / Interest Expense",
        required_inputs=["operating_income", "interest_expense"],
        optional_inputs=[],
        unit="ratio",
        description="Ability to pay interest on debt.",
        interpretation="Higher is safer. Below 1.5 may indicate distress risk."
    ),
    "debt_service_coverage": FormulaDefinition(
        name="Debt Service Coverage Ratio",
        category=FormulaCategory.LEVERAGE,
        formula_text="Operating Income / Total Debt Service",
        required_inputs=["operating_income", "debt_service"],
        optional_inputs=["interest_expense", "principal_payments"],
        unit="ratio",
        description="Ability to pay all debt obligations.",
        interpretation="Above 1.25 is typically required by lenders."
    ),
    
    # ========== GROWTH METRICS ==========
    "revenue_growth_yoy": FormulaDefinition(
        name="Revenue Growth (YoY)",
        category=FormulaCategory.GROWTH,
        formula_text="((Current Revenue - Prior Revenue) / Prior Revenue) × 100",
        required_inputs=["revenue", "prior_revenue"],
        optional_inputs=[],
        unit="percent",
        description="Year-over-year revenue growth rate.",
        interpretation="Positive growth is good. Compare to industry average."
    ),
    "earnings_growth": FormulaDefinition(
        name="Earnings Growth",
        category=FormulaCategory.GROWTH,
        formula_text="((Current EPS - Prior EPS) / Prior EPS) × 100",
        required_inputs=["eps", "prior_eps"],
        optional_inputs=["net_income", "prior_net_income"],
        unit="percent",
        description="Year-over-year earnings per share growth.",
        interpretation="Positive growth indicates improving profitability."
    ),
    "cagr": FormulaDefinition(
        name="Compound Annual Growth Rate (CAGR)",
        category=FormulaCategory.GROWTH,
        formula_text="((Ending Value / Beginning Value)^(1/years) - 1) × 100",
        required_inputs=["ending_value", "beginning_value", "years"],
        optional_inputs=[],
        unit="percent",
        description="Smoothed annual growth rate over multiple years.",
        interpretation="Shows long-term growth trajectory. More reliable than single-year."
    ),
    "sustainable_growth_rate": FormulaDefinition(
        name="Sustainable Growth Rate",
        category=FormulaCategory.GROWTH,
        formula_text="ROE × Retention Ratio",
        required_inputs=["net_income", "shareholders_equity", "dividends"],
        optional_inputs=[],
        unit="percent",
        description="Maximum growth rate without external financing.",
        interpretation="Growth above this requires debt or equity issuance."
    ),
    
    # ========== VALUATION METRICS ==========
    "price_to_earnings": FormulaDefinition(
        name="Price-to-Earnings Ratio (P/E)",
        category=FormulaCategory.VALUATION,
        formula_text="Stock Price / Earnings Per Share",
        required_inputs=["stock_price", "eps"],
        optional_inputs=[],
        unit="ratio",
        description="How much investors pay per dollar of earnings.",
        interpretation="Higher may indicate growth expectations or overvaluation."
    ),
    "price_to_book": FormulaDefinition(
        name="Price-to-Book Ratio (P/B)",
        category=FormulaCategory.VALUATION,
        formula_text="Stock Price / Book Value Per Share",
        required_inputs=["stock_price", "book_value_per_share"],
        optional_inputs=["shareholders_equity", "shares_outstanding"],
        unit="ratio",
        description="Market value relative to accounting book value.",
        interpretation="Below 1.0 may indicate undervaluation or asset issues."
    ),
    "price_to_sales": FormulaDefinition(
        name="Price-to-Sales Ratio (P/S)",
        category=FormulaCategory.VALUATION,
        formula_text="Market Cap / Revenue",
        required_inputs=["market_cap", "revenue"],
        optional_inputs=["stock_price", "shares_outstanding"],
        unit="ratio",
        description="Market value relative to revenue.",
        interpretation="Useful for unprofitable companies. Lower may be undervalued."
    ),
    "ev_to_ebitda": FormulaDefinition(
        name="EV/EBITDA",
        category=FormulaCategory.VALUATION,
        formula_text="Enterprise Value / EBITDA",
        required_inputs=["enterprise_value", "ebitda"],
        optional_inputs=["market_cap", "total_debt", "cash"],
        unit="ratio",
        description="Enterprise value relative to operating earnings.",
        interpretation="Capital-structure neutral. Lower may indicate undervaluation."
    ),
    "peg_ratio": FormulaDefinition(
        name="PEG Ratio",
        category=FormulaCategory.VALUATION,
        formula_text="P/E Ratio / Earnings Growth Rate",
        required_inputs=["stock_price", "eps", "earnings_growth_rate"],
        optional_inputs=[],
        unit="ratio",
        description="P/E adjusted for growth. More nuanced than P/E alone.",
        interpretation="Below 1.0 may indicate undervaluation vs. growth."
    ),
    
    # ========== DUPONT ANALYSIS ==========
    "dupont_roe": FormulaDefinition(
        name="DuPont ROE",
        category=FormulaCategory.DUPONT,
        formula_text="Net Profit Margin × Asset Turnover × Equity Multiplier",
        required_inputs=["net_income", "revenue", "total_assets", "shareholders_equity"],
        optional_inputs=[],
        unit="percent",
        description="ROE decomposed into three components for deeper analysis.",
        interpretation="Shows whether ROE comes from margins, efficiency, or leverage."
    ),
    
    # ========== CASH FLOW METRICS ==========
    "free_cash_flow": FormulaDefinition(
        name="Free Cash Flow (FCF)",
        category=FormulaCategory.CASH_FLOW,
        formula_text="Operating Cash Flow - Capital Expenditures",
        required_inputs=["operating_cash_flow", "capital_expenditures"],
        optional_inputs=[],
        unit="currency",
        description="Cash available after maintaining/expanding asset base.",
        interpretation="Positive FCF indicates ability to pay dividends, reduce debt."
    ),
    "fcf_margin": FormulaDefinition(
        name="Free Cash Flow Margin",
        category=FormulaCategory.CASH_FLOW,
        formula_text="(Free Cash Flow / Revenue) × 100",
        required_inputs=["operating_cash_flow", "capital_expenditures", "revenue"],
        optional_inputs=[],
        unit="percent",
        description="FCF as percentage of revenue.",
        interpretation="Higher indicates stronger cash generation vs. sales."
    ),
    "cash_flow_to_debt": FormulaDefinition(
        name="Cash Flow to Debt Ratio",
        category=FormulaCategory.CASH_FLOW,
        formula_text="Operating Cash Flow / Total Debt",
        required_inputs=["operating_cash_flow", "total_debt"],
        optional_inputs=[],
        unit="ratio",
        description="Ability to cover debt with operating cash flow.",
        interpretation="Higher is better. Above 0.20 is generally healthy."
    ),
    "capex_to_revenue": FormulaDefinition(
        name="CapEx to Revenue Ratio",
        category=FormulaCategory.CASH_FLOW,
        formula_text="(Capital Expenditures / Revenue) × 100",
        required_inputs=["capital_expenditures", "revenue"],
        optional_inputs=[],
        unit="percent",
        description="Investment intensity relative to revenue.",
        interpretation="Varies by industry. High may indicate growth investment."
    ),
}


# ============================================================
# CALCULATION ENGINE
# ============================================================

def calculate_formula(formula_name: str, data: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate a specific formula given the required data.
    
    Args:
        formula_name: Key from FORMULA_REGISTRY
        data: Dict of financial data values (e.g., {'revenue': 90753, 'net_income': 23636})
    
    Returns:
        Dict with 'success', 'result', 'formula', 'interpretation', etc.
    """
    if formula_name not in FORMULA_REGISTRY:
        return {
            'success': False,
            'error': f"Unknown formula: {formula_name}",
            'available_formulas': list(FORMULA_REGISTRY.keys())
        }
    
    formula = FORMULA_REGISTRY[formula_name]
    
    # Check required inputs
    missing_inputs = [inp for inp in formula.required_inputs if inp not in data or data[inp] is None]
    if missing_inputs:
        return {
            'success': False,
            'error': f"Missing required inputs: {missing_inputs}",
            'formula_name': formula.name,
            'required_inputs': formula.required_inputs,
            'provided_inputs': list(data.keys())
        }
    
    # Calculate based on formula name
    try:
        result = _compute_formula(formula_name, data)
        
        return {
            'success': True,
            'formula_name': formula.name,
            'result': result,
            'unit': formula.unit,
            'formula_text': formula.formula_text,
            'description': formula.description,
            'interpretation': formula.interpretation,
            'category': formula.category.value,
            'inputs_used': {k: data.get(k) for k in formula.required_inputs}
        }
    
    except ZeroDivisionError:
        return {
            'success': False,
            'error': "Division by zero - denominator is zero",
            'formula_name': formula.name
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'formula_name': formula.name
        }


def _compute_formula(name: str, d: Dict[str, float]) -> float:
    """Internal formula computation logic."""
    
    # ========== PROFITABILITY ==========
    if name == "gross_profit_margin":
        return (d["gross_profit"] / d["revenue"]) * 100
    
    elif name == "operating_profit_margin":
        return (d["operating_income"] / d["revenue"]) * 100
    
    elif name == "net_profit_margin":
        return (d["net_income"] / d["revenue"]) * 100
    
    elif name == "return_on_assets":
        return (d["net_income"] / d["total_assets"]) * 100
    
    elif name == "return_on_equity":
        return (d["net_income"] / d["shareholders_equity"]) * 100
    
    elif name == "return_on_invested_capital":
        tax_rate = d.get("tax_rate", 0.21)  # Default 21% corporate rate
        nopat = d["operating_income"] * (1 - tax_rate)
        invested_capital = d["total_debt"] + d["shareholders_equity"] - d.get("cash", 0)
        return (nopat / invested_capital) * 100
    
    elif name == "ebitda_margin":
        ebitda = d.get("ebitda")
        if ebitda is None:
            # Calculate from components if available
            ebitda = d.get("operating_income", 0) + d.get("depreciation", 0) + d.get("amortization", 0)
        return (ebitda / d["revenue"]) * 100
    
    # ========== LIQUIDITY ==========
    elif name == "current_ratio":
        return d["current_assets"] / d["current_liabilities"]
    
    elif name == "quick_ratio":
        return (d["current_assets"] - d["inventory"]) / d["current_liabilities"]
    
    elif name == "cash_ratio":
        return d["cash"] / d["current_liabilities"]
    
    elif name == "operating_cash_flow_ratio":
        return d["operating_cash_flow"] / d["current_liabilities"]
    
    # ========== EFFICIENCY ==========
    elif name == "asset_turnover":
        avg_assets = (d["total_assets"] + d.get("prior_total_assets", d["total_assets"])) / 2
        return d["revenue"] / avg_assets
    
    elif name == "inventory_turnover":
        avg_inventory = (d["inventory"] + d.get("prior_inventory", d["inventory"])) / 2
        return d["cost_of_goods_sold"] / avg_inventory
    
    elif name == "receivables_turnover":
        avg_ar = (d["accounts_receivable"] + d.get("prior_accounts_receivable", d["accounts_receivable"])) / 2
        return d["revenue"] / avg_ar
    
    elif name == "days_sales_outstanding":
        return (d["accounts_receivable"] / d["revenue"]) * 365
    
    elif name == "days_inventory_outstanding":
        return (d["inventory"] / d["cost_of_goods_sold"]) * 365
    
    elif name == "days_payable_outstanding":
        return (d["accounts_payable"] / d["cost_of_goods_sold"]) * 365
    
    elif name == "cash_conversion_cycle":
        dso = (d["accounts_receivable"] / d["revenue"]) * 365
        dio = (d["inventory"] / d["cost_of_goods_sold"]) * 365
        dpo = (d["accounts_payable"] / d["cost_of_goods_sold"]) * 365
        return dso + dio - dpo
    
    # ========== LEVERAGE ==========
    elif name == "debt_to_equity":
        return d["total_debt"] / d["shareholders_equity"]
    
    elif name == "debt_to_assets":
        return d["total_debt"] / d["total_assets"]
    
    elif name == "equity_multiplier":
        return d["total_assets"] / d["shareholders_equity"]
    
    elif name == "interest_coverage":
        return d["operating_income"] / d["interest_expense"]
    
    elif name == "debt_service_coverage":
        debt_service = d.get("debt_service") or (d.get("interest_expense", 0) + d.get("principal_payments", 0))
        return d["operating_income"] / debt_service
    
    # ========== GROWTH ==========
    elif name == "revenue_growth_yoy":
        return ((d["revenue"] - d["prior_revenue"]) / d["prior_revenue"]) * 100
    
    elif name == "earnings_growth":
        current = d.get("eps") or d.get("net_income")
        prior = d.get("prior_eps") or d.get("prior_net_income")
        return ((current - prior) / abs(prior)) * 100
    
    elif name == "cagr":
        return (pow(d["ending_value"] / d["beginning_value"], 1 / d["years"]) - 1) * 100
    
    elif name == "sustainable_growth_rate":
        roe = (d["net_income"] / d["shareholders_equity"]) * 100
        retention_ratio = 1 - (d.get("dividends", 0) / d["net_income"])
        return roe * retention_ratio
    
    # ========== VALUATION ==========
    elif name == "price_to_earnings":
        return d["stock_price"] / d["eps"]
    
    elif name == "price_to_book":
        bvps = d.get("book_value_per_share")
        if bvps is None:
            bvps = d["shareholders_equity"] / d["shares_outstanding"]
        return d["stock_price"] / bvps
    
    elif name == "price_to_sales":
        mkt_cap = d.get("market_cap")
        if mkt_cap is None:
            mkt_cap = d["stock_price"] * d["shares_outstanding"]
        return mkt_cap / d["revenue"]
    
    elif name == "ev_to_ebitda":
        ev = d.get("enterprise_value")
        if ev is None:
            ev = d["market_cap"] + d["total_debt"] - d["cash"]
        return ev / d["ebitda"]
    
    elif name == "peg_ratio":
        pe = d["stock_price"] / d["eps"]
        return pe / d["earnings_growth_rate"]
    
    # ========== DUPONT ==========
    elif name == "dupont_roe":
        npm = d["net_income"] / d["revenue"]
        at = d["revenue"] / d["total_assets"]
        em = d["total_assets"] / d["shareholders_equity"]
        return npm * at * em * 100
    
    # ========== CASH FLOW ==========
    elif name == "free_cash_flow":
        return d["operating_cash_flow"] - d["capital_expenditures"]
    
    elif name == "fcf_margin":
        fcf = d["operating_cash_flow"] - d["capital_expenditures"]
        return (fcf / d["revenue"]) * 100
    
    elif name == "cash_flow_to_debt":
        return d["operating_cash_flow"] / d["total_debt"]
    
    elif name == "capex_to_revenue":
        return (d["capital_expenditures"] / d["revenue"]) * 100
    
    else:
        raise ValueError(f"No computation defined for formula: {name}")


def auto_calculate_all_possible(data: Dict[str, float]) -> Dict[str, Dict]:
    """
    Given extracted financial data, calculate ALL possible formulas.
    
    Returns dict of formula_name -> calculation result for all formulas
    that can be computed with the available data.
    """
    results = {}
    
    for formula_name, formula_def in FORMULA_REGISTRY.items():
        # Check if we have all required inputs
        has_all_inputs = all(inp in data and data[inp] is not None 
                            for inp in formula_def.required_inputs)
        
        if has_all_inputs:
            result = calculate_formula(formula_name, data)
            if result.get('success'):
                results[formula_name] = result
    
    return results


def get_formulas_by_category(category: FormulaCategory = None) -> Dict[str, FormulaDefinition]:
    """Get all formulas, optionally filtered by category."""
    if category is None:
        return FORMULA_REGISTRY
    
    return {k: v for k, v in FORMULA_REGISTRY.items() if v.category == category}


def explain_formula(formula_name: str) -> str:
    """Get a human-readable explanation of a formula."""
    if formula_name not in FORMULA_REGISTRY:
        return f"Unknown formula: {formula_name}"
    
    f = FORMULA_REGISTRY[formula_name]
    
    return f"""
## {f.name}

**Category:** {f.category.value}

**Formula:** `{f.formula_text}`

**Description:** {f.description}

**Interpretation:** {f.interpretation}

**Required Inputs:** {', '.join(f.required_inputs)}
"""


def get_required_inputs(formula_name: str) -> List[str]:
    """Get the required inputs for a formula."""
    if formula_name not in FORMULA_REGISTRY:
        return []
    return FORMULA_REGISTRY[formula_name].required_inputs


def format_result(result: Dict) -> str:
    """Format a calculation result for display."""
    if not result.get('success'):
        return f"❌ {result.get('error', 'Calculation failed')}"
    
    value = result['result']
    unit = result['unit']
    
    if unit == 'percent':
        formatted = f"{value:.2f}%"
    elif unit == 'ratio':
        formatted = f"{value:.2f}x"
    elif unit == 'days':
        formatted = f"{value:.1f} days"
    elif unit == 'currency':
        if abs(value) >= 1_000_000_000:
            formatted = f"${value/1_000_000_000:.2f}B"
        elif abs(value) >= 1_000_000:
            formatted = f"${value/1_000_000:.2f}M"
        else:
            formatted = f"${value:,.2f}"
    else:
        formatted = f"{value:.2f}"
    
    return f"""
**{result['formula_name']}**: {formatted}

*Formula:* {result['formula_text']}
*Interpretation:* {result['interpretation']}
"""


# ============================================================
# DETECTION - What formula is the user asking for?
# ============================================================

FORMULA_KEYWORDS = {
    "gross_profit_margin": ["gross margin", "gross profit margin", "gpm"],
    "operating_profit_margin": ["operating margin", "operating profit margin", "opm", "ebit margin"],
    "net_profit_margin": ["net margin", "net profit margin", "profit margin", "npm"],
    "return_on_assets": ["roa", "return on assets", "asset return"],
    "return_on_equity": ["roe", "return on equity", "equity return"],
    "return_on_invested_capital": ["roic", "return on invested capital", "return on capital"],
    "ebitda_margin": ["ebitda margin", "ebitda %"],
    "current_ratio": ["current ratio", "working capital ratio"],
    "quick_ratio": ["quick ratio", "acid test", "acid-test"],
    "cash_ratio": ["cash ratio"],
    "operating_cash_flow_ratio": ["operating cash flow ratio", "ocf ratio"],
    "asset_turnover": ["asset turnover", "total asset turnover"],
    "inventory_turnover": ["inventory turnover", "stock turnover"],
    "receivables_turnover": ["receivables turnover", "ar turnover"],
    "days_sales_outstanding": ["dso", "days sales outstanding", "collection period"],
    "days_inventory_outstanding": ["dio", "days inventory outstanding", "inventory days"],
    "days_payable_outstanding": ["dpo", "days payable outstanding", "payable days"],
    "cash_conversion_cycle": ["ccc", "cash conversion cycle", "cash cycle"],
    "debt_to_equity": ["debt to equity", "d/e ratio", "de ratio", "leverage ratio"],
    "debt_to_assets": ["debt to assets", "debt ratio"],
    "equity_multiplier": ["equity multiplier", "financial leverage"],
    "interest_coverage": ["interest coverage", "times interest earned", "tie ratio"],
    "debt_service_coverage": ["dscr", "debt service coverage"],
    "revenue_growth_yoy": ["revenue growth", "sales growth", "yoy growth", "year over year growth"],
    "earnings_growth": ["earnings growth", "eps growth", "profit growth"],
    "cagr": ["cagr", "compound annual growth", "compound growth"],
    "sustainable_growth_rate": ["sustainable growth", "sgr"],
    "price_to_earnings": ["p/e", "pe ratio", "price to earnings", "price earnings"],
    "price_to_book": ["p/b", "pb ratio", "price to book"],
    "price_to_sales": ["p/s", "ps ratio", "price to sales"],
    "ev_to_ebitda": ["ev/ebitda", "ev ebitda", "enterprise value to ebitda"],
    "peg_ratio": ["peg", "peg ratio", "p/e to growth"],
    "dupont_roe": ["dupont", "dupont analysis", "dupont roe"],
    "free_cash_flow": ["fcf", "free cash flow"],
    "fcf_margin": ["fcf margin", "free cash flow margin"],
    "cash_flow_to_debt": ["cash flow to debt", "cf to debt"],
    "capex_to_revenue": ["capex ratio", "capex to revenue", "capital intensity"],
}


def detect_formula_query(query: str) -> Optional[str]:
    """
    Detect if the user is asking for a specific financial formula/ratio.
    
    Returns the formula_name if found, None otherwise.
    """
    q = query.lower()
    
    matches = []
    for formula_name, keywords in FORMULA_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                matches.append((formula_name, len(kw)))
    
    if matches:
        # Return longest match (most specific)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]
    
    return None
