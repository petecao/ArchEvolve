#!/usr/bin/env python3
"""Compile unchanged primary and diagnostic BFS through the public interface.

Created: 2026-09-25 (Eastern Time). No guest execution or performance claim.
Run in a verified socket lane under an outer 700-second timeout.
"""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, profile
from swdb.store import Store

OUTER_SECONDS = 700
CLEANUP_RESERVE_SECONDS = 30


def main():
    # Leave 30 seconds for the public evaluator's nested compiler termination
    # and final receipt before the required outer 700-second timeout.
    deadline = time.monotonic() + OUTER_SECONDS - CLEANUP_RESERVE_SECONDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--implementation', choices=('gapbs-bfs-do', 'dx100-bfs-scalar', 'dx100-bfs-maa-reference'),
                        default='dx100-bfs-scalar')
    parser.add_argument('--build-evaluation', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        raise SystemExit('invalid smoke identifier')
    runs = args.runs_dir.resolve()
    if not any(runs.is_relative_to(base) for base in ('/data/yanruj/EvolveSWDB_runs', '/data1/yanruj/EvolveSWDB_runs')):
        raise SystemExit('raw output must use authorized EvolveSWDB_runs storage')
    store = Store(ROOT / 'records')
    profile._verified_lane(store.get('mbit10', 'machine'), f'mbit10-evaluation-node{args.lane}')
    model = store.get(args.build_evaluation, 'evaluation')
    if (not model or model['outcome']['state'] != 'complete' or model['outcome']['stage'] != 'build'
            or model['evidence_kind'] != 'execution'):
        raise SystemExit('completed real model build required')
    implementation = store.get(args.implementation, 'implementation')
    folder = runs / (args.id + '.driver')
    folder.mkdir(parents=True, exist_ok=False)
    receipt = {'id': args.id, 'created': '2026-09-25', 'state': 'running', 'stages': [], 'builds': {},
               'gain_claim': False, 'guest_execution': False, 'model_build': model['id'],
               'outer_seconds': OUTER_SECONDS, 'cleanup_reserve_seconds': CLEANUP_RESERVE_SECONDS,
               'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    interrupted = False
    def interrupt(signum, frame):
        nonlocal interrupted
        if interrupted:
            return
        interrupted = True
        raise InterruptedError(f'compile smoke interrupted by signal {signum}')
    handlers = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    def save():
        (folder / 'driver.json').write_text(json.dumps(receipt, indent=2) + '\n')
    def call(command, *parameters, timeout=60):
        step = f"{len(receipt['stages']):02d}-{command}"
        argv = [sys.executable, '-m', 'swdb', command, *map(str, parameters), '--format', 'json']
        out, err = folder / (step + '.json'), folder / (step + '.stderr')
        row = {'command': argv, 'output': str(out), 'stderr': str(err), 'state': 'running'}
        receipt['stages'].append(row)
        save()
        before = time.monotonic()
        child = None
        try:
            with out.open('w') as stdout, err.open('w') as stderr:
                allowed = min(timeout, deadline - time.monotonic())
                if allowed <= 0:
                    raise TimeoutError('compile smoke total time budget exhausted')
                row['timeout_s'] = allowed
                child = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
                child.wait(timeout=allowed)
            row['state'] = 'complete' if child.returncode == 0 else 'failed'
        except BaseException as exc:
            if child is not None and child.poll() is None:
                # The public evaluator catches TERM, terminates its separately
                # grouped compiler, and persists interrupted stages.
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=5)
            row.update(state='interrupted_or_timeout' if isinstance(exc, (InterruptedError, TimeoutError, subprocess.TimeoutExpired)) else 'failed',
                       reason=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            row.update(returncode=child.returncode if child is not None else None,
                       host_wall_s=time.monotonic() - before,
                       stdout_sha256=artifacts.file_hash(out), stderr_sha256=artifacts.file_hash(err))
            save()
        if child.returncode:
            raise RuntimeError(f'{command} failed; retained {out} and {err}')
        return json.loads(out.read_text())
    save()
    try:
        source = call('source-snapshot', args.implementation, '--id', args.id + '.source', '--runs-dir', runs)
        candidate = call('baseline-candidate', source['id'], '--id', args.id + '.candidate', '--runs-dir', runs)
        if candidate['artifact']['sha256'] != source['artifact']['sha256']:
            raise RuntimeError('unchanged baseline source identity changed')
        receipt.update(candidate=candidate['id'], source_snapshot=source['id'], source_sha256=candidate['artifact']['sha256'])
        for mode in ('primary', 'diagnostic'):
            rid = args.id + '.' + mode
            request = {'message_version': '1.0', 'id': rid + '.build', 'machine': 'mbit10',
                'hardware_target': 'dx100-e4fc4af-4c', 'model_root': model['context']['model_root'],
                'build_evaluation': model['id'], 'candidate': candidate['id'], 'function': implementation['function'],
                'accelerated': args.implementation == 'dx100-bfs-maa-reference', 'roi': 'bfs.complete_call.v1',
                'diagnostic_regions': mode == 'diagnostic',
                'budget': {'total_seconds': 240, 'build_seconds': 120, 'memory_gib': 16, 'storage_gib': 1}}
            path = folder / (mode + '.request.json')
            path.write_text(json.dumps(request, indent=2) + '\n')
            built = call('dx100-compile', path, '--runs-dir', runs, '--lane', args.lane, timeout=300)
            receipt['builds'][mode] = {'evaluation': built['id'], 'binary_sha256': built['build']['binary_sha256'],
                'flags': built['build']['flags'], 'compiler_version': built['build']['compiler_version'],
                'source_sha256': built['context']['candidate_sha256'], 'model': built['context']['model']}
            call('get', built['id'])
            save()
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        save()
        raise
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
