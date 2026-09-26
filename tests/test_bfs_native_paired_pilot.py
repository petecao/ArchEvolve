"""Bounded paired-driver contract fixtures; no calibration. Created: 2026-09-26 ET."""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

import pytest

from scripts import bfs_native_paired_pilot as driver
from scripts import bfs_process
from swdb import artifacts, bfs_native, bfs_native_pair, bfs_protocol, yamlio
from swdb.store import Store


def test_all_retained_first_blocks_generate_the_exact_new_unchanged_pair_requests():
    plan = yamlio.load(driver.PLAN)
    driver.validate_plan(plan)
    store = Store(driver.ROOT / 'records')
    machine = store.get('mbit10', 'machine')
    for cell in plan['cells']:
        first = store.get(cell['first_evaluation'], 'evaluation')
        before = copy.deepcopy(first)
        request = driver.pair_request(first, cell, machine)
        assert request['collection'] == driver.COLLECTION
        assert request['budget']['total_seconds'] == 2400
        for role in bfs_native_pair.ROLES:
            member = request[role]
            assert member['id'] == cell[role + '_evaluation']
            assert member['candidate'] == first['candidate']
            assert member['sources'] == [0, 1234, 7777]
            assert member['repetitions'] == 10 and member.get('warmups', 0) == 0
            assert member.get('protocol') is None
            assert member['budget']['total_seconds'] == 2400
        assert first == before


@pytest.mark.parametrize('fault', ['id', 'lane', 'count', 'order', 'retry', 'warmup-bool',
                                   'source-bool', 'deadline', 'spread', 'rss', 'gap', 'analysis'])
def test_plan_rejects_changes_to_prospective_identity_policy_or_bounds(fault):
    plan = yamlio.load(driver.PLAN)
    if fault == 'id': plan['id'] += '.retry'
    elif fault == 'lane': plan['lane'] = 'mbit10-evaluation-node0'
    elif fault == 'count': plan['cells'].pop()
    elif fault == 'order': plan['cells'].reverse()
    elif fault == 'retry': plan['bounds']['retries'] = 1
    elif fault == 'warmup-bool': plan['bounds']['warmups'] = False
    elif fault == 'source-bool': plan['sources'][0] = False
    elif fault == 'deadline': plan['deadline_et'] = '2026-09-26T16:00:00-04:00'
    elif fault == 'spread': plan['maximum_relative_spread'] = .11
    elif fault == 'rss': plan['bounds']['sampled_rss_bytes'] *= 2
    elif fault == 'gap': plan['bounds']['resource_max_gap_seconds'] = 31
    else: plan['analysis'] = 'bootstrap_source_medians.v1'
    with pytest.raises(ValueError):
        driver.validate_plan(plan)


def test_new_finite_deadline_requires_the_entire_outer_allowance_without_resetting_old_pilot():
    latest = driver.DEADLINE - timedelta(seconds=10920)
    assert latest.hour == 11 and latest.minute == 58
    assert driver.launch_budget(latest) == 10800
    assert driver.launch_budget(latest - timedelta(hours=1)) == 10800
    with pytest.raises(ValueError, match='complete outer allowance'):
        driver.launch_budget(latest + timedelta(microseconds=1))
    with pytest.raises(ValueError):
        driver.launch_budget(driver.DEADLINE)
    assert driver.previous.PILOT_DEADLINE.hour == 5


@pytest.mark.parametrize('changed', [True, False])
def test_public_driver_rejects_a_changed_or_relocated_plan_before_creating_run_artifacts(tmp_path, changed):
    plan = yamlio.load(driver.PLAN)
    if changed:
        plan['bounds']['retries'] = 1
    request = tmp_path / 'changed-plan.json'
    request.write_text(json.dumps(plan))
    runs = tmp_path / 'not-created'
    result = subprocess.run([sys.executable, str(Path(driver.__file__)), '--plan', str(request),
        '--runs-dir', str(runs), '--lane', driver.LANE], cwd=driver.ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert ('paired plan changes fixed identities' if changed else 'exact canonical plan path') in result.stderr
    assert not runs.exists()


def fake_process(proc, pid, parent, start, *, rss=10, children=(), extra_thread=()):
    folder = proc / str(pid)
    folder.mkdir(parents=True, exist_ok=True)
    fields = ['S', str(parent)] + ['0'] * 17 + [str(start)]
    (folder / 'stat').write_text(f'{pid} (fixture process) ' + ' '.join(fields))
    (folder / 'status').write_text(f'Name:\tfixture\nVmRSS:\t{rss} kB\n')
    task = folder / 'task' / str(pid)
    task.mkdir(parents=True, exist_ok=True)
    (task / 'children').write_text(' '.join(map(str, children)))
    if extra_thread:
        other = folder / 'task' / str(pid + 1000)
        other.mkdir(exist_ok=True)
        (other / 'children').write_text(' '.join(map(str, extra_thread)))


def test_rss_follows_all_threads_and_observed_descendants_across_new_sessions_and_reparenting(tmp_path):
    # Session/process-group fields are zero: ownership depends on parentage, not a group.
    fake_process(tmp_path, 100, 1, 1000, children=[101], extra_thread=[102])
    fake_process(tmp_path, 101, 100, 1001, children=[103])
    fake_process(tmp_path, 102, 100, 1002)
    fake_process(tmp_path, 103, 101, 1003)
    sampler = driver.DescendantRSS(100, tmp_path)
    assert sampler.sample()['rss_bytes'] == 40 * 1024
    fake_process(tmp_path, 100, 1, 1000)
    shutil.rmtree(tmp_path / '100/task/1100')
    fake_process(tmp_path, 101, 1, 1001, children=[103])
    assert {r['pid'] for r in sampler.sample()['processes']} == {100, 101, 102, 103}
    # A PID reused by an unrelated process is no longer charged as our descendant.
    fake_process(tmp_path, 101, 999, 2001)
    assert 101 not in {r['pid'] for r in sampler.sample()['processes']}


def test_rss_fails_closed_for_stale_child_list_with_unrelated_reused_pid(tmp_path):
    fake_process(tmp_path, 100, 1, 1000, children=[101])
    fake_process(tmp_path, 101, 999, 2001)
    with pytest.raises(ValueError, match='discovering parent'):
        driver.DescendantRSS(100, tmp_path).sample()


def test_rss_missing_live_telemetry_fails_but_exited_child_is_not_an_error(tmp_path):
    fake_process(tmp_path, 100, 1, 1000, children=[101])
    assert driver.DescendantRSS(100, tmp_path).sample()['rss_bytes'] == 10 * 1024
    (tmp_path / '100/status').unlink()
    with pytest.raises(ValueError, match='live owned process telemetry'):
        driver.DescendantRSS(100, tmp_path).sample()


def test_stalled_observer_is_rejected_by_the_owned_stage_watchdog(monkeypatch):
    monitor = driver.ResourceMonitor(lambda: None)
    monitor.last_observation_started = 100.0
    monkeypatch.setattr(driver.time, 'monotonic', lambda: 130.0)
    monitor.check()
    monkeypatch.setattr(driver.time, 'monotonic', lambda: 130.01)
    with pytest.raises(ValueError, match='telemetry is stale'):
        monitor.check()


def test_slow_post_rss_guard_work_does_not_reset_the_observation_age(monkeypatch):
    current = [100.0]
    monkeypatch.setattr(driver.time, 'monotonic', lambda: current[0])
    def observe():
        current[0] = 129.0  # RSS read at the start; storage observation takes 29 seconds.
    monitor = driver.ResourceMonitor(observe)
    monitor.start()
    try:
        monitor.check()
        current[0] = 130.01
        with pytest.raises(ValueError, match='telemetry is stale'):
            monitor.check()
    finally:
        monitor.stop()


def driver_receipt_fixture(tmp_path, monkeypatch):
    """Metadata-only receipt fixture for admission-reader integration, never timing evidence.

    Only the host-specific raw-volume selector is substituted. Real source modules,
    retained old records, canonical plan and all retained request/log hashes are read.
    Public result bodies are explicit fixture stand-ins; validate_pair_result must
    still independently reject these as performance evidence.
    """
    plan = yamlio.load(driver.PLAN)
    runs = tmp_path / 'fixture-runs'
    folder = runs / (driver.RUN_ID + '.driver')
    folder.mkdir(parents=True)
    monkeypatch.setattr(driver.previous, 'raw_root', lambda value: Path(value).resolve())
    store = Store(driver.ROOT / 'records')
    machine = store.get('mbit10', 'machine')
    started = datetime(2026, 9, 26, 9, 0, tzinfo=driver.DEADLINE.tzinfo)
    receipt = {'id': driver.RUN_ID, 'state': 'complete', 'role': 'paired_unchanged_native_calibration',
        'gain_claim': False, 'protocol_freeze': False, 'profiling': False,
        'bounds': copy.deepcopy(driver.BOUNDS), 'deadline_et': driver.DEADLINE.isoformat(),
        'started': started.isoformat(), 'finished': (started + timedelta(seconds=25)).isoformat(), 'host_wall_s': 25,
        'plan': {'path': str(driver.PLAN), 'sha256': artifacts.file_hash(driver.PLAN), 'canonical_sha256': artifacts.digest(plan)},
        'records': str(driver.ROOT / 'records'), 'runs_dir': str(runs), 'driver_pid': 100,
        'repository_commit': 'a' * 40, 'lane': driver.LANE + ' (verified: affinity, bind:1, lease held, generation 999999)',
        'inherited_runtime_settings': {name: None for name in driver.RUNTIME_SETTINGS},
        'batch_raw_bytes_sampled': 20, 'batch_raw_bytes_peak_sampled': 20, 'cells': [], 'stages': [],
        'runtime': {'python_executable': str(Path(sys.executable).resolve()),
                    'python_sha256': artifacts.file_hash(Path(sys.executable).resolve()), 'modules': {}}}

    def write_ref(path, value):
        path.write_bytes(value if isinstance(value, bytes) else value.encode())
        return {'path': str(path), 'sha256': artifacts.file_hash(path)}

    for name, source in {'native': bfs_native.__file__, 'pair': bfs_native_pair.__file__,
                          'protocol': bfs_protocol.__file__, 'driver': driver.__file__, 'process': bfs_process.__file__}.items():
        ref = write_ref(folder / (name + '-runtime.py'), Path(source).read_bytes())
        ref['source_path'] = str(Path(source).resolve())
        receipt['runtime']['modules'][name] = ref
    receipt['verifier_module_sha256'] = receipt['runtime']['modules']['native']['sha256']
    receipt['paired_module_sha256'] = receipt['runtime']['modules']['pair']['sha256']
    samples = []
    for offset in (1, 6, 11, 16, 21, 24):
        stamp = (started + timedelta(seconds=offset)).isoformat()
        samples.append({'sampled_at': stamp, 'guard_started': stamp, 'guard_finished': stamp, 'guard_wall_s': 0,
                        'rss_bytes': 1024, 'processes': [{'pid': 100, 'parent_pid': 1, 'start_ticks': 10, 'rss_bytes': 1024}],
                        'batch_raw_bytes': 20, 'raw_free_bytes': 40 * 1024**3, 'build_free_bytes': 20 * 1024**3,
                        'lane': receipt['lane']})
    rss_ref = write_ref(folder / 'rss-samples.jsonl', ''.join(json.dumps(row) + '\n' for row in samples))
    receipt['rss'] = {'scope': 'driver and observed owned descendants across sessions; PID/start-time bound',
                      'nominal_interval_seconds': 5, 'true_peak': False, 'hard_kernel_cap': False,
                      'peak_sampled_bytes': 1024, 'last_sampled_bytes': 1024, 'maximum_gap_seconds': 5,
                      'maximum_guard_seconds': 0, 'samples': rss_ref}

    def stage(command, output, body, timeout):
        index = len(receipt['stages'])
        out = write_ref(output, body)
        err = write_ref(folder / (f'{index:02d}' + '.stderr'), '')
        receipt['stages'].append({'command': command, 'state': 'complete', 'returncode': 0,
            'output': out['path'], 'stdout_sha256': out['sha256'], 'stderr': err['path'], 'stderr_sha256': err['sha256'],
            'timeout_s': timeout, 'host_wall_s': .1})

    stage(['git', 'rev-parse', 'HEAD'], folder / 'repository-commit.txt', 'a' * 40 + '\n', 10)
    for cell_index, cell in enumerate(plan['cells']):
        first = store.get(cell['first_evaluation'], 'evaluation')
        # Reopen the actual local compiler path; simulated version stdout remains a fixture.
        compiler = str(Path(first['build']['compiler']).resolve(strict=True))
        request = driver.pair_request(first, cell, machine)
        ref = write_ref(folder / (cell['id'] + '.request.json'), json.dumps(request))
        entry = {'id': cell['id'], 'state': 'complete', 'first_evaluation': cell['first_evaluation'],
                 'first_record_sha256': cell['first_evaluation_sha256'], 'pair': cell['id'],
                 'baseline_evaluation': cell['baseline_evaluation'], 'candidate_evaluation': cell['candidate_evaluation'],
                 'compiler_resolved': compiler, 'compiler_sha256': artifacts.file_hash(compiler), 'request': ref,
                 'started': (started + timedelta(seconds=2 + 5 * cell_index)).isoformat(),
                 'finished': (started + timedelta(seconds=6 + 5 * cell_index)).isoformat()}
        receipt['cells'].append(entry)
        stage([compiler, '--version'], folder / (cell['id'] + '.compiler-version.txt'),
              '\n'.join(first['build']['compiler_version']) + '\n', 30)
    for cell, entry in zip(plan['cells'], receipt['cells']):
        result = {'id': cell['id'], 'evidence_kind': 'fixture', 'gain_claim': False,
                  'started': entry['started'], 'prepared_at': entry['started'],
                  'finished': entry['finished']}
        entry['pair_sha256'] = artifacts.digest(result)
        command = [receipt['runtime']['python_executable'], '-m', 'swdb', 'evaluate-pair', entry['request']['path'],
                   '--runs-dir', str(runs), '--lane', driver.LANE, '--records', str(driver.ROOT / 'records'), '--format', 'json']
        stage(command, folder / (cell['id'] + '.result.json'), json.dumps(result), 2460)
        receipt['stages'][-1]['host_wall_s'] = 4
    return plan, receipt, samples


def reseal_samples(receipt, samples):
    path = Path(receipt['rss']['samples']['path'])
    path.write_text(''.join(json.dumps(row) + '\n' for row in samples))
    receipt['rss']['samples']['sha256'] = artifacts.file_hash(path)


def test_driver_reader_reopens_all_metadata_and_preserves_fixture_boundary(tmp_path, monkeypatch):
    plan, receipt, _ = driver_receipt_fixture(tmp_path, monkeypatch)
    refs = driver.validate_driver_receipt(receipt, plan)
    assert len(refs) == 29
    assert all(artifacts.file_hash(ref['path']) == ref['sha256'] for ref in refs)
    assert all(json.loads(Path(row['output']).read_text())['evidence_kind'] == 'fixture' for row in receipt['stages'][5:])
    assert receipt['gain_claim'] is False


@pytest.mark.parametrize('fault', ['elapsed', 'absolute', 'late-start', 'command', 'request', 'result',
    'runtime', 'plan-digest', 'preflight-command', 'stderr', 'extra-attempt', 'missing-cell', 'raw-over',
    'rss-over', 'declared-peak', 'gap', 'gap-start', 'guard', 'orphan', 'cycle', 'root-reused',
    'lane-missing', 'lane-bare', 'lane-node0', 'runtime-settings-missing', 'runtime-settings-key', 'runtime-settings-type',
    'compiler', 'pair-before-cell', 'pair-after-cell', 'pair-budget', 'pair-reversed', 'cell-overlap'])
def test_driver_reader_rejects_resealed_but_invalid_collection_receipts(tmp_path, monkeypatch, fault):
    plan, receipt, samples = driver_receipt_fixture(tmp_path, monkeypatch)
    if fault == 'elapsed': receipt['host_wall_s'] = 10801
    elif fault == 'absolute': receipt['finished'] = '2026-09-26T15:00:01-04:00'
    elif fault == 'late-start': receipt['started'] = '2026-09-26T11:58:01-04:00'
    elif fault == 'command': receipt['stages'][5]['command'][3] = 'evaluate'
    elif fault == 'request':
        ref = receipt['cells'][0]['request']; path = Path(ref['path'])
        data = json.loads(path.read_text()); data['baseline']['repetitions'] = 5
        path.write_text(json.dumps(data)); ref['sha256'] = artifacts.file_hash(path)
    elif fault == 'result':
        stage = receipt['stages'][5]; path = Path(stage['output'])
        path.write_text('{}'); stage['stdout_sha256'] = artifacts.file_hash(path)
    elif fault == 'runtime':
        ref = receipt['runtime']['modules']['native']; Path(ref['path']).write_text('# replaced\n')
        ref['sha256'] = artifacts.file_hash(ref['path'])
    elif fault == 'plan-digest': receipt['plan']['canonical_sha256'] = 'f' * 64
    elif fault == 'preflight-command': receipt['stages'][0]['command'] = ['echo', 'a' * 40]
    elif fault == 'stderr': Path(receipt['stages'][0]['stderr']).write_text('changed')
    elif fault == 'extra-attempt': receipt['stages'].append(copy.deepcopy(receipt['stages'][-1]))
    elif fault == 'missing-cell': receipt['cells'].pop()
    elif fault == 'raw-over': samples[1]['batch_raw_bytes'] = driver.BOUNDS['batch_raw_bytes'] + 1
    elif fault == 'rss-over':
        samples[1]['processes'][0]['rss_bytes'] = driver.BOUNDS['sampled_rss_bytes'] + 1
        samples[1]['rss_bytes'] = driver.BOUNDS['sampled_rss_bytes'] + 1
    elif fault == 'declared-peak': receipt['rss']['peak_sampled_bytes'] = 1
    elif fault.startswith('runtime-settings'):
        if fault == 'runtime-settings-missing': receipt.pop('inherited_runtime_settings')
        elif fault == 'runtime-settings-key': receipt['inherited_runtime_settings']['OTHER'] = None
        else: receipt['inherited_runtime_settings']['OMP_THREAD_LIMIT'] = 4
    elif fault.startswith('lane-'):
        if fault == 'lane-missing':
            receipt.pop('lane')
            for row in samples: row.pop('lane')
        else:
            receipt['lane'] = driver.LANE if fault == 'lane-bare' else 'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 999999)'
            for row in samples: row['lane'] = receipt['lane']
    elif fault == 'compiler':
        receipt['cells'][0]['compiler_resolved'] = str(Path(sys.executable).resolve())
        receipt['cells'][0]['compiler_sha256'] = artifacts.file_hash(sys.executable)
        receipt['stages'][1]['command'][0] = receipt['cells'][0]['compiler_resolved']
    elif fault.startswith('pair-'):
        stage = receipt['stages'][5]; path = Path(stage['output']); result = json.loads(path.read_text())
        if fault == 'pair-before-cell': result['started'] = receipt['started']
        elif fault == 'pair-after-cell': result['finished'] = receipt['finished']
        elif fault == 'pair-reversed': result['prepared_at'] = receipt['finished']
        else: result['finished'] = '2026-09-26T09:41:00-04:00'
        path.write_text(json.dumps(result)); stage['stdout_sha256'] = artifacts.file_hash(path)
        receipt['cells'][0]['pair_sha256'] = artifacts.digest(result)
    elif fault == 'cell-overlap': receipt['cells'][1]['started'] = receipt['cells'][0]['started']
    elif fault == 'gap':
        receipt['finished'] = '2026-09-26T09:01:00-04:00'; receipt['host_wall_s'] = 60
        receipt['rss']['maximum_gap_seconds'] = 36
    elif fault == 'gap-start':
        receipt['started'] = '2026-09-26T08:59:30-04:00'; receipt['host_wall_s'] = 55
        receipt['rss']['maximum_gap_seconds'] = 31
    elif fault == 'guard': samples[1]['guard_wall_s'] = 31
    elif fault in ('orphan', 'cycle'):
        samples[1]['processes'].append({'pid': 200, 'parent_pid': 999 if fault == 'orphan' else 201,
                                        'start_ticks': 20, 'rss_bytes': 0})
        if fault == 'cycle':
            samples[1]['processes'].append({'pid': 201, 'parent_pid': 200, 'start_ticks': 21, 'rss_bytes': 0})
    else: samples[1]['processes'][0]['start_ticks'] = 11
    reseal_samples(receipt, samples)
    with pytest.raises(ValueError):
        driver.validate_driver_receipt(receipt, plan)


def test_reader_allows_reparenting_only_after_observing_same_owned_identity(tmp_path, monkeypatch):
    plan, receipt, samples = driver_receipt_fixture(tmp_path, monkeypatch)
    for index, sample in enumerate(samples):
        sample['processes'].append({'pid': 200, 'parent_pid': 100 if index == 0 else 1, 'start_ticks': 20, 'rss_bytes': 0})
    reseal_samples(receipt, samples)
    driver.validate_driver_receipt(receipt, plan)
    samples[1]['processes'][-1]['start_ticks'] = 21
    reseal_samples(receipt, samples)
    with pytest.raises(ValueError, match='not connected'):
        driver.validate_driver_receipt(receipt, plan)


@pytest.mark.parametrize('fault', [None, 'before-pair', 'after-pair', 'reversed', 'build-budget', 'run-budget'])
def test_each_member_build_and_trial_must_fit_inside_its_actual_pair_budget(fault):
    begin = datetime(2026, 9, 26, 9, 0, tzinfo=driver.DEADLINE.tzinfo)
    end = begin + timedelta(seconds=2400)
    stage = {'stage': 'execution', 'started': begin.isoformat(), 'finished': (begin + timedelta(seconds=60)).isoformat()}
    if fault == 'before-pair': stage['started'] = (begin - timedelta(seconds=1)).isoformat()
    elif fault == 'after-pair': stage['finished'] = (end + timedelta(seconds=1)).isoformat()
    elif fault == 'reversed': stage['finished'] = (begin - timedelta(seconds=1)).isoformat()
    elif fault == 'build-budget':
        stage.update(stage='build', finished=(begin + timedelta(seconds=181)).isoformat())
    elif fault == 'run-budget': stage['finished'] = (begin + timedelta(seconds=61)).isoformat()
    if fault is None:
        driver.validate_member_interval({'stages': [stage]}, begin, end)
    else:
        with pytest.raises(ValueError):
            driver.validate_member_interval({'stages': [stage]}, begin, end)


def test_inflight_monitor_failure_during_stop_cannot_interrupt_receipt_persistence(tmp_path):
    # Run the actual signal handler/monitor in a disposable process, never pytest's process.
    script = '''
import json, threading, time
from pathlib import Path
from scripts.bfs_native_paired_pilot import ResourceMonitor
from scripts.bfs_process import interruption_signals
entered, release = threading.Event(), threading.Event()
calls = 0
def fail():
    global calls
    calls += 1
    if calls == 1: return
    entered.set(); release.wait(2); raise ValueError('fixture guard failure')
m = ResourceMonitor(fail)
with interruption_signals():
    m.start(); assert entered.wait(8)
    threading.Timer(.05, release.set).start()
    try: raise ValueError('fixture preflight failure')
    except ValueError:
        m.stop()
        Path('final.json').write_text(json.dumps({'state':'failed','reason':str(m.error)}))
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=tmp_path,
        env={**__import__('os').environ, 'PYTHONPATH': str(driver.ROOT)}, capture_output=True, text=True, timeout=12)
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / 'final.json').read_text()) == {'state': 'failed', 'reason': 'fixture guard failure'}


def test_live_monitor_failure_interrupts_and_reaps_owned_stage(tmp_path):
    script = '''
import json, time
from pathlib import Path
from scripts.bfs_native_paired_pilot import ResourceMonitor
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
receipt={'stages':[]}; calls=0
def sample():
    global calls
    calls += 1
    if calls > 1: raise ValueError('fixture RSS ceiling exceeded')
m=ResourceMonitor(sample)
with interruption_signals():
    try:
        m.start()
        run_stage(receipt, Path('.'), [__import__('sys').executable,'-c','import time; print("fixture child",flush=True); time.sleep(60)'],
                  timeout=15, deadline=time.monotonic()+15, cwd=Path('.'), monitor=m.check)
    except BaseException as exc: receipt.update(state='failed', reason=str(exc))
    finally:
        m.stop(); save_receipt(Path('.'),receipt)
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=tmp_path,
        env={**__import__('os').environ, 'PYTHONPATH': str(driver.ROOT)}, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    saved = json.loads((tmp_path / 'driver.json').read_text())
    assert saved['state'] == 'failed'
    assert saved['stages'][0]['returncode'] is not None
    assert saved['stages'][0]['state'] in ('interrupted_or_timeout', 'failed')
    assert Path(tmp_path / saved['stages'][0]['output']).read_text() == 'fixture child\n'
