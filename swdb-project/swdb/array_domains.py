"""Explicit typed array-window declarations; created 2026-10-15 ET (tickets24/36).

A declaration is part of the input contract, not a source-origin certificate.
Proof admission must independently connect it to every operation and caller.
"""
import ast
import hashlib
import re
from pathlib import Path


class Refused(ValueError):
    pass


def identity():
    return {'id': 'swdb-array-domain-1', 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _plain(ctype):
    return ' '.join(re.sub(r'\b(?:const|volatile|restrict)\b', '', ctype).split())


def _extent(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 256:
        raise Refused('extent needs a nonempty integer expression string of at most 256 characters')
    if not re.fullmatch(r'[A-Za-z_0-9\s()+*-]+', text, re.ASCII):
        raise Refused('extent allows only integer arithmetic: parameters, constants, +, - and *')
    # C identifiers such as lambda, async and True must not acquire Python
    # keyword/literal meaning merely because this bounded parser uses ast.
    aliases = {}

    def rename(match):
        name = match.group()
        if name not in aliases:
            aliases[name] = f'array_domain_parameter_{len(aliases)}'
        return aliases[name]

    encoded = re.sub(r'\b[A-Za-z_][A-Za-z_0-9]*\b', rename, text.strip(), flags=re.ASCII)
    originals = {alias: name for name, alias in aliases.items()}
    try:
        tree = ast.parse(encoded, mode='eval')
    except (SyntaxError, ValueError, RecursionError):
        raise Refused('extent allows only integer arithmetic: parameters, constants, +, - and *') from None
    if len(list(ast.walk(tree))) > 64:
        raise Refused('extent integer arithmetic is too large')
    names = set()

    def render(node):
        if isinstance(node, ast.Name) and node.id in originals:
            name = originals[node.id]
            names.add(name)
            return f'((integer){name})', None
        if isinstance(node, ast.Constant) and type(node.value) is int and 0 <= node.value <= 2**64 - 1:
            return str(node.value), node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value, constant = render(node.operand)
            sign = '+' if isinstance(node.op, ast.UAdd) else '-'
            return f'({sign}{value})', None if constant is None else constant if sign == '+' else -constant
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left, lc = render(node.left)
            right, rc = render(node.right)
            sign = '+' if isinstance(node.op, ast.Add) else '-' if isinstance(node.op, ast.Sub) else '*'
            constant = None
            if lc is not None and rc is not None:
                constant = lc + rc if sign == '+' else lc - rc if sign == '-' else lc * rc
            return f'({left} {sign} {right})', constant
        raise Refused('extent allows only integer arithmetic: parameters, constants, +, - and *')

    rendered, constant = render(tree.body)
    if constant is not None and constant < 0:
        raise Refused('an array-window extent must be nonnegative')
    return rendered, names


def problems(declarations, parameters=None):
    """Shape first; with lowered parameters also check actual names and types."""
    if not isinstance(declarations, dict):
        return [('array_domains', 'array_domains needs a mapping from pointer parameters to extent declarations')]
    from swdb.c_lowering import FLOAT_TYPES, INTEGER_TYPES
    parameters = None if parameters is None else {name: (ctype, pointer) for name, ctype, pointer in parameters}
    found = []
    for name, data in declarations.items():
        where = f'array_domains.{name}'
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_]\w*', name, re.ASCII):
            found.append((where, 'an array domain names a pointer parameter'))
            continue
        if not isinstance(data, dict) or set(data) != {'extent'}:
            found.append((where, 'an array domain has exactly extent'))
            continue
        try:
            _rendered, names = _extent(data['extent'])
        except Refused as exc:
            found.append((where + '.extent', str(exc)))
            continue
        if parameters is None:
            continue
        ctype, pointer = parameters.get(name, ('', False))
        element = _plain(ctype.replace('*', ''))
        if not pointer or ctype.count('*') != 1 or element not in INTEGER_TYPES | FLOAT_TYPES:
            found.append((where, 'an array domain needs a primitive pointer parameter of the lowered proof unit'))
        for variable in sorted(names):
            scalar, is_pointer = parameters.get(variable, ('', True))
            if is_pointer or _plain(scalar) not in INTEGER_TYPES:
                found.append((where + '.extent', f'{variable} is not a scalar integer parameter of the lowered proof unit'))
    return found
