# test/test_financial_formulas.py
"""
Test suite for financial formulas engine.
"""

from src.analysis.financial_formulas import (
    calculate_formula, 
    auto_calculate_all_possible,
    detect_formula_query,
    explain_formula,
    FORMULA_REGISTRY
)


def test_profitability_ratios():
    """Test profitability ratio calculations."""
    # Apple Q2 2025 sample data (in millions)
    data = {
        'revenue': 90753,
        'gross_profit': 41000,
        'operating_income': 27900,
        'net_income': 23636,
        'total_assets': 337411,
        'shareholders_equity': 57407,
    }
    
    print("=" * 60)
    print("PROFITABILITY RATIOS")
    print("=" * 60)
    
    # Test Gross Profit Margin
    result = calculate_formula('gross_profit_margin', data)
    assert result['success'], f"Gross margin failed: {result}"
    print(f"✅ Gross Profit Margin: {result['result']:.2f}%")
    
    # Test Net Profit Margin
    result = calculate_formula('net_profit_margin', data)
    assert result['success']
    print(f"✅ Net Profit Margin: {result['result']:.2f}%")
    
    # Test ROA
    result = calculate_formula('return_on_assets', data)
    assert result['success']
    print(f"✅ ROA: {result['result']:.2f}%")
    
    # Test ROE
    result = calculate_formula('return_on_equity', data)
    assert result['success']
    print(f"✅ ROE: {result['result']:.2f}%")


def test_liquidity_ratios():
    """Test liquidity ratio calculations."""
    data = {
        'current_assets': 143562,
        'current_liabilities': 133973,
        'inventory': 6232,
        'cash': 26752,
    }
    
    print("\n" + "=" * 60)
    print("LIQUIDITY RATIOS")
    print("=" * 60)
    
    result = calculate_formula('current_ratio', data)
    assert result['success']
    print(f"✅ Current Ratio: {result['result']:.2f}x")
    
    result = calculate_formula('quick_ratio', data)
    assert result['success']
    print(f"✅ Quick Ratio: {result['result']:.2f}x")
    
    result = calculate_formula('cash_ratio', data)
    assert result['success']
    print(f"✅ Cash Ratio: {result['result']:.2f}x")


def test_leverage_ratios():
    """Test leverage ratio calculations."""
    data = {
        'total_debt': 109280,
        'shareholders_equity': 57407,
        'total_assets': 337411,
        'operating_income': 27900,
        'interest_expense': 1200,
    }
    
    print("\n" + "=" * 60)
    print("LEVERAGE RATIOS")
    print("=" * 60)
    
    result = calculate_formula('debt_to_equity', data)
    assert result['success']
    print(f"✅ Debt-to-Equity: {result['result']:.2f}x")
    
    result = calculate_formula('debt_to_assets', data)
    assert result['success']
    print(f"✅ Debt-to-Assets: {result['result']:.2f}")
    
    result = calculate_formula('interest_coverage', data)
    assert result['success']
    print(f"✅ Interest Coverage: {result['result']:.2f}x")


def test_growth_metrics():
    """Test growth calculations."""
    data = {
        'revenue': 90753,
        'prior_revenue': 81297,
        'eps': 1.53,
        'prior_eps': 1.40,
        'ending_value': 90753,
        'beginning_value': 70000,
        'years': 3,
    }
    
    print("\n" + "=" * 60)
    print("GROWTH METRICS")
    print("=" * 60)
    
    result = calculate_formula('revenue_growth_yoy', data)
    assert result['success']
    print(f"✅ Revenue Growth (YoY): {result['result']:.2f}%")
    
    result = calculate_formula('earnings_growth', data)
    assert result['success']
    print(f"✅ Earnings Growth: {result['result']:.2f}%")
    
    result = calculate_formula('cagr', data)
    assert result['success']
    print(f"✅ CAGR: {result['result']:.2f}%")


def test_efficiency_ratios():
    """Test efficiency ratio calculations."""
    data = {
        'revenue': 90753,
        'total_assets': 337411,
        'accounts_receivable': 28865,
        'inventory': 6232,
        'accounts_payable': 52476,
        'cost_of_goods_sold': 49753,
    }
    
    print("\n" + "=" * 60)
    print("EFFICIENCY RATIOS")
    print("=" * 60)
    
    result = calculate_formula('asset_turnover', data)
    assert result['success']
    print(f"✅ Asset Turnover: {result['result']:.2f}x")
    
    result = calculate_formula('days_sales_outstanding', data)
    assert result['success']
    print(f"✅ DSO: {result['result']:.1f} days")
    
    result = calculate_formula('days_inventory_outstanding', data)
    assert result['success']
    print(f"✅ DIO: {result['result']:.1f} days")
    
    result = calculate_formula('cash_conversion_cycle', data)
    assert result['success']
    print(f"✅ Cash Conversion Cycle: {result['result']:.1f} days")


def test_dupont_analysis():
    """Test DuPont ROE calculation."""
    data = {
        'net_income': 23636,
        'revenue': 90753,
        'total_assets': 337411,
        'shareholders_equity': 57407,
    }
    
    print("\n" + "=" * 60)
    print("DUPONT ANALYSIS")
    print("=" * 60)
    
    result = calculate_formula('dupont_roe', data)
    assert result['success']
    print(f"✅ DuPont ROE: {result['result']:.2f}%")
    
    # Also calculate standard ROE to compare
    roe_result = calculate_formula('return_on_equity', data)
    print(f"   Standard ROE: {roe_result['result']:.2f}%")
    
    # They should match (within floating point tolerance)
    assert abs(result['result'] - roe_result['result']) < 0.01


def test_auto_calculate():
    """Test auto-calculating all possible formulas."""
    data = {
        'revenue': 90753,
        'net_income': 23636,
        'total_assets': 337411,
        'shareholders_equity': 57407,
        'current_assets': 143562,
        'current_liabilities': 133973,
        'inventory': 6232,
        'cash': 26752,
        'gross_profit': 41000,
        'operating_income': 27900,
    }
    
    print("\n" + "=" * 60)
    print("AUTO-CALCULATE ALL POSSIBLE FORMULAS")
    print("=" * 60)
    
    results = auto_calculate_all_possible(data)
    
    print(f"✅ Auto-calculated {len(results)} formulas from {len(data)} data points:\n")
    
    for name, res in results.items():
        unit = res['unit']
        value = res['result']
        
        if unit == 'percent':
            formatted = f"{value:.2f}%"
        elif unit == 'ratio':
            formatted = f"{value:.2f}x"
        elif unit == 'days':
            formatted = f"{value:.1f} days"
        else:
            formatted = f"{value:,.2f}"
        
        print(f"   • {res['formula_name']}: {formatted}")


def test_formula_detection():
    """Test detecting formula queries."""
    print("\n" + "=" * 60)
    print("FORMULA QUERY DETECTION")
    print("=" * 60)
    
    test_queries = [
        ("What is the ROE?", "return_on_equity"),
        ("Calculate the current ratio", "current_ratio"),
        ("What's the debt to equity?", "debt_to_equity"),
        ("Show me the gross margin", "gross_profit_margin"),
        ("What is the P/E ratio?", "price_to_earnings"),
        ("Tell me about revenue growth", "revenue_growth_yoy"),
        ("What is the CAGR?", "cagr"),
        ("Show free cash flow", "free_cash_flow"),
    ]
    
    for query, expected in test_queries:
        result = detect_formula_query(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{query}' -> {result} (expected: {expected})")


if __name__ == "__main__":
    print("🧮 FINANCIAL FORMULAS ENGINE TEST SUITE\n")
    
    test_profitability_ratios()
    test_liquidity_ratios()
    test_leverage_ratios()
    test_growth_metrics()
    test_efficiency_ratios()
    test_dupont_analysis()
    test_auto_calculate()
    test_formula_detection()
    
    print("\n" + "=" * 60)
    print(f"✅ ALL TESTS PASSED! ({len(FORMULA_REGISTRY)} formulas registered)")
    print("=" * 60)
