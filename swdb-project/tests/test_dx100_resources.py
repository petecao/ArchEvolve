"""Bounded host-only observation controls. Updated: 2026-09-26."""
import json
from pathlib import Path
import runpy
import sys
import time
from types import ModuleType, SimpleNamespace

import pytest

from swdb import dx100_resources


def test_process_group_observation_excludes_other_jobs_and_retains_phase(tmp_path, monkeypatch):
    monkeypatch.setattr(dx100_resources.subprocess, 'check_output', lambda *a, **k:
                        '100 100 1234\n101 100 567\n200 200 99000000\n')
    rows = dx100_resources.process_group(100)
    assert rows == [{'pid': 100, 'rss_kib': 1234}, {'pid': 101, 'rss_kib': 567}]
    simulation = tmp_path / 'simulation'
    simulation.mkdir()
    (simulation / 'host-memory-phases.jsonl').write_text(
        '{"phase":"instantiate_end"}\n{"phase":"statistics_dump_begin"}\n{"incomplete')
    log = tmp_path / 'simulation.log'
    log.write_text('retained simulator log')
    path = tmp_path / 'memory.jsonl'
    dx100_resources.observe(path, 100, rows, time.monotonic(), log, tmp_path, 'contract_fixture')
    observation = json.loads(path.read_text())
    assert observation['rss_kib'] == 1801
    assert observation['last_simulator_phase'] == 'statistics_dump_begin'
    assert observation['evidence_kind'] == 'contract_fixture'
    assert not observation['host_cost_is_bfs_performance']


def test_phase_observer_resolves_one_vector_without_evaluating_statistics(tmp_path):
    module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/dx100_host_memory.py'))
    observer = module['Observer'](tmp_path)
    observer.allocator = None
    class Root:
        def resolveStat(self, name):
            assert name == 'system.l3.ReadReq_T.hits'
            return SimpleNamespace(size=2, subnames=['cpu.inst', 'cpu.data'])
        def getStats(self):
            raise AssertionError('must not enumerate the statistics tree')
    observer.requestors(Root())
    row = json.loads(observer.path.read_text())
    assert row['requestors'] == 2 and row['subnames'] == ['cpu.inst', 'cpu.data']
    assert row['observation_seconds'] >= 0
    for _ in range(200):
        observer.write('bounded_fixture')
    assert len(observer.path.read_text().splitlines()) == 128


def test_wrapper_forwards_model_calls_once_and_observes_dump_phases(tmp_path, monkeypatch):
    model = tmp_path / 'model'
    entry = model / 'configs/deprecated/example/se.py'
    entry.parent.mkdir(parents=True)
    entry.write_text('import m5\nm5.instantiate("retained")\nm5.simulate(123)\n')
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'stats.txt').write_text('sealed fixture statistics\n')
    calls = []
    m5 = ModuleType('m5')
    m5.options = SimpleNamespace(outdir=str(output))
    m5.curTick = lambda: 100
    m5.instantiate = lambda checkpoint: calls.append(('instantiate', checkpoint))
    m5.stats = SimpleNamespace(dump=lambda *a, **k: calls.append(('dump', a, k)))
    def simulate(ticks):
        calls.append(('simulate', ticks))
        m5.stats.dump('preserved', selected=True)
        cause = 'm5_exit instruction encountered' if ticks == 123 else 'exiting with last active thread context'
        return SimpleNamespace(getCause=lambda: cause, getCode=lambda: 0)
    m5.simulate = simulate
    objects = ModuleType('m5.objects')
    objects.Root = SimpleNamespace(getInstance=lambda: SimpleNamespace(resolveStat=lambda name:
        SimpleNamespace(size=1, subnames=['fixture-requestor'])))
    monkeypatch.setitem(sys.modules, 'm5', m5)
    monkeypatch.setitem(sys.modules, 'm5.objects', objects)
    monkeypatch.setenv('SWDB_DX100_MODEL_ROOT', str(model))
    monkeypatch.setenv('SWDB_DX100_EXECUTION_BINDING_SHA256', 'fixture')
    monkeypatch.setenv('SWDB_DX100_VERIFY_MAX_TICKS', '456')
    old_path, old_argv = sys.path[:], sys.argv[:]
    try:
        runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/dx100_verify.py'))
    finally:
        sys.path[:], sys.argv[:] = old_path, old_argv
    assert calls == [('instantiate', 'retained'), ('simulate', 123),
                     ('dump', ('preserved',), {'selected': True}), ('simulate', 456),
                     ('dump', ('preserved',), {'selected': True})]
    phases = [json.loads(line)['phase'] for line in (output / 'host-memory-phases.jsonl').read_text().splitlines()]
    assert phases.count('statistics_dump_begin') == phases.count('statistics_dump_end') == 2
    assert phases.count('requestor_vector') == 1
    assert json.loads((output / 'roi-seal.json').read_text())['verification']['state'] == 'finished'


def test_sealed_roi_rejects_different_host_observer_before_accepting_verdict(tmp_path):
    from swdb.dx100 import _correctness
    from swdb.bfs_native import StageFailure
    (tmp_path / 'roi-seal.json').write_text(json.dumps({
        'format': 'swdb.dx100.roi-seal.v1', 'execution_binding_sha256': 'execution',
        'driver_sha256': 'driver', 'host_memory_observer_sha256': 'different-observer',
        'roi_exit_cause': 'm5_exit instruction encountered'}))
    session = SimpleNamespace(data={'context': {
        'execution_binding_sha256': 'execution', 'verification_driver': {'sha256': 'driver'},
        'host_memory_observer': {'sha256': 'expected-observer'}}})
    with pytest.raises(StageFailure, match='sealed ROI does not identify'):
        _correctness(session, {'verification': {'checker': 'dx100.bfs.verifier.v1'}},
                     tmp_path, tmp_path / 'unused.log', True)
