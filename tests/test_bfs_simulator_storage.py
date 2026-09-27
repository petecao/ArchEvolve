"""Dispatch storage belongs to the existing batch cap. Dated 2026-09-26 ET.

Small allocated files and scaled byte units are contract fixtures, not host runs.
"""
from datetime import datetime, timedelta
from contextlib import nullcontext
import json
from pathlib import Path
import sys

import pytest

from scripts import bfs_simulator_batch as batch
from scripts import bfs_simulator_batch_terminal as terminal
from scripts import bfs_linux_fixture as fixture_runner
from swdb import artifacts


def roots(tmp_path):
    runs = tmp_path / 'bfs-t15-simulator-batch-20260926-a1'
    dispatch = Path(str(runs) + '.dispatch')
    runs.mkdir(); dispatch.mkdir()
    return runs, dispatch


def test_finalization_charges_large_dispatch_to_unchanged_batch_cap(tmp_path, monkeypatch):
    runs, dispatch = roots(tmp_path)
    folder = runs / (runs.name + '.driver'); folder.mkdir()
    (dispatch / 'outer.stdout').write_bytes(b'x' * (256 * 1024))
    policy = json.loads((batch.PLAN_DIR / 'bfs-t15-simulator-batch-20260926-a1.json').read_text())
    monkeypatch.setattr(batch, 'GIB', 4096)  # Same fixed 40-unit cap, small real allocation.
    end = datetime.now(batch.ET) + timedelta(minutes=1)
    class Ledger:
        bounds = policy['bounds']; monotonic_end = batch.time.monotonic() + 60
        started = batch.time.monotonic()
        def observation(self, raw): return {'raw_bytes': raw, 'charged_raw_bytes': raw}
    ledger = Ledger(); ledger.end = end
    assert batch.allocated_bytes([runs]) < policy['bounds']['batch_storage_gib'] * batch.GIB
    receipt = {'state': 'complete'}
    with pytest.raises(ValueError, match='common allowance'):
        batch.finalize_receipt(receipt, folder, runs, ledger, folder/'absent-ledger')
    assert json.loads((folder/'driver.json').read_text())['state'] == 'failed'


def test_storage_roots_are_exact_canonical_siblings_counted_once(tmp_path):
    runs, dispatch = roots(tmp_path)
    (runs/'raw').write_bytes(b'a' * 8192)
    (dispatch/'helper.log').write_bytes(b'b' * 32768)
    paths = batch.batch_storage_paths(runs)
    assert paths == [runs, dispatch]
    assert batch.allocated_bytes(paths) == batch.allocated_bytes([runs]) + batch.allocated_bytes([dispatch])


def test_public_monitor_refuses_large_dispatch_before_any_series(tmp_path, monkeypatch):
    """Use main's actual monitor and allocated disk bytes, with no host child."""
    from test_bfs_simulator_batch import plan, admission
    policy = plan(); begin = batch.now(); approval = admission(policy, started=begin)
    runs = tmp_path/policy['id']; dispatch = Path(str(runs)+'.dispatch'); dispatch.mkdir()
    (dispatch/'outer.stdout').write_bytes(b'x' * (256 * 1024))
    class Budget:
        create = staticmethod(lambda *args, **kwargs: 'fixture-binding')
        def __init__(self, *args): pass
        def reservation(self): return nullcontext(batch.time.monotonic()+5)
        def snapshot(self): return {}
    class Owner:
        def __init__(self, budget): self.budget=budget; self.history={}
        def finish(self, *args, **kwargs): return {'state':'all_owned_descendants_absent','errors':[]}
        def sample(self): pytest.fail('storage must reject before RSS or any child stage')
    class Guard:
        def __init__(self, callback):
            self.callback=callback; self.maximum_gap_seconds=self.maximum_guard_seconds=0
        def start(self): self.callback()
        def stop(self, deadline): pass
    monkeypatch.setattr(sys, 'argv', ['batch','t15','--admission',str(tmp_path/'admission'),
        '--admission-sha256','fixture','--runs-dir',str(runs),'--lane','1',
        '--outer-started',begin.isoformat(),'--outer-deadline',(begin+timedelta(seconds=43200)).isoformat(),
        '--pane-pid','10','--pane-start-ticks','100'])
    monkeypatch.setattr(batch, 'GIB', 4096)
    monkeypatch.setattr(batch, 'RAW_ROOTS', (tmp_path,))
    monkeypatch.setattr(batch, 'read_reference', lambda *args: approval)
    monkeypatch.setattr(batch.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(batch.lifecycle, 'SharedCleanup', Budget)
    monkeypatch.setattr(batch.lifecycle, 'Owned', Owner)
    monkeypatch.setattr(batch.lifecycle, 'Monitor', Guard)
    monkeypatch.setattr(batch.lifecycle, 'identity', lambda pid: {'pid':pid,'start_ticks':1})
    monkeypatch.setattr(batch.lifecycle, 'ancestry', lambda *args: [])
    monkeypatch.setattr(batch, 'collect_series', lambda *args: pytest.fail('must not launch a series'))
    with pytest.raises(ValueError, match='shared batch raw-storage ceiling'):
        batch.main()
    saved = json.loads((runs/(runs.name+'.driver')/'driver.json').read_text())
    assert saved['state']=='failed' and saved['stages']==[] and saved['series']==[]
    assert saved['storage_paths']==[str(runs),str(dispatch)]


@pytest.mark.parametrize('fault', ['missing', 'symlink', 'not-directory', 'relative', 'parent-symlink'])
def test_storage_roots_reject_missing_or_redirected_dispatch(tmp_path, fault):
    runs, dispatch = roots(tmp_path)
    if fault in {'missing', 'symlink', 'not-directory'}:
        dispatch.rmdir()
        if fault == 'symlink': dispatch.symlink_to(runs, target_is_directory=True)
        if fault == 'not-directory': dispatch.write_text('not a directory')
    elif fault == 'relative': runs = Path(runs.name)
    else:
        link = tmp_path/'link'; link.symlink_to(tmp_path, target_is_directory=True)
        runs = link/runs.name
    with pytest.raises(ValueError, match='storage'):
        batch.batch_storage_paths(runs)


@pytest.fixture
def closed_storage(tmp_path, monkeypatch):
    runs, dispatch = roots(tmp_path)
    monkeypatch.setattr(batch, 'RAW_ROOTS', (tmp_path,))
    monkeypatch.setattr(batch, 'GIB', 4096)
    plan = json.loads((batch.PLAN_DIR/'bfs-t15-simulator-batch-20260926-a1.json').read_text())
    folder = runs/(runs.name+'.driver'); folder.mkdir()
    driver_path = folder/'driver.json'; terminal_path = dispatch/'terminal-validation.json'
    driver = {'id': plan['id'], 'state': 'complete', 'plan': plan, 'plan_sha256': artifacts.digest(plan),
        'finished': '2026-09-26T10:00:00-04:00', 'preparation_charges': [],
        'storage_paths': [str(runs), str(dispatch)], 'final_ledger': {'raw_bytes': 0, 'charged_raw_bytes': 0}}
    def seal():
        driver_path.write_text(json.dumps(driver))
        driver_ref = {'path': str(driver_path), 'sha256': artifacts.file_hash(driver_path)}
        audit = {'id': plan['id'], 'state': driver['state'], 'driver': driver_ref,
            'cleanup_state': 'terminal_and_reaped', 'lease_released': True,
            'observed_at': '2026-09-26T10:01:00-04:00'}
        terminal_path.write_text(json.dumps(audit))
        return driver_ref, {'path': str(terminal_path), 'sha256': artifacts.file_hash(terminal_path)}
    return runs, dispatch, driver, seal


def test_terminal_recounts_helper_and_its_own_persisted_audit_outputs(closed_storage):
    runs, dispatch, driver, seal = closed_storage
    refs = seal()
    result = terminal.validate_storage_accounting(*refs, current='2026-09-26T10:02:00-04:00')
    assert result['state'] == 'within_existing_storage_budget'
    assert result['raw_bytes'] == batch.allocated_bytes([runs, dispatch])
    assert result['raw_bytes'] > driver['final_ledger']['raw_bytes']
    # This is the caller's required last-write recheck, without another write.
    (dispatch/'storage-readback.json').write_text(json.dumps(result))
    (dispatch/'outer.stdout').write_bytes(b'x' * (256 * 1024))
    with pytest.raises(ValueError, match='storage ceiling'):
        terminal.validate_storage_accounting(*refs, current='2026-09-26T10:02:01-04:00')


@pytest.mark.parametrize('fault', ['extra-root', 'duplicate-root', 'changed-plan', 'omitted-preparation', 'wrong-audit-driver'])
def test_terminal_storage_rejects_resealed_accounting_substitutions(closed_storage, fault, monkeypatch):
    runs, dispatch, driver, seal = closed_storage
    if fault == 'extra-root': driver['storage_paths'].append(str(runs.parent))
    elif fault == 'duplicate-root': driver['storage_paths'] = [str(runs), str(runs)]
    elif fault == 'changed-plan':
        driver['plan']['bounds']['batch_storage_gib'] += 1
        driver['plan_sha256'] = artifacts.digest(driver['plan'])
    elif fault == 'omitted-preparation':
        monkeypatch.setattr(batch, 'preparation_charges', lambda plan: [{'id': 'retained.fixture', 'raw_bytes': 1024}])
    refs = seal()
    if fault == 'wrong-audit-driver':
        path = Path(refs[1]['path']); value = json.loads(path.read_text())
        value['driver']['sha256'] = 'f'*64; path.write_text(json.dumps(value))
        refs[1]['sha256'] = artifacts.file_hash(path)
    with pytest.raises(ValueError):
        terminal.validate_storage_accounting(*refs, current='2026-09-26T10:02:00-04:00')


def test_only_consumed_simulator_fixture_ids_advance():
    assert fixture_runner.SELECTIONS['owned_cleanup'][0] == 'bfs-simulator-owned-linux-20260926-a3'
    assert fixture_runner.SELECTIONS['dx100_interruption'][0] == 'bfs-simulator-interruption-linux-20260926-a3'
    assert fixture_runner.SELECTIONS['native_campaign_owned_cleanup'][0] == 'bfs-native-campaign-owned-linux-20260926-a1'
