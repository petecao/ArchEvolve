"""Source-backed pending caller obligations for v3; created 2026-10-16 ET.

This compiler certificate never grants an origin, assumes a precondition or
selects the qualified model. The body/dependency/liveness proofs remain pending.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb import vector_reallocation_model as model


class Refused(ValueError):
    pass


def identity():
    return {'id': 'vector-reallocation-caller-check-1',
            'sha256': hashlib.sha256(Path(__file__).read_bytes() +
                Path(__file__).with_name('vector_reallocation_caller_vcs.py').read_bytes() +
                Path(__file__).with_name('vector_reallocation_lifetime.py').read_bytes() +
                Path(__file__).with_name('vector_reallocation_capacity.py').read_bytes()).hexdigest()}


def children(node):
    return [c for c in node.get('inner', []) if isinstance(c, dict) and c.get('kind')]


def ctype(node):
    t = node.get('type', {})
    return t.get('desugaredQualType', t.get('qualType', ''))


def strip(node):
    wrappers = {'ExprWithCleanups', 'MaterializeTemporaryExpr', 'ParenExpr', 'ImplicitCastExpr', 'CStyleCastExpr'}
    while node.get('kind') in wrappers:
        parts = children(node)
        if len(parts) != 1:
            raise Refused('a single checked expression wrapper is required')
        if node.get('kind') in {'ImplicitCastExpr', 'CStyleCastExpr'}:
            cast = node.get('castKind')
            if cast not in {'NoOp', 'LValueToRValue', 'IntegralCast'} or \
                    (cast == 'IntegralCast' and ctype(node) != 'unsigned long'):
                raise Refused('only exact size_t widening and value-preserving wrappers are supported')
        node = parts[0]
    return node


def ref(node, declaration):
    node = strip(node)
    return node.get('kind') == 'DeclRefExpr' and node.get('referencedDecl', {}).get('id') == declaration.get('id')


def literal(node, value):
    node = strip(node)
    return node.get('kind') == 'IntegerLiteral' and int(node['value']) == value


def decl(statement):
    parts = children(statement)
    if statement.get('kind') != 'DeclStmt' or len(parts) != 1 or parts[0].get('kind') != 'VarDecl':
        raise Refused('one automatic local declaration is required')
    node = parts[0]
    if node.get('storageClass') or node.get('tls') or len(children(node)) != 1:
        raise Refused('the receiver and alias must be automatic initialized locals')
    return node, strip(children(node)[0])


def member(node, name, owner):
    node = strip(node)
    parts = children(node)
    if node.get('kind') != 'CXXMemberCallExpr' or not parts:
        raise Refused('a direct source vector member call is required')
    target = parts[0]
    objects = children(target)
    if target.get('kind') != 'MemberExpr' or target.get('name') != name or target.get('isArrow') or \
            len(objects) != 1 or not ref(objects[0], owner):
        raise Refused('the unchanged automatic receiver must own the direct member call')
    return parts[1:]


def span(node, source):
    raw = source.encode()
    area = node.get('range', {})
    start = area.get('begin', {}).get('offset')
    end = area.get('end', {})
    stop = end.get('offset', -1) + end.get('tokLen', 0)
    if start is None or not 0 <= start < stop <= len(raw):
        raise Refused('a complete physical source span is required')
    return {'begin': start, 'end': stop,
            'sha256': hashlib.sha256(raw[start:stop]).hexdigest()}


def certify(node, *, source, text, defines, models, provenance):
    body = next((c for c in children(node) if c.get('kind') == 'CompoundStmt'), {})
    def walk(n):
        yield n
        for c in children(n):
            yield from walk(c)
    if not any(n.get('kind') == 'MemberExpr' and n.get('name') == 'reserve' for n in walk(body)):
        return {}
    base = {'checker': identity(), 'candidate_only': True, 'caller_domain': 'obligations to prove; not assumptions',
            'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'lowered_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'original_caller_premises_added': [], 'known_origins_granted': [],
            'qualified_model_candidate': model.identity(), 'qualified_models_required': sorted(model.MEMBERS),
            'selected_models': 'original v2; qualified v3 proof admission is pending'}
    try:
        if defines or re.search(r'\boperator\s*(?:new|delete)\b|\bnamespace\s+std\b', source):
            raise Refused('build defines and replacement allocation/standard definitions are unsupported')
        for directive in re.findall(r'^\s*#.*$', source, re.M):
            if not re.fullmatch(r'\s*#\s*include\s*<(?:vector|cstddef)>\s*', directive):
                raise Refused('only the pinned vector/cstddef includes are supported')
        params = [c for c in children(node) if c.get('kind') == 'ParmVarDecl']
        if len(params) != 1 or ctype(params[0]) != 'int' or ctype(node) != 'int (int)':
            raise Refused('one scalar int count and an int return are required')
        count = params[0]
        statements = children(body)
        if len(statements) != 4:
            raise Refused('expected construction, capture, reserve and guarded return only')
        receiver, ctor = decl(statements[0])
        typename = re.sub(r'\s+', '', ctype(receiver)).replace('std::__1::', 'std::')
        if typename not in {'std::vector<int>', 'std::vector<int,std::allocator<int>>'}:
            raise Refused('only the declared int vector candidate is supported')
        args = children(ctor)
        if ctor.get('kind') != 'CXXConstructExpr' or len(args) != 2 or not ref(args[0], count) or not literal(args[1], 7):
            raise Refused('count/value construction must use the unchanged count and literal seven')
        alias, capture = decl(statements[1])
        if ctype(alias) != 'int *' or member(capture, 'data', receiver):
            raise Refused('one unchanged data alias must be captured')
        reserve = member(statements[2], 'reserve', receiver)
        if len(reserve) != 1:
            raise Refused('reserve requires exactly one source count expression')
        request, arg = None, strip(reserve[0])
        if ref(arg, count):
            request = 'count'
        elif arg.get('kind') == 'BinaryOperator' and arg.get('opcode') == '+' and \
                ctype(arg) == 'unsigned long' and len(children(arg)) == 2:
            left, right = children(arg)
            if ref(left, count) and literal(right, 1):
                request = 'count+1'
        if request is None:
            raise Refused('only exact count or widened count+1 is supported')
        returned = children(statements[3])
        if statements[3].get('kind') != 'ReturnStmt' or len(returned) != 1:
            raise Refused('one immediate guarded scalar return is required')
        choice = strip(returned[0])
        parts = children(choice)
        if choice.get('kind') != 'ConditionalOperator' or len(parts) != 3:
            raise Refused('empty storage must be guarded by count>0')
        condition, observed, empty = parts
        condition = strip(condition)
        if condition.get('kind') != 'BinaryOperator' or condition.get('opcode') != '>' or \
                len(children(condition)) != 2 or not ref(children(condition)[0], count) or \
                not literal(children(condition)[1], 0) or not literal(empty, 0):
            raise Refused('the exact count>0 guard and zero empty return are required')
        observed = strip(observed)
        values = children(observed)
        observation = None
        if observed.get('kind') == 'UnaryOperator' and observed.get('opcode') == '*' and \
                len(values) == 1 and ref(values[0], alias):
            observation = 'captured alias'
        elif observed.get('kind') == 'CXXOperatorCallExpr' and len(values) == 3 and ref(values[1], receiver) and literal(values[2], 0):
            function = values[0]
            if function.get('kind') == 'ImplicitCastExpr' and function.get('castKind') == 'FunctionToPointerDecay' and len(children(function)) == 1:
                function = children(function)[0]
            function = strip(function)
            if function.get('kind') == 'DeclRefExpr' and function.get('referencedDecl', {}).get('name') == 'operator[]':
                observation = 'current buffer'
        if observation is None:
            raise Refused('only current element zero or the unchanged captured alias may be observed')
        required = {'std_vector_int_ctor_count_value', 'std_vector_int_data', 'std_vector_int_reserve', 'std_vector_int_dtor'}
        if observation == 'current buffer':
            required.add('std_vector_int_operator_index')
        if not required <= set(models) or not provenance:
            raise Refused('complete original model and header provenance is required')
        calls = [('ctor_count_value', statements[0]), ('data', capture), ('reserve', statements[2])]
        if observation == 'current buffer':
            calls.append(('operator_index', observed))
        calls.append(('dtor', node))
        base.update(verdict='pending', count={'name':count['name'],'type':'int','source':span(count,source)},
                    receiver={'name': receiver['name'], 'storage': 'automatic local object',
                    'source': span(statements[0], source)}, alias={'name': alias['name'], 'source': span(statements[1], source)},
                    reserve_request=request, observation=observation, guard='count>0',
                    entry_obligations=[{'property': '0 <= ' + count['name'], 'status': 'pending'}],
                    call_obligations=[{'call': call, 'status': 'pending', 'source': span(statement, source)}
                                      for call, statement in calls],
                    scalar_read_obligation={'status': 'pending', 'path': 'count>0', 'observed': observation,
                                            'source': span(observed, source)},
                    stdlib_binding_sha256=hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest())
        from swdb import vector_reallocation_caller_vcs, vector_reallocation_lifetime, vector_reallocation_capacity
        base['capacity_qualification']=vector_reallocation_capacity.bind(provenance)
        base['lowered_lifetime']=vector_reallocation_lifetime.certify(
            text,node['name'],count['name'],receiver['name'],alias['name'],request,observation)
        base['heap_lifetime_plan'] = vector_reallocation_caller_vcs.prepare(base)
        return base
    except (Refused, KeyError, ValueError) as exc:
        return {**base, 'verdict': 'refused', 'reason': str(exc)}
