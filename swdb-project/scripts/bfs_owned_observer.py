#!/usr/bin/env python3
"""Bounded read-only observations of one owned process tree. Date: 2026-09-26 ET.

Run inside the same lane and outer deadline as the observed driver. This tool
never signals a process, waits for/reaps a child, or attests complete cleanup.
The coordinator independently audits every retained identity after termination.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_native_paired_pilot import DescendantRSS
from scripts.bfs_process import interruption_signals

INTERVAL_SECONDS = 5
MAX_SECONDS = 1200
MAX_SAMPLE_SECONDS = 2
MAX_GAP_SECONDS = 10
MAX_BYTES = 8 * 1024**2
MAX_SAMPLES = 242
MAX_IDENTITIES = 4096
MAX_SELF_ADDRESS_BYTES = 512 * 1024**2
MAX_SELF_CPU_SECONDS = 20


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def now():
    return datetime.now(timezone.utc)


def stamp(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'observer deadline needs an explicit zone')
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(pid, proc=Path('/proc')):
    require(type(pid) is int and pid > 0, 'invalid owned PID')
    folder = Path(proc) / str(pid)
    try:
        fields = (folder / 'stat').read_text().rsplit(')', 1)[1].split()
        require(len(fields) > 21, 'owned process stat is incomplete')
        return {'pid': pid, 'parent_pid': int(fields[1]), 'start_ticks': int(fields[19]),
                'state': fields[0], 'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE')}
    except FileNotFoundError:
        require(not folder.exists(), 'owned process identity is unavailable')
        return None
    except (IndexError, TypeError):
        raise ValueError('owned process identity is malformed') from None


def ancestry(driver, pane, proc=Path('/proc')):
    rows, seen, pid = [], set(), driver['pid']
    while len(rows) < 32:
        row = identity(pid, proc)
        require(row is not None and pid not in seen, 'owned ancestry is missing or cyclic')
        require(row['state'] != 'Z', 'owned ancestry already terminated before observation')
        seen.add(pid)
        if not rows:
            require(row['start_ticks'] == driver['start_ticks'], 'driver PID was reused')
        rows.append(row)
        if pid == pane['pid']:
            require(row['start_ticks'] == pane['start_ticks'], 'pane PID was reused')
            return rows
        pid = row['parent_pid']
        require(pid > 1, 'driver is not descended from its declared pane')
    raise ValueError('owned ancestry exceeds its fixed bound')


def status(row, proc):
    current = identity(row['pid'], proc)
    if current is None or current['start_ticks'] != row['start_ticks']:
        return {**row, 'state': 'absent'}
    return current


def observe(driver, pane, folder, deadline, *, proc=Path('/proc'),
            wall=now, monotonic=time.monotonic, sleep=time.sleep, interval=INTERVAL_SECONDS):
    """Write bounded samples; uncertainty remains a failed observation receipt."""
    start, started = monotonic(), wall()
    for row in (driver, pane):
        require(isinstance(row, dict) and type(row.get('pid')) is int and row['pid'] > 0
                and type(row.get('start_ticks')) is int and row['start_ticks'] >= 0,
                'owned PID/start identity is malformed')
    remaining = (deadline - started).total_seconds()
    require(0 < remaining <= MAX_SECONDS, 'observer must fit the same remaining outer deadline')
    until = start + remaining
    folder = Path(folder)
    folder.mkdir(exist_ok=False)
    sample_path = folder / 'resource-samples.jsonl'
    receipt_path = folder / 'process-observations.json'
    receipt = {'format': 'swdb.owned-process-observations.v1', 'created': '2026-09-26',
        'state': 'observing', 'started': started.isoformat(), 'deadline': deadline.isoformat(),
        'driver_pid': driver['pid'], 'driver_identity': driver, 'pane_pid': pane['pid'],
        'launcher_identity': pane, 'ancestry': [], 'owned_processes': [],
        'observer_identity': identity(os.getpid(), proc) if proc == Path('/proc') else None,
        'bounds': {'outer_seconds': MAX_SECONDS, 'nominal_interval_seconds': INTERVAL_SECONDS,
            'maximum_sample_seconds': MAX_SAMPLE_SECONDS, 'maximum_gap_seconds': MAX_GAP_SECONDS,
            'maximum_bytes': MAX_BYTES, 'maximum_samples': MAX_SAMPLES,
            'maximum_identities': MAX_IDENTITIES, 'self_address_bytes': MAX_SELF_ADDRESS_BYTES,
            'self_cpu_seconds': MAX_SELF_CPU_SECONDS},
        'sampling_complete': False, 'cleanup_verified': False, 'sample_count': 0,
        'rss_scope': 'observed driver descendants; observer is included only when a descendant; not the simulator RSS budget',
        'maximum_sample_seconds': 0, 'maximum_gap_seconds': 0,
        'implementation': {'observer_sha256': digest(__file__),
            'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                                          text=True, timeout=3).strip(),
            'sampler_sha256': digest(ROOT / 'scripts/bfs_native_paired_pilot.py')},
        'limitation': 'Periodic observations can miss short-lived children; final cleanup requires an independent audit.'}
    known = {}
    sample_bytes, last = 0, start

    def save():
        data = (json.dumps(receipt, indent=2) + '\n').encode()
        require(sample_bytes + len(data) <= MAX_BYTES, 'observer storage bound exhausted')
        with receipt_path.open('wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def remember(rows):
        for row in rows:
            key = (row['pid'], row['start_ticks'])
            known[key] = {key: row[key] for key in ('pid', 'parent_pid', 'start_ticks')}
        require(len(known) <= MAX_IDENTITIES, 'observer identity bound exhausted')

    def check_sample_cost(before):
        cost = monotonic() - before
        receipt['maximum_sample_seconds'] = max(receipt['maximum_sample_seconds'], cost)
        require(cost <= MAX_SAMPLE_SECONDS, 'observer sample cost exceeded its bound')

    try:
        receipt['ancestry'] = ancestry(driver, pane, proc)
        remember(receipt['ancestry'])
        if receipt['observer_identity'] is not None:
            remember([receipt['observer_identity']])
        sampler = DescendantRSS(driver['pid'], proc)
        sampler.known[driver['pid']] = driver['start_ticks']
        save()
        with sample_path.open('xb') as stream:
            while True:
                before = monotonic()
                observed_before = wall().isoformat()
                gap = before - last
                receipt['maximum_gap_seconds'] = max(receipt['maximum_gap_seconds'], gap)
                require(gap <= MAX_GAP_SECONDS, 'observer sampling gap exceeded its bound')
                require(before < until and wall() < deadline, 'observer outer deadline exhausted')
                current = status(driver, proc)
                if current['state'] in ('absent', 'Z'):
                    require(current['state'] != 'Z' or current['rss_bytes'] == 0,
                            'terminated driver has nonzero RSS')
                    require(receipt['sample_count'] > 0, 'driver terminated before the first observation')
                    check_sample_cost(before)
                    receipt.update(state='driver_terminated', driver_terminal_observation=current,
                                   sampling_complete=True)
                    break
                require(receipt['sample_count'] < MAX_SAMPLES, 'observer sample bound exhausted')
                try:
                    sample = sampler.sample()
                except ValueError as exc:
                    # The leader can terminate between its status read and the
                    # sampler's root-presence check. Retain all identities the
                    # sampler actually observed, including surviving children.
                    current = status(driver, proc)
                    for pid, token in sampler.known.items():
                        row = identity(pid, proc)
                        if row is not None and row['start_ticks'] == token:
                            remember([row])
                        elif (pid, token) not in known:
                            known[pid, token] = {'pid': pid, 'start_ticks': token, 'parent_pid': None}
                    if str(exc) in ('driver RSS telemetry is unavailable', 'live owned process telemetry is unavailable') \
                            and current['state'] in ('absent', 'Z') and receipt['sample_count'] > 0:
                        require(current['state'] != 'Z' or current['rss_bytes'] == 0,
                                'terminated driver has nonzero RSS')
                        check_sample_cost(before)
                        receipt.update(state='driver_terminated', driver_terminal_observation=current,
                                       sampling_complete=True, terminal_sample_race=True)
                        break
                    raise
                remember(sample['processes'])
                sample.update(observer_started=observed_before,
                              observer_wall_s=monotonic() - before)
                encoded = (json.dumps(sample) + '\n').encode()
                require(sample_bytes + len(encoded) + 2 * 1024**2 <= MAX_BYTES,
                        'observer storage bound exhausted')
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
                sample_bytes += len(encoded)
                receipt['sample_count'] += 1
                last = before
                save()
                # Charge sample serialization and both durable writes as well
                # as procfs reads. The row's observer_wall_s is read cost only.
                check_sample_cost(before)
                sleep(min(interval, max(0, until - monotonic())))
    except BaseException as exc:
        receipt.update(state='failed', sampling_complete=False, reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        # A reused PID is never treated as the original process. Unknown/live
        # descendants remain visible and are never signaled by this observer.
        terminal = []
        for row in known.values():
            try:
                terminal.append(status(row, proc))
            except (OSError, ValueError) as exc:
                terminal.append({**row, 'state': 'unknown', 'reason': str(exc)})
                receipt.update(state='failed', sampling_complete=False)
        receipt['owned_processes'] = terminal
        if sample_path.is_file():
            receipt['resource_samples'] = {'path': str(sample_path), 'sha256': digest(sample_path)}
        receipt.update(finished=wall().isoformat(), host_wall_s=monotonic() - start)
        if monotonic() >= until or wall() >= deadline:
            receipt.update(state='failed', sampling_complete=False,
                           reason='observer finalization exceeded its outer deadline')
        save()
        # A delayed final flush cannot leave a successful receipt behind. The
        # enclosing timeout remains the bound for a blocked filesystem call.
        if receipt['state'] != 'failed' and (monotonic() >= until or wall() >= deadline):
            receipt.update(state='failed', sampling_complete=False,
                           reason='observer final persistence exceeded its outer deadline',
                           finished=wall().isoformat(), host_wall_s=monotonic() - start)
            save()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('driver-pid', 'driver-start-ticks', 'pane-pid', 'pane-start-ticks'):
        parser.add_argument('--' + name, type=int, required=True)
    parser.add_argument('--deadline', required=True, help='Same absolute outer deadline, at most 1200 seconds away')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    folder = args.output_dir.absolute()
    require(not folder.is_symlink() and folder.resolve() == folder and any(folder.is_relative_to(base) for base in
            (Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))),
            'observer output must be a new directory under authorized raw storage')
    require(sys.platform == 'linux', 'observer requires Linux procfs')
    for name, bound in ((resource.RLIMIT_AS, MAX_SELF_ADDRESS_BYTES), (resource.RLIMIT_CPU, MAX_SELF_CPU_SECONDS)):
        soft, hard = resource.getrlimit(name)
        limits = [value for value in (soft, hard, bound) if value != resource.RLIM_INFINITY]
        capped = min(limits)
        resource.setrlimit(name, (capped, capped))
    with interruption_signals():
        result = observe({'pid': args.driver_pid, 'start_ticks': args.driver_start_ticks},
            {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}, folder, stamp(args.deadline))
    require(result['state'] == 'driver_terminated' and result['sampling_complete'],
            'observer did not finish a bounded observation interval')
    print(json.dumps({'state': result['state'], 'sampling_complete': result['sampling_complete'],
        'process_observations': {'path': str(folder / 'process-observations.json'),
                                'sha256': digest(folder / 'process-observations.json')}}))


if __name__ == '__main__':
    main()
