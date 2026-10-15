"""Checked primitive bounded entry-window views; created 2026-10-15 ET.

The first slice admits a single straight-line primitive function. The generated
numerical checks are identical in lowered C and source C++ differential/replay.
Typed input windows remain explicit contract premises. This is not a model,
helper-call or general source-language admission path.
"""
import ast
import hashlib
import re
from pathlib import Path

from swdb import array_domains, c_lowering, cbmc_translator as tr, wp_pointer_bounds


class Refused(ValueError):
    pass


def identity():
    return {'id': 'swdb-bounded-entry-windows-1',
            'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _tree(text):
    # This consumes only the closed, freshly regenerated source checker's math
    # language. It never interprets candidate-supplied C or arbitrary ACSL.
    text = re.sub(r'\(integer\)', '', text)
    if not re.fullmatch(r'[A-Za-z_0-9\s()+*-]+', text, re.ASCII):
        raise Refused('bounded window target needs pure integer arithmetic')
    try:
        parsed = ast.parse(text, mode='eval')
    except (SyntaxError, ValueError, RecursionError):
        raise Refused('bounded window target needs pure integer arithmetic') from None
    if len(list(ast.walk(parsed))) > 128:
        raise Refused('bounded window target is too large')

    def visit(n):
        if isinstance(n, ast.Name):
            return {'kind': 'parameter', 'name': n.id}
        if isinstance(n, ast.Constant) and type(n.value) is int and 0 <= n.value <= 2**64 - 1:
            return {'kind': 'constant', 'value': n.value}
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            child = visit(n.operand)
            return child if isinstance(n.op, ast.UAdd) else {
                'kind': 'sub', 'left': {'kind': 'constant', 'value': 0}, 'right': child}
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult)):
            return {'kind': {ast.Add: 'add', ast.Sub: 'sub', ast.Mult: 'mul'}[type(n.op)],
                    'left': visit(n.left), 'right': visit(n.right)}
        raise Refused('bounded window target needs pure integer arithmetic')

    return visit(parsed.body)


def _render(tree, bounds):
    # Check EVERY intermediate, not merely the final interval: cancellation
    # must not hide overflow of the fixed-width representation of mathematics.
    try:
        low, high = array_domains.interval(tree, bounds)
    except array_domains.Refused as exc:
        raise Refused(str(exc)) from None
    if low < -(2**127) or high > 2**127 - 1:
        raise Refused('bounded window mathematical intermediate exceeds signed 128-bit representation')
    kind = tree['kind']
    if kind == 'constant':
        return f'((__int128){tree["value"]}ULL)'
    if kind == 'parameter':
        return f'((__int128){tree["name"]})'
    sign = {'add': '+', 'sub': '-', 'mul': '*'}[kind]
    return f'({_render(tree["left"], bounds)} {sign} {_render(tree["right"], bounds)})'


def _span(node):
    span = node.get('range') or {}
    begin, end = span.get('begin') or {}, span.get('end') or {}
    if (any(k in begin or k in end for k in ('includedFrom', 'spellingLoc', 'expansionLoc'))
            or type(begin.get('offset')) is not int or type(end.get('offset')) is not int
            or type(end.get('tokLen')) is not int):
        raise Refused('bounded windows need direct main-source byte ranges')
    return begin['offset'], end['offset'] + end['tokLen']


def prepare(lowering, source, planner, *, defines=()):
    """Return generated C, instrumented source function and a checked view report.

    The caller must freshly lower and regenerate this view before every real
    launch. No certificate loaded from disk is accepted as a source plan.
    """
    source = Path(source)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != lowering.source_sha256:
        raise Refused('bounded entry-window source changed after lowering')
    # Reserve across the whole source, including macros and globals outside
    # the selected function. A new local must never hide an existing binding.
    if re.search(rb'\bswdb_window_[A-Za-z_0-9]*\b', raw):
        raise Refused('source uses a reserved bounded-window instrumentation name')
    try:
        report = wp_pointer_bounds.check(lowering)
    except wp_pointer_bounds.Refused as exc:
        raise Refused(str(exc)) from None
    bound = report.get('entry_windows') or {}
    if (not bound.get('windows') or planner.get('declarations_sha256') != bound.get('declarations_sha256')
            or planner.get('check') != array_domains.identity()):
        raise Refused('bounded window planner and source declarations differ')
    if lowering.models or lowering.summaries or lowering.probes or lowering.std_models or report.get('owner'):
        raise Refused('bounded primitive windows do not admit models, summaries, helpers or owners')
    functions = [a['function'] for a in lowering.anchors if a['kind'] == 'contract']
    if functions != [lowering.function]:
        raise Refused('bounded primitive windows require one function without helper calls')
    tool = c_lowering.locate()
    nodes = c_lowering._named(c_lowering._dump(tool, source, lowering.function, (), tuple(defines)),
                              lowering.function, {'FunctionDecl'})
    nodes = [n for n in nodes if any(c.get('kind') == 'CompoundStmt' for c in n.get('inner', []))]
    if len(nodes) != 1:
        raise Refused('bounded windows need one exact source function definition')
    node = nodes[0]
    if any(c.get('kind', '').endswith('Attr') for c in node.get('inner', [])):
        raise Refused('bounded primitive windows require an attribute-free source function')
    start, end = _span(node)
    body = next(c for c in node['inner'] if c.get('kind') == 'CompoundStmt')
    body_start, body_end = _span(body)
    expected = {'begin': start, 'end': end, 'body_begin': body_start, 'body_end': body_end}
    source_map = (report.get('source_functions') or {}).get(lowering.function)
    if source_map != expected:
        raise Refused('bounded window function source map is absent or stale')
    statements = [c for c in body.get('inner', []) if c.get('kind')]
    allowed = {'DeclStmt', 'ReturnStmt', 'CStyleCastExpr', 'ImplicitCastExpr', 'BinaryOperator', 'NullStmt'}
    if any(c['kind'] not in allowed for c in statements):
        raise Refused('bounded primitive windows currently require a straight-line function body')
    scalar_bounds = {}
    names = set()
    for child in wp_pointer_bounds._walk(node):
        kind = child.get('kind', '')
        referenced = child.get('referencedDecl') or {}
        if str(referenced.get('name', '')).startswith('swdb_window_'):
            raise Refused('source references a reserved bounded-window instrumentation name')
        if 'volatile' in (child.get('type') or {}).get('qualType', ''):
            raise Refused('bounded primitive windows do not add checks to volatile source operations')
        if kind in {'CallExpr', 'CXXMemberCallExpr', 'CXXOperatorCallExpr', 'LambdaExpr',
                    'StmtExpr', 'ConditionalOperator', 'BinaryConditionalOperator', 'CompoundStmt'} and child is not body:
            raise Refused('bounded primitive windows do not admit calls or nested control')
        if kind in {'VarDecl', 'ParmVarDecl'}:
            name = child.get('name', '')
            if name in names or name.startswith('swdb_window_'):
                raise Refused('bounded window source shadows or reserves an instrumentation name')
            names.add(name)
            qual = ' '.join(re.sub(r'\bconst\b', '', (child.get('type') or {}).get('qualType', '')).split())
            if qual in c_lowering.INTEGER_TYPES:
                scalar_bounds[name] = tr._integer_draw_bounds(qual)
    additions, checks = {}, []
    entry = []
    for index, (name, window) in enumerate(bound['windows'].items(), 1):
        planned = planner.get('windows', {}).get(name) or {}
        if any(planned.get(k) != v for k, v in window.items()):
            raise Refused('bounded window planner binding differs from source binding')
        cap = planned.get('physical_capacity')
        low, high = planned.get('extent_interval', [None, None])
        if type(cap) is not int or type(low) is not int or type(high) is not int or not 0 <= low <= high <= cap:
            raise Refused('bounded window extent does not fit its nonnull physical buffer')
        expression = _render(window['extent_tree'], planner.get('scalar_intervals', {}))
        snapshot = f'swdb_window_extent_{name}'
        entry += [f'const __int128 {snapshot} = {expression};',
                  f'SWDB_PROP(0 <= {snapshot} && {snapshot} <= (__int128){cap}ULL && '
                  f'{snapshot} <= (__int128)(SIZE_MAX / sizeof({window["element_type"]})), '
                  f'"swdb_window_entry_{index}");']
    additions[f'{lowering.function}.entry'] = entry
    cpp_additions = {body_start + 1: entry}
    placements = {_span(stmt): i for i, stmt in enumerate(statements, 1)}
    for index, row in enumerate(report['sites'], 1):
        origin = row.get('origin') or {}
        if row.get('admission_only') or row.get('kind') not in {None, 'access'} or origin.get('kind') != 'entry_window':
            raise Refused('bounded primitive windows need a checked entry origin for every operation')
        name = origin.get('parameter')
        if name not in bound['windows'] or row.get('function') != lowering.function:
            raise Refused('bounded operation is outside the declared entry function')
        match = re.fullmatch(re.escape(lowering.function) + r'\.s([1-9][0-9]*)\.before', row.get('anchor', ''))
        ordinal = int(match[1]) if match else 0
        if not 1 <= ordinal <= len(statements):
            raise Refused('bounded operation has no direct source statement anchor')
        position = _span(statements[ordinal - 1])
        span = {'begin': position[0], 'end': position[1]}
        declared_span = row.get('source_statement')
        if (declared_span != span
                or position not in placements or row.get('anchor') != f'{lowering.function}.s{placements[position]}.before'):
            raise Refused('bounded operation is not at its exact direct source statement')
        guard = row.get('window_guard', '')
        target = relation = None
        for op in ('<=', '<'):
            suffix = f') {op} ({origin["elements"]})'
            if guard.startswith('0 <= (') and guard.endswith(suffix):
                target, relation = guard[len('0 <= ('):-len(suffix)], op
                break
        if target is None:
            raise Refused('bounded window operation has no closed numerical guard')
        expression = _render(_tree(target), scalar_bounds)
        label = f'swdb_window_{"access" if row.get("kind") == "access" else "formation"}_{index}'
        check = (f'SWDB_PROP(0 <= ({expression}) && ({expression}) {relation} '
                 f'swdb_window_extent_{name}, "{label}");')
        additions.setdefault(row['anchor'], []).append(check)
        cpp_additions.setdefault(position[0], []).append(check)
        checks.append({'property': label, 'anchor': row['anchor'], 'source_statement': span,
                       'parameter': name, 'relation': relation})
    c_text = lowering.text
    for anchor, lines in additions.items():
        marker = f'/* swdb-anchor {anchor} */'
        if c_text.count(marker) != 1:
            raise Refused('bounded window check anchor is absent or duplicated')
        c_text = c_text.replace(marker, marker + '\n' + '\n'.join(lines))
    cpp = raw[start:end]
    for offset, lines in sorted(cpp_additions.items(), reverse=True):
        if not start <= offset < end:
            raise Refused('bounded source insertion is outside its function')
        where = offset - start
        cpp = cpp[:where] + ('\n' + '\n'.join(lines) + '\n').encode() + cpp[where:]
    audit = dict(planner, admission='checked_primitive_source_operations', source_operations_checked=True,
                 operation_check=identity(), source_functions={lowering.function: expected}, operations=checks,
                 integer_model='checked signed __int128 representation of every mathematical intermediate',
                 restriction='nonnull bounded buffers; one straight-line primitive function; no imported domains or calls',
                 entry_window_semantics={'role': 'explicit typed-window input-contract premise; not inferred from validity',
                     'checked': 'entry extent/target capacity and every admitted formation/access numerical bound',
                     'representation': 'nonnull physical harness buffers; logical extent can be smaller than capacity',
                     'caller_boundary': 'no helper, imported summary, model or whole-function domain admission'},
                 source_sha256=lowering.source_sha256,
                 c_view_sha256=hashlib.sha256(c_text.encode()).hexdigest(),
                 cxx_function_sha256=hashlib.sha256(cpp).hexdigest())
    return c_text, cpp.decode(), audit
