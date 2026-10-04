#!/usr/bin/env python3
"""T17/T20 controlled-simulator series requests (data only). Created 2026-09-28 ET.

Four series per route (baseline/candidate x uniform18/kronecker18), one replay per
ordered source under the frozen R11 determinism basis, primary + diagnostic per
cell. Bounds follow the measured T15 b3 costs (bound_audit_20260927) at >= 2x.
These requests allocate no lane or clock; root assigns lanes before dispatch.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

S = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25'
store = Store(ROOT / 'records')
PROTOCOLS = {'t17': 'bfs-t17-controlled-simulator-20260928.feee73bcca275c56',
             't20': 'bfs-t20-controlled-simulator-20260928.b504c267f86b65b5'}
FAMILIES = {'uniform18': 'bfs-20260925-uniform18.cd2169a5c421baf7',
            'kronecker18': 'bfs-20260925-kronecker18.48de8267ac2098d5'}
CONFIG = {'baseline': {'mode': 'BASE', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384},
          'candidate': {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384}}
BOUNDS = {'total_seconds': 43200, 'checkpoint_seconds': 3600, 'run_seconds': 7200, 'diagnostic_seconds': 10800,
          'profile_seconds': 2400, 'package_seconds': 2400, 'memory_gib': 48, 'storage_gib': 10,
          'batch_storage_gib': 30, 'verification_ticks': 10**14}
BASIS = ('T15 b3 measured per execution: primary simulation 1,675-2,040 s, diagnostic 2,128-2,511 s, checkpoint '
         '~77 s, correctness ~380 s; profile 733-908 s; package 683-862 s; ~2.3 GB retained per pair. One replay '
         'x three sources per series needs ~5.5 h host time plus gem5-slot waits; 43,200 s is ~2x.')


def row(route, role, family, protocol):
    settings = store.get(protocol, 'protocol')['settings']['route']
    builds = settings['builds']
    primary = builds[f'{role}_primary']['id']; diagnostic = builds[f'{role}_diagnostic']['id']
    candidate = store.get(primary, 'evaluation')['candidate']
    return {'id': f'bfs-{route}-routes-20260928-a1.{role}.{family}', 'route': route, 'role': role,
            'family': family, 'workload': FAMILIES[family], 'candidate': candidate,
            'primary_build': {'id': primary, 'sha256': artifacts.digest(store.get(primary, 'evaluation'))},
            'diagnostic_build': {'id': diagnostic, 'sha256': artifacts.digest(store.get(diagnostic, 'evaluation'))},
            'accelerated': role == 'candidate', 'configuration': CONFIG[role],
            'protocol': protocol, 'protocol_role': role, 'repetitions': 1,
            'series_arguments': ['--id', f'bfs-{route}-routes-20260928-a1.{role}.{family}', '--candidate', candidate,
                '--workload', FAMILIES[family], '--build-evaluation', 'bfs-dx100-build-20260925-a2',
                '--primary-build', primary, '--diagnostic-build', diagnostic,
                '--protocol', protocol, '--protocol-role', role, '--verifier', 'dx100.bfs.verifier.v2',
                '--trace-transport', 'gem5-gzip.v1', '--require-capacity',
                *[x for key, value in BOUNDS.items() for x in ('--' + key.replace('_', '-'), str(value))]]
                + (['--accelerated'] if role == 'candidate' else [])}


for route, protocol in PROTOCOLS.items():
    request = {'format': 'swdb.bfs.controlled-simulator-series-request.v1', 'created': '2026-09-28',
               'id': f'bfs-{route}-routes-20260928-a1', 'protocol': protocol,
               'protocol_sha256': artifacts.digest(store.get(protocol, 'protocol')),
               'bounds': BOUNDS, 'bounds_basis': BASIS,
               'companion_case': ('Run bfs.dx100.competing-parent-case.v1 on the candidate primary build before any gain '
                                  'claim (see protocol settings.correctness.companion_cases).'),
               'series': [row(route, role, family, protocol) for family in FAMILIES for role in ('baseline', 'candidate')],
               'dispatch_allowed': False, 'lane': None, 'gain_claim': False}
    path = S / 'requests' / f'bfs-{route}-routes-series-20260928-a1.json'
    path.write_text(json.dumps(request, indent=1) + '\n')
    print(path, artifacts.file_hash(path))
