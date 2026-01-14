# test/test_comparison_engine.py
import pytest
from src.analysis.comparison_engine import MultiTableComparator
from src.analysis.metric_registry import METRIC_REGISTRY

# Mock tables (simplified structure for the test)
MOCK_TABLES = [
    {
        "source": "doc1.pdf",
        "df": None, # Actual DF not needed for this test as we mocking calculation results
        # We are testing _generate_summary which takes 'results' list, 
        # so we don't need full table ingestion logic here.
    },
    {
        "source": "doc2.pdf",
        "df": None,
    }
]

def test_summary_formatting_revenue_growth_percent():
    """Test that revenue_growth (percent) is formatted as %"""
    
    comparator = MultiTableComparator(MOCK_TABLES)
    
    # Mock results from compute_metric_with_reasoning
    results = [
        {
            "source": "doc1.pdf",
            "value": 5.08,
            "period": "2025"
        },
        {
            "source": "doc2.pdf",
            "value": -4.31,
            "period": "2024"
        }
    ]
    
    summary = comparator._generate_summary("revenue_growth", results)
    
    print("\nGenerated Summary (Percent):\n", summary)
    
    # Assertions
    assert "5.08%" in summary
    assert "-4.31%" in summary
    assert "$5.08" not in summary  # Should NOT be dollar
    assert "9.39 percentage points" in summary or "9.39" in summary

def test_summary_formatting_revenue_currency():
    """Test that revenue (currency) is formatted as $"""
    
    comparator = MultiTableComparator(MOCK_TABLES)
    
    results = [
        {
            "source": "doc1.pdf",
            "value": 95123000000, # 95B
            "period": "2025"
        },
        {
            "source": "doc2.pdf",
            "value": 90000000000, # 90B
            "period": "2024"
        }
    ]
    
    summary = comparator._generate_summary("revenue", results)
    
    print("\nGenerated Summary (Currency):\n", summary)
    
    # Assertions
    assert "$95.12B" in summary
    assert "$90.00B" in summary
    
def test_summary_formatting_current_ratio():
    """Test that current_ratio (ratio) is formatted as x"""
    
    comparator = MultiTableComparator(MOCK_TABLES)
    
    results = [
        {
            "source": "doc1.pdf",
            "value": 1.5,
            "period": "2025"
        },
        {
            "source": "doc2.pdf",
            "value": 1.1,
            "period": "2024"
        }
    ]
    
    summary = comparator._generate_summary("current_ratio", results)
    
    print("\nGenerated Summary (Ratio):\n", summary)
    
    # Assertions
    assert "1.50x" in summary
    assert "1.10x" in summary
    assert "0.40x" in summary

if __name__ == "__main__":
    test_summary_formatting_revenue_growth_percent()
    test_summary_formatting_revenue_currency()
    test_summary_formatting_current_ratio()
    print("All tests passed!")
