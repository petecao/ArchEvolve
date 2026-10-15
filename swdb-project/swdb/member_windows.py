"""Checked entry-specific pointer-field windows (2026-10-15 ET).

Only one trivial automatic receiver, with immutable pointer/count captures from
an explicit entry window, is admitted. This is a selected-entry context, never a
contract for an arbitrary method receiver. Ordinary init/validity/RTE remain.
"""
import hashlib
import json
from pathlib import Path
import re


class Refused(ValueError):
    pass


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def identity():
    return {'id': 'swdb-member-windows-1', 'sha256': _hash(Path(__file__).read_bytes())}


def _children(n):
    return [c for c in n.get('inner', []) if isinstance(c, dict) and c.get('kind')]


def _walk(n):
    yield n
    for c in _children(n):
        yield from _walk(c)


def _strip(n):
    while n.get('kind') in {'ParenExpr', 'ImplicitCastExpr'}:
        if n.get('kind') == 'ImplicitCastExpr' and n.get('castKind') not in {'NoOp', 'LValueToRValue', 'FunctionToPointerDecay'}:
            raise Refused('member context needs identity source conversions')
        n, = _children(n)
    return n


def _qual(n):
    return n.get('type', {}).get('qualType', '')


def _type(n):
    return re.sub(r'\bconst\b|[&*]', '', _qual(n)).strip()


def _key(n, source):
    from swdb.helper_windows import _span
    return (n.get('kind'), *_span(n, source), n.get('name'), _qual(n), n.get('mangledName'))


def certify(definitions, classes, *, source, tool, includes, defines, entry, windows):
    """Return (serializable context, exact emitted-AST member origins).

    An independent complete original TU binds calls/declarations; physical span
    keys join separately dumped printer ASTs. Process-local IDs never cross dumps.
    A refusal is returned only for a prospective pointer-field context; unrelated
    ordinary units keep their existing policy.
    """
    if not windows or not any(n.get('kind') == 'MemberExpr' and '*' in _qual(n)
                              for root in definitions.values() for n in _walk(root)):
        return None, {}
    from swdb.helper_windows import _Tree, _span, Refused as TreeRefused
    source = Path(source).resolve()
    try:
        tree = _Tree(source, tool, includes, defines)
        emitted = {_key(n, source): name for name, n in definitions.items()}
        emitted_mangled = {n.get('mangledName') for n in definitions.values()}
        full = {emitted[_key(n, source)]: n for n in _walk(tree.root)
                if n.get('kind') in {'FunctionDecl', 'CXXMethodDecl'} and n.get('mangledName') in emitted_mangled and
                any(c.get('kind') == 'CompoundStmt' for c in _children(n)) and
                _key(n, source) in emitted}
        if set(full) != set(definitions):
            raise Refused('member context needs exact original definitions for every retained callee')
        entry_node = full[entry]
        body, = [c for c in _children(entry_node) if c.get('kind') == 'CompoundStmt']
        candidates = [n for n in _walk(body) if n.get('kind') == 'VarDecl' and _type(n) in classes]
        if len(candidates) != 1:
            raise Refused('member context needs one automatic receiver without copies or aliases')
        obj, = candidates
        record_name = _type(obj)
        if _qual(obj) != record_name or obj.get('storageClass') or obj.get('tls'):
            raise Refused('member receiver must be one automatic object')
        records = [n for n in _walk(tree.root) if n.get('kind') == 'CXXRecordDecl' and
                   n.get('name') == record_name and n.get('completeDefinition')]
        if len(records) != 1:
            raise Refused('member receiver record is ambiguous')
        record, = records
        data = record.get('definitionData', {})
        if (record.get('tagUsed') == 'union' or record.get('bases') or not data.get('isTrivial') or
                not data.get('isStandardLayout') or any(n.get('kind', '').endswith('Attr') for n in _walk(record))):
            raise Refused('member receiver needs a trivial standard-layout record without attributes')
        fields = [n for n in _children(record) if n.get('kind') == 'FieldDecl']
        pointers = [n for n in fields if _qual(n) == 'int *']
        counts = [n for n in fields if _qual(n) == 'int']
        if len(fields) != 2 or len(pointers) != 1 or len(counts) != 1 or any(_children(n) for n in fields):
            raise Refused('member receiver needs exactly an int pointer and signed int count, without initializers')
        pointer, count = pointers[0], counts[0]
        params = {n['name']: n for n in _children(entry_node) if n.get('kind') == 'ParmVarDecl'}
        statements = _children(body)
        if (len(statements) < 4 or statements[0].get('kind') != 'DeclStmt' or
                [n.get('id') for n in _children(statements[0])] != [obj['id']]):
            raise Refused('member captures must immediately follow the first automatic receiver declaration')
        captures = []
        for statement, field in zip(statements[1:3], (pointer, count)):
            if statement.get('kind') != 'BinaryOperator' or statement.get('opcode') != '=':
                raise Refused('member captures need direct dominating pointer/count assignments')
            left, right = _children(statement)
            left, right = _strip(left), _strip(right)
            if (left.get('kind') != 'MemberExpr' or left.get('referencedMemberDecl') != field['id'] or
                    _strip(_children(left)[0]).get('referencedDecl', {}).get('id') != obj['id'] or
                    right.get('kind') != 'DeclRefExpr'):
                raise Refused('member captures must bind exact receiver fields to bare entry parameters')
            ref = right.get('referencedDecl', {})
            if ref.get('name') not in params or ref.get('id') != params[ref['name']]['id']:
                raise Refused('member capture is not an entry parameter')
            captures.append((statement, left, ref['name']))
        p_name, n_name = captures[0][2], captures[1][2]
        window = windows['windows'].get(p_name)
        if (not window or window['element_type'] != 'int' or
                window['extent_tree'] != {'kind': 'parameter', 'name': n_name} or _qual(params[n_name]) != 'int'):
            raise Refused('member capture needs the exact explicit int pointer/count entry window')
        capture_ids = {n['id'] for pair in captures for n in pair[:2]}
        captured_params = {params[p_name]['id'], params[n_name]['id']}
        full_to_name = {n['id']: name for name, n in full.items()}
        # All receiver-valued expression uses must be consumed by exact fields or
        # checked direct call receiver/argument bindings; aliases/escape are absent.
        allowed_refs, member_origins, checked_calls, calls = set(), {}, set(), []
        bindings = {entry: {obj['id']}}
        visited, active = set(), set()

        def receiver(n, bindings_for_fn):
            n = _strip(n)
            if n.get('kind') == 'CXXThisExpr' and 'this' in bindings_for_fn:
                allowed_refs.add(n['id']); return 'this', True
            if n.get('kind') == 'DeclRefExpr' and n.get('referencedDecl', {}).get('id') in bindings_for_fn:
                allowed_refs.add(n['id'])
                declaration = tree.nodes.get(n['referencedDecl']['id'], {})
                return n['referencedDecl']['name'], '&' in _qual(declaration) or '*' in _qual(declaration)
            raise Refused('member call/access uses another or untracked receiver')

        def visit(name, environment):
            if name in active:
                raise Refused('recursive member context cannot be fully inlined')
            if name in visited:
                if bindings[name] != environment:
                    raise Refused('retained callee has more than one receiver context')
                return
            active.add(name); bindings[name] = environment
            fn = full[name]
            if any(n.get('kind', '').endswith('Attr') or 'volatile' in _qual(n) for n in _walk(fn)):
                raise Refused('member context attributes/volatile source are unsupported')
            parents = {c.get('id'): n for n in _walk(fn) for c in _children(n)}
            for node in _walk(fn):
                kind, children = node.get('kind'), _children(node)
                if kind in {'CXXNewExpr', 'CXXDeleteExpr', 'CXXThrowExpr', 'LambdaExpr', 'CXXConstructExpr'}:
                    if kind != 'CXXConstructExpr' or _type(node) != record_name or children:
                        raise Refused('member context lifetime/construction effects are unsupported')
                if kind in {'BinaryOperator', 'CompoundAssignOperator', 'UnaryOperator'} and children and (
                        kind == 'CompoundAssignOperator' or node.get('opcode') in {'=', '++', '--', '&'}):
                    target = _strip(children[0])
                    if target.get('referencedDecl', {}).get('id') in captured_params:
                        raise Refused('member captured entry bindings cannot be mutated or addressed')
                    if target.get('kind') == 'MemberExpr' and target.get('referencedMemberDecl') in {pointer['id'], count['id']} and node['id'] not in capture_ids:
                        raise Refused('member pointer/count fields must remain immutable after capture')
                if kind == 'MemberExpr' and node.get('referencedMemberDecl') in {pointer['id'], count['id']}:
                    base, arrow = receiver(children[0], environment)
                    if node['id'] in capture_ids:
                        continue
                    parent = parents.get(node['id'], {})
                    if parent.get('kind') != 'ImplicitCastExpr' or parent.get('castKind') != 'LValueToRValue':
                        raise Refused('member field aliases/addresses/writes are unsupported')
                    if node.get('referencedMemberDecl') == pointer['id']:
                        use = parents.get(parent['id'], {})
                        if use.get('kind') != 'ArraySubscriptExpr' or _strip(_children(use)[0]).get('id') != node['id']:
                            raise Refused('member pointer field may only be the direct indexed base')
                        prefix = base + ('->' if arrow else '.')
                        member_origins[(name, _span(node, source))] = {
                            'kind': 'contextual_member_window', 'element_type': 'int',
                            'root': prefix + pointer['name'], 'relative_offset': '0',
                            'elements': '((integer)' + prefix + count['name'] + ')',
                            'field_guard': (f'\\valid_read(&{prefix}{pointer["name"]}) && \\initialized(&{prefix}{pointer["name"]}) && '
                                            f'\\valid_read(&{prefix}{count["name"]}) && \\initialized(&{prefix}{count["name"]})'),
                            'declarations_sha256': windows['declarations_sha256']}
                if kind in {'CallExpr', 'CXXMemberCallExpr', 'CXXOperatorCallExpr'}:
                    callee = _strip(children[0]); args = children[1:]; target_env = set()
                    if kind == 'CXXMemberCallExpr':
                        target = tree.nodes.get(callee.get('referencedMemberDecl'), {})
                        receiver(_children(callee)[0], environment); target_env.add('this')
                    else:
                        target = tree.nodes.get(callee.get('referencedDecl', {}).get('id'), {})
                        if kind == 'CXXOperatorCallExpr' and target.get('kind') == 'CXXMethodDecl':
                            receiver(args[0], environment); target_env.add('this'); args = args[1:]
                    target_name = full_to_name.get(target.get('id'))
                    if target_name is None or target.get('virtual') or target.get('isVirtual'):
                        raise Refused('member context requires a closed direct nonvirtual callee definition')
                    formals = [n for n in _children(target) if n.get('kind') == 'ParmVarDecl']
                    if len(args) != len(formals):
                        raise Refused('member context call arity differs from exact original declaration')
                    for arg, formal in zip(args, formals):
                        if _type(formal) == record_name:
                            if _qual(formal) != 'const ' + record_name + ' &':
                                raise Refused('helper receiver must be a const reference, never copied or rebound')
                            receiver(arg, environment); target_env.add(formal['id'])
                        else:
                            from swdb.c_lowering import INTEGER_TYPES, FLOAT_TYPES
                            if ('*' in _qual(formal) or '&' in _qual(formal) or
                                    _type(formal) not in INTEGER_TYPES | FLOAT_TYPES):
                                raise Refused('member context nonreceiver arguments must be primitive scalar values, never pointers/references')
                    checked_calls.add((name, _span(node, source)))
                    calls.append({'caller': name, 'callee': target_name, 'span': list(_span(node, source)),
                                  'mangled': target.get('mangledName')})
                    visit(target_name, target_env)
            for node in _walk(fn):
                if ((node.get('kind') == 'DeclRefExpr' and _type(node) == record_name) or
                        node.get('kind') == 'CXXThisExpr' and _type(node) == record_name):
                    if node['id'] not in allowed_refs:
                        raise Refused('member receiver copy, alias or escape is unsupported')
            active.remove(name); visited.add(name)
        visit(entry, {obj['id']})
        if visited != set(full):
            raise Refused('member context has retained bodies outside the closed entry call graph')
        # Receiver visitation memoization is not a path-length proof: a shared
        # callee may first be visited through a shorter path. Independently
        # compute the longest path over the complete checked call graph.
        successors = {name: set() for name in full}
        for call in calls:
            successors[call['caller']].add(call['callee'])
        heights, pending = {}, set()
        def height(name):
            if name in pending:
                raise Refused('recursive member context cannot be fully inlined')
            if name not in heights:
                pending.add(name)
                heights[name] = max((1 + height(child) for child in successors[name]), default=0)
                pending.remove(name)
            return heights[name]
        depth = height(entry)
        if depth > 2:
            raise Refused('member context exceeds independently demonstrated two-level inline depth')
        origins, handles = {}, set()
        for name, fn in definitions.items():
            for n in _walk(fn):
                span = _span(n, source) if n.get('kind') in {'MemberExpr', 'CallExpr', 'CXXMemberCallExpr', 'CXXOperatorCallExpr'} else None
                if (name, span) in member_origins:
                    origins[(name, n['id'])] = member_origins[(name, span)]
                if (name, span) in checked_calls:
                    handles.add((name, n['id']))
        if len(origins) != len(member_origins) or len(handles) != len(checked_calls):
            raise Refused('member context original/printer access or call correspondence differs')
        report = {'check': identity(), 'entry': entry, 'inline_functions': sorted(set(full) - {entry}),
                  'source_sha256': _hash(source.read_bytes()), 'declarations_sha256': windows['declarations_sha256'],
                  'receiver': {'name': obj['name'], 'span': list(_span(obj, source)), 'type': record_name},
                  'captures': [{'field': left['name'], 'parameter': param, 'span': list(_span(stmt, source))}
                               for stmt, left, param in captures],
                  'calls': sorted(calls, key=lambda c: (c['caller'], c['span'])),
                  'accesses': [{'function': name, 'span': list(span), 'origin': origin}
                               for (name, span), origin in sorted(member_origins.items())],
                  'input_premises_added': [], 'maximum_call_depth': depth, 'allowed_call_depth': 2, 'scope': 'selected entry after exact closed direct-callee inlining'}
        report['certificate_sha256'] = _hash(report)
        return report, origins
    except TreeRefused as exc:
        raise Refused(str(exc)) from None


def check(report, source_sha256):
    row = dict(report); digest = row.pop('certificate_sha256', None)
    if digest != _hash(row) or row.get('check') != identity() or row.get('source_sha256') != source_sha256:
        raise Refused('member-window context/source/checker is stale or changed')
    return report


def check_launch(lowering, policy, flags, command):
    """Pin the selected-entry proof and both parsing/WP inlining stages exactly."""
    certificate = check(lowering.pointer_bounds['member_windows'], lowering.source_sha256)
    expected = {'certificate': certificate, 'entry': certificate['entry'],
                'inline_functions': certificate['inline_functions']}
    if policy != expected:
        raise Refused('member context generated settings differ from the checked source context')
    selected = '-wp-fct=' + certificate['entry']
    inline = '-inline-calls=' + ','.join(certificate['inline_functions'])
    def options(words):
        return [str(f) for f in words if str(f).startswith(('-wp-fct', '-wp-skip-fct', '-inline-calls',
                                                         '-no-inline-calls', '-remove-inlined', '-no-remove-inlined'))]
    if options(flags) != [selected, inline]:
        raise Refused('member context needs exactly its selected entry and closed inline set')
    words = list(map(str, command))
    stages, stage = [], []
    for word in words:
        if word == '-then':
            stages.append(stage); stage = []
        else:
            stage.append(word)
    stages.append(stage)
    if len(stages) != 3 or [options(s) for s in stages] != [[inline], [selected, inline], []]:
        raise Refused('member context parse/WP command stages differ from the exact checked inlining policy')
    return expected
