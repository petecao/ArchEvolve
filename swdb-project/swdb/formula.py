"""Element-count formulas: integer arithmetic over input property symbols.

A formula is a Python-style expression using + - * // ( ), integer literals, and names
(for example `num_nodes + 1`, `2 * num_edges_undirected`). Nothing else is allowed, so a
formula can be evaluated without running any code.
"""

import ast

_OPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b, ast.FloorDiv: lambda a, b: a // b}


class FormulaError(ValueError):
    pass


def _parse(text):
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"formula {text!r} is not valid: {exc.msg}") from None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Expression, ast.Name, ast.Load, ast.BinOp, *_OPS)):
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            continue
        raise FormulaError(f"formula {text!r} uses {type(node).__name__}; only + - * // ( ), integers, and names")
    return tree


def symbols(text):
    """The names a formula uses, in first-use order. Raises FormulaError if it is malformed."""
    return list(dict.fromkeys(node.id for node in ast.walk(_parse(text)) if isinstance(node, ast.Name)))


def evaluate(text, values):
    """Evaluate with {symbol: int or None}. Returns None if any symbol it uses is None.

    Raises FormulaError if a symbol is not in `values` at all (the input does not define it).
    """
    tree = _parse(text)
    missing = [name for name in symbols(text) if name not in values]
    if missing:
        raise FormulaError(f"formula {text!r} uses {', '.join(missing)}, which the input does not define")
    if any(values[name] is None for name in symbols(text)):
        return None

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        return _OPS[type(node.op)](ev(node.left), ev(node.right))

    return ev(tree)
