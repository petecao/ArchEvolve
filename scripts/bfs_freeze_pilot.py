#!/usr/bin/env python3
"""Prepare and publish a native protocol from actual unchanged BFS pilots.

Updated: 2026-09-26 (Eastern Time). Preparation does not freeze settings. Publish
revalidates the reviewed evidence and requires the shared accelerator size gate.
This narrow native freeze does not resolve Ticket 15 or the artifact reference.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_coverage, bfs_protocol, profile_package
from swdb.store import Store

REVISION = 'e4fc4afdf894f295442cef3604667a469fab8e62'
SOURCES = [0, 1234, 7777]
BUILD_FIELDS = ('compiler', 'compiler_version', 'flags')
PLANS = [ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25' / name
         for name in ('pilot-plan.md', 'artifact-reference-plan.md')]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sample_grid(evaluation, sources, repetitions):
    """Validate actual native trials without inventing a pre-existing freeze."""
    context, binary = evaluation['context'], evaluation['build']['binary_sha256']
    require(context['sources'] == sources and all(type(source) is int for source in context['sources'])
            and type(context['repetitions']) is int and context['repetitions'] == repetitions,
            'pilot source sequence/repetitions differ from the planned grid')
    cells, paths = {}, set()
    for row in evaluation['timing']:
        position, repetition = row.get('source_position'), row.get('repetition')
        require(type(position) is int and type(repetition) is int and 0 <= position < len(sources)
                and 0 <= repetition < repetitions, 'unexpected pilot trial cell')
        cell = (position, repetition)
        require(cell not in cells and row.get('output') not in paths, 'duplicate trial or reused process output')
        require(type(row.get('source')) is int and row['source'] == sources[position]
                and row.get('binary_sha256') == binary and row.get('roi') == context['roi']
                and row.get('basis') == 'measured' and row.get('quantity') == 'native_roi_wall_seconds'
                and row.get('verified') is True and row.get('evidence_kind') == 'execution',
                'pilot timing source/binary/ROI/evidence identity differs')
        value = row.get('duration_s')
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, 'invalid actual pilot duration')
        cells[cell] = value; paths.add(row['output'])
    require(len(cells) == len(sources) * repetitions, 'missing actual pilot trials')
    return [summary(source, [cells[position, repeat] for repeat in range(repetitions)])
            for position, source in enumerate(sources)]


def summary(source, values):
    median = statistics.median(values)
    return {'source': source, 'samples_seconds': values, 'median_seconds': median,
            'relative_spread': (max(values) - min(values)) / median}


def unchanged(store, candidate):
    implementation = store.get(candidate['implementation'], 'implementation')
    source = store.get(candidate['source_snapshot'], 'source_snapshot')
    require(implementation and source and candidate.get('artifact_role') == 'source_baseline'
            and not candidate.get('proposal') and source['implementation'] == implementation['id']
            and candidate['artifact']['sha256'] == source['artifact']['sha256']
            and all(item['context'].get('function') == implementation['function'] for item in (source, candidate)),
            'calibration is not an unchanged identified starting source')
    expected = artifacts.identify(artifacts.source_root(store, implementation))
    require(candidate['artifact']['sha256'] == expected['sha256'], 'calibration changed the pinned application source')
    return implementation, source


def packet(store, package_id):
    package = store.get(package_id, 'profile_package')
    require(package is not None, 'missing pilot profile package: ' + package_id)
    evaluation = store.get(package.get('evaluation'), 'evaluation')
    require(evaluation and bfs_coverage._real(evaluation) and evaluation['outcome']['state'] == 'complete'
            and not bfs_coverage._correctness(evaluation, store), 'pilot needs complete real independently checked primary evidence')
    accepted, rejected = bfs_coverage._packages(store, evaluation)
    require(any(row['id'] == package_id for row in accepted), 'pilot package is incomplete, invalid, stale, or a fixture: ' + str(rejected))
    candidate = store.get(evaluation['candidate'], 'candidate')
    implementation, source = unchanged(store, candidate)
    diagnostic = store.get(package['region_profile'], 'region_profile')
    expected_context = profile_package._context(evaluation)
    require(candidate['artifact']['sha256'] == expected_context['source_sha256']
            and all(profile_package._same(package['context'].get(key), value) for key, value in expected_context.items()),
            'pilot package or timed source context differs from the actual candidate')
    reasons = (profile_package._profile_check(diagnostic, evaluation, candidate)
               + profile_package._check_observations(diagnostic, evaluation, candidate))
    require(not reasons, 'pilot observations are unavailable or incompatible: ' + str(reasons))
    workload = store.get(evaluation['context']['workload']['id'], 'workload')
    require(workload is not None, 'pilot workload is not registered')
    bfs_protocol.verify_immutable(workload)
    require(workload['definition']['canonical_sha256'] == evaluation['context']['workload']['canonical_sha256'],
            'pilot loaded adjacency differs from registration')
    records = [package, evaluation, candidate, implementation, source, diagnostic, workload]
    availability = bfs_coverage._availability(records, evaluation['context'].get('host'))
    require(availability and all(row['state'] == 'verified' for row in availability),
            'pilot raw/source/binary evidence is unavailable, remote-unverified, or changed')
    source_root = artifacts.verify(candidate['artifact'])
    regions = [profile_package._region(row, source_root) for row in package['regions'] if profile_package._timing_quantity(row)]
    require(all(any(row['kind'] == kind for row in regions) for kind in ('function', 'loop')),
            'pilot lacks usable automatically discovered function/loop attribution')
    return {'package': package, 'evaluation': evaluation, 'candidate': candidate, 'implementation': implementation,
            'diagnostic': diagnostic, 'workload': workload, 'regions': regions, 'availability': availability,
            'record_identities': {row['id']: artifacts.digest(row) for row in records}}


def workload_plan(workload, scale):
    definition = workload['definition']; generator = definition['generator']
    parameters = generator['parameters']
    require(definition['family'] in {'kronecker', 'uniform_random'} and definition['sources'] == SOURCES
            and parameters.get('scale') == scale and parameters.get('edge_factor') == 16
            and parameters.get('seed') == 27491095 and parameters.get('symmetrize') is True
            and generator['revision'] == REVISION
            # The pinned builder retains IDs through the highest sampled endpoint;
            # a Kronecker graph need not contain the last possible vertex ID.
            and type(definition['realized']['num_vertices']) is int
            and max(SOURCES) < definition['realized']['num_vertices'] <= 2**scale,
            'workload differs from the planned generator, scale, degree, or source sequence')
    representations = definition['representations']
    require(all(any(row.get('application') == app and row.get('canonical_sha256') == definition['canonical_sha256']
                    and row.get('adjacency_verified') is True for row in representations) for app in ('gapbs', 'dx100-gapbs')),
            'both application loaders lack verified equivalent adjacency')


def native_lane(context, machine):
    """Read the historical verifier receipt; do not acquire a lane to review it."""
    from swdb.profile import lane_required
    require(context.get('host') == 'mbit10'
            and machine.get('id') == context.get('target') == 'mbit10'
            and machine.get('hostname') == 'mbit10' and lane_required(machine),
            'native pilot lacks the recorded socket-lane verifier receipt')
    from swdb.cli import Failure
    try:
        lane = bfs_protocol.verified_native_lane(context.get('lane'), machine)
    except Failure as exc:
        raise ValueError('native pilot: ' + str(exc)) from None
    require(context.get('backend_configuration', {}).get('lane') == lane,
            'native pilot verified lane differs from the machine or requested configuration')
    return lane


def freeze_header(spec, store):
    require(re.fullmatch(r'[a-z0-9][a-z0-9._-]*', spec.get('id', '')), 'invalid protocol identifier')
    request = {'message_version': '1.0', 'id': spec['id'], 'version': spec.get('version', 1)}
    if 'supersedes' in spec:
        require(isinstance(spec['supersedes'], str) and spec['supersedes'].strip(),
                'supersedes must identify the exact previous frozen protocol')
        request['supersedes'] = spec['supersedes']
    version, previous, _invalidated = bfs_protocol._version(request, store, 'protocol')
    prior_names = [row.id for row in store.of_kind('protocol') if row.data.get('requested_id') == request['id']]
    require(not prior_names or previous in prior_names,
            'changing an existing protocol name requires supersedes and a newer version')
    require(version == 1 or previous is not None, 'version greater than one requires supersedes')
    return request


def prepare(spec, store):
    require(spec.get('mode') == 'native', 'this narrow driver prepares native protocols only')
    request = freeze_header(spec, store)
    ceiling = spec.get('maximum_relative_spread')
    require(type(ceiling) in (int, float) and math.isfinite(ceiling) and ceiling > 0,
            'an explicit fixed maximum_relative_spread is required')
    require(isinstance(spec.get('spread_justification'), str) and spec['spread_justification'].strip(),
            'the operator must justify the spread ceiling from the actual baseline pilot')
    selection = spec.get('size_selection', {})
    scale = selection.get('scale')
    require(type(scale) is int and scale in (16, 18), 'performance scale must be planned18 or cost-qualified16')
    require(isinstance(selection.get('justification'), str) and selection['justification'].strip(),
            'shared workload-size selection requires a retained justification')
    ids = spec.get('packages', [])
    require(len(ids) == 2 and len(set(ids)) == 2, 'one distinct native package per graph family is required')
    packets = [packet(store, rid) for rid in ids]
    require({item['workload']['definition']['family'] for item in packets} == {'kronecker', 'uniform_random'},
            'both graph families are required')
    require(len({item['implementation']['id'] for item in packets}) == 1
            and packets[0]['implementation']['id'] in {'dx100-bfs-scalar', 'gapbs-bfs-do'},
            'native calibration requires one unchanged scalar implementation')
    identities, observations, configurations, builds, instruments = {}, [], [], [], []
    for item in packets:
        evaluation = item['evaluation']; context = evaluation['context']; workload_plan(item['workload'], scale)
        machine = store.get(evaluation['machine'], 'machine')
        require(machine is not None, 'native pilot machine metadata is missing')
        native_lane(context, machine)
        require(context['basis'] == 'measured' and context['roi'] == 'bfs.complete_call.v1'
                and context['threads'] == 4 and context['target'] == 'mbit10'
                and context.get('verifier') == 'swdb.bfs.structural.v1' and context.get('function') == 'DOBFS'
                and not any(flag.startswith('-DMAA') for flag in evaluation['build']['flags']),
                'native pilot ROI, threads, actual lane, or CPU artifact differs from plan')
        require(context.get('machine_sha256') == artifacts.digest(machine), 'native pilot machine metadata changed')
        identities.update(item['record_identities']); identities[machine['id']] = artifacts.digest(machine)
        samples = sample_grid(evaluation, SOURCES, 5)
        overhead = []
        for execution in item['diagnostic']['executions']:
            require(execution.get('kind') in ('regions', 'memory') and execution.get('correctness', {}).get('passed') is True,
                    'collector overhead needs an independently checked diagnostic execution')
            duration = execution.get('diagnostic_wall_seconds')
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
                    'diagnostic overhead observation is missing')
            median = next(row['median_seconds'] for row in samples if row['source'] == execution['source'])
            overhead.append({'kind': execution['kind'], 'source': execution['source'], 'diagnostic_wall_seconds': duration,
                'primary_median_seconds': median, 'observed_duration_ratio': duration / median,
                'interpretation': 'different instrumented diagnostic process; overhead context, never an ROI gain',
                'output_sha256': execution['output_sha256'], 'binary_sha256': execution['binary_sha256']})
        observations.append({'evaluation': evaluation['id'], 'profile_package': item['package']['id'],
            'workload': item['workload']['id'], 'family': item['workload']['definition']['family'], 'samples': samples,
            'source_sha256': item['candidate']['artifact']['sha256'], 'binary_sha256': evaluation['build']['binary_sha256'],
            'collector_overhead': overhead, 'diagnostic_build': item['package']['evidence']['diagnostic_build'],
            'region_attribution': item['regions'], 'raw_verification': item['availability'],
            'load_average': context.get('load_average'), 'lane': context['lane'], 'stages': evaluation['stages']})
        configurations.append({'id': context['target'], 'machine_sha256': context['machine_sha256'],
                               'configuration': context['backend_configuration']})
        builds.append({**{key: evaluation['build'][key] for key in BUILD_FIELDS}, 'adapter': context['adapter']})
        instruments.append(context['instrumentation'])
    for values in (configurations, builds, instruments):
        require(artifacts.digest(values[0]) == artifacts.digest(values[1]), 'native graph pilots used different target/build/instrumentation')
    gates = []
    if any(row['relative_spread'] > ceiling for item in observations for row in item['samples']):
        gates.append('observed native baseline spread exceeds the fixed supplied ceiling; no automatic relaxation')
    rejected = []
    for rid in selection.get('rejected_evaluations', []):
        row = store.get(rid, 'evaluation')
        require(row is not None, 'unknown rejected pilot evaluation')
        rejected.append({'evaluation': rid, 'sha256': artifacts.digest(row), 'outcome': row['outcome'], 'request': row['request']})
        identities[rid] = artifacts.digest(row)
    if scale == 16:
        cost_failure = False
        for item in rejected:
            row = store.get(item['evaluation'], 'evaluation')
            wid = row.get('context', {}).get('workload', {}).get('id') or row.get('request', {}).get('workload', {}).get('id')
            workload = store.get(wid, 'workload')
            if workload and workload['definition']['generator']['parameters'].get('scale') == 18:
                if bfs_coverage._real(row) and row['outcome']['state'] != 'complete' and re.search(
                        r'budget|time|storage|memory|resource', str(row['outcome']), re.I):
                    unchanged(store, store.get(row['candidate'], 'candidate')); cost_failure = True
        if not cost_failure:
            gates.append('scale16 requires a retained unchanged scale18 resource-cost failure')
    accelerated = accelerator_gate(store, selection.get('accelerator_packages', []), packets, identities, gates, ceiling)
    policy = {'minimum_speedup': 1.05, 'maximum_relative_spread': ceiling, 'confidence': 0.95,
              'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925}
    calibration = {'native_pilots': observations, 'record_identities': identities, 'shared_size_selection': selection,
        'accelerator_size_evidence': accelerated, 'rejected_pilots': rejected, 'spread_justification': spec['spread_justification'],
        'plans': [{'path': str(path), 'sha256': artifacts.file_hash(path)} for path in PLANS],
        'scope': 'native protocol only; no candidate acceptance, artifact reproduction, or Ticket15 completion',
        'region_comparisons': 'baseline attribution retained; no candidate region mapping or regional speedup invented'}
    settings = {'mode': 'native', 'kernel': 'gapbs-bfs', 'workloads': [item['workload']['id'] for item in packets],
        'targets': {role: copy.deepcopy(configurations[0]) for role in ('baseline', 'candidate')},
        'builds': {role: copy.deepcopy(builds[0]) for role in ('baseline', 'candidate')},
        'instrumentation': {role: copy.deepcopy(instruments[0]) for role in ('baseline', 'candidate')},
        'threads': 4, 'roi': 'bfs.complete_call.v1',
        'correctness': {'coverage': 'every_timed_trial', 'verifier': 'swdb.bfs.structural.v1', 'required_cases': [],
                        'supporting_pilot_evidence': [item['evaluation'] for item in observations]},
        'sampling': {'repetitions': 5, 'warmups': 0, 'aggregation': 'geomean_source_median_ratio'},
        'profitability': policy, 'differences': {'software': ['Explicit source rewrite evaluated after this freeze'],
            'accelerator': [], 'configuration': []}, 'region_pairs': [], 'calibration': calibration}
    bfs_protocol._validate_settings(settings, store)
    request['settings'] = settings
    result = {'format': 'swdb.bfs.native-pilot-freeze-review.v1', 'input': spec, 'publishable': not gates,
              'unmet_gates': gates, 'freeze_request': request, 'gain_claim': False, 'ticket15_complete': False}
    result['identity_sha256'] = artifacts.digest(result)
    return result


def accelerator_gate(store, ids, native, identities, gates, ceiling):
    require(isinstance(ids, list) and len(ids) == len(set(ids)), 'accelerator packages must be distinct record IDs')
    if not ids:
        gates.append('actual shared-size accelerator feasibility/correctness/coverage pilot is missing')
        return {'executions': [], 'repeatability': []}
    allowed = {item['workload']['id'] for item in native}
    grouped, evidence, evaluated, repeatability = {}, [], set(), []
    for rid in ids:
        item = packet(store, rid); evaluation = item['evaluation']; context = evaluation['context']
        require(item['implementation']['id'] == 'dx100-bfs-maa-reference' and context.get('basis') == 'simulated'
                and item['workload']['id'] in allowed and evaluation['id'] not in evaluated
                and context['threads'] == 4 and len(evaluation['timing']) == 1,
                'size feasibility requires distinct actual unchanged author-reference simulator executions')
        require(context['roi'] in ('bfs.complete_call.v1', 'bfs.dx100.traversal.v1')
                and context['backend_configuration'].get('mode') == 'MAA', 'reference ROI/configuration differs from calibration')
        observation = evaluation['timing'][0]
        require(observation.get('quantity') == 'simulated_roi_seconds' and observation.get('basis') == 'simulated'
                and observation.get('verified') is True and observation.get('source') in SOURCES
                and type(observation.get('duration_s')) in (int, float)
                and math.isfinite(observation['duration_s']) and observation['duration_s'] > 0,
                'reference pilot lacks actual simulated ROI timing')
        coverage = bfs_coverage._acceleration(evaluation, store)
        require(coverage['executed'], 'reference pilot used only fallback or lacks observed accelerator execution')
        signature = artifacts.digest({'context': {key: context.get(key) for key in
            ('candidate_sha256', 'target', 'backend_configuration', 'instrumentation', 'adapter', 'roi')},
            'build': {key: evaluation['build'].get(key) for key in
                      (*BUILD_FIELDS, 'adapter', 'binary_sha256', 'simulator_sha256')}})
        grouped.setdefault(item['workload']['id'], []).append((evaluation, coverage, signature))
        evaluated.add(evaluation['id']); identities.update(item['record_identities'])
        evidence.append({'evaluation': evaluation['id'], 'profile_package': rid, 'workload': item['workload']['id'],
            'timing': evaluation['timing'], 'coverage': coverage, 'build': evaluation['build'],
            'configuration': context['backend_configuration'], 'instrumentation': context['instrumentation'],
            'raw_verification': item['availability'], 'stages': evaluation['stages']})
    for wid in allowed:
        rows = grouped.get(wid, [])
        if len(rows) != 6 or len({signature for _, _, signature in rows}) != 1:
            gates.append(wid + ': requires two identical configured replays per each of three sources')
            continue
        for source in SOURCES:
            runs = [e for e, _, _ in rows if e['timing'][0]['source'] == source]
            if len(runs) != 2 or len({e['timing'][0]['output'] for e in runs}) != 2 or len({e['build']['binary_sha256'] for e in runs}) != 1:
                gates.append(wid + ': repeated simulator runs are missing, duplicated, or use different binaries')
            else:
                measured = summary(source, [e['timing'][0]['duration_s'] for e in runs])
                repeatability.append({'workload': wid, **measured, 'evaluations': [e['id'] for e in runs],
                                      'quantity': 'simulated_roi_seconds'})
                if measured['relative_spread'] > ceiling:
                    gates.append(wid + ': observed simulator repeatability exceeds the supplied fixed spread ceiling')
        for case in ('full_tiles', 'tail_tiles', 'competing_parent_updates'):
            if not any(coverage['cases'].get(case) for _, coverage, _ in rows):
                gates.append(wid + ': missing observed accelerator ' + case)
    return {'executions': evidence, 'repeatability': repeatability}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'publish'))
    parser.add_argument('file', type=Path, help='operator selection JSON for prepare; exact review JSON for publish')
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    args = parser.parse_args()
    args.records = args.records.resolve()
    source = json.loads(args.file.read_text())
    spec = source['input'] if args.action == 'publish' else source
    if args.action == 'publish':
        copy_of_review = copy.deepcopy(source); digest = copy_of_review.pop('identity_sha256')
        require(artifacts.digest(copy_of_review) == digest, 'review content identity changed')
    # The public query verifies the master records; preparation then uses exactly
    # that authoritative folder for bounded cross-record and raw-artifact checks.
    for rid in spec.get('packages', []) + spec.get('size_selection', {}).get('accelerator_packages', []):
        result = subprocess.run([sys.executable, '-m', 'swdb', 'get', rid, '--records', str(args.records), '--format', 'json'],
                                cwd=ROOT, capture_output=True, text=True, timeout=180)
        require(result.returncode == 0, 'public pilot retrieval failed: ' + result.stderr)
    review = prepare(spec, Store(args.records))
    if args.action == 'publish':
        require(review == source, 'reviewed evidence or settings changed; prepare and review again')
        require(review['publishable'], 'empirical freeze blocked: ' + '; '.join(review['unmet_gates']))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
    request_file = args.output / 'freeze-request.json'
    request_file.write_text(json.dumps(review['freeze_request'], indent=2) + '\n')
    if args.action == 'publish':
        result = subprocess.run([sys.executable, '-m', 'swdb', 'freeze-protocol', str(request_file),
            '--records', str(args.records), '--format', 'json'], cwd=ROOT, capture_output=True, text=True, timeout=180)
        (args.output / 'freeze.stdout.json').write_text(result.stdout)
        (args.output / 'freeze.stderr').write_text(result.stderr)
        require(result.returncode == 0, 'public freeze failed; retained exact request and diagnostics')
        frozen = json.loads(result.stdout)
        result = subprocess.run([sys.executable, '-m', 'swdb', 'get', frozen['id'], '--records', str(args.records), '--format', 'json'],
                                cwd=ROOT, capture_output=True, text=True, timeout=180)
        require(result.returncode == 0 and json.loads(result.stdout) == frozen, 'fresh public frozen-protocol retrieval differs')
        print(json.dumps({'protocol': frozen['id'], 'gain_claim': False, 'ticket15_complete': False}))
    else:
        print(json.dumps({'review': str(args.output / 'review.json'), 'publishable': review['publishable'],
                          'unmet_gates': review['unmet_gates'], 'frozen': False}))


if __name__ == '__main__':
    main()
