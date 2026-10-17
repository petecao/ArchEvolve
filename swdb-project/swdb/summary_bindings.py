"""Bind imported generic summaries to the actual callee and proof domain (2026-10-15 ET).

Equality here is deliberately syntactic over a fresh complete C closure. It is
not inferred from a shared function name or from agreement of two native views.
DX imports have their separate checked model binding and do not use this path.
"""
import hashlib
from pathlib import Path

from swdb import c_lowering, helper_windows, proof_setup
from swdb.store import Store


class Refused(ValueError):
    pass


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _body(text):
    first, separator, rest = text.partition('\n')
    if not separator or not first.startswith('/* C lowering of ') or not first.endswith('Generated: do not edit. */'):
        raise Refused('summary closure has no recognized lowering provenance header')
    return rest


def _closure(source, function, defines):
    tree = helper_windows._Tree(source, c_lowering.locate(), (), defines)
    pending, seen = [tree.entry(function)], set()
    while pending:
        fn = pending.pop()
        if fn['id'] in seen:
            continue
        seen.add(fn['id'])
        if any(n.get('kind', '').endswith('Attr') for n in fn.get('inner', [])):
            raise Refused('summary source attributes are outside checked closure equality')
        for node in helper_windows._walk(tree.body(fn) or {}):
            if node.get('kind') == 'VarDecl' and node.get('storageClass') in {'static', 'extern'}:
                raise Refused('summary source persistent local state is unsupported')
            if node.get('kind') == 'DeclRefExpr':
                decl = tree.nodes.get(node.get('referencedDecl', {}).get('id'), {})
                if decl.get('kind') == 'VarDecl' and decl not in list(helper_windows._walk(tree.body(fn) or {})):
                    raise Refused('summary source global state needs an independent call-state binding')
            if node.get('kind') == 'CallExpr':
                target = tree.binding(node)
                if tree.body(target) is None:
                    raise Refused('summary closure contains an unbound external call')
                pending.append(target)
    lowered = c_lowering.lower(source, function, defines=defines)
    if lowered.models or lowered.std_models or lowered.summaries or lowered.allocation:
        raise Refused('summary closure with model or summary dependencies needs recursive source binding')
    return tree, lowered


def check(adapter, source, caller, callee, entry_id, record_id, *, caller_bounds=None):
    """Return generator-owned binding metadata, or refuse before importing any assumes.

    A finite array proof is reusable only for direct calls with distinct caller
    entry-buffer bases of exactly its proved capacity. Its scalar size limits
    must follow from literal arguments or the caller's requested bounds. More general subobjects,
    aliases and contextual helper calls remain closed.
    """
    try:
        return _check(adapter, Path(source), caller, callee, entry_id, record_id, caller_bounds)
    except (helper_windows.Refused, c_lowering.LoweringError, OSError, KeyError, TypeError) as exc:
        raise Refused(f'summary {entry_id} source/proof binding refused: {exc}') from None


def _check(adapter, source, caller, callee, entry_id, record_id, caller_bounds):
    entry = adapter.library.get(entry_id) or {}
    unit = entry.get('proof_unit') or {}
    location = unit.get('source') or {}
    library_source = adapter.library.resolve(location)
    if _sha(library_source.read_bytes()) != location.get('sha256') or unit.get('function') != callee:
        raise Refused('summary implementation source differs from its declared pin')
    _, expected = _closure(library_source, callee, adapter.defines)
    tree, actual = _closure(source, callee, adapter.defines)
    if _body(actual.text) != _body(expected.text):
        raise Refused('actual called definition differs from the proven summary implementation')
    records = Store(adapter.records)
    record = records.get(record_id, 'proof') or {}
    pins = record.get('pins') or {}
    method = {'id': adapter.method.id, 'sha256': adapter.method.sha256}
    setup = record.get('proof_setup_check') or {}
    contract_pin = {'id': entry_id, 'sha256': adapter.library.content_sha256(entry_id)}
    if (record.get('subject') != {'kind': 'library_summary', 'id': entry_id}
            or record.get('verdict') != 'proven'
            or (record.get('job') or {}).get('adapter') not in {'wp', 'cbmc', 'crux-llvm-c', 'crux-llvm-cxx'}
            or record.get('evidence_kind') != adapter.method.data.get('evidence_kind')
            or pins.get('code') != contract_pin or pins.get('contract') != contract_pin
            or pins.get('method_version') != method or setup.get('method_version') != method
            or setup.get('verdict') != 'passed' or not setup.get('runs')
            or setup.get('check') != proof_setup.identity()['proof_setup_check']
            or pins.get('c_lowering') != {'id': f'{callee}.c', 'sha256': expected.sha256}
            or pins.get('build_constants', []) != list(adapter.defines)
            or pins.get('summaries') or pins.get('models')):
        raise Refused('summary proof does not certify this fresh implementation, method and build closure')
    reports = [record.get('evidence', {}).get('adapter_log'),
               *record.get('evidence', {}).get('reports', [])]
    if not reports or any(not row or _sha(Path(row['path']).read_bytes()) != row.get('sha256') for row in reports):
        raise Refused('summary proof evidence is missing or changed')
    bounds = record.get('bounds') or {}
    if bounds.get('threads') not in (1, 'unbounded'):
        raise Refused('summary proof has no supported sequential domain')
    if (record.get('job') or {}).get('adapter') == 'wp':
        reading = record.get('verdict_reading') or {}
        if reading.get('verdict') != 'proven' or reading.get('check') != proof_setup.identity()['verdict_reading']:
            raise Refused('summary WP proof has no current successful property reading')
    finite = {name: value for name, value in bounds.items() if name != 'threads' and value != 'unbounded'}
    if any(type(value) is not int or value < 0 or not any(p[0] == name and not p[2] for p in actual.parameters)
           for name, value in finite.items()):
        raise Refused('summary proof has unsupported finite dimensions')
    if caller_bounds is None and finite:
        raise Refused('an unbounded caller cannot import a finite summary proof')
    pointers = [(index, name) for index, (name, _, pointer) in enumerate(actual.parameters) if pointer]
    root = tree.entry(caller)
    calls = []
    # Independently resolve each call in the retained caller closure. A namespace,
    # template, overload or attributed prototype cannot borrow a global name.
    pending, seen = [root], set()
    while pending:
        fn = pending.pop()
        if fn['id'] in seen:
            continue
        seen.add(fn['id'])
        for node in helper_windows._walk(tree.body(fn) or {}):
            if node.get('kind') != 'CallExpr':
                continue
            ref = helper_windows._unwrap(node['inner'][0]).get('referencedDecl', {})
            if ref.get('name') == callee:
                bound = tree.binding(node)
                if bound['id'] != tree.entry(callee)['id']:
                    raise Refused('summary call is not bound to its checked definition')
                calls.append((fn, node))
            elif ref.get('name') in tree.functions:
                target = tree.binding(node)
                if tree.body(target) is not None:
                    pending.append(target)
    if not calls:
        raise Refused('no independently bound call to the imported summary')
    sizes = {name: value for name, value in (caller_bounds or {}).items()
             if name != 'threads' and type(value) is int}
    root_scalars = {n['id']: n.get('name') for n in root.get('inner', [])
                    if n.get('kind') == 'ParmVarDecl' and '*' not in n.get('type', {}).get('qualType', '')}
    for fn, call in calls:
        for name, limit in finite.items():
            if fn['id'] != root['id']:
                raise Refused('finite summary dimensions require direct checked entry calls')
            index = next(i for i, p in enumerate(actual.parameters) if p[0] == name)
            argument = helper_windows._unwrap(call['inner'][index + 1])
            if argument.get('kind') == 'IntegerLiteral':
                upper = int(argument['value'])
            elif argument.get('kind') == 'DeclRefExpr':
                upper = sizes.get(root_scalars.get(argument.get('referencedDecl', {}).get('id')))
            else:
                upper = None
            if upper is None or upper > limit:
                raise Refused('callee size argument exceeds or lacks a checked summary proof bound')
        # A parameter written earlier is no longer its entry value. Reject the
        # whole grammar, rather than infer a call-state invariant from its name.
        protected = set(root_scalars) if finite else set()
        if pointers and finite:
            protected |= {n['id'] for n in root.get('inner', []) if n.get('kind') == 'ParmVarDecl'
                          and '*' in n.get('type', {}).get('qualType', '')}
        for node in helper_windows._walk(tree.body(root)):
            children = node.get('inner', [])
            mutation = (node.get('kind') == 'CompoundAssignOperator' or
                        (node.get('kind') == 'BinaryOperator' and node.get('opcode') == '=') or
                        (node.get('kind') == 'UnaryOperator' and node.get('opcode') in {'++', '--', '&'}))
            if mutation and children:
                target = helper_windows._unwrap(children[0])
                if target.get('referencedDecl', {}).get('id') in protected:
                    raise Refused('summary call domain uses a modified or escaped entry parameter')
    if pointers and finite:
        if max(sizes.values(), default=0) != max(finite.values()):
            raise Refused('caller and summary entry-buffer capacities differ')
        root_parameters = {n['id'] for n in root.get('inner', []) if n.get('kind') == 'ParmVarDecl'
                           and '*' in n.get('type', {}).get('qualType', '')}
        for fn, call in calls:
            if fn['id'] != root['id']:
                raise Refused('finite pointer summaries require a direct checked entry-buffer call')
            roots = []
            for index, _ in pointers:
                argument = helper_windows._unwrap(call['inner'][index + 1])
                ident = argument.get('referencedDecl', {}).get('id')
                if argument.get('kind') != 'DeclRefExpr' or ident not in root_parameters:
                    raise Refused('finite pointer summary argument is not an entry-buffer base')
                roots.append(ident)
            if len(set(roots)) != len(roots):
                raise Refused('finite pointer summary arguments alias distinct proof buffers')
    return {'entry': entry_id, 'proof_record': record_id, 'source_sha256': expected.source_sha256,
            'callee_lowering_sha256': actual.sha256, 'proof_lowering_sha256': expected.sha256,
            'finite_bounds': finite, 'call_count': len(calls),
            'scope': 'equal fresh global callee closure; finite arguments follow from unchanged entry bounds'}


def bind(adapter, context, source, caller, callee, entry_id, record_id, *, caller_bounds=None):
    checked = check(adapter, source, caller, callee, entry_id, record_id, caller_bounds=caller_bounds)
    context.setdefault('summary_binding_runtime', []).append(
        (str(source), caller, callee, entry_id, record_id, caller_bounds))
    context.setdefault('settings', {}).setdefault('summary_bindings', []).append(checked)
    return checked


def recheck(adapter, context):
    plans = context.get('summary_binding_runtime', [])
    checked = [check(adapter, *plan[:5], caller_bounds=plan[5]) for plan in plans]
    if checked != context.get('settings', {}).get('summary_bindings', []):
        raise Refused('summary source/proof binding changed or disappeared before launch')
    expected = {(row['entry'], row['proof_record']) for row in checked}
    # DX model imports are recorded separately and never borrow these generic proofs.
    actual = {(row['id'], row['proof_record']) for row in (context.get('pins') or {}).get('summaries', [])}
    if expected != actual:
        raise Refused('imported generic summary pins lack their independent source/proof binding')
    return checked
