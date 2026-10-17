"""Checked entry-specific pointer-field windows (2026-10-15 ET).

One trivial automatic array receiver captures immutable pointer/count fields
from an explicit entry window. An additional closed scalar/reference object may
use a checked enclosing-local lifetime. This selected-entry context never forms
a contract for an arbitrary method receiver. Ordinary init/validity/RTE remain.
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


class _ScalarLifetimes:
    """One closed automatic scalar/reference object; no pointer-origin exemptions."""
    def __init__(self, tree, full, source, entry, bag, bag_type):
        from swdb.helper_windows import _span
        self.tree, self.full, self.source, self.entry = tree, full, source, entry
        self.nodes, self.objects, self.owners, self.allowed, self.rows = tree.nodes, {}, {}, set(), []
        entry_fn = full[entry]
        body, = [n for n in _children(entry_fn) if n.get('kind') == 'CompoundStmt']
        self.parents = {n.get('id'): p for p in _walk(body) for n in _children(p)}
        record_names = {n.get('name') for n in _walk(tree.root) if n.get('kind') == 'CXXRecordDecl' and n.get('completeDefinition')}
        extras = [n for n in _walk(body) if n.get('kind') == 'VarDecl' and _type(n) in record_names and n['id'] != bag['id']]
        if len(extras) > 1:
            raise Refused('member scalar lifetime needs at most one additional automatic object')
        self.constructions = {}
        for obj in extras:
            name = _type(obj)
            records = [n for n in _walk(tree.root) if n.get('kind') == 'CXXRecordDecl' and n.get('completeDefinition') and n.get('name') == name]
            if len(records) != 1 or name == bag_type:
                raise Refused('member scalar lifetime record/copy is ambiguous')
            record, = records
            fields = [n for n in _children(record) if n.get('kind') == 'FieldDecl']
            if (not fields or record.get('bases') or record.get('tagUsed') == 'union' or
                    any(_qual(n) not in {'int', 'int &'} or _children(n) for n in fields) or
                    any(n.get('kind', '').endswith('Attr') or n.get('virtual') or n.get('isVirtual') or
                        n.get('kind') == 'VarDecl' for n in _children(record))):
                raise Refused('member scalar lifetime needs plain int/reference fields and no hidden storage/effects')
            if _qual(obj) != name or obj.get('storageClass') or obj.get('tls'):
                raise Refused('member scalar lifetime object must be automatic and unaliased')
            decl = self.parents.get(obj['id'], {})
            scope = self.parents.get(decl.get('id'), {})
            if decl.get('kind') != 'DeclStmt' or _children(decl) != [obj] or scope.get('kind') != 'CompoundStmt':
                raise Refused('member scalar lifetime needs one direct compound-scope declaration')
            # First slice has one normal block exit; no alternate lifetime edges.
            if any(n.get('kind') in {'ReturnStmt', 'BreakStmt', 'ContinueStmt', 'GotoStmt', 'IndirectGotoStmt',
                                     'CXXThrowExpr', 'LabelStmt'} for n in _walk(scope)):
                raise Refused('member scalar lifetime needs a normal scope exit without early control transfer')
            constructors = [n for n in _children(record) if n.get('kind') == 'CXXConstructorDecl' and not n.get('isImplicit')]
            destructors = [n for n in _children(record) if n.get('kind') == 'CXXDestructorDecl' and not n.get('isImplicit')]
            if len(constructors) != 1 or len(destructors) != 1:
                raise Refused('member scalar lifetime needs exact single constructor/destructor definitions')
            ctor, dtor = constructors[0], destructors[0]
            by_id = {n['id']: cname for cname, n in full.items()}
            if ctor['id'] not in by_id or dtor['id'] not in by_id:
                raise Refused('member scalar lifetime special members are not exact retained original definitions')
            init, = _children(obj)
            if (init.get('kind') != 'CXXConstructExpr' or init.get('constructionKind') != 'complete' or
                    init.get('ctorType', {}).get('qualType') != _qual(ctor)):
                raise Refused('member scalar lifetime needs exact noncopy complete construction')
            formals = [n for n in _children(ctor) if n.get('kind') == 'ParmVarDecl']
            if len(formals) != len(_children(init)) or any(_qual(n) != 'int &' for n in formals):
                raise Refused('member scalar constructor needs plain int-reference parameters')
            initializers = [n for n in _children(ctor) if n.get('kind') == 'CXXCtorInitializer']
            if {n.get('anyInit', {}).get('id') for n in initializers} != {n['id'] for n in fields} or len(initializers) != len(fields):
                raise Refused('member scalar constructor must explicitly initialize every exact field')
            ref_ids = {n['id'] for n in formals}
            for initializer in initializers:
                target = initializer.get('anyInit', {})
                if _qual(target) == 'int &':
                    value, = _children(initializer)
                    if value.get('kind') != 'DeclRefExpr' or value.get('referencedDecl', {}).get('id') not in ref_ids:
                        raise Refused('member scalar reference field must bind an exact constructor reference parameter')
            refs = []
            for actual, formal in zip(_children(init), formals):
                value = _strip(actual)
                ref = self.nodes.get(value.get('referencedDecl', {}).get('id'), {})
                parent = self.parents.get(ref.get('id'), {})
                outer = self.parents.get(parent.get('id'), {})
                ancestors = []
                current = self.parents.get(scope.get('id'), {})
                while current:
                    ancestors.append(current.get('id')); current = self.parents.get(current.get('id'), {})
                if (value.get('kind') != 'DeclRefExpr' or ref.get('kind') != 'VarDecl' or _qual(ref) != 'int' or
                        ref.get('storageClass') or ref.get('tls') or not _children(ref) or
                        parent.get('kind') != 'DeclStmt' or outer.get('id') not in ancestors or
                        _span(ref, source)[0] >= _span(obj, source)[0]):
                    raise Refused('member scalar reference requires a prior plain local in a strictly enclosing lifetime')
                refs.append({'formal': formal['name'], 'local': ref['name'], 'span': list(_span(ref, source))})
            owner = {'object': obj, 'record': record, 'field_ids': {n['id'] for n in fields},
                     'scope': scope, 'ctor': by_id[ctor['id']], 'dtor': by_id[dtor['id']]}
            self.objects[name] = owner
            for method in _children(record):
                if method.get('id') in by_id:
                    self.owners[by_id[method['id']]] = name
            self.constructions[init['id']] = owner
            self.rows.append({'object': obj['name'], 'type': name, 'span': list(_span(obj, source)),
                              'scope': list(_span(scope, source)), 'constructor': owner['ctor'],
                              'destructor': owner['dtor'], 'references': refs})
        if not self.objects:
            return
        for name, fn in full.items():
            if fn.get('kind') not in {'CXXConstructorDecl', 'CXXDestructorDecl'}:
                # Scalar helpers may not return references/addresses; the Bag
                # index method retains its separately checked array-reference policy.
                if any(n.get('id') == fn['id'] for record in _walk(tree.root)
                       if record.get('kind') == 'CXXRecordDecl' and record.get('name') == bag_type
                       for n in _children(record)):
                    continue
                result = _qual(fn).split(' (', 1)[0]
                if result not in {'int', 'void'}:
                    raise Refused('member scalar methods cannot return aliases or receiver storage')

    def receiver(self, node, function):
        node = _strip(node)
        if node.get('kind') == 'DeclRefExpr' and function == self.entry:
            ref = node.get('referencedDecl', {}).get('id')
            owner = next((n for n in self.objects.values() if n['object']['id'] == ref), None)
        elif node.get('kind') == 'CXXThisExpr' and function in self.owners:
            owner = self.objects[self.owners[function]]
        else:
            owner = None
        if owner is None:
            raise Refused('member scalar call/access uses an untracked receiver')
        self.allowed.add(node['id'])
        return owner['record']['name']

    def reference_argument(self, arg, formal, function, captured):
        """Only nonescaping scalar storage; never a pointer/count or field alias."""
        if _qual(formal) != 'int &':
            return False
        arg = _strip(arg)
        ref = self.nodes.get(arg.get('referencedDecl', {}).get('id'), {})
        if (arg.get('kind') != 'DeclRefExpr' or ref.get('id') in captured or
                function != self.entry or ref.get('kind') != 'VarDecl' or ref.get('id') not in self.parents or _qual(ref) != 'int' or
                ref.get('storageClass') or ref.get('tls')):
            raise Refused('member scalar reference arguments need exact noncaptured plain local storage')
        # No formal/reference forwarding in this first grammar; the exact local
        # binding is live throughout this direct call. Constructors additionally
        # require the strict enclosing-scope lifetime checked above.
        return True

    def inspect(self, node, function):
        kind = node.get('kind')
        if kind == 'MemberExpr':
            owner = next((n for n in self.objects.values() if node.get('referencedMemberDecl') in n['field_ids']), None)
            if owner and self.receiver(_children(node)[0], function) != owner['record']['name']:
                raise Refused('member scalar field belongs to another receiver')
        if kind == 'UnaryOperator' and node.get('opcode') == '&':
            raise Refused('member scalar lifetime does not admit address-taking/escape')
        if kind == 'VarDecl' and '&' in _qual(node):
            raise Refused('member scalar lifetime does not admit local reference aliases')

    def finish(self, full):
        for function, fn in full.items():
            for node in _walk(fn):
                if ((node.get('kind') == 'DeclRefExpr' and _type(node) in self.objects) or
                        node.get('kind') == 'CXXThisExpr' and _type(node) in self.objects):
                    if node['id'] not in self.allowed:
                        raise Refused('member scalar receiver copy, alias or escape is unsupported')


def certify(definitions, classes, *, source, tool, includes, defines, entry, windows):
    """Return (serializable context, exact emitted-AST member origins).

    An independent complete original TU binds calls/declarations; physical span
    keys join separately dumped printer ASTs. Process-local IDs never cross dumps.
    A refusal is returned only for a prospective pointer-field context; unrelated
    ordinary units keep their existing policy.
    """
    if any(n.get('kind') == 'FieldDecl' and '[' in _qual(n)
           for record in classes.values() for n in _children(record)):
        return _fixed_arrays(definitions, source=source, tool=tool, includes=includes, defines=defines, entry=entry)
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
                if n.get('kind') in {'FunctionDecl', 'CXXMethodDecl', 'CXXConstructorDecl', 'CXXDestructorDecl'} and n.get('mangledName') in emitted_mangled and
                any(c.get('kind') == 'CompoundStmt' for c in _children(n)) and
                _key(n, source) in emitted}
        if set(full) != set(definitions):
            raise Refused('member context needs exact original definitions for every retained callee')
        entry_node = full[entry]
        body, = [c for c in _children(entry_node) if c.get('kind') == 'CompoundStmt']
        pointer_records = {name for name, record in classes.items() if any(c.get('kind') == 'FieldDecl' and '*' in _qual(c) for c in _children(record))}
        candidates = [n for n in _walk(body) if n.get('kind') == 'VarDecl' and _type(n) in pointer_records]
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
        scalar = _ScalarLifetimes(tree, full, source, entry, obj, record_name)
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
                if scalar.objects:
                    scalar.inspect(node, name)
                if kind in {'CXXNewExpr', 'CXXDeleteExpr', 'CXXThrowExpr', 'LambdaExpr', 'CXXConstructExpr'}:
                    if kind == 'CXXConstructExpr' and node.get('id') in scalar.constructions:
                        lifetime = scalar.constructions[node['id']]
                        for target_name, event in ((lifetime['ctor'], 'constructor'), (lifetime['dtor'], 'destructor')):
                            event_source = node if event == 'constructor' else lifetime['scope']
                            calls.append({'caller': name, 'callee': target_name, 'span': list(_span(event_source, source)),
                                          'mangled': full[target_name].get('mangledName'), 'lifetime_event': event})
                            visit(target_name, set())
                    elif kind != 'CXXConstructExpr' or _type(node) != record_name or children:
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
                        if target.get('id') in {full[k]['id'] for k in scalar.owners}:
                            if scalar.receiver(_children(callee)[0], name) != scalar.owners[full_to_name[target['id']]]:
                                raise Refused('member scalar call binds another receiver')
                        else:
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
                            if scalar.objects and scalar.reference_argument(arg, formal, name, captured_params):
                                continue
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
        scalar.finish(full)
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
                  'scalar_lifetimes': scalar.rows, 'input_premises_added': [], 'maximum_call_depth': depth, 'allowed_call_depth': 2, 'scope': 'selected entry after exact closed direct-callee inlining'}
        report['certificate_sha256'] = _hash(report)
        return report, origins
    except TreeRefused as exc:
        raise Refused(str(exc)) from None


def _fixed_arrays(definitions, *, source, tool, includes, defines, entry):
    """Closed automatic trivial records with exact one-dimensional subobjects.

    The certificate grants structural array identity only. It grants no validity,
    initializedness, index range or function contract. Those remain RTE/WP goals
    after the exact closed call graph is inlined at its original entry.
    """
    from swdb.helper_windows import _Tree, _span, Refused as TreeRefused
    from swdb.c_lowering import INTEGER_TYPES, FLOAT_TYPES
    source = Path(source).resolve()
    primitive = INTEGER_TYPES | FLOAT_TYPES
    try:
        tree = _Tree(source, tool, includes, defines)
        keys = {_key(n, source): name for name,n in definitions.items()}
        mangled = {n.get('mangledName') for n in definitions.values()}
        full = {keys[_key(n,source)]: n for n in _walk(tree.root)
                if n.get('kind') in {'FunctionDecl','CXXMethodDecl'} and n.get('mangledName') in mangled
                and any(c.get('kind') == 'CompoundStmt' for c in _children(n))
                and _key(n,source) in keys}
        if set(full) != set(definitions) or entry not in full:
            raise Refused('fixed member context requires every exact original definition')
        by_id = {n['id']:name for name,n in full.items()}
        records, owners, field_owners = {}, {}, {}
        for record in _walk(tree.root):
            if record.get('kind') not in {'CXXRecordDecl','ClassTemplateSpecializationDecl'} or not record.get('completeDefinition'):
                continue
            methods = [n for n in _children(record) if n.get('id') in by_id]
            if not methods:
                continue
            data = record.get('definitionData',{})
            fields = [n for n in _children(record) if n.get('kind') == 'FieldDecl']
            if (record.get('tagUsed') == 'union' or record.get('bases') or not data.get('isTrivial') or
                    not data.get('isStandardLayout') or any(n.get('kind','').endswith('Attr') or
                    n.get('virtual') or n.get('isVirtual') or n.get('kind') == 'VarDecl' or
                    n.get('kind') in {'CXXConstructorDecl','CXXDestructorDecl'} and not n.get('isImplicit')
                    for n in _children(record))):
                raise Refused('fixed member context needs trivial standard-layout records without hidden effects')
            types = {_type(n) for method in methods for n in _walk(method) if n.get('kind') == 'CXXThisExpr'}
            if len(types) != 1:
                raise Refused('fixed member receiver has ambiguous instantiated type')
            typename, = types
            if typename in records:
                raise Refused('fixed member receiver record is ambiguous')
            arrays = {}
            for field in fields:
                match = re.fullmatch(r'(.+)\[(\d+)\]',_qual(field))
                if match and match[1].strip() in primitive and int(match[2]) > 0:
                    arrays[field['id']] = (match[1].strip(),int(match[2]))
                elif _qual(field) not in primitive or _children(field):
                    raise Refused('fixed member fields need plain scalars or exact one-dimensional primitive arrays')
                field_owners[field['id']] = typename
            if not arrays:
                raise Refused('fixed member receiver has no exact primitive array')
            records[typename] = {'record':record,'arrays':arrays}
            owners.update((by_id[n['id']],typename) for n in methods)
        if not records or entry in owners:
            raise Refused('fixed member arrays need a separate closed automatic-object entry')
        body, = [n for n in _children(full[entry]) if n.get('kind') == 'CompoundStmt']
        objects, object_rows = {}, []
        for stmt in _children(body):
            for obj in _children(stmt) if stmt.get('kind') == 'DeclStmt' else []:
                if _type(obj) not in records:
                    continue
                init = _children(obj)
                if (_qual(obj) != _type(obj) or obj.get('storageClass') or obj.get('tls') or
                        _children(stmt) != [obj] or len(init) != 1 or init[0].get('kind') != 'CXXConstructExpr' or
                        init[0].get('constructionKind') != 'complete' or _children(init[0])):
                    raise Refused('fixed member object needs direct trivial automatic construction without copy/alias')
                objects[obj['id']] = _type(obj)
                object_rows.append({'name':obj['name'],'type':_type(obj),'span':list(_span(obj,source))})
        if set(objects.values()) != set(records):
            raise Refused('fixed member records need exact automatic objects in the selected entry')
        allowed, access_origins, calls = set(), {}, []
        successors = {name:set() for name in full}
        def receiver(node, function, expected):
            node = _strip(node)
            actual = objects.get(node.get('referencedDecl',{}).get('id')) if function == entry and node.get('kind') == 'DeclRefExpr' else (
                owners.get(function) if node.get('kind') == 'CXXThisExpr' else None)
            if actual != expected:
                raise Refused('fixed member access/call needs an exact live automatic receiver')
            allowed.add(node['id'])
            return 'this->' if node.get('kind') == 'CXXThisExpr' else node['referencedDecl']['name']+'.'
        for name, fn in full.items():
            if _qual(fn).split(' (',1)[0] not in primitive | {'void'}:
                raise Refused('fixed member helpers must return primitive values, never aliases')
            parents = {n['id']:p for p in _walk(fn) for n in _children(p) if 'id' in n}
            for node in _walk(fn):
                kind, parts = node.get('kind'), _children(node)
                if (kind.endswith('Attr') or 'volatile' in _qual(node) or
                        kind in {'CXXNewExpr','CXXDeleteExpr','LambdaExpr','GotoStmt','CXXThrowExpr'} or
                        kind == 'UnaryOperator' and node.get('opcode') == '&' or
                        kind in {'ParmVarDecl','VarDecl'} and _qual(node) not in primitive and node.get('id') not in objects):
                    raise Refused('fixed member context cannot admit aliases, opaque storage or lifetime effects')
                if kind == 'CXXConstructExpr' and not (name == entry and any(_children(tree.nodes[oid]) == [node] for oid in objects)):
                    raise Refused('fixed member context cannot admit copies or extra construction')
                if kind == 'MemberExpr' and node.get('referencedMemberDecl') in field_owners:
                    typename = field_owners[node['referencedMemberDecl']]
                    prefix = receiver(parts[0],name,typename)
                    shape = records[typename]['arrays'].get(node['referencedMemberDecl'])
                    if shape:
                        parent = parents.get(node['id'],{})
                        use = parents.get(parent.get('id'),{})
                        if (parent.get('kind') != 'ImplicitCastExpr' or parent.get('castKind') != 'ArrayToPointerDecay' or
                                use.get('kind') != 'ArraySubscriptExpr' or _children(use)[0].get('id') != parent.get('id')):
                            raise Refused('fixed member arrays may only be the direct indexed subobject base')
                        access_origins[(name,_span(node,source))] = {'kind':'one_dimensional_array',
                            'name':prefix+node['name'],'element_type':shape[0],'elements':shape[1],
                            'subobject_type':typename,'subobject_field':node['name']}
                if kind in {'CallExpr','CXXMemberCallExpr','CXXOperatorCallExpr'}:
                    callee = _strip(parts[0])
                    target = tree.nodes.get(callee.get('referencedMemberDecl') if kind == 'CXXMemberCallExpr' else
                                            callee.get('referencedDecl',{}).get('id'),{})
                    target_name = by_id.get(target.get('id'))
                    if target_name is None or kind == 'CXXOperatorCallExpr':
                        raise Refused('fixed member context requires exact closed direct callees')
                    if target_name in owners:
                        if kind != 'CXXMemberCallExpr':
                            raise Refused('fixed member call needs direct receiver syntax')
                        receiver(_children(callee)[0],name,owners[target_name])
                    elif kind != 'CallExpr':
                        raise Refused('fixed member callee owner differs from the original call')
                    successors[name].add(target_name)
                    calls.append({'caller':name,'callee':target_name,'span':list(_span(node,source)),
                                  'mangled':target.get('mangledName')})
            for node in _walk(fn):
                if ((node.get('kind') == 'DeclRefExpr' and _type(node) in records) or node.get('kind') == 'CXXThisExpr') and node['id'] not in allowed:
                    raise Refused('fixed member receiver copy, alias, escape or arbitrary input is unsupported')
        heights, pending, visited = {}, set(), set()
        def height(name):
            if name in pending:
                raise Refused('recursive fixed member context cannot be fully inlined')
            if name not in heights:
                pending.add(name); visited.add(name)
                heights[name] = max((1+height(c) for c in successors[name]),default=0)
                pending.remove(name)
            return heights[name]
        depth = height(entry)
        if visited != set(full) or depth > 2:
            raise Refused('fixed member context must be closed at the demonstrated two-level inline depth')
        origins = {}
        for name,fn in definitions.items():
            for node in _walk(fn):
                if node.get('kind') == 'MemberExpr' and (name,_span(node,source)) in access_origins:
                    origins[(name,node['id'])] = access_origins[(name,_span(node,source))]
        if len(origins) != len(access_origins):
            raise Refused('fixed member original/printer subobject correspondence differs')
        report = {'check':identity(),'protocol':'closed-automatic-fixed-member-arrays-1','entry':entry,
                  'inline_functions':sorted(set(full)-{entry}),'source_sha256':_hash(source.read_bytes()),
                  'receivers':object_rows,'calls':calls,'accesses':[{'function':name,'span':list(span),'origin':origin}
                    for (name,span),origin in sorted(access_origins.items())],
                  'input_premises_added':[],'maximum_call_depth':depth,'allowed_call_depth':2,
                  'scope':'selected entry after exact closed direct-callee inlining'}
        report['certificate_sha256'] = _hash(report)
        return report,origins
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
