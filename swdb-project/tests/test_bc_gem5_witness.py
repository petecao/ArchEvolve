"""BC gem5 completion witness and read-only execution case. Created: 2026-10-03 ET (ticket 44).

Fixtures only: synthetic seals, traces and outputs, plus a native build of the
trusted BC gem5 driver around upstream GAPBS bc.cc with the certification m5
stub. None of this is a gem5 result.
"""

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from swdb import bfs_protocol, dx100_coverage, kernels, read_only_checks as checks
from swdb import bc_witness
from swdb import dx100_witness
from swdb.cli import Failure
from swdb.store import Record, Store

import test_dx100_witness as bfs_fixture
from test_bfs_protocol import _sg

ROOT = Path(__file__).resolve().parents[1]
GRAPH = {"num_vertices": 6, "directed": True,
         "edges": [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [4, 5], [1, 4]]}


def _ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def bc_evaluation(tmp_path, score_line='SWDB_BC_RESULT source=0 vertices=6 score_count=6 score_fnv1a64=0123456789abcdef'):
    """The BFS v2 fixture evaluation re-expressed as a protected complete-call BC candidate."""
    data = bfs_fixture.evaluation(tmp_path)
    context, check = data['context'], data['correctness']['checks'][0]
    for holder in (data['request']['verification'], context, check, check['continuation']):
        key = 'checker' if holder is not context else 'verifier'
        holder[key] = bc_witness.CHECKER
    contract = bc_witness.graph_verification_contract('dx100-gapbs')
    wrapper = tmp_path / 'complete_call.cc'
    wrapper.write_text('// Explicit BC wrapper fixture.\n')
    driver = _ref(wrapper)
    context.update(candidate_build=True, roi=bc_witness.ROI, application='dx100-gapbs', graph_verification=contract,
                   candidate_driver=driver, verifier_source=dict(driver))
    context['instrumentation']['graph_verification'] = contract
    data['build']['adapter'] = 'dx100.complete_call.v2'
    binding = context['execution_binding']
    binding['roi'] = bc_witness.ROI
    from swdb.artifacts import digest
    context['execution_binding_sha256'] = digest(binding)
    check['binding'] = binding
    # Re-seal with the BC checker and binding, exactly as the BC driver writes it.
    seal_path = Path(context['sealed_roi']['path'])
    seal = {key: value for key, value in context['sealed_roi'].items() if key not in {'path', 'sha256'}}
    seal['verification'] = check['continuation']
    seal['execution_binding_sha256'] = context['execution_binding_sha256']
    seal_path.write_text(json.dumps(seal))
    context['sealed_roi'] = {**_ref(seal_path), **seal}
    check['sealed_roi'] = _ref(seal_path)
    log = Path(check['output']['path'])
    log.write_text(f'SWDB_DX100_ROI_SEALED\n{score_line}\nVerification: PASS\n')
    reference = _ref(log)
    check.update(output=reference, output_sha256=reference['sha256'], verifier_source=dict(driver),
                 observed_verdicts=[{'verdict': 'PASS', 'line': 3, 'after_seal': True}],
                 completion_sequence={'kind': 'protected_candidate', 'observed': True, 'times': []})
    del check['parent_results']
    check['score_results'] = [r for r in [bc_witness.parse_result(score_line, 2, True)] if r]
    data['stages'][0].update(log=str(log), log_sha256=reference['sha256'])
    return data


def test_bc_gem5_seam_selects_the_bc_plugin():
    bc = kernels.BC
    assert kernels.by_gem5_checker('dx100.bc.verifier.v2') is bc and kernels.by_gem5_roi('bc.complete_call.v1') is bc
    assert kernels.by_gem5_checker('dx100.bfs.verifier.v2') is kernels.BFS
    assert kernels.witness_checkers() == {'dx100.bfs.verifier.v2', 'dx100.bc.verifier.v2'}
    assert all((ROOT / path).is_file() for path in bc.gem5_verification_runtime)
    assert bc.gem5_verification_runtime[1:] == kernels.BFS.gem5_verification_runtime[1:]
    assert bc.race_companion is False and kernels.BFS.race_companion is True


def test_bc_verify_driver_differs_from_the_frozen_bfs_driver_only_in_its_checker():
    bfs = (ROOT / 'scripts/dx100_verify.py').read_text().splitlines()
    bc = (ROOT / 'scripts/dx100_bc_verify.py').read_text().splitlines()
    body = lambda lines: [line for line in lines[lines.index('import hashlib'):]
                          if 'checker' not in line and 'witnessed = ' not in line and not line.lstrip().startswith('#')]
    assert body(bfs) == body(bc)
    assert "if checker != 'dx100.bc.verifier.v2':" in '\n'.join(bc)


def test_bc_completion_witness_applies_the_v2_rules_to_bc_identities(tmp_path):
    data = bc_evaluation(tmp_path)
    original = copy.deepcopy(data)
    assert bc_witness.validate_completed_witness(data)['completed'] is True
    assert kernels.BC.validate_completed_witness(data)['completed'] is True
    assert data == original
    assert kernels.BC.validate_record_witness(data)['availability']['state'] == 'verified'
    with pytest.raises(Failure):
        dx100_witness.validate_completed_witness(data)  # the BFS validator refuses BC identities


@pytest.mark.parametrize('mutation, message', [
    (lambda d: d['context'].update(verifier='dx100.bfs.verifier.v2'), 'checker identity'),
    (lambda d: d['context'].update(roi='bfs.complete_call.v1'), 'complete-call BC candidates'),
    (lambda d: d['context'].update(graph_verification=dict(d['context']['graph_verification'], count_type='double')), 'original-adjacency'),
    (lambda d: d['correctness']['checks'][0].update(score_results=[]), 'missing or ambiguous'),
    (lambda d: d['correctness']['checks'][0].update(parent_results=[]), 'not parent results'),
    (lambda d: d['correctness']['checks'][0]['score_results'][0].update(score_count=5), 'incomplete'),
    (lambda d: d['correctness']['checks'][0]['observed_verdicts'][0].update(verdict='FAIL'), 'verdict'),
    (lambda d: d['stages'][0].update(returncode=1), 'cleanly'),
])
def test_bc_completion_witness_rejects_wrong_identities_and_results(tmp_path, mutation, message):
    data = bc_evaluation(tmp_path)
    mutation(data)
    with pytest.raises(Failure, match=message):
        bc_witness.validate_completed_witness(data)


def test_bc_witness_rechecks_exact_output_and_seal_bytes(tmp_path):
    data = bc_evaluation(tmp_path)
    log = Path(data['correctness']['checks'][0]['output']['path'])
    log.write_text(log.read_text().replace('score_count=6', 'score_count=7'))
    with pytest.raises(Failure, match='differ'):
        bc_witness.validate_completed_witness(data)
    (tmp_path / 'second').mkdir()
    data = bc_evaluation(tmp_path / 'second')
    seal = Path(data['context']['sealed_roi']['path'])
    seal.write_text(seal.read_text().replace('dx100.bc.verifier.v2', 'dx100.bfs.verifier.v2'))
    with pytest.raises(Failure):
        bc_witness.validate_completed_witness(data)


def test_bc_witness_metadata_only_validation_still_checks_bc_rules(tmp_path):
    data = bc_evaluation(tmp_path)
    assert bc_witness.validate_completed_witness(data, verify_artifacts=False)['completed'] is True
    data['correctness']['checks'][0]['score_results'][0]['after_seal'] = False
    with pytest.raises(Failure):
        bc_witness.validate_completed_witness(data, verify_artifacts=False)


def test_bc_gem5_result_lines_and_failure_identity():
    row = kernels.BC.parse_gem5_result('SWDB_BC_RESULT source=3 vertices=9 score_count=9 score_fnv1a64=00000000000000ff',
                                       7, True)
    assert row['source'] == 3 and row['score_count'] == 9 and row['line'] == 7 and kernels.BC.gem5_result_complete(row)
    assert kernels.BC.parse_gem5_result('SWDB_BFS_RESULT source=3 vertices=9 parent_count=9 parent_fnv1a64=00000000000000ff', 7, True) is None
    assert 'BC' in kernels.BC.gem5_failure_message()


def _read_only_trace(tmp_path, stream=2, indirect=4, ranges=2):
    path = tmp_path / 'readonly.log'
    lines, tick = [], 110
    for unit, opcode, count in [('S', 'STREAM_LD', stream), ('I', 'INDIR_LD', indirect), ('R', 'RANGE_LOOP', ranges)]:
        for _ in range(count):
            lines += [f'{tick}: system.maa: {unit}[0] Start [INSTR[opcode({opcode})]]',
                      f'{tick + 1}: system.maa: {unit}[0] End [INSTR]']
            tick += 2
    path.write_text('\n'.join(lines) + '\nSWDB_BC_SCORE_STORAGE address=1000 count=6 element_bytes=4\n')
    return path


def test_bc_read_only_case_uses_the_forward_pass_instruction_mix(tmp_path):
    observed = dx100_coverage.observe(_read_only_trace(tmp_path), {'simTicks': '100', 'finalTick': '200'}, 16,
                                      read_only=True, plugin=kernels.BC)
    case = observed['read_only_executed']
    assert case['state'] == 'observed' and case['rule'] == 'S>=1,I>=1,R>=1,A=0,indirect_stores=0,I=3*R-S'
    check = {'checker': 'dx100.bc.verifier.v2', 'coverage': observed}
    assert 'read_only_executed' in bfs_protocol.accelerator_cases(check)
    wrong = dx100_coverage.observe(_read_only_trace(tmp_path, indirect=5), {'simTicks': '100', 'finalTick': '200'}, 16,
                                   read_only=True, plugin=kernels.BC)
    assert wrong['read_only_executed']['state'] == 'unobserved'


@pytest.fixture
def graph_store(tmp_path, monkeypatch):
    store = Store(tmp_path / 'empty')
    store.add(Record('workload.yaml', {'kind': 'workload', 'id': 'bc-graph', 'definition': {'sources': [0]}}))
    adjacency = [[1, 2], [3, 4], [3], [4], [5], []]
    monkeypatch.setattr(bfs_protocol, 'materialize_workload', lambda store, wid: {'graph': {'adjacency': adjacency}})
    return store


def test_bc_frontier_sizes_come_from_the_forward_pass_print(tmp_path, graph_store):
    path = tmp_path / 'run.stdout'
    path.write_text('Starting PBFS: 1 elements\nStarting PBFS: 2 elements\nStarting PBFS: 2 elements\n'
                    'Starting PBFS: 1 elements\nStarting Brandes: 2/5: 3-5 elements\n')
    observed = checks.observe_output(path, graph_store, 'bc-graph', 0, kernels.BC)
    assert observed['frontier_sizes']['state'] == 'passed' and observed['frontier_sizes']['observed'] == [1, 2, 2, 1]
    assert observed['parent_gather_race']['outcome'] == 'inconclusive'
    source = tmp_path / 'bc.cc'
    source.write_text('// fixture\n            ' + kernels.BC.frontier_text + '\n')
    log_ref = _ref(path)
    evaluation = {'context': {'verifier': 'dx100.bc.verifier.v2', 'workload': {'id': 'bc-graph'}, 'timed_source': _ref(source)},
                  'request': {'workload': {'id': 'bc-graph'}}}
    check = {**observed, 'output': log_ref, 'source': 0}
    checks.validate_frontier(evaluation, check, graph_store)
    source.write_text('// fixture without the forward-pass print\n')
    evaluation['context']['timed_source'] = _ref(source)
    with pytest.raises(Failure, match='frontier print'):
        checks.validate_frontier(evaluation, check, graph_store)


def test_bc_read_only_protocol_needs_no_race_companion(tmp_path, monkeypatch):
    """The read-only case for BC freezes without BFS's parent-gather race companion."""
    calls = []
    monkeypatch.setattr(checks, 'validate_companion_settings', lambda *args: calls.append(args))
    store = Store(tmp_path / 'empty')
    correctness = {'verifier': 'dx100.bc.verifier.v2', 'coverage': 'every_timed_trial', 'required_cases': [],
                   'required_accelerator_cases': {'baseline': [], 'candidate': ['read_only_executed']}}
    protocol = {'settings': {'kernel': 'gapbs-bc', 'correctness': correctness}}
    assert checks.companion_acceptance(store, protocol, {}, {}) is None and calls == []
    protocol['settings']['kernel'] = 'gapbs-bfs'
    with pytest.raises(Exception):
        checks.companion_acceptance(store, protocol, {}, {})
    assert calls  # BFS still requires its companion


def test_trusted_bc_gem5_driver_checks_returned_scores_natively(tmp_path):
    compiler = shutil.which('clang++') or shutil.which('g++')
    if not compiler:
        pytest.skip('C++ compiler unavailable')
    model = tmp_path / 'model'
    (model / 'include/gem5').mkdir(parents=True)
    shutil.copy(ROOT / 'library/dx100/strict/gem5/m5ops.h', model / 'include/gem5/m5ops.h')
    graph = tmp_path / 'graph.sg'
    graph.write_bytes(_sg(GRAPH, 8))
    outcomes = {}
    for name, mutate in (('pass', None), ('nan', '  scores[1] = NAN;\n  return scores;\n}')):
        source = tmp_path / name / 'bc.cc'
        shutil.copytree(ROOT / 'apps/gapbs/src', source.parent)
        if mutate:
            text = source.read_text()
            assert text.count('  return scores;\n}') == 1
            source.write_text(text.replace('  return scores;\n}', mutate))
        wrapper = tmp_path / name / 'complete_call.cc'
        wrapper.write_text(kernels.BC.gem5_driver(source, model, 'Brandes', sg_offset_bytes=8))
        binary = tmp_path / name / 'bc'
        built = subprocess.run([compiler, '-std=c++11', '-O2', str(wrapper), '-o', str(binary)], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr[-3000:]
        run = subprocess.run([str(binary), '-f', str(graph), '-r', '0', '-n', '1'], capture_output=True, text=True, timeout=60)
        outcomes[name] = run
    passed = outcomes['pass']
    assert passed.returncode == 0, passed.stderr
    rows = [kernels.BC.parse_gem5_result(line, 0, True) for line in passed.stdout.splitlines()]
    rows = [row for row in rows if row]
    assert len(rows) == 1 and rows[0]['score_count'] == rows[0]['vertices'] == 6 and rows[0]['source'] == 0
    assert 'SWDB_BC_SCORE_STORAGE address=' in passed.stdout and 'Verification: PASS' in passed.stdout
    # A NaN score passes the program's own BCVerifier but not the trusted oracle.
    assert outcomes['nan'].returncode == 4 and 'Verification: FAIL' in outcomes['nan'].stdout
