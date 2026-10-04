#!/usr/bin/env python3
"""T17/T20 protocol version 2: source [0] per family only. Created 2026-09-28 ET.

Copies each frozen v1 settings map exactly and changes only the workload
identities to the source-0 registrations of the same graph bytes, plus a
recorded calibration rationale. User-approved scope change (option A, relayed by
root 2026-09-28 18:40 ET), made before any candidate assessment.
"""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

S = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25'
store = Store(ROOT / 'records')
V1 = {'t17': 'bfs-t17-controlled-simulator-20260928.feee73bcca275c56',
      't20': 'bfs-t20-controlled-simulator-20260928.b504c267f86b65b5'}
WORKLOADS = {'bfs-20260925-uniform18.cd2169a5c421baf7': 'bfs-20260928-uniform18-s0.8c7e69dfa516e53c',
             'bfs-20260925-kronecker18.48de8267ac2098d5': 'bfs-20260928-kronecker18-s0.cf4283236c5cb50c'}
for old, new in WORKLOADS.items():
    a, b = store.get(old, 'workload')['definition'], store.get(new, 'workload')['definition']
    assert b['sources'] == [0] and a['sources'][0] == 0 and a['canonical_sha256'] == b['canonical_sha256']
    assert [r['sha256'] for r in a['representations']] == [r['sha256'] for r in b['representations']]
for route, protocol in V1.items():
    frozen = store.get(protocol, 'protocol')
    settings = copy.deepcopy(frozen['settings'])
    settings['workloads'] = [WORKLOADS[w] for w in settings['workloads']]
    settings['calibration']['version_2_change'] = {
        'date': '2026-09-28', 'supersedes': protocol,
        'change': 'Ordered sources reduced from [0, 1234, 7777] to [0] per family (same graph bytes, canonical adjacency and representations); every other setting is identical to version 1.',
        'rationale': ('Deterministic simulator (R11: identical modeled statistics across 32 compared executions); the '
                      'source dimension is reduced to fit the schedule (user-approved option A). The change precedes any '
                      'candidate assessment: version 1 collected only baseline pairs (routes a1, interrupted and retained).'),
        'invalidated': 'No comparison was bound to version 1.',
        'retained_attempt': 'bfs-t17-t20-routes-simulator-batch-20260928-a1 (observations/t17-t20-routes-a1-closure-20260928.json)'}
    request = {'message_version': '1.0', 'id': frozen['requested_id'], 'version': 2, 'supersedes': protocol,
               'settings': settings}
    path = S / 'requests' / f'bfs-{route}-controlled-simulator-freeze-20260928-a2.json'
    path.write_text(json.dumps(request, indent=1) + '\n')
    print(path, artifacts.file_hash(path))
