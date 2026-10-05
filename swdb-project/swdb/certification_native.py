"""Native-CPU candidate-artifact certification (certify 1.4). Created: 2026-10-05 ET (ticket 75).

Agent-decided under Yan-Ru's 2026-10-05 delegation; revisable.

Certify 1.3 (ticket 70) certifies DX100 rewrites: a strict functional layer, two tile sizes and
the DX100 library seams. A native-CPU rewrite of the fork's scalar TDStep (an Extensa native
campaign's output) calls no DX100 intrinsic and is timed with the frozen native build flags, so it
needs its own matrix. A rewrite contract selects this path by pinning a native candidate profile
(``certification_profile``, format ``swdb.native-candidate-profile.v1``). The profile names:

* the matrix: build configurations (the frozen native protocol's ``-O3`` flags and an ``-O1 -g``
  build), thread counts and the five certification graphs of ``swdb.certification.matrix_graphs``;
* the negative controls, each a fault in ``library/native/certification/seams.cc`` with the named
  check that must reject it;
* the rewrite scope (only the body of one function may change) and the evaluator's frontier hook.

Isolation is ticket 70's, unchanged in kind: the candidate translation unit is compiled once per
build configuration with a forced prelude and an evaluator-owned ``main``; the positive matrix and
every control link that same object, and a fault macro reaches only the seam object. Every check is
computed out of process from the evaluator records (``swdb.certification_isolation.judge``), with
the native execution witness (claims and pushes through the contract's seams). The harness scan
refuses candidate-authored lines that name harness symbols.

This is pre-check evidence on the certifying host (ADR 0008); the target correctness check stays
the evaluator's compiled verifier on every timed trial on mbit10.
"""
from __future__ import annotations

import difflib
from pathlib import Path

from swdb import artifacts, yamlio
from swdb.cli import Failure, UsageError

PROFILE_FORMAT = 'swdb.native-candidate-profile.v1'
_PROFILE_FIELDS = {'format', 'id', 'entry', 'date', 'target', 'kernel', 'harness', 'harness_v14', 'matrix', 'controls',
                   'required_categories', 'rewrite_scope', 'instrumentation', 'execution_witness', 'notes'}
_HARNESS_FIELDS = {'prelude', 'record', 'seams', 'driver'}
_MATRIX_FIELDS = {'builds', 'threads', 'graphs', 'control_threads', 'control_graph', 'fault_batch', 'sources'}
_CONTROL_FIELDS = {'id', 'category', 'macro', 'expected_check', 'emulates', 'graph'}
CHECKS = ('verifier', 'frontier_size_equality', 'duplicate_frontier', 'execution_witness')
CATEGORIES = ('index_bounds', 'dropped_operand', 'aliasing', 'double_claim', 'overlapping_pointer',
              'ordering', 'capacity')
MATRIX_GRAPHS = ('kronecker-10', 'kronecker-14', 'kronecker-16', 'uniform-14', 'two-level-degree-17000')
#: Control-only graphs (ticket 75 review). staging-tail-17: source 0 -> vertices 1..17, vertex i -> leaf 17 + i.
#: The second window holds 17 vertices in push order 1..17 (one thread expands the source), so a dropped
#: final partial batch of a 16-lane staging loses exactly vertex 17 and its unique leaf.
CONTROL_GRAPHS = ('staging-tail-17',)


def positive_runs(spec, graphs, controls):
    """(threads, graph name) of every positive cell: the matrix, plus each control-only graph at the
    controls' thread count, so no control runs on an input that no positive run uses (ticket 75 review)."""
    runs = [(threads, name) for threads in spec['threads'] for name, _ in graphs]
    extra = sorted({c.get('graph') for c in controls} - {name for name, _ in graphs} - {None})
    return runs + [(spec['control_threads'], name) for name in extra]


def staging_tail_graph(path, width=17):
    import struct
    nodes = 1 + 2 * width
    rows = [list(range(1, width + 1))] + [[width + i] for i in range(1, width + 1)] + [[] for _ in range(width)]
    inverse = [[] for _ in range(nodes)]
    for u, row in enumerate(rows):
        for v in row:
            inverse[v].append(u)
    edges = sum(map(len, rows))
    with Path(path).open('wb') as stream:
        stream.write(struct.pack('<Bii', 1, edges, nodes))
        for adjacency in (rows, inverse):
            offset = 0
            stream.write(struct.pack('<i', offset))
            for row in adjacency:
                offset += len(row)
                stream.write(struct.pack('<i', offset))
            for row in adjacency:
                if row:
                    stream.write(struct.pack('<' + 'i' * len(row), *row))


def _closed(value, fields, where, optional=frozenset()):
    if not isinstance(value, dict):
        raise UsageError(f'native candidate profile: {where} must be a mapping')
    missing, unknown = fields - set(optional) - set(value), set(value) - fields
    if missing or unknown:
        raise UsageError(f'native candidate profile: {where} fields differ (missing {sorted(missing)}, '
                         f'unknown {sorted(unknown)})')
    return value


def is_native(entry):
    """True for a rewrite contract that pins a native candidate profile."""
    return isinstance(entry, dict) and entry.get('kind') == 'rewrite_contract' and \
        isinstance(entry.get('certification_profile'), dict)


def load_profile(catalog, entry):
    """The pinned profile of a native contract, checked against its pins and the contract."""
    pin = entry['certification_profile']
    try:
        catalog._pin(pin)
        path = catalog.resolve(pin)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise UsageError('native candidate profile pin: ' + str(exc)) from None
    data = yamlio.load(path)
    _closed(data, _PROFILE_FIELDS, 'profile', optional={'notes'})
    if data['format'] != PROFILE_FORMAT or data['entry'] != entry['id'] or data['target'] != 'native_cpu':
        raise UsageError('native candidate profile names another format, entry or target')
    if data['kernel'] != (entry.get('correctness_check') or {}).get('kernel'):
        raise UsageError('native candidate profile kernel differs from the contract correctness check')
    harness = _closed(data['harness'], _HARNESS_FIELDS, 'harness')
    resolved = {}
    for name, item in harness.items():
        try:
            catalog._pin({**item, 'root': 'library'})
            resolved[name] = catalog.resolve({**item, 'root': 'library'})
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise UsageError(f'native candidate profile harness {name}: {exc}') from None
    matrix = _closed(data['matrix'], _MATRIX_FIELDS, 'matrix')
    builds = matrix['builds']
    if not isinstance(builds, list) or not builds or any(
            not isinstance(b, dict) or set(b) - {'id', 'flags', 'note'} or not b.get('id')
            or not isinstance(b.get('flags'), list) or not all(isinstance(f, str) and f.startswith('-') for f in b['flags'])
            for b in builds):
        raise UsageError('native candidate profile builds need an id and a flag list')
    if len({b['id'] for b in builds}) != len(builds):
        raise UsageError('native candidate profile build IDs repeat')
    threads = matrix['threads']
    if not isinstance(threads, list) or not threads or any(type(t) is not int or t < 1 for t in threads):
        raise UsageError('native candidate profile threads must be positive integers')
    if list(matrix['graphs']) != list(MATRIX_GRAPHS) or matrix['control_graph'] not in MATRIX_GRAPHS:
        raise UsageError('native candidate profile graphs must be the certification graphs')
    if type(matrix['control_threads']) is not int or matrix['control_threads'] < 2:
        raise UsageError('native candidate controls run with at least two threads')
    if type(matrix['fault_batch']) is not int or matrix['fault_batch'] < 1:
        raise UsageError('native candidate profile fault_batch must be a positive integer')
    sources = matrix['sources']
    if not isinstance(sources, list) or not sources or any(type(s) is not int or s < 0 for s in sources):
        raise UsageError('native candidate profile sources must be nonnegative vertex IDs')
    controls = data['controls']
    if not isinstance(controls, list) or not controls:
        raise UsageError('native candidate profile needs negative controls')
    for control in controls:
        _closed(control, _CONTROL_FIELDS, 'control', optional={'emulates', 'graph'})
        if control.get('graph', matrix['control_graph']) not in MATRIX_GRAPHS + CONTROL_GRAPHS:
            raise UsageError(f"native candidate control {control['id']} names an unknown graph")
        if control['category'] not in CATEGORIES or control['expected_check'] not in CHECKS:
            raise UsageError(f"native candidate control {control.get('id')} has an unknown category or check")
        if not str(control['macro']).startswith('SWDB_NATIVE_FAULT_'):
            raise UsageError(f"native candidate control {control['id']} must select a native seam fault")
    if not set(data['required_categories']) <= {c['category'] for c in controls}:
        raise UsageError('native candidate profile controls miss a required category')
    declared = {c.get('id') for c in entry.get('negative_controls') or []}
    if {c['id'] for c in controls} != declared:
        raise UsageError('native candidate profile controls differ from the contract negative_controls')
    scope = _closed(data['rewrite_scope'], {'file', 'begin', 'end'}, 'rewrite_scope')
    hook = _closed(data['instrumentation'], {'anchor', 'hook', 'hook_v14'}, 'instrumentation')
    # Ticket 75 (merged after ticket 76): the certify 1.4 harness (one binary, blinded plan).
    resolved_v14 = {}
    for name, item in _closed(data['harness_v14'], _HARNESS_FIELDS, 'harness_v14').items():
        try:
            catalog._pin({**item, 'root': 'library'})
            resolved_v14[name] = catalog.resolve({**item, 'root': 'library'})
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise UsageError(f'native candidate profile harness_v14 {name}: {exc}') from None
    witness = _closed(data['execution_witness'], {'rule'}, 'execution_witness')
    if witness['rule'] != 'claims_and_pushes_when_reached':
        raise UsageError('native candidate profile names an unknown execution-witness rule')
    return {'path': path, 'sha256': artifacts.file_hash(path), 'data': data, 'harness': resolved,
            'harness_v14': resolved_v14, 'scope': scope, 'hook': hook}


# --- scope and instrumentation -------------------------------------------------------------------

def changed_files(tree, snapshot):
    original = {item['path']: item for item in snapshot['artifact']['files']}
    current = {item['path']: item for item in artifacts.manifest(tree)}
    return sorted(path for path in set(original) | set(current) if original.get(path) != current.get(path))


def check_scope(profile, tree, snapshot, snapshot_text):
    """Only the declared function body of the declared file may change (structural, before any build)."""
    scope = profile['scope']
    changed = changed_files(tree, snapshot)
    if changed != [scope['file']]:
        raise UsageError('native contract permits only a rewrite of ' + scope['file'] + '; changed files: '
                         + ', '.join(changed))
    candidate = (Path(tree) / scope['file']).read_text()

    def outside(text):
        start = text.find(scope['begin'])
        end = text.find(scope['end'], start + 1) if start >= 0 else -1
        if start < 0 or end < 0 or text.count(scope['begin']) != 1:
            raise UsageError('native rewrite scope markers are missing or ambiguous')
        return text[:start], text[end:]

    if outside(snapshot_text) != outside(candidate):
        before, after = outside(snapshot_text), outside(candidate)
        lines = list(difflib.unified_diff((before[0] + before[1]).splitlines(), (after[0] + after[1]).splitlines(),
                                          lineterm='', n=0))[2:6]
        raise UsageError('native candidate changes code outside ' + scope['begin'].strip('( ') + ': '
                         + ' | '.join(lines))
    # Ticket 75 review: the region between the markers must stay exactly one function definition with
    # the snapshot's signature (no added top-level functions, globals or macros after its body).
    if _definition(snapshot_text, scope)[0] != _definition(candidate, scope)[0]:
        raise UsageError('native candidate changes the signature of ' + scope['begin'].strip('( '))
    return changed


def _definition(text, scope):
    """(signature tokens, body tokens) of the one function definition between the scope markers."""
    from swdb.certification_faults import tokens
    start = text.find(scope['begin'])
    region = text[start:text.find(scope['end'], start + 1)]
    words = [token for token, _, _ in tokens(region)]
    if '{' not in words:
        raise UsageError('native rewrite scope holds no function definition')
    open_at = words.index('{')
    depth = 0
    for position in range(open_at, len(words)):
        depth += {'{': 1, '}': -1}.get(words[position], 0)
        if depth == 0:
            break
    if depth != 0 or position != len(words) - 1:
        raise UsageError('native rewrite scope must hold exactly one function definition '
                         f"({scope['begin'].strip('( ')}); text follows its body")
    return words[:open_at], words[open_at:]


def instrument(profile, source):
    """Insert the evaluator's frontier hook before the protected frontier print (a private build copy)."""
    hook = profile['hook']
    if source.count(hook['anchor']) != 1:
        raise Failure('BFS frontier logging statement differs from the protected exact text')
    if source.count('bool BFSVerifier(') != 1:
        raise Failure('BFS correctness check is missing or ambiguous')
    return source.replace(hook['anchor'], hook['hook'] + '\n        ' + hook['anchor'], 1)


# --- builds --------------------------------------------------------------------------------------

class NativeBuild:
    """The objects of one candidate tree at one build configuration (ticket 70's CandidateBuild shape)."""

    def __init__(self, folder, profile, tree, source_path, build, fault_batch, harness=None):
        from swdb.certification import compiler
        self.folder, self.profile, self.tree = Path(folder), profile, Path(tree)
        self.source_path, self.build = Path(source_path), build
        self.folder.mkdir(parents=True, exist_ok=True)
        self.compiler = compiler()
        self.flags = list(build['flags'])
        self.includes = ['-I' + str(self.tree / 'benchmarks/API'), '-I' + str(self.tree / 'include')]
        self.fault_batch = fault_batch
        self.harness = harness or profile['harness']   # 1.3 harness, or the 1.4 one (one seam object)
        self._trusted = {}

    def _compile(self, source, output, extra=()):
        from swdb.certification import execute
        command = [self.compiler, *self.flags, *extra, '-c', str(source), '-o', str(output)]
        result = execute(command, Path(str(output) + '.build.json'), timeout=180)
        if result['returncode'] == 0:
            result['object_sha256'] = artifacts.file_hash(output)
        return result

    def candidate_object(self, text, label):
        self.source_path.write_text(text)
        extra = ['-Dmain=swdb_candidate_main', '-iquote', str(self.source_path.parent), *self.includes,
                 '-include', str(self.harness['prelude'])]
        output = self.folder / f'candidate-{label}.o'
        result = self._compile(self.source_path, output, extra)
        result['object'] = str(output)
        result['source_sha256'] = artifacts.digest(text)
        return result

    def trusted_object(self, kind, fault=None):
        key = (kind, fault)
        if key not in self._trusted:
            source = self.harness['record' if kind == 'record' else 'seams']
            name = kind if kind == 'record' else 'seams-' + (fault or 'none').lower()
            output = self.folder / f'{name}.o'
            extra = [f'-DSWDB_NATIVE_FAULT_BATCH={self.fault_batch}'] if kind == 'seams' else []
            result = self._compile(source, output, extra + (['-D' + fault] if fault else []))
            result['object'] = str(output)
            if result['returncode']:
                raise Failure(f'trusted certification object failed to build ({name}); see ' + result['log'])
            self._trusted[key] = result
        return self._trusted[key]

    def link(self, candidate, fault, output):
        from swdb.certification import execute
        record, seams = self.trusted_object('record'), self.trusted_object('seams', fault)
        command = [self.compiler, '-fopenmp', '-pthread', candidate['object'], record['object'], seams['object'],
                   '-o', str(output)]
        result = execute(command, Path(str(output) + '.link.json'), timeout=180)
        result.update(candidate_object_sha256=candidate.get('object_sha256'),
                      record_object_sha256=record['object_sha256'], seam_object_sha256=seams['object_sha256'],
                      fault_macro=fault)
        return result


def witness_ok(parsed, counts):
    """Execution witness: claims and pushes went through the contract's seams whenever BFS went past the source."""
    if len(counts) <= 1:
        return True
    return bool(parsed.get('claims')) and bool(parsed.get('pushes'))


def judge_native(plugin, run, graph, vertex, counts, adjacency):
    from swdb import certification as c
    from swdb import certification_isolation as isolation
    from swdb.certification_feedback import STRICT_MESSAGES
    if graph not in adjacency:
        adjacency[graph] = c.graph_adjacency(graph)
    parsed = isolation.parse_records(run['record'], set(STRICT_MESSAGES))
    check = lambda values: plugin.certification_check_result(adjacency[graph], vertex, values)
    return isolation.judge(run, parsed, counts, check_result=check, result_kind=plugin.certification_result_kind,
                           witness=witness_ok)


def certify_native(tree, library, folder, profile, plugin, *, sources=None):
    """Run the profile's matrix and controls on one candidate tree; returns (matrix, controls)."""
    from swdb import certification as c
    from swdb import certification_isolation as isolation
    data = profile['data']
    matrix_spec = data['matrix']
    sources = list(sources or matrix_spec['sources'])
    graphs = c.matrix_graphs(folder, library, max(matrix_spec['threads']))
    by_name = dict(graphs)
    tail = folder / 'staging-tail-17.sg'
    staging_tail_graph(tail)
    by_name['staging-tail-17'] = tail
    source_path = Path(tree) / data['rewrite_scope']['file']
    source = source_path.read_text()
    driver = profile['harness']['driver'].read_text()
    instrumented = instrument(profile, source) + driver
    adjacency = {}

    def evidence(link, verdict):
        return {'candidate_object_sha256': link['candidate_object_sha256'],
                'seam_object_sha256': link['seam_object_sha256'], 'record_object_sha256': link['record_object_sha256'],
                'named_checks': verdict['named_checks'], 'observed_checks': verdict['observed_checks'],
                'result_check': verdict['result_check'], 'record_problems': verdict['record_problems']}

    matrix, controls = [], []
    for build_spec in matrix_spec['builds']:
        label = build_spec['id']
        build = NativeBuild(folder / f'bfs-{label}.objects', profile, tree, source_path, build_spec,
                            matrix_spec['fault_batch'])
        positive = build.candidate_object(instrumented, 'positive')
        output = folder / f'bfs-{label}'
        link = build.link(positive, None, output) if positive['returncode'] == 0 else positive
        if link['returncode'] != 0:
            matrix.append({'build': label, 'status': 'failed', 'reason': 'build failed', 'compile': positive,
                           'link': link})
            continue
        for threads, graph_name in positive_runs(matrix_spec, graphs, data['controls']):
            graph = by_name[graph_name]
            for vertex in sources:
                counts = plugin.certification_oracle(graph, vertex)
                run = isolation.run(output, graph, vertex, folder / f'{graph_name}-{label}-t{threads}-{vertex}.json',
                                    threads)
                verdict = judge_native(plugin, run, graph, vertex, counts, adjacency)
                matrix.append({'graph': graph_name, 'graph_sha256': artifacts.file_hash(graph), 'source': vertex,
                               'oracle_frontier_counts': counts, 'build': label, 'flags': build_spec['flags'],
                               'threads': threads, 'status': 'passed' if verdict['passed'] else 'failed',
                               'reason': verdict['reason'], 'compile': positive, 'link': link, 'run': run,
                               **evidence(link, verdict)})
        vertex = sources[0]
        threads = matrix_spec['control_threads']
        for control in data['controls']:
            graph_name = control.get('graph', matrix_spec['control_graph'])
            graph = by_name[graph_name]
            counts = plugin.certification_oracle(graph, vertex)
            output_mutant = folder / f'bfs-{label}-{control["id"]}'
            control_link = build.link(positive, control['macro'], output_mutant)
            fault = {'site': 'library_fault', 'macro': control['macro'], 'delivery': 'separate_object', 'version': 1,
                     'seam_source_sha256': artifacts.file_hash(profile['harness']['seams'])}
            expected = {control['expected_check']}
            if control_link['returncode']:
                controls.append({'id': control['id'], 'build': label, 'status': 'invalid', 'reason': 'build failed',
                                 'observed_checks': [], 'fault': fault, 'compile': positive, 'link': control_link})
                continue
            run = isolation.run(output_mutant, graph, vertex, folder / f'control-{label}-{control["id"]}.json', threads)
            verdict = judge_native(plugin, run, graph, vertex, counts, adjacency)
            record = evidence(control_link, verdict)
            controls.append({'id': control['id'], 'build': label, 'threads': threads, 'expected_check':
                             control['expected_check'],
                             'status': c.control_status(expected, record['observed_checks'], run, verdict['passed']),
                             'reason': verdict['reason'], 'graph': graph_name,
                             'graph_sha256': artifacts.file_hash(graph), 'fault': fault, 'compile': positive,
                             'link': control_link, 'run': run, **record})
    source_path.write_text(source)  # a private build copy, never a vendored tree
    return matrix, controls


# --- certify 1.4 (blinded, attributed; ticket 76's mechanism for native-CPU contracts) ------------

#: The native 1.4 seam object's fault indices (library/native/certification/v1_4/seams.cc `enum Fault`).
FAULT_INDEX_V14 = {None: 0, 'claim_without_write': 1, 'partial_batch_dropped': 2, 'stale_row_offset': 3,
                   'forged_frontier': 4}
ATTRIBUTION_V14 = {'claim_without_write': 'lost_claim_left_unset',
                   'partial_batch_dropped': 'missing_child_of_hidden_vertex',
                   'stale_row_offset': 'parent_without_edge_from_stale_vertex',
                   'forged_frontier': 'duplicate_is_forged_push'}


def _plan_line(fault, nonce):
    line = f'plan 2 {FAULT_INDEX_V14[fault]:02d} {nonce}\n'.encode('ascii')
    assert len(line) == 43
    return line


def run_v14(binary, graph, source, log, threads, fault=None):
    """One blinded run: a fresh record file and a plan pipe (ticket 76's descriptor layout)."""
    import os
    import secrets
    from swdb.certification import execute
    from swdb.certification_blinding import CHANNEL_ENV, PLAN_ENV
    nonce = secrets.token_hex(16)
    # Ticket 75 review: the record file is named by the nonce (the parent keeps the mapping in `log`),
    # so the candidate cannot learn the fault from the descriptor's path.
    record = Path(log).parent / f'run-{nonce}.record'
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    plan_read, plan_write = os.pipe()
    try:
        os.write(plan_write, _plan_line(fault, nonce))
        os.close(plan_write)
        plan_write = None
        result = execute([binary, '-f', graph, '-r', source, '-n', '1', '-v'], log, threads=threads,
                         extra_env={CHANNEL_ENV: str(descriptor), PLAN_ENV: str(plan_read)},
                         pass_fds=(descriptor, plan_read))
    finally:
        os.close(descriptor)
        os.close(plan_read)
        if plan_write is not None:
            os.close(plan_write)
    result.update(record=str(record.resolve()), record_sha256=artifacts.file_hash(record),
                  plan={'fault': fault, 'nonce': nonce})
    return result


def witness_v14(parsed, counts, book):
    """Native execution witness under 1.4: claims and pushes through the seams once BFS passes the source."""
    return len(counts) <= 1 or (bool(parsed.get('claims')) and bool(parsed.get('pushes')))


def attributed_v14(fault, parsed, verdict, book, adjacency, source):
    """(attributed, evidence) of one native control run, from its trusted records alone."""
    from swdb import certification_blinding as blinding
    rule = ATTRIBUTION_V14[fault]
    if fault == 'forged_frontier':
        return blinding.attributed(fault, parsed, verdict, book, {'duplicate_frontier'})
    values = (parsed['result'] or {}).get('values') or []
    record = parsed['native_faults'].get({'claim_without_write': 'lost', 'partial_batch_dropped': 'hidden',
                                          'stale_row_offset': 'stale'}[fault])
    if not record:
        return False, {'rule': rule, 'fault_record': None}
    if rule == 'lost_claim_left_unset':
        address, value = record[0], record[1]
        base = parsed['result_base'][0] if parsed['result_base'] else None
        vertex = (address - base) // 4 if base is not None and (address - base) % 4 == 0 else -1
        depth = {v: d for d, level in enumerate(blinding.level_sets(adjacency, source)) for v in level}
        parent = values[vertex] if 0 <= vertex < len(values) else None
        wrong = parent is None or not (0 <= parent < len(adjacency) and vertex in adjacency[parent]
                                       and depth.get(parent, -2) + 1 == depth.get(vertex, -1))
        hit = 0 <= vertex < len(values) and parent != value and wrong
        return hit, {'rule': rule, 'vertex': vertex, 'claimed_value': value,
                     'returned': values[vertex] if 0 <= vertex < len(values) else None}
    if rule == 'missing_child_of_hidden_vertex':
        children = {v for u in record for v in adjacency[u]}
        levels = blinding.level_sets(adjacency, source)
        observed = [set(w) for _, w in parsed['windows'] if w]
        for depth, expected in enumerate(levels):
            seen = observed[depth] if depth < len(observed) else set()
            if seen != expected:
                hits = sorted((expected - seen) & children)
                return bool(hits), {'rule': rule, 'level': depth, 'hidden': record[:5], 'missing_children': hits[:5]}
        return False, {'rule': rule, 'hidden': record[:5], 'levels_equal': True}
    u, begin, end = record[0], record[1], record[2]
    flat = [v for row in adjacency for v in row]
    stale_row = set(flat[max(begin, 0):max(end, 0)])
    neighbors = set(adjacency[u])
    hits = [x for x, parent in enumerate(values) if parent == u and x != u and x not in neighbors and x in stale_row]
    return bool(hits), {'rule': rule, 'vertex': u, 'children_without_edge': hits[:5]}


def certify_native_v14(tree, library, folder, profile, plugin, *, rng=None):
    """The profile's matrix and controls under certify 1.4: one binary per build, blinded plans, a random
    order per build, attributed rejections, the slide-window ledger and the seam witness."""
    import random
    from swdb import certification as c
    from swdb import certification_blinding as blinding
    from swdb.certification_feedback import STRICT_MESSAGES
    rng = rng or random.SystemRandom()
    data = profile['data']
    spec = data['matrix']
    harness = profile['harness_v14']
    sources = list(spec['sources'])
    graphs = c.matrix_graphs(folder, library, max(spec['threads']))
    by_name = dict(graphs)
    tail = folder / 'staging-tail-17.sg'
    staging_tail_graph(tail)
    by_name['staging-tail-17'] = tail
    source_path = Path(tree) / data['rewrite_scope']['file']
    source = source_path.read_text()
    hook = profile['hook']
    if source.count(hook['anchor']) != 1 or source.count('bool BFSVerifier(') != 1:
        raise Failure('BFS frontier logging statement or correctness check differs from the protected text')
    instrumented = source.replace(hook['anchor'], hook['hook_v14'] + '\n        ' + hook['anchor'], 1) + \
        harness['driver'].read_text()
    adjacency = {}

    def rows(graph):
        if graph not in adjacency:
            adjacency[graph] = c.graph_adjacency(graph)
        return adjacency[graph]

    def judged(run, graph, vertex, counts):
        parsed = blinding.parse_records(run['record'], set(STRICT_MESSAGES))
        check = lambda values: plugin.certification_check_result(rows(graph), vertex, values)
        verdict = blinding.judge(run, parsed, counts, check_result=check, result_kind=plugin.certification_result_kind,
                                 source=vertex, claims_address_result=True, witness=witness_v14)
        return parsed, verdict

    matrix, controls, schedule = [], [], []
    for build_spec in spec['builds']:
        label = build_spec['id']
        build = NativeBuild(folder / f'bfs-{label}.v14', profile, tree, source_path, build_spec, spec['fault_batch'],
                            harness=harness)
        positive = build.candidate_object(instrumented, 'positive')
        output = folder / f'bfs-{label}.v14.bin'
        link = build.link(positive, None, output) if positive['returncode'] == 0 else positive
        if link['returncode'] != 0:
            matrix.append({'build': label, 'status': 'failed', 'reason': 'build failed', 'compile': positive, 'link': link})
            continue
        binary_sha256 = artifacts.file_hash(output)
        jobs = [{'kind': 'matrix', 'graph_name': name, 'graph': by_name[name], 'vertex': vertex, 'threads': threads,
                 'fault': None} for threads, name in positive_runs(spec, graphs, data['controls']) for vertex in sources]
        for control in data['controls']:
            name = control.get('graph', spec['control_graph'])
            jobs.append({'kind': 'control', 'control': control, 'graph_name': name, 'graph': by_name[name],
                         'vertex': sources[0], 'threads': spec['control_threads'], 'fault': control['id']})
        for canonical, job in enumerate(jobs):
            job['canonical'] = canonical
        rng.shuffle(jobs)
        done_matrix, done_controls = [], []
        for order, job in enumerate(jobs):
            schedule.append({'build': label, 'order': order, 'kind': job['kind'],
                             'name': job['fault'] or f"{job['graph_name']}/t{job['threads']}/{job['vertex']}"})
            counts = plugin.certification_oracle(job['graph'], job['vertex'])
            tag = job['fault'] or f"{job['graph_name']}-t{job['threads']}-{job['vertex']}"
            run = run_v14(output, job['graph'], job['vertex'], folder / f'v14-{label}-{tag}.json', job['threads'],
                          fault=job['fault'])
            parsed, verdict = judged(run, job['graph'], job['vertex'], counts)
            evidence = {'candidate_object_sha256': link['candidate_object_sha256'], 'binary_sha256': binary_sha256,
                        'seam_object_sha256': link['seam_object_sha256'],
                        'record_object_sha256': link['record_object_sha256'], 'plan': run['plan'],
                        'named_checks': verdict['named_checks'], 'observed_checks': verdict['observed_checks'],
                        'result_check': verdict['result_check'], 'record_problems': verdict['record_problems'],
                        'seam_witness': verdict['seam_witness'], 'schedule_order': order}
            if job['kind'] == 'matrix':
                done_matrix.append((job['canonical'], {
                    'graph': job['graph_name'], 'graph_sha256': artifacts.file_hash(job['graph']), 'source': job['vertex'],
                    'oracle_frontier_counts': counts, 'build': label, 'flags': build_spec['flags'],
                    'threads': job['threads'], 'status': 'passed' if verdict['passed'] else 'failed',
                    'reason': verdict['reason'], 'compile': positive, 'link': link, 'run': run, **evidence}))
                continue
            control = job['control']
            status = c.control_status({control['expected_check']}, verdict['observed_checks'], run, verdict['passed'])
            reason = verdict['reason']
            ok, attribution = attributed_v14(job['fault'], parsed, verdict, verdict['_book'], rows(job['graph']),
                                             job['vertex'])
            import json
            attribution = json.loads(json.dumps(attribution))   # records are JSON (tuples become lists)
            if status == 'rejected' and not ok:
                status, reason = 'invalid', 'check_not_attributed_to_fault'
            done_controls.append((job['canonical'], {
                'id': control['id'], 'build': label, 'threads': job['threads'], 'expected_check': control['expected_check'],
                'status': status, 'reason': reason, 'graph': job['graph_name'],
                'graph_sha256': artifacts.file_hash(job['graph']),
                'fault': {'site': 'library_fault', 'plan': control['id'], 'delivery': 'run_plan', 'version': 1,
                          'attribution': ATTRIBUTION_V14[control['id']],
                          'seam_source_sha256': artifacts.file_hash(harness['seams'])},
                'attribution': {'attributed': ok, **attribution}, 'compile': positive, 'link': link, 'run': run,
                **evidence}))
        matrix.extend(cell for _, cell in sorted(done_matrix, key=lambda pair: pair[0]))
        controls.extend(cell for _, cell in sorted(done_controls, key=lambda pair: pair[0]))
    source_path.write_text(source)  # a private build copy, never a vendored tree
    return matrix, controls, schedule
