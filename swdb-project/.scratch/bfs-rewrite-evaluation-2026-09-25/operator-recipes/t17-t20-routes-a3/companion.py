#!/usr/bin/env python3
"""AC10 companion case for one candidate's exact timed binary. Created 2026-09-28 ET.

Implements `bfs.dx100.competing-parent-case.v1` from the frozen T17/T20 protocols:
one correctness-only public dx100-execute of the candidate primary build and
frozen MAA configuration on the collision graph (source 0). The template is the
candidate's retained uniform18 s0.r0 primary request from the route series; only
the ID, budget, graph and protocol binding change (correctness-only, no timing
sample). Runs inside socket_lane.sh. No retry: an existing run root refuses.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

ET = ZoneInfo('America/New_York')
WORKLOAD = 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e'
BUDGET = {'total_seconds': 3300, 'checkpoint_seconds': 600, 'run_seconds': 2400, 'memory_gib': 48, 'storage_gib': 10}
REQUIRED = {'executed', 'full_tiles', 'tail_tiles', 'competing_parent_updates'}


def require(ok, why):
    if not ok:
        raise SystemExit('refused: ' + why)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--root', type=Path, required=True, help='counted allocation root for this case')
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--primary-build', required=True)
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    require(os.environ.get('LACT_SOCKET_LANE_PID'), 'run inside socket_lane.sh')
    store = Store(ROOT / 'records')
    raw = args.root / args.run_id
    require(not raw.exists() and store.get(args.run_id + '.execute') is None, 'fresh run ID required; no retry')
    build = store.get(args.primary_build, 'evaluation')
    template = json.loads(args.template.read_text())
    require(template.get('candidate_build') == build['id']
            and template['binary'] == {'path': build['build']['binary'], 'sha256': build['build']['binary_sha256']}
            and template['verification'].get('coverage') is True, 'template is not this candidate timed primary')
    workload = store.get(WORKLOAD, 'workload')
    rep = next(r for r in workload['definition']['representations'] if r['application'] == 'dx100-gapbs')
    require(artifacts.file_hash(rep['path']) == rep['sha256'], 'collision graph representation changed')
    request = {key: value for key, value in template.items()
               if key not in {'protocol', 'protocol_role', 'checkpoint_manifest'}}
    request.update(id=args.run_id + '.execute', budget=BUDGET, protocol_trial={'source_position': 0, 'repetition': 0},
                   workload={'id': WORKLOAD, 'source': 0, 'representation': {'path': rep['path'], 'sha256': rep['sha256']}})
    raw.mkdir(parents=True); (raw / 'runs').mkdir()
    path = raw / 'request.json'; path.write_text(json.dumps(request, indent=2) + '\n')
    receipt = {'format': 'swdb.bfs.ac10-companion-case.v1', 'case': 'bfs.dx100.competing-parent-case.v1',
               'id': args.run_id, 'created': '2026-09-28', 'started': datetime.now(ET).isoformat(),
               'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'template': {'path': str(args.template), 'sha256': artifacts.file_hash(args.template)},
               'request': {'path': str(path), 'sha256': artifacts.file_hash(path)},
               'primary_build': args.primary_build, 'timed_binary_sha256': build['build']['binary_sha256'],
               'workload': WORKLOAD, 'gain_claim': False, 'automatic_retry_allowed': False}
    common = ['--records', str(ROOT / 'records'), '--db', str(raw / 'swdb.sqlite'), '--format', 'json']
    began = time.monotonic()
    with (raw / 'execute.json').open('x') as out, (raw / 'execute.stderr').open('x') as err:
        code = subprocess.run([sys.executable, '-m', 'swdb', 'dx100-execute', str(path), '--runs-dir', str(raw / 'runs'),
                               '--lane', str(args.lane), *common], cwd=ROOT, stdout=out, stderr=err,
                              timeout=BUDGET['total_seconds'] + 120).returncode
    fresh = subprocess.run([sys.executable, '-m', 'swdb', 'get', args.run_id + '.execute', *common], cwd=ROOT,
                           capture_output=True, text=True, timeout=180)
    record = json.loads(fresh.stdout) if fresh.returncode == 0 else {}
    from swdb.bfs_protocol import accelerator_cases
    check = ((record.get('correctness') or {}).get('checks') or [{}])[0]
    observed = sorted(accelerator_cases(check)) if check else []
    parent = (check.get('coverage') or {}).get('competing_parent_updates') or {}
    receipt.update(finished=datetime.now(ET).isoformat(), execute_returncode=code,
                   execute_host_wall_s=time.monotonic() - began, fresh_get_returncode=fresh.returncode,
                   outcome=record.get('outcome'), correctness=(record.get('correctness') or {}).get('state'),
                   binary_sha256=(record.get('timing') or [{}])[0].get('binary_sha256'),
                   accelerator_cases=observed, competing_parent_updates={k: parent.get(k) for k in ('state', 'count')},
                   parent_storage_attributed=parent.get('parent_storage') is not None,
                   record_sha256=artifacts.digest(record) if record else None)
    receipt['passed'] = (code == 0 and receipt['correctness'] == 'passed'
                         and receipt['binary_sha256'] == build['build']['binary_sha256']
                         and REQUIRED <= set(observed) and receipt['parent_storage_attributed'])
    with (raw / 'receipt.json').open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if receipt['passed'] else 1)


if __name__ == '__main__':
    main()
