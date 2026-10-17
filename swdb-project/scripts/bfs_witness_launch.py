#!/usr/bin/env python3
"""Supervise the one fixed a3 client and read-only observer. Date: 2026-09-26 ET."""
import argparse
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_owned_observer as observer
from scripts import dx100_witness_continuation as a3
from scripts.bfs_process import interruption_signals
from swdb import artifacts, profile, yamlio
from swdb.store import Store

DRIVER_ROOT = Path('/data1/yanruj/EvolveSWDB_dx100_continuation_20260926_a3')
DRIVER_COMMIT = '1018432fdb3800522d723afb874f3bffa41dd0e5'
DRIVER_PATH = 'scripts/dx100_witness_continuation.py'
DRIVER_SHA256 = '5673c4e35653e6804784e376c9832a2c73654f384ad7c2deffc4d30f2d0a2711'
OUTPUT = a3.RAW_ROOT / 'witness-a3-dispatch1/supervisor'
RUNTIME_FILES = ('scripts/bfs_witness_launch.py', 'scripts/bfs_owned_observer.py',
                 'scripts/bfs_native_paired_pilot.py', 'scripts/bfs_process.py',
                 'scripts/dx100_witness_continuation.py', 'swdb/processes.py')
require = a3.require


def ref(path):
    return {'path': str(Path(path).absolute()), 'sha256': artifacts.file_hash(path)}


def runtime(commit, root=ROOT):
    require(isinstance(commit, str) and re.fullmatch('[a-f0-9]{40}', commit), 'exact prospective runtime commit is required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, timeout=3).strip() == commit,
            'supervisor checkout differs from its prospective commit')
    require(subprocess.run(['git', 'diff', '--quiet', commit, '--', 'scripts', 'swdb', 'schemas'],
                           cwd=root, timeout=3).returncode == 0, 'supervisor imported runtime has unreviewed changes')
    result = {}
    for name in RUNTIME_FILES:
        expected = hashlib.sha256(subprocess.check_output(['git', 'show', commit + ':' + name], cwd=root, timeout=3)).hexdigest()
        require(artifacts.file_hash(root / name) == expected, 'supervisor runtime source changed: ' + name)
        result[name] = ref(root / name)
    return result


def window(started, deadline, current):
    require(deadline-started == timedelta(seconds=a3.OUTER_SECONDS) and started <= current < deadline
            and deadline <= a3.DEADLINE, 'supervisor must share the original 1200-second outer window')
    a3.launch_budget(started)
    remaining = (deadline-current).total_seconds()
    require(remaining > a3.CLEANUP_SECONDS, 'supervisor has no work allowance before cleanup')
    return remaining-a3.CLEANUP_SECONDS, remaining


def validate_driver(root):
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, timeout=3).strip() == DRIVER_COMMIT
            and artifacts.file_hash(root / DRIVER_PATH) == DRIVER_SHA256,
            'original a3 driver checkout changed')
    require(subprocess.run(['git', 'diff', '--quiet', DRIVER_COMMIT, '--', 'scripts', 'swdb', 'schemas'],
                           cwd=root, timeout=3).returncode == 0, 'original a3 imported runtime changed')
    request = root / a3.REQUEST.relative_to(a3.ROOT)
    require(artifacts.digest(yamlio.load(request)) == a3.REQUEST_SHA256, 'original a3 request changed')
    return request


def stop_owned(child, identity, deadline, outer_deadline, identify):
    """Signal a still-owned session leader; share the original remaining wait."""
    def remaining():
        return min(deadline-time.monotonic(), (outer_deadline-observer.now()).total_seconds())

    def reap_disappeared():
        # The direct child can exit between poll(), procfs and getpgid().
        # Its disappearance is not permission to signal a numeric PID again.
        try:
            child.wait(timeout=max(0, remaining()))
        except subprocess.TimeoutExpired:
            raise TimeoutError('disappearing child could not be reaped before the shared cleanup deadline') from None

    for sig in (signal.SIGTERM, signal.SIGKILL):
        if child.poll() is not None:
            return  # Reaped numeric PID/group identities must never be signaled.
        current = identify(child.pid)
        if current is None:
            return reap_disappeared()
        require(all(current[key] == identity[key] for key in ('pid', 'start_ticks')),
                'owned child identity changed before cleanup; no signal sent')
        try:
            group = os.getpgid(child.pid)
        except ProcessLookupError:
            return reap_disappeared()
        require(group == child.pid, 'owned child is no longer its declared session group')
        require(remaining() > 0, 'shared supervisor cleanup deadline exhausted')
        try:
            os.killpg(child.pid, sig)
        except ProcessLookupError:
            pass
        allowed = max(0, remaining())
        if sig == signal.SIGTERM:
            allowed = max(0, min(20, allowed-5))
        try:
            child.wait(timeout=allowed)
            return
        except subprocess.TimeoutExpired:
            if sig == signal.SIGKILL:
                raise TimeoutError('owned child could not be reaped before the shared cleanup deadline') from None


def supervise(folder, driver_command, observer_command, *, driver_cwd, observer_cwd,
              outer_deadline, work_deadline, hard_deadline, pane, metadata=None,
              identify=observer.identity, poll_interval=.1):
    """One launch only; directly owned session leaders are always waited/reaped."""
    folder = Path(folder)
    folder.mkdir(exist_ok=False)
    children, streams = {}, []
    receipt = {'id': a3.PROBE_ID + '.launcher', 'created': '2026-09-26', 'state': 'starting',
        'started': observer.now().isoformat(), 'outer_deadline': outer_deadline.isoformat(),
        'supervisor_identity': identify(os.getpid()), 'pane_identity': pane,
        'automatic_retry_allowed': False, 'cleanup_verified': False, 'gain_claim': False,
        'children': {}, 'metadata': metadata or {}}
    started = time.monotonic()

    def save():
        (folder / 'launcher.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def spawn(role, command, cwd):
        require(time.monotonic() < work_deadline and observer.now() < outer_deadline,
                'supervisor original work deadline exhausted before launch')
        out, err = folder / (role + '.stdout'), folder / (role + '.stderr')
        handles = [out.open('w'), err.open('w')]
        streams.extend(handles)
        row = {'command': list(map(str, command)), 'state': 'starting', 'stdout': str(out), 'stderr': str(err)}
        receipt['children'][role] = row
        save()
        child = subprocess.Popen(row['command'], cwd=cwd, stdout=handles[0], stderr=handles[1], start_new_session=True)
        children[role] = child
        row['pid'] = child.pid
        identity = identify(child.pid)
        require(identity is not None, role + ' identity unavailable immediately after launch')
        row.update(identity=identity, state='running')
        save()
        return identity

    try:
        driver = spawn('driver', driver_command, driver_cwd)
        spawn('observer', observer_command(driver, folder / 'observer'), observer_cwd)
        receipt['state'] = 'running'; save()
        while True:
            codes = {role: child.poll() for role, child in children.items()}
            if codes['observer'] is not None and codes['observer'] != 0:
                raise RuntimeError('read-only observer failed; stopping owned driver')
            if all(code is not None for code in codes.values()):
                require(time.monotonic() < work_deadline and observer.now() < outer_deadline,
                        'supervisor original work deadline exhausted')
                require(codes['driver'] == codes['observer'] == 0, 'driver or observer exited unsuccessfully')
                observed_path = folder / 'observer/process-observations.json'
                require(observed_path.is_file() and observed_path.stat().st_size <= observer.MAX_BYTES,
                        'successful observer receipt is unavailable')
                observed = json.loads(observed_path.read_text())
                require(observed.get('state') == 'driver_terminated' and observed.get('sampling_complete') is True
                        and observed.get('cleanup_verified') is False
                        and all(observed['driver_identity'][key] == driver[key] for key in ('pid', 'start_ticks'))
                        and all(observed['launcher_identity'][key] == pane[key] for key in ('pid', 'start_ticks'))
                        and all(observed['observer_identity'][key] == receipt['children']['observer']['identity'][key]
                                for key in ('pid', 'start_ticks'))
                        and a3.stamp(observed['deadline']) == outer_deadline
                        and a3.stamp(receipt['started']) <= a3.stamp(observed['started'])
                        <= a3.stamp(observed['finished']) < outer_deadline,
                        'successful observer receipt does not bind the launched driver/pane')
                receipt['process_observations'] = ref(observed_path)
                receipt['state'] = 'complete'
                break
            require(time.monotonic() < work_deadline and observer.now() < outer_deadline,
                    'supervisor original work deadline exhausted')
            time.sleep(min(poll_interval, max(0, work_deadline-time.monotonic())))
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
    finally:
        errors = []
        cleanup_end = min(hard_deadline, time.monotonic() + a3.CLEANUP_SECONDS)
        # Driver gets the first cleanup opportunity to stop its nested sessions.
        # Each wait spends the remaining shared reserve; no new per-child clock.
        for role in ('driver', 'observer'):
            child = children.get(role)
            if child is None:
                continue
            try:
                if child.poll() is None:
                    identity = receipt['children'][role].get('identity')
                    require(identity is not None, 'owned child start identity is unavailable; no signal sent')
                    stop_owned(child, identity, cleanup_end, outer_deadline, identify)
            except BaseException as exc:
                errors.append(f'{role}: {type(exc).__name__}: {exc}')
            # Even a denied signal or a procfs race must not skip a direct
            # child's bounded wait. Preserve the cleanup error independently.
            try:
                remaining = min(cleanup_end-time.monotonic(), (outer_deadline-observer.now()).total_seconds())
                child.wait(timeout=max(0, remaining))
            except BaseException as exc:
                errors.append(f'{role} reap: {type(exc).__name__}: {exc}')
            receipt['children'][role].update(returncode=child.returncode,
                reaped=child.returncode is not None, state='terminated' if child.returncode is not None else 'unknown')
        for stream in streams:
            stream.close()
        if errors:
            receipt.update(state='failed', cleanup_errors=errors)
        for role in ('driver', 'observer'):
            code = children[role].returncode if role in children else None
            path = folder / (role + '.exit')
            label = str(code) if code is not None else ('unknown_unreaped' if role in children else 'not_started')
            path.write_text(label + '\n')
            receipt[role + '_exit'] = ref(path)
            row = receipt['children'].get(role, {})
            for stream in ('stdout', 'stderr'):
                if row.get(stream) and Path(row[stream]).is_file():
                    row[stream + '_sha256'] = artifacts.file_hash(row[stream])
        # Both final writes are checked after persistence. The second retains
        # timestamps after the first; a late final hash/write cannot leave success.
        for _ in range(2):
            if time.monotonic() >= hard_deadline or observer.now() >= outer_deadline:
                receipt.update(state='failed', final_error='supervisor finalization exceeded original outer deadline')
            receipt.update(finished=observer.now().isoformat(), host_wall_s=time.monotonic()-started,
                           combined_exit=0 if receipt['state'] == 'complete' else 1)
            (folder / 'supervisor.exit').write_text(str(receipt['combined_exit']) + '\n')
            save()
        if receipt['state'] == 'complete' and (time.monotonic() >= hard_deadline or observer.now() >= outer_deadline):
            receipt.update(state='failed', combined_exit=1, final_error='supervisor final persistence exceeded original outer deadline')
            (folder / 'supervisor.exit').write_text('1\n'); save()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--driver-checkout', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--outer-started', required=True)
    parser.add_argument('--outer-deadline', required=True)
    parser.add_argument('--pane-pid', type=int, required=True)
    parser.add_argument('--pane-start-ticks', type=int, required=True)
    for kind in a3.BATCHES:
        parser.add_argument('--' + kind + '-completion', type=Path, required=True)
        parser.add_argument('--' + kind + '-sha256', required=True)
    args = parser.parse_args()
    started, deadline, current = a3.stamp(args.outer_started), a3.stamp(args.outer_deadline), observer.now()
    work_seconds, total_seconds = window(started, deadline, current)
    clock = time.monotonic()
    work_deadline, hard_deadline = clock+work_seconds, clock+total_seconds
    require(socket.gethostname().split('.')[0] == 'mbit10', 'a3 supervisor requires mbit10')
    require(args.driver_checkout.absolute() == args.driver_checkout.resolve() == DRIVER_ROOT,
            'a3 supervisor requires its unchanged prepared driver checkout')
    require(args.output_dir.absolute() == args.output_dir.resolve() == OUTPUT,
            'a3 supervisor requires its new fixed dispatch child directory')
    sources = runtime(args.expected_commit)
    request = validate_driver(DRIVER_ROOT)
    pane = {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}
    identity = observer.identity(os.getpid())
    ancestors = observer.ancestry(identity, pane)
    lane = profile._verified_lane(Store(DRIVER_ROOT / 'records').get('mbit10', 'machine'), 'mbit10-evaluation-node0')
    driver_command = [sys.executable, str(DRIVER_ROOT / DRIVER_PATH), '--runs-dir', str(a3.RAW_ROOT), '--lane', '0']
    for kind in a3.BATCHES:
        driver_command += ['--' + kind + '-completion', str(getattr(args, kind + '_completion').absolute()),
                           '--' + kind + '-sha256', getattr(args, kind + '_sha256')]
    def observer_command(driver, folder):
        return [sys.executable, str(ROOT / 'scripts/bfs_owned_observer.py'), '--driver-pid', str(driver['pid']),
            '--driver-start-ticks', str(driver['start_ticks']), '--pane-pid', str(pane['pid']),
            '--pane-start-ticks', str(pane['start_ticks']), '--deadline', deadline.isoformat(), '--output-dir', str(folder)]
    with interruption_signals():
        a3.launch_budget(observer.now())
        receipt = supervise(OUTPUT, driver_command, observer_command, driver_cwd=DRIVER_ROOT, observer_cwd=ROOT,
            outer_deadline=deadline, work_deadline=work_deadline, hard_deadline=hard_deadline, pane=pane,
            metadata={'outer_started': started.isoformat(), 'driver_commit': DRIVER_COMMIT,
                'driver_script': ref(DRIVER_ROOT / DRIVER_PATH), 'request': ref(request),
                'runtime_commit': args.expected_commit, 'runtime': sources, 'lane': lane, 'ancestry': ancestors})
    print(json.dumps({'state': receipt['state'], 'combined_exit': receipt['combined_exit'],
                      'launcher': ref(OUTPUT / 'launcher.json')}))
    return receipt['combined_exit']


if __name__ == '__main__':
    raise SystemExit(main())
