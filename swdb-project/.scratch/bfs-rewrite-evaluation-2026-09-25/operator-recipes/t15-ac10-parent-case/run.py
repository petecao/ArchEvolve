#!/usr/bin/env python3
"""AC10 timed-binary competing-parent correctness case. Created 2026-09-27 ET.

Runs one correctness-only public dx100-execute of the exact T15 primary
(timed) author binary and MAA configuration on the fixed collision-heavy A2
coverage graph (8,212 vertices; 4,097-vertex frontier sharing 16 parents).
Diagnostic coverage never substitutes for this primary evidence. Run it inside
socket_lane.sh and an outer timeout of at most 3,600 s, after the T15 grid.
No retry: an existing run root or record ID refuses.
"""
import argparse
from datetime import datetime
import hashlib
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
RUN_ID = 'bfs-t15-ac10-parent-case-20260928-a1'
RAW = Path('/data/yanruj/EvolveSWDB_runs') / RUN_ID
WORKLOAD = 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e'
PRIMARY_BINARY_SHA = '6abd8190e4e1daf7c670c214dd0323393e3d29a9a26a3487c21f66e5ef194a5d'
BUDGET = {'total_seconds': 3300, 'checkpoint_seconds': 600, 'run_seconds': 2400, 'memory_gib': 48, 'storage_gib': 10}


def require(ok, why):
    if not ok:
        raise SystemExit('refused: ' + why)


def now():
    return datetime.now(ET).isoformat()


def payload(template_path, store):
    """Reuse the actual b3 primary request; change only the correctness graph."""
    template = json.loads(Path(template_path).read_text())
    require(template['binary']['sha256'] == PRIMARY_BINARY_SHA and 'candidate_build' not in template
            and template['verification'].get('coverage') is True, 'template is not the exact timed primary')
    workload = store.get(WORKLOAD, 'workload')
    rep = next(r for r in workload['definition']['representations'] if r['application'] == 'dx100-gapbs')
    require(artifacts.file_hash(rep['path']) == rep['sha256'], 'A2 graph representation changed')
    value = dict(template)
    value.update(id=RUN_ID + '.execute', budget=BUDGET,
                 workload={'id': WORKLOAD, 'source': 0, 'representation': {'path': rep['path'], 'sha256': rep['sha256']}},
                 protocol_trial={'source_position': 0, 'repetition': 0})
    value.pop('checkpoint_manifest', None)
    return template, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True, help='retained T15 b3 primary request JSON')
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    require(os.environ.get('LACT_SOCKET_LANE_PID'), 'run inside socket_lane.sh')
    store = Store(ROOT / 'records')
    require(not RAW.exists() and store.get(RUN_ID + '.execute') is None, 'fresh run ID required; no retry')
    template, request = payload(args.template, store)
    RAW.mkdir(parents=True)
    runs = RAW / 'runs'; runs.mkdir()
    req = RAW / 'request.json'; req.write_text(json.dumps(request, indent=2) + '\n')
    receipt = {'format': 'swdb.bfs.ac10-parent-case.v1', 'id': RUN_ID, 'created': '2026-09-27', 'started': now(),
               'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'template': {'path': str(args.template), 'sha256': artifacts.file_hash(args.template)},
               'request': {'path': str(req), 'sha256': artifacts.file_hash(req)},
               'timed_binary_sha256': PRIMARY_BINARY_SHA, 'configuration': request['configuration'],
               'workload': WORKLOAD, 'purpose': 'AC10 competing-parent coverage on the exact timed binary',
               'gain_claim': False, 'automatic_retry_allowed': False}
    common = ['--records', str(ROOT / 'records'), '--db', str(RAW / 'swdb.sqlite'), '--format', 'json']
    began = time.monotonic()
    with (RAW / 'execute.json').open('x') as out, (RAW / 'execute.stderr').open('x') as err:
        code = subprocess.run([sys.executable, '-m', 'swdb', 'dx100-execute', str(req), '--runs-dir', str(runs),
                               '--lane', str(args.lane), *common], cwd=ROOT, stdout=out, stderr=err,
                              timeout=BUDGET['total_seconds'] + 120).returncode
    receipt.update(execute_returncode=code, execute_host_wall_s=time.monotonic() - began)
    fresh = subprocess.run([sys.executable, '-m', 'swdb', 'get', RUN_ID + '.execute', *common], cwd=ROOT,
                           capture_output=True, text=True, timeout=180)
    record = json.loads(fresh.stdout) if fresh.returncode == 0 else {}
    checks = (record.get('correctness') or {}).get('checks') or [{}]
    coverage = checks[0].get('coverage', {})
    receipt.update(finished=now(), fresh_get_returncode=fresh.returncode,
                   outcome=record.get('outcome'), correctness=(record.get('correctness') or {}).get('state'),
                   binary_sha256=(record.get('timing') or [{}])[0].get('binary_sha256'),
                   coverage={key: coverage.get(key) for key in ('state', 'full_tiles', 'tail_tiles')},
                   competing_parent_updates={k: (coverage.get('competing_parent_updates') or {}).get(k)
                                             for k in ('state', 'count')},
                   record_sha256=artifacts.digest(record) if record else None)
    receipt['ac10_parent_case_passed'] = (code == 0 and receipt['correctness'] == 'passed'
        and receipt['binary_sha256'] == PRIMARY_BINARY_SHA
        and receipt['competing_parent_updates']['state'] == 'observed')
    with (RAW / 'receipt.json').open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if receipt['ac10_parent_case_passed'] else 1)


if __name__ == '__main__':
    main()
