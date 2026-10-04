#!/usr/bin/env python3
"""Prepare and publish a native protocol from actual unchanged BFS pilots.

Updated: 2026-09-27 (Eastern Time). Preparation does not freeze settings. Publish
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
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_coverage, bfs_protocol, profile_package
from swdb.cli import Failure
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


def repeatability_control(spec, packets, store, identities, gates):
    """Recheck the final unchanged block; a numerical A/A gain vetoes freeze."""
    from scripts import bfs_native_repeatability as repeat
    from swdb.bfs_native import json_observation, StageFailure
    from swdb.cli import Failure
    result = {'state': 'unqualified', 'pairs': [], 'gain_claim': False,
              'scope': 'unchanged-code negative control; no candidate assessment or empirical gain'}
    try:
        selected = spec.get('repeatability')
        require(isinstance(selected, dict) and set(selected) == {'evaluations', 'driver_receipt'},
                'repeatability evaluations and exact driver_receipt are required')
        mapping = selected['evaluations']
        require(isinstance(mapping, dict) and set(mapping) == {item['evaluation']['id'] for item in packets}
                and len(mapping) == len(set(mapping.values())) == len(packets)
                and len(packets) in (2, 4),
                'repeatability mapping must name exactly the selected first-block evaluations')
        plan = json.loads(repeat.PLAN.read_text()); repeat.validate_plan(plan)
        cells = {cell['first_evaluation']: cell for cell in plan['cells']}
        require(all(first in cells and cells[first]['id'] == second for first, second in mapping.items()),
                'repeatability mapping differs from the fixed final unchanged-block plan')
        ref = selected['driver_receipt']
        require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'} and Path(ref['path']).is_absolute(),
                'repeatability driver receipt needs an absolute path and exact hash')
        receipt, digest = json_observation(Path(ref['path']), 32 * 1024**2, 'repeatability driver receipt')
        require(digest == ref['sha256'], 'repeatability driver receipt bytes differ')
        require(isinstance(receipt.get('plan'), dict)
                and isinstance(receipt.get('cells'), list)
                and all(isinstance(row, dict) for row in receipt['cells'])
                and isinstance(receipt.get('stages'), list)
                and all(isinstance(row, dict) for row in receipt['stages']),
                'repeatability receipt plan/cells/stages have malformed nested types')
        require(receipt.get('id') == repeat.RUN_ID and receipt.get('state') == 'complete'
                and receipt.get('role') == 'second_unchanged_native_calibration_block'
                and receipt.get('bounds') == repeat.BOUNDS and receipt.get('profiling') is False
                and receipt.get('gain_claim') is False and receipt.get('protocol_freeze') is False
                and receipt.get('plan', {}).get('sha256') == artifacts.file_hash(repeat.PLAN)
                and [row.get('id') for row in receipt.get('cells', [])] == [row['id'] for row in plan['cells']]
                and all(row.get('state') == 'complete' for row in receipt['cells']),
                'repeatability receipt lacks the complete fixed four-cell block')
        result.update(driver_receipt=copy.deepcopy(ref), retained_driver=receipt,
            plan={'path': str(repeat.PLAN), 'sha256': artifacts.file_hash(repeat.PLAN)})
        policy = {'minimum_speedup': 1.05, 'confidence': .95, 'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925}
        result['numerical_policy'] = policy
        for item in packets:
            first = item['evaluation']; cell = cells[first['id']]
            second = store.get(mapping[first['id']], 'evaluation')
            require(second is not None, 'required second-block evaluation is unavailable: ' + cell['id'])
            machine = store.get(first['machine'], 'machine')
            expected_request = repeat.first_request(first, cell, machine)
            second_samples = repeat.repeat_result(first, second, machine, expected_request)
            require([(row.get('repetition'), row.get('source_position')) for row in first['timing']]
                    == [(rep, position) for rep in range(5) for position in range(3)]
                    and all(len(row['correctness']['checks']) == 15 for row in (first, second)),
                    'repeatability blocks must preserve the full original trial/check order and count')
            require(second.get('source_snapshot') == first.get('source_snapshot'), 'second-block source snapshot changed')
            candidate = store.get(second['candidate'], 'candidate')
            implementation, source = unchanged(store, candidate)
            entry = next(row for row in receipt['cells'] if row['id'] == second['id'])
            require(entry.get('evaluation') == second['id'] and entry.get('first_evaluation') == first['id']
                    and entry.get('first_record_sha256') == artifacts.digest(first)
                    and entry.get('first_binary_sha256') == entry.get('second_binary_sha256') == first['build']['binary_sha256']
                    and entry.get('first_verifier_module_sha256') == first['context'].get('verifier_sha256')
                    and receipt.get('verifier_module_sha256') == second['context'].get('verifier_sha256')
                    and re.fullmatch(r'[a-f0-9]{64}', entry.get('compiler_sha256', ''))
                    and isinstance(receipt.get('inherited_runtime_settings'), dict)
                    and set(receipt['inherited_runtime_settings']) == {
                        'OMP_THREAD_LIMIT', 'OMP_WAIT_POLICY', 'GOMP_SPINCOUNT', 'GOMP_CPU_AFFINITY'}
                    and all(value is None or isinstance(value, str)
                            for value in receipt['inherited_runtime_settings'].values()),
                    'repeatability driver cell differs from retained evaluation identities')
            outputs = [row for row in receipt.get('stages', [])
                       if Path(row.get('output', '')).name == second['id'] + '.result.json']
            require(len(outputs) == 1 and outputs[0].get('state') == 'complete'
                    and type(outputs[0].get('returncode')) is int and outputs[0]['returncode'] == 0,
                    'second-block public evaluation result is missing or unsuccessful')
            returned, returned_sha = json_observation(Path(outputs[0]['output']), 32 * 1024**2,
                                                      'second-block public evaluation result')
            require(returned_sha == outputs[0].get('stdout_sha256')
                    and artifacts.digest(returned) == artifacts.digest(second),
                    'second-block record differs from the retained public evaluation result')
            availability = repeat.verify_available([first, second, candidate, source, implementation,
                {'path': ref['path'], 'sha256': ref['sha256']},
                {'path': outputs[0]['output'], 'sha256': returned_sha}])
            first_samples = sample_grid(first, SOURCES, 5)
            a, b = ({position: row['samples_seconds'] for position, row in enumerate(samples)}
                    for samples in (first_samples, second_samples))
            directions = []
            for label, left, right in (('first_over_second', a, b), ('second_over_first', b, a)):
                measured = bfs_protocol._statistics(left, right, policy)
                exceeds = measured['confidence_interval']['lower'] > policy['minimum_speedup']
                directions.append({'direction': label, 'statistics': measured, 'numerical_gain_leg': exceeds})
                if exceeds:
                    gates.append(first['id'] + ': unchanged-code A/A ' + label
                        + ' lower confidence bound exceeds 1.05; native profitability is uncalibrated regardless of spread ceiling')
            if any(row['relative_spread'] > spec['maximum_relative_spread'] for row in second_samples):
                gates.append(second['id'] + ': second-block spread exceeds the fixed supplied ceiling')
            pair = {'first_evaluation': first['id'], 'second_evaluation': second['id'], 'directions': directions,
                'blocks': [{'evaluation': row['id'], 'sha256': artifacts.digest(row),
                    'samples': samples, 'timing': copy.deepcopy(row['timing']),
                    'correctness': copy.deepcopy(row['correctness']), 'stages': copy.deepcopy(row.get('stages', [])),
                    'context': copy.deepcopy(row['context']), 'build': copy.deepcopy(row['build'])}
                    for row, samples in ((first, first_samples), (second, second_samples))],
                'diagnostics': {'first_profile_package': item['package']['id'],
                    'first_region_profile': item['diagnostic']['id'], 'second': None,
                    'scope': 'first-block diagnostics retain their original evaluation; second block collected no new profile'},
                'condition_limits': {'first_compiler_executable_sha256': None, 'first_inherited_runtime_settings': None,
                    'second_compiler_executable_sha256': entry.get('compiler_sha256'),
                    'second_inherited_runtime_settings': receipt.get('inherited_runtime_settings'),
                    'verifier_module_equal': first['context'].get('verifier_sha256') == second['context'].get('verifier_sha256'),
                    'interpretation': 'missing historical settings remain unknown; evaluator code may differ despite identical timed bytes'},
                'raw_verification': availability}
            result['pairs'].append(pair)
            identities.update({row['id']: artifacts.digest(row) for row in (second, candidate, source, implementation)})
        result['state'] = 'numerical_gain_detected' if any(direction['numerical_gain_leg']
            for pair in result['pairs'] for direction in pair['directions']) else 'no_numerical_gain_detected'
        result['limitation'] = 'A control without a numerical gain does not establish nominal interval coverage or statistical power.'
    except (Failure, StageFailure, ValueError, KeyError, TypeError, OSError) as exc:
        result['reason'] = str(exc)
        gates.append('native repeatability evidence is not qualified (missing, unavailable, or incompatible): ' + str(exc))
    return result


def calibrated_runtime(control, paired_mode):
    """Bind observed native inputs without filling gaps in historical records."""
    from swdb.bfs_native import RUNTIME_INHERITED, controlled_environment, validate_runtime_policy
    policies = []
    if paired_mode:
        retained = control.get('retained_driver', {}).get('inherited_runtime_settings')
        require(isinstance(retained, dict) and set(retained) == set(RUNTIME_INHERITED),
                'paired calibration lacks its observed inherited runtime inputs')
        evaluations = [evaluation for pair in control.get('pairs', [])
                       for evaluation in pair.get('evaluations', {}).values()]
        require(len(evaluations) == 8, 'paired calibration lacks runtime inputs for all eight members')
        for evaluation in evaluations:
            controlled = evaluation['build'].get('execution_environment')
            require(controlled == controlled_environment(evaluation['context']['threads']),
                    'paired calibration controlled runtime inputs differ from its declared execution')
            policy = {'version': 1, 'environment': {**controlled, **retained}}
            validate_runtime_policy(policy, evaluation['context']['threads'])
            if 'native_runtime' in evaluation['build']:
                explicit = validate_runtime_policy(evaluation['build']['native_runtime'],
                                                   evaluation['context']['threads'])
                require(artifacts.digest(explicit) == artifacts.digest(policy),
                        'paired primary runtime inputs differ from its retained driver snapshot')
            policies.append(policy)
        evidence = {'basis': 'revalidated paired driver inherited inputs and primary controlled inputs',
                    'driver_receipt': copy.deepcopy(control['driver_receipt']),
                    'evaluations': [row['id'] for row in evaluations]}
    else:
        blocks = [block for pair in control.get('pairs', []) for block in pair.get('blocks', [])]
        require(blocks, 'serial calibration lacks observed runtime inputs for every block')
        for block in blocks:
            require(block['build'].get('execution_environment') == controlled_environment(block['context']['threads']),
                    'serial calibration controlled runtime inputs contradict its declared execution')
            policies.append(validate_runtime_policy(block['build'].get('native_runtime'), block['context']['threads']))
        evidence = {'basis': 'explicit runtime inputs retained in every serial calibration block',
                    'evaluations': [block['evaluation'] for block in blocks]}
    require(policies and all(value == policies[0] for value in policies),
            'native calibration runtime inputs differ between its observations')
    return copy.deepcopy(policies[0]), evidence


def prepare(spec, store):
    require(spec.get('mode') == 'native', 'this narrow driver prepares native protocols only')
    one_thread_mode = 'one_thread_calibration' in spec
    paired_mode = 'paired_calibration' in spec
    require(not (one_thread_mode and paired_mode), 'select exactly one native calibration route')
    threads, repetitions = (1, 10) if one_thread_mode else (4, 5)
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
    native_only = (native_only_size_scope(spec, one_thread_mode, selection)
                   if 'accelerator_size_gate' in spec else None)
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
                and context['threads'] == threads and context['target'] == 'mbit10'
                and context.get('verifier') == 'swdb.bfs.structural.v1' and context.get('function') == 'DOBFS'
                and not any(flag.startswith('-DMAA') for flag in evaluation['build']['flags']),
                'native pilot ROI, threads, actual lane, or CPU artifact differs from plan')
        require(context.get('machine_sha256') == artifacts.digest(machine), 'native pilot machine metadata changed')
        identities.update(item['record_identities']); identities[machine['id']] = artifacts.digest(machine)
        samples = sample_grid(evaluation, SOURCES, repetitions)
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
    historical_gates = []
    if any(row['relative_spread'] > ceiling for item in observations for row in item['samples']):
        (historical_gates if paired_mode else gates).append(
            'observed native baseline spread exceeds the fixed supplied ceiling; no automatic relaxation')
    historical_packets = packets
    if paired_mode:
        from scripts.bfs_paired_calibration import historical_packets as read_historical_packets
        historical_packets = read_historical_packets(spec, packets, store)
        for item in historical_packets:
            identities.update(item['record_identities'])
    historical_spec = spec
    if one_thread_mode:
        from scripts.bfs_one_thread_calibration import historical_selection
        historical_spec, historical_packets = historical_selection(spec, store)
        for item in historical_packets:
            identities.update(item['record_identities'])
            if any(row['relative_spread'] > ceiling for row in sample_grid(item['evaluation'], SOURCES, 5)):
                historical_gates.append(item['evaluation']['id'] + ': historical first-block spread exceeds the fixed ceiling')
    control = repeatability_control(historical_spec, historical_packets, store, identities,
                                    historical_gates if paired_mode or one_thread_mode else gates)
    historical_control, paired_primary = None, []
    if paired_mode or one_thread_mode:
        from scripts.bfs_paired_calibration import qualify
        require(control.get('state') in {'no_numerical_gain_detected', 'numerical_gain_detected'},
                'paired publication must retain a revalidated historical serial control, including its failures')
        # The collection/analysis changed prospectively. Retain the old failed
        # controls, including their vetoes, instead of relabeling them as paired.
        historical_control = {'control': control, 'unmet_gates': historical_gates,
            'admitted_for_new_sampling': False,
            'review_spread_ceiling': ceiling, 'original_spread_policy_frozen': False,
            'scope': 'historical serial collection; retained without promoting or excluding its observations; '
                'spread diagnostics use the supplied prospective ceiling, not a retroactive historical freeze'}
        if one_thread_mode:
            from scripts.bfs_one_thread_calibration import historical_paired_control, qualify as qualify_one_thread
            historical_paired = historical_paired_control(spec, store, identities)
            control, paired_primary = qualify_one_thread(spec, packets, store, identities, gates)
        else:
            control, paired_primary = qualify(spec, packets, store, identities, gates)
        for item, primary in zip(packets, paired_primary):
            historical = item['evaluation']
            require(all(primary['context'].get(key) == historical['context'].get(key)
                        for key in ('candidate_sha256', 'application', 'function', 'adapter',
                                    'target', 'machine_sha256', 'backend_configuration', 'instrumentation',
                                    'sources', 'threads', 'roi', 'verifier'))
                    and all(primary['build'].get(key) == historical['build'].get(key)
                            for key in (*BUILD_FIELDS, 'template_sha256', 'wrapper_sha256',
                                        'binary_sha256', 'execution_environment')),
                    'paired primary differs from the source/build/target treatment of its retained diagnostic package')
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
    if native_only is not None:
        accelerated = native_only
    else:
        accelerated = accelerator_gate(store, selection.get('accelerator_packages', []), packets, identities, gates, ceiling)
    policy = {'minimum_speedup': 1.05, 'maximum_relative_spread': ceiling, 'confidence': 0.95,
              'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925}
    calibration = {'native_pilots': observations, 'repeatability_control': control,
        'record_identities': identities, 'shared_size_selection': selection,
        'accelerator_size_evidence': accelerated, 'rejected_pilots': rejected, 'spread_justification': spec['spread_justification'],
        'plans': [{'path': str(path), 'sha256': artifacts.file_hash(path)} for path in PLANS],
        'scope': 'native protocol only; no candidate acceptance, artifact reproduction, or Ticket15 completion',
        'region_comparisons': 'baseline attribution retained; no candidate region mapping or regional speedup invented'}
    if paired_mode or one_thread_mode:
        calibration.update(historical_serial_control=historical_control,
            diagnostic_scope='native_pilots retain their historical five-trial primary and collector overhead; '
                'new paired grids alone supply the prospective sampling readiness evidence')
    if one_thread_mode:
        calibration.update(historical_four_thread_paired_control=historical_paired,
            diagnostic_scope='all four fresh one-thread profiles are bound to their new ten-repetition primaries; '
                             'historical diagnostics and failures remain separately scoped')
    runtime_policy = None
    try:
        if one_thread_mode:
            from scripts.bfs_one_thread_calibration import calibrated_runtime as one_thread_runtime
            runtime_policy, runtime_evidence = one_thread_runtime(control)
        else:
            runtime_policy, runtime_evidence = calibrated_runtime(control, paired_mode)
        calibration['native_runtime_evidence'] = runtime_evidence
    except (Failure, ValueError, KeyError, TypeError) as exc:
        gates.append('native runtime calibration is unsupported: ' + str(exc))
    settings = {'mode': 'native', 'kernel': 'gapbs-bfs', 'workloads': [item['workload']['id'] for item in packets],
        'targets': {role: copy.deepcopy(configurations[0]) for role in ('baseline', 'candidate')},
        'builds': {role: copy.deepcopy(builds[0]) for role in ('baseline', 'candidate')},
        'instrumentation': {role: copy.deepcopy(instruments[0]) for role in ('baseline', 'candidate')},
        'threads': threads, 'roi': 'bfs.complete_call.v1',
        'correctness': {'coverage': 'every_timed_trial', 'verifier': 'swdb.bfs.structural.v1', 'required_cases': [],
                        'supporting_pilot_evidence': [item['evaluation'] for item in observations]},
        'sampling': {'repetitions': 5, 'warmups': 0, 'aggregation': 'geomean_source_median_ratio'},
        'profitability': policy, 'differences': {'software': ['Explicit source rewrite evaluated after this freeze'],
            'accelerator': [], 'configuration': []}, 'region_pairs': [], 'calibration': calibration}
    if paired_mode or one_thread_mode:
        settings['sampling'] = copy.deepcopy(control['sampling'])
        settings['correctness']['supporting_pilot_evidence'] = control['selected_primary_evaluations']
    if runtime_policy is not None:
        settings['native_runtime'] = runtime_policy
    bfs_protocol._validate_settings(settings, store)
    request['settings'] = settings
    result = {'format': 'swdb.bfs.native-pilot-freeze-review.v1', 'input': spec, 'publishable': not gates,
              'unmet_gates': gates, 'freeze_request': request, 'gain_claim': False, 'ticket15_complete': False}
    result['identity_sha256'] = artifacts.digest(result)
    return result


def supporting_case_evidence(store, item):
    """Keep independently checked diagnostic cases separate from primary evidence.

    Only the unchanged author reference's calibration may use this receipt.
    Candidate qualification and primary timing/coverage are never modified.
    """
    primary, profile = item['evaluation'], item['diagnostic']
    require(item['implementation']['id'] == 'dx100-bfs-maa-reference'
            and primary['context']['roi'] == 'bfs.dx100.traversal.v1',
            'separate case support is only for the unchanged author traversal calibration')
    runs = [run for run in profile.get('executions', []) if run.get('kind') == 'regions']
    require(len(runs) == 1, 'calibration requires one identified region diagnostic execution')
    run = runs[0]
    diagnostic = store.get(run.get('evaluation'), 'evaluation')
    require(diagnostic and diagnostic['id'] != primary['id'] and bfs_coverage._real(diagnostic)
            and diagnostic.get('outcome', {}).get('state') == 'complete'
            and diagnostic.get('context', {}).get('verifier') == 'dx100.bfs.verifier.v2'
            and not bfs_coverage._correctness(diagnostic, store),
            'supporting diagnostic requires its own complete real passed v2 correctness')
    context = diagnostic['context']
    require(all(diagnostic.get(key) == primary.get(key) for key in
                ('candidate', 'source_snapshot', 'implementation', 'machine'))
            and profile_package._same(profile_package._context(diagnostic), profile_package._context(primary))
            and context['workload']['id'] == primary['context']['workload']['id']
            and all(profile_package._same(context.get(key), primary['context'].get(key))
                    for key in ('model', 'interface', 'basis', 'verifier'))
            and all(profile_package._same(diagnostic['build'].get(key), primary['build'].get(key))
                    for key in ('model_build', 'simulator', 'simulator_sha256'))
            and all(profile_package._same(context.get('instrumentation', {}).get(key),
                                          primary['context'].get('instrumentation', {}).get(key))
                    for key in ('verifier_runtime', 'post_roi_trace')),
            'supporting diagnostic source/workload/ROI/target/model differs from primary')
    require(len(diagnostic.get('timing', [])) == len(primary.get('timing', [])) == 1,
            'supporting diagnostic must identify one actual replay')
    cell = {key: primary['timing'][0][key] for key in ('source', 'source_position', 'repetition')}
    require(all(type(value) is int and type(run.get(key)) is int
                and type(diagnostic['timing'][0].get(key)) is int
                and run.get(key) == value == diagnostic['timing'][0].get(key) for key, value in cell.items())
            and profile_package._same(run.get('correctness'), diagnostic['correctness'])
            and profile_package._same(run.get('execution_outcome'), diagnostic['outcome'])
            and run.get('evidence_kind') == 'execution', 'supporting diagnostic replay or retained verdict differs')
    build = store.get(context.get('candidate_build'), 'evaluation')
    model_ref = primary['build'].get('model_build', {})
    model = store.get(model_ref.get('evaluation'), 'evaluation')
    require(build and bfs_coverage._real(build) and build.get('outcome', {}).get('state') == 'complete'
            and build['outcome'].get('stage') == 'candidate_build'
            and build.get('candidate') == primary.get('candidate')
            and build.get('request', {}).get('diagnostic_regions') is True
            and build.get('context', {}).get('function') == 'DOBFSMAA'
            and build['context'].get('roi') == primary['context']['roi']
            and build['context'].get('accelerated_requested') is True
            and build['context'].get('candidate_sha256') == primary['context']['candidate_sha256']
            and build['context'].get('model_build') == model_ref.get('evaluation')
            and model and bfs_coverage._real(model) and model.get('outcome', {}).get('state') == 'complete'
            and model['outcome'].get('stage') == 'build' and artifacts.digest(model) == model_ref.get('sha256'),
            'supporting diagnostic lacks an exact real source/model compilation receipt')
    binary = {'path': diagnostic['build']['binary'], 'sha256': diagnostic['build']['binary_sha256']}
    region_binary = profile.get('artifacts', {}).get('region_binary', {})
    definition = build['context']['diagnostic']
    stages = [stage for stage in diagnostic.get('stages', []) if stage.get('stage') == 'simulation']
    require(build['build']['binary'] == binary['path'] and build['build']['binary_sha256'] == binary['sha256']
            and all(region_binary.get(key) == value for key, value in binary.items())
            and run.get('binary_sha256') == binary['sha256'] and len(stages) == 1
            and run.get('output') == run.get('region_output') == stages[0].get('log')
            and run.get('output_sha256') == run.get('region_output_sha256') == stages[0].get('log_sha256')
            and profile_package._same(item['package']['evidence']['diagnostic_executions'], profile['executions'])
            and profile_package._same(definition['discovery'], profile['discovery'])
            and profile['discovery'].get('backend') == 'libclang-cindex'
            and isinstance(definition.get('difference'), str) and definition['difference']
            and run.get('differences_from_primary') == [definition['difference']]
            and region_binary.get('difference') == definition['difference'],
            'supporting diagnostic differs from the packaged collector/binary/log')
    records = [diagnostic, build, model]
    availability = bfs_coverage._availability(records, context.get('host'))
    require(availability and all(row['state'] == 'verified' for row in availability),
            'supporting diagnostic raw/build/model artifacts are unavailable or changed')
    from swdb.dx100_profile import statistics
    from swdb.dx100_coverage import observe, trace_reference
    seal = context['sealed_roi']
    require(profile_package._same(seal['statistics'], context['statistics']), 'supporting diagnostic statistics differ from seal')
    intervals = statistics(Path(context['statistics']['path']), time.monotonic() + 30)
    require(len(intervals) == 1, 'supporting diagnostic needs one sealed statistics interval')
    values = intervals[0]['values']
    counters = {name: int(value) for name, value in values.items()
                if re.fullmatch(r'\S*maa\S*\.numInst(?:_[A-Z]+)?', name) and re.fullmatch(r'\d+', value)}
    log = Path(stages[0]['log'])
    actual = observe(log, values, context['configuration']['tile_elements'],
                     trace=trace_reference(diagnostic), deadline=time.monotonic() + 30)
    actual.update(instruction_counters=counters,
        accelerator_executed=(context['configuration'].get('mode') == 'MAA'
            and any(value > 0 for name, value in counters.items() if name.endswith('.numInst'))
            and all(actual['completed_trace_units'].get(unit, 0) > 0 for unit in ('S', 'I', 'R', 'A'))))
    require(artifacts.file_hash(log) == stages[0]['log_sha256']
            and artifacts.file_hash(Path(context['statistics']['path'])) == context['statistics']['sha256']
            and len(diagnostic['correctness']['checks']) == 1
            and profile_package._same(actual, diagnostic['correctness']['checks'][0].get('coverage')),
            'supporting diagnostic case observations differ from retained raw statistics/trace')
    coverage = bfs_coverage._acceleration(diagnostic, store)
    require(coverage['executed'], 'supporting diagnostic lacks positive executed accelerator evidence')
    return {'evaluation': diagnostic['id'], 'evaluation_sha256': artifacts.digest(diagnostic),
        'primary_evaluation': primary['id'], 'profile_package': item['package']['id'], 'region_profile': profile['id'],
        'build_evaluation': build['id'], 'build_sha256': artifacts.digest(build), 'model_build': model_ref,
        'binary': binary, 'cell': cell, 'coverage': coverage, 'checks': copy.deepcopy(diagnostic['correctness']['checks']),
        'instrumentation': copy.deepcopy(context['instrumentation']),
        'differences_from_primary': copy.deepcopy(run['differences_from_primary']),
        'raw_verification': availability,
        'scope': 'separate independently checked author diagnostic cases for calibration only; not primary coverage or timing'}


RESUME_PLAN = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/resume-plan-20260927.md'


def native_only_size_scope(spec, one_thread_mode, selection):
    """Explicit R7 route (2026-09-27 ET): a native-only protocol may omit the
    shared simulator size evidence. Opt-in only for the one-thread calibration;
    the selection must name the recorded decision by exact file hash and supply
    no accelerator packages. Controlled-simulator protocols keep the gate."""
    scope = spec['accelerator_size_gate']
    require(one_thread_mode, 'native-only size scope is limited to the one-thread calibration route')
    require(isinstance(scope, dict) and set(scope) == {'state', 'decision', 'plan', 'justification'}
            and scope['state'] == 'native_only_not_required' and scope['decision'] == 'R7'
            and isinstance(scope['justification'], str) and scope['justification'].strip(),
            'native-only size scope has an unsupported shape')
    plan = scope['plan']
    require(isinstance(plan, dict) and set(plan) == {'path', 'sha256'}
            and Path(plan['path']).resolve() == RESUME_PLAN.resolve()
            and artifacts.file_hash(RESUME_PLAN) == plan['sha256']
            and 'R7. **Native protocol independence.**' in RESUME_PLAN.read_text(),
            'native-only size scope must bind the exact recorded R7 decision')
    require(not selection.get('accelerator_packages'),
            'native-only size scope cannot also admit accelerator packages')
    return {'executions': [], 'repeatability': [], 'state': 'native_only_not_required',
            'decision': copy.deepcopy(scope),
            'scope': 'native protocol only; every controlled-simulator freeze keeps the shared accelerator size gate'}


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
        position, repetition = observation.get('source_position'), observation.get('repetition')
        require(type(position) is int and 0 <= position < len(SOURCES)
                and type(repetition) is int and 0 <= repetition < 2
                and type(observation.get('source')) is int and observation['source'] == SOURCES[position],
                'reference pilot source/replay cell differs from the planned grid')
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
        support = None
        if context['roi'] == 'bfs.dx100.traversal.v1' and not all(coverage['cases'].get(case)
                for case in ('full_tiles', 'tail_tiles', 'competing_parent_updates')):
            support = supporting_case_evidence(store, item)
            identities[support['evaluation']] = support['evaluation_sha256']
            identities[support['build_evaluation']] = support['build_sha256']
            identities[support['model_build']['evaluation']] = support['model_build']['sha256']
        grouped.setdefault(item['workload']['id'], []).append((evaluation, coverage, signature, support))
        evaluated.add(evaluation['id']); identities.update(item['record_identities'])
        evidence.append({'evaluation': evaluation['id'], 'profile_package': rid, 'workload': item['workload']['id'],
            'timing': evaluation['timing'], 'coverage': coverage, 'build': evaluation['build'],
            'configuration': context['backend_configuration'], 'instrumentation': context['instrumentation'],
            'raw_verification': item['availability'], 'stages': evaluation['stages'],
            'supporting_case_evidence': [support] if support else []})
    for wid in allowed:
        rows = grouped.get(wid, [])
        if len(rows) != 6 or len({signature for _, _, signature, _ in rows}) != 1:
            gates.append(wid + ': requires two identical configured replays per each of three sources')
            continue
        for source in SOURCES:
            runs = [e for e, _, _, _ in rows if e['timing'][0]['source'] == source]
            if (len(runs) != 2 or {e['timing'][0]['repetition'] for e in runs} != {0, 1}
                    or len({e['timing'][0]['output'] for e in runs}) != 2
                    or len({e['build']['binary_sha256'] for e in runs}) != 1):
                gates.append(wid + ': repeated simulator runs are missing, duplicated, or use different binaries')
            else:
                measured = summary(source, [e['timing'][0]['duration_s'] for e in runs])
                repeatability.append({'workload': wid, **measured, 'evaluations': [e['id'] for e in runs],
                                      'quantity': 'simulated_roi_seconds'})
                if measured['relative_spread'] > ceiling:
                    gates.append(wid + ': observed simulator repeatability exceeds the supplied fixed spread ceiling')
        for case in ('full_tiles', 'tail_tiles', 'competing_parent_updates'):
            if not any(coverage['cases'].get(case) or (support and support['coverage']['cases'].get(case))
                       for _, coverage, _, support in rows):
                gates.append(wid + ': missing observed accelerator ' + case)
    return {'executions': evidence, 'repeatability': repeatability}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'publish'))
    parser.add_argument('file', type=Path, help='operator selection JSON for prepare; exact review JSON for publish')
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--db', type=Path, required=True,
                        help='absolute SQLite cache path in separately accounted raw storage, outside code/records/output')
    args = parser.parse_args()
    args.records = args.records.resolve()
    require(args.db.is_absolute() and args.db == args.db.resolve()
            and args.db != args.file.resolve()
            and all(root != args.db and root not in args.db.parents
                    for root in (ROOT.resolve(), args.records, args.output.resolve()))
            and (not args.db.exists() or args.db.is_file()),
            'database must be an absolute, nonsymlinked file outside repository, records, input, and new output directory')
    source = json.loads(args.file.read_text())
    spec = source['input'] if args.action == 'publish' else source
    if args.action == 'publish':
        copy_of_review = copy.deepcopy(source); digest = copy_of_review.pop('identity_sha256')
        require(artifacts.digest(copy_of_review) == digest, 'review content identity changed')
    # The public query verifies the master records; preparation then uses exactly
    # that authoritative folder for bounded cross-record and raw-artifact checks.
    for rid in spec.get('packages', []) + spec.get('size_selection', {}).get('accelerator_packages', []):
        result = subprocess.run([sys.executable, '-m', 'swdb', 'get', rid, '--records', str(args.records),
                                 '--db', str(args.db), '--format', 'json'],
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
            '--records', str(args.records), '--db', str(args.db), '--format', 'json'],
            cwd=ROOT, capture_output=True, text=True, timeout=180)
        (args.output / 'freeze.stdout.json').write_text(result.stdout)
        (args.output / 'freeze.stderr').write_text(result.stderr)
        require(result.returncode == 0, 'public freeze failed; retained exact request and diagnostics')
        frozen = json.loads(result.stdout)
        result = subprocess.run([sys.executable, '-m', 'swdb', 'get', frozen['id'], '--records', str(args.records),
                                 '--db', str(args.db), '--format', 'json'],
                                cwd=ROOT, capture_output=True, text=True, timeout=180)
        require(result.returncode == 0 and json.loads(result.stdout) == frozen, 'fresh public frozen-protocol retrieval differs')
        print(json.dumps({'protocol': frozen['id'], 'gain_claim': False, 'ticket15_complete': False}))
    else:
        print(json.dumps({'review': str(args.output / 'review.json'), 'publishable': review['publishable'],
                          'unmet_gates': review['unmet_gates'], 'frozen': False}))


if __name__ == '__main__':
    main()
