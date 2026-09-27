#!/usr/bin/env python3
"""Finite sequential simulator-series coordination. Created: 2026-09-26 ET.

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
from scripts.dx100_build import disk_usage_kib
from swdb import artifacts, bfs_coverage, bfs_protocol, profile, profile_package, yamlio
from swdb.store import Store

ET = ZoneInfo('America/New_York')
GIB = 1024**3
PLAN_HASHES = {'t15': 'bec894d3c21400617aa5b02afd9e97fcb104e11da1c1e52d43355aa10d788833', 't16': '8485d6ad0ca8708d9ef4d3342676748a5e39bc421d0a30d262fe2bff2f7c457e'}
PLAN_DIR = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests'
RAW_ROOTS = (Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))
BUILD_ROOT = Path('/data1/yanruj/EvolveSWDB_builds')
CLEANUP_RUNTIME = ('scripts/bfs_simulator_batch.py', 'scripts/bfs_simulator_series.py',
                   'scripts/bfs_owned_execution.py', 'scripts/bfs_owned_rss.py', 'scripts/bfs_process.py')


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


def runtime_identity():
    suffixes = {'.py', '.cc', '.cpp', '.h', '.hpp', '.json', '.yaml', '.sh'}
    result = {str(path.relative_to(ROOT)): artifacts.file_hash(path)
            for name in ('swdb', 'scripts', 'schemas', 'vocab')
            for path in sorted((ROOT / name).rglob('*')) if path.is_file() and path.suffix in suffixes}
    result.update({name: artifacts.file_hash(ROOT/name) for name in
                   ('tests/test_bfs_owned_execution.py', 'tests/test_dx100_interruption.py')})
    return result


def allocated_bytes(paths):
    total = 0
    for value in paths:
        path = Path(value)
        require(path.exists() and path == path.resolve(), 'charged storage path missing or symlinked')
        used, warnings = disk_usage_kib(path)
        require(not warnings, 'raw-storage accounting is incomplete')
        total += used * 1024
    return total


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


def preparation_charges(plan):
    """Reopen the fixed retained preparation; caller-supplied credits are forbidden."""
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
        rows.append({'id': entry['id'], 'elapsed_seconds': math.ceil(max(stage_seconds, duration + 1)),
                     'raw_bytes': allocated_bytes(entry['storage_paths'])})
    return rows


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
        require(available > 0 and latest == self.end - timedelta(seconds=available)
                and stamp(admission['prepared_at']) <= first <= self.outer_started <= started_at <= latest,
                'prospective schedule is absent, late, or cannot fit the remaining batch allowance')
        self.monotonic_end = started + available - startup
        self.startup_seconds = startup

    def remaining(self):
        remaining = min(self.monotonic_end - time.monotonic(), (self.end - now()).total_seconds())
        require(remaining > self.bounds['cleanup_seconds'], 'common batch deadline exhausted')
        return remaining

    def next_allowance(self, raw_bytes):
        require(self.remaining() >= self.bounds['series_seconds'] + self.bounds['cleanup_seconds'],
                'insufficient shared time for the next full series allowance and cleanup')
        storage = math.floor((self.bounds['batch_storage_gib'] * GIB - self.charged_bytes - raw_bytes) / GIB)
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
    for row in plan['series']:
        candidate = store.get(row['candidate']); source = store.get(candidate['source_snapshot'])
        implementation = store.get(candidate['implementation']); workload = store.get(row['workload'])
        frozen = protocols.get(row['protocol_key'])
        validate_selection(candidate, source, implementation, workload, frozen, row['protocol_role'], True,
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
    own = f'mbit10-evaluation-node{node}'
    verified = profile._verified_lane(machine, own)
    root = Path(os.environ.get('LACT_LEASE_ROOT', '/data1/yanruj/lact-host-lease'))
    rows = {}
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        path = root / (name + '.meta.json')
        value = json.loads(path.read_text())
        kernel_held = None
        if name != own:
            with (root / (name + '.lease')).open('rb') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    kernel_held = False
                except BlockingIOError:
                    kernel_held = True
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
            require(value.get('state') == ('held' if kernel_held else 'released'),
                    'other lease metadata and kernel lock disagree')
            require(name != 'mbit10-evaluation' or not kernel_held, 'legacy kernel lease is held')
        rows[name] = {'sha256': artifacts.file_hash(path), 'metadata': value, 'kernel_held': kernel_held}
    return {'verified_lane': verified, 'leases': rows}


def series_command(plan, row, admission, config, runs, records, node, seconds, storage, cleanup=None):
    b = plan['bounds']
    command = [admission['python']['path'], str(ROOT / 'scripts/bfs_simulator_series.py'),
        '--id', row['id'], '--candidate', row['candidate'], '--workload', row['workload'],
        '--build-evaluation', plan['model_build'], '--diagnostic-build', row['diagnostic_build'],
        '--configuration', str(config), '--runs-dir', str(runs), '--records', str(records), '--lane', str(node),
        '--author-binary', '--verifier', plan['verifier'], '--require-capacity',
        '--total-seconds', str(seconds), '--checkpoint-seconds', str(b['checkpoint_seconds']),
        '--run-seconds', str(b['run_seconds']), '--diagnostic-seconds', str(b['diagnostic_seconds']),
        '--memory-gib', str(b['memory_gib']), '--storage-gib', str(b['storage_gib']),
        '--batch-storage-gib', str(storage), '--verification-ticks', str(plan['verification_ticks'])]
    if cleanup is not None:
        command += ['--owned-cleanup-ledger', str(cleanup.path), '--owned-cleanup-binding', cleanup.binding]
    if row['accelerated']:
        command.append('--accelerated')
    if row['protocol_key'] is not None:
        command += ['--protocol', admission['protocols'][row['protocol_key']]['id'], '--protocol-role', row['protocol_role']]
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
    expected_protocol = admission['protocols'][row['protocol_key']]['id'] if row['protocol_key'] else None
    require(child.get('state') == 'complete' and child.get('id') == row['id']
            and child.get('candidate') == row['candidate'] and child.get('workload') == row['workload']
            and child.get('configuration') == row['configuration'] and child.get('roi') == plan['roi']
            and child.get('model_build') == plan['model_build'] and child.get('repetitions') == 2
            and child.get('protocol') == expected_protocol and child.get('bounds') == expected_bounds
            and child.get('diagnostic_build') == {'evaluation': row['diagnostic_build'],
                'sha256': plan['record_sha256'][row['diagnostic_build']]}
            and child.get('stages') and all(stage.get('state') == 'complete' for stage in child['stages']),
            'series receipt differs from its planned complete identity or bounds')
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
    expected = [(position, source, repetition) for position, source in enumerate(row['sources']) for repetition in range(2)]
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

    # A completed child declaration is not evidence of the public aggregation.
    # Reopen its exact ordered primaries and the admitted immutable policy before
    # using the same semantic/grid reader as a subsequent public comparison.
    aggregate_id = row['id'] + '.aggregate'
    require(child.get('aggregate') == aggregate_id, 'series aggregate identity differs from the planned aggregate')
    frozen = store.get(expected_protocol, 'protocol')
    require(frozen and frozen.get('id') == expected_protocol
            and artifacts.digest(frozen) == admission['protocols'][row['protocol_key']]['sha256'],
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
        require(request.get('protocol') == context.get('protocol') == expected_protocol
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
            and all(len(values) == 2 for values in observations.values()),
            'series aggregate lacks the complete actual frozen sample grid')


def collect_series(plan, admission, receipt, folder, runs, records, node, ledger, owned, monitor):
    """Launch each public series once; terminal readback cannot skip cleanup."""
    for row in plan['series']:
        raw = monitor()
        require(runtime_identity() == admission['runtime_sha256'], 'runtime changed during batch')
        seconds, storage = ledger.next_allowance(raw)
        admit_capacity(receipt, node, row['id'])
        config = folder / (row['id'] + '.configuration.json')
        with config.open('x') as stream:
            stream.write(json.dumps(row['configuration'], indent=2) + '\n')
        child_root = runs / row['id']
        require(not child_root.exists(), 'series root already exists; no resume')
        command = series_command(plan, row, admission, config, child_root, records, node, seconds, storage, owned.budget)
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
    args = parser.parse_args()
    plan = yamlio.load(PLAN_DIR / f'bfs-{args.kind}-simulator-batch-20260926-a1.json')
    validate_plan(plan, args.kind)
    admission_ref = {'path': str(args.admission.absolute()), 'sha256': args.admission_sha256}
    admission = read_reference(admission_ref)
    require(socket.gethostname().split('.')[0] == 'mbit10', 'simulator batch execution requires mbit10')
    ledger = Ledger(plan, admission, started, started_at, stamp(args.outer_started))
    require(stamp(args.outer_deadline) == min(ledger.end, stamp(args.outer_started)+timedelta(
            seconds=plan['bounds']['batch_seconds']-ledger.charged_seconds)),
            'outer deadline differs from the same charged batch allowance')
    runs = args.runs_dir.absolute()
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
        require(raw + ledger.charged_bytes < plan['bounds']['batch_storage_gib'] * GIB, 'shared batch raw-storage ceiling exceeded')
        for path, minimum in ((runs, plan['bounds']['raw_reserve_gib']), (BUILD_ROOT.parent, plan['bounds']['build_reserve_gib'])):
            stat = os.statvfs(path)
            require(stat.f_bavail * stat.f_frsize >= minimum * GIB, 'raw/build free-space reserve violated')
        sample = {**ledger.observation(raw), **(lease_observation(store.get('mbit10'), args.lane)
                  if store else {'lease_admission': 'record_store_loading'}),
                  'owned_processes': owned.sample()}
        require(sample['owned_processes']['rss_bytes'] <= lifecycle.SAMPLED_RSS_BYTES,
                'sampled whole-tree RSS exceeded 52 GiB')
        with ledger_file.open('a') as stream:
            stream.write(json.dumps(sample) + '\n')
        return raw
    try:
        owned = lifecycle.Owned(cleanup_budget)
        guard = lifecycle.Monitor(monitor); guard.start()
        require((now()-stamp(args.outer_started)).total_seconds() <= 30,
                'first resource observation exceeded outer startup allowance')
        store = Store(records)
        for row in plan['series']:
            require(not any(rid == row['id'] or rid.startswith(row['id'] + '.') for rid in store.by_id)
                    and not list(BUILD_ROOT.glob(row['id'] + '*')), 'series IDs or build paths already exist; no retry')
        validate_cleanup_tests(admission)
        prerequisites, availability = validate_inputs(plan, admission, store)
        receipt.update(code_commit=admission['code_commit'], runtime_sha256=admission['runtime_sha256'],
                       raw_input_verification=availability, prerequisites=prerequisites)
        def guarded():
            guard.check(); return guard.observe()
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
            with cleanup_budget.reservation():
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
