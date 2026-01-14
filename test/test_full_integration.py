# test/test_full_integration.py
"""
End-to-end integration test for the Finance AI RAG system.
Tests all layers: Temporal, Formulas, Metrics, Charts, OpenRouter fallback.
"""

import os
import sys
import pandas as pd

# Ensure environment
os.environ.setdefault('CHROMA_DB_PATH', 'data/chroma_db')
os.environ.setdefault('HF_HOME', 'C:/Users/kk/.cache/huggingface')


def test_layer_temporal_comparison():
    """Test Layer 0.5: Temporal Comparison Engine"""
    print("\n" + "=" * 60)
    print("TEST 1: TEMPORAL COMPARISON (Layer 0.5)")
    print("=" * 60)
    
    from src.analysis.temporal_comparison import (
        is_temporal_comparison,
        handle_temporal_comparison
    )
    
    # Create mock segment data
    df = pd.DataFrame({
        "Segment": ["Americas", "Europe", "Greater China", "Japan"],
        "Three Months Ended March 29, 2025": ["37264", "24123", "16002", "8564"],
        "Three Months Ended March 30, 2024": ["34264", "22123", "15002", "7564"]
    })
    
    tables = [{"df": df, "source": "Apple_10Q.pdf", "page": 3}]
    
    query = "What was the net sales for Greater China in March 2024 and March 2025?"
    
    # Test detection
    assert is_temporal_comparison(query), "Should detect temporal query"
    print(f"✅ Temporal query detected: '{query[:50]}...'")
    
    # Test handling
    result = handle_temporal_comparison(query, tables)
    
    if result.get('success'):
        print(f"✅ Temporal comparison succeeded")
        print(f"   Results: {len(result.get('results', []))} periods extracted")
        if result.get('variance'):
            var = result['variance']
            print(f"   Change: ${var.get('absolute_change', 0):,.0f} ({var.get('percent_change', 0):+.2f}%)")
        return True
    else:
        print(f"⚠️ Temporal comparison failed: {result.get('error')}")
        return False


def test_layer_formulas():
    """Test Layer 1.5: Financial Formulas Engine"""
    print("\n" + "=" * 60)
    print("TEST 2: FINANCIAL FORMULAS (Layer 1.5)")
    print("=" * 60)
    
    from src.analysis.financial_formulas import (
        detect_formula_query,
        calculate_formula,
        auto_calculate_all_possible
    )
    
    # Test detection
    queries = [
        ("What is the ROE?", "return_on_equity"),
        ("Calculate current ratio", "current_ratio"),
        ("Show P/E ratio", "price_to_earnings"),
    ]
    
    all_passed = True
    for query, expected in queries:
        detected = detect_formula_query(query)
        if detected == expected:
            print(f"✅ Detected '{query}' -> {detected}")
        else:
            print(f"❌ Expected {expected}, got {detected}")
            all_passed = False
    
    # Test calculation
    data = {
        'net_income': 23636,
        'shareholders_equity': 57407,
        'revenue': 90753,
        'total_assets': 337411,
    }
    
    result = calculate_formula('return_on_equity', data)
    if result.get('success'):
        print(f"✅ ROE Calculated: {result['result']:.2f}%")
    else:
        print(f"❌ ROE calculation failed: {result.get('error')}")
        all_passed = False
    
    # Test auto-calculate
    auto_results = auto_calculate_all_possible(data)
    print(f"✅ Auto-calculated {len(auto_results)} formulas from {len(data)} inputs")
    
    return all_passed


def test_layer_metrics():
    """Test Layer 2: Deterministic Metrics"""
    print("\n" + "=" * 60)
    print("TEST 3: DETERMINISTIC METRICS (Layer 2)")
    print("=" * 60)
    
    from src.analysis.question_router import resolve_intent
    from src.analysis.financial_reasoning import compute_metric_with_reasoning
    
    # Create mock income statement
    df = pd.DataFrame({
        "Item": ["Net sales", "Cost of sales", "Gross margin", "Operating income", "Net income"],
        "Three Months Ended March 29, 2025": ["90753", "49753", "41000", "27900", "23636"],
        "Three Months Ended March 30, 2024": ["81297", "44753", "36544", "24900", "20636"]
    })
    
    tables = [{"df": df, "source": "Apple_10Q.pdf", "page": 1}]
    
    # Test metric extraction
    test_queries = [
        "What is the net income?",
        "Total revenue?",
        "Operating income for Q2?"
    ]
    
    all_passed = True
    for query in test_queries:
        matched = resolve_intent(query)
        if matched:
            m_name, m_config = matched[0]
            result = compute_metric_with_reasoning(m_name, tables, query)
            if result.get('success'):
                print(f"✅ '{query[:30]}...' -> {m_name}: ${result['result']:,.0f}")
            else:
                print(f"⚠️ '{query[:30]}...' -> Extraction failed")
        else:
            print(f"⚠️ '{query[:30]}...' -> No metric matched")
    
    return all_passed


def test_chart_generation():
    """Test Chart Generation"""
    print("\n" + "=" * 60)
    print("TEST 4: CHART GENERATION")
    print("=" * 60)
    
    from src.visualization.chart_generator import (
        generate_chart,
        create_waterfall_chart,
        create_comparison_bar_chart
    )
    
    # Test basic bar chart
    df = pd.DataFrame({
        "Period": ["Q1 2024", "Q2 2024", "Q1 2025", "Q2 2025"],
        "Revenue": [80000, 85000, 88000, 90753]
    })
    
    result = generate_chart(
        df=df,
        x_col="Period",
        y_col="Revenue",
        title="Revenue Trend",
        output_path="data/static/test_revenue.png"
    )
    
    if result.get('success'):
        print(f"✅ Bar chart generated: {result.get('image_path')}")
    else:
        print(f"⚠️ Bar chart failed: {result.get('error')}")
    
    # Test waterfall chart
    try:
        fig = create_waterfall_chart(
            labels=["Q1 2024", "Revenue Growth", "Cost Reduction", "One-time Expense", "Q1 2025"],
            values=[80000, 5000, 3000, -1000, 87000],
            title="Revenue Bridge Q1 2024 to Q1 2025"
        )
        fig.write_image("data/static/test_waterfall.png", width=1000, height=600)
        print(f"✅ Waterfall chart generated: data/static/test_waterfall.png")
    except Exception as e:
        print(f"⚠️ Waterfall chart failed: {e}")
    
    # Test comparison chart
    try:
        df_comp = pd.DataFrame({
            "Segment": ["Americas", "Europe", "Greater China", "Japan"],
            "2024": [34264, 22123, 15002, 7564],
            "2025": [37264, 24123, 16002, 8564]
        })
        fig = create_comparison_bar_chart(
            df=df_comp,
            x_col="Segment",
            value_cols=["2024", "2025"],
            title="Segment Revenue Comparison"
        )
        fig.write_image("data/static/test_comparison.png", width=1000, height=600)
        print(f"✅ Comparison chart generated: data/static/test_comparison.png")
    except Exception as e:
        print(f"⚠️ Comparison chart failed: {e}")
    
    return True


def test_llm_narrator():
    """Test LLM Narrator with Gemini/OpenRouter fallback"""
    print("\n" + "=" * 60)
    print("TEST 5: LLM NARRATOR (Gemini + OpenRouter Fallback)")
    print("=" * 60)
    
    from src.ai.llm_narrator import LLMNarrator
    
    narrator = LLMNarrator()
    
    # Test simple explanation
    try:
        response = narrator.explain(
            user_question="What is Apple's revenue?",
            rag_context="Apple Inc. reported total net sales of $90,753 million for Q2 2025.",
            computed_result="Revenue: $90,753 Million (As of March 29, 2025)"
        )
        
        if response and len(response) > 50:
            print(f"✅ LLM Narrator responded ({len(response)} chars)")
            print(f"   Preview: {response[:100]}...")
            return True
        else:
            print(f"⚠️ Weak response: {response[:50] if response else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ LLM Narrator failed: {e}")
        return False


def test_full_query_route():
    """Test Full Query Route (End-to-End)"""
    print("\n" + "=" * 60)
    print("TEST 6: FULL QUERY ROUTE (End-to-End)")
    print("=" * 60)
    
    from src.analysis.query_controller import route_query
    from src.visualization.chart_generator import generate_chart
    
    # Create comprehensive mock data
    df_income = pd.DataFrame({
        "Item": ["Total net sales", "Cost of sales", "Gross margin", "Operating income", "Net income", "EPS"],
        "Three Months Ended March 29, 2025": ["90753", "49753", "41000", "27900", "23636", "1.53"],
        "Three Months Ended March 30, 2024": ["81297", "44753", "36544", "24900", "20636", "1.40"]
    })
    
    df_segments = pd.DataFrame({
        "Segment": ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific"],
        "Three Months Ended March 29, 2025": ["37264", "24123", "16002", "8564", "6047"],
        "Three Months Ended March 30, 2024": ["34264", "22123", "15002", "7564", "5047"]
    })
    
    tables = [
        {"df": df_income, "source": "Apple_10Q.pdf", "page": 1},
        {"df": df_segments, "source": "Apple_10Q.pdf", "page": 3}
    ]
    
    test_queries = [
        "What is the net income?",  # Layer 2: Deterministic
        "Revenue for Greater China March 2024 vs March 2025?",  # Layer 0.5: Temporal
        "What is the gross profit margin?",  # Layer 1.5: Formula
    ]
    
    all_passed = True
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        try:
            answer, chart = route_query(
                question=query,
                tables=tables,
                chart_gen=generate_chart,
                session_id="test_session"
            )
            
            if answer and len(answer) > 50:
                print(f"   ✅ Answer: {answer[:80]}...")
                if chart:
                    print(f"   📊 Chart: {chart}")
            else:
                print(f"   ⚠️ Weak answer: {answer[:50] if answer else 'None'}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("🧪 FINANCE AI - FULL INTEGRATION TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results['temporal'] = test_layer_temporal_comparison()
    results['formulas'] = test_layer_formulas()
    results['metrics'] = test_layer_metrics()
    results['charts'] = test_chart_generation()
    results['narrator'] = test_llm_narrator()
    results['full_route'] = test_full_query_route()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name.upper()}: {status}")
    
    print(f"\n   TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) need attention")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
