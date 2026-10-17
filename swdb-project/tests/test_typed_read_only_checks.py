"""Synthetic traces and trusted graph fixtures, never gem5 results. 2026-10-03 ET."""
import copy
from pathlib import Path

import pytest

from swdb import artifacts, bfs_protocol, dx100_coverage, read_only_checks as checks
from swdb.cli import Failure
from swdb.store import Record, Store


def trace(tmp_path, extra=''):
    path = tmp_path / 'readonly.log'
    lines = []
    tick = 110
    for unit, opcode, count in [('S', 'STREAM_LD', 2), ('I', 'INDIR_LD', 4), ('R', 'RANGE_LOOP', 2)]:
        for number in range(count):
            lines += [f'{tick}: system.maa: {unit}[0] Start [INSTR[opcode({opcode})]]',
                      f'{tick + 1}: system.maa: {unit}[0] End [INSTR]']
            tick += 2
    lines += ['150: system.maa: R[0] executeInstruction: tile size: 16',
              '151: system.maa: R[0] executeInstruction: tile size: 7']
    path.write_text('\n'.join(lines) + '\n' + extra)
    return path


def test_readonly_opcode_mix_and_original_executed_case_stay_separate(tmp_path):
    path = trace(tmp_path)
    observed = dx100_coverage.observe(path, {'simTicks': '100', 'finalTick': '200'}, 16, read_only=True)
    assert observed['read_only_executed']['state'] == 'observed'
    check = {'coverage': observed}
    assert bfs_protocol.accelerator_cases(check) == {'read_only_executed', 'full_tiles', 'tail_tiles'}
    assert 'executed' not in bfs_protocol.accelerator_cases(check)
    historical = dx100_coverage.observe(path, {'simTicks': '100', 'finalTick': '200'}, 16)
    assert 'completed_trace_opcodes' not in historical and 'read_only_executed' not in historical
    historical.update(accelerator_executed=True, instruction_counters={'system.maa.numInst': 1})
    historical['completed_trace_units']['A'] = 1
    assert 'executed' in bfs_protocol.accelerator_cases({'coverage': historical})


@pytest.mark.parametrize('extra', [
    '170: system.maa: I[0] Start [INSTR[opcode(INDIR_ST_VECTOR)]]\n171: system.maa: I[0] End [INSTR]\n',
    '170: system.maa: A[0] Start [INSTR[opcode(ALU_SCALAR)]]\n171: system.maa: A[0] End [INSTR]\n',
    '170: system.maa: I[0] End [INSTR]\n',
    '170: system.maa: I[0] Start [INSTR[opcode(INDIR_LD)]]\n',
])
def test_readonly_refuses_store_alu_and_incomplete_opcode_stream(tmp_path, extra):
    observed = dx100_coverage.observe(trace(tmp_path, extra), {'simTicks': '100', 'finalTick': '200'}, 16, read_only=True)
    assert observed['read_only_executed']['state'] == 'unobserved'


@pytest.fixture
def graph_store(tmp_path, monkeypatch):
    store = Store(tmp_path / 'empty')
    store.add(Record('workload.yaml', {'kind': 'workload', 'id': 'coverage-graph', 'definition': {'sources': [0]}}))
    # Independent original-adjacency graph: two depth-1 vertices race to depth 2.
    adjacency = [[1, 2], [0, 3], [0, 3], [1, 2]]
    monkeypatch.setattr(bfs_protocol, 'materialize_workload', lambda store, wid: {'graph': {'adjacency': adjacency}})
    assert checks.oracle_counts(store, 'coverage-graph', 0) == [1, 2, 1]
    return store


def output(tmp_path, store, name='run', probe='SWDB cas_fail_negative_hint=3 l3_violations=0\n'):
    path = tmp_path / (name + '.stdout')
    path.write_text('Starting TDStep: 1 elements\nStarting TDStep: 2 elements\nStarting TDStep: 1 elements\n' + probe)
    observed = checks.observe_output(path, store, 'coverage-graph', 0)
    return path, observed


@pytest.mark.parametrize('negative,violations,outcome', [(3, 0, 'observed'), (0, 0, 'inconclusive'), (3, 1, 'refuted')])
def test_frontier_and_l3_outcome_derive_from_exact_stdout(tmp_path, graph_store, negative, violations, outcome):
    path, observed = output(tmp_path, graph_store, probe=f'SWDB cas_fail_negative_hint={negative} l3_violations={violations}\n')
    assert observed['frontier_sizes']['state'] == 'passed'
    assert observed['parent_gather_race']['outcome'] == outcome
    path.write_text(path.read_text().replace('Starting TDStep: 2 elements', 'Starting TDStep: 1 elements'))
    assert checks.observe_output(path, graph_store, 'coverage-graph', 0)['frontier_sizes']['state'] == 'failed'


def test_companion_binds_exact_timed_binary_and_refutes_nonobserved_race(tmp_path, graph_store, monkeypatch):
    monkeypatch.setattr(bfs_protocol, '_check_verifier_identity', lambda *args: None)
    source = tmp_path / 'bfs.cc'
    source.write_text(checks.FRONTIER_TEXT + '\n')
    protocol = {'id': 'protocol', 'identity_sha256': 'a' * 64, 'frozen_at': '2026-10-03T10:00:00Z',
        'settings': {'correctness': {'verifier': 'dx100.bfs.verifier.v2', 'required_accelerator_cases': {'baseline': [], 'candidate': ['read_only_executed']},
            'companion_cases': {'parent_gather_race': {'workload': 'coverage-graph', 'source': 0}}}}}
    primary = {'candidate': 'same-tree', 'evidence_kind': 'contract_fixture',
               'build': {'binary_sha256': 'b' * 64}, 'context': {'target': 'target', 'configuration': {}, 'candidate_sha256': 'd' * 64}}
    graph_store.add(Record('candidate.yaml', {'kind': 'candidate', 'id': 'same-tree', 'artifact': {'sha256': 'd' * 64}}))
    for role in ('timed', 'diagnostic'):
        path, observed = output(tmp_path, graph_store, role)
        evaluation = {'id': role, 'kind': 'evaluation', 'candidate': 'same-tree', 'evidence_kind': 'contract_fixture',
            'outcome': {'state': 'complete'}, 'correctness': {'state': 'passed', 'checks': [{'passed': True,
                'source': 0, 'output': {'path': str(path), 'sha256': artifacts.file_hash(path)}, **observed}]},
            'build': {'binary_sha256': 'b' * 64 if role == 'timed' else 'c' * 64,
                      'flags': [] if role == 'timed' else ['-DSWDB_DXC_DIAGNOSTIC']},
            'context': {'target': 'target', 'configuration': {}, 'verifier': 'dx100.bfs.verifier.v2', 'candidate_sha256': 'd' * 64,
                'source': 0, 'workload': {'id': 'coverage-graph'},
                'timed_source': {'path': str(source), 'sha256': artifacts.file_hash(source)},
                'protocol_binding': {'protocol': 'protocol', 'frozen_sha256': 'a' * 64,
                    'companion_case': 'parent_gather_race', 'bound_at': '2026-10-03T10:01:00Z'}}}
        graph_store.add(Record(role + '.yaml', evaluation))
    request = {'companion_evaluations': {'timed': 'timed', 'diagnostic': 'diagnostic'}}
    assert checks.companion_acceptance(graph_store, protocol, request, primary)['outcome'] == 'observed'
    with pytest.raises(Failure, match='explicit timed'):
        checks.companion_acceptance(graph_store, protocol, {}, primary)
    diagnostic = graph_store.get('diagnostic')
    path, observed = output(tmp_path, graph_store, 'diagnostic', 'SWDB cas_fail_negative_hint=4 l3_violations=1\n')
    diagnostic['correctness']['checks'][0].update(observed, output={'path': str(path), 'sha256': artifacts.file_hash(path)})
    with pytest.raises(Failure, match='L3 outcome is refuted'):
        checks.companion_acceptance(graph_store, protocol, request, primary)
