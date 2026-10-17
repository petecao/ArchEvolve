"""Synthetic procfs observer tests, not lab execution evidence. Date: 2026-09-26 ET."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil

import pytest

from scripts import bfs_owned_observer as observer


def process(proc, pid, parent, start, *, children=(), state='S', rss=10):
    folder = proc / str(pid)
    folder.mkdir(parents=True, exist_ok=True)
    fields = [state, str(parent)] + ['0'] * 17 + [str(start), '0', '0' if state == 'Z' else str(rss)]
    (folder / 'stat').write_text(f'{pid} (test process (nested)) ' + ' '.join(fields))
    (folder / 'status').write_text(f'Name:\ttest\nVmRSS:\t{rss} kB\n')
    task = folder / 'task' / str(pid)
    task.mkdir(parents=True, exist_ok=True)
    (task / 'children').write_text(' '.join(map(str, children)))


class Clock:
    def __init__(self, callback=lambda: None):
        self.t = 0
        self.callback = callback

    def monotonic(self):
        return self.t

    def wall(self):
        return datetime(2026, 9, 26, 16, tzinfo=timezone.utc) + timedelta(seconds=self.t)

    def sleep(self, seconds):
        self.t += seconds
        self.callback()


@pytest.fixture
def case(tmp_path, monkeypatch):
    proc = tmp_path / 'proc'
    process(proc, 90, 80, 900)
    process(proc, 80, 1, 800)  # Shared server is context, never an owned ancestor.
    process(proc, 100, 90, 1000, children=[101])
    process(proc, 101, 100, 1001)
    driver, pane = {'pid': 100, 'start_ticks': 1000}, {'pid': 90, 'start_ticks': 900}
    folder = tmp_path / 'observations'

    def forbidden(*args, **kwargs):
        pytest.fail('read-only observer signaled or killed a process')

    monkeypatch.setattr(observer.os, 'kill', forbidden)
    monkeypatch.setattr(observer.os, 'killpg', forbidden)

    def run(clock, seconds=20):
        return observer.observe(driver, pane, folder, clock.wall() + timedelta(seconds=seconds),
            proc=proc, wall=clock.wall, monotonic=clock.monotonic, sleep=clock.sleep)

    return proc, driver, pane, folder, run


def test_stops_at_exact_pane_and_preserves_live_orphan_without_reaping(case):
    proc, driver, pane, folder, run = case

    def terminate():
        shutil.rmtree(proc / '100')
        process(proc, 101, 1, 1001)  # Detached/reparented owned child survives.

    result = run(Clock(terminate))
    assert result['state'] == 'driver_terminated' and result['sampling_complete'] is True
    assert result['cleanup_verified'] is False
    assert [row['pid'] for row in result['ancestry']] == [100, 90]
    assert result['launcher_identity'] == pane and result['driver_identity'] == driver
    retained = {row['pid']: row for row in result['owned_processes']}
    assert set(retained) == {90, 100, 101} and retained[101]['state'] == 'S'
    assert retained[100]['state'] == 'absent' and (proc / '101').exists()
    samples = Path(result['resource_samples']['path'])
    assert observer.digest(samples) == result['resource_samples']['sha256']
    assert {row['pid'] for row in json.loads(samples.read_text())['processes']} == {100, 101}


@pytest.mark.parametrize('changed', ['driver', 'pane', 'not_ancestor'])
def test_rejects_stale_or_unowned_initial_identities(case, changed):
    proc, driver, pane, folder, run = case
    if changed == 'driver': driver['start_ticks'] += 1
    elif changed == 'pane': pane['start_ticks'] += 1
    else: pane.update(pid=101, start_ticks=1001)
    with pytest.raises(ValueError, match='reused|not descended'):
        run(Clock())
    assert json.loads((folder / 'process-observations.json').read_text())['state'] == 'failed'
    assert (proc / '100').exists() and (proc / '101').exists()


def test_reused_driver_pid_is_terminal_old_identity_not_new_process(case):
    proc, _, _, _, run = case
    result = run(Clock(lambda: process(proc, 100, 999, 2000)))
    assert result['driver_terminal_observation']['state'] == 'absent'
    assert any(row['pid'] == 100 and row['start_ticks'] == 1000 and row['state'] == 'absent'
               for row in result['owned_processes'])
    assert observer.identity(100, proc)['start_ticks'] == 2000


def test_zero_rss_driver_zombie_is_observed_without_claiming_cleanup(case):
    proc, _, _, _, run = case
    result = run(Clock(lambda: process(proc, 100, 90, 1000, state='Z')))
    assert result['driver_terminal_observation']['state'] == 'Z'
    assert result['driver_terminal_observation']['rss_bytes'] == 0
    assert result['cleanup_verified'] is False


def test_deadline_exhaustion_retains_live_processes_and_does_not_signal(case):
    proc, _, _, folder, run = case
    with pytest.raises(ValueError, match='outer deadline exhausted'):
        run(Clock(), seconds=5)
    result = json.loads((folder / 'process-observations.json').read_text())
    assert result['state'] == 'failed' and result['sampling_complete'] is False
    assert result['sample_count'] == 1 and all(row['state'] == 'S' for row in result['owned_processes'])
    assert (proc / '100').exists() and (proc / '101').exists()


def test_long_scheduling_gap_fails_even_when_driver_has_just_terminated(case):
    proc, _, _, folder, run = case
    clock = Clock()

    def sleep(seconds):
        clock.t += 11
        shutil.rmtree(proc / '100')

    clock.sleep = sleep
    with pytest.raises(ValueError, match='sampling gap'):
        run(clock)
    assert json.loads((folder / 'process-observations.json').read_text())['sampling_complete'] is False


def test_storage_bound_preserves_failure_and_never_overwrites_existing_output(case, monkeypatch):
    _, _, _, folder, run = case
    monkeypatch.setattr(observer, 'MAX_BYTES', 16 * 1024)
    with pytest.raises(ValueError, match='storage bound'):
        run(Clock())
    before = (folder / 'process-observations.json').read_bytes()
    assert json.loads(before)['state'] == 'failed'
    with pytest.raises(FileExistsError):
        run(Clock())
    assert (folder / 'process-observations.json').read_bytes() == before


@pytest.mark.parametrize('seconds', [0, -1, 1201])
def test_invalid_remaining_budget_fails_before_creating_output(case, seconds):
    _, _, _, folder, run = case
    with pytest.raises(ValueError, match='same remaining outer deadline'):
        run(Clock(), seconds=seconds)
    assert not folder.exists()


def test_live_unreadable_identity_stays_unknown_in_failed_receipt(case):
    proc, _, _, folder, run = case

    def disappear_stat():
        (proc / '100/stat').unlink()

    with pytest.raises(ValueError, match='identity is unavailable'):
        run(Clock(disappear_stat))
    result = json.loads((folder / 'process-observations.json').read_text())
    assert result['state'] == 'failed' and any(row['pid'] == 100 and row['state'] == 'unknown'
                                             for row in result['owned_processes'])


def test_ordinary_root_exit_during_sampler_does_not_discard_observed_children(case, monkeypatch):
    proc, _, _, _, run = case
    original = observer.DescendantRSS.sample
    calls = 0

    def sample(sampler):
        nonlocal calls
        calls += 1
        if calls == 2:
            shutil.rmtree(proc / '100')
            raise ValueError('driver RSS telemetry is unavailable')
        return original(sampler)

    monkeypatch.setattr(observer.DescendantRSS, 'sample', sample)
    result = run(Clock())
    assert result['terminal_sample_race'] is True and result['sampling_complete'] is True
    assert {row['pid'] for row in result['owned_processes']} == {90, 100, 101}


def test_sample_cost_includes_durable_writes(case, monkeypatch):
    _, _, _, folder, run = case
    clock = Clock()
    calls = 0

    def slow_fsync(fd):
        nonlocal calls
        calls += 1
        if calls == 2:  # First JSONL sample, after the initial receipt.
            clock.t += 3

    monkeypatch.setattr(observer.os, 'fsync', slow_fsync)
    with pytest.raises(ValueError, match='sample cost'):
        run(clock)
    result = json.loads((folder / 'process-observations.json').read_text())
    assert result['state'] == 'failed' and result['maximum_sample_seconds'] == 3


def test_final_hashing_is_charged_before_success(case, monkeypatch):
    proc, _, _, _, run = case
    clock = Clock(lambda: shutil.rmtree(proc / '100'))
    original = observer.digest

    def slow_digest(path):
        result = original(path)
        if Path(path).name == 'resource-samples.jsonl':
            clock.t += 20
        return result

    monkeypatch.setattr(observer, 'digest', slow_digest)
    result = run(clock)
    assert result['state'] == 'failed' and result['sampling_complete'] is False
    assert 'finalization' in result['reason'] and result['host_wall_s'] == 25


def test_final_persistence_cannot_leave_success_after_deadline(case, monkeypatch):
    proc, _, _, folder, run = case
    clock = Clock(lambda: shutil.rmtree(proc / '100'))

    def final_flush(fd):
        if json.loads((folder / 'process-observations.json').read_text()).get('state') == 'driver_terminated':
            clock.t += 20

    monkeypatch.setattr(observer.os, 'fsync', final_flush)
    result = run(clock)
    assert result['state'] == 'failed' and result['sampling_complete'] is False
    assert 'final persistence' in result['reason']
    assert json.loads((folder / 'process-observations.json').read_text()) == result


@pytest.mark.parametrize('race', [False, True])
def test_terminal_observation_cost_is_checked_before_success(case, monkeypatch, race):
    proc, _, _, folder, run = case
    clock = Clock()
    if race:
        original = observer.DescendantRSS.sample
        calls = 0

        def sample(sampler):
            nonlocal calls
            calls += 1
            if calls == 2:
                clock.t += 3
                shutil.rmtree(proc / '100')
                raise ValueError('driver RSS telemetry is unavailable')
            return original(sampler)

        monkeypatch.setattr(observer.DescendantRSS, 'sample', sample)
    else:
        clock.callback = lambda: shutil.rmtree(proc / '100')
        original = observer.status

        def status(row, proc):
            result = original(row, proc)
            if row['pid'] == 100 and result['state'] == 'absent':
                clock.t += 3
            return result

        monkeypatch.setattr(observer, 'status', status)
    with pytest.raises(ValueError, match='sample cost'):
        run(clock)
    result = json.loads((folder / 'process-observations.json').read_text())
    assert result['state'] == 'failed' and result['sampling_complete'] is False
    assert result['maximum_sample_seconds'] == 3
