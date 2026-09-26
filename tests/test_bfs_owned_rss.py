"""Actual observer seams using a synthetic proc tree. Date: 2026-09-26 ET."""
import shutil
from pathlib import Path
import os
import subprocess
import sys
import time

import pytest

from scripts.bfs_owned_rss import DescendantRSS, RSS_SOURCE
from scripts.bfs_native_paired_pilot import DescendantRSS as HistoricalRSS


def process(proc, pid, parent, start, pages=10, *, state='S', children=(), extra_thread=()):
    folder = proc / str(pid)
    task = folder / 'task' / str(pid)
    task.mkdir(parents=True, exist_ok=True)
    fields = [state, str(parent)] + ['0'] * 17 + [str(start), '0', str(pages)]
    (folder / 'stat').write_text(f'{pid} (fixture (process)) ' + ' '.join(fields))
    (folder / 'status').write_text(f'Name:\tfixture\nState:\t{state}\nVmRSS:\t{pages * 4} kB\n')
    (task / 'children').write_text(' '.join(map(str, children)))
    if extra_thread:
        task = folder / 'task' / str(pid + 1000)
        task.mkdir(exist_ok=True)
        (task / 'children').write_text(' '.join(map(str, extra_thread)))
    return folder


def test_exit_between_stat_and_status_reproduces_old_abort_and_new_sampler_avoids_cross_read(tmp_path, monkeypatch):
    process(tmp_path, 100, 1, 1000, children=[101])
    child = process(tmp_path, 101, 100, 1001, pages=20)
    original = Path.read_text
    accesses = []

    def exiting(path, *args, **kwargs):
        if path == child / 'status':
            accesses.append(path)
            process(tmp_path, 101, 100, 1001, pages=0, state='Z')
            return 'Name:\tfixture\nState:\tZ (zombie)\n'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', exiting)
    old = HistoricalRSS(100, tmp_path)
    with pytest.raises(ValueError, match='owned process RSS is unavailable'):
        old.sample()
    assert 101 not in old.known
    assert accesses == [child / 'status']
    accesses.clear()
    fresh = DescendantRSS(100, tmp_path)
    result = fresh.sample()
    row = next(row for row in result['processes'] if row['pid'] == 101)
    assert row['state'] == 'Z' and row['rss_bytes'] == row['rss_pages'] == 0
    assert fresh.known[101] == 1001 and accesses == []
    assert result['rss_source'] == RSS_SOURCE
    assert result['rss_bytes'] == 10 * result['page_size_bytes']


def test_live_rss_is_explicit_stat_pages_not_a_missing_status_fallback(tmp_path):
    folder = process(tmp_path, 100, 1, 1000, pages=23)
    (folder / 'status').unlink()
    result = DescendantRSS(100, tmp_path).sample()
    assert result['processes'][0]['rss_pages'] == 23
    assert result['rss_bytes'] == 23 * result['page_size_bytes']


@pytest.mark.parametrize('fault', ['missing-rss', 'negative', 'noninteger'])
def test_unavailable_live_rss_fails_and_retains_exact_identity(tmp_path, fault):
    process(tmp_path, 100, 1, 1000, children=[101])
    child = process(tmp_path, 101, 100, 1001)
    text = (child / 'stat').read_text()
    if fault == 'missing-rss': text = text.rsplit(' ', 1)[0]
    else: text = text.rsplit(' ', 1)[0] + (' -1' if fault == 'negative' else ' bad')
    (child / 'stat').write_text(text)
    sampler = DescendantRSS(100, tmp_path)
    with pytest.raises(ValueError, match='101/1001 RSS'):
        sampler.sample()
    assert sampler.known == {100: 1000, 101: 1001}


def test_follows_all_threads_and_known_reparented_children_but_not_reused_pids(tmp_path):
    process(tmp_path, 100, 1, 1000, children=[101], extra_thread=[102])
    process(tmp_path, 101, 100, 1001, children=[103])
    process(tmp_path, 102, 100, 1002)
    process(tmp_path, 103, 101, 1003)
    sampler = DescendantRSS(100, tmp_path)
    assert sampler.sample()['rss_bytes'] == 40 * sampler.page_size
    process(tmp_path, 100, 1, 1000)
    shutil.rmtree(tmp_path / '100/task/1100')
    process(tmp_path, 101, 1, 1001, children=[103])
    assert {row['pid'] for row in sampler.sample()['processes']} == {100, 101, 102, 103}
    process(tmp_path, 101, 999, 9999)
    assert 101 not in {row['pid'] for row in sampler.sample()['processes']}


def test_stale_child_list_cannot_adopt_an_unrelated_process(tmp_path):
    process(tmp_path, 100, 1, 1000, children=[101])
    process(tmp_path, 101, 999, 9999)
    sampler = DescendantRSS(100, tmp_path)
    with pytest.raises(ValueError, match='discovering parent'):
        sampler.sample()
    assert 101 not in sampler.known


def test_parent_reused_after_discovery_cannot_adopt_new_owners_child(tmp_path, monkeypatch):
    process(tmp_path, 100, 1, 1000, children=[101])
    process(tmp_path, 101, 100, 1001, children=[102])
    process(tmp_path, 102, 101, 1002)
    sampler = DescendantRSS(100, tmp_path)
    original = sampler._stat

    def reuse_before_adoption(pid):
        if pid == 102:
            process(tmp_path, 101, 999, 9999, children=[102])
            process(tmp_path, 102, 101, 9998)
        return original(pid)

    monkeypatch.setattr(sampler, '_stat', reuse_before_adoption)
    with pytest.raises(ValueError, match='discovering parent'):
        sampler.sample()
    assert sampler.known == {100: 1000, 101: 1001}


@pytest.mark.parametrize('phase', ['task-reaped', 'pid-reused'])
def test_process_changes_while_reading_task_children_do_not_follow_unrelated_descendants(tmp_path, monkeypatch, phase):
    process(tmp_path, 100, 1, 1000, children=[101])
    child = process(tmp_path, 101, 100, 1001, children=[102])
    process(tmp_path, 102, 101, 1002)
    original = Path.read_text

    def changing(path, *args, **kwargs):
        if path == child / 'task/101/children':
            if phase == 'task-reaped': shutil.rmtree(child)
            else: process(tmp_path, 101, 999, 9999, children=[102])
            return '102'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', changing)
    sampler = DescendantRSS(100, tmp_path)
    result = sampler.sample()
    assert {row['pid'] for row in result['processes']} == {100, 101}
    assert sampler.known == {100: 1000, 101: 1001}


def test_missing_live_stat_fails_but_reaped_child_is_skipped(tmp_path):
    parent = process(tmp_path, 100, 1, 1000, children=[101])
    assert len(DescendantRSS(100, tmp_path).sample()['processes']) == 1
    (parent / 'stat').unlink()
    with pytest.raises(ValueError, match='live owned PID 100 stat'):
        DescendantRSS(100, tmp_path).sample()


def test_wrong_stat_pid_is_never_owned(tmp_path):
    folder = process(tmp_path, 100, 1, 1000)
    (folder / 'stat').write_text((folder / 'stat').read_text().replace('100 (', '999 (', 1))
    sampler = DescendantRSS(100, tmp_path)
    with pytest.raises(ValueError, match='identity is malformed'):
        sampler.sample()
    assert sampler.known == {}


@pytest.mark.skipif(sys.platform != 'linux', reason='requires actual Linux proc lifecycle')
def test_linux_observes_live_child_zombie_and_reaping_without_status_fallback(tmp_path):
    """Real Linux lifecycle with owned children; finite 15-second wall ceiling."""
    deadline = time.monotonic() + 15
    sampler = DescendantRSS(os.getpid())
    observed = []
    for index in range(4):
        child = subprocess.Popen([sys.executable, '-c',
            'import os,sys; os.write(1,b"ready\\n"); sys.stdin.buffer.read(1)'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, start_new_session=True)
        try:
            # read readiness without a blocking read beyond the test's ceiling.
            import select
            ready, _, _ = select.select([child.stdout], [], [], max(0, deadline-time.monotonic()))
            assert ready and child.stdout.readline() == b'ready\n'
            live = next(row for row in sampler.sample()['processes'] if row['pid'] == child.pid)
            assert live['rss_pages'] > 0 and live['state'] != 'Z'
            child.stdin.write(b'x'); child.stdin.flush()
            zombie = None
            while time.monotonic() < deadline:
                row = sampler._stat(child.pid)
                if row and row['state'] == 'Z':
                    zombie = next(row for row in sampler.sample()['processes'] if row['pid'] == child.pid)
                    break
                time.sleep(.005)
            assert zombie is not None and zombie['rss_pages'] == 0
            assert zombie['start_ticks'] == live['start_ticks']
            child.wait(timeout=max(.01, deadline-time.monotonic()))
            assert child.pid not in {row['pid'] for row in sampler.sample()['processes']}
            assert sampler.known[child.pid] == live['start_ticks']
            observed.append({'pid':child.pid, 'start_ticks':live['start_ticks'], 'zombie_observed':True, 'reaped':True})
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=2)
            child.stdin.close(); child.stdout.close()
    import json
    (tmp_path / 'linux-rss-lifecycle-result.json').write_text(json.dumps({
        'created':'2026-09-26', 'rss_source':RSS_SOURCE, 'page_size_bytes':sampler.page_size,
        'state':'passed', 'observations':observed, 'remaining_seconds':deadline-time.monotonic()},indent=2)+'\n')
