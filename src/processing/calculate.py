def safe_divide(x, y):
    """Avoid division by zero."""
    try:
        return float(x) / float(y)
    except ZeroDivisionError:
        return None

def apply_calculator(expression: str):
    """
    Very simple calculator tool.
    Later we will connect this to the LLM.
    """
    try:
        return eval(expression, {"__builtins__": None}, {})
    except Exception:
        return None
