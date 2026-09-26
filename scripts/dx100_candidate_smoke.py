#!/usr/bin/env python3
"""Bounded public complete-call simulator and diagnostic integration smoke.

Created: 2026-09-25 (Eastern Time). This tiny graph cannot establish a gain.
Updated: 2026-09-26 (Eastern Time).
Run inside a verified socket lane with an external 2400-second timeout.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile
from swdb.store import Store
from scripts.bfs_generate_workload import widen_sg
from scripts.bfs_process import interruption_signals, run_stage

OUTER_SECONDS = 2400
CLEANUP_RESERVE_SECONDS = 30


def main():
    with interruption_signals():
        return run()


def run():
    deadline = time.monotonic() + OUTER_SECONDS
    work_deadline = deadline - CLEANUP_RESERVE_SECONDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
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
    if model['outcome']['state'] != 'complete' or model['outcome']['stage'] != 'build' or model['evidence_kind'] != 'execution':
        raise SystemExit('completed real model build required')
    folder = runs / (args.id + '.driver'); folder.mkdir(parents=True, exist_ok=False)
    stages = []
    receipt = {'id': args.id, 'created': '2026-09-25', 'state': 'running', 'stages': stages, 'gain_claim': False,
        'outer_seconds': OUTER_SECONDS, 'cleanup_reserve_seconds': CLEANUP_RESERVE_SECONDS,
        'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    def save(): (folder / 'driver.json').write_text(json.dumps(receipt, indent=2) + '\n')
    def call(command, *parameters, timeout=600):
        step = f'{len(stages):02d}-{command}'
        argv = [sys.executable, '-m', 'swdb', command, *map(str, parameters), '--format', 'json']
        out, err = folder / (step + '.json'), folder / (step + '.stderr')
        run_stage(receipt, folder, argv, timeout=min(timeout, work_deadline-time.monotonic()), deadline=deadline,
                  cwd=ROOT, output=out, stderr=err)
        return json.loads(out.read_text())
    def request(name, value):
        path = folder / (name + '.request.json'); path.write_text(json.dumps(value, indent=2) + '\n'); return path
    def ref(path): return {'path': str(path), 'sha256': artifacts.file_hash(path)}
    save()
    try:
        binaries = {Path(row['path']).name: row for row in model['build']['details']['binaries']}
        converter = Path(binaries['converter']['path'])
        if artifacts.file_hash(converter) != binaries['converter']['sha256']:
            raise RuntimeError('selected converter changed')
        sg32, sg64 = folder / 'uniform64-sg32.sg', folder / 'uniform64-sg64.sg'
        run_stage(receipt, folder, [str(converter), '-u', '6', '-k', '4', '-b', str(sg32)],
                  output=folder / 'generate.log', timeout=min(60, work_deadline-time.monotonic()), deadline=deadline,
                  cwd=ROOT, env={**os.environ, 'OMP_NUM_THREADS': '1'})
        widen_sg(sg32, sg64)
        registration = {'message_version': '1.0', 'id': args.id + '.workload', 'kernel': 'gapbs-bfs',
            'family': 'uniform_random', 'sources': [0], 'normalization': bfs_protocol.NORMALIZATION,
            'generator': {'name': 'pinned DX100 converter diagnostic', 'revision': model['build']['model_revision'],
                          'parameters': {'scale': 6, 'edge_factor': 4, 'binary_sha256': binaries['converter']['sha256']}},
            'representations': [{'id': args.id + '.' + name, 'application': application, 'format': fmt, **ref(path)}
                for name, application, fmt, path in [('sg32', 'dx100-gapbs', 'gapbs_sg32le', sg32),
                                                    ('sg64', 'gapbs', 'gapbs_sg64le', sg64)]]}
        workload = call('register-workload', request('workload', registration))
        snapshot = call('source-snapshot', 'dx100-bfs-scalar', '--id', args.id + '.source', '--runs-dir', runs)
        candidate = call('baseline-candidate', snapshot['id'], '--id', args.id + '.candidate', '--runs-dir', runs)
        evaluations = {}
        for mode in ('primary', 'diagnostic'):
            rid = args.id + '.' + mode
            build = {'message_version': '1.0', 'id': rid + '.build', 'machine': 'mbit10',
                'hardware_target': 'dx100-e4fc4af-4c', 'model_root': model['context']['model_root'],
                'build_evaluation': model['id'], 'candidate': candidate['id'], 'function': 'DOBFS',
                'accelerated': False, 'roi': 'bfs.complete_call.v1', 'diagnostic_regions': mode == 'diagnostic',
                'budget': {'total_seconds': 240, 'build_seconds': 120, 'memory_gib': 16, 'storage_gib': 1}}
            compiled = call('dx100-compile', request(mode + '-compile', build), '--runs-dir', runs, '--lane', args.lane, timeout=300)
            execution = {'message_version': '1.0', 'id': rid + '.evaluation', 'machine': 'mbit10',
                'hardware_target': 'dx100-e4fc4af-4c', 'model_root': model['context']['model_root'],
                'build_evaluation': model['id'], 'candidate': candidate['id'], 'candidate_build': compiled['id'],
                'binary': {'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']},
                'simulator': {key: binaries['gem5.opt'][key] for key in ('path', 'sha256')},
                'workload': {'id': workload['id'], 'source': 0, 'representation': ref(sg32)},
                'configuration': {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384},
                'verification': {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': 1000000000000},
                'budget': {'total_seconds': 800, 'checkpoint_seconds': 300, 'run_seconds': 450, 'memory_gib': 32, 'storage_gib': 2}}
            evaluations[mode] = call('dx100-execute', request(mode + '-execute', execution), '--runs-dir', runs, '--lane', args.lane, timeout=850)
        primary = evaluations['primary']
        collected = call('dx100-profile', request('profile', {'message_version': '1.0', 'id': args.id + '.profile',
            'evaluation': primary['id'], 'diagnostic_evaluation': evaluations['diagnostic']['id'], 'budget': {'total_seconds': 60}}),
            '--runs-dir', runs)
        context = primary['context']
        package = call('profile-package', request('package', {'message_version': '1.0', 'id': args.id + '.package',
            'implementation': candidate['implementation'], 'evaluation': primary['id'], 'region_profile': collected['id'],
            'context': {'source_sha256': candidate['artifact']['sha256'], 'canonical_graph_sha256': context['workload']['canonical_sha256'],
                        'sources': context['sources'], 'target': context['target'], 'target_configuration': context['backend_configuration'],
                        'threads': context['threads'], 'roi': context['roi']}}))
        receipt.update(state='complete', primary=primary['id'], diagnostic=evaluations['diagnostic']['id'],
                       region_profile=collected['id'], profile_package=package['id'], completeness=package['completeness'])
        if package['completeness'] != 'complete':
            raise RuntimeError('simulator smoke retained an incomplete profile package')
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}'); save(); raise
    save(); print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
