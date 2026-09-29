"""Explicit admission of the fixed one-thread calibration. Created: 2026-09-26 ET.

Read-only qualification over an unchanged pinned collector checkout; no pilot,
provider, repair, or protocol execution. The publisher retains old defaults.
"""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from scripts import bfs_native_one_thread_pilot as driver
from scripts import bfs_paired_calibration as paired
from scripts import dx100_witness_continuation as terminal
from scripts.bfs_owned_execution import identity as reader_identity
from scripts.bfs_freeze_pilot import packet, require, sample_grid
from swdb import artifacts, bfs_native

COLLECTOR_COMMIT = '319645eab0a25c815fa03fe1c372d32b4ba45d10'
RUN_ID = 'bfs-native-one-thread-pilot-20260926-a1'
READBACK_SECONDS = 900
READBACK_CLEANUP_SECONDS = 30
PLAN_RELATIVE = '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-one-thread-pilot-20260926-a1.json'
HISTORICAL_PREPARE = {
    'receipt': {'path': '/data/yanruj/EvolveSWDB_runs/bfs-native-paired-review-20260926-a1/prepare-receipt.json',
                'sha256': '2cf5845cb0a908d7503d52796b89f1f2e712ddfbdb1274ecd6568a993f161a50'},
    'terminal_audit': {'path': '/data/yanruj/EvolveSWDB_runs/bfs-native-paired-review-20260926-a1/prepare-terminal-validation.json',
                       'sha256': '2deb2eaf3699e1c030e4e27d3413eaf14cd5677e71e3b99997b2a6dd0147534f'}}


def read(reference, maximum=32*1024**2):
    return json.loads(terminal.reference(reference, maximum))


def selection(spec):
    selected = spec['one_thread_calibration']
    require(isinstance(selected, dict) and set(selected) == {
        'run_id', 'code_commit', 'collector_checkout', 'driver_receipt', 'terminal_receipt',
        'packages', 'historical_paired_calibration'}, 'one-thread calibration selection has an unsupported shape')
    require(selected['run_id'] == RUN_ID and selected['code_commit'] == COLLECTOR_COMMIT,
            'one-thread calibration run/code differs from the fixed reviewed study')
    require(isinstance(selected['collector_checkout'], str) and Path(selected['collector_checkout']).is_absolute(),
            'one-thread reader requires its original absolute collector checkout')
    require(isinstance(selected['packages'], list) and len(selected['packages']) == len(set(selected['packages'])) == 4,
            'all four distinct fresh diagnostic packages are required')
    require(type(spec['maximum_relative_spread']) in (int, float) and spec['maximum_relative_spread'] == .10,
            'one-thread calibration keeps the fixed 0.10 spread ceiling')
    return selected


def historical_selection(spec, store):
    selected = selection(spec)
    old_spec = copy.deepcopy(spec)
    old_spec.pop('one_thread_calibration')
    old_spec['paired_calibration'] = copy.deepcopy(selected['historical_paired_calibration'])
    old = paired.historical_packets(old_spec, [], store)
    return old_spec, old


def historical_paired_control(spec, store, identities):
    """Preserve the sealed old metadata; never requalify it under newer code."""
    selected = selection(spec)['historical_paired_calibration']
    plan = json.loads(driver.PLAN.read_text()); driver.validate_plan(plan)
    old_path = driver.ROOT/plan['historical_plan']['path']
    require(artifacts.file_hash(old_path) == plan['historical_plan']['sha256'], 'historical paired plan changed')
    old_plan = json.loads(old_path.read_text())
    require(set(selected) == {'pairs', 'driver_receipt', 'historical_packages'}
            and selected['pairs'] == [cell['id'] for cell in old_plan['cells']],
            'historical paired selection must retain the exact four original cells')
    fixed_audit = plan['fixed_prerequisites']['paired']
    audit = read(fixed_audit)
    require(audit['driver'] == selected['driver_receipt'], 'historical driver differs from its fixed terminal audit')
    retained = read(selected['driver_receipt'])
    require(retained['state'] == 'complete' and [row['id'] for row in retained['cells']] == selected['pairs'],
            'historical paired driver lacks its complete original grid')
    for rid, digest in plan['historical_records'].items():
        record = store.get(rid)
        require(record and artifacts.digest(record) == digest, 'sealed historical paired record changed: '+rid)
        identities[rid] = digest
    sampling = {'repetitions': 10, 'warmups': 0, 'aggregation': 'geomean_source_median_ratio',
                'collection': old_plan['collection'], 'analysis': old_plan['analysis']}
    controls, gates = [], []
    for cell, entry in zip(old_plan['cells'], retained['cells']):
        pair = store.get(cell['id'], 'evaluation_pair')
        require(artifacts.digest(pair) == entry['pair_sha256'], 'historical pair differs from retained driver')
        members = {role: store.get(pair[role+'_evaluation'], 'evaluation') for role in ('baseline', 'candidate')}
        samples = {role: sample_grid(row, old_plan['sources'], 10) for role, row in members.items()}
        checked = paired.negative_control(samples, plan['profitability'], sampling)
        gates.extend(cell['id']+': '+reason for reason in checked['unmet_gates'])
        controls.append({'pair': pair['id'], 'pair_sha256': artifacts.digest(pair), **checked,
                         'samples': samples, 'evaluations': copy.deepcopy(members)})
    return {'control': {'state': 'unqualified' if gates else 'qualified', 'pairs': controls,
                       'sampling': sampling, 'gain_claim': False, 'driver_receipt': selected['driver_receipt'],
                       'retained_driver': retained, 'terminal_receipt': fixed_audit},
            'original_prepare_attempt': {key: {'reference': copy.deepcopy(ref), 'retained': read(ref)}
                                         for key, ref in HISTORICAL_PREPARE.items()},
            'unmet_gates': gates, 'admitted_for_new_sampling': False,
            'scope': 'sealed four-thread records and their fixed-policy statistics; preserved historical outcome, '
                     'not a new raw-artifact admission under the changed collector runtime'}


def terminal_closure(reference, driver_reference, receipt, current=None, proc=Path('/proc')):
    """Require the full completed node1 batch and its exact owned-process union."""
    current = current or datetime.now(timezone.utc)
    audit = read(reference)
    require(audit.get('id') == RUN_ID and audit.get('state') == 'complete'
            and audit.get('repository_commit') == COLLECTOR_COMMIT
            and audit.get('driver') == driver_reference and audit.get('lease_released') is True,
            'one-thread terminal audit is not bound to the completed fixed driver')
    lane = read(audit['lane'])['socket_lane']; exit_bytes = terminal.reference(audit['outer_exit'], 64).strip()
    generation = lane.get('lease_generation')
    require(type(generation) is int and generation > 0 and lane.get('host') == 'mbit10'
            and type(lane.get('node')) is int and lane['node'] == 1 and lane.get('lease_name') == driver.LANE
            and type(lane.get('exit_code')) is int and lane['exit_code'] == 0 and exit_bytes == b'0',
            'one-thread lane/outer completion differs')
    began, ended = terminal.stamp(receipt['started']), terminal.stamp(receipt['finished'])
    lane_begin, lane_end = terminal.stamp(lane['started_utc']), terminal.stamp(lane['ended_utc'])
    observed = terminal.stamp(audit['observed_at'])
    # The outer clock precedes entry to the helper. Helper stamps represent
    # whole-second intervals, while the retained outer/driver clocks are exact.
    outer_begin = terminal.stamp(receipt['outer_start'])
    require(outer_begin <= began <= ended < lane_end+timedelta(seconds=1)
            and outer_begin < lane_begin+timedelta(seconds=1) and lane_begin <= began
            and ended <= observed <= current and lane_end <= observed
            and lane_end < terminal.stamp(receipt['outer_end'])+timedelta(seconds=1)
            and receipt['lane']['verified_lane'] ==
                f'{driver.LANE} (verified: affinity, bind:1, lease held, generation {generation})',
            'one-thread terminal window/lane binding differs')
    lease = read(audit['lease_snapshot'])
    require(lease.get('state') == 'released' and type(lease['lease'].get('generation')) is int
            and lease['lease']['generation'] == generation
            and lease['lease']['lease_name'] == driver.LANE
            and lane_end <= terminal.stamp(lease['released_at']) <= observed,
            'one-thread lane release is unavailable')
    observations = receipt['process_observations']; ancestors = observations['ancestry']
    identity, pane = observations['driver_identity'], observations['pane_identity']
    def key(row):
        require(isinstance(row, dict) and type(row.get('pid')) is int and row['pid'] > 0
                and type(row.get('start_ticks')) is int and row['start_ticks'] >= 0,
                'one-thread owned identity is malformed')
        return row['pid'], row['start_ticks']
    require(ancestors and key(identity) == key(ancestors[0]) and identity['pid'] == receipt['driver_pid']
            and key(pane) == key(ancestors[-1])
            and all(row.get('parent_pid') == parent['pid'] for row, parent in zip(ancestors, ancestors[1:])),
            'one-thread terminal ancestry/pane binding differs')
    samples = [json.loads(line) for line in terminal.reference(receipt['rss']['samples'], 64*1024**2).splitlines() if line.strip()]
    require(samples and all(sample.get('processes') for sample in samples), 'one-thread terminal samples are absent')
    owned = ancestors + observations['owned_processes'] + [row for sample in samples for row in sample['processes']]
    owned += [stage['identity'] for stage in receipt['stages'] if stage.get('identity') is not None]
    owned += receipt.get('cleanup', {}).get('observed', [])
    owned += [row for stage in receipt['stages'] for row in stage.get('cleanup', {}).get('observed', [])]
    expected = {key(row) for row in owned}
    declared = audit.get('owned_processes', [])
    require(expected == {key(row) for row in declared}, 'one-thread terminal audit omits or adds owned identities')
    zombie = audit.get('cleanup_state') == 'terminal_no_live_owned_processes'
    require((zombie and audit.get('owned_processes_absent') is False and audit.get('owned_processes_nonrunning') is True)
            or (audit.get('cleanup_state') == 'terminal_and_reaped' and audit.get('owned_processes_absent') is True
                and all(row.get('state') == 'absent' for row in declared)),
            'one-thread audit does not establish terminal cleanup')
    terminal.verify_terminal_processes(declared, proc, launcher_identity=key(pane) if zombie else None)
    return {'audit': copy.deepcopy(reference), 'driver': copy.deepcopy(driver_reference),
            'cleanup_state': audit['cleanup_state'], 'lane': audit['lane'], 'lease_snapshot': audit['lease_snapshot'],
            'owned_processes': copy.deepcopy(declared), 'observed_at': audit['observed_at']}


def stop_reader(child, deadline):
    """Stop only the still-owned reader session within its remaining reserve."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if child.poll() is not None:
            return  # communicate/poll already reaped it; do not signal a numeric group.
        require(time.monotonic() < deadline, 'reader shutdown exhausted its cleanup deadline')
        try:
            require(os.getpgid(child.pid) == child.pid, 'reader no longer owns its declared session')
            os.killpg(child.pid, sig)
        except ProcessLookupError:
            return  # The separate unconditional wait handles disappearance.
        remaining = max(0, deadline-time.monotonic())
        allowance = min(20, max(0, remaining-5)) if sig == signal.SIGTERM else remaining
        try:
            child.wait(timeout=allowance)
            return
        except subprocess.TimeoutExpired:
            pass


def pinned_readback(selected, receipt, store, *, reader_observer=None):
    """Use the unmodified measured reader in its own pristine original checkout.

    Optional synchronous spawn/finished observations require Linux identities.
    Persist spawn before any reap, and finish inside the same cleanup deadline.
    Observation failures reject admission; they never change the stable result
    or replace an earlier reader error. Callback persistence time is charged.
    """
    start = time.monotonic(); work_end = start+READBACK_SECONDS
    hard_end = work_end+READBACK_CLEANUP_SECONDS
    require(reader_observer is None or callable(reader_observer), 'reader observer must be callable')
    checkout = Path(selected['collector_checkout'])
    require(checkout == checkout.resolve() and checkout.is_dir(), 'collector checkout is missing or symlinked')
    runtime = driver.runtime_identity(COLLECTOR_COMMIT, root=checkout)
    require(artifacts.digest(runtime) == artifacts.digest(receipt['runtime']), 'collector runtime inventory differs from measurement')
    plan = json.loads((checkout/PLAN_RELATIVE).read_text()); driver.validate_plan(plan)
    # Exact reviewed code only; this invokes admission, not the collector main.
    program = ('import json,sys; from pathlib import Path; from scripts import bfs_native_one_thread_pilot as d; '
               'from swdb.store import Store; from swdb import yamlio; '
               'v=json.loads(sys.argv[1]); '
               'r=d.validate_driver_receipt(v["driver"],yamlio.load(d.PLAN),Store(Path(v["records"])),v["commit"]); '
               'print(json.dumps(r,sort_keys=True,allow_nan=False))')
    payload = {'driver': selected['driver_receipt'], 'records': str(Path(store.dir).resolve()), 'commit': COLLECTOR_COMMIT}
    command = [runtime['python']['path'], '-c', program, json.dumps(payload, sort_keys=True)]
    env = dict(os.environ)
    for name, value in driver.PYTHON_INPUTS.items():
        if value is None: env.pop(name, None)
        else: env[name] = value
    remaining = work_end-time.monotonic()
    require(remaining > 0, 'one-thread readback preflight exhausted its total allowance')
    child = subprocess.Popen(command, cwd=checkout, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    error, cleanup_error, identity = None, None, None
    try:
        if reader_observer is not None:
            # A fast exited child is still identifiable while it is unreaped.
            # Capture and persist before communicate/poll can discard that PID.
            identity = reader_identity(child.pid)
            require(identity is not None and identity['pid'] == child.pid
                    and identity['parent_pid'] == os.getpid()
                    and type(identity.get('start_ticks')) is int and identity['start_ticks'] >= 0,
                    'reader spawn identity is unavailable')
            reader_observer({'event': 'spawn', 'identity': copy.deepcopy(identity),
                'observed_at': datetime.now(timezone.utc).isoformat(),
                'work_deadline_monotonic': work_end, 'hard_deadline_monotonic': hard_end})
        remaining = work_end-time.monotonic()
        require(remaining > 0, 'reader startup exhausted its work allowance')
        stdout, stderr = child.communicate(timeout=remaining)
        require(child.returncode == 0 and len(stdout) <= 8*1024**2 and len(stderr) <= 1024**2,
                'pinned one-thread reader failed: ' + stderr[:2048].decode(errors='replace'))
    except BaseException as exc:
        error = exc
    finally:
        cleanup_start = time.monotonic()
        cleanup_end = min(hard_end, cleanup_start+READBACK_CLEANUP_SECONDS)
        try:
            stop_reader(child, cleanup_end)
        except BaseException as exc:
            cleanup_error = exc
        # Even denied signals or identity races cannot skip the direct wait.
        try:
            child.wait(timeout=max(0, cleanup_end-time.monotonic()))
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        finally:
            for stream in (child.stdout, child.stderr):
                try:
                    if stream is not None: stream.close()
                except BaseException as exc:
                    cleanup_error = cleanup_error or exc
        if reader_observer is not None:
            try:
                require(time.monotonic() <= cleanup_end, 'reader observation exhausted its cleanup deadline')
                reader_observer({'event': 'finished', 'identity': copy.deepcopy(identity),
                    'pid': child.pid, 'returncode': child.returncode,
                    'direct_reaped': child.returncode is not None,
                    'observed_at': datetime.now(timezone.utc).isoformat(),
                    'cleanup_started_monotonic': cleanup_start,
                    'cleanup_deadline_monotonic': cleanup_end,
                    'cleanup_elapsed_before_event_seconds': time.monotonic()-cleanup_start,
                    'hard_deadline_monotonic': hard_end,
                    'original_error': None if error is None else f'{type(error).__name__}: {error}',
                    'cleanup_error': None if cleanup_error is None else f'{type(cleanup_error).__name__}: {cleanup_error}'})
                require(time.monotonic() <= cleanup_end, 'reader observation exceeded its cleanup deadline')
            except BaseException as exc:
                cleanup_error = cleanup_error or exc
    if error is not None:
        raise error from cleanup_error
    if cleanup_error is not None:
        raise cleanup_error
    result = json.loads(stdout)
    require(result.get('state') == 'complete' and result.get('qualified') is True
            and result.get('gain_claim') is False and result.get('driver') == selected['driver_receipt'],
            'one-thread primary/diagnostic study did not qualify')
    # Stable values only: prepare/publish independently revalidate the same review.
    evidence = {'code_commit': COLLECTOR_COMMIT, 'checkout': str(checkout), 'result': result,
        'stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
        'work_seconds': READBACK_SECONDS, 'cleanup_seconds': READBACK_CLEANUP_SECONDS}
    require(time.monotonic() <= hard_end, 'one-thread readback finalization exceeded its total allowance')
    return plan, evidence


def qualify(spec, packets, store, identities, gates, *, reader_observer=None):
    selected = selection(spec); receipt = read(selected['driver_receipt'])
    require(receipt.get('id') == RUN_ID and receipt.get('repository_commit') == COLLECTOR_COMMIT
            and receipt.get('state') == 'complete' and receipt.get('primary_qualified') is True
            and receipt.get('gain_claim') is receipt.get('protocol_freeze') is receipt.get('provider_calls') is False,
            'one-thread study is incomplete, unqualified, or from another code pin')
    closure = terminal_closure(selected['terminal_receipt'], selected['driver_receipt'], receipt)
    if reader_observer is None:
        plan, readback = pinned_readback(selected, receipt, store)
    else:
        plan, readback = pinned_readback(selected, receipt, store, reader_observer=reader_observer)
    require([row.get('id') for row in receipt.get('cells', [])] == [cell['id'] for cell in plan['cells']],
            'one-thread primary grid differs from its four fixed cells')
    require(selected['packages'] == [row['id'] for row in receipt['diagnostics']], 'fresh diagnostic package order differs')
    all_packets = [packet(store, rid) for rid in selected['packages']]
    require([item['evaluation']['id'] for item in all_packets] == [cell['baseline_evaluation'] for cell in plan['cells']]
            and {item['package']['id'] for item in packets} <= set(selected['packages']),
            'selected freeze packages are not the fixed fresh one-thread baselines')
    control = {'state': 'qualified', 'pairs': [], 'gain_claim': False,
        'sampling': {'repetitions': 10, 'warmups': 0, 'aggregation': 'geomean_source_median_ratio',
                     'collection': copy.deepcopy(plan['collection']), 'analysis': plan['analysis']},
        'native_runtime': copy.deepcopy(plan['native_runtime']), 'driver_receipt': copy.deepcopy(selected['driver_receipt']),
        'terminal_closure': closure, 'pinned_readback': readback,
        'fresh_diagnostics': [], 'selected_primary_evaluations': [item['evaluation']['id'] for item in packets],
        'scope': 'fixed one-thread baseline A/A and fresh diagnostics; no candidate gain or nominal interval-coverage claim'}
    for cell, entry, item in zip(plan['cells'], receipt['cells'], all_packets):
        pair = store.get(cell['id'], 'evaluation_pair')
        require(pair and artifacts.digest(pair) == entry['pair_sha256'], 'one-thread pair changed after pinned readback')
        evaluated = {role: store.get(cell[role+'_evaluation'], 'evaluation') for role in ('baseline', 'candidate')}
        for role, evaluation in evaluated.items():
            require(evaluation and artifacts.digest(evaluation) == entry['members'][role]['sha256'],
                    'one-thread member changed after pinned readback')
            identities[evaluation['id']] = artifacts.digest(evaluation)
        checked = paired.negative_control(entry['samples'], plan['profitability'], control['sampling'])
        require(artifacts.digest(checked) == artifacts.digest(entry['control']), 'one-thread control changed after pinned readback')
        gates.extend(cell['id'] + ': ' + reason for reason in checked['unmet_gates'])
        control['pairs'].append({'pair': pair['id'], 'pair_sha256': artifacts.digest(pair), **checked,
                                 'evaluations': evaluated, 'samples': copy.deepcopy(entry['samples'])})
        identities[pair['id']] = artifacts.digest(pair); identities.update(item['record_identities'])
        control['fresh_diagnostics'].append({'package': item['package']['id'], 'evaluation': item['evaluation']['id'],
            'region_profile': item['diagnostic']['id'], 'record_identities': copy.deepcopy(item['record_identities']),
            'scope': 'fresh one-thread diagnostics; never substituted for primary timing'})
    if any(pair['unmet_gates'] for pair in control['pairs']): control['state'] = 'unqualified'
    return control, [item['evaluation'] for item in packets]


def calibrated_runtime(control):
    policy = bfs_native.validate_runtime_policy(control['native_runtime'], 1)
    evaluations = [row for pair in control['pairs'] for row in pair['evaluations'].values()]
    require(len(evaluations) == 8, 'one-thread runtime requires all eight actual members')
    for row in evaluations:
        observed = bfs_native.validate_runtime_policy(row['build'].get('native_runtime'), 1)
        require(artifacts.digest(observed) == artifacts.digest(policy)
                and artifacts.digest(row['build'].get('execution_environment')) == artifacts.digest(bfs_native.controlled_environment(1)),
                'one-thread member runtime differs from the admitted policy')
    return copy.deepcopy(policy), {'basis': 'explicit requested runtime inputs in all eight newly measured members',
        'evaluations': [row['id'] for row in evaluations], 'driver_receipt': control['driver_receipt'],
        'terminal_closure': control['terminal_closure']['audit'], 'collector_commit': COLLECTOR_COMMIT}
