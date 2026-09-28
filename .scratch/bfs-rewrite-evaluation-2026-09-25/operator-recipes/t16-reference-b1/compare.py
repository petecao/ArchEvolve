#!/usr/bin/env python3
"""T16 v3 post-batch comparisons and fresh-process retrieval. Created 2026-09-28 ET.

Usage: compare.py <runtime checkout>. The runtime checkout must hold the public
records written by the three completed split jobs (M, S1, S2) in its records
folder. This script reads their completed series receipts, issues exactly two
public compare-evaluations requests (artifact pair, matched control) and
retrieves every result in fresh processes. It runs no execution, retries
nothing and changes no protocol. An existing output folder or comparison ID is
refused. The version-3 protocols have no region pairs, so no region packages
are passed.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
RUNS = Path('/data/yanruj/EvolveSWDB_runs')
JOBS = {'maa': 'bfs-t16-reference-m-simulator-batch-20260928-c1',
        'artifact.scalar': 'bfs-t16-reference-s1-simulator-batch-20260928-c1',
        'control.scalar': 'bfs-t16-reference-s2-simulator-batch-20260928-c1'}
OUT = RUNS/'bfs-t16-reference-comparisons-20260928-c1'


def series(family):
    plan_id = JOBS[family]; sid = f'{plan_id}.{family}'
    path = RUNS/plan_id/sid/sid/(sid + '.driver')/'driver.json'
    value = json.loads(path.read_text())
    if value.get('state') != 'complete':
        raise SystemExit(f'refused: {family} series is not complete')
    return value


def swdb(*args):
    result = subprocess.run([sys.executable, '-m', 'swdb', *args, '--records', str(ROOT/'records'), '--format', 'json'],
                            cwd=ROOT, capture_output=True, text=True, timeout=7200)
    return result.returncode, result.stdout, result.stderr


def main():
    if ROOT is None or not (ROOT/'swdb').is_dir():
        raise SystemExit('usage: compare.py <runtime checkout>')
    plan = json.loads((ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/requests'/(JOBS['maa'] + '.json')).read_text())
    frozen = {key: value['frozen_id'] for key, value in plan['protocol_requests'].items()}
    scalar = {key: series(f'{key}.scalar') for key in ('artifact', 'control')}
    maa = series('maa')
    candidate = {'artifact': maa['aggregate'], 'control': maa['shared_aggregates'][frozen['control']]}
    OUT.mkdir(exist_ok=False)
    summary = {'created': '2026-09-28', 'runtime': str(ROOT), 'comparisons': {}}
    for key in ('artifact', 'control'):
        request = {'message_version': '1.0', 'id': f'bfs-t16-reference-20260928-c1.{key}.comparison', 'protocol': frozen[key],
                   'baseline_evaluation': scalar[key]['aggregate'], 'candidate_evaluation': candidate[key],
                   'comparison_baseline': 'dx100-bfs-scalar'}
        path = OUT/(request['id'] + '.request.json')
        path.write_text(json.dumps(request, indent=2) + '\n')
        code, stdout, stderr = swdb('compare-evaluations', str(path))
        (OUT/(request['id'] + '.stdout.json')).write_text(stdout)
        (OUT/(request['id'] + '.stderr')).write_text(stderr)
        fresh = {rid: swdb('get', rid, '--chain')[0]
                 for rid in (request['id'], candidate[key], scalar[key]['aggregate'])}
        result = json.loads(stdout) if stdout.strip() else {}
        summary['comparisons'][key] = {'request': str(path), 'returncode': code, 'fresh_retrieval_returncodes': fresh,
            'decision': result.get('decision'), 'gain_claim': result.get('gain_claim'),
            'evidence_kind': result.get('evidence_kind'), 'metrics': result.get('metrics')}
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
