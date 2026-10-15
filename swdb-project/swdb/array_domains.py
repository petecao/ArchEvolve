"""Explicit typed array-window declarations; created 2026-10-15 ET (tickets24/36).

A declaration is part of the input contract, not a source-origin certificate.
Proof admission must independently connect it to every operation and caller.
"""
import ast
import hashlib
import json
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
            return {'kind': 'parameter', 'name': name}, None
        if isinstance(node, ast.Constant) and type(node.value) is int and 0 <= node.value <= 2**64 - 1:
            return {'kind': 'constant', 'value': node.value}, node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value, constant = render(node.operand)
            sign = '+' if isinstance(node.op, ast.UAdd) else '-'
            tree = value if sign == '+' else {'kind': 'sub', 'left': {'kind': 'constant', 'value': 0}, 'right': value}
            return tree, None if constant is None else constant if sign == '+' else -constant
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left, lc = render(node.left)
            right, rc = render(node.right)
            sign = '+' if isinstance(node.op, ast.Add) else '-' if isinstance(node.op, ast.Sub) else '*'
            constant = None
            if lc is not None and rc is not None:
                constant = lc + rc if sign == '+' else lc - rc if sign == '-' else lc * rc
            return {'kind': {'+': 'add', '-': 'sub', '*': 'mul'}[sign], 'left': left, 'right': right}, constant
        raise Refused('extent allows only integer arithmetic: parameters, constants, +, - and *')

    rendered, constant = render(tree.body)
    if constant is not None and constant < 0:
        raise Refused('an array-window extent must be nonnegative')
    return rendered, names


def _entry_acsl(tree):
    kind = tree['kind']
    if kind == 'constant':
        return str(tree['value'])
    if kind == 'parameter':
        return f'\\at((integer){tree["name"]},Pre)'
    operator = {'add': '+', 'sub': '-', 'mul': '*'}[kind]
    return f'({_entry_acsl(tree["left"])} {operator} {_entry_acsl(tree["right"])})'


def bind(declarations, parameters):
    """Bind input windows to the lowered signature, without certifying origins.

    Scalar leaves denote mathematical integers at function entry. A source
    checker must still bind these names to actual parameter declarations and
    reject shadowing or mutation of pointer bindings before using this result.
    """
    parameters = tuple(parameters)
    found = problems(declarations, parameters)
    if found:
        raise Refused('; '.join(f'{where}: {reason}' for where, reason in found))
    types = {name: ctype for name, ctype, _pointer in parameters}
    windows = {}
    for name, data in sorted(declarations.items()):
        tree, names = _extent(data['extent'])
        windows[name] = {'parameter': name, 'element_type': _plain(types[name].replace('*', '')),
                         'extent_tree': tree, 'entry_acsl': _entry_acsl(tree), 'parameters': sorted(names)}
    digest = hashlib.sha256(json.dumps(declarations, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'check': identity(), 'declarations_sha256': digest, 'windows': windows}


def interval(tree, bounds):
    """Conservative mathematical interval over all supplied integer draws.

    Repeated leaves deliberately lose correlation. A larger interval can refuse
    a valid plan, but cannot silently narrow a bounded experiment's inputs.
    """
    if not isinstance(tree, dict):
        raise Refused('an extent interval needs a canonical expression tree')
    kind = tree.get('kind')
    if kind == 'constant' and set(tree) == {'kind', 'value'} and type(tree['value']) is int:
        return tree['value'], tree['value']
    if kind == 'parameter' and set(tree) == {'kind', 'name'}:
        bound = bounds.get(tree['name'])
        if (not isinstance(bound, (tuple, list)) or len(bound) != 2
                or any(type(value) is not int for value in bound) or bound[0] > bound[1]):
            raise Refused(f'{tree["name"]} needs ordered mathematical integer draw bounds')
        return tuple(bound)
    if kind not in {'add', 'sub', 'mul'} or set(tree) != {'kind', 'left', 'right'}:
        raise Refused('an extent interval needs a canonical expression tree')
    left, right = interval(tree['left'], bounds), interval(tree['right'], bounds)
    if kind == 'add':
        return left[0] + right[0], left[1] + right[1]
    if kind == 'sub':
        return left[0] - right[1], left[1] - right[0]
    products = [a * b for a in left for b in right]
    return min(products), max(products)


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
