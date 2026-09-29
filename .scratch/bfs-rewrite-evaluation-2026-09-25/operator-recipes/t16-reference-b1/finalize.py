#!/usr/bin/env python3
"""Write the T16 b1 protocol requests and batch plan. Created 2026-09-27 ET.

Run on the Mac, in the repository, after the R12 probe and the T15 replay check
(R11). ``requests`` writes the two freeze requests; ``plan`` writes the batch plan
after both protocols are frozen through the public ``swdb freeze-protocol`` CLI.
Scientific settings are the seal-runtime policies except: replay count (R11),
the verifier runtime of this checkout, and the opt-in atomic verifier continuation
(R12). Targets, graph, source, builds, ROI, correctness and profitability are unchanged.

Updated 2026-09-28 ET (low storage): ``requests --low-storage`` writes version-2
requests that supersede the frozen b1 protocols and change only the candidate
debug flags to MAATrace (unit Start/End lines, which prove accelerator execution);
``plan`` then pins the MAATrace-only trace treatment and the smaller storage.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, yamlio  # noqa: E402
from swdb.dx100_witness import POST_ROI_CPU_TREATMENT  # noqa: E402
from swdb.store import Store  # noqa: E402

REQUESTS = ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/requests'
SOURCES = {'artifact': 'author-reference-seal-runtime-freeze-20260927-a1.yaml',
           'control': 'author-matched-control-seal-runtime-freeze-20260927-a1.yaml'}
NAMES = {'artifact': 'author-reference-t16-b1-20260927', 'control': 'author-matched-control-t16-b1-20260927'}
PLAN_ID = 'bfs-t16-reference-simulator-batch-20260927-b1'


def request_path(key, low_storage=False, version=None):
    version = version or (2 if low_storage else 1)
    return REQUESTS/f'{NAMES[key]}-freeze{"" if version == 1 else "-v" + str(version)}.yaml'


def v3_requests():
    """2026-09-28 B+C replan: version 3 drops only the region correspondence.

    The scalar roles no longer run diagnostic executions, so no scalar region
    package exists; a diagnostic region comparison cannot be formed and the policy
    must not require one. Primary timing, correctness, coverage, instrumentation,
    replay grid and profitability are unchanged from version 2.
    """
    store = Store(ROOT/'records')
    for key in SOURCES:
        original = yamlio.load(request_path(key, version=2))
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == original['id']
                  and row.data['settings'] == original['settings']]
        assert len(frozen) == 1, 'the version-2 protocol must be frozen exactly once'
        settings = copy.deepcopy(original['settings'])
        settings['region_pairs'] = []
        value = {'message_version': '1.0', 'id': original['id'], 'version': 3, 'supersedes': frozen[0]['id'],
                 'settings': settings}
        header = ('# Created 2026-09-28 (Eastern Time): T16 version 3 for the user-approved B+C replan. Only change: '
                  'region_pairs removed because the scalar roles run primary executions only (no diagnostic, '
                  'region profile or package); scalar evidence is primary timing, sealed statistics, verifier and '
                  'memory statistics. Supersedes ' + frozen[0]['id'] + '.\n')
        request_path(key, version=3).write_text(header + yamlio.dumps(value))
        print(request_path(key, version=3))


SPLIT = {'m': ('maa',), 's1': ('artifact.scalar',), 's2': ('control.scalar',)}


def v4_requests():
    """2026-09-29: version 4 drops only the post-ROI CPU switch (O3 verification).

    At uniform22 the MAA primary's m5.switchCpus drain never completed (T16 M c1,
    01:50 ET). gem5 cannot resume a partially drained system, so no safe fallback
    exists; the verifier stays on the timed O3 CPUs. The determinism evidence is
    rebound as {path, sha256}, as new freezes require. Nothing else changes.
    """
    store = Store(ROOT/'records')
    for key in SOURCES:
        original = yamlio.load(request_path(key, version=3))
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == original['id']
                  and row.data['settings'] == original['settings']]
        assert len(frozen) == 1, 'the version-3 protocol must be frozen exactly once'
        settings = copy.deepcopy(original['settings'])
        for role in ('baseline', 'candidate'):
            settings['instrumentation'][role].pop('post_roi_cpu')
        evidence = settings['sampling']['determinism']['evidence']
        path = evidence if isinstance(evidence, str) else evidence['path']
        settings['sampling']['determinism']['evidence'] = {'path': path, 'sha256': artifacts.file_hash(ROOT/path)}
        value = {'message_version': '1.0', 'id': original['id'], 'version': 4, 'supersedes': frozen[0]['id'],
                 'settings': settings}
        header = ('# Created 2026-09-29 (Eastern Time): T16 version 4. Only change: the opt-in post-ROI '
                  'AtomicSimpleCPU switch is removed (verification stays on the timed O3 CPUs) because its gem5 '
                  'drain never completed at uniform22 (M c1, 2026-09-29 01:50 ET) and gem5 cannot resume a '
                  'partial drain; determinism evidence rebound as {path, sha256}. Supersedes ' + frozen[0]['id'] + '.\n')
        request_path(key, version=4).write_text(header + yamlio.dumps(value))
        print(request_path(key, version=4))


def split_plans_c2():
    """Fresh c2 single-series plans on version 4 with O3-verification bounds."""
    store = Store(ROOT/'records')
    protocols = {}
    for key in SOURCES:
        path = request_path(key, version=4); request = yamlio.load(path)
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == request['id']
                  and row.data['settings'] == request['settings']]
        assert len(frozen) == 1, 'freeze the version-4 request exactly once first'
        protocols[key] = {'path': str(path.relative_to(ROOT)), 'sha256': artifacts.file_hash(path),
                          'frozen_id': frozen[0]['id']}
    for job, names in SPLIT.items():
        plan = build_split(protocols, job, names, generation='c2')
        path = REQUESTS/f"{plan['id']}.json"
        path.write_text(json.dumps(plan, indent=1) + '\n')
        print(job, path.name, artifacts.digest(plan))


def split_plans():
    """Three single-series plans on the version-3 protocols (fresh IDs, low storage)."""
    store = Store(ROOT/'records')
    protocols = {}
    for key in SOURCES:
        path = request_path(key, version=3); request = yamlio.load(path)
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == request['id']
                  and row.data['settings'] == request['settings']]
        assert len(frozen) == 1, 'freeze the version-3 request exactly once first'
        protocols[key] = {'path': str(path.relative_to(ROOT)), 'sha256': artifacts.file_hash(path),
                          'frozen_id': frozen[0]['id']}
    for job, names in SPLIT.items():
        plan = build_split(protocols, job, names)
        path = REQUESTS/f"{plan['id']}.json"
        path.write_text(json.dumps(plan, indent=1) + '\n')
        print(job, path.name, artifacts.digest(plan))


def build_split(protocols, job, names, generation='c1'):
    atomic = generation == 'c1'
    base = build_plan(protocols, 1, atomic, low_storage=True)
    date = '20260928' if generation == 'c1' else '20260929'
    plan_id = f'bfs-t16-reference-{job}-simulator-batch-{date}-{generation}'
    if not atomic:
        # 2026-09-29: O3 verification. MAA uniform18 O3 verification took 1,887 s
        # (x16 about 30 ks); run 72,000 s and diagnostic 86,400 s (7,200 checkpoint
        # + 79,170 simulation) are the public ceilings for author binaries.
        base['bounds'].update(run_seconds=72000, diagnostic_seconds=86400, sampled_tree_memory_gib=56, memory_gib=54)
        base['bound_changes'].update(
            run_seconds='43,200 -> 72,000 (c2): O3 post-ROI verification, estimated about 30 ks at uniform22',
            diagnostic_seconds='79,200 -> 86,400 (c2): O3 post-ROI verification after the diagnostic ROI',
            sampled_tree_memory_gib=('52 -> 56 (c2, root 2026-09-29): M c1 MAA primary reached 39.1 GiB at its ROI seal '
                                     '(+1.2 GiB/h during the ROI, +3.2 GiB at the statistics dump); an 8-h O3 verifier could '
                                     'add about 10 GiB (about 49 GiB), too close to 52. One single-slot uniform22 gem5 plus the '
                                     'driver fits one NUMA node (about 62 GB); 56 GiB keeps about 6 GB of headroom.'),
            memory_gib='48 -> 54 (c2): per-execution process-group budget below the 56-GiB lane-tree cap')
    rows = []
    for row in base['series']:
        name = row['id'][len(PLAN_ID) + 1:]
        if name in names:
            row = {**row, 'id': f'{plan_id}.{name}'}
            if row['accelerated'] is False:
                row['primary_only'] = True
            rows.append(row)
    bounds = base['bounds']
    primary = min(86400, bounds['checkpoint_seconds'] + bounds['run_seconds'] + 60)
    if job == 'm':
        series_seconds = (primary + bounds['diagnostic_seconds'] + bounds['profile_seconds']
                          + bounds['package_seconds'] + 4 * bounds['aggregate_seconds'])
        storage = 12
    else:
        series_seconds = primary + 2 * bounds['aggregate_seconds']
        storage = 8
    total = 3600 + series_seconds + 3570 + 30
    base.update(id=plan_id, series=rows, updated='2026-09-28' if atomic else '2026-09-29',
        lane={'nodes': [0, 1], 'assigned_by': 'root 2026-09-28: M on node0 after the MemAcc cell; S1 on node1 after '
                                              'routes a2; S2 on node0 after M'},
        budget_authority=('User-approved B+C replan (root 2026-09-28): T16 v3 as three single-series lane jobs. The '
                          'interrupted b1 run (user-confirmed stop 18:53:29 ET) and every earlier T16 charge stay '
                          'retained separately; no failed or interrupted ID is resumed; no automatic retry.'),
        concurrency={**base['concurrency'], 'drivers': 1})
    base['allocation'].update(total_seconds=total,
        partition_seconds={'preparation': 3600, 'series': series_seconds, 'finalization': 3570, 'scientific_cleanup': 30},
        storage_gib=storage, shared_series_gib=storage - 4, per_series_cap_gib=storage - 4,
        free_space_required_at_admission_gib=storage + base['bounds']['raw_reserve_gib'])
    bounds.update(batch_seconds=total, series_seconds=series_seconds, batch_storage_gib=storage)
    base['accounting']['preparation_reservation']['id'] = plan_id.replace('-simulator-batch-', '-preparation-')
    return base


def low_storage_requests():
    """Version 2 of each frozen b1 request: candidate debug flags MAATrace only."""
    store = Store(ROOT/'records')
    for key in SOURCES:
        original = yamlio.load(request_path(key))
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == original['id']
                  and row.data['settings'] == original['settings']]
        assert len(frozen) == 1, 'the version-1 protocol must be frozen exactly once'
        settings = copy.deepcopy(original['settings'])
        assert settings['instrumentation']['baseline']['debug_flags'] == 'MAATrace'
        settings['instrumentation']['candidate']['debug_flags'] = 'MAATrace'
        value = {'message_version': '1.0', 'id': original['id'], 'version': 2, 'supersedes': frozen[0]['id'],
                 'settings': settings}
        header = ('# Created 2026-09-28 (Eastern Time): T16 b1 low-storage version 2; only the candidate debug flags '
                  'change (MAATrace-only unit Start/End trace). Supersedes ' + frozen[0]['id'] + '.\n')
        request_path(key, True).write_text(header + yamlio.dumps(value))
        print(request_path(key, True))


def runtime():
    return {'driver_sha256': artifacts.file_hash(ROOT/'scripts/dx100_verify.py'),
            'parser_sha256': artifacts.file_hash(ROOT/'swdb/dx100_witness.py'),
            'observer_sha256': artifacts.file_hash(ROOT/'scripts/dx100_host_memory.py')}


def write_requests(repetitions, atomic, evidence=None):
    for key, name in SOURCES.items():
        original = yamlio.load(REQUESTS/name)
        settings = copy.deepcopy(original['settings'])
        settings['sampling']['repetitions'] = repetitions
        if repetitions == 1:
            # R11: one replay only with the named deterministic-replay evidence.
            settings['sampling']['determinism'] = {'basis': 'deterministic_simulator_replay.v1', 'evidence': evidence}
        for role in ('baseline', 'candidate'):
            settings['instrumentation'][role]['verifier_runtime'] = runtime()
            if atomic:
                settings['instrumentation'][role]['post_roi_cpu'] = dict(POST_ROI_CPU_TREATMENT)
        value = {'message_version': '1.0', 'id': NAMES[key], 'version': 1, 'settings': settings}
        header = (f'# Created 2026-09-27 (Eastern Time) for T16 b1 from {name}: replays {repetitions} (R11), '
                  f'verifier runtime of this checkout{", atomic post-ROI verifier continuation (R12)" if atomic else ""}.\n')
        request_path(key).write_text(header + yamlio.dumps(value))
        print(request_path(key))


def write_plan():
    store = Store(ROOT/'records')
    protocols, repetitions, atomic = {}, set(), set()
    low_storage = all(request_path(key, True).is_file() for key in SOURCES)
    for key in SOURCES:
        path = request_path(key, low_storage); request = yamlio.load(path)
        frozen = [row.data for row in store.of_kind('protocol') if row.data.get('requested_id') == request['id']
                  and row.data['settings'] == request['settings']]
        assert len(frozen) == 1, 'freeze the request exactly once first'
        protocols[key] = {'path': str(path.relative_to(ROOT)), 'sha256': artifacts.file_hash(path),
                          'frozen_id': frozen[0]['id']}
        repetitions.add(request['settings']['sampling']['repetitions'])
        atomic.add('post_roi_cpu' in request['settings']['instrumentation']['candidate'])
    assert len(repetitions) == len(atomic) == 1
    plan = build_plan(protocols, repetitions.pop(), atomic.pop(), low_storage)
    path = REQUESTS/f'{PLAN_ID}.json'
    path.write_text(json.dumps(plan, indent=1) + '\n')
    print(path, artifacts.digest(plan))


def build_plan(protocols, reps, atomic, low_storage=False):
    """The fixed T16 b1 plan for already frozen protocol references."""
    old = json.loads((REQUESTS/'bfs-t16-protocol-recovery-simulator-batch-20260927-a1.json').read_text())
    pilot = json.loads((REQUESTS/'bfs-t15-pilot-simulator-batch-20260927-b1.json').read_text())
    executions = 3 * 2 * reps  # three series, primary + diagnostic per replay
    run, diagnostic = 43200, 79200  # diagnostic: 7,200 checkpoint + 71,970 simulation + 30
    # Every execution's full public envelope, serialized behind one gem5 slot,
    # plus this series' own profile and package calls (they do not hold the slot)
    # and, for the MAA series with its shared protocol, two aggregate calls and
    # two chain readbacks, each bounded by aggregate_seconds.
    primary_envelope, diagnostic_envelope = min(86400, 3600 + run + 60), diagnostic
    profile, package, aggregate = 36000, 36000, 14400
    if low_storage:
        # MAATrace-only traces are about 1/1000 of the full stream, so trace
        # rereads no longer dominate; the remaining work is log/statistics parsing.
        profile, package, aggregate = 7200, 7200, 3600
    series_seconds = ((executions // 2) * (primary_envelope + diagnostic_envelope)
                      + reps * (profile + package) + 4 * aggregate)
    plan = {key: pilot[key] for key in ('format', 'automatic_retry_allowed', 'gain_claim', 'model_build', 'target',
            'verifier', 'roi', 'threads', 'warmups', 'verification_ticks', 'profitability', 'historical_failure',
            'required_a3', 'required_coverage', 'historical_coverage_failure', 'supervision', 'trace_transport')}
    plan.update(created='2026-09-27', updated='2026-09-27', id=PLAN_ID, role='author_reference_and_matched_control',
        repetitions=reps, raw_root='/data/yanruj/EvolveSWDB_runs',
        record_sha256=old['record_sha256'], protocol_requests=protocols,
        lane={'nodes': [0, 1], 'assigned_by': 'root 2026-09-27: node0 after T15 releases it, or node1 if it frees first'},
        clock='Fresh incremental allocation: absolute end = admission preparation + allocation.total_seconds; latest start = preparation + 3,600 s.',
        budget_authority=('Root decisions R10-R12 (2026-09-27) on the resumed plan: one MAA execution set bound to both '
                          'protocols, one replay per source when T15 replays are deterministic, and an atomic post-ROI '
                          'verifier continuation proven on kron14. Historical T16 charges (24,325 s / 11,011,186,688 bytes, '
                          'including the stopped protocol-recovery a1 run and its 0.226 s dead-owner reservation under R1) '
                          'remain retained separately. No resume of any failed ID, no automatic retry.'),
        allocation={'policy': 't16_incremental_allocation.v1',
                    'total_seconds': 3600 + series_seconds + 3570 + 30,
                    'partition_seconds': {'preparation': 3600, 'series': series_seconds,
                                          'finalization': 3570, 'scientific_cleanup': 30},
                    'storage_gib': 64 if reps == 1 else 124, 'overhead_reserve_gib': 4,
                    'shared_series_gib': 60 if reps == 1 else 120, 'per_series_cap_gib': 50 if reps == 1 else 98,
                    # Root 2026-09-28 11:15 ET: /data had 94 GiB free with T17/T20 queued first;
                    # the raw reserve may drop from 30 to 20 GiB for T16 (recorded below).
                    'free_space_required_at_admission_gib': (64 if reps == 1 else 124) + 20,
                    'reserve_change': 'raw_reserve_gib 30 -> 20 GiB, root-approved 2026-09-28 11:15 ET because '
                                      '/data had about 94 GiB free with T17/T20 queued before T16',
                    'notes': ['The three series run concurrently (R3) behind one gem5 slot; each series allowance is a '
                              'ceiling inside the same envelope, sized as every planned execution at its run bound.',
                              'Each series driver has its own 30-second shared cleanup ledger (three drivers).',
                              'Storage: MAA uniform22 trace about 19.3 GiB per execution (T15 uniform18 1.30 GB x 16); '
                              'scalar traces near zero; no trace is deleted in flight.']},
        concurrency={'mode': 'series_drivers_in_one_lane_job.v1', 'drivers': 3, 'gem5_slots': 1,
                     'basis': 'Measured 2026-09-27: the uniform22 artifact.scalar gem5 held about 30.7 GB RSS for 8,695 s; '
                              'the 52-GiB lane-tree sampled cap admits one simulator.',
                     'lane_tree_sampled_rss_gib': 52},
        bounds={'batch_seconds': 3600 + series_seconds + 3570 + 30, 'series_seconds': series_seconds,
                'cleanup_seconds': 30, 'checkpoint_seconds': 3600, 'run_seconds': run,
                'diagnostic_seconds': diagnostic, 'profile_seconds': profile, 'package_seconds': package, 'aggregate_seconds': aggregate, 'memory_gib': 48, 'storage_gib': 24,
                'batch_storage_gib': 64 if reps == 1 else 124, 'raw_reserve_gib': 20, 'build_reserve_gib': 10,
                'monitor_interval_seconds': 5, 'sampled_tree_memory_gib': 52, 'maximum_telemetry_gap_seconds': 30},
        bound_changes={
            'run_seconds': 'raised 14,400 -> 43,200: uniform22 scalar ROI measured > 10,700 s and estimated 15,000-30,000 s '
                           '(0.219 simulated s in <= 8,100 host s; about 0.5 simulated s remained); bound only',
            'diagnostic_seconds': 'raised 600 -> 79,200: T15 diagnostics took 1.4-1.5x the primary ROI host time (region markers); 7,200 s is its checkpoint bound, '
                                  'leaving 71,970 s for simulation; bound only',
            'storage_gib': 'raised 15 -> 24: MAA uniform22 debug trace estimated 19.3 GiB; bound only',
            'profile_seconds': 'raised -> 36,000: T15 b2 measured dx100-profile 900 s for uniform18 (17.8-GB decoded traces); '
                               'uniform22 traces are about 16x larger (about 14,400 s); 2.5x margin; bound only',
            'package_seconds': 'new 36,000: profile-package re-validates both full traces (T15 about 815 s for uniform18, '
                               'about 13,000 s scaled to uniform22); 2.8x margin; bound only',
            'aggregate_seconds': 'new 14,400 (default 180): aggregation and chain readback re-validate each primary trace; '
                                 'T15 scale-18 aggregation took about 21 min for its primaries (about 3.5 min each), '
                                 'about 1 h for one uniform22 MAA primary; 4x margin; bound only'},
        accounting={'preparation': [], 'preparation_reservation': {
            'id': 'bfs-t16-reference-preparation-20260927-b1', 'elapsed_seconds': 3600, 'raw_bytes': 4294967296},
            'excluded': 'All earlier T16 attempts, proofs and failures remain charged in their own records.'},
        series=[])
    if atomic:
        plan['post_roi_cpu'] = 'AtomicSimpleCPU'
    if low_storage:
        storage, per_execution, per_series, reserve = 16, 4, 8, 10
        plan['trace_flags'] = 'MAATrace'
        plan['allocation'].update(storage_gib=storage, shared_series_gib=storage - 4, per_series_cap_gib=per_series,
            free_space_required_at_admission_gib=storage + reserve,
            reserve_change='raw_reserve_gib 30 -> 10 GiB, root-approved 2026-09-28 (low-storage variant; '
                           '/data expected at 35-50 GiB free after T17/T20)',
            notes=plan['allocation']['notes'][:2] + [
                'Low storage (2026-09-28): accelerated executions record only the MAATrace unit Start/End '
                'trace (verification.coverage false). Measured on T15 b3 uniform18: MAATrace lines are a '
                'negligible share of the full stream; scalar traces are empty (20 bytes). Per execution the '
                'retained raw output is dominated by its uniform22 checkpoint (about 0.52 GB).',
                'Tile-size and indirect-store (competing-parent) observations are unobserved by design; '
                'accelerator execution (the frozen required case) stays observed. No trace is deleted.'])
        plan['bounds'].update(storage_gib=per_execution, batch_storage_gib=storage, raw_reserve_gib=reserve)
        plan['bound_changes'].update(
            storage_gib='24 -> 4 in the low-storage variant: checkpoint about 0.52 GB plus MAATrace-only trace and logs',
            profile_seconds='36,000 -> 7,200 in the low-storage variant (no full trace to reread)',
            package_seconds='36,000 -> 7,200 in the low-storage variant (no full trace to reread)',
            aggregate_seconds='14,400 -> 3,600 in the low-storage variant (no full trace to reread)')
    for name, key, role, scalar, config in (
            ('artifact.scalar', 'artifact', 'baseline', True, {'mode': 'BASE', 'l3_size_mb': 10, 'l3_assoc': 20}),
            ('control.scalar', 'control', 'baseline', True, {'mode': 'BASE', 'l3_size_mb': 8, 'l3_assoc': 16}),
            ('maa', 'artifact', 'candidate', False, {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16})):
        kind = 'scalar' if scalar else 'maa'
        row = {'id': f'{PLAN_ID}.{name}', 'candidate': f'bfs-author-{kind}-compile-20260925-a1.candidate',
               'diagnostic_build': f'bfs-author-{kind}-compile-20260925-a1.diagnostic.build',
               'workload': 'bfs-20260925-uniform22.f23b09bb0c0601b5', 'sources': [2796003],
               'configuration': {**config, 'tile_elements': 16384}, 'accelerated': not scalar,
               'protocol_key': key, 'protocol_role': role}
        if not scalar:
            row['shared_protocol_keys'] = ['control']
        plan['series'].append(row)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('requests', 'plan', 'v3-requests', 'split-plans', 'v4-requests', 'split-plans-c2'))
    parser.add_argument('--repetitions', type=int, choices=(1, 2))
    parser.add_argument('--atomic', action=argparse.BooleanOptionalAction)
    parser.add_argument('--evidence', help='R11: repository path of the retained T15 replay-determinism observation')
    parser.add_argument('--low-storage', action='store_true',
                        help='write version-2 requests superseding the frozen b1 protocols (MAATrace-only candidate)')
    args = parser.parse_args()
    if args.mode == 'v4-requests':
        v4_requests()
    elif args.mode == 'split-plans-c2':
        split_plans_c2()
    elif args.mode == 'v3-requests':
        v3_requests()
    elif args.mode == 'split-plans':
        split_plans()
    elif args.mode == 'requests' and args.low_storage:
        low_storage_requests()
    elif args.mode == 'requests':
        if args.repetitions is None or args.atomic is None:
            parser.error('requests need --repetitions and --atomic/--no-atomic from the R11/R12 evidence')
        if args.repetitions == 1 and not (args.evidence and (ROOT/args.evidence).is_file()):
            parser.error('one replay needs --evidence naming a retained determinism observation')
        write_requests(args.repetitions, args.atomic, args.evidence)
    else:
        write_plan()


if __name__ == '__main__':
    main()
