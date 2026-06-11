def calculator(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        allowed = set("0123456789+-*/.()% ")
        clean = "".join(c for c in expression if c in allowed)
        result = eval(clean)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
