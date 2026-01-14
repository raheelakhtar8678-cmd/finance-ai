# test/test_formatting.py
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.query_controller import format_currency
from src.analysis.metric_registry import METRIC_REGISTRY

def test_format_currency_percent():
    """Test that metrics with unit='percent' are formatted correctly."""
    
    # Revenue Growth
    val = 5.08
    formatted = format_currency(val, metric_name="revenue_growth")
    print(f"Revenue Growth: {val} -> {formatted}")
    assert formatted == "5.08%"
    
    # Gross Margin
    val = 45.6
    formatted = format_currency(val, metric_name="gross_margin")
    print(f"Gross Margin: {val} -> {formatted}")
    assert formatted == "45.60%"
    
    # Fallback if metric name not provided
    formatted_default = format_currency(5.08)
    print(f"Default (no metric): {val} -> {formatted_default}")
    assert formatted_default == "$5.08"

def test_format_currency_ratio():
    """Test that metrics with unit='ratio' are formatted correctly."""
    
    val = 1.5
    formatted = format_currency(val, metric_name="current_ratio")
    print(f"Current Ratio: {val} -> {formatted}")
    assert formatted == "1.50x"

def test_format_currency_standard():
    """Test standard currency formatting."""
    
    # Billions
    val = 95_123_000_000
    formatted = format_currency(val, metric_name="revenue")
    print(f"Revenue (B): {val} -> {formatted}")
    assert "billion" in formatted
    assert "$95.12" in formatted
    
    # Millions
    val = 4_600_000
    formatted = format_currency(val, metric_name="operating_income")
    print(f"Income (M): {val} -> {formatted}")
    assert "million" in formatted
    assert "$4.60" in formatted

if __name__ == "__main__":
    test_format_currency_percent()
    test_format_currency_ratio()
    test_format_currency_standard()
    print("✅ All formatting tests passed!")
