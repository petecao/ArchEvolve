"""Read the prospective paired A/A study without claiming a gain. Date: 2026-09-26 ET."""

import copy
import json
from pathlib import Path

from swdb import artifacts, bfs_protocol
from swdb.bfs_native import json_observation
from scripts.bfs_freeze_pilot import require


def historical_packets(spec, selected_packets, store):
    """Require all old cells, including DX100's failed control for either freeze."""
    from scripts import bfs_native_repeatability as historical
    from scripts.bfs_freeze_pilot import packet
    selection = spec['paired_calibration']
    require(isinstance(selection, dict), 'paired calibration selection must be a mapping')
    ids = selection.get('historical_packages')
    require(isinstance(ids, list) and len(ids) == len(set(ids)) == 4,
            'paired publication must retain four distinct historical packages')
    plan = json.loads(historical.PLAN.read_text())
    historical.validate_plan(plan)
    packets = [packet(store, rid) for rid in ids]
    require([item['evaluation']['id'] for item in packets]
            == [cell['first_evaluation'] for cell in plan['cells']],
            'historical packages must preserve all four original cells in their fixed order')
    require(all(item['package']['id'] in ids for item in selected_packets),
            'selected implementation packages differ from retained historical packages')
    return packets


def negative_control(samples, policy, sampling):
    """Keep both label directions; a numerical gain in either vetoes admission."""
    grids = {role: {position: row['samples_seconds'] for position, row in enumerate(rows)}
             for role, rows in samples.items()}
    directions, reasons = [], []
    for left, right in (('baseline', 'candidate'), ('candidate', 'baseline')):
        measured = bfs_protocol._statistics(grids[left], grids[right], policy, sampling)
        gain = measured['confidence_interval']['lower'] > policy['minimum_speedup']
        directions.append({'direction': left + '_over_' + right,
                           'statistics': measured, 'numerical_gain_leg': gain})
        if gain:
            reasons.append('unchanged-code ' + left + '_over_' + right
                           + ' lower confidence bound exceeds 1.05')
    if any(row['relative_spread'] > policy['maximum_relative_spread']
           for rows in samples.values() for row in rows):
        reasons.append('paired source timing spread exceeds the prospective fixed ceiling')
    return {'directions': directions, 'unmet_gates': reasons, 'gain_claim': False}


def qualify(spec, packets, store, identities, gates):
    """Reopen all four cells and their public/driver receipts before publication."""
    from scripts import bfs_native_paired_pilot as driver
    selected = spec['paired_calibration']
    require(isinstance(selected, dict) and set(selected) == {'pairs', 'driver_receipt', 'historical_packages'},
            'paired calibration requires all fixed pairs, historical packages, and one exact driver receipt')
    plan = json.loads(driver.PLAN.read_text())
    driver.validate_plan(plan)
    pair_ids = [cell['id'] for cell in plan['cells']]
    require(selected['pairs'] == pair_ids, 'paired calibration must retain the complete fixed four-cell study')
    require(spec['maximum_relative_spread'] == plan['maximum_relative_spread'],
            'paired spread ceiling differs from its prospective plan')
    reference = selected['driver_receipt']
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
            and isinstance(reference['path'], str) and Path(reference['path']).is_absolute(),
            'paired driver receipt requires an absolute path and exact hash')
    receipt, digest = json_observation(Path(reference['path']), 32 * 1024**2, 'paired pilot driver receipt')
    require(digest == reference['sha256'], 'paired pilot driver receipt bytes changed')
    require(receipt.get('id') == driver.RUN_ID and receipt.get('state') == 'complete'
            and receipt.get('role') == 'paired_unchanged_native_calibration'
            and receipt.get('bounds') == driver.BOUNDS
            and receipt.get('gain_claim') is False and receipt.get('protocol_freeze') is False
            and receipt.get('profiling') is False
            and receipt.get('plan', {}).get('sha256') == artifacts.file_hash(driver.PLAN)
            and isinstance(receipt.get('cells'), list)
            and all(isinstance(row, dict) for row in receipt['cells'])
            and [row.get('id') for row in receipt['cells']] == pair_ids
            and all(row.get('state') == 'complete' for row in receipt['cells']),
            'paired pilot driver did not complete the unchanged fixed study')
    require(isinstance(receipt.get('stages'), list)
            and all(isinstance(row, dict) for row in receipt['stages']),
            'paired pilot driver stages are malformed')
    execution_artifacts = driver.validate_driver_receipt(receipt, plan)
    sampling = {'repetitions': driver.REPETITIONS, 'warmups': 0,
                'aggregation': 'geomean_source_median_ratio',
                'collection': copy.deepcopy(driver.COLLECTION),
                'analysis': 'paired_repetition_block_bootstrap.v1'}
    policy = {'minimum_speedup': 1.05, 'confidence': .95, 'bootstrap_resamples': 2000,
              'bootstrap_seed': 20260925, 'maximum_relative_spread': plan['maximum_relative_spread']}
    result = {'state': 'unqualified', 'gain_claim': False, 'pairs': [],
              'driver_receipt': copy.deepcopy(reference), 'retained_driver': receipt,
              'execution_artifact_rechecks': execution_artifacts,
              'sampling': sampling, 'numerical_policy': policy,
              'scope': 'fixed unchanged-code negative controls; no candidate gain or interval-coverage claim'}
    primary = {}
    for cell, entry in zip(plan['cells'], receipt['cells']):
        first = store.get(cell['first_evaluation'], 'evaluation')
        require(first is not None, 'paired study lost its retained historical first block')
        machine = store.get(first['machine'], 'machine')
        request = driver.pair_request(first, cell, machine)
        pair = store.get(cell['id'], 'evaluation_pair')
        require(pair is not None and entry.get('pair_sha256') == artifacts.digest(pair)
                and entry.get('first_evaluation') == first['id']
                and entry.get('first_record_sha256') == artifacts.digest(first),
                'paired driver cell differs from its actual pair or historical block')
        requested, request_sha = json_observation(Path(entry['request']['path']), 10 * 1024**2,
                                                 'paired study submitted request')
        require(request_sha == entry['request']['sha256'] and requested == request,
                'paired study submitted request differs from the fixed plan')
        outputs = [stage for stage in receipt['stages']
                   if Path(stage.get('output', '')).name == pair['id'] + '.result.json']
        require(len(outputs) == 1 and outputs[0].get('state') == 'complete'
                and type(outputs[0].get('returncode')) is int and outputs[0]['returncode'] == 0,
                'paired study public result is missing or unsuccessful')
        returned, output_sha = json_observation(Path(outputs[0]['output']), 32 * 1024**2,
                                               'paired study public result')
        require(output_sha == outputs[0].get('stdout_sha256') and returned == pair,
                'paired study record differs from its public result bytes')
        samples = driver.validate_pair_result(store, first, pair, machine, request)
        evaluations = {role: store.get(pair[role + '_evaluation'], 'evaluation')
                       for role in ('baseline', 'candidate')}
        require(all(entry.get(role + '_evaluation') == evaluation['id']
                    for role, evaluation in evaluations.items()),
                'paired driver role identities differ from actual evaluations')
        require(isinstance(entry.get('compiler_resolved'), str)
                and Path(entry['compiler_resolved']).is_absolute()
                and artifacts.file_hash(entry['compiler_resolved']) == entry.get('compiler_sha256'),
                'paired study compiler is unavailable or changed')
        control = negative_control(samples, policy, sampling)
        gates.extend(pair['id'] + ': ' + reason for reason in control['unmet_gates'])
        result['pairs'].append({'pair': pair['id'], 'pair_sha256': artifacts.digest(pair),
            'first_evaluation': first['id'], 'samples': samples, **control,
            'evaluations': {role: {'id': row['id'], 'sha256': artifacts.digest(row),
                'context': copy.deepcopy(row['context']), 'build': copy.deepcopy(row['build']),
                'timing': copy.deepcopy(row['timing']), 'correctness': copy.deepcopy(row['correctness'])}
                for role, row in evaluations.items()}})
        identities.update({row['id']: artifacts.digest(row)
                           for row in (first, pair, machine, *evaluations.values())})
        primary[first['id']] = evaluations['baseline']
    require(all(item['evaluation']['id'] in primary for item in packets),
            'profile packages do not correspond to the prospective paired study')
    # Historical diagnostics remain attached to their actual five-trial primary.
    # The new complete paired grids alone supply prospective sampling readiness.
    result['selected_primary_evaluations'] = [primary[item['evaluation']['id']]['id'] for item in packets]
    result['state'] = 'qualified' if not any(row['unmet_gates'] for row in result['pairs']) else 'unqualified'
    return result, [primary[item['evaluation']['id']] for item in packets]
