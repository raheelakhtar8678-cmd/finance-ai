# src/analysis/formula_evaluator.py
"""
Safe Deterministic Formula Evaluator
Uses AST to evaluate financial formulas without the risks of eval().
"""

import ast
import operator as op
from typing import Dict, Any, Optional

# Supported operators for financial math
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def safe_eval(expr: str, variables: Dict[str, float]) -> Optional[float]:
    """
    Evaluates a mathematical expression safely using the provided variables.
    """
    try:
        # Parse the expression into an AST
        node = ast.parse(expr, mode='eval').body
        return _eval(node, variables)
    except Exception as e:
        print(f"⚠️ Formula evaluation error: {e}")
        return None

def _eval(node, variables):
    """Recursive helper for AST evaluation."""
    if isinstance(node, ast.Num):  # <3.8
        return node.n
    elif isinstance(node, ast.Constant):  # >=3.8
        return node.value
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left, variables), _eval(node.right, variables))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](_eval(node.operand, variables))
    elif isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise NameError(f"Variable '{node.id}' not provided.")
    else:
        raise TypeError(f"Unsupported AST node: {type(node)}")

def evaluate_metric(formula: str, data: Dict[str, float]) -> Dict[str, Any]:
    """
    Main entry point for calculating a metric based on raw data.
    """
    result = safe_eval(formula, data)
    
    if result is not None:
        return {
            "success": True,
            "result": result,
            "formula_used": formula,
            "inputs": data
        }
    
    return {
        "success": False,
        "error": "Evaluation failed"
    }

if __name__ == "__main__":
    # Quick test
    test_vars = {"revenue": 1000, "cost_of_revenue": 400}
    test_formula = "(revenue - cost_of_revenue) / revenue * 100"
    print(f"Result: {evaluate_metric(test_formula, test_vars)}")
