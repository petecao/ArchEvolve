#!/usr/bin/env python3
"""Collect unchanged native BFS pilot evidence through the public CLI.

Created: 2026-09-25 (Eastern Time). This driver never freezes a protocol,
submits a rewrite, compares candidates, or claims a gain.
"""
import argparse
import json
import os
import re
import signal
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, profile
from swdb.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--implementation', choices=['dx100-bfs-scalar', 'gapbs-bfs-do'], required=True)
    parser.add_argument('--workloads', nargs=2, required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--lane', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        parser.error('id must use record identifier syntax')
    if socket.gethostname().split('.')[0] != 'mbit10':
        parser.error('this bounded pilot requires mbit10')
    runs = artifacts.external_directory(args.runs_dir)
    if not any(base in runs.parents for base in (Path('/data1/yanruj'), Path('/data/yanruj'))):
        parser.error('raw output must use an authorized host volume')
    store = Store(args.records)
    profile._verified_lane(store.get('mbit10', 'machine'), args.lane)
    folder = runs / (args.id + '.driver')
    folder.mkdir(exist_ok=False)
    receipt = {'id': args.id, 'state': 'running', 'implementation': args.implementation,
               'role': 'unchanged_source_baseline_pilot', 'gain_claim': False,
               'protocol_freeze': False, 'lane': args.lane, 'stages': [], 'workloads': [],
               'bounds': {'threads': 4, 'repetitions': 5, 'warmups': 0,
                          'evaluation_seconds': 1200, 'profile_seconds': 1200,
                          'driver_seconds': 7200}}
    started = time.monotonic()

    def save():
        (folder / 'driver.json').write_text(json.dumps(receipt, indent=2))

    def interrupt(signum, _frame):
        raise InterruptedError(f'pilot interrupted by signal {signum}')

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupt)

    def call(command, *rest, timeout=180):
        profile._verified_lane(store.get('mbit10', 'machine'), args.lane)
        remaining = 7200 - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError('pilot driver budget exhausted')
        if os.statvfs(runs).f_bavail * os.statvfs(runs).f_frsize < 30 * 1024**3:
            raise RuntimeError('pilot raw-output free-space reserve is below 30 GiB')
        if os.statvfs('/data1').f_bavail * os.statvfs('/data1').f_frsize < 10 * 1024**3:
            raise RuntimeError('pilot source/build free-space reserve is below 10 GiB')
        index = len(receipt['stages'])
        out, err = folder / f'{index:02}-{command}.json', folder / f'{index:02}-{command}.stderr'
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest),
                '--records', str(args.records), '--format', 'json']
        entry = {'command': argv, 'state': 'running', 'stdout': str(out), 'stderr': str(err)}
        receipt['stages'].append(entry)
        save()
        before = time.monotonic()
        with out.open('w') as stdout, err.open('w') as stderr:
            child = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                child.wait(timeout=min(timeout, remaining))
            except BaseException:
                # Give the evaluator a chance to persist interrupted stages before killing.
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
                    child.wait()
                entry.update(state='interrupted_or_timeout', returncode=child.returncode)
                save()
                raise
        entry.update(state='complete' if child.returncode == 0 else 'failed',
                     returncode=child.returncode, host_wall_s=time.monotonic() - before,
                     stdout_sha256=artifacts.file_hash(out), stderr_sha256=artifacts.file_hash(err))
        save()
        if child.returncode:
            raise RuntimeError(f'{command} failed; retained {out} and {err}')
        return json.loads(out.read_text())

    def request(command, value, *, timeout=180, execute=False):
        path = folder / (value['id'] + '.request.json')
        path.write_text(json.dumps(value, indent=2))
        rest = ['--runs-dir', runs, '--lane', args.lane] if execute else []
        return call(command, path, *rest, timeout=timeout)

    save()
    try:
        receipt['repository_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        workloads = [call('get', wid) for wid in args.workloads]
        if {w['definition']['family'] for w in workloads} != {'kronecker', 'uniform_random'}:
            raise ValueError('pilot requires exactly one registered workload per graph family')
        if any(w['kind'] != 'workload' or w['definition']['sources'] != [0, 1234, 7777] for w in workloads):
            raise ValueError('pilot requires registered planned source sequence [0, 1234, 7777]')
        source = call('source-snapshot', args.implementation, '--id', args.id + '.source', '--runs-dir', runs)
        baseline = call('baseline-candidate', source['id'], '--id', args.id + '.baseline', '--runs-dir', runs)
        if baseline['artifact']['sha256'] != source['artifact']['sha256']:
            raise RuntimeError('unchanged baseline source identity changed')
        receipt.update(source_snapshot=source['id'], candidate=baseline['id'])
        save()
        for workload in workloads:
            family = workload['definition']['family']
            prefix = args.id + '.' + family.replace('_', '-')
            entry = {'workload': workload['id'], 'family': family, 'state': 'running'}
            receipt['workloads'].append(entry)
            save()
            evaluation = request('evaluate', {'message_version': '1.0', 'id': prefix + '.evaluation',
                'candidate': baseline['id'], 'machine': 'mbit10', 'threads': 4, 'repetitions': 5,
                'sources': workload['definition']['sources'], 'roi': 'bfs.complete_call.v1',
                'target_configuration': {'lane': args.lane}, 'workload': {'id': workload['id']},
                'comparison_baseline': args.implementation,
                'budget': {'build_seconds': 180, 'run_seconds': 60, 'total_seconds': 1200}},
                timeout=1260, execute=True)
            if evaluation['correctness']['state'] != 'passed' or len(evaluation['timing']) != 15:
                raise RuntimeError('pilot requires all fifteen independently verified timing observations')
            entry.update(evaluation=evaluation['id'], timing_summary=[])
            for position, vertex in enumerate(workload['definition']['sources']):
                values = [row['duration_s'] for row in evaluation['timing'] if row['source_position'] == position]
                entry['timing_summary'].append({'source_position': position, 'source': vertex,
                    'samples': values, 'median_seconds': statistics.median(values),
                    'relative_spread': (max(values) - min(values)) / statistics.median(values)})
            save()
            discovered = request('bfs-profile', {'message_version': '1.0', 'id': prefix + '.profile',
                'evaluation': evaluation['id'], 'memory': True,
                'budget': {'discovery_seconds': 120, 'build_seconds': 180, 'run_seconds': 600, 'total_seconds': 1200}},
                timeout=1260, execute=True)
            context = evaluation['context']
            package = request('profile-package', {'message_version': '1.0', 'id': prefix + '.package',
                'implementation': args.implementation, 'evaluation': evaluation['id'], 'region_profile': discovered['id'],
                'context': {'source_sha256': context['candidate_sha256'],
                    'canonical_graph_sha256': context['workload']['canonical_sha256'],
                    'sources': context['sources'], 'target': context['target'],
                    'target_configuration': context['backend_configuration'],
                    'threads': context['threads'], 'roi': context['roi']}})
            entry.update(region_profile=discovered['id'], profile_package=package['id'],
                         package_completeness=package['completeness'], reasons=package['reasons'])
            call('profile-strategies', package['id'])
            call('get', package['id'], '--chain')
            if package['completeness'] != 'complete':
                raise RuntimeError('pilot package is incomplete: ' + '; '.join(package['reasons']))
            entry['state'] = 'complete'
            save()
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        save()
        raise
    receipt['host_wall_s'] = time.monotonic() - started
    save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
