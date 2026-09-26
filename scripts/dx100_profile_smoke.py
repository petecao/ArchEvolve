#!/usr/bin/env python3
"""Collect one real, explicitly unverified DX100 source profile.

Created: 2026-09-25 (Eastern Time). This fixed diagnostic is not a pilot,
candidate assessment, retry, comparison, or accelerator-coverage claim.
Updated: 2026-09-26 (Eastern Time).
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile
from swdb.store import Store
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from scripts.bfs_simulator_series import validate_diagnostic_build
from scripts.dx100_build import disk_usage_kib


@interruption_signals()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    if socket.gethostname().split('.')[0] != 'mbit10':
        parser.error('this real diagnostic requires mbit10')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        parser.error('invalid diagnostic identifier')
    runs = args.runs_dir.resolve()
    if not any(runs != Path(base) and runs.is_relative_to(base) for base in (
            '/data/yanruj/EvolveSWDB_runs', '/data1/yanruj/EvolveSWDB_runs')):
        parser.error('use a dedicated child of the authorized run storage')
    runs = artifacts.external_directory(runs)
    if any(runs.iterdir()):
        parser.error('the diagnostic output directory must be empty')
    store = Store(ROOT / 'records')
    lane = f'mbit10-evaluation-node{args.lane}'
    profile._verified_lane(store.get('mbit10', 'machine'), lane)
    folder = runs / (args.id + '.driver')
    folder.mkdir()
    started = time.monotonic()
    deadline = started + 2370  # Required outer timeout is 2400 seconds.
    receipt = {'id': args.id, 'created': datetime.now(ZoneInfo('America/New_York')).isoformat(), 'state': 'running',
        'purpose': 'source_bound_observation_diagnostic', 'gain_claim': False,
        'accelerator_coverage_claim': False, 'stages': [], 'lane': lane,
        'bounds': {'outer_seconds': 2400, 'memory_gib': 48, 'batch_storage_gib': 4,
                   'attempts_per_treatment': 1},
        'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}

    def save():
        receipt['host_wall_s'] = time.monotonic() - started
        save_receipt(folder, receipt)

    def monitor():
        if time.monotonic() >= deadline:
            raise TimeoutError('fixed diagnostic deadline reached')
        for volume, reserve in ((runs, 30), (Path('/data1'), 10)):
            stat = os.statvfs(volume)
            if stat.f_bavail * stat.f_frsize < reserve * 1024**3:
                raise RuntimeError(f'{volume}: free-space reserve below {reserve} GiB')
        used, warnings = disk_usage_kib(runs)
        if warnings:
            raise RuntimeError('cannot account for diagnostic output storage: ' + '; '.join(warnings))
        if used * 1024 >= 4 * 1024**3:
            raise RuntimeError('fixed diagnostic batch storage bound reached')

    def call(command, *rest, timeout=120, retained_execution=None):
        profile._verified_lane(Store(ROOT / 'records').get('mbit10', 'machine'), lane)
        monitor()
        out = folder / f'{len(receipt["stages"]):02d}-{command}.json'
        try:
            run_stage(receipt, folder, [sys.executable, '-m', 'swdb', command, *map(str, rest), '--format', 'json'],
                output=out, timeout=timeout, deadline=deadline, cwd=ROOT, monitor=monitor)
        except RuntimeError:
            # The CLI returns 1 for a retained unsuccessful evaluation. Its
            # stage stays failed in this receipt; only exact sealed observations
            # may proceed to independent collection. Infrastructure failures do
            # not become accepted merely because an output file exists.
            stage = receipt['stages'][-1]
            if (retained_execution is None or stage.get('returncode') != 1
                    or stage.get('state') != 'failed'):
                raise
            value = json.loads(out.read_text())
            persisted = Store(ROOT / 'records').get(retained_execution, 'evaluation')
            if (not persisted or value != persisted or value.get('id') != retained_execution
                    or value.get('outcome', {}).get('state') not in {
                        'incorrect', 'missing_observation', 'timed_out', 'budget_exhausted', 'interrupted'}
                    or not all(key in value.get('context', {})
                               for key in ('sealed_roi', 'statistics', 'actual_configuration'))):
                raise
        finally:
            save()
        return json.loads(out.read_text())

    def request(command, payload, *, timeout=120, execute=False):
        path = folder / (payload['id'] + '.request.json')
        path.write_text(json.dumps(payload, indent=2) + '\n')
        options = ['--runs-dir', runs, '--lane', args.lane] if execute else []
        if command == 'dx100-profile':
            options = ['--runs-dir', runs]
        return call(command, path, *options,
                    timeout=timeout, retained_execution=payload['id'] if execute else None)

    save()
    try:
        model = call('get', 'bfs-dx100-build-20260925-a2')
        prior = call('get', 'bfs-dx100-smoke-20260925-a6')
        candidate = call('get', 'bfs-dx100-compile-20260925-a1.candidate')
        implementation = call('get', candidate['implementation'])
        source = call('get', candidate['source_snapshot'])
        builds = {kind: call('get', f'bfs-dx100-compile-20260925-a1.{kind}.build')
                  for kind in ('primary', 'diagnostic')}
        expected = artifacts.identify(artifacts.source_root(Store(ROOT / 'records'), implementation))
        if (candidate.get('artifact_role') != 'source_baseline' or candidate.get('proposal')
                or candidate['artifact']['sha256'] != source['artifact']['sha256']
                or candidate['artifact']['sha256'] != expected['sha256']):
            raise ValueError('the observation probe requires the unchanged scalar baseline')
        validate_diagnostic_build(builds['diagnostic'], candidate, implementation, model,
                                  'bfs.complete_call.v1', False)
        graph = prior['request']['workload']['representation']
        if graph['sha256'] != '00d156b95baa9806c8e7623400e0347770942aee64dbed227309886ee605f78b':
            raise ValueError('the retained tiny diagnostic graph differs from the plan')
        workload = request('register-workload', {'message_version': '1.0', 'id': args.id + '.uniform64',
            'kernel': 'gapbs-bfs', 'family': 'uniform_random',
            'generator': {'name': 'DX100 GAPBS converter', 'revision': model['build']['model_revision'],
                'parameters': {'scale': 6, 'edge_factor': 4, 'seed': 27491095, 'symmetrize': True,
                               'source_evaluation': prior['id'], 'purpose': 'profiling bring-up only'}},
            'normalization': bfs_protocol.NORMALIZATION, 'sources': [0],
            'representations': [{'id': args.id + '.dx100', **graph,
                                'format': 'gapbs_sg32le', 'application': 'dx100-gapbs'}]})
        pair = {}
        for treatment in ('primary', 'diagnostic'):
            built = builds[treatment]
            total, run = (1100, 750) if treatment == 'primary' else (600, 270)
            pair[treatment] = request('dx100-execute', {
                'message_version': '1.0', 'id': args.id + '.' + treatment,
                'machine': 'mbit10', 'hardware_target': 'dx100-e4fc4af-4c',
                'model_root': model['context']['model_root'], 'build_evaluation': model['id'],
                'candidate': candidate['id'], 'candidate_build': built['id'],
                'simulator': prior['request']['simulator'],
                'binary': {'path': built['build']['binary'], 'sha256': built['build']['binary_sha256']},
                'workload': {'id': workload['id'], 'source': 0, 'representation': graph},
                'configuration': {'mode': 'BASE', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384},
                'verification': {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': 10**10},
                'budget': {'total_seconds': total, 'checkpoint_seconds': 300, 'run_seconds': run,
                           'memory_gib': 48, 'storage_gib': 2}}, timeout=total + 30, execute=True)
            context = pair[treatment]['context']
            if not all(key in context for key in ('sealed_roi', 'statistics', 'actual_configuration')):
                raise RuntimeError(f'{treatment} has no complete sealed observation; no retry')
        collected = request('dx100-profile', {'message_version': '1.0', 'id': args.id + '.profile',
            'evaluation': pair['primary']['id'], 'diagnostic_evaluation': pair['diagnostic']['id'],
            'budget': {'total_seconds': 120}}, timeout=150)
        context = pair['primary']['context']
        package = request('profile-package', {'message_version': '1.0', 'id': args.id + '.package',
            'implementation': candidate['implementation'], 'evaluation': pair['primary']['id'],
            'region_profile': collected['id'], 'context': {
                'source_sha256': candidate['artifact']['sha256'],
                'canonical_graph_sha256': context['workload']['canonical_sha256'],
                'sources': [0], 'target': context['target'],
                'target_configuration': context['backend_configuration'], 'threads': 4, 'roi': context['roi']}})
        refreshed = call('get', pair['primary']['id'], '--chain')
        catalog = Store(ROOT / 'records')
        if refreshed.get('root') != pair['primary']['id']:
            raise RuntimeError('fresh result chain has the wrong root')
        for record_id in (pair['primary']['id'], pair['diagnostic']['id'], collected['id'], package['id']):
            if refreshed.get('records', {}).get(record_id) != catalog.get(record_id):
                raise RuntimeError('fresh result chain omits or changes ' + record_id)
        for value in pair.values():
            current = refreshed['records'][value['id']]
            if any(current[key] != value[key] for key in ('outcome', 'correctness')):
                raise RuntimeError('collection changed a retained execution verdict')
        if (refreshed['records'][package['id']] != package
                or refreshed['records'][collected['id']] != collected):
            raise RuntimeError('fresh result chain changes profile/package evidence')
        receipt.update(profile=collected['id'], package=package['id'], completeness=package['completeness'],
            collection_outcome=collected['outcome'], collection_limits=collected['reasons'],
            execution_outcomes={key: value['outcome'] for key, value in pair.items()},
            correctness={key: value['correctness'] for key, value in pair.items()},
            fresh_result_retrieved=True)
        if collected['outcome']['state'] not in {'complete', 'partial'} or package['completeness'] != 'complete':
            raise RuntimeError('actual observation package remains incomplete')
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
