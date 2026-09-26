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
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from scripts.bfs_native_paired_pilot import DescendantRSS
from scripts import bfs_dx100_coverage_execution as coverage_case
from scripts import dx100_witness_continuation as witness_case
from scripts.bfs_simulator_series import admit_capacity, validate_diagnostic_build, validate_selection
from scripts.dx100_build import disk_usage_kib
from swdb import artifacts, bfs_coverage, bfs_protocol, profile, profile_package, yamlio
from swdb.store import Store

ET = ZoneInfo('America/New_York')
GIB = 1024**3
PLAN_HASHES = {'t15': 'ae7a3ff3378da283e867520837eec4a47173dff12bdfc1fbca0c6b99ddcf8927', 't16': '28c6a0c312f40aa545008dd28b0d4865d8d898a4e8be1d382509528f7cc23e79'}
PLAN_DIR = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests'
RAW_ROOTS = (Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))
BUILD_ROOT = Path('/data1/yanruj/EvolveSWDB_builds')
CLEANUP_RUNTIME = ('scripts/bfs_simulator_batch.py', 'scripts/bfs_process.py',
                   'scripts/bfs_native_paired_pilot.py', 'swdb/processes.py')


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
    return {str(path.relative_to(ROOT)): artifacts.file_hash(path)
            for name in ('swdb', 'scripts', 'schemas', 'vocab')
            for path in sorted((ROOT / name).rglob('*')) if path.is_file() and path.suffix in suffixes}


def allocated_bytes(paths):
    total = 0
    for value in paths:
        path = Path(value)
        require(path.exists() and path == path.resolve(), 'charged storage path missing or symlinked')
        used, warnings = disk_usage_kib(path)
        require(not warnings, 'raw-storage accounting is incomplete')
        total += used * 1024
    return total


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
    def __init__(self, plan, admission, started, started_at):
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
                and stamp(admission['prepared_at']) <= first <= started_at <= latest,
                'prospective schedule is absent, late, or cannot fit the remaining batch allowance')
        self.monotonic_end = started + available

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
        return {'observed_at': now().isoformat(), 'elapsed_seconds': time.monotonic() - self.started,
                'charged_elapsed_seconds': self.charged_seconds + time.monotonic() - self.started,
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
    require(plan['required_a3'] == witness_case.PROBE_ID
            and plan['required_coverage'] == coverage_case.RUN_ID + '.execute', 'prerequisite identities differ')
    current = stamp(admission['prepared_at'])
    observed = {'a3': coverage_case.validate_a3(proofs['a3'], store, current)}
    observed['coverage'] = coverage_case.validate_completed(proofs['coverage'], store, current,
                                                          admission['coverage_commit'])
    for kind in ('paired', 'provider'):
        observed[kind] = witness_case.validate_completion(proofs[kind], kind, current)
    return observed


def validate_cleanup_tests(admission):
    """Local fixture tests are insufficient authority for Linux process cleanup."""
    refs = admission['linux_cleanup_tests']
    require(isinstance(refs, list) and len(refs) == 2, 'two actual Linux cleanup test receipts are required')
    variants = set()
    expected = {name: admission['runtime_sha256'][name] for name in CLEANUP_RUNTIME}
    for ref in refs:
        result = read_reference(ref)
        require(result.get('format') == 'swdb.bfs.simulator-batch-cleanup-test.v1'
                and result.get('host') == 'mbit10' and result.get('platform') == 'linux'
                and result.get('repository_commit') == admission['code_commit']
                and result.get('runtime_sha256') == expected
                and result.get('fixture_only') is True and result.get('state') == 'passed'
                and type(result.get('failure_variant')) is bool
                and type(result.get('host_wall_s')) in (int, float)
                and 0 < result.get('host_wall_s', 0) <= 20
                and result.get('address_space_bytes') == 512 * 1024**2
                and result.get('cleanup', {}).get('state') == 'all_owned_descendants_absent'
                and result['cleanup'].get('subreaper') is True
                and stamp(result['finished']) <= stamp(admission['prepared_at']),
                'Linux cleanup admission is missing or differs from this exact code')
        variants.add(result['failure_variant'])
    require(variants == {False, True}, 'cleanup tests must exercise success and failure leaders')


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


def series_command(plan, row, admission, config, runs, records, node, seconds, storage):
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
        command = series_command(plan, row, admission, config, child_root, records, node, seconds, storage)
        entry = {'id': row['id'], 'state': 'running', 'command': command, 'started': now().isoformat(),
                 'series_seconds': seconds, 'remaining_storage_gib': storage}
        receipt['series'].append(entry); save_receipt(folder, receipt)
        output = folder / (row['id'] + '.stdout.json')
        try:
            run_stage(receipt, folder, command, timeout=seconds,
                deadline=min(ledger.monotonic_end, time.monotonic() + (ledger.end - now()).total_seconds())
                         - plan['bounds']['cleanup_seconds'], cwd=ROOT, output=output, monitor=monitor)
        finally:
            # run_stage already gave nested handlers their bounded graceful interval.
            try:
                entry['cleanup'] = owned.finish()
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
        validate_series_result(plan, row, admission, child, seconds, storage, Store(records))
        entry.update(state='complete', finished=now().isoformat(), receipt=child_ref)
        monitor()


def finalize_receipt(receipt, folder, runs, ledger, ledger_file):
    """Final hashing and persistence are inside the shared budget, even on failure."""
    def observation():
        row = ledger.observation(allocated_bytes([runs]))
        require(row['charged_raw_bytes'] < ledger.bounds['batch_storage_gib'] * GIB,
                'final retained storage exceeded the common allowance')
        require(time.monotonic() <= ledger.monotonic_end and now() <= ledger.end,
                'cleanup or final accounting exceeded the common deadline')
        return row

    try:
        if ledger_file.exists():
            receipt['ledger_artifact'] = {'path': str(ledger_file), 'sha256': artifacts.file_hash(ledger_file)}
        # The second write retains the first post-persistence observation. Both
        # writes are checked afterward; failure must not leave a complete receipt.
        for _ in range(2):
            receipt['final_ledger'] = observation()
            receipt.update(finished=now().isoformat(), elapsed_seconds=time.monotonic() - ledger.started)
            save_receipt(folder, receipt)
            observation()
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
    args = parser.parse_args()
    plan = yamlio.load(PLAN_DIR / f'bfs-{args.kind}-simulator-batch-20260926-a1.json')
    validate_plan(plan, args.kind)
    admission_ref = {'path': str(args.admission.absolute()), 'sha256': args.admission_sha256}
    admission = read_reference(admission_ref)
    require(socket.gethostname().split('.')[0] == 'mbit10', 'simulator batch execution requires mbit10')
    ledger = Ledger(plan, admission, started, started_at)
    runs = args.runs_dir.absolute()
    require(runs.name == plan['id'] and any(base in runs.parents for base in RAW_ROOTS)
            and runs == runs.resolve(), 'use the exact new batch name in authorized raw storage, without symlinks')
    require(not runs.exists(), 'batch root already exists; resumes and retries are forbidden')
    records = ROOT / 'records'
    store = Store(records)
    for row in plan['series']:
        require(not any(rid == row['id'] or rid.startswith(row['id'] + '.') for rid in store.by_id)
                and not list(BUILD_ROOT.glob(row['id'] + '*')), 'series IDs or build paths already exist; no retry')
    runs.mkdir(parents=True, exist_ok=False)
    folder = runs / (plan['id'] + '.driver'); folder.mkdir()
    receipt = {'id': plan['id'], 'created': '2026-09-26', 'state': 'running', 'started': started_at.isoformat(),
        'plan': plan, 'plan_sha256': artifacts.digest(plan), 'admission': admission_ref,
        'stages': [], 'series': [], 'gain_claim': False, 'protocol_freeze': False,
        'automatic_retry_allowed': False, 'ticket_acceptance': False, 'preparation_charges': admission['preparation_charges']}
    save_receipt(folder, receipt)
    owned = None
    ledger_file = folder / 'ledger.jsonl'
    def monitor():
        ledger.remaining()
        raw = allocated_bytes([runs])
        require(raw + ledger.charged_bytes < plan['bounds']['batch_storage_gib'] * GIB, 'shared batch raw-storage ceiling exceeded')
        for path, minimum in ((runs, plan['bounds']['raw_reserve_gib']), (BUILD_ROOT.parent, plan['bounds']['build_reserve_gib'])):
            stat = os.statvfs(path)
            require(stat.f_bavail * stat.f_frsize >= minimum * GIB, 'raw/build free-space reserve violated')
        sample = {**ledger.observation(raw), **lease_observation(store.get('mbit10'), args.lane),
                  'owned_processes': owned.sample()}
        with ledger_file.open('a') as stream:
            stream.write(json.dumps(sample) + '\n')
        return raw
    try:
        owned = OwnedDescendants()
        validate_cleanup_tests(admission)
        prerequisites, availability = validate_inputs(plan, admission, store)
        receipt.update(code_commit=admission['code_commit'], runtime_sha256=admission['runtime_sha256'],
                       raw_input_verification=availability, prerequisites=prerequisites)
        collect_series(plan, admission, receipt, folder, runs, records, args.lane, ledger, owned, monitor)
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        for entry in receipt['series']:
            if entry['state'] == 'running': entry.update(state='failed', finished=now().isoformat())
        raise
    finally:
        try:
            previous_cleanup = receipt['series'][-1].get('cleanup', {}) if receipt['series'] else {}
            receipt['cleanup'] = (previous_cleanup if previous_cleanup.get('state') == 'failed' else
                                  owned.finish() if owned else {'state': 'subreaper_not_admitted'})
            require(receipt['cleanup']['state'] != 'failed', 'owned cleanup exhausted its bounded attempt')
        except BaseException as exc:
            receipt.update(state='failed', final_accounting_error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            finalize_receipt(receipt, folder, runs, ledger, ledger_file)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    with interruption_signals():
        main()
