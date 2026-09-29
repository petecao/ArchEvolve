#!/usr/bin/env python3
"""Build the T17/T20 routes batch plan from the frozen protocols. Created 2026-09-28 ET."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts  # noqa: E402
from swdb.store import Store  # noqa: E402

S = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25'
store = Store(ROOT / 'records')
pilot = json.loads((S / 'requests/bfs-t15-pilot-simulator-batch-20260927-b3.json').read_text())
PID = 'bfs-t17-t20-routes-simulator-batch-20260928-a3'
GIB = 1024**3
keep = ('format', 'automatic_retry_allowed', 'gain_claim', 'model_build', 'target', 'verifier', 'threads',
        'warmups', 'verification_ticks', 'profitability', 'historical_failure', 'required_a3', 'required_coverage',
        'historical_coverage_failure', 'supervision', 'trace_transport', 'raw_root')
plan = {key: pilot[key] for key in keep}
plan.update(created='2026-09-28', updated='2026-09-28', id=PID, role='candidate_route_collection',
    roi='bfs.complete_call.v1', repetitions=1, lane={'node': 0, 'assigned_by': 'root 2026-09-28'},
    clock='Fresh allocation: absolute end = admission preparation + 172,800 s; latest start = preparation + 3,600 s.',
    budget_authority=('User-approved autonomous T17/T20 route collection (root 2026-09-28): eight frozen series in one '
                      'node0 lane job with one gem5 slot, plus each candidate AC10 companion case.'),
    allocation={'policy': 'routes_incremental_allocation.a3', 'total_seconds': 86400,
        'partition_seconds': {'preparation': 3600, 'series': 79200, 'finalization_and_companions': 3570, 'scientific_cleanup': 30},
        'storage_gib': 30, 'overhead_reserve_gib': 4, 'shared_series_gib': 26, 'per_series_cap_gib': 10,
        'free_space_required_at_admission_gib': 60,
        'notes': ['Four drivers (route x family) each run baseline then candidate; per_series_cap_gib caps each driver root.',
                  'Basis: T15 b3 retained 27.49 GB for 24 executions (about 1.15 GB each); 48 executions need about 51 GiB.']},
    concurrency={'mode': 'family_drivers_in_one_lane_job.v1', 'drivers': 4, 'gem5_slots': 1,
                 'basis': 'One gem5 (16-GB guest) holds 29.5-34.2 GiB sampled RSS; the 52-GiB lane-tree cap admits one.',
                 'lane_tree_sampled_rss_gib': 52},
    bounds={'batch_seconds': 86400, 'series_seconds': 43200, 'cleanup_seconds': 30,
        'checkpoint_seconds': 3600, 'run_seconds': 7200, 'diagnostic_seconds': 10800,
        'profile_seconds': 2400, 'package_seconds': 2400, 'aggregate_seconds': 7200,
        'memory_gib': 48, 'storage_gib': 10, 'batch_storage_gib': 30, 'raw_reserve_gib': 30, 'build_reserve_gib': 10,
        'monitor_interval_seconds': 5, 'sampled_tree_memory_gib': 52, 'maximum_telemetry_gap_seconds': 30},
    bound_basis=('T15 b3 measured: primary simulation 1,675-2,040 s, diagnostic 2,128-2,511 s, profile 733-908 s, '
                 'package 683-862 s, trace re-validation about 350-415 s per primary (aggregate re-validates three '
                 'primaries: about 21 min; 7,200 s is >= 5x). 48 executions at about 40 min of gem5 each serialize to '
                 'about 32 h; each driver waits for the shared slot, so 72,000 s per series and 172,800 s overall.'),
    accounting={'preparation': [], 'preparation_reservation': {'id': 'bfs-t17-t20-routes-preparation-20260928-a3',
        'elapsed_seconds': 3600, 'raw_bytes': 4 * GIB},
        'excluded': 'T15 pilot attempts, T17/T20 builds and earlier failures remain charged in their own records.'})
protocols = {'t17': 'bfs-t17-controlled-simulator-20260928.952dead4468b86d7',
             't20': 'bfs-t20-controlled-simulator-20260928.35ade0da7e50e931'}
WORKLOADS = {'bfs-20260925-uniform18.cd2169a5c421baf7': 'bfs-20260928-uniform18-s0.8c7e69dfa516e53c',
             'bfs-20260925-kronecker18.48de8267ac2098d5': 'bfs-20260928-kronecker18-s0.cf4283236c5cb50c'}
plan['protocol_requests'] = {key: {'path': f'.scratch/bfs-rewrite-evaluation-2026-09-25/requests/bfs-{key}-controlled-simulator-freeze-20260928-a2.json',
                                   'sha256': artifacts.file_hash(S / f'requests/bfs-{key}-controlled-simulator-freeze-20260928-a2.json')}
                             for key in protocols}
rows, records = [], dict(pilot['record_sha256'])
for route in protocols:
    request = json.loads((S / f'requests/bfs-{route}-routes-series-20260928-a1.json').read_text())
    for item in request['series']:
        family = item['family']
        item = dict(item, id=item['id'].replace('20260928-a1', '20260928-a3'), workload=WORKLOADS[item['workload']])
        rows.append({'id': item['id'], 'group': f'{route}.{family}', 'candidate': item['candidate'],
                     'primary_build': item['primary_build']['id'], 'diagnostic_build': item['diagnostic_build']['id'],
                     'workload': item['workload'], 'sources': [0], 'configuration': item['configuration'],
                     'accelerated': item['accelerated'], 'protocol_key': route, 'protocol_role': item['protocol_role']})
        candidate = store.get(item['candidate'])
        for rid in (item['candidate'], candidate['source_snapshot'], candidate['implementation'],
                    item['primary_build']['id'], item['diagnostic_build']['id'], item['workload']):
            records[rid] = artifacts.digest(store.get(rid))
    records[protocols[route]] = artifacts.digest(store.get(protocols[route], 'protocol'))
# Driver order: each group runs its baseline before its candidate.
rows.sort(key=lambda row: (row['group'], row['protocol_role'] != 'baseline'))
plan['series'] = rows
plan['scope_change'] = ('2026-09-28 option A (user-approved): v2 protocols with source [0] per family; routes a1 '
                        'retained as interrupted (observations/t17-t20-routes-a1-closure-20260928.json).')
plan['relaunch'] = ('a3 replaces routes a2, stopped 2026-09-28 after one driver self-terminated on a transient procfs '
                    'reparenting race in lane-tree telemetry; the batch now retries that race (race_tolerant). a2 retained.')
plan['bound_basis'] = ('Scalar complete-call pairs measured in routes a1: primary ~2,060 s, diagnostic ~3,240 s of '
                       'gem5 slot time; author MAA pairs ~4,700 s. Eight pairs serialize to ~12 h on one slot; '
                       '43,200 s per series and 86,400 s overall.')
plan['record_sha256'] = dict(sorted(records.items()))
path = S / 'requests' / (PID + '.json')
path.write_text(json.dumps(plan, indent=1) + '\n')
print(path, artifacts.digest(json.loads(path.read_text())))
