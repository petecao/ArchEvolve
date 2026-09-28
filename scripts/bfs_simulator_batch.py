#!/usr/bin/env python3
"""Finite sequential simulator-series coordination. Created: 2026-09-26 ET.
Updated 2026-09-27 ET (R2/R3): the T15 pilot kind runs one family per driver,
two drivers inside one lane job, sharing a one-slot gem5 pool, the lane-tree
52-GiB sampled RSS cap and one 96-GiB aggregate storage allowance.
Updated 2026-09-27 ET (T16 b1): the same incremental one-lane shape serves the
T16 reference kind (one driver per series); frozen protocols may fix one replay
(R11), one MAA series may bind both protocols (R10), and an opt-in atomic
post-ROI verifier continuation (R12) is passed to every execution.

No evaluator, retries, protocol publication, provider calls, or gain decisions.
Run only under socket_lane.sh and a matching external timeout.
"""
import argparse
import ctypes
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import signal
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_process import interruption_signals, save_receipt
from scripts import bfs_owned_execution as lifecycle
from scripts.bfs_native_paired_pilot import DescendantRSS
from scripts import bfs_dx100_coverage_execution as coverage_case
from scripts import dx100_witness_continuation as witness_case
from scripts.bfs_simulator_series import admit_capacity, validate_diagnostic_build, validate_selection
from swdb import artifacts, bfs_coverage, bfs_protocol, profile, profile_package, yamlio
from swdb.store import Store

ET = ZoneInfo('America/New_York')
GIB = 1024**3
PLAN_HASHES = {'t16-reference': 'a6749593b06e983f6c13bc11940a5e0da37f2551f0271ec1cb912a2a0f7785ca', 't17-t20-routes': '29d4adf356147e932a0c5654d0b447c7cfd4839b709c590c4313eb97fa1ca06f', 't15-pilot-b3': '85b0b76901b008b28fcce1da0245e98f4904ca8ee3a97edf4da1dc78397c4368', 't15-pilot-b2': '0545e3f47fa09feabd673fa1d4a69fb8326abe2691535e1b0dffab29ed3da3be', 't15-pilot': 'f515581f5ff0bc933a93eff3ad8e93b0dfcf58a960606c16f1505ca9fb878f8a', 't16-protocol-recovery': 'eb0d62b55afc0c3632ef264ee0ed916d14792ac27836debcb2718048e8b226a8', 't16-seal-recovery': '5d60f36a9fcea96aed9f1f491d6ad9275a3219b1e9798fc9ad41cccd0640a7db', 't15-lease-recovery': '6798cbc9396a26e178ac1dbb9c631a4fa2dac4b6705751424b301a9dedb93a01', 't16-lease-recovery': 'ea1ecabb42854562bbc243b84f6afaab234597e4475e8013c80f887c5c53832a', 't15-supervision-recovery': '5c3a7cbfd0498ff746ddd635bb4fc11f6e4cbf555ff957af1a56248a70bb6ea6', 't16-supervision-recovery': '1400c0572527e913c64e858d13ac0edbc7eda2f5925daa66f651a9ca49036825', 't15-setup-recovery': '8efb0d32c076280a936ec4da0945c9b0653e3128e41389a3fc3965e86522725e', 't15': 'bec894d3c21400617aa5b02afd9e97fcb104e11da1c1e52d43355aa10d788833', 't16': '8485d6ad0ca8708d9ef4d3342676748a5e39bc421d0a30d262fe2bff2f7c457e', 't15-correction': '4bc526b7aa86ff09499a6478f7068319357789ca27fedb58a011d5b75937b7ea'}
PILOT_KIND = 't15-pilot'
PILOT_ID = 'bfs-t15-pilot-simulator-batch-20260927-b1'
# 2026-09-27: b1 failed its first-pair 120-s profile gate; b2 is the fresh relaunch.
PILOT_PLANS = {PILOT_KIND: PILOT_ID, 't15-pilot-b2': 'bfs-t15-pilot-simulator-batch-20260927-b2',
               't15-pilot-b3': 'bfs-t15-pilot-simulator-batch-20260927-b3'}
PILOT_POLICY = 't15_incremental_allocation.v1'
T16_KIND = 't16-reference'
T16_ID = 'bfs-t16-reference-simulator-batch-20260927-b1'
T16_POLICY = 't16_incremental_allocation.v1'
# Incremental one-lane allocations: policy -> (kind, plan ID, flat preparation row).
# 2026-09-28: T17/T20 controlled-simulator routes reuse the pilot lane-job design;
# rows carry a driver `group` and retained primary builds instead of author binaries.
ROUTES_KIND = 't17-t20-routes'
ROUTES_ID = 'bfs-t17-t20-routes-simulator-batch-20260928-a1'
ROUTES_POLICY = 'routes_incremental_allocation.v1'
INCREMENTAL = {PILOT_POLICY: (PILOT_KIND, PILOT_ID, 'bfs-t15-pilot-preparation-20260927-b1'),
               ROUTES_POLICY: (ROUTES_KIND, ROUTES_ID, 'bfs-t17-t20-routes-preparation-20260928-a1'),
               T16_POLICY: (T16_KIND, T16_ID, 'bfs-t16-reference-preparation-20260927-b1')}
PILOT_TEST_CASES = {
    'owned_cleanup': {
        'test_linux_owned_stage_reaps_detached_child[False]',
        'test_linux_owned_stage_reaps_detached_child[True]',
        'test_linux_nested_interruption_uses_one_cleanup_budget',
        'test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve',
        'test_linux_storage_observation_handles_sqlite_journal_unlink',
        'test_linux_gem5_slot_is_released_by_child_not_parent'},
    'dx100_interruption': {'test_public_interruption_is_durable_before_postmortem[raises]',
                           'test_public_interruption_is_durable_before_postmortem[stalls]'}}
SETUP_RECOVERY_ID = 'bfs-t15-setup-recovery-simulator-batch-20260926-a1'
SETUP_FAILURE_ID = 'bfs-t15-correction-simulator-batch-20260926-a1'
SETUP_HARD_END = '2026-09-27T09:14:09.851819-04:00'
PLAN_DIR = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests'
RAW_ROOTS = (Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))
BUILD_ROOT = Path('/data1/yanruj/EvolveSWDB_builds')
CLEANUP_RUNTIME = ('scripts/bfs_simulator_batch.py', 'scripts/bfs_simulator_series.py',
                   'scripts/bfs_owned_execution.py', 'scripts/bfs_owned_rss.py', 'scripts/bfs_process.py',
                   'scripts/bfs_storage.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def now():
    return datetime.now(ET)


def stamp(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'clock timestamp needs its time zone')
    return result


def read_reference(ref, maximum=2 * 1024**2):
    path = Path(ref['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'missing or unsafe admission reference')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum and hashlib.sha256(raw).hexdigest() == ref['sha256'],
            'admission reference changed or exceeded its read bound')
    return json.loads(raw)


def validate_plan(plan, kind):
    require(artifacts.digest(plan) == PLAN_HASHES[kind], 'prospective plan differs from the reviewed fixed scope')


def is_pilot(plan):
    """True for every incremental one-lane allocation (T15 pilot, T16 reference)."""
    return plan.get('allocation', {}).get('policy') in INCREMENTAL


def plan_path(kind):
    if kind in PILOT_PLANS:
        return PLAN_DIR / (PILOT_PLANS[kind] + '.json')
    for plan_kind, plan_id, _ in INCREMENTAL.values():
        if kind == plan_kind:
            return PLAN_DIR / (plan_id + '.json')
    date = '20260927' if kind in {'t15-lease-recovery', 't16-lease-recovery', 't16-seal-recovery', 't16-protocol-recovery'} else '20260926'
    return PLAN_DIR / f'bfs-{kind}-simulator-batch-{date}-a1.json'


def pilot_storage_paths(plan):
    """The whole incremental allocation: both family roots and the lane dispatch."""
    base = Path(plan['raw_root']) / plan['id']
    return [base, Path(str(base) + '.dispatch')]


def validate_pilot_tests(plan, admission):
    """Fresh Linux ownership/interruption tests at the exact admitted runtime (R9)."""
    import xml.etree.ElementTree as XML
    refs = admission['linux_cleanup_tests']
    require(isinstance(refs, list) and len(refs) == 2, 'two pilot Linux test receipts are required')
    seen = set()
    for ref in refs:
        result = read_reference(ref)
        kind = result.get('kind')
        require(kind in PILOT_TEST_CASES and kind not in seen
                and result.get('format') == 'swdb.bfs.pilot-linux-tests.v1'
                and result.get('host') == 'mbit10' and result.get('platform') == 'linux'
                and result.get('code_commit') == admission['code_commit']
                and result.get('runtime_sha256') == admission['runtime_sha256']
                and type(result.get('returncode')) is int and result['returncode'] == 0
                and stamp(result['started']) <= stamp(result['finished']) <= stamp(admission['prepared_at']),
                'pilot Linux test receipt is missing, failed or differs from this runtime')
        seen.add(kind)
        junit = result['junit']; path = Path(junit['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and path.stat().st_size <= 4*1024**2 and artifacts.file_hash(path) == junit['sha256'],
                'pilot Linux JUnit changed')
        cases = XML.fromstring(path.read_bytes()).findall('.//testcase')
        require(cases and all(not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped'))
                for case in cases) and PILOT_TEST_CASES[kind] <= {case.get('name') for case in cases},
                'pilot Linux tests omit required cases or contain failures/skips')
    require(seen == set(PILOT_TEST_CASES), 'both pilot Linux test receipts are required')


def runtime_identity():
    suffixes = {'.py', '.cc', '.cpp', '.h', '.hpp', '.json', '.yaml', '.sh'}
    result = {str(path.relative_to(ROOT)): artifacts.file_hash(path)
            for name in ('swdb', 'scripts', 'schemas', 'vocab')
            for path in sorted((ROOT / name).rglob('*')) if path.is_file() and path.suffix in suffixes}
    result.update({name: artifacts.file_hash(ROOT/name) for name in
                   ('tests/test_bfs_owned_execution.py', 'tests/test_dx100_interruption.py',
                    'tests/test_bfs_owned_rss.py', 'tests/test_bfs_linux_fixture_audit.py',
                    'tests/test_bfs_simulator_batch.py', 'tests/test_dx100_witness.py')})
    return result


def allocated_bytes(paths):
    from scripts.bfs_storage import allocated_bytes as observe_allocation
    return observe_allocation(paths)


def batch_storage_paths(runs):
    """Charge the exact raw root and its wrapper sibling once (2026-09-26)."""
    runs = Path(runs)
    dispatch = Path(str(runs) + '.dispatch')
    paths = [runs, dispatch]
    require(all(path.is_absolute() and path == path.resolve() and path.is_dir()
                and not path.is_symlink() for path in paths),
            'batch storage requires canonical raw and exact .dispatch directories')
    require(not runs.samefile(dispatch), 'batch storage roots must be distinct')
    return paths


def failed_batch_charge(entry):
    """Retain a closed failed attempt in a separately fixed correction (2026-09-26).

    Reuse the original terminal readers; failure is a charge, never a completed
    prerequisite or permission to resume its IDs. The plan pins every reference.
    """
    from scripts import bfs_simulator_batch_terminal as terminal
    driver = read_reference(entry['driver'], maximum=16 * 1024**2)
    lane = read_reference(entry['lane'])['socket_lane']
    require(driver.get('id') == entry['id'] and driver.get('state') == 'failed'
            and type(lane.get('exit_code')) is int and lane['exit_code'] != 0,
            'retained failed batch is not a closed failed execution')
    require(not driver.get('plan', {}).get('accounting', {}).get('retained_failed_batches'),
            'nested corrective attempts are not authorized')
    observed = now().isoformat()
    terminal.validate_cleanup_ledger(entry['driver'], entry['cleanup_ledger'],
        expected_run_id=entry['id'], expected_outer_start=driver['outer_started'],
        expected_deadline=driver['outer_deadline'], current=observed)
    storage = terminal.validate_storage_accounting(entry['driver'], entry['terminal'], current=observed)
    audit = read_reference(entry['terminal'], maximum=16 * 1024**2)
    dispatch = Path(storage['storage_paths'][1])
    require(Path(entry['lane']['path']) == dispatch/'lane.json'
            and all(audit.get('lane', {}).get(key) == entry['lane'][key] for key in ('path', 'sha256'))
            and lane.get('job') == entry['id'] and lane.get('host') == 'mbit10'
            and lane.get('lease_generation') == audit.get('lease_generation'),
            'failed batch helper differs from the independently closed lane')
    require(storage['storage_paths'] == entry['storage_paths']
            and type(entry['retained_bytes']) is int and entry['retained_bytes'] > 0
            and storage['raw_bytes'] == entry['retained_bytes'],
            'closed failed batch storage changed after independent closure')
    start, finish = stamp(lane['started_utc']), stamp(lane['ended_utc'])
    outer, completed = stamp(driver['outer_started']), stamp(driver['finished'])
    require(outer < start + timedelta(seconds=1) and start <= stamp(driver['started'])
            and outer <= completed < finish + timedelta(seconds=1)
            and start <= finish <= stamp(observed), 'failed batch helper and original clock disagree')
    closed = stamp(entry['closed_at'])
    require(completed <= stamp(audit['observed_at']) <= closed <= stamp(observed),
            'failed batch closure endpoint precedes its independent readback')
    # Whole-second helper endpoints undercount by up to one second. Include the
    # full outer execution and finalization, not only its child-stage duration.
    seconds = math.ceil(max((finish+timedelta(seconds=1)-outer).total_seconds(),
                            (closed-outer).total_seconds()))
    return {'id': entry['id'], 'elapsed_seconds': seconds, 'raw_bytes': storage['raw_bytes']}


def setup_failure_charges(plan):
    """The one fixed pre-guest failure is a flat cost, never a retry tree."""
    from scripts import bfs_simulator_batch_terminal as terminal
    entry = plan['accounting']['retained_setup_failure']
    require(plan['id'] == SETUP_RECOVERY_ID and entry['id'] == SETUP_FAILURE_ID,
            'only the fixed setup recovery lineage is supported')
    driver = read_reference(entry['driver'], maximum=16*1024**2)
    old_plan = driver['plan']; validate_plan(old_plan, 't15-correction')
    require(driver.get('id') == SETUP_FAILURE_ID and driver.get('state') == 'failed'
            and driver.get('code_commit') == entry['code_commit']
            and driver.get('outer_deadline') == entry['absolute_end'] == SETUP_HARD_END
            and plan.get('clock_policy') == {'method':'original_absolute_end_clamp.v1',
                                           'absolute_end':SETUP_HARD_END}
            and 'retained_setup_failure' not in old_plan['accounting'],
            'setup recovery differs from the exact consumed attempt and original end')
    approval = read_reference(entry['admission'])
    require(driver.get('admission') == entry['admission']
            and approval.get('plan_sha256') == artifacts.digest(old_plan)
            and approval.get('code_commit') == entry['code_commit'],
            'setup recovery prior admission binding differs')
    # Reopen every old proof and audit before retaining its full, nonrefundable
    # reservation. The old plan has only the original failed batch, not this one.
    validate_cleanup_tests(approval)
    validate_preparation_reservation(old_plan, approval)
    prior = preparation_charges(old_plan)
    require(prior == entry['prior_charges']
            and approval.get('preparation_charges') == prior
            and driver.get('preparation_charges') == prior,
            'setup recovery prior flat charges changed')
    reserved = old_plan['accounting']['preparation_reservation']
    old_proof = {key:reserved[key] for key in ('id','elapsed_seconds','raw_bytes')}
    require(old_proof == entry['prior_proof_charge'] and old_proof in prior,
            'setup recovery omits or refunds the consumed proof reservation')
    observed = now().isoformat()
    terminal.validate_cleanup_ledger(entry['driver'], entry['cleanup_ledger'],
        expected_run_id=SETUP_FAILURE_ID, expected_outer_start=driver['outer_started'],
        expected_deadline=SETUP_HARD_END, current=observed)
    storage = terminal.validate_storage_accounting(entry['driver'],entry['terminal'],current=observed)
    audit = read_reference(entry['terminal'], maximum=16*1024**2)
    require(all(audit.get('driver',{}).get(k) == entry['driver'][k] for k in ('path','sha256'))
            and audit.get('state') == 'failed' and audit.get('lease_released') is True,
            'setup recovery lacks exact independent failed closure')
    lane_ref = audit['lane']; lane = read_reference(lane_ref)['socket_lane']
    dispatch = Path(storage['storage_paths'][1])
    require(Path(lane_ref['path']) == dispatch/'lane.json'
            and lane.get('job') == SETUP_FAILURE_ID and lane.get('host') == 'mbit10'
            and lane.get('lease_generation') == audit.get('lease_generation')
            and type(lane.get('exit_code')) is int and lane['exit_code'] != 0
            and storage['storage_paths'] == entry['storage_paths']
            and storage['raw_bytes'] == entry['retained_bytes'],
            'setup failure lane or final retained bytes changed')
    outer, finished, closed = map(stamp,(driver['outer_started'],driver['finished'],entry['closed_at']))
    lane_start,lane_end = stamp(lane['started_utc']),stamp(lane['ended_utc'])
    require(outer < lane_start+timedelta(seconds=1) and lane_start <= stamp(driver['started'])
            and outer <= finished < lane_end+timedelta(seconds=1)
            and lane_end <= closed <= stamp(observed)
            and finished <= stamp(audit['observed_at']) <= closed,
            'setup failure clock or final closure endpoint changed')
    seconds = math.ceil(max((lane_end+timedelta(seconds=1)-outer).total_seconds(),
                            (closed-outer).total_seconds()))
    require(seconds == entry['elapsed_seconds'], 'setup failure whole-envelope charge changed')
    # Exact public record, first grid position, and on-disk leaf establish a
    # setup failure. A later failed checkpoint/simulation is not this exception.
    record_path = Path(entry['evaluation']['path'])
    require(record_path.is_absolute() and record_path == record_path.resolve()
            and not record_path.is_symlink() and artifacts.file_hash(record_path) == entry['evaluation']['sha256'],
            'setup failure public record changed')
    value = yamlio.load(record_path)
    row = old_plan['series'][0]; evaluation_id = row['id']+'.s0.r0.primary.evaluation'
    request = value.get('request',{})
    require(value.get('id') == evaluation_id and request.get('id') == evaluation_id
            and value.get('evidence_kind') == 'execution' and request.get('fixture') is not True
            and value.get('outcome') == {'state':'interrupted','stage':'execution_identity','reason':'interrupted by SIGTERM'}
            and value.get('timing') == [] and value.get('correctness') == {'state':'unverified','checks':[]}
            and len(value.get('stages',[])) == 1
            and value['stages'][0].get('stage') == 'execution_identity'
            and value['stages'][0].get('state') == 'interrupted'
            and request.get('candidate') == row['candidate']
            and request.get('build_evaluation') == old_plan['model_build']
            and request.get('configuration') == row['configuration']
            and request.get('workload',{}).get('id') == row['workload']
            and request.get('workload',{}).get('source') == row['sources'][0]
            and request.get('protocol_trial') == {'source_position':0,'repetition':0}
            and request.get('verification') == {'checker':old_plan['verifier'],
                'max_ticks':old_plan['verification_ticks'],'coverage':True,
                'post_roi_trace':'SyscallBase','trace_transport':old_plan['trace_transport']}
            and not any(k in request for k in ('checkpoint_manifest','checkpoint_evaluation','protocol','candidate_build')),
            'retained failure is not the exact pre-guest first public call')
    runs = Path(storage['storage_paths'][0]); leaf = runs/row['id']/evaluation_id
    require(leaf.is_dir() and not leaf.is_symlink() and leaf == leaf.resolve()
            and {p.name for p in leaf.iterdir()} == {'host-observation.json'},
            'setup failure has checkpoint, simulation or other guest artifacts')
    host_ref = value.get('context',{}).get('host_observation',{})
    require(host_ref.get('path') == str(leaf/'host-observation.json'), 'setup failure host observation path differs')
    read_reference(host_ref)
    raw = value.get('raw_artifacts',[])
    require(len(raw) == 2 and {r.get('kind') for r in raw} == {'dx100_execute','host_observation'}
            and next(r for r in raw if r['kind']=='dx100_execute').get('path') == str(leaf)
            and next(r for r in raw if r['kind']=='host_observation').get('sha256') == host_ref['sha256'],
            'setup failure raw evidence differs')
    related = sorted(record_path.parent.glob(SETUP_FAILURE_ID+'*.yaml'))
    require(related == [record_path] and len(driver.get('series',[])) == 1
            and driver['series'][0].get('id') == row['id'] and driver['series'][0].get('state') == 'failed',
            'setup recovery contains another public execution or series')
    require(not any(p.is_dir() and p.name in {'checkpoint','simulation'} for p in runs.rglob('*')),
            'setup recovery contains a checkpoint or simulation directory')
    return [old_proof, {'id':entry['id'],'elapsed_seconds':seconds,'raw_bytes':storage['raw_bytes']}]


def preparation_charges(plan):
    """Reopen the fixed retained preparation; caller-supplied credits are forbidden."""
    if is_pilot(plan):
        # Earlier attempts inside the same approved allocation are flat charges
        # whose closed storage is recounted; they are never resumed.
        rows = []
        for entry in plan['accounting'].get('retained_attempts', []):
            require(allocated_bytes(entry['storage_paths']) == entry['raw_bytes'],
                    'retained pilot attempt storage changed after closure')
            rows.append({key: entry[key] for key in ('id', 'elapsed_seconds', 'raw_bytes')})
        reserved = plan['accounting']['preparation_reservation']
        rows.append({key: reserved[key] for key in ('id', 'elapsed_seconds', 'raw_bytes')})
        require(len({row['id'] for row in rows}) == len(rows), 'pilot charges repeat an attempt')
        return rows
    if 'supervision_recovery' in plan['accounting'] or 'lease_recovery' in plan['accounting']:
        from scripts.bfs_simulator_recovery import preparation_charges as recovery_charges
        return recovery_charges(plan)
    rows = []
    for entry in plan['accounting']['preparation']:
        driver, wrapped = read_reference(entry['driver']), read_reference(entry['lane'])
        lane = wrapped['socket_lane']
        require(driver.get('id') == entry['id'] and driver.get('state') == 'complete'
                and lane.get('exit_code') == 0, 'charged preparation did not complete')
        stage_seconds = sum(stage['host_wall_s'] for stage in driver['stages'])
        duration = (stamp(lane['ended_utc']) - stamp(lane['started_utc'])).total_seconds()
        require(math.isfinite(stage_seconds) and stage_seconds >= 0 and duration >= 0,
                'preparation cost is malformed')
        # Helper timestamps truncate seconds: charge the conservative upper edge.
        seconds = math.ceil(max(stage_seconds, duration + 1))
        raw_bytes = allocated_bytes(entry['storage_paths'])
        if 'closed_envelope' in entry:
            envelope = entry['closed_envelope']
            preflight = read_reference(envelope['preflight'])
            audit = read_reference(envelope['terminal'], maximum=16 * 1024**2)
            start, end = stamp(envelope['started']), stamp(envelope['finished'])
            require(start == stamp(preflight['observed_at'])
                    and start <= stamp(driver['started']) <= stamp(driver['finished'])
                    <= stamp(audit['observed_at']) <= end <= now(),
                    'preparation closure envelope differs from retained execution')
            require(audit.get('id') == entry['id'] and audit.get('state') == 'complete'
                    and audit.get('lease_released') is True
                    and audit.get('cleanup_state') in {'terminal_and_reaped','terminal_no_live_owned_processes'}
                    and all(audit.get('driver', {}).get(key) == entry['driver'][key]
                            and audit.get('lane', {}).get(key) == entry['lane'][key]
                            for key in ('path', 'sha256')),
                    'preparation envelope lacks matching independent closure')
            require(type(envelope['retained_bytes']) is int and envelope['retained_bytes'] == raw_bytes,
                    'preparation storage changed after its final read-only count')
            seconds = max(seconds, math.ceil((end-start).total_seconds()))
        rows.append({'id': entry['id'], 'elapsed_seconds': seconds, 'raw_bytes': raw_bytes})
    retained = plan['accounting'].get('retained_failed_batches', [])
    require(len(retained) <= 1, 'only one separately planned corrective attempt is authorized')
    rows.extend(failed_batch_charge(entry) for entry in retained)
    if 'retained_setup_failure' in plan['accounting']:
        rows.extend(setup_failure_charges(plan))
    reservation = plan['accounting'].get('preparation_reservation')
    if reservation is not None:
        require(all(type(reservation.get(key)) is int and reservation[key] > 0
                    for key in ('elapsed_seconds', 'raw_bytes')), 'invalid fixed preparation reservation')
        rows.append({key: reservation[key] for key in ('id', 'elapsed_seconds', 'raw_bytes')})
    require(len({row['id'] for row in rows}) == len(rows), 'preparation charges repeat an execution')
    return rows


def validate_preparation_reservation(plan, admission):
    """Charge the full prospectively fixed Linux-proof allowance, with no refund.

    Actual proof hashes are sealed later in admission, avoiding a code/plan/proof
    hash cycle. Their complete closed envelopes must fit the fixed reservation.
    """
    if is_pilot(plan):
        # The incremental allocation reserves its 3,600 preparation seconds and
        # 4-GiB overhead as one flat row; it carries no historical proof group.
        reserved = plan['accounting']['preparation_reservation']
        known = set(PILOT_PLANS.values()) | {plan_id for _, plan_id, _ in INCREMENTAL.values()}
        require(plan['id'] in known and reserved == {'id': plan['id'].replace('-simulator-batch-', '-preparation-'), 'elapsed_seconds': 3600,
                             'raw_bytes': 4 * GIB} and 'preparation_reservation' not in admission,
                'pilot preparation reservation differs from the approved partition')
        return
    if {'lease_recovery', 'seal_recovery', 'protocol_recovery'} & plan['accounting'].keys():
        require('linux_proof_runtime' not in admission and 'linux_proof_provenance' not in plan,
                'recovery requires exact current-runtime Linux proof without consumer exceptions')
    reserved = plan['accounting'].get('preparation_reservation')
    if reserved is None:
        require('preparation_reservation' not in admission, 'unplanned preparation reservation')
        return
    if 'linux_proof_provenance' in plan:
        from scripts.bfs_simulator_recovery import PROOF_PROVENANCE, proof_admission
        require(plan['linux_proof_provenance'] == PROOF_PROVENANCE
                and 'linux_proof_runtime' in admission, 'explicit fixed Linux proof provenance is required')
        admission = proof_admission(admission)
    actual = admission['preparation_reservation']
    paths = [Path(path) for path in reserved['storage_paths']]
    require(len(paths) == len(set(paths)) == 5 and all(path.is_absolute() and path == path.resolve()
            and path.is_dir() and not path.is_symlink() for path in paths),
            'preparation reservation requires exact canonical output roots')
    group = paths[-1]
    require(group.name == reserved['id']+'.dispatch'
            and Path(actual['preflight']['path']) == group/'preflight.json',
            'preparation preflight is outside its fixed accounting root')
    preflight = read_reference(actual['preflight'])
    start, end = stamp(preflight['observed_at']), stamp(actual['finished'])
    require(preflight.get('id') == reserved['id'] and preflight.get('code_commit') == admission['code_commit']
            and start <= end <= stamp(admission['prepared_at'])
            and (end-start).total_seconds() <= reserved['elapsed_seconds'],
            'preparation work exceeds or differs from the fixed reserved envelope')
    require(set(actual['audits']) == set(actual['auditor_readbacks']) == set(reserved['selections']),
            'preparation reservation omits external auditor completion')
    expected_paths, seen = [], set()
    for reference in admission['linux_cleanup_tests']:
        proof = read_reference(reference)
        kind = proof.get('kind')
        require(kind in reserved['selections'] and kind not in seen,
                'reserved preparation proof selection differs')
        seen.add(kind)
        if plan.get('id') == SETUP_RECOVERY_ID and kind == 'owned_cleanup':
            import xml.etree.ElementTree as XML
            junit = proof['junit']; path = Path(junit['path'])
            require(path.is_absolute() and path.is_file() and not path.is_symlink()
                    and path.stat().st_size <= 4*1024**2
                    and artifacts.file_hash(path) == junit['sha256'],
                    'setup recovery SQLite Linux proof artifact changed')
            cases = XML.fromstring(path.read_bytes()).findall('.//testcase')
            selected = [case for case in cases if case.get('name') ==
                        'test_linux_storage_observation_handles_sqlite_journal_unlink']
            require(len(selected) == 1 and not any(selected[0].find(tag) is not None
                    for tag in ('failure','error','skipped')),
                    'setup recovery requires the actual passed Linux SQLite journal case')
        run_id = reserved['selections'][kind]
        raw = group.parent/run_id; dispatch = Path(str(raw)+'.dispatch')
        expected_paths.extend([raw,dispatch])
        audit = read_reference(proof['terminal_audit'], maximum=16 * 1024**2)
        completion_ref = actual['audits'][kind]
        completion = read_reference(completion_ref)
        require(Path(reference['path']) == raw/'proof.json'
                and Path(proof['terminal_audit']['path']) == raw/'terminal-audit.json'
                and proof.get('independent_cleanup_verified') is True
                and audit.get('id') == run_id and audit.get('state') == 'passed'
                and audit.get('code_commit') == admission['code_commit']
                and audit.get('lease_released') is True
                and audit.get('cleanup_state') in {'terminal_and_reaped','terminal_no_live_owned_processes'}
                and audit.get('driver') == proof.get('driver')
                and start <= stamp(proof['started']) <= stamp(proof['finished'])
                <= stamp(audit['observed_at']) <= end,
                'reserved preparation omits exact independent fixture closure')
        require(Path(completion_ref['path']) == dispatch/'audit-receipt.json'
                and completion.get('state') == 'complete'
                and type(completion.get('returncode')) is int and completion['returncode'] == 0
                and completion.get('outer_seconds') == 60
                and type(completion.get('host_wall_s')) in (int,float)
                and math.isfinite(completion['host_wall_s']) and 0 <= completion['host_wall_s'] <= 60
                and all(completion.get('proof', {}).get(key) == reference[key]
                        and completion.get('terminal_audit', {}).get(key) == proof['terminal_audit'][key]
                        for key in ('path','sha256'))
                and stamp(proof['finished']) <= stamp(completion['audit_started'])
                <= stamp(audit['observed_at']) <= stamp(completion['audit_finished']) <= end
                and (stamp(completion['audit_finished'])-stamp(completion['audit_started'])).total_seconds() <= 60,
                'preparation external audit failed, escaped its cap, or finished after the envelope')
        readback_ref = actual['auditor_readbacks'][kind]
        readback = read_reference(readback_ref)
        wrapper_exit = read_reference(readback['wrapper_exit'], maximum=16)
        require(Path(readback_ref['path']) == group/(kind+'.readback.json')
                and readback.get('id') == run_id
                and type(readback.get('wrapper_returncode')) is int and readback['wrapper_returncode'] == 0
                and Path(readback['wrapper_exit']['path']) == group/(kind+'.audit-wrapper.exit')
                and type(wrapper_exit) is int and wrapper_exit == 0
                and all(readback.get(field, {}).get(key) == wanted[key]
                        for field,wanted in (('audit_receipt',completion_ref),('proof',reference),
                                             ('terminal_audit',proof['terminal_audit']))
                        for key in ('path','sha256'))
                and stamp(completion['audit_finished']) <= stamp(readback['finished']) <= end,
                'preparation auditor wrapper or final hash readback failed or escaped the envelope')
    require(seen == set(reserved['selections']) and set(paths) == set(expected_paths+[group]),
            'preparation reservation omits or adds output roots')
    used = allocated_bytes(paths)
    require(type(actual['raw_bytes']) is int and used == actual['raw_bytes'] <= reserved['raw_bytes'],
            'preparation output changed or exceeded the full reserved storage allowance')
    if 'supervision_recovery' in plan['accounting'] or 'lease_recovery' in plan['accounting']:
        from scripts.bfs_simulator_recovery import validate_supplement
        validate_supplement(plan, admission)


class OwnedDescendants:
    """Adopt orphaned nested sessions, then kill/reap only PID/start-time owners."""
    def __init__(self):
        require(sys.platform == 'linux' and hasattr(os, 'pidfd_open')
                and hasattr(signal, 'pidfd_send_signal'), 'Linux subreaper and pidfd support are required')
        libc = ctypes.CDLL(None, use_errno=True)
        require(libc.prctl(36, 1, 0, 0, 0) == 0, 'cannot enable child subreaper')
        active = ctypes.c_int()
        require(libc.prctl(37, ctypes.byref(active), 0, 0, 0) == 0 and active.value == 1,
                'child subreaper is not active')
        self.sampler = DescendantRSS(os.getpid())

    def sample(self):
        return self.sampler.sample()

    def kill_identity(self, row):
        try:
            handle = os.pidfd_open(row['pid'])
        except ProcessLookupError:
            return
        try:
            fields = (Path('/proc') / str(row['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[19]) == row['start_ticks']:
                signal.pidfd_send_signal(handle, signal.SIGKILL)
        except (FileNotFoundError, ProcessLookupError):
            pass
        finally:
            os.close(handle)

    def finish(self, seconds=5):
        until = time.monotonic() + seconds
        observed = {}
        while True:
            rows = [row for row in self.sample()['processes'] if row['pid'] != os.getpid()]
            for row in rows:
                observed[row['pid'], row['start_ticks']] = row
                self.kill_identity(row)
            # All orphans are our children because subreaper admission precedes dispatch.
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                    if pid == 0: break
                except ChildProcessError:
                    break
            if not rows:
                return {'state': 'all_owned_descendants_absent', 'observed': list(observed.values()),
                        'subreaper': True, 'checked_at': now().isoformat()}
            require(time.monotonic() < until, 'owned descendants remain after bounded cleanup')
            time.sleep(0.02)


class Ledger:
    def __init__(self, plan, admission, started, started_at, outer_started=None):
        self.outer_started = outer_started or started_at
        startup = (started_at-self.outer_started).total_seconds()
        require(0 <= startup <= 30, 'outer/helper startup exceeded telemetry admission bound')
        self.bounds, self.started = plan['bounds'], started
        clock = admission['clock']
        self.end = stamp(clock['absolute_end'])
        first, latest = stamp(clock['not_before']), stamp(clock['latest_start'])
        charged = preparation_charges(plan)
        require(admission['preparation_charges'] == charged, 'admission omits or changes actual preparatory charges')
        self.charged_seconds = sum(row['elapsed_seconds'] for row in charged)
        self.charged_bytes = sum(row['raw_bytes'] for row in charged)
        available = self.bounds['batch_seconds'] - self.charged_seconds
        if 'clock_policy' in plan:
            if 'supervision_recovery' in plan['accounting'] or 'lease_recovery' in plan['accounting']:
                from scripts.bfs_simulator_recovery import hard_end
                expected_end = hard_end(plan)
            else:
                require(plan['id'] == SETUP_RECOVERY_ID
                        and plan['clock_policy'] == {'method':'original_absolute_end_clamp.v1',
                                                     'absolute_end':SETUP_HARD_END},
                        'setup recovery must retain its fixed original hard end and full-series latest start')
                expected_end = stamp(SETUP_HARD_END)
            require(self.end == expected_end
                    and latest <= self.end-timedelta(seconds=self.bounds['series_seconds']+self.bounds['cleanup_seconds']),
                    'setup recovery must retain its fixed original hard end and full-series latest start')
            usable = min(available, (self.end-self.outer_started).total_seconds())
            require(available > 0 and usable >= self.bounds['series_seconds']+self.bounds['cleanup_seconds']
                    and stamp(admission['prepared_at']) <= first <= self.outer_started <= started_at <= latest,
                    'setup recovery is late or cannot admit a full series and cleanup')
            self.monotonic_end = started + usable - startup
        else:
            require(available > 0 and latest == self.end - timedelta(seconds=available)
                    and stamp(admission['prepared_at']) <= first <= self.outer_started <= started_at <= latest,
                    'prospective schedule is absent, late, or cannot fit the remaining batch allowance')
            self.monotonic_end = started + available - startup
        self.startup_seconds = startup

    def remaining(self):
        remaining = min(self.monotonic_end - time.monotonic(), (self.end - now()).total_seconds())
        require(remaining > self.bounds['cleanup_seconds'], 'common batch deadline exhausted')
        return remaining

    def next_allowance(self, raw_bytes, series_cap_gib=None):
        require(self.remaining() >= self.bounds['series_seconds'] + self.bounds['cleanup_seconds'],
                'insufficient shared time for the next full series allowance and cleanup')
        storage = math.floor((self.bounds['batch_storage_gib'] * GIB - self.charged_bytes - raw_bytes) / GIB)
        if series_cap_gib is not None:
            storage = min(series_cap_gib, storage)
        require(storage >= 1, 'shared batch raw-storage allowance exhausted')
        return self.bounds['series_seconds'], storage

    def observation(self, raw_bytes):
        return {'observed_at': now().isoformat(), 'elapsed_seconds': self.startup_seconds + time.monotonic() - self.started,
                'charged_elapsed_seconds': self.charged_seconds + self.startup_seconds + time.monotonic() - self.started,
                'raw_bytes': raw_bytes, 'charged_raw_bytes': self.charged_bytes + raw_bytes,
                'absolute_end': self.end.isoformat()}


def validate_inputs(plan, admission, store):
    require(admission.get('format') == 'swdb.bfs.simulator-batch-admission.v1'
            and admission.get('plan_sha256') == artifacts.digest(plan), 'admission does not bind this exact plan')
    require(admission.get('runtime_sha256') == runtime_identity(), 'reviewed runtime files changed')
    python = admission['python']
    require(str(Path(sys.executable).resolve()) == python['path']
            and artifacts.file_hash(python['path']) == python['sha256'], 'Python runtime differs from admission')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    require(commit == admission['code_commit'], 'checkout differs from admitted code commit')
    required = []
    for rid, digest in plan['record_sha256'].items():
        record = store.get(rid)
        require(record is not None and artifacts.digest(record) == digest, 'fixed input record changed: ' + rid)
        required.append(record)
    failure = plan['historical_failure']
    require(artifacts.file_hash(store.dir / store.path_of(failure['id'])) == failure['file_sha256'],
            'retained a1 failure changed')
    require(store.get('bfs-dx100-witness-20260926-a2') is None, 'expired witness a2 has an execution record')
    old_coverage = store.get(plan['historical_coverage_failure']['id'])
    require(old_coverage is not None and artifacts.digest(old_coverage) ==
            plan['historical_coverage_failure']['sha256'], 'historical coverage a1 failure is absent or changed')
    require(artifacts.file_hash(store.dir/store.path_of(old_coverage['id'])) ==
            plan['historical_coverage_failure']['file_sha256'], 'historical coverage file bytes changed')
    prerequisites = validate_prerequisites(plan, admission, store)
    protocols = {}
    require(set(admission['protocols']) == set(plan['protocol_requests']), 'frozen protocol admission differs from plan')
    for key, ref in admission['protocols'].items():
        request_ref = plan['protocol_requests'][key]
        request_path = ROOT / request_ref['path']
        require(artifacts.file_hash(request_path) == request_ref['sha256'], 'prospective protocol request changed')
        request = yamlio.load(request_path)
        frozen = store.get(ref['id'], 'protocol')
        require(frozen and artifacts.digest(frozen) == ref['sha256'], 'frozen protocol missing or changed')
        bfs_protocol.verify_immutable(frozen)
        require(frozen.get('requested_id') == request['id'] and frozen['settings'] == request['settings']
                and stamp(frozen['frozen_at']) <= stamp(admission['prepared_at']),
                'protocol must freeze the exact reviewed settings before batch admission')
        protocols[key] = frozen
    if 'protocol_recovery' in plan['accounting']:
        from scripts.bfs_simulator_recovery import validate_protocol_runtime
        validate_protocol_runtime(plan, protocols)
    for row in plan['series']:
        candidate = store.get(row['candidate']); source = store.get(candidate['source_snapshot'])
        implementation = store.get(candidate['implementation']); workload = store.get(row['workload'])
        frozen = protocols.get(row['protocol_key'])
        validate_selection(candidate, source, implementation, workload, frozen, row['protocol_role'],
                           not row.get('primary_build'),
                           artifacts.identify(artifacts.source_root(store, implementation)))
        require(workload['definition']['sources'] == row['sources'], 'ordered workload sources changed')
        validate_diagnostic_build(store.get(row['diagnostic_build']), candidate, implementation,
            store.get(plan['model_build']), plan['roi'], row['accelerated'], frozen, row['protocol_role'])
    availability = bfs_coverage._availability(required, 'mbit10')
    require(availability and all(row['state'] == 'verified' for row in availability),
            'input source/build/graph/raw artifacts are unavailable or changed')
    return prerequisites, availability


def validate_prerequisites(plan, admission, store):
    proofs = admission['proofs']
    require(set(proofs) == {'a3', 'coverage', 'paired', 'provider'},
            'actual witness, fixed coverage, and prior batch terminal audits are required')
    # Lazy import: A2's measured native ownership module imports this module.
    from scripts import bfs_dx100_coverage_a2 as coverage_a2
    require(plan['required_a3'] == witness_case.PROBE_ID
            and plan['required_coverage'] == coverage_a2.RUN_ID + '.execute', 'prerequisite identities differ')
    current = stamp(admission['prepared_at'])
    observed = {'a3': coverage_case.validate_a3(proofs['a3'], store, current)}
    observed['coverage'] = coverage_a2.validate_completed(proofs['coverage'], store, current,
                                                          admission['coverage_commit'])
    for kind in ('paired', 'provider'):
        observed[kind] = witness_case.validate_completion(proofs[kind], kind, current)
    return observed


def validate_cleanup_tests(admission):
    """Actual Linux nested cleanup and public interruption proof at this exact pin."""
    import xml.etree.ElementTree as XML
    from scripts.bfs_simulator_recovery import proof_admission
    admission = proof_admission(admission)
    refs = admission['linux_cleanup_tests']
    require(isinstance(refs, list) and len(refs) == 2, 'two actual Linux fixture receipts are required')
    expected = {name: admission['runtime_sha256'][name] for name in CLEANUP_RUNTIME}
    expected.update({name: admission['runtime_sha256'][name] for name in
                     ('swdb/dx100.py', 'tests/test_dx100_interruption.py', 'tests/test_bfs_owned_execution.py')})
    required = {
        'owned_cleanup': {
            'test_linux_owned_stage_reaps_detached_child[False]',
            'test_linux_owned_stage_reaps_detached_child[True]',
            'test_linux_nested_interruption_uses_one_cleanup_budget',
            'test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve'},
        'dx100_interruption': {'test_public_interruption_is_durable_before_postmortem[raises]',
                              'test_public_interruption_is_durable_before_postmortem[stalls]'}}
    seen = set()
    for ref in refs:
        result = read_reference(ref)
        kind = result.get('kind')
        require(kind in required and kind not in seen and result.get('format') == 'swdb.bfs.linux-fixture.v1'
                and result.get('host') == 'mbit10' and result.get('platform') == 'linux'
                and result.get('code_commit') == admission['code_commit']
                and result.get('runtime_sha256') == expected
                and result.get('evidence_kind') == 'contract_fixture' and result.get('state') == 'passed'
                and type(result.get('returncode')) is int and result['returncode'] == 0
                and stamp(result['started']) <= stamp(result['finished']) <= stamp(admission['prepared_at'])
                and (stamp(result['finished'])-stamp(result['started'])).total_seconds() <= 90,
                'Linux fixture admission is missing or differs from this exact code')
        seen.add(kind)
        command = result.get('command', [])
        require(isinstance(command, list) and command[1:3] == ['-m', 'pytest']
                and str(Path(command[0]).resolve()) == admission['python']['path']
                and '--junitxml='+result['junit']['path'] in command, 'Linux fixture command is unbound')
        module = ('tests/test_bfs_owned_execution.py' if kind == 'owned_cleanup'
                  else 'tests/test_dx100_interruption.py')
        require(any(arg == module or arg.startswith(module+'::') for arg in command),
                'Linux fixture command omits required module')
        raw = {}
        for key, bound in (('stdout', 16*1024**2), ('junit', 4*1024**2)):
            item = result[key]; path = Path(item['path'])
            require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'unsafe fixture artifact')
            with path.open('rb') as stream: content = stream.read(bound+1)
            require(len(content) <= bound and hashlib.sha256(content).hexdigest() == item['sha256'],
                    'Linux fixture artifact differs')
            raw[key] = content
        cases = XML.fromstring(raw['junit']).findall('.//testcase')
        require(cases and all(not any(case.find(tag) is not None for tag in ('failure','error','skipped'))
                for case in cases) and required[kind] <= {case.get('name') for case in cases},
                'Linux fixture omits required cases or contains failures/skips')
    require(seen == set(required), 'cleanup and interruption proofs are both required')


def lease_observation(machine, node):
    """Bounded coherent snapshots; only the other socket may change ownership.

    hostlock acquires flock before publishing held metadata, and publishes
    released metadata before unlocking (2026-09-27 installed protocol audit).
    Neither short publication window is permission to ignore a persistent
    disagreement, a legacy conflict, or any change to our own lease.
    """
    own = f'mbit10-evaluation-node{node}'
    other = f'mbit10-evaluation-node{1-node}'
    legacy = 'mbit10-evaluation'
    verified = profile._verified_lane(machine, own)
    root = Path(os.environ.get('LACT_LEASE_ROOT', '/data1/yanruj/lact-host-lease'))
    own_path = root / (own + '.meta.json')
    own_raw = own_path.read_bytes()
    own_value = json.loads(own_raw)
    require(own_value.get('state') == 'held', 'own lane metadata is not held')

    def snapshot(name):
        path = root / (name + '.meta.json')
        before = path.read_bytes()
        value = json.loads(before)
        require(value.get('state') in {'held', 'released'}, 'invalid lease metadata state')
        with (root / (name + '.lease')).open('rb') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                held = False
            except BlockingIOError:
                held = True
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
        after = path.read_bytes()
        coherent = before == after and value['state'] == ('held' if held else 'released')
        return {'sha256': hashlib.sha256(before).hexdigest(), 'metadata': value,
                'kernel_held': held}, coherent

    previous = None
    # Five reads and at most four 50-ms waits, charged to the caller's clock.
    # Two consecutive coherent identical observations are required, including
    # when the first read happens to fall just before an ownership transition.
    for attempt in range(5):
        require(own_path.read_bytes() == own_raw
                and profile._verified_lane(machine, own) == verified,
                'own lane changed during lease snapshot')
        legacy_row, legacy_ok = snapshot(legacy)
        require(legacy_ok, 'other lease metadata and kernel lock disagree (legacy)')
        require(not legacy_row['kernel_held'], 'legacy kernel lease is held')
        row, coherent = snapshot(other)
        require(own_path.read_bytes() == own_raw, 'own lane changed during lease snapshot')
        if coherent and row == previous:
            # Do not return after an external read without rechecking legacy
            # exclusion and the lane's complete kernel/ancestry admission.
            final_legacy, final_ok = snapshot(legacy)
            require(final_ok and not final_legacy['kernel_held']
                    and final_legacy == legacy_row, 'legacy lease changed during snapshot')
            require(own_path.read_bytes() == own_raw
                    and profile._verified_lane(machine, own) == verified,
                    'own lane changed during lease snapshot')
            return {'verified_lane': verified, 'leases': {
                legacy: final_legacy,
                own: {'sha256': hashlib.sha256(own_raw).hexdigest(),
                      'metadata': own_value, 'kernel_held': None}, other: row},
                'other_socket_snapshot_attempts': attempt + 1}
        previous = row if coherent else None
        if attempt < 4:
            time.sleep(.05)
    raise ValueError('other lease metadata and kernel lock disagree or did not stabilize')


def series_command(plan, row, admission, config, runs, records, node, seconds, storage, cleanup=None, slots=None):
    b = plan['bounds']
    command = [admission['python']['path'], str(ROOT / 'scripts/bfs_simulator_series.py'),
        '--id', row['id'], '--candidate', row['candidate'], '--workload', row['workload'],
        '--build-evaluation', plan['model_build'], '--diagnostic-build', row['diagnostic_build'],
        '--configuration', str(config), '--runs-dir', str(runs), '--records', str(records), '--lane', str(node),
        *(['--primary-build', row['primary_build']] if row.get('primary_build') else ['--author-binary']),
        '--verifier', plan['verifier'], '--require-capacity',
        '--total-seconds', str(seconds), '--checkpoint-seconds', str(b['checkpoint_seconds']),
        '--run-seconds', str(b['run_seconds']), '--diagnostic-seconds', str(b['diagnostic_seconds']),
        '--memory-gib', str(b['memory_gib']), '--storage-gib', str(b['storage_gib']),
        '--batch-storage-gib', str(storage), '--verification-ticks', str(plan['verification_ticks'])]
    if cleanup is not None:
        command += ['--owned-cleanup-ledger', str(cleanup.path), '--owned-cleanup-binding', cleanup.binding]
    if row['accelerated']:
        command.append('--accelerated')
    if 'trace_transport' in plan:
        require(plan['trace_transport'] == 'gem5-gzip.v1', 'unsupported planned trace transport')
        command += ['--trace-transport', plan['trace_transport']]
    if row['protocol_key'] is not None:
        command += ['--protocol', admission['protocols'][row['protocol_key']]['id'], '--protocol-role', row['protocol_role']]
    for key in row.get('shared_protocol_keys', []):
        command += ['--shared-protocol', admission['protocols'][key]['id']]
    if 'post_roi_cpu' in plan:
        command += ['--post-roi-cpu', plan['post_roi_cpu']]
    if 'trace_flags' in plan:
        command += ['--trace-flags', plan['trace_flags']]
    if 'profile_seconds' in b:
        command += ['--profile-seconds', str(b['profile_seconds'])]
    if 'package_seconds' in b:
        command += ['--package-seconds', str(b['package_seconds'])]
    if 'aggregate_seconds' in b:
        command += ['--aggregate-seconds', str(b['aggregate_seconds'])]
    if slots is not None:
        command += ['--gem5-slot-dir', str(slots), '--gem5-slots', str(plan['concurrency']['gem5_slots'])]
    return command


def package_binding(store, package_id, requested, evaluation_id, profile_id, candidate_id):
    """Reopen a sealed public package; its ID is content-addressed, not a request ID."""
    package = store.get(package_id, 'profile_package')
    require(package and package.get('id') == package_id and package.get('requested_id') == requested
            and type(package.get('package_version')) is int and package['package_version'] == 1,
            'series package does not identify the requested first immutable assembly')
    profile_package.verify(package)
    evaluation = store.get(evaluation_id, 'evaluation')
    region = store.get(profile_id, 'region_profile')
    candidate = store.get(candidate_id, 'candidate')
    snapshot = store.get(package['source_snapshot'], 'source_snapshot')
    require(evaluation and region and candidate and snapshot, 'series package ancestry is unavailable')
    require(package.get('evaluation') == evaluation_id and package.get('region_profile') == profile_id
            and package.get('candidate') == evaluation.get('candidate') == candidate_id
            and package.get('implementation') == evaluation.get('implementation') == candidate['implementation']
            and package['source_snapshot'] == requested + '.v1.source'
            and snapshot['implementation'] == candidate['implementation']
            and artifacts.digest(snapshot['artifact']) == artifacts.digest(candidate['artifact'])
            and not profile_package._profile_check(region, evaluation, candidate),
            'series package evaluation/profile/source binding differs')
    require(package['evidence'].get('evaluation_sha256') == artifacts.digest(evaluation)
            and package['evidence'].get('region_profile_sha256') == artifacts.digest(region)
            and artifacts.digest(package['evidence']['full_application']) == artifacts.digest(candidate['artifact'])
            and all(profile_package._same(package['context'].get(key), value)
                    for key, value in profile_package._context(evaluation).items()),
            'series package retained evidence or exact context changed')
    return package


def validate_series_result(plan, row, admission, child, seconds, storage, store):
    expected_bounds = {name: plan['bounds'][name] for name in
        ('checkpoint_seconds', 'run_seconds', 'diagnostic_seconds', 'memory_gib', 'storage_gib')}
    expected_bounds.update(total_seconds=seconds, batch_storage_gib=storage,
                           verification_ticks=plan['verification_ticks'])
    for name in ('profile_seconds', 'package_seconds', 'aggregate_seconds'):
        if name in plan['bounds']:
            expected_bounds[name] = plan['bounds'][name]
    expected_protocol = admission['protocols'][row['protocol_key']]['id'] if row['protocol_key'] else None
    shared_ids = [admission['protocols'][key]['id'] for key in row.get('shared_protocol_keys', [])]
    repetitions = 2
    if expected_protocol:
        repetitions = store.get(expected_protocol, 'protocol')['settings']['sampling']['repetitions']
    require(child.get('shared_protocols', []) == shared_ids and child.get('post_roi_cpu') == plan.get('post_roi_cpu')
            and child.get('trace_flags') == plan.get('trace_flags'),
            'series shared-protocol, post-ROI CPU or trace-flag treatment differs from the plan')
    require(child.get('state') == 'complete' and child.get('id') == row['id']
            and child.get('candidate') == row['candidate'] and child.get('workload') == row['workload']
            and child.get('configuration') == row['configuration'] and child.get('roi') == plan['roi']
            and child.get('model_build') == plan['model_build'] and child.get('repetitions') == repetitions
            and child.get('protocol') == expected_protocol and child.get('bounds') == expected_bounds
            and child.get('diagnostic_build') == {'evaluation': row['diagnostic_build'],
                'sha256': plan['record_sha256'][row['diagnostic_build']]}
            and child.get('stages') and all(stage.get('state') == 'complete' for stage in child['stages']),
            'series receipt differs from its planned complete identity or bounds')
    require(child.get('trace_transport') == plan.get('trace_transport'),
            'series trace transport differs from its explicit planned collector')
    supervision = child.get('owned_supervision', {})
    require(supervision.get('format') == 'swdb.bfs.simulator-supervision.v1'
            and supervision.get('sampled_tree_rss_bytes') == lifecycle.SAMPLED_RSS_BYTES
            and supervision.get('maximum_gap_seconds') == 30
            and supervision.get('rss_source') == lifecycle.RSS_SOURCE
            and supervision.get('hard_memory_quota') is False
            and type(supervision.get('maximum_observed_gap_seconds')) in (int,float)
            and 0 <= supervision['maximum_observed_gap_seconds'] <= 30
            and type(supervision.get('maximum_guard_seconds')) in (int,float)
            and 0 <= supervision['maximum_guard_seconds'] <= 30
            and child.get('owned_cleanup', {}).get('state') == 'all_owned_descendants_absent'
            and all(stage.get('cleanup', {}).get('state') == 'all_owned_descendants_absent'
                    for stage in child['stages']), 'series lacks the prospective whole-tree/cleanup contract')
    expected = [(position, source, repetition) for position, source in enumerate(row['sources'])
                for repetition in range(repetitions)]
    samples = child.get('samples', [])
    require([(sample.get('source_position'), sample.get('source'), sample.get('repetition'))
             for sample in samples] == expected, 'series did not retain its complete ordered sample grid')
    for sample in samples:
        prefix = f"{row['id']}.s{sample['source_position']}.r{sample['repetition']}"
        require(sample.get('completeness') == 'complete' and all(sample.get(key) == prefix + suffix
                for key, suffix in (('evaluation', '.primary.evaluation'), ('diagnostic_evaluation', '.diagnostic.evaluation'),
                                    ('profile', '.profile'))),
                'series sample references differ from the prospective grid')
        package = package_binding(store, sample.get('package'), prefix + '.package', sample['evaluation'],
                                  sample['profile'], row['candidate'])
        if plan.get('trace_transport') is not None:
            for key in ('evaluation', 'diagnostic_evaluation'):
                execution = store.get(sample[key], 'evaluation')
                require(execution is not None
                        and execution.get('context', {}).get('trace_transport') == plan['trace_transport']
                        and execution.get('request', {}).get('verification', {}).get('trace_transport')
                        == plan['trace_transport'], 'planned trace transport is missing from a public execution')
        require(package.get('completeness') == 'complete' and package['evidence']['classification'] == 'execution',
                'series package is not complete actual execution evidence')
        context = package['context']
        require(context.get('workload', {}).get('id') == row['workload']
                and context.get('sources') == [sample['source']] and context.get('roi') == plan['roi']
                and context.get('target') == plan['target'] and context.get('threads') == plan['threads']
                and all(profile_package._same(context.get('target_configuration', {}).get(key), value)
                        for key, value in row['configuration'].items()),
                'series package source/workload/ROI/target treatment differs from its planned sample')
    if expected_protocol is None:
        require(child.get('aggregate') is None, 'unfrozen calibration series cannot declare a protocol aggregate')
        return
    require(child.get('aggregate') == row['id'] + '.aggregate', 'series aggregate identity differs from the planned aggregate')
    require(child.get('shared_aggregates', {}) == {pid: f"{row['id']}.shared{index}.aggregate"
                                                    for index, pid in enumerate(shared_ids)},
            'series shared aggregates differ from the planned protocols')
    keys = [row['protocol_key'], *row.get('shared_protocol_keys', [])]
    for key, aggregate_id in zip(keys, [child['aggregate'], *child.get('shared_aggregates', {}).values()]):
        validate_series_aggregate(plan, row, admission, samples, store, key, aggregate_id, expected_protocol)


def validate_series_aggregate(plan, row, admission, samples, store, key, aggregate_id, primary_protocol):
    """Reopen one public aggregate under one admitted protocol (R10: possibly shared)."""
    # A completed child declaration is not evidence of the public aggregation.
    # Reopen its exact ordered primaries and the admitted immutable policy before
    # using the same semantic/grid reader as a subsequent public comparison.
    expected_protocol = admission['protocols'][key]['id']
    frozen = store.get(expected_protocol, 'protocol')
    require(frozen and frozen.get('id') == expected_protocol
            and artifacts.digest(frozen) == admission['protocols'][key]['sha256'],
            'series aggregate protocol differs from the admitted frozen record')
    bfs_protocol.verify_immutable(frozen)
    bfs_protocol._validate_settings(frozen['settings'], store)
    aggregate = store.get(aggregate_id, 'evaluation')
    primary_ids = [sample['evaluation'] for sample in samples]
    expected_request = {'message_version': '1.0', 'id': aggregate_id, 'protocol': expected_protocol,
                        'protocol_role': row['protocol_role'], 'evaluations': primary_ids}
    require(aggregate and aggregate.get('id') == aggregate_id
            and aggregate.get('candidate') == row['candidate']
            and aggregate.get('outcome', {}).get('state') == 'complete'
            and aggregate['outcome'].get('stage') == 'aggregation'
            and aggregate.get('gain_claim') is False
            and artifacts.digest(aggregate.get('request')) == artifacts.digest(expected_request),
            'series aggregate is not the exact completed public protocol/role request')
    components = []
    for sample in samples:
        primary = store.get(sample['evaluation'], 'evaluation')
        require(primary and primary.get('id') == sample['evaluation']
                and primary.get('candidate') == row['candidate'], 'series aggregate primary identity differs')
        trial = {'source_position': sample['source_position'], 'repetition': sample['repetition']}
        request, context = primary.get('request', {}), primary.get('context', {})
        binding = bfs_protocol.protocol_binding(context, expected_protocol)
        require(request.get('protocol') == context.get('protocol') == primary_protocol
                and binding.get('protocol') == expected_protocol and binding.get('role') == row['protocol_role']
                and request.get('protocol_role') == row['protocol_role']
                and request.get('fixture') is not True and primary.get('evidence_kind') == 'execution'
                and artifacts.digest(request.get('protocol_trial')) == artifacts.digest(trial)
                and artifacts.digest(context.get('protocol_trial')) == artifacts.digest(trial)
                and context.get('workload', {}).get('id') == row['workload']
                and context.get('sources') == context.get('workload', {}).get('sources') == [sample['source']]
                and type(context.get('repetitions')) is int and context['repetitions'] == 1
                and len(primary.get('timing', [])) == 1
                and all(type(primary['timing'][0].get(key)) is int
                        and primary['timing'][0][key] == value for key, value in trial.items())
                and primary['timing'][0].get('source') == sample['source'],
                'series aggregate primary protocol role or ordered trial binding differs')
        components.append({'evaluation': primary['id'], 'sha256': artifacts.digest(primary)})
    require(artifacts.digest(aggregate.get('component_evaluations')) == artifacts.digest(components),
            'series aggregate public component order or digests differ from its sample grid')
    observations, workload_id, classification = bfs_protocol._evaluation_samples(
        store, aggregate, frozen, row['protocol_role'])
    require(classification == 'execution' and workload_id == row['workload']
            and set(observations) == set(range(len(row['sources'])))
            and all(len(values) == frozen['settings']['sampling']['repetitions'] for values in observations.values()),
            'series aggregate lacks the complete actual frozen sample grid')


def collect_series(plan, admission, receipt, folder, runs, records, node, ledger, owned, monitor,
                   rows=None, aggregate=None, slots=None):
    """Launch each public series once; terminal readback cannot skip cleanup."""
    for row in plan['series'] if rows is None else rows:
        raw = monitor(force=True) if aggregate is not None else monitor()
        require(runtime_identity() == admission['runtime_sha256'], 'runtime changed during batch')
        if aggregate is not None:
            seconds, storage = ledger.next_allowance(aggregate(), plan['allocation']['per_series_cap_gib'])
        else:
            seconds, storage = ledger.next_allowance(raw)
        admit_capacity(receipt, node, row['id'])
        config = folder / (row['id'] + '.configuration.json')
        with config.open('x') as stream:
            stream.write(json.dumps(row['configuration'], indent=2) + '\n')
        child_root = runs / row['id']
        require(not child_root.exists(), 'series root already exists; no resume')
        command = series_command(plan, row, admission, config, child_root, records, node, seconds, storage,
                                 owned.budget, slots)
        entry = {'id': row['id'], 'state': 'running', 'command': command, 'started': now().isoformat(),
                 'series_seconds': seconds, 'remaining_storage_gib': storage}
        receipt['series'].append(entry); save_receipt(folder, receipt)
        output = folder / (row['id'] + '.stdout.json')
        try:
            lifecycle.run_stage(receipt, folder, command, timeout=seconds, owned=owned,
                deadline=min(ledger.monotonic_end, time.monotonic() + (ledger.end - now()).total_seconds())
                         - plan['bounds']['cleanup_seconds'], cwd=ROOT, output=output, monitor=monitor)
        finally:
            # Lifecycle run_stage charged every child and detached descendant to
            # the shared reserve, including the normal-leader-exit path.
            try:
                entry['cleanup'] = receipt['stages'][-1]['cleanup']
            except BaseException as exc:
                entry['cleanup'] = {'state': 'failed', 'reason': f'{type(exc).__name__}: {exc}'}
                raise
            finally:
                save_receipt(folder, receipt)
        child_file = child_root / (row['id'] + '.driver') / 'driver.json'
        child_ref = {'path': str(child_file), 'sha256': artifacts.file_hash(child_file)}
        child = read_reference(child_ref, maximum=16 * 1024**2)
        require(child == read_reference({'path': str(output), 'sha256': artifacts.file_hash(output)},
                                       maximum=16 * 1024**2), 'series stdout differs from its retained receipt')
        require(child.get('owned_supervision', {}).get('cleanup_ledger') == str(owned.budget.path)
                and child['owned_supervision'].get('cleanup_binding') == owned.budget.binding,
                'series did not use this shared cleanup reserve')
        sample_ref = child['owned_resource_artifact']
        require(artifacts.file_hash(sample_ref['path']) == sample_ref['sha256'], 'series resource stream changed')
        lifecycle.validate_samples(sample_ref['path'], child['owned_started'], child['owned_finished'])
        validate_series_result(plan, row, admission, child, seconds, storage, Store(records))
        entry.update(state='complete', finished=now().isoformat(), receipt=child_ref)
        monitor()


def finalize_receipt(receipt, folder, runs, ledger, ledger_file):
    """Final hashing and persistence are inside the shared budget, even on failure."""
    def observation():
        row = ledger.observation(allocated_bytes(batch_storage_paths(runs)))
        require(row['charged_raw_bytes'] < ledger.bounds['batch_storage_gib'] * GIB,
                'final retained storage exceeded the common allowance')
        require(time.monotonic() <= ledger.monotonic_end and now() <= ledger.end,
                'cleanup or final accounting exceeded the common deadline')
        return row

    try:
        if ledger_file.exists():
            receipt['ledger_artifact'] = {'path': str(ledger_file), 'sha256': artifacts.file_hash(ledger_file)}
            if receipt.get('outer_started'):
                receipt['resource_validation'] = lifecycle.validate_samples(ledger_file, receipt['outer_started'],
                    now().isoformat(), nested=True)
        # The second write retains the first post-persistence observation. Both
        # writes are checked afterward; failure must not leave a complete receipt.
        for _ in range(2):
            receipt['final_ledger'] = observation()
            receipt.update(finished=now().isoformat(), elapsed_seconds=time.monotonic() - ledger.started)
            save_receipt(folder, receipt)
            observation()
            if receipt.get('outer_started'):
                lifecycle.validate_samples(ledger_file, receipt['outer_started'], now().isoformat(), nested=True)
    except BaseException as exc:
        receipt.update(state='failed', final_accounting_error=f'{type(exc).__name__}: {exc}',
                       finished=now().isoformat(), elapsed_seconds=time.monotonic() - ledger.started)
        save_receipt(folder, receipt)
        raise


def main():
    started, started_at = time.monotonic(), now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=PLAN_HASHES)
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--admission-sha256', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    parser.add_argument('--outer-started', required=True)
    parser.add_argument('--outer-deadline', required=True)
    parser.add_argument('--pane-pid', type=int, required=True)
    parser.add_argument('--pane-start-ticks', type=int, required=True)
    parser.add_argument('--family', help='pilot only: the one family series this driver runs')
    args = parser.parse_args()
    plan = yamlio.load(plan_path(args.kind))
    validate_plan(plan, args.kind)
    pilot = is_pilot(plan)
    selected = plan['series']
    grouped = pilot and any('group' in row for row in plan['series'])
    if grouped:
        selected = [row for row in plan['series'] if row.get('group') == args.family]
        require(selected, 'route driver requires a planned series group')
    elif pilot:
        selected = [row for row in plan['series'] if row['id'] == plan['id'] + '.' + str(args.family)]
        require(len(selected) == 1, 'pilot driver requires exactly one planned family')
    else:
        require(args.family is None, 'family selection is only defined for the pilot')
    admission_ref = {'path': str(args.admission.absolute()), 'sha256': args.admission_sha256}
    admission = read_reference(admission_ref)
    require(socket.gethostname().split('.')[0] == 'mbit10', 'simulator batch execution requires mbit10')
    ledger = Ledger(plan, admission, started, started_at, stamp(args.outer_started))
    require(stamp(args.outer_deadline) == min(ledger.end, stamp(args.outer_started)+timedelta(
            seconds=plan['bounds']['batch_seconds']-ledger.charged_seconds)),
            'outer deadline differs from the same charged batch allowance')
    runs = args.runs_dir.absolute()
    if pilot:
        # One family root inside the allocation root; both count in the aggregate.
        driver_root = plan['id'] + '.' + args.family if grouped else selected[0]['id']
        require(runs == pilot_storage_paths(plan)[0] / driver_root and runs == runs.resolve(),
                'pilot family root differs from the planned allocation root')
    else:
        require(runs.name == plan['id'] and any(base in runs.parents for base in RAW_ROOTS)
                and runs == runs.resolve(), 'use the exact new batch name in authorized raw storage, without symlinks')
    require(not runs.exists(), 'batch root already exists; resumes and retries are forbidden')
    dispatch = Path(str(runs) + '.dispatch')
    require(dispatch.is_dir() and not dispatch.is_symlink() and dispatch == dispatch.resolve(),
            'batch storage requires the existing exact .dispatch wrapper directory')
    records = ROOT / 'records'
    store = None
    runs.mkdir(parents=True, exist_ok=False)
    folder = runs / (plan['id'] + '.driver'); folder.mkdir()
    receipt = {'id': plan['id'], 'created': '2026-09-26', 'state': 'running', 'started': started_at.isoformat(),
        'plan': plan, 'plan_sha256': artifacts.digest(plan), 'admission': admission_ref,
        'outer_started': args.outer_started, 'outer_deadline': args.outer_deadline,
        'stages': [], 'series': [], 'gain_claim': False, 'protocol_freeze': False,
        'automatic_retry_allowed': False, 'ticket_acceptance': False, 'preparation_charges': admission['preparation_charges']}
    receipt['storage_paths'] = list(map(str, batch_storage_paths(runs)))
    lane_root = lane_sampler = aggregate = slots = None
    if pilot:
        lane_root = lifecycle.identity(os.getppid())
        # A fresh observer per sample: lane identities are telemetry here, and
        # each driver's own Owned history retains its complete ownership union.
        lane_sampler = lambda: lifecycle.DescendantRSS(lane_root['pid']).sample()
        aggregate_paths = pilot_storage_paths(plan)
        aggregate = lambda: allocated_bytes(aggregate_paths)
        slots = aggregate_paths[1] / 'gem5-slots'
        require(slots.is_dir() and not slots.is_symlink(), 'pilot gem5 slot directory is missing')
        receipt['concurrency'] = {**plan['concurrency'], 'family': selected[0]['id'], 'lane_root': lane_root,
            'aggregate_storage_paths': list(map(str, aggregate_paths)), 'gem5_slot_dir': str(slots),
            'lane_tree_sampled_rss_limit_bytes': lifecycle.SAMPLED_RSS_BYTES}
    save_receipt(folder, receipt)
    owned = guard = None
    budget_path = folder/'cleanup-ledger.json'
    binding = lifecycle.SharedCleanup.create(budget_path, args.outer_deadline, deadline=ledger.monotonic_end)
    cleanup_budget = lifecycle.SharedCleanup(budget_path, binding, ledger.monotonic_end)
    driver_identity = lifecycle.identity(os.getpid())
    pane = {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}
    receipt['process_observations'] = {'driver_identity': driver_identity, 'pane_identity': pane,
        'ancestry': lifecycle.ancestry(driver_identity, pane)}
    receipt['cleanup_budget'] = {'path': str(budget_path), 'binding': binding, 'budget_seconds': 30}
    ledger_file = folder / 'ledger.jsonl'
    finalizing = False
    def monitor():
        if finalizing:
            require(time.monotonic() < ledger.monotonic_end and now() < ledger.end,
                    'common batch deadline exhausted during cleanup')
        else:
            ledger.remaining()
        raw = allocated_bytes(batch_storage_paths(runs))
        total = aggregate() if pilot else raw
        require(total + ledger.charged_bytes < plan['bounds']['batch_storage_gib'] * GIB, 'shared batch raw-storage ceiling exceeded')
        if pilot:
            require(raw < plan['allocation']['per_series_cap_gib'] * GIB, 'pilot family storage cap exceeded')
        for path, minimum in ((runs, plan['bounds']['raw_reserve_gib']), (BUILD_ROOT.parent, plan['bounds']['build_reserve_gib'])):
            stat = os.statvfs(path)
            require(stat.f_bavail * stat.f_frsize >= minimum * GIB, 'raw/build free-space reserve violated')
        sample = {**ledger.observation(raw), **(lease_observation(store.get('mbit10'), args.lane)
                  if store else {'lease_admission': 'record_store_loading'}),
                  'owned_processes': owned.sample()}
        require(sample['owned_processes']['rss_bytes'] <= lifecycle.SAMPLED_RSS_BYTES,
                'sampled whole-tree RSS exceeded 52 GiB')
        if pilot:
            lane_tree = lane_sampler()
            sample.update(aggregate_raw_bytes=total, lane_tree_rss_bytes=lane_tree['rss_bytes'],
                          lane_tree_processes=len(lane_tree['processes']))
            require(lane_tree['rss_bytes'] <= lifecycle.SAMPLED_RSS_BYTES,
                    'sampled whole-lane-tree RSS exceeded 52 GiB')
        with ledger_file.open('a') as stream:
            stream.write(json.dumps(sample) + '\n')
        return raw
    try:
        owned = lifecycle.Owned(cleanup_budget)
        guard = lifecycle.Monitor(monitor); guard.start()
        require((now()-stamp(args.outer_started)).total_seconds() <= 30,
                'first resource observation exceeded outer startup allowance')
        store = Store(records)
        for row in selected:
            require(not any(rid == row['id'] or rid.startswith(row['id'] + '.') for rid in store.by_id)
                    and not list(BUILD_ROOT.glob(row['id'] + '*')), 'series IDs or build paths already exist; no retry')
        if pilot:
            validate_pilot_tests(plan, admission)
        else:
            validate_cleanup_tests(admission)
        validate_preparation_reservation(plan, admission)
        prerequisites, availability = validate_inputs(plan, admission, store)
        receipt.update(code_commit=admission['code_commit'], runtime_sha256=admission['runtime_sha256'],
                       raw_input_verification=availability, prerequisites=prerequisites)
        def guarded(force=False):
            # R2: stage polls every 0.25 s must not append a ledger line each
            # time; the periodic monitor still bounds the gap to 30 seconds.
            guard.check()
            if pilot and not force and guard.last_started is not None and \
                    time.monotonic() - guard.last_started < lifecycle.SAMPLE_INTERVAL_SECONDS:
                return None
            return guard.observe()
        if pilot:
            collect_series(plan, admission, receipt, folder, runs, records, args.lane, ledger, owned, guarded,
                           rows=selected, aggregate=aggregate, slots=slots)
        else:
            collect_series(plan, admission, receipt, folder, runs, records, args.lane, ledger, owned, guarded)
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        for entry in receipt['series']:
            if entry['state'] == 'running': entry.update(state='failed', finished=now().isoformat())
        raise
    finally:
        original_failure = sys.exc_info()[1]
        finalizing = True
        final_error = None
        def failed(exc, field):
            nonlocal final_error
            final_error = final_error or exc
            receipt.update(state='failed', **{field: f'{type(exc).__name__}: {exc}'})
        # Keep sampling through owned teardown without a monitor signal
        # interrupting the already bounded finalization path.
        if guard:
            guard.interrupt = False
        try:
            receipt['cleanup'] = lifecycle.verified_finish(owned) if owned else {'state': 'subreaper_not_admitted'}
            require(receipt['cleanup']['state'] != 'failed', 'owned cleanup exhausted its bounded attempt')
        except BaseException as exc:
            failed(exc, 'owned_cleanup_error')
        try:
            if guard:
                with cleanup_budget.reservation() as until: guard.stop(until)
        except BaseException as exc:
            failed(exc, 'monitor_shutdown_error')
        if owned:
            receipt['process_observations']['owned_processes'] = list(owned.history.values())
        try:
            with cleanup_budget.reservation():
                receipt['cleanup_accounting'] = cleanup_budget.snapshot()
        except BaseException as exc:
            failed(exc, 'cleanup_accounting_error')
        if guard:
            receipt['telemetry'] = {'sampled_rss_limit_bytes': lifecycle.SAMPLED_RSS_BYTES,
                'rss_source': lifecycle.RSS_SOURCE, 'maximum_gap_seconds': guard.maximum_gap_seconds,
                'maximum_guard_seconds': guard.maximum_guard_seconds, 'hard_memory_quota': False}
        try:
            # R2: three streaming reads of a long ledger (measured about one
            # second per 30,000 lines) need more than the default 5-second grant;
            # the fixed 30-second shared reserve still bounds the total.
            with (cleanup_budget.reservation(maximum=15) if pilot else cleanup_budget.reservation()):
                finalize_receipt(receipt, folder, runs, ledger, ledger_file)
        except BaseException as exc:
            failed(exc, 'final_accounting_error')
        # A secondary shutdown/accounting failure stays visible in the receipt
        # without replacing the original stage exception. If work succeeded,
        # any finalizer failure must still make the public process fail.
        if final_error is not None and original_failure is None:
            raise final_error
    with cleanup_budget.reservation():
        print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    with interruption_signals():
        main()
