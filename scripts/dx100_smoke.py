#!/usr/bin/env python3
"""Bounded real-model compatibility smoke through the public adapter.

Created: 2026-09-25 (Eastern Time). Tiny uniform graph is diagnostic only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import profile
from swdb.store import Store


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id', required=True)
    p.add_argument('--build-evaluation', required=True)
    p.add_argument('--runs-dir', type=Path, required=True)
    p.add_argument('--lane', type=int, choices=(0, 1), required=True)
    p.add_argument('--checkpoint-evaluation', help='reuse only an exact matching retained real checkpoint')
    a = p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', a.id):
        raise SystemExit('smoke ID must use the record identifier syntax')
    a.runs_dir = a.runs_dir.resolve()
    if not any(a.runs_dir.is_relative_to(base) for base in (
            '/data1/yanruj/EvolveSWDB_runs', '/data/yanruj/EvolveSWDB_runs')):
        raise SystemExit('smoke raw output must use authorized EvolveSWDB_runs storage')
    store = Store(ROOT / 'records')
    profile._verified_lane(store.get('mbit10', 'machine'), f'mbit10-evaluation-node{a.lane}')
    build = store.get(a.build_evaluation, 'evaluation')
    if (build['outcome']['state'] != 'complete' or build['outcome']['stage'] != 'build'
            or build['evidence_kind'] != 'execution'):
        raise SystemExit('a completed real model build is required')
    folder = a.runs_dir.resolve() / (a.id + '.driver')
    folder.mkdir(parents=True, exist_ok=False)
    binaries = {Path(row['path']).name: row for row in build['build']['details']['binaries']}
    def ref(path):
        return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    prior = store.get(a.checkpoint_evaluation, 'evaluation') if a.checkpoint_evaluation else None
    if a.checkpoint_evaluation:
        if (not prior or prior.get('evidence_kind') != 'execution'
                or not prior.get('context', {}).get('checkpoint_manifest')):
            raise SystemExit('reuse requires an existing identified real checkpoint')
        workload = prior['request']['workload']
    else:
        converter = Path(binaries['converter']['path'])
        if ref(converter)['sha256'] != binaries['converter']['sha256']:
            raise SystemExit('converter changed since the selected build')
        graph = folder / 'uniform64.sg'
        with (folder / 'generate.log').open('w') as log:
            subprocess.run([str(converter), '-u', '6', '-k', '4', '-b', str(graph)],
                stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60,
                env={**os.environ, 'OMP_NUM_THREADS': '1'})
        workload = {'id': a.id + '.uniform64-diagnostic', 'source': 0, 'representation': ref(graph)}
    request = {'message_version': '1.0', 'id': a.id, 'machine': 'mbit10',
        'hardware_target': 'dx100-e4fc4af-4c', 'model_root': build['context']['model_root'],
        'build_evaluation': build['id'],
        'simulator': {key: binaries['gem5.opt'][key] for key in ('path', 'sha256')},
        'binary': {key: binaries['bfs_maa'][key] for key in ('path', 'sha256')},
        'workload': workload,
        'configuration': {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384},
        'verification': {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': 1000000000000},
        'budget': {'total_seconds': 1100, 'memory_gib': 32, 'storage_gib': 2,
            'checkpoint_seconds': 300, 'run_seconds': 750}}
    if prior:
        request['checkpoint_manifest'] = prior['context']['checkpoint_manifest']
        request['checkpoint_evaluation'] = prior['id']
    path = folder / 'request.json'
    path.write_text(json.dumps(request, indent=2) + '\n')
    with (folder / 'evaluation.stdout.json').open('w') as out, (folder / 'evaluation.stderr').open('w') as err:
        result = subprocess.run([sys.executable, '-m', 'swdb', 'dx100-execute', str(path),
            '--runs-dir', str(a.runs_dir), '--lane', str(a.lane), '--format', 'json'],
            cwd=ROOT, stdout=out, stderr=err, timeout=1150)
    print((folder / 'evaluation.stdout.json').read_text())
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
