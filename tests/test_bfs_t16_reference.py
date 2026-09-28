"""T16 reference b1 batch kind (R10-R12), 2026-09-27 ET.

Synthetic contract data only: plan arithmetic, driver commands, and admission of
one completed series whose primaries also bind a second matching protocol. No
simulator, measurement, or empirical claim is produced here.
"""
import copy
import importlib.util
from types import SimpleNamespace

import pytest

from scripts import bfs_simulator_batch as batch
from swdb import artifacts, bfs_protocol
from test_bfs_simulator_batch import admission
from test_bfs_simulator_batch_admission import admit, completed, immutable, reseal  # noqa: F401

RECIPE = batch.ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t16-reference-b1'


def finalize():
    spec = importlib.util.spec_from_file_location('t16_finalize', RECIPE/'finalize.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def t16_plan(reps=1, atomic=True):
    protocols = {key: {'path': f'.scratch/x/{key}.yaml', 'sha256': key[0]*64, 'frozen_id': key + '.frozen'}
                 for key in ('artifact', 'control')}
    return finalize().build_plan(protocols, reps, atomic)


def test_plan_keeps_the_frozen_grid_and_sizes_the_allocation_from_bounds():
    value = t16_plan()
    old = batch.yamlio.load(batch.PLAN_DIR/'bfs-t16-protocol-recovery-simulator-batch-20260927-a1.json')
    assert value['record_sha256'] == old['record_sha256'] and value['id'] == batch.T16_ID
    names = [row['id'][len(value['id']) + 1:] for row in value['series']]
    assert names == ['artifact.scalar', 'control.scalar', 'maa']
    by_name = dict(zip(names, value['series']))
    for name, old_name in (('artifact.scalar', 'artifact.scalar'), ('control.scalar', 'control.scalar'), ('maa', 'artifact.maa')):
        old_row = next(row for row in old['series'] if row['id'].endswith('.' + old_name))
        assert {k: by_name[name][k] for k in ('candidate', 'diagnostic_build', 'workload', 'sources', 'configuration',
                                              'accelerated', 'protocol_key', 'protocol_role')} == \
            {k: old_row[k] for k in ('candidate', 'diagnostic_build', 'workload', 'sources', 'configuration',
                                     'accelerated', 'protocol_key', 'protocol_role')}
    control_maa = next(row for row in old['series'] if row['id'].endswith('.control.maa'))
    assert control_maa['configuration'] == by_name['maa']['configuration']  # R10 identity match
    assert by_name['maa']['shared_protocol_keys'] == ['control'] and value['post_roi_cpu'] == 'AtomicSimpleCPU'
    bounds, allocation = value['bounds'], value['allocation']
    primary = bounds['checkpoint_seconds'] + bounds['run_seconds'] + 60
    post = bounds['profile_seconds'] + bounds['package_seconds']
    tail = 4 * bounds['aggregate_seconds']
    assert bounds['series_seconds'] == 3 * (primary + bounds['diagnostic_seconds']) + post + tail == 507780
    assert sum(allocation['partition_seconds'].values()) == allocation['total_seconds'] == bounds['batch_seconds'] == 514980
    assert bounds['diagnostic_seconds'] - min(bounds['diagnostic_seconds'] // 2, 7200) - 30 >= bounds['run_seconds'] - 30
    assert (allocation['storage_gib'], allocation['per_series_cap_gib'], bounds['storage_gib']) == (64, 50, 24)
    assert allocation['free_space_required_at_admission_gib'] == 84 and bounds['raw_reserve_gib'] == 20
    assert batch.is_pilot(value) and batch.plan_path(batch.T16_KIND).name == batch.T16_ID + '.json'
    assert batch.preparation_charges(value) == [{'id': 'bfs-t16-reference-preparation-20260927-b1',
                                                'elapsed_seconds': 3600, 'raw_bytes': 4*batch.GIB}]
    batch.validate_preparation_reservation(value, {})
    changed = copy.deepcopy(value); changed['accounting']['preparation_reservation']['id'] = 'other'
    with pytest.raises(ValueError, match='approved partition'):
        batch.validate_preparation_reservation(changed, {})
    two = t16_plan(reps=2)
    assert two['bounds']['series_seconds'] == 6 * (primary + bounds['diagnostic_seconds']) + 2 * post + tail
    assert 'post_roi_cpu' not in t16_plan(atomic=False)


def test_series_commands_bind_shared_protocol_and_atomic_verifier(tmp_path):
    value = t16_plan(); approval = admission(value)
    approval['protocols'] = {'artifact': {'id': 'artifact.frozen', 'sha256': 'a'*64},
                             'control': {'id': 'control.frozen', 'sha256': 'c'*64}}
    commands = {row['id'].rsplit('.', 1)[-1]: batch.series_command(value, row, approval, tmp_path/'c', tmp_path/'raw',
                tmp_path/'r', 0, value['bounds']['series_seconds'], 50, None, tmp_path/'slots') for row in value['series']}
    arg = lambda command, name: command[command.index(name) + 1]
    maa = commands['maa']
    assert arg(maa, '--protocol') == 'artifact.frozen' and arg(maa, '--protocol-role') == 'candidate'
    assert arg(maa, '--shared-protocol') == 'control.frozen' and maa.count('--shared-protocol') == 1
    assert '--accelerated' in maa and arg(maa, '--post-roi-cpu') == 'AtomicSimpleCPU'
    scalar = commands['scalar']  # control.scalar is the last '.scalar' key
    assert '--shared-protocol' not in scalar and arg(scalar, '--protocol') == 'control.frozen'
    for command in commands.values():
        assert arg(command, '--run-seconds') == '43200' and arg(command, '--diagnostic-seconds') == '79200'
        assert arg(command, '--storage-gib') == '24' and arg(command, '--profile-seconds') == '36000'
        assert arg(command, '--package-seconds') == '36000' and arg(command, '--aggregate-seconds') == '14400'
        assert arg(command, '--gem5-slots') == '1' and arg(command, '--batch-storage-gib') == '50'


def _share(value):
    """Bind every completed primary to a second frozen policy that differs only in disclosures."""
    settings = copy.deepcopy(value.frozen['settings']); settings['differences'] = {'configuration': ['second policy']}
    control = immutable('protocol', 'synthetic-control', settings=settings, state='frozen',
        frozen_at=value.frozen['frozen_at'], workload_identities=value.frozen['workload_identities'])
    value.store.values[control['id']] = control
    value.approved['protocols']['control'] = {'id': control['id'], 'sha256': artifacts.digest(control)}
    value.row['shared_protocol_keys'] = ['control']
    for primary in value.primaries:
        binding = copy.deepcopy(primary['context']['protocol_binding'])
        binding.update(protocol=control['id'], frozen_sha256=control['identity_sha256'],
                       settings_sha256=artifacts.digest(settings))
        primary['context']['shared_protocol_bindings'] = {control['id']: binding}
    reseal(value)
    request = {'message_version': '1.0', 'id': value.row['id'] + '.shared0.aggregate', 'protocol': control['id'],
               'protocol_role': value.row['protocol_role'], 'evaluations': [item['id'] for item in value.primaries]}
    return control, request


def test_one_primary_grid_is_admitted_under_both_protocols(completed, monkeypatch):
    control, request = _share(completed)
    monkeypatch.setattr(bfs_protocol, '_request', lambda _: copy.deepcopy(request))
    shared = bfs_protocol.aggregate_evaluations(SimpleNamespace(records=None))
    assert shared['outcome']['state'] == 'complete', shared['outcome']
    completed.store.values[shared['id']] = shared
    completed.child['shared_protocols'] = [control['id']]
    completed.child['shared_aggregates'] = {control['id']: shared['id']}
    admit(completed)
    assert shared['context']['protocol'] == control['id'] != completed.aggregate['context']['protocol']
    completed.child['shared_aggregates'] = {}
    with pytest.raises(ValueError, match='shared aggregates'):
        admit(completed)


def test_shared_series_without_the_shared_binding_is_refused(completed, monkeypatch):
    control, request = _share(completed)
    monkeypatch.setattr(bfs_protocol, '_request', lambda _: copy.deepcopy(request))
    shared = bfs_protocol.aggregate_evaluations(SimpleNamespace(records=None))
    completed.store.values[shared['id']] = shared
    completed.child['shared_protocols'] = [control['id']]
    completed.child['shared_aggregates'] = {control['id']: shared['id']}
    for primary in completed.primaries:
        del primary['context']['shared_protocol_bindings']
    reseal(completed)  # the main aggregate is consistent again; the shared one is not
    with pytest.raises(ValueError, match='protocol role or ordered trial binding|component order or digests'):
        admit(completed)
    monkeypatch.setattr(bfs_protocol, '_request', lambda _: {**copy.deepcopy(request), 'id': request['id'] + '.x'})
    refused = bfs_protocol.aggregate_evaluations(SimpleNamespace(records=None))
    assert refused['outcome']['state'] == 'incompatible' and 'binding' in refused['outcome']['reason']
    completed.child['shared_protocols'] = []
    with pytest.raises(ValueError, match='shared-protocol, post-ROI CPU'):
        admit(completed)


def test_one_replay_requires_declared_deterministic_simulator_basis():
    from swdb import yamlio
    from swdb.cli import Failure
    from swdb.store import Store
    store = Store(batch.ROOT/'records')
    request = yamlio.load(batch.PLAN_DIR/'author-reference-seal-runtime-freeze-20260927-a1.yaml')
    settings = copy.deepcopy(request['settings'])
    bfs_protocol._validate_settings(settings, store, require_simulation_identity=True)
    settings['sampling']['repetitions'] = 1
    with pytest.raises(Failure, match='repetitions'):
        bfs_protocol._validate_settings(settings, store, require_simulation_identity=True)
    for bad in ({'basis': 'other', 'evidence': 'x'}, {'basis': 'deterministic_simulator_replay.v1', 'evidence': ' '},
                {'basis': 'deterministic_simulator_replay.v1'}):
        settings['sampling']['determinism'] = bad
        with pytest.raises(Failure, match='deterministic-replay'):
            bfs_protocol._validate_settings(settings, store, require_simulation_identity=True)
    settings['sampling']['determinism'] = {'basis': 'deterministic_simulator_replay.v1', 'evidence': 'observation.json'}
    bfs_protocol._validate_settings(settings, store, require_simulation_identity=True)
    settings['sampling']['repetitions'] = 0
    with pytest.raises(Failure, match='repetitions'):
        bfs_protocol._validate_settings(settings, store, require_simulation_identity=True)


def test_low_storage_plan_keeps_grid_and_only_narrows_trace_and_storage(tmp_path):
    full, low = t16_plan(), finalize().build_plan(
        {key: {'path': f'.scratch/x/{key}.yaml', 'sha256': key[0]*64, 'frozen_id': key + '.v2'}
         for key in ('artifact', 'control')}, 1, True, low_storage=True)
    assert low['trace_flags'] == 'MAATrace' and 'trace_flags' not in full
    assert low['series'] == full['series'] and low['post_roi_cpu'] == full['post_roi_cpu']
    bounds, allocation = low['bounds'], low['allocation']
    assert (bounds['storage_gib'], bounds['batch_storage_gib'], bounds['raw_reserve_gib']) == (4, 16, 10)
    assert allocation['free_space_required_at_admission_gib'] == 26 and allocation['per_series_cap_gib'] == 8
    for key in ('run_seconds', 'diagnostic_seconds', 'checkpoint_seconds'):
        assert bounds[key] == full['bounds'][key]
    primary = bounds['checkpoint_seconds'] + bounds['run_seconds'] + 60
    assert bounds['series_seconds'] == (3 * (primary + bounds['diagnostic_seconds'])
        + bounds['profile_seconds'] + bounds['package_seconds'] + 4 * bounds['aggregate_seconds'])
    assert sum(allocation['partition_seconds'].values()) == allocation['total_seconds'] == bounds['batch_seconds']
    approval = admission(low)
    approval['protocols'] = {'artifact': {'id': 'artifact.v2', 'sha256': 'a'*64}, 'control': {'id': 'control.v2', 'sha256': 'c'*64}}
    for row in low['series']:
        command = batch.series_command(low, row, approval, tmp_path/'c', tmp_path/'raw', tmp_path/'r', 0,
                                       bounds['series_seconds'], 8, None, tmp_path/'slots')
        assert command[command.index('--trace-flags') + 1] == 'MAATrace'


def test_maatrace_only_stream_still_proves_accelerator_execution(tmp_path):
    """MAATrace emits only unit Start/End lines; they alone carry the required 'executed' case."""
    from swdb import bfs_protocol
    from swdb.dx100_coverage import observe
    log = tmp_path / 'trace'
    log.write_text('\n'.join(f'{110 + i}: global: {unit}[0] {edge} [INSTR]' for i, (unit, edge) in enumerate(
        (u, e) for u in 'SIRA' for e in ('Start', 'End'))) + '\n')
    coverage = observe(log, {'simTicks': '100', 'finalTick': '200'}, 16384)
    assert coverage['completed_trace_units'] == {'S': 1, 'I': 1, 'R': 1, 'A': 1}
    assert coverage['full_tiles']['state'] == coverage['tail_tiles']['state'] == 'unobserved'
    assert coverage['competing_parent_updates']['state'] == 'unobserved'
    check = {'coverage': {**coverage, 'accelerator_executed': True,
                          'instruction_counters': {'system.maa.numInst': 5}}}
    assert bfs_protocol.accelerator_cases(check) == {'executed'}
