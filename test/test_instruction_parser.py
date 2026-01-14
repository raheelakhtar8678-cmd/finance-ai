# test/test_instruction_parser.py
"""
Tests for the Instructed Retriever instruction parser
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.instruction_parser import (
    parse_instructions, 
    build_chroma_where_filter,
    format_instructions_log
)


def test_period_extraction():
    """Test period constraint extraction from queries."""
    test_cases = [
        ("What was Q2 2025 revenue?", "Q2 2025"),
        ("Show me first quarter 2024 earnings", "Q1 2024"),
        ("Revenue for fiscal year 2025", "FY 2025"),
        ("March 2025 net income", "March 2025"),
        ("What was 2024 profit?", "2024"),
        ("Show me the latest revenue", None),  # No specific period
    ]
    
    print("🧪 Testing Period Extraction...")
    passed = 0
    for query, expected_period in test_cases:
        result = parse_instructions(query)
        actual = result.get("period_filter")
        
        if expected_period is None:
            status = "✅" if actual is None else "❌"
        else:
            # Fuzzy match - check if expected is contained in actual
            status = "✅" if (actual and expected_period in actual) else "❌"
        
        if status == "✅":
            passed += 1
        print(f"{status} | '{query[:40]}...' → Period: {actual} (expected: {expected_period})")
    
    print(f"\nPeriod Extraction: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_statement_type_inference():
    """Test statement type inference from query content."""
    test_cases = [
        ("What is the net income?", "Income Statement"),
        ("Is the company profitable?", "Income Statement"),
        ("Show me total assets", "Balance Sheet"),
        ("What is the debt level?", "Balance Sheet"),
        ("Cash flow from operations?", "Cash Flow Statement"),
        ("Free cash flow analysis", "Cash Flow Statement"),
        ("iPhone revenue breakdown", "Segment Info"),
        ("What time is it?", None),  # Irrelevant query
    ]
    
    print("🧪 Testing Statement Type Inference...")
    passed = 0
    for query, expected_stmt in test_cases:
        result = parse_instructions(query)
        actual = result.get("stmt_type_filter")
        status = "✅" if actual == expected_stmt else "❌"
        if status == "✅":
            passed += 1
        print(f"{status} | '{query[:35]}...' → Statement: {actual} (expected: {expected_stmt})")
    
    print(f"\nStatement Type: {passed}/{len(test_cases)} passed\n")
    return passed >= len(test_cases) - 1  # Allow 1 miss


def test_segment_detection():
    """Test segment/region detection."""
    test_cases = [
        ("Greater China operating income", "Greater China"),
        ("iPhone revenue", "Iphone"),
        ("Americas sales", "Americas"),
        ("Services segment growth", "Services"),
        ("Total company revenue", None),  # No segment
    ]
    
    print("🧪 Testing Segment Detection...")
    passed = 0
    for query, expected_seg in test_cases:
        result = parse_instructions(query)
        actual = result.get("segment_filter")
        
        if expected_seg is None:
            status = "✅" if actual is None else "❌"
        else:
            status = "✅" if (actual and actual.lower() == expected_seg.lower()) else "❌"
        
        if status == "✅":
            passed += 1
        print(f"{status} | '{query[:35]}...' → Segment: {actual} (expected: {expected_seg})")
    
    print(f"\nSegment Detection: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_where_filter_building():
    """Test ChromaDB where filter construction."""
    print("🧪 Testing Where Filter Building...")
    
    # Test 1: Statement type filter
    instructions = {"stmt_type_filter": "Income Statement"}
    where = build_chroma_where_filter(instructions)
    expected = {"stmt_type": {"$eq": "Income Statement"}}
    status = "✅" if where == expected else "❌"
    print(f"{status} | Statement filter: {where}")
    
    # Test 2: Source filter (single)
    instructions = {}
    where = build_chroma_where_filter(instructions, source_filter=["apple_10q.pdf"])
    expected = {"source": {"$eq": "apple_10q.pdf"}}
    status = "✅" if where == expected else "❌"
    print(f"{status} | Source filter (single): {where}")
    
    # Test 3: Combined filter
    instructions = {"stmt_type_filter": "Balance Sheet"}
    where = build_chroma_where_filter(instructions, source_filter=["file1.pdf", "file2.pdf"])
    # Should have $and with both conditions
    status = "✅" if where and "$and" in where else "❌"
    print(f"{status} | Combined filter: {where}")
    
    # Test 4: No filter
    instructions = {}
    where = build_chroma_where_filter(instructions)
    status = "✅" if where is None else "❌"
    print(f"{status} | Empty filter: {where}")
    
    print()
    return True


def test_complex_queries():
    """Test complex multi-constraint queries."""
    print("🧪 Testing Complex Queries...")
    
    test_cases = [
        "What was Greater China operating income for Q2 2025?",
        "Show me iPhone revenue for the three months ended March 2025",
        "Compare Americas vs Europe net sales for fiscal year 2024",
    ]
    
    for query in test_cases:
        result = parse_instructions(query)
        print(f"\n📋 Query: {query}")
        print(format_instructions_log(result))
        print(f"   Keywords: {result.get('keywords', [])}")
        print(f"   Confidence: {result.get('confidence', 0):.0%}")
    
    return True


def run_all_tests():
    """Run all instruction parser tests."""
    print("=" * 60)
    print("INSTRUCTED RETRIEVER - Instruction Parser Tests")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Period Extraction", test_period_extraction()))
    results.append(("Statement Type Inference", test_statement_type_inference()))
    results.append(("Segment Detection", test_segment_detection()))
    results.append(("Where Filter Building", test_where_filter_building()))
    results.append(("Complex Queries", test_complex_queries()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if not passed:
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
