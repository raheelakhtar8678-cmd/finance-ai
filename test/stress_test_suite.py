# test/stress_test_suite.py
"""
Comprehensive Pre-Release Stress Test Suite

Tests all major components:
1. Chart Generation (5 scenarios)
2. Complex Query Accuracy (4 cross-checks)  
3. Edge Cases
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

import os
import pandas as pd
from pathlib import Path

# ==========================================
# TEST CONFIGURATION
# ==========================================

PDF_PATH = r"e:\finance-ai\data\uploads\119a8e66-0803-40db-9ff1-614d46365b5f_618374cc-0b7e-4007-8f49-da55758e5811.pdf"
CHART_OUTPUT_DIR = Path("data/static")
CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_VALUES = {
    "greater_china_oi_2025": 6_626_000_000,  # $6.626B
    "greater_china_oi_2024": 6_700_000_000,  # $6.700B
    "greater_china_ns_2025": 16_002_000_000, # $16.002B
    "total_revenue_6mo_2025": 195_400_000_000, # ~$195.4B 
    "eps_diluted": 1.53,
}

# ==========================================
# TEST 1: CHART GENERATION
# ==========================================

def test_chart_generation():
    """Test that charts are generated correctly."""
    print("\n" + "="*60)
    print("TEST 1: CHART GENERATION")
    print("="*60)
    
    from src.visualization.chart_generator import (
        generate_chart,
        create_bar_chart,
        create_comparison_bar_chart,
        create_pie_chart,
        create_waterfall_chart
    )
    
    results = []
    
    # Test 1.1: Simple Bar Chart
    print("\n📊 Test 1.1: Simple Bar Chart")
    try:
        df = pd.DataFrame({
            "Metric": ["Revenue", "Operating Income", "Net Income"],
            "Value": [90.75, 27.9, 24.78]
        })
        result = generate_chart(df, "Metric", "Value", "Q2 2025 Key Metrics", 
                               output_path="data/static/test_bar.png")
        
        chart_path = result.get("path") or "data/static/test_bar.png"
        if os.path.exists(chart_path):
            print(f"   ✅ Bar chart saved: {chart_path}")
            results.append(("Bar Chart", True))
        else:
            print(f"   ❌ Bar chart NOT saved at {chart_path}")
            results.append(("Bar Chart", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Bar Chart", False))
    
    # Test 1.2: Comparison Bar Chart
    print("\n📊 Test 1.2: Comparison Bar Chart")
    try:
        df = pd.DataFrame({
            "Segment": ["Americas", "Europe", "Greater China", "Japan"],
            "2024": [37.5, 24.0, 16.4, 6.3],
            "2025": [38.6, 25.0, 16.0, 7.3]
        })
        fig = create_comparison_bar_chart(df, "Segment", ["2024", "2025"], "Revenue by Segment")
        fig.write_image("data/static/test_comparison.png")
        
        if os.path.exists("data/static/test_comparison.png"):
            print(f"   ✅ Comparison chart saved")
            results.append(("Comparison Chart", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Comparison Chart", False))
    
    # Test 1.3: Pie Chart
    print("\n📊 Test 1.3: Pie Chart")
    try:
        df = pd.DataFrame({
            "Product": ["iPhone", "Mac", "iPad", "Wearables", "Services"],
            "Revenue": [46.8, 8.0, 6.4, 9.6, 26.6]
        })
        fig = create_pie_chart(df, "Product", "Revenue", "Product Revenue Mix")
        fig.write_image("data/static/test_pie.png")
        
        if os.path.exists("data/static/test_pie.png"):
            print(f"   ✅ Pie chart saved")
            results.append(("Pie Chart", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Pie Chart", False))
    
    # Test 1.4: Waterfall Chart
    print("\n📊 Test 1.4: Waterfall Chart")
    try:
        labels = ["Q2 2024 OI", "Revenue Growth", "Cost Savings", "FX Impact", "Q2 2025 OI"]
        values = [6700, -50, +30, -54, 6626]
        fig = create_waterfall_chart(labels, values, "Operating Income Bridge")
        fig.write_image("data/static/test_waterfall.png")
        
        if os.path.exists("data/static/test_waterfall.png"):
            print(f"   ✅ Waterfall chart saved")
            results.append(("Waterfall Chart", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Waterfall Chart", False))
    
    return results


# ==========================================
# TEST 2: INSTRUCTION PARSER INTEGRATION
# ==========================================

def test_instruction_parser_integration():
    """Test that instruction parser correctly enhances queries."""
    print("\n" + "="*60)
    print("TEST 2: INSTRUCTED RETRIEVER INTEGRATION")
    print("="*60)
    
    from src.analysis.instruction_parser import parse_instructions, build_chroma_where_filter
    from src.analysis.query_rewriter import rewrite_query_with_instructions
    
    test_cases = [
        {
            "query": "What was Greater China operating income for Q2 2025?",
            "expected_period": "Q2 2025",
            "expected_stmt": "Income Statement",
            "expected_segment": "Greater China"
        },
        {
            "query": "Show me cash flow from operations for the six months ended March 2025",
            "expected_period": "March 2025",
            "expected_stmt": "Cash Flow Statement",
            "expected_segment": None
        },
        {
            "query": "Total assets on the balance sheet",
            "expected_period": None,
            "expected_stmt": "Balance Sheet",
            "expected_segment": None
        }
    ]
    
    results = []
    for tc in test_cases:
        print(f"\n🔍 Query: {tc['query'][:50]}...")
        inst = parse_instructions(tc["query"])
        
        period_ok = (inst.get("period_filter") == tc["expected_period"]) or \
                   (tc["expected_period"] and inst.get("period_filter") and tc["expected_period"] in inst.get("period_filter"))
        stmt_ok = inst.get("stmt_type_filter") == tc["expected_stmt"]
        seg_ok = (inst.get("segment_filter") == tc["expected_segment"]) or \
                (tc["expected_segment"] and inst.get("segment_filter") and tc["expected_segment"].lower() in str(inst.get("segment_filter")).lower())
        
        print(f"   Period: {'✅' if period_ok else '❌'} {inst.get('period_filter')} (expected: {tc['expected_period']})")
        print(f"   Statement: {'✅' if stmt_ok else '❌'} {inst.get('stmt_type_filter')} (expected: {tc['expected_stmt']})")
        print(f"   Segment: {'✅' if seg_ok else '❌'} {inst.get('segment_filter')} (expected: {tc['expected_segment']})")
        
        results.append((tc["query"][:30], period_ok and stmt_ok and seg_ok))
        
        # Test filter building
        where_filter = build_chroma_where_filter(inst, source_filter=["test.pdf"])
        if where_filter:
            print(f"   ✅ ChromaDB filter: {where_filter}")
        
        # Test query rewriting
        enhanced = rewrite_query_with_instructions(tc["query"], inst)
        if len(enhanced) > len(tc["query"]):
            print(f"   ✅ Query enhanced (+{len(enhanced) - len(tc['query'])} chars)")
    
    return results


# ==========================================
# TEST 3: PRIOR PERIOD EXTRACTION
# ==========================================

def test_prior_period_extraction():
    """Test that prior period values are correctly extracted."""
    print("\n" + "="*60)
    print("TEST 3: PRIOR PERIOD EXTRACTION (PyMuPDF)")
    print("="*60)
    
    if not os.path.exists(PDF_PATH):
        print(f"   ⚠️ Skipping: PDF not found at {PDF_PATH}")
        return [("Prior Period", False)]
    
    from src.ingestion.pymupdf_extractor import extract_segment_values_direct
    
    result = extract_segment_values_direct(PDF_PATH, "Greater China")
    
    results = []
    
    # Check current values
    oi_current = result.get("operating_income")
    oi_prior = result.get("operating_income_prior")
    ns_current = result.get("net_sales")
    ns_prior = result.get("net_sales_prior")
    
    print(f"\n📊 Greater China Results:")
    print(f"   Operating Income (Current): ${oi_current:,.0f}" if oi_current else "   ❌ OI Current: N/A")
    print(f"   Operating Income (Prior):   ${oi_prior:,.0f}" if oi_prior else "   ❌ OI Prior: N/A")
    print(f"   Net Sales (Current):        ${ns_current:,.0f}" if ns_current else "   ❌ NS Current: N/A")
    print(f"   Net Sales (Prior):          ${ns_prior:,.0f}" if ns_prior else "   ❌ NS Prior: N/A")
    
    # Verify values
    oi_current_ok = oi_current and abs(oi_current - EXPECTED_VALUES["greater_china_oi_2025"]) < 100_000_000
    oi_prior_ok = oi_prior and abs(oi_prior - EXPECTED_VALUES["greater_china_oi_2024"]) < 100_000_000
    
    if oi_current_ok:
        print(f"   ✅ OI Current matches expected ($6.626B)")
        results.append(("OI Current", True))
    else:
        print(f"   ❌ OI Current mismatch")
        results.append(("OI Current", False))
    
    if oi_prior_ok:
        print(f"   ✅ OI Prior matches expected ($6.700B)")
        results.append(("OI Prior", True))
    else:
        print(f"   ❌ OI Prior mismatch (expected $6.700B)")
        results.append(("OI Prior", False))
    
    # Calculate YoY change
    if oi_current and oi_prior:
        change = (oi_current - oi_prior) / oi_prior * 100
        print(f"\n📉 YoY Change: {change:+.1f}% (expected: -1.1%)")
        change_ok = abs(change - (-1.1)) < 0.5
        results.append(("YoY Change", change_ok))
    
    return results


# ==========================================
# TEST 4: EDGE CASES
# ==========================================

def test_edge_cases():
    """Test edge case handling."""
    print("\n" + "="*60)
    print("TEST 4: EDGE CASES")
    print("="*60)
    
    from src.analysis.instruction_parser import parse_instructions
    
    edge_cases = [
        ("What is the profit margin?", "ratio"),
        ("Show me negative cash flow items", "negative"),
        ("Compare iPhone vs Mac revenue", "multi-segment"),
        ("Q1 Q2 Q3 Q4 revenue trend", "multi-period"),
    ]
    
    results = []
    for query, case_type in edge_cases:
        print(f"\n🔧 [{case_type}] {query}")
        try:
            inst = parse_instructions(query)
            print(f"   ✅ Parsed successfully: {inst.get('priority', 'core')}")
            results.append((case_type, True))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((case_type, False))
    
    return results


# ==========================================
# MAIN
# ==========================================

def run_stress_tests():
    """Run all stress tests."""
    print("\n" + "="*70)
    print("🚗 FINANCE-AI PRE-RELEASE STRESS TEST SUITE")
    print("="*70)
    
    all_results = []
    
    # Run all tests
    all_results.extend(test_chart_generation())
    all_results.extend(test_instruction_parser_integration())
    all_results.extend(test_prior_period_extraction())
    all_results.extend(test_edge_cases())
    
    # Summary
    print("\n" + "="*70)
    print("📋 STRESS TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, ok in all_results if ok)
    total = len(all_results)
    
    for name, ok in all_results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {status} | {name}")
    
    print(f"\n🏁 TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - READY FOR RELEASE!")
    else:
        print(f"\n⚠️ {total - passed} tests failed - review required")
    
    return passed == total


if __name__ == "__main__":
    success = run_stress_tests()
    exit(0 if success else 1)
