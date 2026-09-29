#!/usr/bin/env python3
"""Fixed corrective coverage a2. Interface v1. Date: 2026-09-26 ET.

One outer clock: TERM3570/KILL30, including helper/preflight/final persistence.
The required admission pins code, Linux fixture proofs and whole-native cleanup.
No retries, source edits, providers, protocol publication or performance claims.
"""
import argparse
import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_dx100_coverage_execution as original
from scripts import bfs_native_one_thread_pilot as native
from scripts import bfs_owned_observer as observer
from scripts import bfs_t17_build_only as build_only
from scripts.bfs_native_paired_pilot import ResourceMonitor
from scripts.bfs_owned_rss import RSS_SOURCE
from scripts.bfs_process import interruption_signals
from scripts.bfs_simulator_batch import lease_observation
from scripts.bfs_witness_launch import stop_owned
from swdb import artifacts, yamlio
from swdb.store import Store

RUN_ID = 'bfs-dx100-coverage-20260926-a2'
PLAN = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-coverage-a2-20260926.json'
PLAN_SHA = 'd78c09751d9b56abddcce0a7217983fc1652ef6dc83c09fc55ecf8a9a4d4be5a'
LANE = 'mbit10-evaluation-node0'
require, stamp, now, ref, exact = native.require, native.witness.stamp, native.now, native.ref, native.exact
read = native.read
REMOVED_ENV = ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE',
    'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH', 'CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH')
FIXED_ENV = {'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': '/data1/yanruj/tmp', 'PATH': '/usr/bin:/bin'}


def validate_plan(value):
    require(artifacts.digest(value) == PLAN_SHA, 'a2 prospective request changed')
    require(exact(value['compile_request'], original.compile_request(run_id=RUN_ID)), 'a2 compile request changed')
    return value


def runtime_identity(commit, root=ROOT):
    result = native.runtime_identity(commit, root=root)
    plan_path = root/PLAN.relative_to(ROOT)
    require(subprocess.run(['git', 'diff', '--quiet', commit, '--', str(PLAN.relative_to(ROOT)), 'pyproject.toml'],
                           cwd=root, timeout=5).returncode == 0, 'a2 plan differs from the code pin')
    result['a2_plan'] = ref(plan_path)
    result['project_config'] = ref(root/'pyproject.toml')
    validate_plan(read(result['a2_plan']))
    names = subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'--','tests'],cwd=root,timeout=5).decode().splitlines()
    actual = {str(p.relative_to(root)) for p in (root/'tests').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(names and set(names) == actual and len(names) <= 4096
            and subprocess.run(['git','diff','--quiet',commit,'--','tests'],cwd=root,timeout=5).returncode == 0,
            'Linux fixture source tree differs from the code pin')
    require(all(not (root/name).is_symlink() for name in names), 'Linux fixture source is symlinked')
    result['test_files'] = {name:ref(root/name) for name in names}
    return result


def validate_linux_proof(reference, kind, commit, prepared_at, runtime):
    """Reopen pinned Linux contract tests, never simulator acceptance evidence."""
    proof = read(reference)
    require(proof.get('format') == 'swdb.bfs.linux-fixture.v1' and proof.get('kind') == kind
            and proof.get('host') == 'mbit10' and proof.get('platform') == 'linux'
            and proof.get('evidence_kind') == 'contract_fixture'
            and proof.get('code_commit') == commit and proof.get('state') == 'passed'
            and type(proof.get('returncode')) is int and proof['returncode'] == 0
            and stamp(proof['started']) <= stamp(proof['finished']) <= prepared_at,
            'reviewed Linux fixture identity/result is missing')
    require(exact(proof.get('runtime'), runtime), 'Linux fixture runtime differs from the admitted runtime')
    command = proof.get('command', [])
    require(isinstance(command, list) and len(command) > 3 and command[1:3] == ['-m', 'pytest']
            and str(Path(command[0]).resolve()) == runtime['python']['path']
            and any(arg.startswith('--junitxml=') and arg.split('=', 1)[1] == proof['junit']['path'] for arg in command),
            'Linux fixture command is unbound')
    original.a3.reference(proof['stdout'], 16*1024**2)
    report = ET.fromstring(original.a3.reference(proof['junit'], 4*1024**2))
    cases = report.findall('.//testcase')
    require(cases and all(not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped')) for case in cases),
            'Linux fixture contains no cases or an unsuccessful/skipped case')
    names = {case.get('name', '') for case in cases}
    if kind == 'owned_cleanup':
        require('tests/test_bfs_dx100_coverage_a2.py::test_linux_a2_reaps_detached_child' in command,
                'Linux proof command omits the a2 owned cleanup selector')
        require({'test_linux_a2_reaps_detached_child[False]', 'test_linux_a2_reaps_detached_child[True]'} <= names,
                'Linux proof omits a2 success/failure detached cleanup')
    else:
        require('tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem' in command,
                'Linux proof command omits the public interruption selector')
        require(kind == 'dx100_interruption' and {'test_public_interruption_is_durable_before_postmortem[raises]',
            'test_public_interruption_is_durable_before_postmortem[stalls]'} <= names,
                'Linux proof omits the public interruption fixture')
    return {'proof': reference, 'kind': kind, 'cases': len(cases), 'evidence_kind': 'contract_fixture'}


def native_terminal(reference, plan, store, current, proc=Path('/proc')):
    """Recheck whole-client termination without admitting its measurements."""
    audit = read(reference); driver = read(audit['driver'])
    fixed = plan['native']; native_plan = read(driver['plan'])
    require(artifacts.digest(native_plan) == fixed['plan_sha256'] == native.PLAN_SHA
            and audit.get('id') == driver.get('id') == fixed['id']
            and driver.get('state') in fixed['outcomes']
            and driver.get('repository_commit') == fixed['commit']
            and driver.get('plan_canonical_sha256') == fixed['plan_sha256']
            and exact(driver.get('bounds'), native_plan['bounds'])
            and exact(driver.get('native_runtime'), native_plan['native_runtime'])
            and driver.get('gain_claim') is driver.get('protocol_freeze') is driver.get('provider_calls') is False,
            'native terminal identity or original scope differs')
    begin, end = stamp(driver['started']), stamp(driver['finished'])
    outer, deadline = stamp(driver['outer_start']), stamp(driver['outer_end'])
    b, w = native_plan['bounds'], native_plan['window']
    require(stamp(w['not_before']) <= outer <= begin <= stamp(w['latest_start'])
            and 0 <= (begin-outer).total_seconds() <= 5 and begin <= end <= deadline <= stamp(w['absolute_end'])
            and deadline-outer == timedelta(seconds=b['shared_seconds'])
            and type(driver.get('host_wall_s')) in (int, float)
            and abs((end-begin).total_seconds()-driver['host_wall_s']) <= 1
            and 0 <= driver['host_wall_s'] <= b['shared_seconds']
            and end <= stamp(audit['observed_at']) <= current, 'native original outer budget is unverified')
    if driver.get('phase') == 'primary':
        require((end-outer).total_seconds() <= b['primary_outer_seconds'], 'native primary exceeded its original budget')
    else:
        phase = stamp(driver['diagnostic_started'])
        require(driver.get('phase') == 'diagnostic' and begin <= phase <= end
                and (phase-outer).total_seconds() <= b['primary_outer_seconds']
                and (end-phase).total_seconds() <= b['diagnostic_outer_seconds'], 'native phase budget changed')
    runtime = driver['runtime']; root = Path(runtime['root'])
    actual = native.runtime_identity(fixed['commit'], root=root)
    require(all(exact(runtime.get(key), actual[key]) for key in ('root', 'repository_commit', 'files')),
            'native retained runtime differs from the selected commit')
    original.a3.reference(runtime['python'], 128*1024**2)
    admission = read(driver['admission'])
    require(admission.get('code_commit') == fixed['commit'] and admission.get('plan_sha256') == fixed['plan_sha256']
            and stamp(admission['prepared_at']) <= begin, 'native original admission is unbound')
    native.prerequisites(native_plan, admission, store)
    lane = read(audit['lane'])['socket_lane']; lease = read(audit['lease_snapshot'])
    exit_bytes = original.a3.reference(audit['outer_exit'], 64).decode().strip()
    require(re.fullmatch(r'-?\d+', exit_bytes) is not None, 'native outer exit is malformed')
    success = driver['state'] in {'complete', 'primary_unqualified'}
    require(lane.get('host') == 'mbit10' and type(lane.get('node')) is int and lane['node'] == 1
            and lane.get('lease_name') == 'mbit10-evaluation-node1'
            and type(lane.get('lease_generation')) is int and lane['lease_generation'] > 0
            and type(lane.get('exit_code')) is int
            and ((lane['exit_code'] == int(exit_bytes) == 0) if success else (lane['exit_code'] != 0 and int(exit_bytes) != 0))
            and stamp(lane['started_utc']) <= begin <= end <= stamp(lane['ended_utc'])+timedelta(seconds=1)
            and stamp(lane['ended_utc']) <= stamp(audit['observed_at'])
            and driver['lane']['verified_lane'] == f"mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation {lane['lease_generation']})"
            and lease.get('state') == 'released' and lease['lease']['generation'] == lane['lease_generation']
            and lease['lease']['lease_name'] == lane['lease_name']
            and stamp(lane['ended_utc']) <= stamp(lease['released_at']) <= stamp(audit['observed_at']),
            'native actual lane/exit/release is unbound')
    observations = driver['process_observations']; identity = observations['driver_identity']; pane = observations['pane_identity']
    ancestors = observations['ancestry']
    require(identity['pid'] == driver['driver_pid'] and ancestors and exact(ancestors[0], identity)
            and (ancestors[-1]['pid'], ancestors[-1]['start_ticks']) == (pane['pid'], pane['start_ticks'])
            and all(row['parent_pid'] == parent['pid'] for row, parent in zip(ancestors, ancestors[1:])),
            'native driver/pane ancestry is unbound')
    samples = [json.loads(line) for line in original.a3.reference(driver['rss']['samples'], 64*1024**2).splitlines() if line.strip()]
    require(samples and all(isinstance(row.get('processes'), list) and row['processes'] for row in samples),
            'native terminal sampled identity evidence is incomplete')
    retained = ancestors + observations['owned_processes'] + [identity, pane]
    retained += [p for sample in samples for p in sample['processes']]
    for stage in driver['stages']:
        require(begin <= stamp(stage['started']) <= stamp(stage['finished']) <= end
                and stage.get('state') in {'complete', 'failed'}, 'native terminal contains an active/future public stage')
        if stage.get('identity'):
            require(stage['identity']['parent_pid'] == identity['pid'], 'native direct stage parent differs')
            retained.append(stage['identity'])
        retained += stage.get('cleanup', {}).get('observed', [])
    retained += driver.get('cleanup', {}).get('observed', [])
    keys = lambda rows: {(p['pid'], p['start_ticks']) for p in rows}
    require(all(type(p.get('pid')) is int and p['pid'] > 0 and type(p.get('start_ticks')) is int and p['start_ticks'] >= 0
                for p in retained) and keys(retained) <= keys(audit['owned_processes']),
            'native terminal audit omits an observed owned identity')
    cleanup = audit.get('cleanup_state', audit.get('state'))
    zombie = cleanup == 'terminal_no_live_owned_processes'
    require((zombie and audit.get('owned_processes_absent') is False and audit.get('owned_processes_nonrunning') is True)
            or (cleanup == 'terminal_and_reaped' and audit.get('owned_processes_absent') is True),
            'native terminal audit does not establish cleanup')
    original.a3.verify_terminal_processes(audit['owned_processes'], proc,
        launcher_identity=(pane['pid'], pane['start_ticks']) if zombie else None)
    return {'audit': reference, 'driver': audit['driver'], 'native_state': driver['state'],
            'qualification_used': False, 'cleanup_verified': True, 'repository_commit': fixed['commit']}


def validate_admission(reference, plan, store, commit, started, *, runtime_root=ROOT):
    value = read(reference)
    require(value.get('format') == 'swdb.bfs.coverage-a2-admission.v1' and value.get('code_commit') == commit
            and value.get('plan_sha256') == PLAN_SHA and stamp(value['prepared_at']) <= started,
            'a2 prospective admission is unbound')
    runtime = runtime_identity(commit, root=runtime_root)
    require(exact(value.get('runtime'), runtime), 'a2 runtime differs from prospective admission')
    for name,digest in plan['required_runtime_sha256'].items():
        retained = runtime['test_files' if name.startswith('tests/') else 'files'].get(name,{})
        require(retained.get('sha256') == digest, 'a2 required interruption/observer correction differs: '+name)
    require(set(value.get('linux_proofs', {})) == {'owned_cleanup', 'dx100_interruption'}, 'both Linux fixture proofs are required')
    proofs = {kind: validate_linux_proof(proof, kind, commit, stamp(value['prepared_at']), runtime)
              for kind, proof in value['linux_proofs'].items()}
    for rid, digest in plan['record_sha256'].items():
        require(artifacts.digest(store.get(rid)) == digest, 'fixed record changed: '+rid)
    require(exact(value.get('fixed_prerequisites'), plan['fixed_prerequisites']), 'historical prerequisite pins changed')
    fixed = plan['fixed_prerequisites']
    prepared = stamp(value['prepared_at'])
    previous = {'a3': original.validate_a3(fixed['a3'], store, prepared),
                'coverage': {'audit': fixed['coverage'], 'state': build_only.coverage_cleanup(
                    fixed['coverage'], plan['historical_coverage_commit'], prepared)['state']}}
    for kind in ('paired', 'provider'): previous[kind] = original.a3.validate_completion(fixed[kind], kind, prepared)
    previous['native'] = native_terminal(value['native_terminal'], plan, store, prepared)
    original.validate_source(store)
    require(artifacts.digest(yamlio.load(original.a3.REQUEST)) == plan['execution_binding']['template_sha256']
            and artifacts.file_hash(original.graph_case.__file__) == plan['graph']['generator_sha256'], 'fixed source/template changed')
    return {'admission': reference, 'runtime': runtime, 'linux_proofs': proofs, 'prerequisites': previous}


class Clock:
    def __init__(self, plan, outer_started, outer_deadline):
        self.bounds = plan['bounds']; self.started, self.end = stamp(outer_started), stamp(outer_deadline)
        current = now(); w = plan['window']
        require(stamp(w['not_before']) <= self.started <= stamp(w['latest_start'])
                and self.end-self.started == timedelta(seconds=self.bounds['outer_seconds'])
                and self.end <= stamp(w['absolute_end']) and 0 <= (current-self.started).total_seconds() <= 5,
                'a2 must enter within its original complete 3600-second outer window')
        self.hard = time.monotonic()+(self.end-current).total_seconds()

    def remaining(self, cleanup=False):
        reserve = 0 if cleanup else self.bounds['cleanup_seconds']
        return min(self.hard-time.monotonic(), (self.end-now()).total_seconds())-reserve

    def check(self, cleanup=False):
        require(self.remaining(cleanup) > 0, 'a2 original shared deadline exhausted')


class Driver:
    def __init__(self, plan, clock, folder, build, records, owned, pane, *, entered_at=None):
        self.plan, self.clock, self.folder, self.build, self.records, self.owned = plan, clock, Path(folder), Path(build), Path(records), owned
        entered_at = entered_at or now()
        require(0 <= (entered_at-clock.started).total_seconds() <= 5, 'a2 actual driver entry is outside outer startup allowance')
        self.folder.mkdir(parents=True, exist_ok=False)
        self.samples = self.folder/'rss-samples.jsonl'; self.cleanup_spent = 0; self.last_sample = clock.started
        self.monitor = None; self.guard = None
        identity = observer.identity(os.getpid())
        self.receipt = {'format': 'swdb.bfs.coverage-a2-driver.v1', 'id': RUN_ID, 'created': '2026-09-26', 'state': 'running',
            'started': entered_at.isoformat(), 'outer_started': clock.started.isoformat(),
            'outer_deadline': clock.end.isoformat(), 'bounds': plan['bounds'],
            'plan_sha256': PLAN_SHA, 'plan': ref(PLAN), 'driver_pid': os.getpid(), 'stages': [],
            'gain_claim': False, 'profiling': False, 'automatic_retry_allowed': False, 'provider_calls': False,
            'cleanup_verified': False, 'rss': {'sampled_peak_bytes': 0, 'source': RSS_SOURCE}, 'artifact_peak_bytes': 0,
            'records': str(self.records), 'cleanup_seconds_used': 0}
        self.observations = {'driver_pid': os.getpid(), 'driver_identity': identity, 'observer_identity': identity,
            'observer_kind': 'in_process_driver', 'pane_pid': pane['pid'], 'launcher_identity': pane,
            'ancestry': observer.ancestry(identity, pane), 'cleanup_verified': False,
            'state': 'observing', 'sampling_complete': False}
        self.save()

    def save(self):
        (self.folder/'driver.json').write_text(json.dumps(self.receipt, indent=2)+'\n')

    def cleanup_remaining(self):
        return min(self.clock.remaining(True), self.plan['bounds']['cleanup_seconds']-self.cleanup_spent)

    def cleanup(self):
        start = time.monotonic()
        try:
            allowance = min(5, self.cleanup_remaining()-2)
            require(allowance > 0, 'a2 shared adopted cleanup reserve exhausted')
            return self.owned.finish(seconds=allowance)
        finally:
            self.cleanup_spent += time.monotonic()-start
            self.receipt['cleanup_seconds_used'] = self.cleanup_spent
            require(self.cleanup_spent <= self.plan['bounds']['cleanup_seconds'], 'a2 cumulative cleanup exceeded30s')
            self.clock.check(cleanup=True)

    def accounting(self, cleanup=False):
        size = original.artifact_bytes([self.folder, self.build])
        size += sum(p.lstat().st_size for p in self.records.rglob(RUN_ID+'*.yaml'))
        value = {'artifact_bytes': size, 'raw_free_bytes': shutil.disk_usage(self.folder).free,
            'build_free_bytes': shutil.disk_usage(self.build.parent).free,
            'observed_at': now().isoformat(), 'elapsed_seconds': (now()-self.clock.started).total_seconds()}
        b = self.plan['bounds']; self.clock.check(cleanup)
        require(size <= b['artifact_bytes'] and value['raw_free_bytes'] >= b['raw_reserve_bytes']
                and value['build_free_bytes'] >= b['build_reserve_bytes'], 'a2 storage bound/reserve exhausted')
        return value

    def observe(self):
        start, before = time.monotonic(), now(); row = self.owned.sample()
        row.update(self.accounting(cleanup=True))
        if self.guard is not None:
            leases = self.guard(); row.update(lane=leases['verified_lane'], leases=leases)
        else: row['lane'] = self.receipt.get('lane')
        sampled = stamp(row['sampled_at'])
        row.update(guard_started=before.isoformat(), guard_finished=now().isoformat(), guard_seconds=time.monotonic()-start)
        with self.samples.open('a') as stream: stream.write(json.dumps(row)+'\n')
        require(0 <= (sampled-self.last_sample).total_seconds() <= 30 and row['guard_seconds'] <= 30,
                'a2 resource guard gap/duration exceeded30s')
        self.last_sample = sampled
        self.receipt['rss']['sampled_peak_bytes'] = max(self.receipt['rss']['sampled_peak_bytes'], row['rss_bytes'])
        self.receipt['artifact_peak_bytes'] = max(self.receipt['artifact_peak_bytes'], row['artifact_bytes'])
        require(row['rss_source'] == RSS_SOURCE and row['rss_bytes'] <= self.plan['bounds']['sampled_rss_bytes'],
                'a2 sampled RSS bound/basis failed')

    def check(self):
        if self.monitor is not None: self.monitor.check()
        self.clock.check()

    def stage(self, name, command, seconds, *, env=None, require_success=True):
        self.check(); require(self.clock.remaining() >= seconds, 'a2 lacks the full next stage allowance')
        require(self.cleanup_remaining() > 2, 'a2 cannot admit a stage without its remaining cleanup reserve')
        row = {'name': name, 'command': list(map(str, command)), 'cwd': str(ROOT), 'state': 'running',
            'started': now().isoformat(), 'timeout_seconds': seconds}
        self.receipt['stages'].append(row); self.save()
        out, err = self.folder/(name+'.stdout'), self.folder/(name+'.stderr')
        child, error = None, None; start = time.monotonic()
        try:
            until = start+seconds
            with out.open('x') as stdout, err.open('x') as stderr:
                child = subprocess.Popen(row['command'], cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                row['identity'] = observer.identity(child.pid); require(row['identity'] is not None, 'a2 child identity unavailable')
                self.owned.remember(row['identity']); self.save()
                while child.poll() is None:
                    self.check(); require(time.monotonic() < until, 'a2 public stage timeout')
                    time.sleep(min(.1, max(0, until-time.monotonic())))
                require(time.monotonic() <= until, 'a2 public stage exceeded its work allowance')
                row.update(state='complete' if child.returncode == 0 else 'failed')
                require(not require_success or child.returncode == 0, 'a2 public stage failed')
        except BaseException as exc:
            error = exc; row.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        finally:
            row.update(work_finished=now().isoformat(), work_wall_s=time.monotonic()-start)
            if child is not None:
                cleanup_start = time.monotonic()
                remaining = max(0, self.cleanup_remaining()-5)
                hard = min(self.clock.hard-5, cleanup_start+remaining)
                try:
                    if child.poll() is None:
                        require(row.get('identity') is not None, 'a2 child identity missing during cleanup')
                        stop_owned(child, row['identity'], hard,
                            min(self.clock.end-timedelta(seconds=5), now()+timedelta(seconds=remaining)), observer.identity)
                except BaseException as exc:
                    error = error or exc; row.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
                # A failed signal/identity check does not discharge direct-child reap.
                # Both attempts retain the same original cleanup deadline.
                try:
                    child.wait(timeout=max(0, min(hard-time.monotonic(), self.clock.remaining(True)-5)))
                except BaseException as exc:
                    error = error or exc; row.update(state='failed', reap_error=f'{type(exc).__name__}: {exc}')
                finally:
                    self.cleanup_spent += time.monotonic()-cleanup_start
                row.update(returncode=child.returncode, reaped=child.returncode is not None)
                try: row['cleanup'] = self.cleanup()
                except BaseException as exc:
                    error = error or exc; row.update(state='failed', descendant_cleanup_error=f'{type(exc).__name__}: {exc}')
            row.update(finished=now().isoformat(), host_wall_s=time.monotonic()-start,
                       stdout=ref(out) if out.exists() else None, stderr=ref(err) if err.exists() else None)
            self.save()
        if error is not None: raise error
        self.check()
        return read(row['stdout'], 16*1024**2)

    def public(self, command, request, seconds, env, *, require_success=True):
        path = self.folder/(command+'.request.json')
        with path.open('x') as stream: stream.write(json.dumps(request, indent=2)+'\n')
        self.receipt.setdefault('requests', {})[command] = ref(path)
        argv = [str(Path(sys.executable).absolute()), '-s', '-m', 'swdb', command, str(path), '--records', str(self.records)]
        if command.startswith('dx100-'): argv += ['--runs-dir', str(self.folder), '--lane', '0']
        return self.stage(command, argv+['--format', 'json'], seconds, env=env, require_success=require_success)

    def stop_monitor(self):
        """Use the existing monitor's shutdown handshake with a clipped join."""
        start = time.monotonic()
        try:
            allowance = min(10, self.cleanup_remaining()-2)
            require(allowance > 0, 'a2 monitor shutdown lacks remaining shared cleanup time')
            require(self.monitor.signal_lock.acquire(timeout=allowance), 'a2 monitor shutdown lock exhausted cleanup time')
            try: self.monitor.done.set()
            finally: self.monitor.signal_lock.release()
            if self.monitor.thread is not None:
                remaining = max(0, min(allowance-(time.monotonic()-start), self.cleanup_remaining()-2))
                self.monitor.thread.join(timeout=remaining)
                require(not self.monitor.thread.is_alive(), 'a2 resource monitor did not stop within shared cleanup allowance')
            self.monitor.check()
        finally:
            self.cleanup_spent += time.monotonic()-start
            self.receipt['cleanup_seconds_used'] = self.cleanup_spent
            require(self.cleanup_spent <= self.plan['bounds']['cleanup_seconds'], 'a2 cumulative monitor cleanup exceeded30s')
            self.clock.check(cleanup=True)

    def finalize(self, error=None):
        if error is not None: self.receipt.update(state='failed', reason=f'{type(error).__name__}: {error}')
        final_start, previous_cleanup = time.monotonic(), self.cleanup_spent
        def remaining_finalization():
            self.cleanup_spent = max(self.cleanup_spent, previous_cleanup+time.monotonic()-final_start)
            self.receipt['cleanup_seconds_used'] = self.cleanup_spent
            require(self.cleanup_spent <= self.plan['bounds']['cleanup_seconds'], 'a2 finalization exhausted cumulative30s cleanup')
            self.clock.check(cleanup=True)
        failure = None
        try:
            if self.monitor is not None:
                try: self.stop_monitor()
                except BaseException as exc: failure = exc
            self.receipt['cleanup'] = self.cleanup()
            self.observe()
            if failure is not None: raise failure
        except BaseException as exc:
            self.receipt.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
        def observations():
            if self.samples.exists(): self.receipt['rss']['samples'] = ref(self.samples)
            self.observations.update(state='driver_sampling_finished' if self.receipt['state']=='complete' else 'failed',
                sampling_complete=self.receipt['state']=='complete', resource_samples=self.receipt['rss'].get('samples'),
                owned_processes=[{'pid': p, 'start_ticks': s} for p,s in self.owned.retained_identities()])
            path = self.folder/'process-observations.json'; path.write_text(json.dumps(self.observations, indent=2)+'\n')
            self.receipt['process_observations'] = ref(path)
        try:
            observations()
            for _ in range(2):
                remaining_finalization()
                self.receipt['final_accounting'] = self.accounting(cleanup=True)
                self.receipt.update(finished=now().isoformat(), host_wall_s=(now()-stamp(self.receipt['started'])).total_seconds(),
                                    outer_wall_s=(now()-self.clock.started).total_seconds())
                require((now()-self.last_sample).total_seconds() <= 30, 'a2 final telemetry gap exceeded30s')
                self.save(); self.accounting(cleanup=True); remaining_finalization()
        except BaseException as exc:
            self.receipt.update(state='failed', finalization_error=f'{type(exc).__name__}: {exc}')
            observations(); self.receipt.update(finished=now().isoformat(), host_wall_s=(now()-stamp(self.receipt['started'])).total_seconds(),
                outer_wall_s=(now()-self.clock.started).total_seconds()); self.save()
        return 0 if self.receipt['state']=='complete' else 1


def graph_identity(graph, plan):
    expected = plan['graph']
    fields = ('vertices', 'directed_arcs', 'source', 'canonical_sha256')
    require(exact({key:graph[key] for key in fields}, {key:expected[key] for key in fields})
            and graph['author_bfs_source_sha256'] == original.graph_case.AUTHOR_SOURCE_SHA256
            and graph['representation']['sha256'] == expected['representation_sha256']
            and graph['representation']['bytes'] == expected['representation_bytes'], 'a2 fixed graph identity changed')


def capacity_snapshot(plan, proc=Path('/proc'), node_path=Path('/sys/devices/system/node/node0/meminfo')):
    inputs = {'node': node_path.read_text(), 'zones': (proc/'zoneinfo').read_text(),
              'global': (proc/'meminfo').read_text(), 'pressure': (proc/'pressure/memory').read_text()}
    value = original.dx100_capacity.capacity(inputs['node'], inputs['zones'], inputs['global'], 0, os.sysconf('SC_PAGE_SIZE'))
    require(value['eligible'] is True and value['estimated_available_kib']*1024 >= plan['bounds']['node_available_bytes']
            and value['global_available_kib']*1024 >= plan['bounds']['global_available_bytes'], 'a2 capacity gate failed')
    return {'observed_at': now().isoformat(), 'inputs': inputs, 'estimate': value, 'eligible': True}


def execute(driver, env):
    plan = driver.plan; folder = driver.folder
    python = str(Path(sys.executable).absolute())
    capacity = driver.stage('capacity', [python, str(ROOT/'scripts/dx100_capacity.py'), '--node', '0',
        '--output', str(folder/'capacity.json')], 30, env=env)
    driver.receipt['capacity'] = capacity
    generation_start = time.monotonic()
    graph = driver.stage('generate', [python, str(original.graph_case.__file__), '--output-directory', str(folder/'graph'),
        '--records', str(driver.records), '--lane', LANE], 120, env=env)
    graph_identity(graph, plan); driver.receipt['graph'] = graph
    remaining = 120-(time.monotonic()-generation_start); require(remaining > 0, 'a2 generation/registration allowance exhausted')
    workload = driver.public('register-workload', original.registration_request(graph, run_id=RUN_ID), remaining, env)
    require(time.monotonic()-generation_start <= 120, 'a2 generation/registration shared allowance exceeded')
    compiled = driver.public('dx100-compile', plan['compile_request'], 240, env)
    request = original.execution_request(compiled, workload, graph, run_id=RUN_ID)
    # Reapply availability/capacity before the heavy child, after compilation.
    driver.check(); driver.guard()
    driver.receipt['pre_execute_capacity'] = capacity_snapshot(plan)
    result = driver.public('dx100-execute', request, 3100, env, require_success=False)
    queried = driver.stage('fresh-get', [python, '-s', '-m', 'swdb', 'get', request['id'], '--records', str(driver.records), '--format', 'json'], 30, env=env)
    store = Store(driver.records)
    require(exact(queried, result) and exact(result, store.get(request['id'], 'evaluation')),
            'a2 fresh public retrieval differs')
    driver.receipt['coverage'] = original.validate_coverage(result, request, graph, run_id=RUN_ID)
    driver.check(); driver.receipt.update(state='complete', evaluation=result['id'], evaluation_sha256=artifacts.digest(result))


def finish_work(driver, expected_commit):
    require(exact(runtime_identity(expected_commit), driver.receipt['runtime']), 'a2 runtime changed during the attempt')
    # Rehashing is work: it cannot borrow the subsequent cleanup reserve.
    driver.check()


def validate_completed(reference, store, current, expected_commit, proc=Path('/proc')):
    """Admit only new a2 evidence; the caller selects the prospective code pin."""
    require(isinstance(expected_commit, str) and re.fullmatch('[a-f0-9]{40}', expected_commit), 'a2 caller code pin is required')
    audit = read(reference); value = read(audit['driver']); plan = validate_plan(read(value['plan']))
    b = plan['bounds']; begin, end = stamp(value['started']), stamp(value['finished'])
    outer, deadline = stamp(value['outer_started']), stamp(value['outer_deadline']); window = plan['window']
    require(audit.get('id') == value.get('id') == RUN_ID and audit.get('state') == 'passed'
            and value.get('state') == 'complete' and value.get('repository_commit') == expected_commit
            and value.get('plan_sha256') == PLAN_SHA and exact(value.get('bounds'), b)
            and stamp(window['not_before']) <= outer <= stamp(window['latest_start'])
            and 0 <= (begin-outer).total_seconds() <= 5
            and deadline-outer == timedelta(seconds=3600) and deadline <= stamp(window['absolute_end'])
            and begin <= end <= deadline and end <= stamp(audit['observed_at']) <= current
            and type(value.get('host_wall_s')) in (int, float) and 0 <= value['host_wall_s'] <= 3600
            and abs((end-begin).total_seconds()-value['host_wall_s']) <= 1
            and type(value.get('outer_wall_s')) in (int, float) and 0 <= value['outer_wall_s'] <= 3600
            and abs((end-outer).total_seconds()-value['outer_wall_s']) <= 1
            and type(value.get('cleanup_seconds_used')) in (int, float) and 0 <= value['cleanup_seconds_used'] <= 30
            and value.get('gain_claim') is value.get('profiling') is value.get('automatic_retry_allowed') is value.get('provider_calls') is False,
            'a2 completed identity, interval or original bounds differ')
    root = Path(value['runtime']['root']); folder = Path(audit['driver']['path']).parent
    require(folder == Path(plan['run_root'])/RUN_ID and value['records'] == str(root/'records'), 'a2 paths differ from the prospective plan')
    admitted = validate_admission(value['admission'], plan, store, expected_commit, outer, runtime_root=root)
    require(all(exact(value.get(key), admitted[key]) for key in ('runtime', 'linux_proofs', 'prerequisites')),
            'a2 retained admission/runtime differs from reopened inputs')
    require(exact(value.get('environment'), {**dict.fromkeys(REMOVED_ENV), **FIXED_ENV}), 'a2 controlled inputs changed')
    python = value['python']; resolved = Path(python['path']).resolve(strict=True)
    require(python['resolved'] == str(resolved) and python['sha256'] == artifacts.file_hash(resolved)
            == value['runtime']['python']['sha256'], 'a2 Python executable differs')
    original.validate_source(store)
    original.validate_resources(value)
    rows = [json.loads(line) for line in original.a3.reference(value['rss']['samples'], 16*1024**2).splitlines() if line.strip()]
    require(0 <= (stamp(rows[0]['sampled_at'])-outer).total_seconds() <= 30,
            'a2 initial resource sample omitted outer startup time')
    require(value['rss']['source'] == RSS_SOURCE and all(row.get('rss_source') == RSS_SOURCE
            and type(row.get('page_size_bytes')) is int and row['page_size_bytes'] > 0
            and all(type(p.get('rss_pages')) is int and p['rss_pages'] >= 0 and p['rss_bytes'] == p['rss_pages']*row['page_size_bytes']
                    for p in row['processes']) for row in rows), 'a2 RSS page/identity basis differs')
    original.validate_terminal_cleanup(audit, value, current, proc, in_process=True)
    observations = read(value['process_observations'])
    owned = {(p['pid'],p['start_ticks']) for p in observations['owned_processes']}
    final = value['final_accounting']
    require(value['cleanup']['state'] == 'all_owned_descendants_absent' and value['cleanup'].get('subreaper') is True
            and all((p['pid'],p['start_ticks']) in owned for p in value['cleanup']['observed'])
            and begin <= stamp(final['observed_at']) <= end
            and type(final.get('artifact_bytes')) is int and 0 <= final['artifact_bytes'] <= b['artifact_bytes']
            and final['raw_free_bytes'] >= b['raw_reserve_bytes'] and final['build_free_bytes'] >= b['build_reserve_bytes']
            and original.artifact_bytes([folder, Path(plan['build_root'])]) <= b['artifact_bytes'],
            'a2 final accounting/cleanup is incomplete')
    stages = value['stages']; names = ('capacity','generate','register-workload','dx100-compile','dx100-execute','fresh-get')
    caps = (30,120,120,240,3100,30); require(len(stages) == 6, 'a2 stage grid implies an extra or missing attempt')
    outputs = {}; last = begin
    for row,name,cap in zip(stages,names,caps):
        start, work_end, finish = stamp(row['started']),stamp(row['work_finished']),stamp(row['finished'])
        require(row.get('name') == name and row.get('state') == 'complete' and type(row.get('returncode')) is int and row['returncode'] == 0
                and row.get('reaped') is True and row['cleanup']['state'] == 'all_owned_descendants_absent'
                and type(row.get('timeout_seconds')) in (int,float) and 0 < row['timeout_seconds'] <= cap
                and type(row.get('work_wall_s')) in (int,float) and 0 <= row['work_wall_s'] <= row['timeout_seconds']+1
                and type(row.get('host_wall_s')) in (int,float) and 0 <= row['host_wall_s'] <= cap+30
                and last <= start <= work_end <= finish <= end
                and abs((work_end-start).total_seconds()-row['work_wall_s']) <= 1
                and abs((finish-start).total_seconds()-row['host_wall_s']) <= 1
                and (finish-outer).total_seconds() <= 3570 and row['cwd'] == str(root), 'a2 actual stage interval/allowance failed')
        last = finish; identity = row['identity']
        require(identity['parent_pid'] == value['driver_pid'] and (identity['pid'],identity['start_ticks']) in owned
                and all((p['pid'],p['start_ticks']) in owned for p in row['cleanup']['observed']), 'a2 stage cleanup union is incomplete')
        require(row['stdout']['path'] == str(folder/(name+'.stdout')) and row['stderr']['path'] == str(folder/(name+'.stderr')),
                'a2 stage output paths changed')
        outputs[name] = read(row['stdout'],16*1024**2); original.a3.reference(row['stderr'],16*1024**2)
        if name == 'capacity': expected = [python['path'],str(root/'scripts/dx100_capacity.py'),'--node','0','--output',str(folder/'capacity.json')]
        elif name == 'generate': expected = [python['path'],str(root/'scripts/bfs_dx100_coverage_graph.py'),'--output-directory',str(folder/'graph'),'--records',value['records'],'--lane',LANE]
        elif name == 'fresh-get': expected = [python['path'],'-s','-m','swdb','get',RUN_ID+'.execute','--records',value['records'],'--format','json']
        else:
            request = value['requests'][name]
            require(request['path'] == str(folder/(name+'.request.json')), 'a2 request path differs')
            expected = [python['path'],'-s','-m','swdb',name,request['path'],'--records',value['records']]
            if name.startswith('dx100-'): expected += ['--runs-dir',str(folder),'--lane','0']
            expected += ['--format','json']
        require(row['command'] == expected, 'a2 exact public command changed')
    require((stamp(stages[2]['finished'])-stamp(stages[1]['started'])).total_seconds() <= 120,
            'a2 generation/registration exceeded shared120s')
    capacity = read(outputs['capacity']); raw = capacity['inputs']
    estimate = original.dx100_capacity.capacity(raw['node'],raw['zones'],raw['global'],0,capacity['result']['page_size_bytes'])
    require(exact(capacity['result'],estimate) and estimate['eligible'] is True
            and begin <= stamp(capacity['observed']) <= stamp(stages[0]['finished']), 'a2 initial capacity is unbound')
    observed = value['pre_execute_capacity']; raw = observed['inputs']
    estimate = original.dx100_capacity.capacity(raw['node'],raw['zones'],raw['global'],0,observed['estimate']['page_size_bytes'])
    require(exact(observed['estimate'],estimate) and estimate['eligible'] is True
            and estimate['estimated_available_kib']*1024 >= b['node_available_bytes']
            and estimate['global_available_kib']*1024 >= b['global_available_bytes']
            and 0 <= (stamp(stages[4]['started'])-stamp(observed['observed_at'])).total_seconds() <= 30,
            'a2 pre-execution capacity is stale or inadequate')
    graph = value['graph']; graph_identity(graph,plan)
    compiled, workload, result = (outputs[name] for name in ('dx100-compile','register-workload','dx100-execute'))
    require(exact(outputs['generate'],graph) and all(exact(record,store.get(record['id'])) for record in (compiled,workload,result))
            and exact(outputs['fresh-get'],result) and value['evaluation'] == result['id']
            and artifacts.digest(result) == value['evaluation_sha256'] == audit['evaluation_sha256']
            and exact(yaml.load(original.a3.reference(audit['evaluation']).decode(), Loader=yamlio._Loader),result), 'a2 current/public result differs')
    expected = {'register-workload':original.registration_request(graph,run_id=RUN_ID),
        'dx100-compile':plan['compile_request'],'dx100-execute':original.execution_request(compiled,workload,graph,run_id=RUN_ID)}
    require(set(value['requests']) == set(expected) and all(exact(read(value['requests'][k]),v) for k,v in expected.items()),
            'a2 fixed public requests changed')
    coverage = original.validate_coverage(result,expected['dx100-execute'],graph,run_id=RUN_ID)
    require(exact(coverage,value['coverage']), 'a2 retained coverage differs from actual trace')
    return {'audit':reference,'evaluation':audit['evaluation'],'evaluation_sha256':audit['evaluation_sha256'],
            'repository_commit':expected_commit,'coverage':coverage,'gain_claim':False}


def main():
    entered_at = now()
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('expected-commit', 'outer-started', 'outer-deadline', 'admission-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--admission', type=Path, required=True)
    for name in ('pane-pid', 'pane-start-ticks'): parser.add_argument('--'+name, type=int, required=True)
    args = parser.parse_args(); plan = validate_plan(json.loads(PLAN.read_text()))
    clock = Clock(plan, args.outer_started, args.outer_deadline)
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10', 'a2 requires mbit10 Linux')
    root, build = Path(plan['run_root']), Path(plan['build_root']); records = ROOT/'records'; store = Store(records)
    require(not root.exists() and not build.exists(), 'a2 outputs already exist; no retry/overwrite')
    require(not any(store.get(RUN_ID+suffix) for suffix in ('.compile', '.execute'))
            and not any(r.data.get('requested_id') == RUN_ID+'.workload' for r in store.records), 'a2 record already exists')
    driver = Driver(plan, clock, root/RUN_ID, build, records, native.LockedOwned(),
                    {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}, entered_at=entered_at)
    error = None
    try:
        machine = store.get('mbit10', 'machine')
        def guard():
            value = lease_observation(machine, 0)
            require(not value['leases']['mbit10-evaluation-node1']['kernel_held']
                    and value['verified_lane'] == driver.receipt.get('lane', value['verified_lane']),
                    'a2 own lane changed or another socket became active')
            return value
        driver.guard = guard; driver.receipt['lane'] = guard()['verified_lane']
        driver.monitor = ResourceMonitor(driver.observe); driver.monitor.start()
        driver.receipt.update(repository_commit=args.expected_commit,
            **validate_admission({'path': str(args.admission.absolute()), 'sha256': args.admission_sha256}, plan, store, args.expected_commit, clock.started))
        for path, reserve in ((root, plan['bounds']['raw_reserve_bytes']), (build.parent, plan['bounds']['build_reserve_bytes'])):
            require(shutil.disk_usage(path).free >= reserve+plan['bounds']['artifact_bytes'], 'a2 full storage allowance plus reserve unavailable')
        env = dict(os.environ)
        for name in REMOVED_ENV: env.pop(name, None)
        env.update(FIXED_ENV); require(Path(env['TMPDIR']).is_dir(), 'a2 data1 temporary directory unavailable')
        driver.receipt['environment'] = {**dict.fromkeys(REMOVED_ENV), **FIXED_ENV}
        driver.receipt['python'] = {'path': str(Path(sys.executable).absolute()), 'resolved': str(Path(sys.executable).resolve()),
            'sha256': artifacts.file_hash(Path(sys.executable).resolve()), 'version': sys.version}
        execute(driver, env)
        finish_work(driver, args.expected_commit)
    except BaseException as exc: error = exc
    code = driver.finalize(error)
    print(json.dumps({'id': RUN_ID, 'state': driver.receipt['state'], 'driver': ref(driver.folder/'driver.json')}))
    return code


if __name__ == '__main__':
    with interruption_signals(): raise SystemExit(main())
