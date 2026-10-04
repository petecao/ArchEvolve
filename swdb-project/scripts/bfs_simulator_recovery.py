"""Fixed failed-supervision cost admission. Created 2026-09-26; updated 2026-09-27 ET.

This reader does not repair, settle, qualify, or resume historical evidence.
Only explicitly pinned recovery plans may consume these flat cost rows.
"""
from datetime import timedelta
import json
import math
from pathlib import Path
import time
import xml.etree.ElementTree as XML

from scripts import bfs_owned_execution as owned
from swdb import artifacts, yamlio

IDS = {
    't16-protocol-recovery': 'bfs-t16-protocol-recovery-simulator-batch-20260927-a1',
    't16-seal-recovery': 'bfs-t16-seal-recovery-simulator-batch-20260927-a1',
    't15-lease-recovery': 'bfs-t15-lease-recovery-simulator-batch-20260927-a1',
    't16-lease-recovery': 'bfs-t16-lease-recovery-simulator-batch-20260927-a1',
    't15-supervision-recovery': 'bfs-t15-supervision-recovery-simulator-batch-20260926-a1',
    't16-supervision-recovery': 'bfs-t16-supervision-recovery-simulator-batch-20260926-a1',
}
ENDS = {'t16-protocol-recovery': '2026-09-27T20:16:17.225985-04:00','t16-seal-recovery': '2026-09-27T20:16:17.225985-04:00','t15-lease-recovery': '2026-09-27T09:14:09.851819-04:00',
        't16-lease-recovery': '2026-09-27T20:16:17.225985-04:00','t15-supervision-recovery': '2026-09-27T09:14:09.851819-04:00',
        't16-supervision-recovery': '2026-09-27T20:16:17.225985-04:00'}
BASES = {'t16-protocol-recovery':'t16-seal-recovery','t16-seal-recovery':'t16-lease-recovery','t15-lease-recovery':'t15-supervision-recovery', 't16-lease-recovery':'t16-supervision-recovery','t15-supervision-recovery': 't15-setup-recovery', 't16-supervision-recovery': 't16'}
GROUP_ID = 'bfs-supervision-recovery-linux-20260926-a1'
OLD_GROUP = 'bfs-t15-setup-recovery-linux-20260926-a1'
OLD_T16 = 'bfs-t16-simulator-batch-20260926-a1'
SUPPLEMENT_SELECTORS = [
    'tests/test_bfs_owned_rss.py',
    'tests/test_bfs_owned_execution.py::test_identity_esrch_exit_requires_independently_absent_directory',
    'tests/test_bfs_owned_execution.py::test_identity_esrch_reopens_actual_identity_and_rss',
    'tests/test_bfs_owned_execution.py::test_identity_does_not_suppress_ambiguous_or_invalid_telemetry',
    'tests/test_bfs_owned_execution.py::test_signal_never_admits_reused_or_unknown_identity',
    'tests/test_bfs_linux_fixture_audit.py::test_real_file_lock_and_exact_generation',
    'tests/test_bfs_linux_fixture_audit.py::test_historical_closure_allows_successor_and_records_current_occupancy',
    'tests/test_bfs_linux_fixture_audit.py::test_second_observation_allows_independently_verified_successor_lease',
]


LEASE_GROUP_ID = 'bfs-supervision-lease-recovery-linux-20260927-a1'
LEASE_SELECTORS = ['tests/test_bfs_simulator_batch.py::'+name for name in (
    'test_other_socket_transition_requires_stable_real_lock_snapshot',
    'test_other_socket_persistent_disagreement_is_bounded',
    'test_snapshot_retry_never_tolerates_own_change_or_legacy_conflict',
    'test_other_socket_metadata_changes_during_kernel_probe_are_not_returned',
    'test_external_generations_must_stabilize_before_return',
    'test_other_socket_can_be_legally_held_without_disrupting_this_lane')]


LEASE_SUPPLEMENT_SELECTORS = SUPPLEMENT_SELECTORS + LEASE_SELECTORS


SEAL_GROUP_ID = 'bfs-seal-recovery-linux-20260927-a1'
SEAL_SELECTORS = ['tests/test_dx100_witness.py::test_large_producer_seal_retains_all_progress_and_full_validation', 'tests/test_dx100_witness.py::test_large_diagnostic_seal_uses_same_bound_and_exact_bytes', 'tests/test_dx100_witness.py::test_large_seal_bound_and_regular_identity_still_fail_closed', 'tests/test_dx100_witness.py::test_producer_serialization_unchanged_and_oversize_never_published', 'tests/test_dx100_witness.py::test_large_seal_hash_valid_json_still_requires_exact_retained_object']
SEAL_SUPPLEMENT_SELECTORS = LEASE_SUPPLEMENT_SELECTORS + SEAL_SELECTORS
PROTOCOL_GROUP_ID = 'bfs-protocol-recovery-linux-20260927-a1'
PROTOCOL_SUPPLEMENT_SELECTORS = SEAL_SUPPLEMENT_SELECTORS


def supplement_selectors(plan):
    if 'seal_recovery' in plan['accounting']: return SEAL_SUPPLEMENT_SELECTORS
    return SUPPLEMENT_SELECTORS + (LEASE_SELECTORS if 'lease_recovery' in plan['accounting'] else [])


def failed_lease_batch(plan, base):
    """Charge the immutable failed T15 and its independent closure without qualification."""
    b=batch_api();entry=plan['accounting']['lease_recovery']['failed_batch']
    ref=entry['closure_observation'];path=b.ROOT/ref['repository_path']
    value=b.read_reference({'path':str(path),'sha256':ref['sha256']}, maximum=16*1024**2)
    driver=b.read_reference(entry['driver'],maximum=16*1024**2)
    b.require(driver['id']==base['id']==entry['id']==IDS['t15-supervision-recovery']
              and driver['plan']==base and driver['state']=='failed'
              and driver['reason']=='ValueError: other lease metadata and kernel lock disagree'
              and driver['outer_deadline']==ENDS['t15-supervision-recovery'],
              'failed lease batch identity or original envelope changed')
    b.require(value['driver_reference']==entry['driver'] and value['cleanup_ledger_reference']==entry['ledger']
              and value['owned_closure_verified'] is True and value['identity_count']==280
              and value['series']['samples']==[] and value['public_primary']['reference']==entry['evaluation'],
              'failed lease batch closure provenance changed')
    from scripts.bfs_simulator_batch_terminal import validate_cleanup_ledger
    validate_cleanup_ledger(entry['driver'],entry['ledger'],expected_run_id=entry['id'],
        expected_outer_start=driver['outer_started'],expected_deadline=driver['outer_deadline'],current=b.now())
    correction=value['accounting_correction'];closed=b.stamp(entry['closed_at']);outer=b.stamp(driver['outer_started'])
    b.require(correction['outer_elapsed_seconds_ceiling']==3415,'failed execution cost changed')
    b.require(math.ceil((closed-outer).total_seconds())==entry['elapsed_seconds']==4551
              and closed==b.stamp(value['observed_at'])<=b.now()
              and entry['outer_execution_seconds']==3415,'failed closure wall charge changed')
    for rows in value['identity_observations']:
        current_closed(rows,driver['process_observations']['pane_identity'])
    evaluation=b.read_reference(entry['evaluation'],maximum=16*1024**2)
    b.require(evaluation['outcome']=={'state':'interrupted','stage':'simulation','reason':'interrupted by SIGTERM'}
              and evaluation['correctness']=={'state':'unverified','checks':[]},'failed public result was promoted')
    b.require(entry['storage_paths']==driver['storage_paths']
              and b.allocated_bytes(entry['storage_paths'])==entry['retained_bytes']==1433210880,
              'failed lease batch final storage changed')
    return {'id':entry['id'],'elapsed_seconds':entry['elapsed_seconds'],'raw_bytes':entry['retained_bytes']}



# The successful 2026-09-27 group tested this immutable runtime. Only its two
# consumer readers may differ in the new batch; no tested primitive is waived.
PROOF_COMMIT = '8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
PROOF_MAP_DIGEST = 'd8529ea6c79f9da1b5998b83eef1f42022b3647c25f598844c74ffe1be8bfa5e'
PROOF_CONSUMERS = {
    'scripts/bfs_simulator_batch.py':'b08335b912e5e83e58f366ed5294c32c2de06073600c8faf4fe2cb370918b4e6',
    'scripts/bfs_simulator_recovery.py':'e242c904684bd0e433d0c9501c3c1cd2d8e2f342db8188cfe1894b829d657744'}
PROOF_PROVENANCE = {'code_commit':PROOF_COMMIT, 'runtime_sha256_digest':PROOF_MAP_DIGEST,
    'consumer_only_exceptions':PROOF_CONSUMERS, 'evidence_kind':'contract_fixture'}


PROOF_COMPAT_COMMIT = '6a493a0d489d8d1c76eba8c3431538d6412fd45a'
PROOF_COMPAT_CONSUMERS = {'scripts/bfs_simulator_batch.py': '0ffcc7ef83b0be924d8f3c793110e112c9c5e8e6515547f2e233909b5e425183', 'scripts/bfs_simulator_recovery.py': 'bea576ee47e69b56cd33d9d048a041a03613d48f34b59dc78e2603e0347ec64c'}


def proof_admission(admission):
    """Keep actual proof identity separate from the current execution runtime."""
    b=batch_api()
    declared=admission.get('linux_proof_runtime')
    if declared is None:return admission  # Original exact-runtime admissions.
    b.require(isinstance(declared,dict) and set(declared)=={'code_commit','runtime_sha256'}
              and declared['code_commit']==PROOF_COMMIT
              and artifacts.digest(declared['runtime_sha256'])==PROOF_MAP_DIGEST,
              'Linux proof provenance differs from the immutable successful group')
    old,current=declared['runtime_sha256'],admission['runtime_sha256']
    b.require(admission['code_commit']==PROOF_COMPAT_COMMIT
              and all(current.get(name)==digest for name,digest in PROOF_COMPAT_CONSUMERS.items()),
              'historical proof compatibility is restricted to the exact 6a readers')
    b.require(set(old)==set(current) and all(old[name]==digest for name,digest in PROOF_CONSUMERS.items())
              and all(current[name]==digest for name,digest in old.items() if name not in PROOF_CONSUMERS),
              'current runtime changes a tested primitive or proof dependency')
    return {**admission,'code_commit':PROOF_COMMIT,'runtime_sha256':old}


def batch_api():
    from scripts import bfs_simulator_batch
    return bfs_simulator_batch


def kind(plan):
    found = [key for key, rid in IDS.items() if rid == plan.get('id')]
    batch_api().require(len(found) == 1, 'unsupported supervision recovery identity')
    return found[0]


def hard_end(plan):
    b = batch_api(); key = kind(plan)
    b.require(plan.get('clock_policy') == {
        'method': 'original_absolute_end_clamp.v1', 'absolute_end': ENDS[key]},
        'supervision recovery cannot change the original hard end')
    return b.stamp(ENDS[key])


def base_plan(plan):
    b = batch_api(); key = kind(plan); base = BASES[key]
    filename = IDS[base]+'.json' if base in IDS else 'bfs-'+base+'-simulator-batch-20260926-a1.json'
    value = json.loads((b.PLAN_DIR / filename).read_text())
    b.validate_plan(value, base)
    return value


def same_ref(a, c):
    return all(a.get(k) == c.get(k) for k in ('path', 'sha256'))


def current_closed(rows, pane):
    """Read exact retained identities; never signal or infer absence from RSS."""
    b = batch_api(); seen = set()
    b.require(isinstance(rows, list) and 0 < len(rows) <= 4096, 'retained ownership union missing or oversized')
    for row in rows:
        key = (row.get('pid'), row.get('start_ticks'))
        b.require(all(type(n) is int and n > 0 for n in key) and key not in seen,
                  'retained ownership identity is malformed or duplicated')
        seen.add(key); live = owned.identity(key[0])
        if live is not None and live['start_ticks'] == key[1]:
            b.require(key == (pane['pid'], pane['start_ticks']) and live['state'] == 'Z'
                      and live['rss_bytes'] == 0, 'retained failed work still has a live or unknown owner')
    b.require((pane['pid'], pane['start_ticks']) in seen, 'retained union omits its exact pane')


def failed_group(plan, base):
    """Retain consumed a4 reservation; its pending interruption never becomes proof."""
    b = batch_api(); entry = plan['accounting']['supervision_recovery']['failed_proof_group']
    old = base['accounting']['preparation_reservation']
    b.require(old['id'] == entry['id'] == OLD_GROUP and old['elapsed_seconds'] == 600
              and old['raw_bytes'] == 2*b.GIB, 'failed proof reservation cannot be replaced or refunded')
    observation = b.read_reference(entry['observation'], maximum=16*1024**2)
    preflight = b.read_reference(observation['group_preflight'])
    b.require(observation.get('id') == OLD_GROUP and observation.get('state') == 'failed'
              and observation.get('proof_group_admissible') is False
              and observation.get('code_commit') == entry['code_commit'] == preflight.get('code_commit')
              and observation.get('reservation_seconds') == 600
              and observation.get('reservation_bytes') == 2*b.GIB
              and preflight.get('id') == OLD_GROUP and preflight.get('storage_paths') == old['storage_paths'],
              'failed a4 proof-group identity or original reservation changed')
    start, end = b.stamp(observation['original_started']), b.stamp(entry['closed_at'])
    b.require(start == b.stamp(preflight['observed_at'])
              and b.stamp(observation['original_deadline']) == start+timedelta(seconds=600)
              and start <= b.stamp(observation['observed_at']) <= end <= start+timedelta(seconds=600)
              and end <= b.now(), 'failed proof group escaped its original envelope')
    b.require(set(observation['fixtures']) == {'owned_cleanup', 'dx100_interruption'},
              'failed group selection changed')
    for name, row in observation['fixtures'].items():
        expected = old['selections'][name]; refs = row['refs']
        driver = b.read_reference(refs['driver']); audit = b.read_reference(refs['audit'])
        current_closed(row['owned_union'], driver['process_observations']['pane_identity'])
        b.require(row['id'] == expected == driver['id'] and driver['state'] == 'complete'
                  and audit['returncode'] == row['audit_returncode'] == (0 if name == 'owned_cleanup' else 1)
                  and row['current_owned_processes_closed'] is True,
                  'failed proof-group outcome or identity changed')
        for ref in refs.values():
            if ref is not None:
                path = Path(ref['path'])
                b.require(path.is_absolute() and path.is_file() and not path.is_symlink()
                          and artifacts.file_hash(path) == ref['sha256'], 'failed proof artifact changed')
        if name == 'dx100_interruption':
            raw = Path(refs['driver']['path']).parent
            b.require(refs['proof'] is None and refs['terminal_audit'] is None
                      and not (raw/'proof.json').exists() and not (raw/'terminal-audit.json').exists(),
                      'failed a4 interruption pending was promoted or re-audited')
        current_closed(row['owned_union'], driver['process_observations']['pane_identity'])
    b.require(b.allocated_bytes(old['storage_paths']) == entry['retained_bytes'] == 1548288,
              'closed failed proof-group bytes changed')


def failed_t16(plan, base):
    """Cost-only exception for one immutable failed ledger, never a pass verdict."""
    b = batch_api(); entry = plan['accounting']['supervision_recovery']['failed_batch']
    driver = b.read_reference(entry['driver'], maximum=16*1024**2)
    audit = b.read_reference(entry['terminal'], maximum=16*1024**2)
    accounting = b.read_reference(entry['accounting'])
    ledger = b.read_reference(entry['ledger'])
    b.require(len(audit.get('owned_processes', [])) == 944
              and len([r for r in audit['owned_processes'] if r.get('pid') == 3089858
                       and type(r.get('start_ticks')) is int and r['start_ticks'] > 0]) == 1,
              'failed T16 retained union or outstanding reservation owner is incomplete')
    current_closed(audit['owned_processes'], driver['process_observations']['pane_identity'])
    b.require(entry['id'] == OLD_T16 == driver.get('id') == audit.get('id')
              and driver.get('state') == audit.get('state') == 'failed'
              and driver.get('code_commit') == entry['code_commit'] == audit.get('repository_commit')
              and driver.get('plan') == base
              and driver.get('reason') == 'ProcessLookupError: [Errno 3] No such process'
              and driver.get('outer_deadline') == ENDS['t16-supervision-recovery'],
              'fixed failed T16 identity, reason, plan or hard end changed')
    for field, expected in (('driver', entry['driver']), ('cleanup_ledger', entry['ledger'])):
        b.require(same_ref(audit.get(field, {}), expected), 'failed T16 audit reference differs')
    b.require(audit.get('lease_released') is True and audit.get('complete_retained_identity_union') is True
              and audit.get('cleanup_state') in {'terminal_and_reaped', 'terminal_no_live_owned_processes'}
              and audit.get('cleanup_budget_admissible') is False
              and accounting.get('admitted_cleanup_budget') is False
              and accounting.get('admitted_storage') is False
              and same_ref(accounting.get('driver', {}), entry['driver'])
              and same_ref(accounting.get('terminal', {}), entry['terminal']),
              'failed T16 operational closure or failed accounting verdict changed')
    lane = b.read_reference(audit['lane'])['socket_lane']; exit_code = b.read_reference(audit['outer_exit'])
    runs = Path(entry['storage_paths'][0]); dispatch = Path(str(runs)+'.dispatch')
    b.require(entry['storage_paths'] == list(map(str, (runs, dispatch)))
              and runs.name == OLD_T16 and Path(entry['terminal']['path']) == dispatch/'terminal-validation.json'
              and Path(audit['lane']['path']) == dispatch/'lane.json'
              and Path(audit['outer_exit']['path']) == dispatch/'outer.exit'
              and type(exit_code) is int and exit_code == lane.get('exit_code') == 1
              and lane.get('host') == 'mbit10' and lane.get('job') == OLD_T16
              and lane.get('node') == 0 and lane.get('lease_generation') == audit.get('lease_generation') == 332,
              'failed T16 helper, exit, lane or storage root differs')
    outer, finished, closed = map(b.stamp, (driver['outer_started'], driver['finished'], entry['closed_at']))
    lane_start, lane_end = map(b.stamp, (lane['started_utc'], lane['ended_utc']))
    b.require(outer < lane_start+timedelta(seconds=1) and lane_start <= b.stamp(driver['started'])
              and outer <= finished < lane_end+timedelta(seconds=1)
              and finished <= b.stamp(audit['observed_at']) <= b.stamp(accounting['observed_at']) <= closed <= b.now(),
              'failed T16 closed envelope does not cover all execution and audit work')
    seconds = math.ceil(max((closed-outer).total_seconds(), (lane_end+timedelta(seconds=1)-outer).total_seconds()))
    b.require(seconds == entry['elapsed_seconds'] == 11121, 'failed T16 wall charge differs')
    # The old strict reader must still reject. Do not settle its reservation or
    # manufacture a missing successful final storage snapshot.
    from scripts.bfs_simulator_batch_terminal import validate_cleanup_ledger
    try:
        validate_cleanup_ledger({k:entry['driver'][k] for k in ('path','sha256')},
            {k:entry['ledger'][k] for k in ('path','sha256')}, expected_run_id=OLD_T16,
            expected_outer_start=driver['outer_started'], expected_deadline=driver['outer_deadline'], current=b.now())
    except ValueError as exc:
        b.require(str(exc) == 'final cleanup ledger has outstanding reservations',
                  'failed T16 has an additional unreviewed cleanup inconsistency')
    else:
        raise ValueError('failed T16 ledger was retrospectively settled')
    reservation = {'b3aac8d5d3bc45ca83bf59b152ce8b3b': {'pid':3089858, 'seconds':5,
        'started':'2026-09-26T23:20:50.936598-04:00', 'purpose':'cleanup_or_finalization'}}
    events = ledger.get('events', [])
    b.require(ledger.get('reservations') == reservation and len(events) == 117
              and all(e.get('exceeded_grant') is False and type(e.get('elapsed_seconds')) in (int,float)
                      and math.isfinite(e['elapsed_seconds']) and 0 < e['elapsed_seconds'] <= e['seconds'] for e in events)
              and math.isclose(math.fsum(e['elapsed_seconds'] for e in events), ledger['spent_seconds'], abs_tol=1e-9)
              and math.isclose(ledger['spent_seconds'], 20.94487111307685, rel_tol=0, abs_tol=1e-9)
              and entry['conservative_cleanup_seconds'] == 25.94487111307685,
              'failed T16 settled or full outstanding reservation charge changed')
    current_closed(audit['owned_processes'], driver['process_observations']['pane_identity'])
    path = Path(entry['evaluation']['path'])
    b.require(same_ref(audit['evaluation'], entry['evaluation']) and path.is_file()
              and not path.is_symlink() and artifacts.file_hash(path) == entry['evaluation']['sha256'],
              'failed T16 public record changed')
    evaluation = yamlio.load(path)
    b.require(evaluation.get('outcome') == {'state':'running','stage':'simulation','reason':None}
              and evaluation.get('correctness') == {'state':'unverified','checks':[]}
              and evaluation.get('timing') == [] and audit.get('completed_samples') == 0,
              'failed T16 stale public marker was promoted or replaced')
    b.require(b.allocated_bytes(b.batch_storage_paths(runs)) == entry['retained_bytes'] == 658644992,
              'failed T16 closed storage changed')
    prior = b.preparation_charges(base)
    b.require(prior == driver['preparation_charges'], 'failed T16 prior costs differ')
    current_closed(audit['owned_processes'], driver['process_observations']['pane_identity'])
    return prior + [{'id':OLD_T16, 'elapsed_seconds':seconds, 'raw_bytes':entry['retained_bytes']}]


def preparation_charges(plan):
    b = batch_api(); base = base_plan(plan)
    if 'protocol_recovery' in plan['accounting']:
        recovery = plan['accounting']['protocol_recovery']
        b.require(kind(plan) == 't16-protocol-recovery' and recovery['base_kind'] == BASES[kind(plan)]
                  and recovery['base_plan_sha256'] == artifacts.digest(base)
                  and recovery['prior_proof_reservation'] == base['accounting']['preparation_reservation']
                  and recovery['proof_runtime_policy'] == 'exact_current_runtime_only_no_consumer_exceptions'
                  and 'linux_proof_provenance' not in plan, 'protocol recovery lineage changed')
        rows = preparation_charges(base)
        rows.append(failed_protocol_batch(plan, base))
        fresh = plan['accounting']['preparation_reservation']
        b.require(fresh['id'] == PROTOCOL_GROUP_ID and fresh['elapsed_seconds'] == 600
                  and fresh['raw_bytes'] == 2*b.GIB, 'fresh protocol proof reservation changed')
        rows.append({k:fresh[k] for k in ('id','elapsed_seconds','raw_bytes')})
        b.require(len({r['id'] for r in rows}) == len(rows)
                  and sum(r['elapsed_seconds'] for r in rows) == 15613
                  and sum(r['raw_bytes'] for r in rows) == 10391474176, 'protocol recovery cumulative charge changed')
        return rows
    if 'seal_recovery' in plan['accounting']:
        recovery=plan['accounting']['seal_recovery']
        b.require(kind(plan)=='t16-seal-recovery' and recovery['base_kind']==BASES[kind(plan)]
                  and recovery['base_plan_sha256']==artifacts.digest(base)
                  and recovery['prior_proof_reservation']==base['accounting']['preparation_reservation']
                  and recovery['proof_runtime_policy']=='exact_current_runtime_only_no_consumer_exceptions'
                  and 'linux_proof_provenance' not in plan,'seal recovery cannot replace its fixed original lineage')
        rows=preparation_charges(base)
        fresh=plan['accounting']['preparation_reservation']
        b.require(fresh['id']==SEAL_GROUP_ID and fresh['elapsed_seconds']==600 and fresh['raw_bytes']==2*b.GIB,
                  'fresh seal proof reservation changed')
        rows.append({k:fresh[k] for k in ('id','elapsed_seconds','raw_bytes')})
        b.require(len({r['id'] for r in rows})==len(rows),'seal recovery repeats a cost')
        return rows
    if 'lease_recovery' in plan['accounting']:
        recovery=plan['accounting']['lease_recovery']
        b.require(recovery['base_kind']==BASES[kind(plan)] and recovery['base_plan_sha256']==artifacts.digest(base)
                  and recovery['prior_proof_reservation']==base['accounting']['preparation_reservation']
                  and recovery['proof_runtime_policy']=='exact_current_runtime_only_no_consumer_exceptions'
                  and 'linux_proof_provenance' not in plan,'lease recovery cannot reuse historical proof exceptions')
        rows=preparation_charges(base)
        if kind(plan)=='t15-lease-recovery':rows.append(failed_lease_batch(plan,base))
        fresh=plan['accounting']['preparation_reservation']
        b.require(fresh['id']==LEASE_GROUP_ID and fresh['elapsed_seconds']==600 and fresh['raw_bytes']==2*b.GIB,
                  'fresh lease proof reservation changed')
        rows.append({k:fresh[k] for k in ('id','elapsed_seconds','raw_bytes')})
        b.require(len({r['id'] for r in rows})==len(rows),'lease recovery repeats a cost')
        return rows
    if kind(plan) == 't15-supervision-recovery':
        failed_group(plan, base)
        rows = b.preparation_charges(base)  # Includes failed a4's FULL reservation.
    else:
        rows = failed_t16(plan, base)
    fresh = plan['accounting']['preparation_reservation']
    b.require(fresh['id'] == GROUP_ID and fresh['elapsed_seconds'] == 600 and fresh['raw_bytes'] == 2*b.GIB,
              'fresh recovery proof reservation changed')
    rows.append({k:fresh[k] for k in ('id','elapsed_seconds','raw_bytes')})
    b.require(len({r['id'] for r in rows}) == len(rows), 'recovery costs repeat a row')
    return rows



def retained_supplement_closure(terminal, lane, union, pane, begin, end):
    """Reopen two actual post-exit snapshots; a release boolean is insufficient."""
    b=batch_api(); leases=terminal.get('lease_observations'); processes=terminal.get('process_observations')
    times=terminal.get('observation_times'); names={'mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'}
    b.require(isinstance(leases,list) and len(leases)==2 and isinstance(processes,list) and len(processes)==2
              and isinstance(times,list) and len(times)==2, 'supplement requires two retained lease/process observations')
    first,second=map(b.stamp,times); observed=b.stamp(terminal['observed_at']); lane_end=b.stamp(lane['ended_utc'])
    b.require(max(begin,lane_end) <= first <= second <= observed, 'supplement closure observations precede helper exit')
    for snapshot,rows,at in zip(leases,processes,(first,second)):
        b.require(set(snapshot)==names, 'supplement closure omits a socket or legacy lease')
        for name,row in snapshot.items():
            metadata=row.get('metadata',{}); held=row.get('kernel_held')
            b.require(type(held) is bool and metadata.get('state')==('held' if held else 'released'),
                      'supplement lease metadata disagrees with kernel observation')
            if name==lane['lease_name']:
                lease=metadata.get('lease',{}); generation=lease.get('generation')
                b.require(type(generation) is int and generation>=lane['lease_generation']
                          and lease.get('host')=='mbit10' and lease.get('lease_name')==name,
                          'supplement observed lease identity differs')
                acquired=b.stamp(lease['acquired_at'])
                if generation==lane['lease_generation']:
                    b.require(not held and begin-timedelta(seconds=1)<=acquired<=end
                              and lane_end<=b.stamp(metadata['released_at'])<end+timedelta(seconds=1)
                              and b.stamp(metadata['released_at'])<=at,
                              'supplement exact generation was not independently released')
                else:
                    b.require(lane_end<=acquired<=at, 'supplement successor predates prior release')
                    if not held:b.require(acquired<=b.stamp(metadata['released_at'])<=at,'supplement successor release is invalid')
        b.require(isinstance(rows,list) and len(rows)==len(union)
                  and {(r.get('pid'),r.get('start_ticks')) for r in rows}==union,
                  'supplement observation omits or duplicates a retained identity')
        for row in rows:
            key=(row['pid'],row['start_ticks']); current=row.get('current_identity')
            b.require((row.get('state')=='absent' and (current is None or
                       (current.get('pid'),current.get('start_ticks'))!=key)) or
                      (key==pane and row.get('state')=='Z' and row.get('rss_bytes')==0
                       and row.get('role')=='tmux_launcher'), 'supplement retained observation has live/unknown work')


def validate_supplement(plan, admission):
    """Separate fixed tests are evidence inside the group, not a third proof kind."""
    b = batch_api(); reservation = plan['accounting']['preparation_reservation']
    actual = admission['preparation_reservation']; group = Path(reservation['storage_paths'][-1])
    if 'lease_recovery' in plan['accounting']:
        b.require('linux_proof_runtime' not in admission, 'fresh lease proof cannot use historical runtime aliases')
    ref = actual['supplement']; value = b.read_reference(ref, maximum=4*1024**2)
    _validate_supplement_value(plan, admission, ref, value)


def _validate_supplement_value(plan, admission, ref, value):
    """Shared reader for retained evidence and pre-publication producer validation."""
    b = batch_api(); reservation = plan['accounting']['preparation_reservation']
    actual = admission['preparation_reservation']; group = Path(reservation['storage_paths'][-1])
    b.require(Path(ref['path']) == group/'supplement.readback.json'
              and value.get('format') == 'swdb.bfs.supervision-supplement.v1'
              and value.get('state') == 'passed' and value.get('code_commit') == admission['code_commit']
              and value.get('runtime_sha256') == admission['runtime_sha256']
              and type(value.get('returncode')) is int and value['returncode'] == 0,
              'supplement is missing, failed or uses another runtime')
    pre = b.read_reference(actual['preflight']); start, finish = map(b.stamp,(value['started'],value['finished']))
    b.require(b.stamp(pre['observed_at']) <= start <= finish <= b.stamp(actual['finished'])
              and (finish-start).total_seconds() <= 90, 'supplement exceeds its original finite stage')
    command = value['command']; junit = value['junit']; stdout = value['stdout']
    expected = [command[0],'-m','pytest',*supplement_selectors(plan),'-q','-p','no:cacheprovider',
                '--junitxml='+junit['path'],'--basetemp='+str(group/'supplement/pytest')]
    b.require(command == expected and Path(command[0]).is_absolute()
              and Path(command[0]).resolve()==Path(admission['python']['path']).resolve()
              and value.get('selectors') == supplement_selectors(plan),
              'supplement must run the full fixed RSS suite and exact lease-reader cases')
    for item in (junit, stdout, value['stderr']):
        p = Path(item['path'])
        b.require(group in p.parents and p.is_file() and not p.is_symlink()
                  and p.stat().st_size <= 16*1024**2 and artifacts.file_hash(p) == item['sha256'],
                  'supplement artifact is unsafe, changed or oversized')
    cases = XML.fromstring(Path(junit['path']).read_bytes()).findall('.//testcase')
    names = [case.get('name') for case in cases]
    expected_names = reservation['supplement_testcases']
    b.require(len(names) == len(set(names)) == len(expected_names) and set(names) == set(expected_names)
              and all(not any(case.find(tag) is not None for tag in ('failure','error','skipped')) for case in cases),
              'supplement failed, skipped, duplicated or omitted an exact required case')
    terminal = b.read_reference(value['terminal_audit'], maximum=16*1024**2)
    lane = b.read_reference(terminal['lane'])['socket_lane']; outer_exit = b.read_reference(terminal['outer_exit'])
    b.require(Path(value['terminal_audit']['path']) == group/'supplement/terminal-validation.json'
              and terminal.get('id') == reservation['id']+'.supplement' and terminal.get('state') == 'complete'
              and terminal.get('code_commit') == admission['code_commit']
              and terminal.get('lease_released') is True and terminal.get('complete_retained_identity_union') is True
              and terminal.get('cleanup_state') in {'terminal_and_reaped','terminal_no_live_owned_processes'}
              and type(outer_exit) is int and outer_exit == lane.get('exit_code') == 0
              and lane.get('job') == terminal['id'] and lane.get('host') == 'mbit10'
              and lane.get('lease_generation') == terminal.get('lease_generation')
              and finish <= b.stamp(terminal['observed_at']) <= b.stamp(value['audited_at']) <= b.stamp(actual['finished']),
              'supplement lacks independent exact lane/exit/identity closure')
    driver = b.read_reference(terminal['driver'], maximum=4*1024**2)
    b.require(driver.get('state') == 'complete' and driver.get('command') == command
              and driver.get('code_commit') == admission['code_commit']
              and driver.get('runtime_sha256') == admission['runtime_sha256']
              and driver.get('started') == value['started'] and driver.get('finished') == value['finished']
              and b.stamp(driver['outer_deadline']) == start+timedelta(seconds=90)
              and driver.get('bounds') == {'outer_seconds':90,'work_seconds':60,'cleanup_seconds':30,
                                          'sampled_rss_bytes':512*1024**2,'output_bytes':512*1024**2},
              'supplement closure does not bind its actual driver')
    lane_start, lane_end = map(b.stamp, (lane['started_utc'], lane['ended_utc']))
    b.require(lane.get('node') in (0,1) and lane.get('lease_name') == 'mbit10-evaluation-node'+str(lane['node'])
              and type(lane.get('lease_generation')) is int and lane['lease_generation'] > 0
              and start < lane_start+timedelta(seconds=1) and lane_start <= finish
              and finish < lane_end+timedelta(seconds=1) and lane_end <= start+timedelta(seconds=90),
              'supplement helper escaped its original clock or lane')
    b.require(b.allocated_bytes([group/'supplement']) <= 512*1024**2,
              'supplement final retained output exceeded512MiB')
    current_closed(terminal['owned_processes'], driver['process_observations']['pane_identity'])
    from scripts import bfs_linux_fixture_audit as audit_reader
    reader = audit_reader.Reader(time.monotonic()+30)
    executable = driver['runtime']['python']
    reader.raw(executable)
    b.require(Path(executable['path'])==Path(command[0]).resolve()
              and ('sha256' not in admission['python'] or executable['sha256']==admission['python']['sha256']),
              'supplement executable differs from the pinned Python bytes')
    end = b.stamp(driver['outer_deadline']); ledger_ref = terminal['cleanup_ledger']['ledger']
    b.require(Path(ledger_ref['path']) == group/'supplement/cleanup-ledger.json',
              'supplement cleanup ledger is outside its fixed root')
    budget = audit_reader.ledger_check(reader, ledger_ref, driver, start, end)
    b.require(budget == terminal['cleanup_ledger'], 'supplement final settled ledger differs from audit')
    audit_reader.cleanup(driver['cleanup'], ledger_ref['path'])
    union = {(r['pid'],r['start_ticks']) for r in terminal['owned_processes']}
    declared = driver['process_observations']; chain = declared['ancestry']
    ident = lambda row: (row.get('pid'),row.get('start_ticks'))
    b.require(isinstance(chain,list) and 0 < len(chain) <= 128
              and ident(chain[0]) == ident(declared['driver_identity'])
              and ident(chain[-1]) == ident(declared['pane_identity'])
              and len({ident(row) for row in chain}) == len(chain)
              and all(child.get('parent_pid') == parent.get('pid') for child,parent in zip(chain,chain[1:])),
              'supplement ancestry is not the continuous exact driver-to-pane chain')
    rows = chain+declared['owned_processes']
    rows += [declared['driver_identity'],declared['pane_identity']]+driver['cleanup']['observed']
    b.require(len(driver['stages']) == 1, 'supplement must contain one fixed pytest child')
    stage = driver['stages'][0]
    b.require(stage.get('state') == 'complete' and type(stage.get('returncode')) is int
              and stage['returncode'] == 0 and stage.get('command') == command
              and start <= b.stamp(stage['started']) <= b.stamp(stage['finished']) <= finish
              and b.stamp(driver['work_deadline']) == start+timedelta(seconds=60)
              and type(stage.get('timeout_s')) in (int,float) and math.isfinite(stage['timeout_s'])
              and 0 < stage['timeout_s'] <= (start+timedelta(seconds=60)-b.stamp(stage['started'])).total_seconds()
              and stage.get('identity',{}).get('parent_pid') == declared['driver_identity']['pid']
              and stage.get('output') == stdout['path'] and stage.get('stdout_sha256') == stdout['sha256']
              and stage.get('stderr') == value['stderr']['path'] and stage.get('stderr_sha256') == value['stderr']['sha256'],
              'supplement child, output binding or original work clock differs')
    audit_reader.cleanup(stage['cleanup'], ledger_ref['path'])
    rows += [stage['identity']]+stage['cleanup']['observed']
    samples = reader.raw(driver['resource_samples'],64*1024**2)
    b.require(driver['resource_samples']['path'] == str(group/'supplement/resources.jsonl'),
              'supplement resource stream has an unexpected path')
    coverage = owned.validate_samples(Path(driver['resource_samples']['path']),value['started'],value['finished'])
    b.require(coverage['peak_sampled_rss_bytes'] <= 512*1024**2, 'supplement sampled memory exceeded512MiB')
    lane_rows = 0
    for line in samples.splitlines():
        sample = json.loads(line); rows += sample['processes']
        b.require(type(sample.get('output_bytes')) is int and 0 <= sample['output_bytes'] <= 512*1024**2,
                  'supplement sampled output exceeded512MiB')
        b.require((declared['driver_identity']['pid'],declared['driver_identity']['start_ticks']) in
                  {(r['pid'],r['start_ticks']) for r in sample['processes']}, 'supplement sample omits driver')
        if 'lane' in sample:
            held = sample['lane']['leases'][lane['lease_name']]['metadata']
            b.require(held.get('state') == 'held' and held['lease']['generation'] == lane['lease_generation'],
                      'supplement sampled lease differs')
            lane_rows += 1
    b.require(lane_rows > 0 and {(r['pid'],r['start_ticks']) for r in rows} <= union,
              'supplement audit omits sampled, direct, adopted or ancestor identity')
    retained_supplement_closure(terminal,lane,union,ident(declared['pane_identity']),start,end)
    reader.recheck()
    current_closed(terminal['owned_processes'], declared['pane_identity'])


def failed_protocol_batch(plan, base):
    """Charge closed preparation failure; never turn it into execution evidence."""
    b = batch_api(); entry = plan['accounting']['protocol_recovery']['failed_batch']
    ref = entry['closure_observation']
    audit = b.read_reference({'path': str(b.ROOT/ref['repository_path']), 'sha256': ref['sha256']}, maximum=16*1024**2)
    driver = b.read_reference(entry['driver'], maximum=16*1024**2)
    b.require(driver['id'] == base['id'] == entry['id'] == IDS['t16-seal-recovery']
              and driver['plan'] == base and driver['state'] == 'failed'
              and driver['reason'] == 'ValueError: public stage exited 1'
              and driver['outer_deadline'] == ENDS['t16-seal-recovery'], 'failed protocol batch identity changed')
    b.require(audit['driver_reference'] == entry['driver'] and audit['cleanup_ledger_reference'] == entry['ledger']
              and audit['strict_cleanup_ledger']['passed'] is True and audit['identity_count'] == 106
              and audit['series']['samples'] == [] and audit['outer_exit'] == '1', 'failed protocol closure changed')
    from scripts.bfs_simulator_batch_terminal import validate_cleanup_ledger
    validate_cleanup_ledger(entry['driver'], entry['ledger'], expected_run_id=entry['id'],
        expected_outer_start=driver['outer_started'], expected_deadline=driver['outer_deadline'], current=b.now())
    closed = b.stamp(entry['closed_at'])
    b.require(closed == b.stamp(audit['observed_at']) <= b.now()
              and math.ceil((closed-b.stamp(driver['outer_started'])).total_seconds()) == entry['elapsed_seconds'] == 1839,
              'failed protocol closure-inclusive time changed')
    evaluation = b.read_reference(entry['evaluation'], maximum=16*1024**2)
    b.require(evaluation['outcome'] == {'state':'failed', 'stage':'execution_identity',
                  'reason':'actual simulator instrumentation differs from frozen treatment'}
              and evaluation['correctness'] == {'state':'unverified','checks':[]}
              and evaluation['timing'] == [], 'failed protocol outcome was promoted')
    b.require(len(audit['identity_observations']) == 2, 'failed protocol needs two retained identity observations')
    for rows in audit['identity_observations']:
        b.require(len(rows) == audit['identity_count'], 'failed protocol identity union changed')
        current_closed(rows, driver['process_observations']['pane_identity'])
    b.require(entry['storage_paths'] == driver['storage_paths']
              and b.allocated_bytes(entry['storage_paths']) == entry['retained_bytes'] == audit['final_allocated_bytes'] == 11907072,
              'failed protocol retained storage changed')
    b.require(preparation_charges(base) == driver['preparation_charges'], 'failed protocol prior charges differ')
    return {'id':entry['id'], 'elapsed_seconds':entry['elapsed_seconds'], 'raw_bytes':entry['retained_bytes']}


def validate_protocol_runtime(plan, protocols):
    """Reject a stale freeze before launching a series; science remains unchanged."""
    import copy
    b = batch_api(); base = base_plan(plan)
    runtime = {key: artifacts.file_hash(b.ROOT/path) for key,path in (
        ('driver_sha256','scripts/dx100_verify.py'), ('parser_sha256','swdb/dx100_witness.py'),
        ('observer_sha256','scripts/dx100_host_memory.py'))}
    b.require(runtime == {'driver_sha256':'476874619644d1256dcc5ca1e853c47b7be2e1dc56f538aaa2dd783842e7ad10',
        'parser_sha256':'c9d3e14b70a3689799314556fab2922b1723c00960902109af2922a958cd3498',
        'observer_sha256':'655c5804e26a0d1f8f7738f23ae62268cafe84562dbf8392af6c0169568146fd'},
        'protocol continuation must retain exact reviewed verifier runtime')
    b.require(set(protocols) == {'artifact','control'}, 'both independent protocols are required')
    for key, protocol in protocols.items():
        original = yamlio.load(b.ROOT/base['protocol_requests'][key]['path'])
        expected = copy.deepcopy(original['settings'])
        for role in ('baseline','candidate'):
            expected['instrumentation'][role]['verifier_runtime'] = copy.deepcopy(runtime)
        b.require(protocol['settings'] == expected,
                  'fresh protocol changes scientific settings or has stale verifier runtime')
