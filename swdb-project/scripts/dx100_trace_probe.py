#!/usr/bin/env python3
"""One bounded, unchanged-identity post-ROI syscall probe. Created: 2026-09-26 ET."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from swdb import artifacts, profile
from swdb.store import Store

PROBE_ID = 'bfs-dx100-exit-probe-20260926-a1'
PRIOR_ID = 'bfs-dx100-smoke-20260925-a6'
REQUEST = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-exit-probe-a1.yaml'
OUTER_SECONDS = 1200
CLEANUP_RESERVE_SECONDS = 30


def validate_request(request, prior):
    if prior.get('id') != PRIOR_ID or prior.get('evidence_kind') != 'execution':
        raise ValueError('probe requires the exact retained real a6 evaluation')
    expected = deepcopy(prior['request'])
    expected['id'] = PROBE_ID
    expected['verification'].update(max_ticks=10**10, post_roi_trace='SyscallBase')
    if request != expected:
        raise ValueError('probe may change only ID, post-ROI tick limit, and SyscallBase trace')


def run(*, request_file=REQUEST, validator=validate_request,
        purpose='post-seal syscall diagnosis; no comparison or gain claim'):
    deadline = time.monotonic() + OUTER_SECONDS - CLEANUP_RESERVE_SECONDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    runs = args.runs_dir.resolve()
    if not any(runs.is_relative_to(base) for base in (
            '/data1/yanruj/EvolveSWDB_runs', '/data/yanruj/EvolveSWDB_runs')):
        raise ValueError('probe raw output must use authorized EvolveSWDB_runs storage')
    store = Store(ROOT / 'records')
    profile._verified_lane(store.get('mbit10', 'machine'), f'mbit10-evaluation-node{args.lane}')
    request = yaml.safe_load(request_file.read_text())
    prior = store.get(PRIOR_ID, 'evaluation')
    validator(request, prior or {})
    probe_id = request['id']
    folder = runs / (probe_id + '.driver')
    folder.mkdir(parents=True, exist_ok=False)
    receipt = {'id': probe_id, 'created': '2026-09-26', 'state': 'running',
        'purpose': purpose,
        'outer_seconds': OUTER_SECONDS, 'cleanup_reserve_seconds': CLEANUP_RESERVE_SECONDS,
        'automatic_retry_allowed': False, 'gain_claim': False, 'stages': [],
        'prior_evaluation': PRIOR_ID, 'prior_evaluation_sha256': artifacts.digest(prior),
        'request': {'path': str(request_file), 'sha256': artifacts.file_hash(request_file)},
        'repository_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    save_receipt(folder, receipt)
    try:
        path = folder / 'request.json'
        path.write_text(json.dumps(request, indent=2) + '\n')
        run_stage(receipt, folder, [sys.executable, '-m', 'swdb', 'dx100-execute', str(path),
            '--runs-dir', str(runs), '--lane', str(args.lane), '--format', 'json'],
            output=folder / 'evaluation.stdout.json', stderr=folder / 'evaluation.stderr',
            cwd=ROOT, timeout=1150, deadline=deadline)
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        save_receipt(folder, receipt)


if __name__ == '__main__':
    with interruption_signals():
        run()
