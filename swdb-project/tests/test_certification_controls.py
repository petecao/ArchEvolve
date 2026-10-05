"""Spelling-independent rewrite negative controls. Created: 2026-10-04 ET (ticket 62).

Ticket 20's patch, a whitespace-reformatted copy and a structurally rewritten copy all
certify with every control rejected; a semantically broken rewrite and a rewrite that
bypasses the contract's claim primitive are refused.

Updated: 2026-10-04 ET (ticket 67: forged_frontier v2; a rewrite that counts its chunks
after their pushes certifies).
Updated: 2026-10-04 ET (ticket 70, certify 1.3: faults in a separate object, checks from evaluator
records; adversarial candidates are in test_certification_isolation.py).
"""
import re
import types
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_faults as faults
from swdb import kernels
from swdb.cli import Failure
from swdb.kernels import bc
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'contract.bfs_read_offload'


def _replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def reformatted(source):
    """Ticket 20's rewrite with different whitespace and line breaks only."""
    for old, new in [
        ('dxc_context c=swdb_contexts[omp_get_thread_num()];', 'dxc_context c = swdb_contexts[ omp_get_thread_num() ];'),
        ('if(claimed){parent[v]=u;lqueue.push_back(v);}',
         'if (claimed) {\n        parent[v] = u;\n        lqueue.push_back(v);\n      }'),
        ('__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);', '__dxc_wait(c.tile[3]);\n     __dxc_wait( c.tile[5] );'),
        ('for(;;){', 'for ( ; ; ) {'),
        ('__dxc_const_i32(begin,c.reg[0]);', '__dxc_const_i32(begin, c.reg[0]);'),
        ('std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end))',
         'std::min(begin + size_t(SWDB_CHUNK_SIZE), size_t(queue.shared_out_end))'),
    ]:
        source = _replace(source, old, new)
    return source


def restructured(source):
    """Same meaning, different structure and names: a provider's independent spelling."""
    start = source.index('void TDStep(')
    end = source.index('\nint64_t TDStep2(', start)
    body = source[start:end]
    body = _replace(body, 'dxc_context c=swdb_contexts[omp_get_thread_num()];',
                    'const int tid = omp_get_thread_num();\n   const dxc_context &ctx = swdb_contexts[tid];')
    body = re.sub(r'\bc\.(tile|reg)\[', r'ctx.\1[', body)
    body = _replace(body, 'const size_t end=std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end));',
                    'size_t end = begin + SWDB_CHUNK_SIZE;\n    if (end > queue.shared_out_end) end = queue.shared_out_end;')
    body = _replace(body, 'for(;;){', 'while (true) {')
    body = _replace(body, 'if(count==0)break;', 'if (!count) { break; }')
    body = _replace(body, 'if(claimed){parent[v]=u;lqueue.push_back(v);}',
                    'if (claimed) {\n        parent[v] = u;  // redundant labeled store (L4)\n        lqueue.push_back(v);\n      }')
    return source[:start] + body + source[end:]


def chunk_hook_after_pushes(source):
    """Correct, but counts each accelerated chunk after its claims and pushes (campaign a7's shape).

    Ticket 67: with threshold 64 and tile 16384 the two-level control graph's only pushing
    accelerated level is one chunk, so forged_frontier v1 (fired only after a counted chunk)
    never fired and this correct rewrite was rejected.
    """
    source = _replace(source, '    __dxc_accelerated_chunk();\n    for(;;){', '    for(;;){')
    return _replace(source, '     }\n    }\n   }\n  }else{', '     }\n    }\n    __dxc_accelerated_chunk();\n   }\n  }else{')


def skipped_recheck(source):
    """Semantically broken: the claim trusts the stale DX100 hint without the CAS."""
    return _replace(source, 'const bool claimed=hint<0&&compare_and_swap(parent[v],hint,u);', 'const bool claimed=hint<0;')


def bypassed_claim(source):
    """Correct, but claims with a raw builtin instead of the contract's compare_and_swap (L4)."""
    return _replace(source, 'compare_and_swap(parent[v],hint,u)', '__sync_bool_compare_and_swap(&parent[v],hint,u)')


def _patch(tmp_path, transform):
    plugin = types.SimpleNamespace(certification_source=c.BFS, certification_snapshot=c.DEFAULT_SNAPSHOT,
                                   certification_rewrite=lambda scalar: transform(c.peter_source(scalar)))
    output = tmp_path / 'candidate.patch'
    c.create_peter_patch(Store(ROOT / 'records'), output, plugin=plugin, temporary_root=str(tmp_path))
    return output


def _certify(tmp_path, monkeypatch, transform):
    try:
        c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    patch = _patch(tmp_path, transform)
    return c.certify(Store(ROOT / 'records'), CONTRACT, snapshot=c.DEFAULT_SNAPSHOT, patch=patch,
                     runs_dir=tmp_path / 'runs')


def _controls(record):
    return [(x['id'], x['tile_size'], x['status']) for x in record['negative_controls']]


def test_every_bfs_control_is_a_library_fault_that_leaves_the_candidate_text_unchanged():
    source = c.instrument_source(c.peter_source(Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)['regions'][0]['text']))
    assert set(kernels.BFS.certification_controls) == set(faults.LIBRARY_FAULTS)
    seams = (ROOT / 'library' / faults.SEAM_FILE).read_text()
    for name, macro in faults.LIBRARY_FAULTS.items():
        mutant = kernels.BFS.certification_control(source, name)
        # Ticket 70 (certify 1.3): even forged_frontier no longer edits the protected print.
        assert mutant['fault'] == macro and f'defined({macro})' in seams and mutant['source'] == source
    assert 'swdb_certification_frontier(queue);' in source
    # Spelling never decides whether a control exists.
    assert kernels.BFS.certification_control(reformatted(source), 'shared_context')['fault']


def test_token_matching_ignores_whitespace_and_comments_but_not_meaning():
    site = 'const NodeID fresh=__atomic_load_n(&depths[v],__ATOMIC_RELAXED);'
    spaced = 'x;\n  const NodeID fresh = __atomic_load_n( &depths[v], /* CPU */ __ATOMIC_RELAXED ) ;\n y;'
    assert faults.replace_tokens(spaced, site, 'Z;', 'n') == 'x;\n  Z;\n y;'
    with pytest.raises(Failure, match='mutation site: n'):
        faults.replace_tokens(spaced.replace('depths[v]', 'depths[w]'), site, 'Z;', 'n')
    scalar = bc.forward_pass_source(_bc_scalar())
    instrumented = bc.instrument_source(scalar)
    loose = instrumented.replace(bc.CPU_DEPTH, 'const NodeID fresh =\n   __atomic_load_n(&depths[v], __ATOMIC_RELAXED);')
    assert 'claimed?depth:hint' in bc.control(loose, 'stale_depth_hint')
    for name in bc.CONTROLS:
        assert bc.control(instrumented, name) != instrumented or name in faults.LIBRARY_FAULTS


def _bc_scalar():
    import importlib.util
    spec = importlib.util.spec_from_file_location('prepare_bc', ROOT / 'scripts/prepare_dx100_bc_scalar_snapshot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scalar_source((ROOT / 'apps/dx100' / bc.BC_SOURCE).read_text())


@pytest.mark.parametrize('transform', [lambda s: s, reformatted, restructured],
                         ids=['ticket20', 'reformatted', 'restructured'])
def test_equal_rewrites_certify_with_every_control_rejected(tmp_path, monkeypatch, transform):
    record = _certify(tmp_path, monkeypatch, transform)
    assert record['verdict'] == 'certified'
    assert len(record['matrix']) == 10 and all(x['status'] == 'passed' for x in record['matrix'])
    # Ticket 68 (2026-10-04 ET): 8 library faults and 2 legality controls at each tile size.
    assert len(record['negative_controls']) == 20
    assert all(status == 'rejected' for _, _, status in _controls(record)), _controls(record)
    sites = {x['id']: x['fault']['site'] for x in record['negative_controls']}
    assert sites.pop('knob_out_of_range') == 'knob_assignment' and sites.pop('schedule_out_of_range') == 'schedule_clause'
    assert set(sites.values()) == {'library_fault'}
    # 2026-10-04 ET (final code review): every enforceable clause check was observed. Ticket 68:
    # knob_range and schedule_range are enforced through the certifier's controls; the contract's
    # own controls for them cannot exercise them and are recorded as not enforceable.
    clauses = record['clause_controls']
    assert all(r['matched'] for r in clauses if r['enforceable']), clauses
    assert {r['clause'] for r in clauses if not r['enforceable']} == {'frontier_threshold', 'schedule'}
    assert {(r['clause'], r['control']) for r in clauses if r['source'] == 'certifier' and r['matched']} == {
        ('frontier_threshold', 'knob_out_of_range'), ('schedule', 'schedule_out_of_range')}


def test_forged_frontier_v2_is_killed_when_chunks_are_counted_after_their_pushes(tmp_path, monkeypatch):
    """Ticket 67 (2026-10-04 ET): a negative control must be killable by every correct rewrite."""
    record = _certify(tmp_path, monkeypatch, chunk_hook_after_pushes)
    assert record['verdict'] == 'certified', _controls(record)
    forged = [x for x in record['negative_controls'] if x['id'] == 'forged_frontier']
    assert [(x['tile_size'], x['status']) for x in forged] == [(16384, 'rejected'), (1024, 'rejected')]
    assert all('duplicate_frontier' in x['observed_checks'] and x['fault']['version'] == 2 for x in forged)
    assert record['command']['version'] == c.VERSION


def test_semantically_broken_rewrite_is_refused(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, skipped_recheck)
    assert record['verdict'] == 'failed'
    assert any(x['status'] == 'failed' and x['reason'] == 'frontier_size_equality' for x in record['matrix'])


def test_rewrite_that_bypasses_the_claim_seam_is_refused_by_its_surviving_control(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, bypassed_claim)
    assert record['verdict'] == 'failed'
    assert all(x['status'] == 'passed' for x in record['matrix'])
    survived = {name for name, _, status in _controls(record) if status != 'rejected'}
    assert survived == {'skipped_cas_recheck'}


# --- 2026-10-04 ET: final code review (ticket 43 follow-ups) -----------------------------------

def _run(stdout='', stderr='', returncode=0, timeout=False):
    return {'stdout': stdout, 'stderr': stderr, 'returncode': returncode, 'timeout': timeout}


def _judge(run, counts):
    # 2026-10-04 ET (ticket 70): observed_checks now serves calibration only (certify 1.3 judges
    # candidates from evaluator records), so it is exercised with the BFS calibration-style judge.
    return c.judge_bfs(run, counts, threshold=64)


def test_observed_checks_name_every_failed_check_not_only_the_first():
    # Verifier FAIL and unequal frontier prints: the frontier check is observed behind the verifier.
    run = _run('Starting TDStep: 1 elements\nStarting TDStep: 3 elements\nSWDB trusted_frontier=1\n'
               'SWDB trusted_frontier=3\nVerification: FAIL\n')
    assert c.observed_checks(run, [1, 4], _judge, []) == ['frontier_size_equality', 'verifier']
    assert c.observed_checks(run, [1, 3], _judge, []) == ['verifier']
    strict = _run(stderr='SWDB_STRICT_ASSERT:stream_bounds\n', returncode=134)
    assert c.observed_checks(strict, [1], _judge, ['stream_bounds']) == ['stream_bounds']
    duplicate = _run(stderr='SWDB_PRESERVATION_FAIL:duplicate_frontier\n', returncode=1)
    assert c.observed_checks(duplicate, [1], _judge, ['duplicate_frontier']) == ['duplicate_frontier',
                                                                                 'frontier_size_equality']


def test_a_control_with_expected_named_checks_is_not_rejected_by_any_failure():
    # Before: index_wrap (expected stream_bounds/byte_offset_overflow) counted as rejected on a
    # plain verifier FAIL, so the strict check it exists to exercise was never shown to fire.
    fail = _run('Verification: FAIL\n')
    assert c.control_status({'stream_bounds', 'byte_offset_overflow'}, ['verifier'], fail, False) == 'invalid'
    assert c.control_status({'stream_bounds'}, ['stream_bounds'], _run(returncode=134), False) == 'rejected'
    assert c.control_status(set(), ['verifier'], fail, False) == 'rejected'
    assert c.control_status(set(), ['verifier'], _run(returncode=139), False) == 'invalid'
    assert c.control_status(set(), [], _run('Verification: PASS\n'), True) == 'survived'
    assert c.control_status(set(), ['verifier'], _run(timeout=True), False) == 'invalid'


def _contract(clauses):
    return {'clauses': [{'id': cid, 'negative_control': {'id': control, 'check': check}}
                        for cid, control, check in clauses]}


def test_clause_controls_compare_each_clause_check_with_its_control_runs():
    controls = [{'id': 'dropped_continuation', 'status': 'rejected', 'observed_checks': ['verifier']},
                {'id': 'dropped_continuation', 'status': 'rejected',
                 'observed_checks': ['frontier_size_equality', 'verifier']},
                {'id': 'chunk_off_by_one', 'status': 'rejected', 'observed_checks': ['tile_truncation']}]
    entry = _contract([('L1', 'dropped_continuation', 'frontier_size_equality'),
                       ('chunk_size', 'chunk_off_by_one', 'tile_truncation'),
                       ('frontier_threshold', 'chunk_off_by_one', 'knob_range'),
                       ('L9', 'missing_control', 'verifier')])
    rows = {r['clause']: r for r in c.clause_controls(entry, controls)}
    assert not rows['L1']['matched'] and rows['L1']['enforceable']       # one tile size missed the check
    assert rows['chunk_size']['matched']
    assert not rows['frontier_threshold']['enforceable']                 # no run can report knob_range
    assert not rows['L9']['matched'] and rows['L9']['enforceable']       # the control never ran
    assert {r['source'] for r in rows.values()} == {'contract'}


def test_bc_l4_clause_gains_successor_bit_edge_index_and_path_count_controls():
    instrumented = bc.instrument_source(bc.forward_pass_source(_bc_scalar()))
    for name, expected in [('dropped_successor_bit', '(void)edges[k];'),
                           ('shifted_edge_index', '(edges[k]+1)%g.num_edges_directed()'),
                           ('shifted_path_count_source', 'u=frontier[k==0?count-1:k-1]')]:
        assert name in bc.CONTROLS and bc.CONTROLS[name] == set()
        mutant = bc.control(instrumented, name)
        assert expected in mutant and mutant != instrumented
    entry = _contract([('L4', 'skipped_cas_recheck', 'duplicate_frontier')])
    controls = [{'id': name, 'status': 'rejected', 'observed_checks': ['verifier']}
                for name, _ in kernels.BC.certification_clause_controls['L4']]
    controls.append({'id': 'skipped_cas_recheck', 'status': 'rejected',
                     'observed_checks': ['duplicate_frontier', 'frontier_size_equality']})
    rows = c.clause_controls(entry, controls, kernels.BC)
    assert [(r['control'], r['source'], r['matched']) for r in rows] == [
        ('skipped_cas_recheck', 'contract', True), ('dropped_successor_bit', 'plugin', True),
        ('shifted_edge_index', 'plugin', True), ('shifted_path_count_source', 'plugin', True)]


# --- 2026-10-04 ET: forged_frontier on graphs deeper than three levels (code review P3) ---------

def _layered_graph(path, widths):
    """Serialized directed CSR whose BFS levels from vertex 0 have exactly ``widths`` vertices."""
    import struct
    assert widths[0] == 1
    starts = [sum(widths[:i]) for i in range(len(widths))]
    nodes = sum(widths)
    rows = [[] for _ in range(nodes)]
    for level in range(len(widths) - 1):
        for j in range(widths[level + 1]):
            rows[starts[level] + j % widths[level]].append(starts[level + 1] + j)
    inverse = [[] for _ in range(nodes)]
    for u, row in enumerate(rows):
        for v in row:
            inverse[v].append(u)
    with Path(path).open('wb') as stream:
        stream.write(struct.pack('<Bii', 1, sum(map(len, rows)), nodes))
        for adjacency in (rows, inverse):
            offset = 0
            stream.write(struct.pack('<i', offset))
            for row in adjacency:
                offset += len(row)
                stream.write(struct.pack('<i', offset))
            for row in adjacency:
                if row:
                    stream.write(struct.pack('<' + 'i' * len(row), *row))


@pytest.mark.parametrize('widths', [[1, 2, 3, 4, 5, 6, 7, 2], [1, 2, 3, 4, 5, 100, 100]],
                         ids=['eight-levels-scalar', 'seven-levels-accelerated'])
def test_forged_frontier_is_rejected_on_a_deep_graph(tmp_path, widths):
    """Graphs deeper than three levels (code review P3; ticket 67).

    forged_frontier v2 duplicates the first queue push of the run, so it fires on both graphs,
    including eight scalar levels where v1 never fired (no accelerated chunk). The duplicate lands
    in level 1's window; the evaluator records that window and stops the run (exit 88).
    Ticket 70 (certify 1.3): the fault comes from the seam object linked to the unchanged candidate
    object, and `duplicate_frontier` is computed out of process from the recorded window.
    """
    try:
        c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')
    from swdb import certification_isolation as isolation
    graph = tmp_path / 'layered.sg'
    _layered_graph(graph, widths)
    counts = c.graph_oracle(graph, 0)
    assert counts == widths and len(counts) > 3
    folder = tmp_path / 'tree'
    folder.mkdir()
    tree, _ = c.materialize_snapshot(Store(ROOT / 'records'), c.DEFAULT_SNAPSHOT, folder)
    c.apply_patch(tree, _patch(tmp_path, lambda s: s))
    library = (ROOT / 'library').resolve()
    plugin = kernels.BFS
    instrumented = plugin.certification_instrument((tree / c.BFS).read_text()) + \
        (library / plugin.certification_driver).read_text()
    mutant = plugin.certification_control(instrumented, 'forged_frontier')
    assert mutant['source'] == instrumented
    build = isolation.CandidateBuild(tmp_path / 'objects', library, tree, tree / c.BFS, 1024, 4)
    candidate = build.candidate_object(instrumented, 'positive')
    assert candidate['returncode'] == 0, candidate['stderr'][-2000:]
    binary = tmp_path / 'bfs-forged'
    assert build.link(candidate, mutant['fault'], binary)['returncode'] == 0
    run = isolation.run(binary, graph, 0, tmp_path / 'run.json', 4)
    verdict = c.judge_run(plugin, run, graph, 0, counts)
    status = c.control_status(plugin.certification_controls['forged_frontier'], verdict['observed_checks'], run,
                              verdict['passed'])
    windows = isolation.parse_records(run['record'], set())['frontier']
    assert [len(w) for w in windows] == [1, widths[1] + 1], windows
    assert run['returncode'] == 88 and verdict['named_checks'] == ['duplicate_frontier'] and status == 'rejected'
