#!/usr/bin/env python3
"""One fixed baseline-only native configuration. Created: 2026-09-26 ET.

Public collectors only; no retry, rewrite, protocol publication, or gain claim.
Run inside the verified node1 helper with TERM18120s/KILL120s outer containment.
"""
import argparse
from contextlib import contextmanager
import copy
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_native_paired_pilot as previous, bfs_native_repeatability as original
from scripts import bfs_owned_observer as observer, bfs_dx100_coverage_execution as coverage
from scripts import dx100_witness_continuation as witness, dx100_capacity
from scripts.bfs_freeze_pilot import require, unchanged, native_lane, packet, sample_grid
from scripts.bfs_paired_calibration import negative_control
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_simulator_batch import OwnedDescendants, lease_observation, package_binding
from scripts.bfs_witness_launch import stop_owned
from swdb import artifacts, bfs_native, bfs_native_pair, bfs_protocol, bfs_coverage, profile_package, yamlio
from swdb.store import Store

ET = ZoneInfo('America/New_York')
RUN_ID = 'bfs-native-one-thread-pilot-20260926-a1'
PLAN = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-one-thread-pilot-20260926-a1.json'
PLAN_SHA = 'a96b98b86d2f90eb1de3e3daa1464589e9ee909a7a0128e7913b82eabc5530db'
LANE = 'mbit10-evaluation-node1'
RUNTIME_DIRS = ('scripts', 'swdb', 'schemas', 'vocab', 'tools/bfs_native')
PYTHON_INPUTS = {**dict.fromkeys(('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE')),
                 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
RAW_ROOTS = original.RAW_ROOTS if hasattr(original, 'RAW_ROOTS') else (
    Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))
BUILDS = Path('/data1/yanruj/EvolveSWDB_builds') / RUN_ID


def now():
    return datetime.now(ET)


def ref(path):
    return {'path': str(Path(path).absolute()), 'sha256': artifacts.file_hash(path)}


def read(refvalue, maximum=32 * 1024**2):
    return json.loads(witness.reference(refvalue, maximum))


def exact(left, right):
    return artifacts.digest(left) == artifacts.digest(right)


def validate_plan(plan):
    require(artifacts.digest(plan) == PLAN_SHA, 'plan differs from the exact prospective scope')
    bfs_native.validate_runtime_policy(plan['native_runtime'], 1)
    return plan


def runtime_inventory(root):
    require(not any((root/name).exists() for name in ('sitecustomize.py', 'usercustomize.py')),
            'runtime contains an untracked Python startup hook')
    return {str(path.relative_to(root)) for folder in RUNTIME_DIRS for path in (root/folder).rglob('*')
            if path.is_file() and '__pycache__' not in path.parts}


def runtime_identity(commit, root=ROOT):
    """Pin the complete project runtime tree, not just directly imported modules."""
    require(isinstance(commit, str) and re.fullmatch('[a-f0-9]{40}', commit), 'caller expected commit is required')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, timeout=15)
    require(git('rev-parse', 'HEAD').decode().strip() == commit, 'checkout differs from caller expected commit')
    names = git('ls-tree', '-r', '--name-only', commit, '--', *RUNTIME_DIRS).decode().splitlines()
    require(names and len(names) <= 2000, 'runtime inventory missing or exceeds bound')
    require(not git('diff', commit, '--', *RUNTIME_DIRS), 'tracked runtime differs from reviewed commit')
    require(runtime_inventory(root) == set(names), 'untracked runtime could shadow reviewed code')
    paths = [root / name for name in names]
    require(all(path.is_file() and not path.is_symlink() for path in paths), 'runtime files are missing or symlinked')
    result = {name: ref(root / name) for name in names}
    result[str(PLAN.relative_to(ROOT))] = ref(root / PLAN.relative_to(ROOT))
    require(not git('diff', commit, '--', str(PLAN.relative_to(ROOT))), 'prospective plan differs from code pin')
    return {'repository_commit': commit, 'root': str(root), 'files': result,
            'python': ref(Path(sys.executable).resolve()), 'python_version': sys.version}


def recheck_runtime(runtime):
    require(runtime_inventory(Path(runtime['root'])) == set(runtime['files'])-{str(PLAN.relative_to(ROOT))}
            and all(artifacts.file_hash(value['path']) == value['sha256'] for value in runtime['files'].values())
            and artifacts.file_hash(runtime['python']['path']) == runtime['python']['sha256'],
            'reviewed runtime changed during collection')


class LockedOwned(OwnedDescendants):
    """Serialize observation and mutating cleanup without changing old clients."""
    def __init__(self):
        super().__init__()
        from scripts.bfs_owned_rss import DescendantRSS
        self.sampler = DescendantRSS(os.getpid())
        self.lock = threading.RLock()
        self.identities = set()

    def sample(self):
        started = time.monotonic()
        require(self.lock.acquire(timeout=30), 'owned sampling lock exceeded its guard allowance')
        try:
            result = super().sample()
            self.identities.update((row['pid'], row['start_ticks']) for row in result['processes'])
            require(time.monotonic()-started <= 30, 'serialized sampling exceeded its guard allowance')
            return result
        finally: self.lock.release()

    def finish(self, seconds=5):
        started = time.monotonic()
        require(seconds > 0 and self.lock.acquire(timeout=seconds), 'owned cleanup lock exhausted its bounded allowance')
        try:
            remaining = seconds-(time.monotonic()-started)
            require(remaining > 0, 'owned cleanup allowance exhausted while waiting for observer')
            result = super().finish(seconds=remaining)
            require(time.monotonic()-started <= seconds, 'serialized cleanup exceeded its bounded allowance')
            return result
        finally: self.lock.release()

    def remember(self, identity):
        require(self.lock.acquire(timeout=30), 'owned identity retention lock exceeded its allowance')
        try:
            self.sampler.known[identity['pid']] = identity['start_ticks']
            self.identities.add((identity['pid'], identity['start_ticks']))
        finally: self.lock.release()

    def retained_identities(self):
        require(self.lock.acquire(timeout=30), 'owned identity snapshot lock exceeded its allowance')
        try:
            return sorted(self.identities | set(self.sampler.known.items()))
        finally: self.lock.release()


def validate_resource_ownership(value, rows, begin, end):
    observed = value.get('process_observations', {})
    driver, pane = observed.get('driver_identity', {}), observed.get('pane_identity', {})
    ancestors = observed.get('ancestry', [])
    def key(row):
        require(isinstance(row, dict) and type(row.get('pid')) is int and row['pid'] > 0
                and type(row.get('start_ticks')) is int and row['start_ticks'] >= 0, 'owned PID/start identity is malformed')
        return row['pid'], row['start_ticks']
    driver_key, pane_key = key(driver), key(pane)
    require(driver['pid'] == value['driver_pid'] and ancestors and key(ancestors[0]) == driver_key
            and key(ancestors[-1]) == pane_key and len({key(row) for row in ancestors}) == len(ancestors)
            and all(row.get('parent_pid') == parent['pid'] for row, parent in zip(ancestors, ancestors[1:])),
            'retained driver/pane ancestry is unbound')
    declared = [key(row) for row in observed.get('owned_processes', [])]
    require(declared and len(declared) == len(set(declared)), 'retained owned process union is missing or duplicated')
    known, all_owned, guard_end = {driver_key}, {driver_key}, begin
    for sample in rows:
        guard_start, guard_finish = witness.stamp(sample['guard_started']), witness.stamp(sample['guard_finished'])
        sampled = witness.stamp(sample['sampled_at']); duration = sample.get('guard_seconds')
        require(type(duration) in (int, float) and 0 <= duration <= 30
                and guard_end <= guard_start <= sampled <= guard_finish <= end
                and abs((guard_finish-guard_start).total_seconds()-duration) <= .01,
                'resource guard timestamps/duration are inconsistent or overlapping')
        guard_end = guard_finish
        for stage in value['stages']:
            identity = stage.get('identity')
            if identity is not None and witness.stamp(stage['started']) <= sampled:
                require(identity.get('parent_pid') == driver_key[0] and stage.get('pid') == identity.get('pid'),
                        'direct stage identity is not a child of this driver')
                known.add(key(identity)); all_owned.add(key(identity))
        processes = sample['processes']
        require(processes and len({row['pid'] for row in processes}) == len(processes)
                and all(type(row.get('parent_pid')) is int and row['parent_pid'] >= 0 for row in processes),
                'sample process identities are duplicated or malformed')
        identities = {row['pid']: key(row) for row in processes}
        require(identities.get(driver_key[0]) == driver_key, 'sample changed the exact driver PID/start identity')
        parents = {row['pid']: row['parent_pid'] for row in processes}
        for pid in parents:
            visited = set()
            while pid in parents:
                require(pid not in visited, 'sample parentage contains a cycle')
                visited.add(pid); pid = parents[pid]
        owned = {pid for pid, identity in identities.items() if identity in known}
        remaining = [row for row in processes if row['pid'] not in owned]
        while remaining:
            connected = [row for row in remaining if row['parent_pid'] in owned]
            require(connected, 'sample contains a new process outside the retained owned tree')
            owned.update(row['pid'] for row in connected)
            remaining = [row for row in remaining if row['pid'] not in owned]
        known.update(identities.values()); all_owned.update(identities.values())
    require(all_owned <= set(declared), 'retained owned union omits a sampled/direct identity')


class Clock:
    def __init__(self, plan, started, started_at, outer_start, outer_end):
        self.plan, self.started, self.started_at = plan, started, started_at
        self.outer_start, self.end = witness.stamp(outer_start), witness.stamp(outer_end)
        b, w = plan['bounds'], plan['window']
        require(witness.stamp(w['not_before']) <= self.outer_start <= started_at <= witness.stamp(w['latest_start'])
                and 0 <= (started_at-self.outer_start).total_seconds() <= 5
                and self.end == self.outer_start + timedelta(seconds=b['shared_seconds'])
                and self.end <= witness.stamp(w['absolute_end']), 'prospective outer clock is late, extended, or unbound')
        self.shared_end = started + (self.end-started_at).total_seconds()
        self.phase, self.phase_start = 'primary', started_at
        self.phase_hard = min(self.shared_end, started + b['primary_outer_seconds'] - (started_at-self.outer_start).total_seconds())
        self.work_end = self.phase_hard - b['cleanup_seconds']

    def remaining(self, *, cleanup=False):
        limit = self.phase_hard if cleanup else self.work_end
        return min(limit-time.monotonic(), (self.end-now()).total_seconds(), self.shared_end-time.monotonic())

    def check(self, *, cleanup=False):
        require(self.remaining(cleanup=cleanup) > 0, 'phase/shared absolute or monotonic deadline exhausted')

    def reserve(self, seconds):
        require(self.remaining() >= seconds, 'full next stage allowance does not remain')

    def diagnostics(self):
        require(self.phase == 'primary', 'diagnostic phase cannot be restarted')
        b = self.plan['bounds']
        require(min(self.shared_end-time.monotonic(), (self.end-now()).total_seconds()) >= b['diagnostic_outer_seconds'],
                'full diagnostic outer allowance does not remain')
        self.phase, self.phase_start = 'diagnostic', now()
        self.phase_hard = min(self.shared_end, time.monotonic()+b['diagnostic_outer_seconds'])
        self.work_end = self.phase_hard-b['cleanup_seconds']


def coverage_terminal(reference, current, expected_commit, proc=Path('/proc')):
    """A fixed failed-run cleanup barrier; no correctness promotion."""
    from scripts.bfs_t17_build_only import coverage_cleanup
    driver = coverage_cleanup(reference, expected_commit, current, proc)
    require(driver.get('deadline_et') == coverage.DEADLINE.isoformat() and exact(driver.get('bounds'), coverage.BOUNDS)
            and 0 <= driver.get('host_wall_s', -1) <= coverage.BOUNDS['outer_seconds']
            and witness.stamp(driver['started']) <= witness.stamp(driver['finished']) <= coverage.DEADLINE
            and driver.get('lane') == 'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 321)',
            'coverage terminal window/lane is invalid')
    return {'audit': reference, 'driver_state': driver['state'], 'work_outcome': 'failed',
            'outer_exit': 1, 'cleanup_verified': True, 'coverage_pass_asserted': False}


def prerequisites(plan, admission, store):
    require(isinstance(admission.get('proofs'), dict) and set(admission['proofs']) == {'a3', 'coverage', 'paired', 'provider'},
            'all four terminal prerequisite receipts are required')
    result = {}
    for key, fixed in plan['fixed_prerequisites'].items():
        require(exact(admission['proofs'][key], fixed), 'fixed historical terminal reference changed')
        if key == 'coverage': continue
        result[key] = (coverage.validate_a3(fixed, store, now()) if key == 'a3'
                       else witness.validate_completion(fixed, key, now()))
    require(admission['coverage_commit'] == plan['coverage_commit'], 'coverage prerequisite code pin differs')
    result['coverage'] = coverage_terminal(admission['proofs']['coverage'], now(), admission['coverage_commit'])
    return result


def history(plan, store):
    require(artifacts.file_hash(ROOT/plan['historical_plan']['path']) == plan['historical_plan']['sha256'],
            'historical fixed plan changed')
    for rid, digest in plan['historical_records'].items():
        record = store.get(rid)
        require(record and artifacts.digest(record) == digest, 'historical failed study record changed: '+rid)
    machine = store.get('mbit10', 'machine')
    for cell in plan['cells']:
        original.first_request(store.get(cell['first_evaluation'], 'evaluation'), cell, machine)
    return copy.deepcopy(plan['historical_records'])


def pair_request(first, cell, machine, plan):
    base = original.first_request(first, cell, machine)
    request = {'message_version': '1.0', 'id': cell['id'], 'collection': copy.deepcopy(plan['collection']),
               'budget': {'total_seconds': plan['bounds']['pair_seconds']}}
    for role in bfs_native_pair.ROLES:
        member = copy.deepcopy(base)
        member.update(id=cell[role+'_evaluation'], threads=1, repetitions=10)
        member['build_directory'] = str(BUILDS/'primary'/member['id'])
        member['budget']['total_seconds'] = 2400
        request[role] = member
    bfs_native_pair.validate_request(request)
    return request


def validate_member(first, value, request, plan):
    require(exact(value.get('request'), request) and value.get('id') == request['id']
            and bfs_coverage._real(value) and value.get('outcome', {}).get('state') == 'complete'
            and not bfs_coverage._correctness(value), 'member lacks its exact complete checked actual evaluation')
    for field in ('candidate', 'implementation', 'machine', 'source_snapshot'):
        require(value.get(field) == first.get(field), 'member source identity changed: '+field)
    for field in ('candidate_sha256', 'source_revision', 'application', 'adapter', 'target', 'machine_sha256',
                  'function', 'sources', 'roi', 'protocol', 'basis', 'process_policy', 'verifier',
                  'backend_configuration', 'instrumentation'):
        require(exact(value['context'].get(field), first['context'].get(field)), 'non-thread context changed: '+field)
    require(value['context']['threads'] == 1 and type(value['context']['threads']) is int,
            'member context is not requested one thread')
    for field in ('id', 'canonical_sha256', 'adjacency_order_sha256', 'canonical_file_sha256', 'sources'):
        require(exact(value['context']['workload'].get(field), first['context']['workload'].get(field)), 'member graph changed')
    for field in ('compiler', 'compiler_version', 'flags', 'template_sha256', 'wrapper_sha256', 'binary_sha256'):
        require(exact(value['build'].get(field), first['build'].get(field)), 'member build changed: '+field)
    runtime = bfs_native.validate_runtime_policy(value['build'].get('native_runtime'), 1)
    require(exact(runtime, plan['native_runtime']) and exact(value['build'].get('execution_environment'),
            bfs_native.controlled_environment(1)), 'member requested runtime differs from plan')
    require(not ({row['output'] for row in first['timing']} & {row['output'] for row in value['timing']}),
            'member reused historical output')
    return sample_grid(value, plan['sources'], 10)


def validate_pair_result(store, first, pair, machine, request, plan):
    require(pair.get('id') == request['id'] and exact(pair.get('request'), request)
            and pair.get('outcome', {}).get('state') == 'complete' and pair.get('evidence_kind') == 'execution'
            and pair.get('gain_claim') is False and exact(pair, store.get(pair['id'], 'evaluation_pair')),
            'pair differs from its exact completed public record')
    unchanged(store, store.get(first['candidate'], 'candidate'))
    pair_begin, pair_end = previous.pair_interval(pair)
    members, samples = {}, {}
    for role in bfs_native_pair.ROLES:
        value = store.get(pair[role+'_evaluation'], 'evaluation')
        samples[role] = validate_member(first, value, request[role], plan)
        previous.validate_member_interval(value, pair_begin, pair_end)
        require(native_lane(value['context'], machine) == LANE, 'member lane changed')
        members[role] = value
    sampling = {'collection': plan['collection'], 'analysis': plan['analysis'], 'repetitions': 10}
    bfs_native_pair.validate_receipt(store, members['baseline'], members['candidate'], {'sampling': sampling})
    return {'samples': samples, 'control': negative_control(samples, plan['profitability'], sampling),
            'members': {role: {'id': value['id'], 'sha256': artifacts.digest(value)} for role, value in members.items()}}


def profile_request(cell):
    return {'message_version': '1.0', 'id': cell['profile'], 'evaluation': cell['baseline_evaluation'],
            'build_directory': str(BUILDS/'diagnostic'/cell['profile']),
            'repetitions': 1, 'memory': True, 'budget': {'discovery_seconds': 120, 'build_seconds': 180,
            'run_seconds': 600, 'total_seconds': 1200}}


def package_request(cell, evaluation):
    return {'message_version': '1.0', 'id': cell['package_requested_id'], 'implementation': cell['implementation'],
            'evaluation': cell['baseline_evaluation'], 'region_profile': cell['profile'],
            'context': profile_package._context(evaluation)}


def validate_package(store, cell, package_id, plan):
    package_binding(store, package_id, cell['package_requested_id'], cell['baseline_evaluation'],
                    cell['profile'], cell['candidate'])
    item = packet(store, package_id)
    require(exact(item['evaluation']['build'].get('native_runtime'), plan['native_runtime'])
            and item['evaluation']['context']['threads'] == 1
            and item['diagnostic']['context']['repetitions'] == 1
            and item['diagnostic']['context']['sources'] == plan['sources'], 'fresh diagnostic context differs')
    require(len(item['diagnostic']['executions']) == 6, 'fresh diagnostic source grid is incomplete')
    return {'id': package_id, 'sha256': artifacts.digest(item['package']), 'records': item['record_identities']}


def validate_package_chain(chain, checked):
    require(chain.get('root') == checked['id'] and isinstance(chain.get('records'), dict)
            and all(artifacts.digest(chain['records'].get(rid)) == digest for rid, digest in checked['records'].items()),
            'fresh public package chain omits or changes admitted records')


def capacity_snapshot(plan, proc=Path('/proc'), node_path=Path('/sys/devices/system/node/node1/meminfo')):
    inputs = {'node': node_path.read_text(), 'zones': (proc/'zoneinfo').read_text(),
              'global': (proc/'meminfo').read_text(), 'pressure': (proc/'pressure/memory').read_text()}
    value = dx100_capacity.capacity(inputs['node'], inputs['zones'], inputs['global'], 1, os.sysconf('SC_PAGE_SIZE'))
    required = {'node': plan['bounds']['node_available_bytes'], 'global': plan['bounds']['global_available_bytes']}
    require(value['estimated_available_kib']*1024 >= required['node']
            and value['global_available_kib']*1024 >= required['global'], 'native node/global capacity admission failed')
    return {'observed_at': now().isoformat(), 'inputs': inputs, 'estimate': value, 'required_bytes': required,
            'native_eligible': True, 'estimate_is_guarantee': False}


def validate_driver_receipt(reference, plan, store, expected_commit):
    """Reopen completed collection; external terminal/lease audit remains separate."""
    validate_plan(plan); value = read(reference)
    require(value.get('id') == RUN_ID and value.get('state') in {'complete', 'primary_unqualified'}
            and value.get('repository_commit') == expected_commit and value.get('plan_canonical_sha256') == PLAN_SHA
            and exact(value.get('bounds'), plan['bounds']) and exact(value.get('native_runtime'), plan['native_runtime'])
            and exact(value.get('python_environment'), PYTHON_INPUTS)
            and value.get('gain_claim') is value.get('protocol_freeze') is value.get('provider_calls') is False,
            'driver identity/configuration/state is incompatible')
    require(exact(value.get('runtime'), runtime_identity(expected_commit)), 'driver runtime inventory changed')
    require(exact(read(value['plan']), plan), 'retained prospective plan changed')
    begin, end = witness.stamp(value['started']), witness.stamp(value['finished'])
    outer_begin, outer_end = witness.stamp(value['outer_start']), witness.stamp(value['outer_end'])
    b = plan['bounds']
    require(witness.stamp(plan['window']['not_before']) <= outer_begin <= begin <= witness.stamp(plan['window']['latest_start'])
            and (begin-outer_begin).total_seconds() <= 5 and begin <= end <= outer_end
            and outer_end-outer_begin == timedelta(seconds=b['shared_seconds'])
            and outer_end <= witness.stamp(plan['window']['absolute_end'])
            and type(value.get('host_wall_s')) in (int, float) and 0 <= value['host_wall_s'] <= b['shared_seconds']
            and abs((end-begin).total_seconds()-value['host_wall_s']) <= 1,
            'retained shared clock is incompatible')
    require(value.get('cleanup', {}).get('state') == 'all_owned_descendants_absent'
            and value['cleanup'].get('subreaper') is True, 'driver child cleanup is unavailable')
    accounting = value.get('final_accounting', {})
    require(type(accounting.get('total_raw_bytes')) is int and accounting['total_raw_bytes'] <= b['total_raw_bytes']
            and 0 <= accounting.get('phase_raw_bytes', -1) <= b['phase_raw_bytes']
            and 0 <= accounting.get('build_bytes', -1) <= b['build_subset_bytes']
            and accounting.get('raw_free_bytes', 0) >= b['raw_reserve_bytes']
            and accounting.get('build_free_bytes', 0) >= b['build_reserve_bytes']
            and begin <= witness.stamp(accounting['observed_at']) <= end,
            'final accounted resource bounds are unavailable')
    admission = read(value['admission'])
    require(admission['code_commit'] == expected_commit and admission['plan_sha256'] == PLAN_SHA
            and witness.stamp(admission['prepared_at']) <= begin, 'retained admission is unbound')
    prerequisites(plan, admission, store); history(plan, store)
    rows = [json.loads(line) for line in witness.reference(value['rss']['samples'], 64*1024**2).splitlines() if line.strip()]
    require(rows and len(rows) <= 4000, 'resource samples missing or excessive')
    samples = [witness.stamp(row['sampled_at']) for row in rows]
    require(begin <= samples[0] <= samples[-1] <= end
            and all(0 <= (right-left).total_seconds() <= 30 for left, right in zip([begin]+samples, samples+[end]))
            and value['rss']['peak_bytes'] == max(row['rss_bytes'] for row in rows), 'resource timing or peak is invalid')
    machine = store.get('mbit10', 'machine')
    validate_resource_ownership(value, rows, begin, end)
    for row in rows:
        require(type(row.get('rss_bytes')) is int and 0 <= row['rss_bytes'] <= b['sampled_rss_bytes']
                and row.get('rss_source') == plan['rss_source']
                and type(row.get('page_size_bytes')) is int and 0 < row['page_size_bytes'] <= 1024**2
                and all(type(p.get('rss_pages')) is int and p['rss_pages'] >= 0
                        and p['rss_bytes'] == p['rss_pages']*row['page_size_bytes'] for p in row['processes'])
                and row['rss_bytes'] == sum(p['rss_bytes'] for p in row['processes'])
                and any(p['pid'] == value['driver_pid'] for p in row['processes'])
                and 0 <= row['guard_seconds'] <= 30 and row['total_raw_bytes'] <= b['total_raw_bytes']
                and row['phase_raw_bytes'] <= b['phase_raw_bytes']
                and 0 <= row.get('build_bytes', -1) <= b['build_subset_bytes']
                and row['raw_free_bytes'] >= b['raw_reserve_bytes'] and row['build_free_bytes'] >= b['build_reserve_bytes'],
                'resource sample violates the declared guards')
        require(bfs_protocol.verified_native_lane(row['lane']['verified_lane'], machine) == LANE,
                'resource sample lane differs')
    stages = value['stages']; public = []; prior_end = begin
    require(value['rss'].get('source') == plan['rss_source'], 'RSS observation basis differs')
    for stage in stages:
        stage_begin, stage_end = witness.stamp(stage['started']), witness.stamp(stage['finished'])
        duration = (stage_end-stage_begin).total_seconds()
        require(stage.get('state') == 'complete' and stage.get('returncode') == 0
                and stage.get('cleanup', {}).get('state') == 'all_owned_descendants_absent'
                and type(stage.get('host_wall_s')) in (int, float) and type(stage.get('ceiling_seconds')) in (int, float)
                and 0 <= stage['host_wall_s'] <= stage['ceiling_seconds']
                and 0 <= duration <= stage['ceiling_seconds']
                and abs(duration-stage['host_wall_s']) <= 1
                and prior_end <= stage_begin <= stage_end <= end,
                'retained stage is incomplete or exceeds its allowance')
        prior_end = witness.stamp(stage['finished'])
        phase_start = outer_begin if stage['phase'] == 'primary' else witness.stamp(value['diagnostic_started'])
        work_seconds = b['primary_seconds'] if stage['phase'] == 'primary' else b['diagnostic_seconds']
        require((prior_end-phase_start).total_seconds() <= work_seconds, 'stage used phase cleanup reserve for work')
        witness.reference({'path': stage['output'], 'sha256': stage['stdout_sha256']}, 64*1024**2)
        witness.reference({'path': stage['stderr'], 'sha256': stage['stderr_sha256']}, 64*1024**2)
        if 'request' in stage:
            request = read(stage['request'])
            command = stage['command'][3]
            expected = [value['runtime']['python']['path'], '-m', 'swdb', command, stage['request']['path']]
            if command in {'evaluate-pair', 'bfs-profile'}: expected += ['--runs-dir', value['runs_dir']]
            expected += ['--records', value['records'], '--format', 'json']
            ceilings = {'evaluate-pair':2460, 'bfs-profile':1260, 'profile-package':180}
            require(command in ceilings and stage['command'] == expected and stage['ceiling_seconds'] == ceilings[command],
                    'public command or complete allowance differs from its fixed request')
            public.append((command, request, stage))
            output = json.loads(Path(stage['output']).read_text())
            require(isinstance(output, dict) and exact(output, store.get(output.get('id'))), 'public result differs from current record')
    require([(command, req['id']) for command, req, _ in public[:4]] ==
            [('evaluate-pair', cell['id']) for cell in plan['cells']], 'primary public order differs')
    require([row['id'] for row in value['cells']] == [cell['id'] for cell in plan['cells']], 'four-cell receipt is incomplete')
    controls = []
    for cell, retained in zip(plan['cells'], value['cells']):
        first = store.get(cell['first_evaluation'], 'evaluation'); request = pair_request(first, cell, machine, plan)
        compiler = retained.get('compiler', {})
        resolved = Path(first['build']['compiler']).resolve(strict=True)
        require(compiler.get('compiler_resolved') == str(resolved)
                and compiler.get('compiler_sha256') == artifacts.file_hash(resolved),
                'retained compiler executable differs from the declared build compiler')
        matches = [(req, stage) for command, req, stage in public if command == 'evaluate-pair' and req.get('id') == cell['id']]
        require(len(matches) == 1 and exact(matches[0][0], request), 'exact public pair request is missing')
        pair = store.get(cell['id'], 'evaluation_pair')
        require(pair and artifacts.digest(pair) == retained['pair_sha256']
                and exact(json.loads(Path(matches[0][1]['output']).read_text()), pair), 'public pair result changed')
        pair_begin, pair_end = previous.pair_interval(pair)
        stage = matches[0][1]
        require(witness.stamp(stage['started']) <= pair_begin <= pair_end <= witness.stamp(stage['finished'])
                and (pair_end-pair_begin).total_seconds() <= stage['host_wall_s']+1,
                'actual pair interval is not contained in its public stage')
        observed = validate_pair_result(store, first, pair, machine, request, plan)
        require(all(exact(retained[key], observed[key]) for key in ('samples', 'control', 'members')), 'retained control changed')
        controls.append(observed['control'])
    qualified = not any(control['unmet_gates'] for control in controls)
    require(value.get('primary_qualified') is qualified, 'qualification differs from actual full control')
    expected_stages = []
    for cell in plan['cells']:
        expected_stages.extend([('compiler', cell), ('evaluate-pair', cell)])
    if qualified:
        for cell in plan['cells']:
            expected_stages.extend([('bfs-profile', cell), ('profile-package', cell), ('get', cell)])
    require(len(stages) == len(expected_stages), 'public/identity stage grid is incomplete or has extra calls')
    for stage, (kind, cell) in zip(stages, expected_stages):
        require(stage['phase'] == ('primary' if kind in {'compiler', 'evaluate-pair'} else 'diagnostic'),
                'stage crossed its fixed phase')
        if kind == 'compiler':
            first = store.get(cell['first_evaluation'], 'evaluation')
            require(stage['command'] == [first['build']['compiler'], '--version'] and stage['ceiling_seconds'] == 60
                    and Path(stage['output']).read_text().splitlines()[:2] == first['build']['compiler_version'],
                    'declared compiler identity stage changed')
        else:
            require(stage['command'][3] == kind, 'public stage sequence changed')
    expensive = [stage for stage in stages if len(stage['command']) > 3 and stage['command'][3] in {'evaluate-pair','bfs-profile'}]
    require(len(value.get('capacity', [])) == len(expensive), 'fresh capacity admissions are incomplete')
    for observed, stage in zip(value['capacity'], expensive):
        raw = observed['inputs']; estimate = dx100_capacity.capacity(raw['node'], raw['zones'], raw['global'], 1,
                                                                   observed['estimate']['page_size_bytes'])
        require(exact(observed['estimate'], estimate) and observed['native_eligible'] is True
                and observed['command'] == stage['command']
                and exact(observed['required_bytes'], {'node':b['node_available_bytes'], 'global':b['global_available_bytes']})
                and estimate['estimated_available_kib']*1024 >= b['node_available_bytes']
                and estimate['global_available_kib']*1024 >= b['global_available_bytes']
                and 0 <= (witness.stamp(stage['started'])-witness.stamp(observed['observed_at'])).total_seconds() <= 30,
                'native capacity input/threshold/freshness differs')
    if not qualified:
        require(value['state'] == 'primary_unqualified' and len(public) == 4
                and exact(value['diagnostics'], [{'id': c['profile'], 'state': 'not_dispatched_primary_unqualified'} for c in plan['cells']])
                and (end-outer_begin).total_seconds() <= b['primary_outer_seconds'], 'unqualified primary dispatched diagnostics')
    else:
        diagnostic_start = witness.stamp(value['diagnostic_started'])
        require(value['state'] == 'complete' and len(public) == 12 and len(value['diagnostics']) == 4
                and begin <= diagnostic_start <= end
                and (diagnostic_start-outer_begin).total_seconds() <= b['primary_outer_seconds']
                and (end-diagnostic_start).total_seconds() <= b['diagnostic_outer_seconds'], 'diagnostic phase/grid exceeded its scope')
        for cell, retained in zip(plan['cells'], value['diagnostics']):
            require(retained['state'] == 'complete' and retained['profile'] == cell['profile'], 'diagnostic order changed')
            for command, expected in [('bfs-profile', profile_request(cell)), ('profile-package', package_request(cell, store.get(cell['baseline_evaluation'], 'evaluation')))]:
                matches = [req for name, req, _ in public if name == command and req.get('id') == expected['id']]
                require(len(matches) == 1 and exact(matches[0], expected), 'fresh diagnostic request changed')
            checked = validate_package(store, cell, retained['id'], plan)
            require(all(exact(retained[key], checked[key]) for key in checked), 'fresh package evidence changed')
            witness.reference(retained['public_get'], 64*1024**2)
            validate_package_chain(read(retained['public_get']), checked)
            matches = [stage for stage in stages if stage['output'] == retained['public_get']['path']]
            require(len(matches) == 1 and matches[0]['stdout_sha256'] == retained['public_get']['sha256']
                    and matches[0]['command'] == [value['runtime']['python']['path'], '-m', 'swdb', 'get', retained['id'],
                        '--chain', '--records', value['records'], '--format', 'json']
                    and matches[0]['ceiling_seconds'] == 180, 'fresh package public get is missing or changed')
    return {'state': value['state'], 'qualified': qualified, 'driver': reference, 'controls': controls, 'gain_claim': False}


def bounded_stage(receipt, folder, command, ceiling, clock, owned, monitor, *, env=None, cwd=ROOT):
    """Reserve cleanup inside a CLI ceiling; adopt detached children on success too."""
    clock.reserve(ceiling)
    started = time.monotonic(); hard = min(clock.work_end, started+ceiling)
    work = hard-30
    row = {'command': list(map(str, command)), 'phase': clock.phase, 'started': now().isoformat(),
           'ceiling_seconds': ceiling, 'state': 'starting'}
    receipt['stages'].append(row)
    out, err = folder/f'{len(receipt["stages"]):03d}.stdout', folder/f'{len(receipt["stages"]):03d}.stderr'
    row.update(output=str(out), stderr=str(err)); save_receipt(folder, receipt)
    child, identity = None, None
    try:
        with out.open('x') as stdout, err.open('x') as stderr:
            child = subprocess.Popen(row['command'], cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            row['pid'] = child.pid
            identity = observer.identity(child.pid)
            require(identity is not None or child.poll() is not None, 'spawned child identity is unavailable')
            row['identity'] = identity; save_receipt(folder, receipt)
            if identity is not None and hasattr(owned, 'remember'): owned.remember(identity)
            while child.poll() is None:
                monitor(); clock.check()
                require(time.monotonic() < work, 'public stage work deadline exhausted')
                try: child.wait(timeout=min(.2, max(0, work-time.monotonic())))
                except subprocess.TimeoutExpired: pass
            require(child.returncode == 0, 'public stage failed: '+str(child.returncode))
        row['state'] = 'complete'
    except BaseException as exc:
        row.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            if child is not None:
                try:
                    stop_owned(child, identity, min(hard, clock.phase_hard), clock.end, observer.identity)
                finally:
                    child.wait(timeout=max(0, min(hard-time.monotonic(), (clock.end-now()).total_seconds())))
            row['cleanup'] = owned.finish(seconds=max(0, min(5, hard-time.monotonic(), (clock.end-now()).total_seconds())))
        except BaseException as exc:
            row.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            row.update(returncode=child.returncode if child else None, finished=now().isoformat(),
                       host_wall_s=time.monotonic()-started,
                       stdout_sha256=artifacts.file_hash(out) if out.exists() else None,
                       stderr_sha256=artifacts.file_hash(err) if err.exists() else None)
            save_receipt(folder, receipt)
    require(time.monotonic() <= hard, 'stage cleanup/final persistence exceeded its complete ceiling')
    clock.check()
    return out


class Driver:
    def __init__(self, args, plan, started, started_at):
        self.args, self.plan = args, plan
        self.clock = Clock(plan, started, started_at, args.outer_start, args.outer_end)
        self.runs = args.runs_dir.resolve(); self.folder = self.runs/(RUN_ID+'.driver')
        require(any(base in self.runs.parents for base in RAW_ROOTS), 'raw root is outside permitted host storage')
        require(not self.runs.exists(), 'one-thread run directory already exists; no overwrite/resume')
        require(not BUILDS.exists(), 'one-thread build directory already exists; no overwrite/resume')
        require(args.records.resolve() == ROOT/'records', 'records must belong to the caller-pinned checkout')
        self.runs.mkdir(parents=True, exist_ok=False); self.folder.mkdir()
        self.store = Store(args.records); self.machine = self.store.get('mbit10', 'machine')
        self.receipt = {'id': RUN_ID, 'role': plan['role'], 'state': 'running', 'started': started_at.isoformat(),
            'outer_start': args.outer_start, 'outer_end': args.outer_end, 'bounds': plan['bounds'], 'plan': ref(PLAN),
            'plan_canonical_sha256': PLAN_SHA, 'repository_commit': args.expected_commit,
            'gain_claim': False, 'protocol_freeze': False, 'provider_calls': False,
            'phase': 'primary', 'phases': [], 'stages': [], 'cells': [], 'diagnostics': [],
            'driver_pid': os.getpid(), 'runs_dir': str(self.runs), 'records': str(args.records.resolve()),
            'rss': {'peak_bytes': 0, 'source': plan['rss_source']}, 'raw_peak_bytes': 0}
        self.owned, self.monitor = None, None
        self.last_sample = started_at
        self.phase_start_bytes = 0
        self.accounting_lock = threading.RLock()
        self.env, policy = bfs_native.runtime_environment(1, plan['native_runtime'])
        for name, value in PYTHON_INPUTS.items():
            if value is None: self.env.pop(name, None)
            else: self.env[name] = value
        require(exact(policy, plan['native_runtime']), 'constructed runtime differs')
        self.receipt['native_runtime'] = policy
        self.receipt['python_environment'] = copy.deepcopy(PYTHON_INPUTS)
        save_receipt(self.folder, self.receipt)

    @contextmanager
    def accounting_guard(self, *, cleanup=False):
        started = time.monotonic()
        allowance = max(0, min(30, self.clock.remaining(cleanup=cleanup)))
        require(allowance > 0 and self.accounting_lock.acquire(timeout=allowance),
                'phase accounting lock exhausted its guard allowance')
        try:
            yield
        finally:
            self.accounting_lock.release()
        require(time.monotonic()-started <= 30, 'phase accounting exceeded its guard allowance')
        self.clock.check(cleanup=cleanup)

    def accounting(self, *, cleanup=False):
        with self.accounting_guard(cleanup=cleanup):
            return self.accounting_snapshot(cleanup=cleanup)

    def accounting_snapshot(self, *, cleanup=False):
        self.clock.check(cleanup=cleanup)
        b = self.plan['bounds']; size = self.storage()
        require(size <= b['total_raw_bytes'], 'shared storage allowance exhausted')
        phase_size = size-self.phase_start_bytes
        require(0 <= phase_size <= b['phase_raw_bytes'], 'phase storage allowance exhausted')
        values = {'total_raw_bytes': size, 'phase_raw_bytes': phase_size, 'phase': self.clock.phase,
                  'elapsed_seconds': time.monotonic()-self.clock.started, 'observed_at': now().isoformat()}
        values['build_bytes'] = original.batch_storage(BUILDS, b['build_subset_bytes']) if BUILDS.exists() else 0
        for key, path, reserve in [('raw_free_bytes', self.runs, b['raw_reserve_bytes']),
                                   ('build_free_bytes', Path('/data1'), b['build_reserve_bytes'])]:
            st = os.statvfs(path); values[key] = st.f_bavail*st.f_frsize
            require(values[key] >= reserve, 'free-space reserve violated')
        return values

    def storage(self):
        size = original.batch_storage(self.runs, sys.maxsize)
        if BUILDS.exists(): size += original.batch_storage(BUILDS, sys.maxsize)
        # Public records live in the checkout, outside raw/build directories.
        size += sum(path.lstat().st_size for path in self.args.records.rglob(RUN_ID+'*.yaml'))
        return size

    def observe(self):
        started, stamp = time.monotonic(), now()
        measured = self.owned.sample(); values = self.accounting(cleanup=True)
        measured.update(values, lane=lease_observation(self.machine, 1), load_average=list(os.getloadavg()),
                        guard_started=stamp.isoformat(), guard_finished=now().isoformat(), guard_seconds=time.monotonic()-started)
        sample_at = witness.stamp(measured['sampled_at'])
        require(0 <= (sample_at-self.last_sample).total_seconds() <= 30 and measured['guard_seconds'] <= 30,
                'resource telemetry gap or guard exceeds30s')
        self.last_sample = sample_at
        with (self.folder/'rss-samples.jsonl').open('a') as stream: stream.write(json.dumps(measured)+'\n')
        self.receipt['rss']['peak_bytes'] = max(self.receipt['rss']['peak_bytes'], measured['rss_bytes'])
        self.receipt['raw_peak_bytes'] = max(self.receipt['raw_peak_bytes'], values['total_raw_bytes'])
        require(measured['rss_bytes'] <= self.plan['bounds']['sampled_rss_bytes'], 'owned sampled RSS ceiling exceeded')

    def check(self):
        self.monitor.check(); self.clock.check()

    def stage(self, command, ceiling, *, expensive=False):
        self.check(); self.clock.reserve(ceiling)
        if expensive:
            self.accounting()
            self.receipt.setdefault('capacity', []).append({**capacity_snapshot(self.plan), 'command': list(map(str, command))})
        recheck_runtime(self.receipt['runtime'])
        output = bounded_stage(self.receipt, self.folder, command, ceiling, self.clock, self.owned,
                               self.check, env=self.env)
        recheck_runtime(self.receipt['runtime']); self.check()
        return output

    def public(self, command, request, ceiling, *, expensive=False):
        path = self.folder/(request['id']+'.request.json')
        with path.open('x') as stream: stream.write(json.dumps(request, indent=2)+'\n')
        argv = [self.receipt['runtime']['python']['path'], '-m', 'swdb', command, str(path)]
        if command in {'evaluate-pair', 'bfs-profile'}: argv.extend(['--runs-dir', str(self.runs)])
        argv.extend(['--records', str(self.args.records), '--format', 'json'])
        before = len(self.receipt['stages'])
        try:
            output = self.stage(argv, ceiling, expensive=expensive)
        finally:
            if len(self.receipt['stages']) > before:
                self.receipt['stages'][-1]['request'] = ref(path)
                save_receipt(self.folder, self.receipt)
        result = read(ref(output)); self.store = Store(self.args.records)
        require(isinstance(result, dict) and exact(result, self.store.get(result.get('id'))), 'public result differs from stored record')
        return result

    def run(self):
        self.owned = LockedOwned()
        self.monitor = previous.ResourceMonitor(self.observe)
        self.monitor.start()
        self.receipt['runtime'] = runtime_identity(self.args.expected_commit)
        identity = observer.identity(os.getpid())
        pane = {'pid': self.args.pane_pid, 'start_ticks': self.args.pane_start_ticks}
        self.receipt['process_observations'] = {'driver_identity': identity, 'pane_identity': pane,
            'ancestry': observer.ancestry(identity, pane), 'cleanup_verified': False}
        self.receipt['lane'] = lease_observation(self.machine, 1)
        self.receipt['storage_roots'] = {'raw': str(self.runs), 'builds': str(BUILDS),
                                        'records': str(self.args.records.resolve()), 'record_prefix': RUN_ID}
        for path, reserve, allowance in ((self.runs, self.plan['bounds']['raw_reserve_bytes'], self.plan['bounds']['total_raw_bytes']),
                              (Path('/data1'), self.plan['bounds']['build_reserve_bytes'], self.plan['bounds']['build_subset_bytes'])):
            space = os.statvfs(path)
            require(space.f_bavail*space.f_frsize >= reserve+allowance,
                    'full prospective storage plus reserve is unavailable')
        admission = read({'path': str(self.args.admission.resolve()), 'sha256': self.args.admission_sha256})
        require(admission.get('code_commit') == self.args.expected_commit
                and admission.get('plan_sha256') == PLAN_SHA and witness.stamp(admission['prepared_at']) <= self.clock.started_at,
                'prospective admission code/plan/clock is unbound')
        self.receipt['admission'] = ref(self.args.admission)
        self.receipt['prerequisites'] = prerequisites(self.plan, admission, self.store)
        self.receipt['history'] = history(self.plan, self.store)
        fresh = [cell[key] for cell in self.plan['cells'] for key in
                 ('id', 'baseline_evaluation', 'candidate_evaluation', 'profile', 'package_requested_id')]
        require(not any(self.store.get(rid) for rid in fresh), 'planned record already exists; no overwrite/resume')
        self.clock.reserve(4*2460)
        for cell in self.plan['cells']:
            first = self.store.get(cell['first_evaluation'], 'evaluation')
            compiler = previous.observe_compiler(first, self.folder/(cell['id']+'.compiler.txt'),
                lambda command, seconds, output: output.write_bytes(self.stage(command, seconds+30).read_bytes()))
            request = pair_request(first, cell, self.machine, self.plan)
            pair = self.public('evaluate-pair', request, 2460, expensive=True)
            checked = validate_pair_result(self.store, first, pair, self.machine, request, self.plan)
            require(artifacts.file_hash(compiler['compiler_resolved']) == compiler['compiler_sha256'], 'compiler executable changed')
            self.receipt['cells'].append({'id': cell['id'], 'pair_sha256': artifacts.digest(pair), **checked,
                                          'compiler': compiler, 'state': 'complete'})
            save_receipt(self.folder, self.receipt); self.check()
        require(len(self.receipt['cells']) == 4, 'full primary grid is required')
        qualified = not any(row['control']['unmet_gates'] for row in self.receipt['cells'])
        self.receipt['primary_qualified'] = qualified
        if not qualified:
            self.receipt['diagnostics'] = [{'id': c['profile'], 'state': 'not_dispatched_primary_unqualified'} for c in self.plan['cells']]
            self.receipt['state'] = 'primary_unqualified'
            return
        self.start_diagnostics()
        for cell in self.plan['cells']:
            self.clock.reserve(1620)
            diagnostic = self.public('bfs-profile', profile_request(cell), 1260, expensive=True)
            require(diagnostic['id'] == cell['profile'], 'public profile ID changed')
            evaluation = self.store.get(cell['baseline_evaluation'], 'evaluation')
            package = self.public('profile-package', package_request(cell, evaluation), 180)
            output = self.stage([self.receipt['runtime']['python']['path'], '-m', 'swdb', 'get', package['id'],
                '--chain', '--records', str(self.args.records), '--format', 'json'], 180)
            checked = validate_package(self.store, cell, package['id'], self.plan)
            validate_package_chain(read(ref(output)), checked)
            self.receipt['diagnostics'].append({**checked, 'profile': cell['profile'], 'state': 'complete', 'public_get': ref(output)})
            save_receipt(self.folder, self.receipt); self.check()
        self.receipt['state'] = 'complete'

    def start_diagnostics(self):
        # A monitor sample must pair its storage count with the same phase's
        # baseline. Charge the final primary reads before switching clocks.
        with self.accounting_guard():
            primary = self.accounting()
            next_baseline = self.storage()
            self.clock.check()
            self.receipt['phases'].append({'phase': 'primary', 'finished': now().isoformat(), 'accounting': primary})
            self.clock.diagnostics(); self.phase_start_bytes = next_baseline
            self.receipt['phase'] = 'diagnostic'
            self.receipt['diagnostic_started'] = self.clock.phase_start.isoformat()
            self.receipt['diagnostic_start_bytes'] = self.phase_start_bytes

    def finalize(self):
        """Every final hash/write is charged; overruns retain a failed receipt."""
        error = None
        try:
            monitor_failure = None
            if self.monitor:
                try:
                    self.monitor.stop()
                    self.monitor.check()
                except BaseException as exc:
                    monitor_failure = exc
            if self.owned:
                try:
                    self.receipt['cleanup'] = self.owned.finish(seconds=max(0, min(30, self.clock.remaining(cleanup=True))))
                    self.observe()
                finally:
                    identities = (self.owned.retained_identities() if hasattr(self.owned, 'retained_identities')
                                  else sorted(self.owned.sampler.known.items()))
                    self.receipt.setdefault('process_observations', {})['owned_processes'] = [
                        {'pid': pid, 'start_ticks': ticks} for pid, ticks in identities]
            if (self.folder/'rss-samples.jsonl').exists():
                self.receipt['rss']['samples'] = ref(self.folder/'rss-samples.jsonl')
            if monitor_failure is not None: raise monitor_failure
            for _ in range(2):
                self.receipt['final_accounting'] = self.accounting(cleanup=True)
                self.receipt.update(finished=now().isoformat(), host_wall_s=time.monotonic()-self.clock.started)
                require((now()-self.last_sample).total_seconds() <= 30, 'final resource telemetry gap exceeded')
                save_receipt(self.folder, self.receipt)
                self.accounting(cleanup=True)
        except BaseException as exc:
            error = exc
            self.receipt.update(state='failed', final_accounting_error=f'{type(exc).__name__}: {exc}',
                                finished=now().isoformat(), host_wall_s=time.monotonic()-self.clock.started)
            save_receipt(self.folder, self.receipt)
        if error: raise error


def main():
    started, started_at = time.monotonic(), now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=PLAN)
    parser.add_argument('--records', type=Path, default=ROOT/'records')
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--admission-sha256', required=True)
    parser.add_argument('--outer-start', required=True)
    parser.add_argument('--outer-end', required=True)
    parser.add_argument('--pane-pid', type=int, required=True)
    parser.add_argument('--pane-start-ticks', type=int, required=True)
    args = parser.parse_args()
    plan = validate_plan(yamlio.load(args.plan))
    require(args.plan.resolve() == PLAN, 'exact canonical plan path required')
    require(socket.gethostname().split('.')[0] == 'mbit10' and sys.platform == 'linux', 'actual client requires mbit10 Linux')
    driver = Driver(args, plan, started, started_at)
    with interruption_signals():
        try: driver.run()
        except BaseException as exc:
            driver.receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        finally: driver.finalize()
    print(json.dumps({'id': RUN_ID, 'state': driver.receipt['state'], 'driver': ref(driver.folder/'driver.json'), 'gain_claim': False}))
    return 0 if driver.receipt['state'] in {'complete', 'primary_unqualified'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
