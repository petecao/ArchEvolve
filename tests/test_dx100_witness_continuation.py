"""Synthetic a3 admission checks, never simulator evidence. Created: 2026-09-26 ET."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import sys

import pytest

from scripts import dx100_witness_continuation as continuation
from swdb import artifacts, yamlio


def test_deadline_requires_full_original_outer_window():
    latest = continuation.DEADLINE - timedelta(seconds=1200)
    assert latest.isoformat() == '2026-09-26T15:20:00-04:00'
    assert continuation.launch_budget(latest) == 1170
    assert continuation.launch_budget(latest - timedelta(hours=3)) == 1170
    for current in (latest + timedelta(microseconds=1), continuation.DEADLINE,
                    latest.replace(tzinfo=None)):
        with pytest.raises(ValueError, match='full 1200-second window'):
            continuation.launch_budget(current)


def test_exact_a3_request_changes_only_id_from_failed_a1():
    request = yamlio.load(continuation.REQUEST)
    failed = yamlio.load(continuation.ROOT / 'records/evaluations' / (continuation.FAILED_ID + '.yaml'))
    prior = yamlio.load(continuation.ROOT / 'records/evaluations' / (continuation.PRIOR_ID + '.yaml'))
    expected = deepcopy(failed['request'])
    expected['id'] = continuation.PROBE_ID
    assert request == expected
    continuation.validate_request(request, prior)
    for field, key, value in (
        ('budget', 'run_seconds', 751), ('budget', 'total_seconds', 1101),
        ('budget', 'memory_gib', 64), ('budget', 'storage_gib', 3),
        ('verification', 'max_ticks', 10**12), ('workload', 'source', 1),
        ('simulator', 'sha256', '0' * 64), ('binary', 'sha256', '0' * 64),
        ('checkpoint_manifest', 'sha256', '0' * 64),
    ):
        changed = deepcopy(request)
        changed[field][key] = value
        with pytest.raises(ValueError, match='exact prospective identity'):
            continuation.validate_request(changed, prior)
    with pytest.raises(ValueError, match='exact prospective identity'):
        continuation.validate_request({**request, 'id': continuation.EXPIRED_ID}, prior)


@pytest.fixture
def history(tmp_path):
    records, runs = tmp_path / 'records', tmp_path / 'runs'
    (records / 'evaluations').mkdir(parents=True)
    runs.mkdir()
    original = (continuation.ROOT / 'records/evaluations' / (continuation.FAILED_ID + '.yaml')).read_bytes()
    failed = records / 'evaluations' / (continuation.FAILED_ID + '.yaml')
    failed.write_bytes(original)
    return records, runs, failed, original


def test_history_retains_failed_record_and_never_writes(history):
    records, runs, failed, original = history
    assert continuation.validate_history(records, runs) == failed
    assert failed.read_bytes() == original
    failed.write_bytes(original + b'\n')
    with pytest.raises(ValueError, match='unchanged retained failed a1'):
        continuation.validate_history(records, runs)
    failed.unlink()
    with pytest.raises(ValueError, match='unchanged retained failed a1'):
        continuation.validate_history(records, runs)


@pytest.mark.parametrize('rid', [continuation.EXPIRED_ID, continuation.PROBE_ID])
@pytest.mark.parametrize('kind', ['record', 'output', 'driver', 'broken_symlink'])
def test_history_rejects_every_existing_attempt_path_without_overwrite(history, rid, kind):
    records, runs, failed, original = history
    path = records / 'evaluations' / (rid + '.yaml') if kind == 'record' else runs / (
        rid + '.driver' if kind == 'driver' else rid)
    if kind == 'broken_symlink':
        path.symlink_to(runs / 'missing-target')
    else:
        path.write_text('retain this exact historical content')
    with pytest.raises(ValueError, match='cannot be overwritten or resumed'):
        continuation.validate_history(records, runs)
    assert failed.read_bytes() == original
    if kind == 'broken_symlink':
        assert path.is_symlink()
    else:
        assert path.read_text() == 'retain this exact historical content'


def write_reference(path, value):
    path.write_text(json.dumps(value) if not isinstance(value, str) else value)
    return {'path': str(path), 'sha256': artifacts.file_hash(path)}


def completion_fixture(tmp_path, kind, *, failed=False):
    """A local format fixture, not an observed run or a claim of process cleanup."""
    identity, node, _ = continuation.BATCHES[kind]
    driver = {'id': identity, 'state': ('failed' if failed else 'complete') if kind == 'paired'
              else ('failed_or_interrupted' if failed else 'initial_submissions_finished'),
              'started': '2026-09-26T11:00:01-04:00', 'finished': '2026-09-26T11:01:00-04:00',
              'stages': [{'state': 'failed' if failed else 'complete'}],
              'cells': [{'state': 'not_dispatched' if failed else 'complete'}]}
    samples = write_reference(tmp_path / 'samples.jsonl', {'processes': [{'pid': 101, 'start_ticks': 300}]})
    if kind == 'paired':
        driver.update(driver_pid=101, rss={'samples': samples})
    else:
        driver['resource_artifact'] = samples
    lane = {'socket_lane': {'host': 'mbit10', 'node': node,
            'lease_name': f'mbit10-evaluation-node{node}', 'lease_generation': 400 if node else 318,
            'started_utc': '2026-09-26T15:00:00Z', 'ended_utc': '2026-09-26T15:01:01Z',
            'exit_code': 1 if failed else 0}}
    audit = {'id': identity, 'state': 'terminal_and_reaped',
             'observed_at': '2026-09-26T11:02:00-04:00',
             'driver': write_reference(tmp_path / 'driver.json', driver),
             'lane': write_reference(tmp_path / 'lane.json', lane),
             'outer_exit': write_reference(tmp_path / 'exit', '1\n' if failed else '0\n'),
             'owned_processes': [{'pid': 101, 'start_ticks': 300}],
             'process_observations': write_reference(tmp_path / 'process-observations.json',
                 {'ancestry': [{'pid': 101, 'start_ticks': 300}]}),
             'owned_processes_absent': True, 'lease_released': True}
    proc = tmp_path / 'proc'
    proc.mkdir()
    current = continuation.stamp('2026-09-26T11:03:00-04:00')
    return audit, driver, lane, proc, current


@pytest.mark.parametrize('kind', ['paired', 'provider'])
@pytest.mark.parametrize('failed', [False, True])
def test_terminal_success_and_failure_both_allow_next_independent_attempt(tmp_path, kind, failed):
    audit, _, _, proc, current = completion_fixture(tmp_path, kind, failed=failed)
    ref = write_reference(tmp_path / 'terminal.json', audit)
    result = continuation.validate_completion(ref, kind, current, proc)
    assert result['id'] == continuation.BATCHES[kind][0]
    assert result['audit'] == ref


@pytest.mark.parametrize('fault,reason', [
    ('wrong_id', 'terminal cleanup'), ('unreleased', 'terminal cleanup'),
    ('no_absence', 'terminal cleanup'), ('running', 'not terminal'),
    ('wrong_node', 'lane/outer exit'), ('wrong_lease', 'lane/outer exit'),
    ('wrong_generation', 'lane/outer exit'), ('exit_mismatch', 'lane/outer exit'),
    ('future_audit', 'timestamps'), ('driver_after_lane', 'timestamps'),
    ('naive_timestamp', 'include its zone'), ('active_stage', 'active stage or cell'),
    ('running_cell', 'active stage or cell'), ('empty_processes', 'lacks owned'),
    ('duplicate_process', 'repeats a process'), ('malformed_process', 'malformed'),
    ('changed_driver', 'hash changed'),
])
def test_rehashed_terminal_audits_cannot_bypass_admission(tmp_path, fault, reason):
    audit, driver, lane, proc, current = completion_fixture(tmp_path, 'paired')
    if fault == 'wrong_id': audit['id'] = 'another-batch'
    if fault == 'unreleased': audit['lease_released'] = False
    if fault == 'no_absence': audit['owned_processes_absent'] = False
    if fault == 'running': driver['state'] = 'running'
    if fault == 'wrong_node': lane['socket_lane']['node'] = 0
    if fault == 'wrong_lease': lane['socket_lane']['lease_name'] = 'mbit10-evaluation'
    if fault == 'wrong_generation': lane['socket_lane']['lease_generation'] = True
    if fault == 'exit_mismatch': lane['socket_lane']['exit_code'] = 1
    if fault == 'future_audit': audit['observed_at'] = '2026-09-26T11:04:00-04:00'
    if fault == 'driver_after_lane': driver['finished'] = '2026-09-26T11:02:00-04:00'
    if fault == 'naive_timestamp': driver['finished'] = '2026-09-26T11:01:00'
    if fault == 'active_stage': driver['stages'][0]['state'] = 'running'
    if fault == 'running_cell': driver['cells'][0]['state'] = 'running'
    if fault == 'empty_processes': audit['owned_processes'] = []
    if fault == 'duplicate_process': audit['owned_processes'] *= 2
    if fault == 'malformed_process': audit['owned_processes'][0]['pid'] = True
    audit['driver'] = write_reference(Path(audit['driver']['path']), driver)
    audit['lane'] = write_reference(Path(audit['lane']['path']), lane)
    if fault == 'changed_driver':
        Path(audit['driver']['path']).write_text('{}')
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match=reason):
        continuation.validate_completion(ref, 'paired', current, proc)


def test_live_owned_identity_blocks_even_after_terminal_and_reaped_attestation(tmp_path):
    audit, _, _, proc, current = completion_fixture(tmp_path, 'provider')
    folder = proc / '101'
    folder.mkdir()
    # Linux stat field 22 is start time; comm may itself contain parentheses.
    stat = folder / 'stat'
    stat.write_text('101 (provider (child)) ' + ' '.join(['S', '1'] + ['0'] * 17 + ['300']))
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='prior owned batch process still exists'):
        continuation.validate_completion(ref, 'provider', current, proc)
    stat.write_text(stat.read_text().removesuffix('300') + '301')
    continuation.validate_completion(ref, 'provider', current, proc)  # PID reuse is not the old child.
    stat.write_text('unreadable identity')
    with pytest.raises(ValueError, match='cannot be checked'):
        continuation.validate_completion(ref, 'provider', current, proc)
    stat.unlink()
    with pytest.raises(ValueError, match='cannot be checked'):
        continuation.validate_completion(ref, 'provider', current, proc)


def test_reference_rejects_symlink_and_oversized_receipts(tmp_path):
    path = tmp_path / 'receipt'
    ref = write_reference(path, '{}')
    link = tmp_path / 'link'
    link.symlink_to(path)
    with pytest.raises(ValueError, match='unsafe'):
        continuation.reference({**ref, 'path': str(link)})
    with pytest.raises(ValueError, match='oversized'):
        continuation.reference(ref, limit=1)


def test_helper_second_precision_and_unattempted_cells_are_not_active_jobs(tmp_path):
    audit, driver, lane, proc, current = completion_fixture(tmp_path, 'paired', failed=True)
    driver['finished'] = '2026-09-26T11:01:01.987654-04:00'
    driver['cells'][0]['state'] = 'prepared'
    audit['driver'] = write_reference(Path(audit['driver']['path']), driver)
    ref = write_reference(tmp_path / 'terminal.json', audit)
    continuation.validate_completion(ref, 'paired', current, proc)
    driver['finished'] = '2026-09-26T11:01:02-04:00'
    audit['driver'] = write_reference(Path(audit['driver']['path']), driver)
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='timestamps'):
        continuation.validate_completion(ref, 'paired', current, proc)


@pytest.mark.parametrize('source', ['samples', 'ancestry'])
def test_completion_cannot_omit_sampled_or_ancestral_owned_processes(tmp_path, source):
    audit, driver, _, proc, current = completion_fixture(tmp_path, 'paired')
    if source == 'samples':
        driver['rss']['samples'] = write_reference(tmp_path / 'samples.jsonl',
            {'processes': [{'pid': 101, 'start_ticks': 300}, {'pid': 102, 'start_ticks': 310}]})
    else:
        audit['process_observations'] = write_reference(tmp_path / 'process-observations.json',
            {'ancestry': [{'pid': 101, 'start_ticks': 300}, {'pid': 102, 'start_ticks': 310}]})
    audit['driver'] = write_reference(Path(audit['driver']['path']), driver)
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='omits retained owned'):
        continuation.validate_completion(ref, 'paired', current, proc)


@pytest.mark.parametrize('kind', ['paired', 'provider'])
def test_launcher_zombie_is_truthful_nonrunning_exception_only(tmp_path, kind):
    audit, _, _, proc, current = completion_fixture(tmp_path, kind)
    audit.update(state='terminal_no_live_owned_processes', owned_processes_absent=False,
                 owned_processes_nonrunning=True)
    audit['owned_processes'][0]['state'] = 'absent'
    pid, start = continuation.LAUNCHER_IDENTITIES[kind]
    launcher = {'pid': pid, 'start_ticks': start, 'state': 'Z', 'rss_bytes': 0, 'role': 'tmux_launcher'}
    audit['owned_processes'].append(launcher)
    audit['process_observations'] = write_reference(tmp_path / 'process-observations.json',
        {'ancestry': [{'pid': 101, 'start_ticks': 300}, {'pid': pid, 'start_ticks': start}]})
    ref = write_reference(tmp_path / 'terminal.json', audit)
    folder = proc / str(pid)
    folder.mkdir()
    stat = folder / 'stat'
    def set_stat(state, rss):
        stat.write_text(f'{pid} (bash) ' + ' '.join([state, '1'] + ['0'] * 17 + [str(start), '0', str(rss)]))
    set_stat('Z', 0)
    result = continuation.validate_completion(ref, kind, current, proc)
    assert result['cleanup_state'] == 'terminal_no_live_owned_processes'
    assert result['owned_processes'][-1] == launcher
    for state, rss in [('S', 0), ('Z', 1)]:
        set_stat(state, rss)
        with pytest.raises(ValueError, match='live or has nonzero RSS'):
            continuation.validate_completion(ref, kind, current, proc)
    set_stat('Z', 0)
    launcher['role'] = 'provider'
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='only one retained zero-RSS tmux launcher'):
        continuation.validate_completion(ref, kind, current, proc)
    launcher['role'] = 'tmux_launcher'
    launcher['start_ticks'] += 1
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='only one retained zero-RSS tmux launcher'):
        continuation.validate_completion(ref, kind, current, proc)
    launcher['start_ticks'] -= 1
    audit['owned_processes_absent'] = True
    ref = write_reference(tmp_path / 'terminal.json', audit)
    with pytest.raises(ValueError, match='terminal cleanup'):
        continuation.validate_completion(ref, kind, current, proc)


def test_pinned_diagnosis_is_read_only_and_cannot_promote_the_old_failure(tmp_path, monkeypatch):
    diagnostic = {'kind': 'diagnostic_reparse', 'no_execution': True, 'no_historical_promotion': True,
        'source_record': {'sha256': continuation.FAILED_SHA256},
        'diagnostic_parser': {'sha256': continuation.RUNTIME['swdb/dx100_witness.py']},
        'original_outcome': {'state': 'failed'}, 'diagnostic_result': {'completed': True}}
    ref = write_reference(tmp_path / 'diagnosis.json', diagnostic)
    monkeypatch.setattr(continuation, 'DIAGNOSIS', ref)
    continuation.validate_diagnosis()
    diagnostic['original_outcome']['state'] = 'complete'
    monkeypatch.setattr(continuation, 'DIAGNOSIS', write_reference(tmp_path / 'diagnosis.json', diagnostic))
    with pytest.raises(ValueError, match='required diagnosis'):
        continuation.validate_diagnosis()


def test_public_driver_rejects_late_start_before_host_checks_or_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(continuation, 'now', lambda: continuation.DEADLINE - timedelta(seconds=1199))
    def forbidden(*args, **kwargs):
        pytest.fail('late launch reached a host check or command')
    monkeypatch.setattr(continuation.socket, 'gethostname', forbidden)
    monkeypatch.setattr(continuation, 'run_stage', forbidden)
    monkeypatch.setattr(sys, 'argv', ['a3', '--runs-dir', str(tmp_path), '--lane', '0',
        '--paired-completion', str(tmp_path / 'paired'), '--paired-sha256', '0' * 64,
        '--provider-completion', str(tmp_path / 'provider'), '--provider-sha256', '0' * 64])
    with pytest.raises(ValueError, match='latest launch is 15:20 ET'):
        continuation.main()
    assert list(tmp_path.iterdir()) == []


def test_public_driver_preserves_failure_and_blocks_retry_after_stage_failure(tmp_path, monkeypatch):
    """Only orchestration is exercised: lane/capacity/public execution are synthetic."""
    runs = tmp_path / 'runs'
    runs.mkdir()
    args = ['a3', '--runs-dir', str(runs), '--lane', '0']
    for kind in continuation.BATCHES:
        folder = tmp_path / kind
        folder.mkdir()
        audit, _, _, _, _ = completion_fixture(folder, kind)
        ref = write_reference(folder / 'terminal.json', audit)
        args += ['--' + kind + '-completion', ref['path'], '--' + kind + '-sha256', ref['sha256']]
    monkeypatch.setattr(sys, 'argv', args)
    monkeypatch.setattr(continuation, 'RAW_ROOT', runs)
    monkeypatch.setattr(continuation, 'now', lambda: continuation.stamp('2026-09-26T11:03:00-04:00'))
    monkeypatch.setattr(continuation.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(continuation.profile, '_verified_lane', lambda *args: 'synthetic test lane')
    monkeypatch.setattr(continuation, 'validate_diagnosis', lambda: None)
    monkeypatch.setattr(continuation.subprocess, 'check_output', lambda *args, **kwargs: 'synthetic-test-commit\n')
    calls = []
    def stage(receipt, folder, command, **kwargs):
        calls.append((command, kwargs))
        if '-m' in command:
            raise RuntimeError('synthetic public command failure')
    monkeypatch.setattr(continuation, 'run_stage', stage)
    failed = continuation.ROOT / 'records/evaluations' / (continuation.FAILED_ID + '.yaml')
    original = failed.read_bytes()
    with pytest.raises(RuntimeError, match='synthetic public command failure'):
        continuation.main()
    receipt = json.loads((runs / (continuation.PROBE_ID + '.driver') / 'driver.json').read_text())
    assert receipt['state'] == 'failed' and receipt['prior_failure_preserved'] is True
    assert receipt['gain_claim'] is False and receipt['automatic_retry_allowed'] is False
    assert receipt['outer_seconds'] == 1200 and receipt['cleanup_reserve_seconds'] == 30
    command, bounds = calls[-1]
    assert command[1:4] == ['-m', 'swdb', 'dx100-execute']
    assert bounds['timeout'] == 1150
    dispatched_request = json.loads(Path(command[4]).read_text())
    assert artifacts.digest(dispatched_request) == continuation.REQUEST_SHA256
    assert dispatched_request['budget'] == {'total_seconds': 1100, 'memory_gib': 48,
        'storage_gib': 2, 'checkpoint_seconds': 300, 'run_seconds': 750}
    before = len(calls)
    with pytest.raises(ValueError, match='cannot be overwritten or resumed'):
        continuation.main()
    assert len(calls) == before and failed.read_bytes() == original
