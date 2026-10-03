"""Real strict-interface checks and fail-closed verdicts. Updated: 2026-10-03 ET."""
from pathlib import Path
import subprocess

import pytest

from swdb import certification as c
from swdb.cli import Failure, UsageError
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'library'


@pytest.fixture(scope='module', params=[1024, 16384])
def strict_driver(request, tmp_path_factory):
    folder = tmp_path_factory.mktemp(f'strict-{request.param}')
    executable = folder / 'differential'
    build = c.compile_cpp(LIBRARY / 'dx100/drivers/differential.cc', executable,
                          LIBRARY, tile_size=request.param, threads=4)
    assert build['returncode'] == 0, build['stderr']
    return executable


@pytest.mark.parametrize('operation', [*c.OPERATIONS, 'store'])
def test_strict_matches_independent_reference_semantics(strict_driver, operation):
    run = subprocess.run([strict_driver, operation], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert f'SWDB_DIFFERENTIAL_PASS:{operation}' in run.stdout


CONTROLS = [(operation, name, check) for operation, controls in c.CONTROLS.items()
            for name, check in controls.items()]


@pytest.mark.parametrize('operation,control,expected', CONTROLS)
def test_controls_fail_a_named_runtime_check(strict_driver, operation, control, expected):
    process = subprocess.run([strict_driver, operation, control], capture_output=True, text=True)
    result = {'timeout': False, 'returncode': process.returncode,
              'stdout': process.stdout, 'stderr': process.stderr}
    assert c.rejection(result, expected) == ('rejected', expected)


@pytest.mark.parametrize('returncode,stderr,timeout,expected', [
    (-11, '', False, 'invalid'), (0, '', False, 'survived'),
    (86, 'SWDB_STRICT_ASSERT:other_check', False, 'invalid'),
    (86, 'SWDB_STRICT_ASSERT:memory_region', True, 'invalid'),
])
def test_crashes_wrong_checks_and_timeouts_never_reject_controls(returncode, stderr, timeout, expected):
    result = {'timeout': timeout, 'returncode': returncode, 'stdout': '', 'stderr': stderr}
    assert c.rejection(result, 'memory_region')[0] == expected


def test_independent_two_level_graph_has_required_frontier_and_depth(tmp_path):
    graph = tmp_path / 'two-level.sg'
    c.two_level_graph(graph)
    assert c.graph_oracle(graph, 0) == [1, 4200, 17000]
    assert c.graph_oracle(graph, 1) == [1, 17000]


def test_frontier_oracle_rejects_invalid_graph_before_traversal(tmp_path):
    graph = tmp_path / 'bad.sg'
    graph.write_bytes(b'\x01' + b'\0' * 8)
    with pytest.raises(Failure, match='invalid graph size'):
        c.graph_oracle(graph, 0)


def result(output, returncode=0, stderr=''):
    return {'stdout': output, 'stderr': stderr, 'returncode': returncode, 'timeout': False}


def test_bfs_requires_trusted_counts_and_execution_witness():
    counts = [1, 64, 12]
    output = ''.join(f'Starting TDStep: {n} elements\nSWDB trusted_frontier={n}\n' for n in counts)
    output += 'Verification: PASS\nSWDB accelerated_chunks=1\n'
    assert c.judge_bfs(result(output), counts) == (True, 'all_checks_passed')
    assert c.judge_bfs(result(output.replace('SWDB trusted_frontier=64', 'SWDB trusted_frontier=65')), counts) == (False, 'frontier_size_equality')
    assert c.judge_bfs(result(output.replace('accelerated_chunks=1', 'accelerated_chunks=0')), counts) == (False, 'execution_witness')
    assert c.judge_bfs(result(output.replace('Verification: PASS', 'Verification: FAIL')), counts) == (False, 'verifier')


def test_candidate_prints_cannot_hide_duplicate_enqueue():
    output = 'Starting TDStep: 1 elements\nVerification: PASS\nSWDB accelerated_chunks=1\n'
    rejected = c.judge_bfs(result(output, 88, 'SWDB_PRESERVATION_FAIL:duplicate_frontier'), [1])
    assert rejected == (False, 'frontier_size_equality')


def test_exact_patched_tree_preserves_vendored_identity_and_ships_header(tmp_path):
    store = Store(ROOT / 'records')
    before = c.artifacts.identify(ROOT / 'apps/dx100')
    patch = tmp_path / 'peter.patch'
    c.create_peter_patch(store, patch)
    trial = tmp_path / 'candidate';trial.mkdir()
    tree, snapshot = c.materialize_snapshot(store, c.DEFAULT_SNAPSHOT, trial)
    c.apply_patch(tree, patch)
    c.artifacts.check_protections(tree, snapshot['protections'])
    assert c.artifacts.file_hash(tree / c.HEADER) == c.artifacts.file_hash(LIBRARY / 'dx100/dxc_lowering.hpp')
    assert c.artifacts.identify(ROOT / 'apps/dx100') == before
    source = (tree / c.BFS).read_text()
    assert source.count('__dxc_session_begin();') == 1
    assert source.count('__dxc_accelerated_chunk();') == 1
    assert '__dxc_cas_probe(' in source
    assert '__dxc_report();' in source


def test_candidate_logging_is_protected_before_build():
    with pytest.raises(Failure, match='frontier logging'):
        c.instrument_source('bool BFSVerifier(){}')


def test_calibration_witness_threshold_is_from_scalar_oracle():
    counts = [1, 4200]
    output = ''.join(f'Starting TDStepMAA: {n} elements\nSWDB trusted_frontier={n}\n' for n in counts)
    output += 'Verification: PASS\nSWDB strict_operations=0\n'
    assert c.judge_bfs(result(output), counts, calibrate=True) == (False, 'execution_witness')


def test_forged_frontier_control_prints_oracle_counts_but_trusted_queue_is_checked():
    scalar = c.peter_source(Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)['regions'][0]['text'])
    instrumented = c.instrument_source(scalar)
    mutant = c._rewrite_control(instrumented, 'forged_frontier')
    assert 'swdb_forged_counts[]={1,4200,17000}' in mutant
    assert '<< swdb_forged_counts[swdb_forged_level++]' in mutant
    assert 'swdb_certification_frontier(queue);' in mutant
    assert 'queue.size()-1' not in mutant


def test_bfs_counter_reset_precedes_the_once_per_call_runtime_guard():
    snapshot = Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)
    source = c.peter_source(snapshot['regions'][0]['text'])
    assert source.index('swdb_dxc::chunks() = 0;') < source.index('swdb_acceleration_enabled = uint64_t')


def test_candidate_scope_cannot_certify_uncontracted_header_edits(tmp_path):
    store = Store(ROOT / 'records')
    patch = tmp_path / 'peter.patch'
    c.create_peter_patch(store, patch)
    trial = tmp_path / 'candidate'; trial.mkdir()
    tree, snapshot = c.materialize_snapshot(store, c.DEFAULT_SNAPSHOT, trial)
    c.apply_patch(tree, patch)
    assert c.check_candidate_scope(tree, snapshot) == sorted([c.BFS, c.HEADER])
    (tree / 'benchmarks/gapbs/src/pvector.h').write_text('// uncontracted rewrite\n')
    with pytest.raises(UsageError, match='permits only'):
        c.check_candidate_scope(tree, snapshot)
