"""Spelling-independent rewrite negative controls. Created: 2026-10-04 ET (ticket 62).

Ticket 20's patch, a whitespace-reformatted copy and a structurally rewritten copy all
certify with every control rejected; a semantically broken rewrite and a rewrite that
bypasses the contract's claim primitive are refused.
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


def test_every_bfs_control_is_a_library_fault_and_only_forged_frontier_edits_the_protected_print():
    source = c.instrument_source(c.peter_source(Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)['regions'][0]['text']))
    assert set(kernels.BFS.certification_controls) == set(faults.LIBRARY_FAULTS)
    block = (ROOT / 'library' / faults.FAULT_FILE).read_text()
    for name, macro in faults.LIBRARY_FAULTS.items():
        mutant = kernels.BFS.certification_control(source, name)
        assert mutant['fault'] == macro and f'defined({macro})' in block
        assert (mutant['source'] == source) == (name != 'forged_frontier')
    forged = kernels.BFS.certification_control(source, 'forged_frontier')['source']
    assert 'swdb_forged_counts[]={1,4200,17000}' in forged and 'swdb_certification_frontier(queue);' in forged
    # Spelling never decides whether a control exists.
    assert kernels.BFS.certification_control(reformatted(source), 'shared_context')['fault']


def test_fault_header_keeps_the_canonical_bytes_as_its_prefix():
    canonical = (ROOT / 'library/dx100/dxc_lowering.hpp').read_bytes()
    header = faults.fault_header(canonical, ROOT / 'library')
    assert header.startswith(canonical) and header.endswith((ROOT / 'library' / faults.FAULT_FILE).read_bytes())


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
    assert len(record['negative_controls']) == 16
    assert all(status == 'rejected' for _, _, status in _controls(record)), _controls(record)
    assert all(x['fault']['site'] == 'library_fault' for x in record['negative_controls'])
    # 2026-10-04 ET (final code review): every enforceable clause check was observed; the two
    # clauses whose check names no run reports are recorded as not enforceable.
    clauses = record['clause_controls']
    assert all(r['matched'] for r in clauses if r['enforceable']), clauses
    assert {r['clause'] for r in clauses if not r['enforceable']} == {'frontier_threshold', 'schedule'}


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
    return bc.judge(run, counts, threshold=64)


def test_observed_checks_name_every_failed_check_not_only_the_first():
    # Verifier FAIL and unequal frontier prints: the frontier check is observed behind the verifier.
    run = _run('Starting PBFS: 1 elements\nStarting PBFS: 3 elements\nSWDB trusted_frontier=1\n'
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
