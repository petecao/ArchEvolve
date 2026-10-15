"""Exact qualified std::copy range model; created 2026-10-15 ET (ticket24).

The standard iterator domain is explicit: input endpoints belong to one typed
array range and the destination supplies that many elements of one typed array.
Validity/initialization/separation and numerical bounds remain proof obligations.
This is a checked source/view relation, not a body proof or a caller certificate.
"""
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from swdb import c_lowering

NAME = 'std_copy_int'
TEXT_SHA256 = 'efcf958c7433473e0478d53b60d2aab648124e87df8e04f13b41f1087c94da26'
EXTENT = r'(\at(first,Pre) == \at(last,Pre) ? 0 : (\at(last,Pre) - \at(first,Pre)))'


class Refused(ValueError):
    pass


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':')))


def identity():
    return {'id':'standard-range-model-check-1', 'sha256':_sha(Path(__file__).read_bytes())}


def _children(node):
    return [c for c in node.get('inner', []) if isinstance(c, dict) and c.get('kind')]


def _expression(node, bindings):
    children = _children(node)
    kind = node.get('kind')
    if kind == 'ImplicitCastExpr' and len(children) == 1 and node.get('castKind') in {
            'LValueToRValue', 'NoOp', 'IntegralCast'}:
        return _expression(children[0], bindings)
    if kind == 'DeclRefExpr':
        name = bindings.get((node.get('referencedDecl') or {}).get('id'))
        if name:
            return name
    if kind == 'IntegerLiteral':
        return int(node['value'])
    if kind in {'BinaryOperator', 'UnaryOperator', 'ArraySubscriptExpr', 'ConditionalOperator'}:
        return (node.get('opcode', {'ArraySubscriptExpr':'[]', 'ConditionalOperator':'?:'}.get(kind)),
                *(_expression(c, bindings) for c in children))
    raise Refused('the exact audited std_copy_int expression bindings changed')


def _shape(text, directory):
    source = Path(directory) / 'standard_range_original_ast.c'
    source.write_text('\n'.join([*c_lowering.HEADERS, text]) + '\n')
    tool = c_lowering.locate()
    if tool.missing:
        raise Refused(tool.missing)
    result = subprocess.run([*tool.command, '-x', 'c', '-std=gnu11', '-fsyntax-only',
        '-Xclang', '-ast-dump=json', '-Xclang', '-ast-dump-filter=' + NAME, str(source)],
        capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise Refused('the exact audited std_copy_int model did not parse')
    try:
        function = json.loads(result.stdout)
        first, last, destination, body = _children(function)
        declaration, loop, returned = _children(body)
        count, = _children(declaration)
        initial, condition, increment, assignment = _children(loop)
        index, = _children(initial)
        bindings = {n['id']:n['name'] for n in (first, last, destination, count, index)}
        expressions = [_expression(n, bindings) for n in (
            _children(count)[0], _children(index)[0], condition, increment, assignment, _children(returned)[0])]
    except (KeyError, ValueError, TypeError, IndexError):
        raise Refused('the exact audited std_copy_int C-AST structure changed') from None
    expected = [('?:', ('==', 'first', 'last'), 0, ('-', 'last', 'first')), 0,
                ('<', 'i', 'n'), ('++', 'i'), ('=', ('[]', 'd_first', 'i'), ('[]', 'first', 'i')),
                ('?:', ('==', 'n', 0), 'd_first', ('+', 'd_first', 'n'))]
    if (function.get('kind') != 'FunctionDecl' or function.get('name') != NAME
            or function.get('storageClass') != 'static' or body.get('kind') != 'CompoundStmt'
            or [n.get('name') for n in (first,last,destination,count,index)] != ['first','last','d_first','n','i']
            or [n.get('kind') for n in (first,last,destination)] != ['ParmVarDecl'] * 3
            or [n.get('type',{}).get('qualType') for n in (first,last,destination)] != ['const int *','const int *','int *']
            or count.get('type',{}).get('qualType') != 'const ptrdiff_t'
            or index.get('type',{}).get('qualType') != 'ptrdiff_t'
            or loop.get('kind') != 'ForStmt' or returned.get('kind') != 'ReturnStmt' or expressions != expected):
        raise Refused('the exact audited std_copy_int parameter, count, loop or return relation changed')
    return {'parameters':[['first','const int *'],['last','const int *'],['d_first','int *']],
            'count':'first == last ? 0 : last - first', 'count_binding':'immutable local n',
            'loop':{'index':'i','initial':0,'condition':'i < n','step':'++i','body':'d_first[i] = first[i]'},
            'return':'n == 0 ? d_first : d_first + n', 'pointer_rebinding':False,
            'parser':c_lowering.identity()['clang']}


@dataclass(frozen=True)
class View:
    original: str
    text: str
    certificate: dict
    pins: dict


def wp_view(name, text, directory):
    if name != NAME:
        raise Refused('only the exact std_copy_int model has an audited typed-range relation')
    if _sha(text) != TEXT_SHA256:
        raise Refused('the exact audited std_copy_int body and contract must be unchanged')
    shape = _shape(text, directory)
    entry = f'  /*@ assert std_copy_range_entry: 0 <= {EXTENT} <= PTRDIFF_MAX; */\n'
    access = f'/*@ assert std_copy_range_access: 0 <= i < {EXTENT}; */'
    returned = f'  /*@ assert std_copy_range_return: n == 0 || 0 <= n <= {EXTENT}; */\n'
    view = text.replace('  const ptrdiff_t n =', entry + '  const ptrdiff_t n =')
    view = view.replace('for (ptrdiff_t i = 0; i < n; ++i) d_first[i] = first[i];',
                        'for (ptrdiff_t i = 0; i < n; ++i) { ' + access + ' d_first[i] = first[i]; }')
    view = view.replace('  return n == 0', returned + '  return n == 0')
    contract = text[:text.index('static int *' + NAME)]
    domain = {'model':NAME, 'element_type':'int', 'extent_acsl':EXTENT,
              'extent_environment':'entry pointer values; mathematical element count',
              'source':{'first':'first','last':'last','same_array_required':True,
                        'offset_first':'0','offset_last':EXTENT},
              'destination':{'first':'d_first','same_count_as_source':True,'offset_first':'0'},
              'empty':'equal endpoints execute no C pointer subtraction, indexing or addition',
              'lifetime':'both typed arrays remain live throughout the call; no allocation inference',
              'caller_rule':'same typed array root/subobject and live lifetime; ordered endpoint offsets and destination capacity'}
    certificate = {'version':1, 'check':identity(), 'model':NAME, 'original_text_sha256':_sha(text),
        'view_text_sha256':_sha(view), 'original_contract_sha256':_sha(contract), 'view_contract_sha256':_sha(contract),
        'domain_role':'explicit standard-library valid-range domain; caller discharge required',
        'standalone_scope':'range-qualified body contract; not unrestricted opaque-pointer admission',
        'acsl_input_premises_added':[], 'typed_input_domain':domain, 'range_domain':domain,
        'source_ast':shape, 'obligations':['std_copy_range_entry','std_copy_range_access','std_copy_range_return'],
        'body_operations_removed':[], 'references':['https://eel.is/c++draft/alg.copy',
                                                    'https://eel.is/c++draft/iterator.requirements.general']}
    return View(text, view, certificate, {'standard_range_model_check':identity(),
        'standard_range_model_certificate':{'id':'standard-range-model-certificate-1','sha256':_digest(certificate)}})


def check_view(name, view, directory):
    if view != wp_view(name, c_lowering.model_text(name), directory):
        raise Refused('the qualified std_copy_int source, view, domain or pins changed before launch')


def qualified_origin(view, function, node, definitions):
    """Bind the exact model's entry parameters, never a same-spelled local or callee.

    The caller must first check_view against current canonical bytes and ensure
    its complete model input is exactly HEADERS + view.text. This is not a
    general dictionary-based origin-admission interface.
    """
    if function != NAME or node.get('kind') != 'DeclRefExpr':
        return None
    reference = node.get('referencedDecl') or {}
    parameters = {n.get('id'):n for n in _children(definitions[function]) if n.get('kind') == 'ParmVarDecl'}
    declaration = parameters.get(reference.get('id'))
    if not declaration or declaration.get('name') not in {'first','last','d_first'}:
        return None
    name = declaration['name']
    return {'kind':'qualified_standard_range', 'root':'source' if name != 'd_first' else 'destination',
            'element_type':'int', 'elements':EXTENT, 'relative_offset':EXTENT if name == 'last' else '0',
            'certificate':view.pins['standard_range_model_certificate']}
