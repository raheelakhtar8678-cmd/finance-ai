# E:\finance-ai\test\test_calculator.py

# To import your source code, you need to navigate from the root directory (E:\finance-ai)
# to the src/analysis folder. Since the 'src' folder is a package, we import it directly.
from src.analysis.calculator import safe_eval_expr
import pytest

# Test functions MUST start with 'test_'
def test_basic_addition():
    """Tests simple addition."""
    assert safe_eval_expr("5 + 3") == 8

def test_subtraction_with_variables():
    """Tests subtraction using user-defined variables."""
    expr = "asset_value - liability_value"
    variables = {"asset_value": 50000, "liability_value": 15000}
    result = safe_eval_expr(expr, variables)
    assert result == 35000

def test_complex_formula():
    """Tests a formula combining variables, operations, and function calls."""
    # Test for EBITDA Margin: (Revenue - Expenses) / Revenue * 100
    expr = "(R - E) / R * 100"
    variables = {"R": 1000, "E": 600}
    
    expected_margin = (1000 - 600) / 1000 * 100
    result = safe_eval_expr(expr, variables)
    
    # Use pytest.approx for floating-point comparisons
    assert result == pytest.approx(expected_margin)

def test_unsupported_operator():
    """Tests that an unsafe operator (like bit shift) is correctly rejected."""
    with pytest.raises(ValueError) as excinfo:
        safe_eval_expr("5 << 2")
    assert "Unsupported operator" in str(excinfo.value)

def test_missing_variable():
    """Tests that a missing variable raises an error."""
    with pytest.raises(ValueError) as excinfo:
        safe_eval_expr("existing_var + missing_var", {"existing_var": 10})
    assert "Unknown variable: missing_var" in str(excinfo.value)

def test_safe_function_max():
    """Tests the use of a safe built-in function like max()."""
    expr = "max(2, 8, -1)"
    assert safe_eval_expr(expr) == 8