#!/usr/bin/env python3
"""Build the T17/T20 controlled-simulator freeze requests from actual records. Created 2026-09-28 ET.

Every build/instrumentation field is copied from the retained primary build
records or reproduced from the exact map dx100.execute constructs (swdb/dx100.py
instrumentation block). Target configurations are the matched BASE/MAA
expansions already frozen by the T16 author protocol for the same target and
8-MiB/16-way/16,384-tile treatment. Nothing here executes a guest.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, yamlio  # noqa: E402
from swdb.store import Store  # noqa: E402

S = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25'
store = Store(ROOT / 'records')
t16 = yamlio.load(S / 'requests/author-matched-control-freeze-v1.yaml')['settings']
R11 = S / 'observations/t16-r11-replay-determinism-20260927.json'
AC10 = S / 'observations/t15-ac10-parent-case-20260928.json'
ANALYSIS = S / 'observations/t15-pilot-analysis-20260928.json'
WORKLOADS = ['bfs-20260925-uniform18.cd2169a5c421baf7', 'bfs-20260925-kronecker18.48de8267ac2098d5']
VERIFIER = {name: artifacts.file_hash(ROOT / path) for name, path in (
    ('driver_sha256', 'scripts/dx100_verify.py'), ('parser_sha256', 'swdb/dx100_witness.py'),
    ('observer_sha256', 'scripts/dx100_host_memory.py'))}
POST_ROI = {'flag': 'SyscallBase', 'scope': 'post-seal verifier continuation only',
            'output': 'separate_simulator_trace', 'format_flags': ['FmtFlag'],
            'disabled_format_flags': ['FmtTicksOff', 'FmtStackTrace'],
            'disabled_roi_flags': ['MAATrace', 'MAARangeFuser', 'MAAIndirect'], 'chunk_ticks': 10**9}


def ref(path):
    return {'path': str(Path(path).relative_to(ROOT)), 'sha256': artifacts.file_hash(path)}


def build(rid):
    record = store.get(rid, 'evaluation')
    assert record['outcome'] == {'state': 'complete', 'stage': 'candidate_build',
        'reason': 'Identified candidate compiled; no simulated correctness or timing inferred.'}, rid
    assert record['context']['roi'] == 'bfs.complete_call.v1' and record['build']['adapter'] == 'dx100.complete_call.v2'
    return record


def instrumentation(primary, accelerated):
    """Exact primary map dx100.execute builds for a v2, coverage-when-accelerated series."""
    value = {'treatment': 'primary', 'roi': 'bfs.complete_call.v1',
             'suppressed_internal_events': list(primary['context']['suppressed_internal_events']),
             'verification': 'same_guest_post_roi',
             'debug_flags': 'MAATrace,MAARangeFuser,MAAIndirect' if accelerated else 'MAATrace',
             'verifier_runtime': dict(VERIFIER), 'post_roi_trace': dict(POST_ROI)}
    if primary['context'].get('graph_verification'):
        value['graph_verification'] = dict(primary['context']['graph_verification'])
    return value


def pair(semantic, baseline_diag, candidate_diag, baseline_id, candidate_id):
    regions = {row['id'] for row in baseline_diag['context']['diagnostic']['regions']}
    assert baseline_id in regions, baseline_id
    assert candidate_id in {row['id'] for row in candidate_diag['context']['diagnostic']['regions']}, candidate_id
    discovery, runtime = candidate_diag['context']['diagnostic']['discovery'], candidate_diag['context']['diagnostic']['runtime']
    other = baseline_diag['context']['diagnostic']
    assert all(other['discovery'][key] == discovery[key] for key in ('backend', 'collector', 'library_sha256', 'pass_sha256'))
    assert other['runtime']['sha256'] == runtime['sha256']
    return {'semantic_region': semantic, 'baseline': baseline_id, 'candidate': candidate_id,
            'scope': 'accumulated', 'attribution': 'inclusive', 'evidence': 'simulated_diagnostic_profile',
            'collector': {'backend': discovery['backend'], 'collector': discovery['collector'],
                          'library_sha256': discovery['library_sha256'], 'pass_sha256': discovery['pass_sha256'],
                          'runtime_sha256': runtime['sha256']}}


def settings(route):
    b_primary, c_primary = build(route['baseline_primary']), build(route['candidate_primary'])
    b_diag, c_diag = build(route['baseline_diagnostic']), build(route['candidate_diagnostic'])
    return {
        'mode': 'controlled_simulator', 'kernel': 'gapbs-bfs', 'workloads': WORKLOADS,
        'targets': {'baseline': t16['targets']['baseline'], 'candidate': t16['targets']['candidate']},
        'simulation_identity': t16['simulation_identity'],
        'builds': {role: {key: record['build'][key] for key in ('compiler', 'compiler_version', 'adapter', 'flags')}
                   for role, record in (('baseline', b_primary), ('candidate', c_primary))},
        'instrumentation': {'baseline': instrumentation(b_primary, False), 'candidate': instrumentation(c_primary, True)},
        'threads': 4, 'roi': 'bfs.complete_call.v1',
        'correctness': {
            'coverage': 'every_timed_trial', 'verifier': 'dx100.bfs.verifier.v2', 'required_cases': [],
            'required_accelerator_cases': {'baseline': [], 'candidate': ['executed', 'full_tiles', 'tail_tiles']},
            'companion_cases': [{
                'id': 'bfs.dx100.competing-parent-case.v1',
                'role': 'candidate',
                'requirement': ('Before any gain claim, one correctness-only public dx100-execute of the exact '
                                'candidate primary (timed) binary and frozen MAA configuration on workload '
                                'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e (source 0) must pass the v2 '
                                'verifier and observe competing_parent_updates with parent storage attributed. '
                                'Diagnostic builds never satisfy it.'),
                'workload': 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e',
                'required_accelerator_cases': ['executed', 'full_tiles', 'tail_tiles', 'competing_parent_updates'],
                'basis': ref(AC10)}]},
        'sampling': {'repetitions': 1, 'warmups': 0, 'aggregation': 'geomean_source_median_ratio',
                     'determinism': {'basis': 'deterministic_simulator_replay.v1',
                                     'evidence': '{path} sha256:{sha256}'.format(**ref(R11))}},
        'profitability': {'minimum_speedup': 1.05, 'maximum_relative_spread': 0.1, 'confidence': 0.95,
                          'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925},
        'differences': route['differences'],
        'region_pairs': [pair(name, b_diag, c_diag, baseline, candidate) for name, baseline, candidate in route['pairs']],
        'calibration': {
            'pilot': 'bfs-t15-pilot-simulator-batch-20260927-b3', 'analysis': ref(ANALYSIS),
            'rejected_or_incomplete': ['bfs-t15-pilot-simulator-batch-20260927-b1 (120-s profile gate)',
                                       'bfs-t15-pilot-simulator-batch-20260927-b2 (180-s package timeout)',
                                       'bfs-t15-ac10-parent-case-20260928-a1 (author binary: parent storage unattributable)',
                                       'earlier T15 attempts retained in ticket 15'],
            'size_selection': ('Scale-18 uniform and Kronecker graphs: every T15 execution completed with correctness and '
                               'accelerator full/tail coverage within a one-lane 48-h allocation (about 35-42 min '
                               'simulation per execution); no candidate gain was used to choose them.'),
            'change_rule': ('Any change to settings requires a new protocol version with supersedes; comparisons '
                            'bound to a superseded version are invalidated and must be re-collected.'),
            'quantities': 'simulated_roi_seconds only; host wall time and diagnostic intervals are cost evidence, never timing samples.'},
        'route': {'ticket': route['ticket'], 'baseline_candidate': b_primary['candidate'],
                  'candidate': c_primary['candidate'],
                  'builds': {key: {'id': route[key], 'sha256': artifacts.digest(store.get(route[key], 'evaluation'))}
                             for key in ('baseline_primary', 'baseline_diagnostic', 'candidate_primary', 'candidate_diagnostic')}}}


ROUTES = {
    't17': {'ticket': 17,
        'baseline_primary': 'bfs-scalar-v2-preparation-20260926-a1.dx100.primary.build',
        'baseline_diagnostic': 'bfs-scalar-v2-preparation-20260926-a1.dx100.diagnostic.build',
        'candidate_primary': 'bfs-t17-build-only-20260926-a1',
        'candidate_diagnostic': 'bfs-t17-diagnostic-build-only-20260927-a2',
        'pairs': [('bfs.complete_call', 'function:bfs.cc:13304:76a956649bfe9705', 'function:bfs.cc:13347:4d66411f1e0ed09c'),
                  ('bfs.top_down_step.maa', 'function:bfs.cc:2157:ba2f8e639d5daef5', 'function:bfs.cc:2157:6e2df14488cc294c')],
        'differences': {'software': ['Unchanged dx100-bfs-scalar DOBFS versus the T17 rewrite of the DX100 source (TDStepMAA called from DOBFS).'],
                        'accelerator': ['MAA enabled only for the candidate role.'],
                        'configuration': ['Both roles use LLC 8MiB/16-way and identical CPU, caches, memory and clock; accelerator presence differs.']}},
    't20': {'ticket': 20,
        'baseline_primary': 'bfs-scalar-v2-preparation-20260926-a1.upstream.primary.build',
        'baseline_diagnostic': 'bfs-scalar-v2-preparation-20260926-a1.upstream.diagnostic.build',
        'candidate_primary': 'bfs-t20-context6-primary-build-20260927-c3',
        'candidate_diagnostic': 'bfs-t20-context6-diagnostic-build-20260927-c3',
        'pairs': [('bfs.complete_call', 'function:bfs.cc:3477:2152911a89faaaf1', 'function:bfs.cc:9645:c5933781d13e31de'),
                  ('bfs.top_down_step', 'function:bfs.cc:2004:ffc8e4d681ba23b5', 'function:bfs.cc:4522:cc91f2b43ef677b1')],
        'differences': {'software': ['Unchanged gapbs-bfs-do DOBFS versus the T20 upstream rewrite (DX100Prepare/TDStepDX100 called from DOBFS; TDStep retained as fallback).'],
                        'accelerator': ['MAA enabled only for the candidate role.'],
                        'configuration': ['Both roles use LLC 8MiB/16-way and identical CPU, caches, memory and clock; accelerator presence differs.']}}}


if __name__ == '__main__':
    for key, route in ROUTES.items():
        request = {'message_version': '1.0', 'id': f'bfs-{key}-controlled-simulator-20260928', 'version': 1,
                   'settings': settings(route)}
        path = S / 'requests' / f'bfs-{key}-controlled-simulator-freeze-20260928-a1.json'
        path.write_text(json.dumps(request, indent=1) + '\n')
        print(path, artifacts.file_hash(path))
