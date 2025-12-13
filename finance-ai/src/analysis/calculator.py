# src/analysis/calculator.py
import ast
import operator as op
from typing import Any, Dict

# Supported operators for safe evaluation
SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}

def _eval(node: ast.AST, variables: Dict[str, Any]) -> Any:
    """Recursively evaluate AST nodes (very small safe subset)."""
    if isinstance(node, (ast.Constant, ast.Num)):
        return node.n if hasattr(node, 'n') else node.value
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        left_val = _eval(node.left, variables)
        right_val = _eval(node.right, variables)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func:
            return op_func(left_val, right_val)
        raise ValueError(f"Unsupported operator: {type(node.op)}")
    if isinstance(node, ast.UnaryOp):
        operand_val = _eval(node.operand, variables)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func:
            return op_func(operand_val)
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    raise ValueError(f"Unsupported AST node: {type(node)}")

def safe_eval_expr(expr: str, variables: Dict[str, Any] = None) -> Any:
    """
    Safely evaluate a math expression with variables.
    Example:
        safe_eval_expr("revenue_2024 - revenue_2023", {"revenue_2024": 1234, "revenue_2023": 1000})
    """
    variables = variables or {}
    try:
        tree = ast.parse(expr, mode="eval")
        return _eval(tree.body, variables)
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression '{expr}': {e}")