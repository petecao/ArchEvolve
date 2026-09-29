#!/usr/bin/env python3
"""Re-register the A2 collision graph with an upstream (gapbs, sg64) representation. Created 2026-09-29 ET.

Root-approved T20 AC10 fix (2026-09-29). Off-lane, single-threaded, run under nice.
The retained A2 sg32 file is widened to sg64 with the repository's `widen_sg`
(counts/offsets widened; vertex IDs and neighbor bytes unchanged). One public
`register-workload` call registers both representations; registration itself
requires every representation to load the same canonical adjacency (D13). The
result must also equal the original A2 canonical hash. Fresh ID; the A2 workload
record is not superseded or changed. No retry: an existing output root refuses.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.bfs_generate_workload import widen_sg  # noqa: E402
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

A2 = 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e'
NEW = 'bfs-dx100-coverage-20260929-b1.workload'
OUT = Path('/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260929-b1')


def require(ok, why):
    if not ok:
        raise SystemExit('refused: ' + why)


def main():
    store = Store(ROOT / 'records')
    a2 = store.get(A2, 'workload')
    d = a2['definition']
    (sg32,) = d['representations']
    require(sg32['application'] == 'dx100-gapbs' and artifacts.file_hash(sg32['path']) == sg32['sha256'],
            'retained A2 sg32 representation changed')
    require(not OUT.exists(), 'output root exists; fresh ID required')
    OUT.mkdir(parents=True)
    sg64 = OUT / 'coverage.sg64'
    widen_sg(sg32['path'], sg64)
    request = {'message_version': '1.0', 'id': NEW, 'kernel': d['kernel'], 'family': d['family'],
               'generator': d['generator'], 'sources': d['sources'], 'normalization': d['normalization'],
               'representations': [
                   {'id': NEW + '.dx100', 'application': 'dx100-gapbs', 'path': sg32['path'],
                    'format': 'gapbs_sg32le', 'sha256': sg32['sha256']},
                   {'id': NEW + '.upstream', 'application': 'gapbs', 'path': str(sg64),
                    'format': 'gapbs_sg64le', 'sha256': artifacts.file_hash(sg64)}]}
    path = OUT / 'register.json'
    path.write_text(json.dumps(request, indent=2) + '\n')
    with (OUT / 'register.out.json').open('x') as out, (OUT / 'register.stderr').open('x') as err:
        code = subprocess.run([sys.executable, '-m', 'swdb', 'register-workload', str(path), '--records',
                               str(ROOT / 'records'), '--db', str(OUT / 'swdb.sqlite'), '--format', 'json'],
                              cwd=ROOT, stdout=out, stderr=err, timeout=900).returncode
    require(code == 0, f'register-workload exited {code}')
    record = json.loads((OUT / 'register.out.json').read_text())
    rd = record['definition']
    fresh = subprocess.run([sys.executable, '-m', 'swdb', 'get', record['id'], '--records', str(ROOT / 'records'),
                            '--db', str(OUT / 'fresh.sqlite'), '--format', 'json'],
                           cwd=ROOT, capture_output=True, text=True, timeout=300)
    receipt = {'format': 'swdb.bfs.workload-reregistration.v1', 'created': '2026-09-29', 'workload': record['id'],
               'source_workload': A2, 'request': {'path': str(path), 'sha256': artifacts.file_hash(path)},
               'canonical_sha256': rd['canonical_sha256'], 'a2_canonical_sha256': d['canonical_sha256'],
               'canonical_equal_to_a2': rd['canonical_sha256'] == d['canonical_sha256'],
               'representations': [{k: r.get(k) for k in ('id', 'application', 'format', 'path', 'sha256', 'bytes',
                                                            'canonical_sha256', 'adjacency_verified')}
                                   for r in rd['representations']],
               'realized_equal_to_a2': rd['realized'] == d['realized'], 'sources': rd['sources'],
               'fresh_get_returncode': fresh.returncode,
               'fresh_get_matches': fresh.returncode == 0 and json.loads(fresh.stdout).get('identity_sha256')
               == record.get('identity_sha256'),
               'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    receipt['d13_equivalent'] = (receipt['canonical_equal_to_a2'] and receipt['realized_equal_to_a2']
                                 and all(r['adjacency_verified'] and r['canonical_sha256'] == d['canonical_sha256']
                                         for r in receipt['representations']))
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=1))
    raise SystemExit(0 if receipt['d13_equivalent'] and receipt['fresh_get_matches'] else 1)


if __name__ == '__main__':
    main()
