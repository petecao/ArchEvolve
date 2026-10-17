#!/usr/bin/env python3
"""One fixed T17 build-only attempt. Interface v1, dated 2026-09-26 ET.

Run from a separately pinned orchestration checkout, under one socket-0 helper
and `timeout --signal=TERM --kill-after=30s 270s`. The caller supplies its original
aware --outer-started/--outer-deadline (exactly 300 seconds), actual pane PID/start,
--expected-commit, and hashed --coverage-completion plus --coverage-commit. All
preflight, six public gets, one compile, fresh get/chain and persistence share
270 work seconds plus at most 30 cleanup seconds. Public children use only the
fixed provider checkout; no submit, provider, repair, retry or simulation exists.

The new fixed raw root retains driver.json, resource samples and public outputs.
The driver attests bounded descendant cleanup only. An independent terminal
audit must subsequently include its ancestry, every observed PID/start pair,
actual outer exit and released helper lease; the driver cannot attest its own
reaping. Linux-only subreaper/pidfd admission is mandatory before any public call.
"""
import argparse
from datetime import timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_dx100_coverage_execution as coverage
from scripts import bfs_owned_observer as observer
from scripts.bfs_process import interruption_signals
from scripts.bfs_simulator_batch import OwnedDescendants, lease_observation
from scripts.bfs_witness_launch import stop_owned
from swdb import artifacts, profile_package
from swdb.store import Store

RUN_ID = 'bfs-t17-build-only-20260926-a1'
PUBLIC_ROOT = Path('/data1/yanruj/EvolveSWDB_provider_20260926_a1')
PUBLIC_COMMIT = '5f1b8028619976b36df5fa24b8aacb91bf488168'
CODE_COMMIT = '6346189b55132f195b02544b729f34100d10ba92'
RAW = Path('/data/yanruj/EvolveSWDB_runs/bfs-t17-build-only-20260926')
BUILD = Path('/data1/yanruj/EvolveSWDB_builds') / RUN_ID
PREPARATION = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25'
REQUEST = PREPARATION / 'requests/t17-build-only-20260926-a1.json'
REQUEST_SHA = 'de1b10536fa91f675bb3372f9104c10fbf160f952ac9016538c5d38cdb6fc211'
OBSERVATION = PREPARATION / 'observations/t17-build-only-preflight-20260926.json'
OBSERVATION_SHA = '3085c06203e386862eb7b534afd8d0ff75e0129c20bc9f705f849b6b89d2f649'
COVERAGE_AUDIT_SHA = '65969e8cae4ce113c289ba79c9b3aafd852f36724dcd8c060d8f37837c5c971a'
BOUNDS = {'outer_seconds': 300, 'work_seconds': 270, 'cleanup_seconds': 30,
          'api_seconds': 240, 'build_seconds': 180, 'get_seconds': 15,
          'sampled_rss_bytes': 16 * 1024**3, 'artifact_bytes': 1024**3,
          'raw_reserve_bytes': 30 * 1024**3, 'build_reserve_bytes': 10 * 1024**3,
          'sample_interval_seconds': 5, 'sample_gap_seconds': 30}
require = observer.require
now = observer.now


def ref(path):
    return {'path': str(Path(path).absolute()), 'sha256': artifacts.file_hash(path)}


def owned_descendants():
    # Preserve the proven subreaper/pidfd owner and replace its legacy telemetry
    # before any child exists; old measured clients remain unchanged.
    from scripts.bfs_owned_rss import DescendantRSS
    owned = OwnedDescendants()
    owned.sampler = DescendantRSS(os.getpid())
    return owned


def runtime_tree(root, commit):
    """Bind every tracked public/orchestration source and reject Python shadows."""
    require(re.fullmatch('[a-f0-9]{40}', commit) is not None, 'prospective commit is required')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, timeout=5)
    require(git('rev-parse', 'HEAD').decode().strip() == commit, 'runtime checkout commit differs')
    folders = ('scripts', 'swdb', 'schemas', 'vocab')
    require(subprocess.run(['git', 'diff', '--quiet', commit, '--', *folders],
                           cwd=root, timeout=5).returncode == 0, 'runtime tracked source changed')
    names = git('ls-tree', '-rz', '--name-only', commit, '--', *folders).decode().split('\0')
    names = [name for name in names if name]
    require(names and len(names) <= 4096, 'runtime source inventory is missing or oversized')
    actual = {str(path.relative_to(root)) for folder in folders for path in (root / folder).rglob('*')
              if path.is_file() and '__pycache__' not in path.parts}
    require(actual == set(names)
            and not any((root / name).exists() for name in ('sitecustomize.py', 'usercustomize.py')),
            'runtime contains untracked code or configuration')
    require(all(not (root / name).is_symlink() for name in names), 'runtime source must not be symlinked')
    return {'root': str(root), 'commit': commit,
            'files': {name: artifacts.file_hash(root / name) for name in names}}


class Clock:
    def __init__(self, started, deadline):
        current = now()
        require(deadline - started == timedelta(seconds=BOUNDS['outer_seconds'])
                and started <= current < deadline - timedelta(seconds=BOUNDS['cleanup_seconds']),
                'caller must supply its original 300-second window with remaining work time')
        self.started, self.end = started, deadline
        self.hard = time.monotonic() + (deadline - current).total_seconds()
        self.work = self.hard - BOUNDS['cleanup_seconds']

    def remaining(self, cleanup=False):
        reserve = 0 if cleanup else BOUNDS['cleanup_seconds']
        return min(self.hard - time.monotonic(), (self.end - now()).total_seconds()) - reserve

    def check(self, cleanup=False):
        require(self.remaining(cleanup) > 0, 'original shared deadline exhausted')


class Attempt:
    def __init__(self, folder, build, clock, owned, pane, metadata=None):
        self.folder, self.build, self.clock, self.owned = Path(folder), Path(build), clock, owned
        self.folder.mkdir(exist_ok=False)
        self.sample_file = self.folder / 'resource-samples.jsonl'
        self.last_sample = None
        self.guard = None
        self.cleanup_spent = 0
        self.receipt = {'format': 'swdb.bfs.t17-build-only.v1', 'id': RUN_ID,
            'created': '2026-09-26', 'state': 'running', 'started': clock.started.isoformat(),
            'outer_deadline': clock.end.isoformat(), 'bounds': BOUNDS, 'gain_claim': False,
            'correctness_established': False, 'profiling': False, 'automatic_retry_allowed': False,
            'cleanup_verified': False, 'driver_identity': observer.identity(os.getpid()),
            'pane_identity': pane, 'stages': [], 'metadata': metadata or {},
            'resource_scope': 'driver and observed owned descendants across sessions',
            'sampled_guards_not_hard_caps': True,
            'rss_peak_sampled_bytes': 0, 'artifact_peak_sampled_bytes': 0}
        self.save()

    def save(self):
        (self.folder / 'driver.json').write_text(json.dumps(self.receipt, indent=2) + '\n')


    def cleanup_remaining(self):
        return min(self.clock.remaining(True), BOUNDS['cleanup_seconds']-self.cleanup_spent)

    def descendants(self):
        before = time.monotonic()
        try:
            allowed = min(5, self.cleanup_remaining()-2)
            require(allowed > 0, 'no remaining shared allowance for adopted descendant cleanup')
            return self.owned.finish(seconds=allowed)
        finally:
            self.cleanup_spent += time.monotonic()-before
            self.receipt['cleanup_seconds_used'] = self.cleanup_spent
            require(self.cleanup_spent <= BOUNDS['cleanup_seconds'], 'total shared cleanup allowance exhausted')
            self.clock.check(cleanup=True)

    def account(self, cleanup=False):
        row = {'observed_at': now().isoformat(),
               'elapsed_seconds': (now() - self.clock.started).total_seconds(),
               'artifact_bytes': coverage.artifact_bytes([self.folder, self.build]),
               'raw_free_bytes': shutil.disk_usage(self.folder).free,
               'build_free_bytes': shutil.disk_usage(self.build.parent).free}
        self.clock.check(cleanup)
        require(row['artifact_bytes'] <= BOUNDS['artifact_bytes'], 'shared raw/build storage exceeded')
        require(row['raw_free_bytes'] >= BOUNDS['raw_reserve_bytes']
                and row['build_free_bytes'] >= BOUNDS['build_reserve_bytes'], 'storage reserve exhausted')
        self.receipt['artifact_peak_sampled_bytes'] = max(self.receipt['artifact_peak_sampled_bytes'], row['artifact_bytes'])
        return row

    def sample(self, force=False, cleanup=False):
        before = time.monotonic()
        if not force and self.last_sample is not None and before - self.last_sample < BOUNDS['sample_interval_seconds']:
            self.clock.check(cleanup)
            return
        require(self.last_sample is None or before - self.last_sample <= BOUNDS['sample_gap_seconds'],
                'owned resource observation gap exceeded')
        row = self.owned.sample()
        require(row['rss_bytes'] <= BOUNDS['sampled_rss_bytes'], 'sampled owned RSS exceeded')
        row['accounting'] = self.account(cleanup)
        if self.guard is not None:
            row['leases'] = self.guard()
        with self.sample_file.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        require(time.monotonic() - before <= BOUNDS['sample_gap_seconds'], 'resource guard duration exceeded')
        self.last_sample = before
        self.receipt['rss_peak_sampled_bytes'] = max(self.receipt['rss_peak_sampled_bytes'], row['rss_bytes'])
        self.clock.check(cleanup)

    def stage(self, name, command, timeout, cwd, *, env=None, require_success=True):
        self.clock.check()
        require(self.cleanup_remaining() > 2, 'shared allowance cannot support another public stage')
        row = {'name': name, 'command': list(map(str, command)), 'cwd': str(cwd),
               'started': now().isoformat(), 'state': 'running'}
        self.receipt['stages'].append(row); self.save()
        out, err = self.folder / (name + '.stdout'), self.folder / (name + '.stderr')
        child, error = None, None
        begin = time.monotonic()
        try:
            row['timeout_seconds'] = min(timeout, self.clock.remaining())
            until = begin + row['timeout_seconds']
            with out.open('x') as stdout, err.open('x') as stderr:
                child = subprocess.Popen(row['command'], cwd=cwd, env=env, stdout=stdout,
                                         stderr=stderr, start_new_session=True)
                row['identity'] = observer.identity(child.pid)
                require(row['identity'] is not None, 'public child identity unavailable')
                self.save()
                while child.poll() is None:
                    self.sample()
                    require(time.monotonic() < until, 'public stage timeout exhausted')
                    time.sleep(min(.1, max(0, until-time.monotonic())))
                self.clock.check()
                row['state'] = 'complete' if child.returncode == 0 else 'failed'
                require(not require_success or child.returncode == 0, 'public stage returned an unsuccessful exit')
        except BaseException as exc:
            row.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
            error = exc
        finally:
            if child is not None:
                shutdown_start = time.monotonic()
                remaining = max(0, self.cleanup_remaining()-5)
                shutdown_end = min(self.clock.hard-5, shutdown_start+remaining)
                try:
                    if child.poll() is None:
                        require(row.get('identity') is not None, 'missing owned child identity during cleanup')
                        # Preserve at least five seconds for adopted descendants and final receipts.
                        stop_owned(child, row['identity'], shutdown_end,
                                   min(self.clock.end-timedelta(seconds=5), now()+timedelta(seconds=remaining)), observer.identity)
                except BaseException as exc:
                    error = error or exc
                    row.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
                try:
                    child.wait(timeout=max(0, min(shutdown_end-time.monotonic(), self.clock.remaining(True)-5)))
                except BaseException as exc:
                    error = error or exc
                    row.update(state='failed', reap_error=f'{type(exc).__name__}: {exc}')
                finally:
                    self.cleanup_spent += time.monotonic()-shutdown_start
                row.update(returncode=child.returncode, reaped=child.returncode is not None)
                try:
                    # A reaped leader can leave a nested new session. The next
                    # public stage must not overlap that adopted process tree.
                    row['descendant_cleanup'] = self.descendants()
                except BaseException as exc:
                    error = error or exc
                    row.update(state='failed', descendant_cleanup_error=f'{type(exc).__name__}: {exc}')
            row.update(finished=now().isoformat(), host_wall_s=time.monotonic()-begin,
                       stdout=ref(out) if out.exists() else None, stderr=ref(err) if err.exists() else None)
            self.save()
        if error is not None:
            raise error
        self.sample(force=True)
        require(out.stat().st_size <= 8 * 1024**2, 'public JSON output exceeded its read bound')
        return json.loads(out.read_text())

    def finish(self, error=None):
        if error is not None:
            self.receipt.update(state='failed', reason=f'{type(error).__name__}: {error}')
        try:
            self.receipt['descendant_cleanup'] = self.descendants()
            self.sample(force=True, cleanup=True)
        except BaseException as exc:
            self.receipt.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
        try:
            if self.sample_file.exists():
                self.receipt['resource_samples'] = ref(self.sample_file)
            self.receipt['known_owned_identities'] = [dict(pid=pid, start_ticks=start)
                                                     for pid, start in self.owned.sampler.known.items()]
            for _ in range(2):
                self.receipt['final_accounting'] = self.account(cleanup=True)
                self.receipt['finished'] = now().isoformat()
                self.save()
                self.account(cleanup=True)
        except BaseException as exc:
            self.receipt.update(state='failed', finalization_error=f'{type(exc).__name__}: {exc}', finished=now().isoformat())
            self.save()
        return 0 if self.receipt['state'] == 'complete' else 1


def public_command(*args):
    return [str(Path(sys.executable).absolute()), '-s', '-m', 'swdb', *map(str, args),
            '--records', str(PUBLIC_ROOT / 'records'), '--format', 'json']


def verify_inputs(values, pins):
    for key in ('proposal', 'candidate', 'source_snapshot'):
        require(artifacts.digest(values[key]) == pins[key]['canonical_sha256'], key + ' record changed')
    require(artifacts.digest(values['model']) == pins['model']['build_canonical_sha256']
            and artifacts.digest(values['target']) == pins['model']['target_canonical_sha256'], 'model/target changed')
    profile_package.verify(values['package'])
    require(values['package']['id'] == values['proposal']['profile_package']
            == pins['proposal']['profile_package'], 'origin profile package changed')
    for key in ('candidate', 'source_snapshot'):
        root = artifacts.verify(values[key]['artifact'])
        if key == 'candidate': artifacts.check_protections(root, values[key]['protections'])
    require(values['candidate']['proposal'] == values['proposal']['id']
            and values['candidate']['source_snapshot'] == values['source_snapshot']['id']
            and values['proposal']['repair_budget'] == pins['proposal']['retained_provider_budget'],
            'original creation or provider allowance changed')
    coverage.a3.reference(pins['model']['receipt'])
    require(artifacts.file_hash(pins['compiler']['path']) == pins['compiler']['sha256'], 'compiler changed')


def coverage_cleanup(audit_ref, commit, current, proc=Path('/proc')):
    """Admit terminal ownership of the fixed failed attempt, never its result."""
    read = coverage.a3.reference
    audit = json.loads(read(audit_ref))
    driver = json.loads(read(audit['driver']))
    lane = json.loads(read(audit['lane']))['socket_lane']
    lease = json.loads(read(audit['lease_snapshot']))
    observed = json.loads(read(audit['process_observations']))
    require(re.fullmatch('[a-f0-9]{40}', commit) is not None
            and driver.get('repository_commit') == commit
            and audit.get('id') == driver.get('id') == coverage.RUN_ID
            and audit.get('state') == driver.get('state') == 'failed',
            'coverage prerequisite must preserve the fixed failed attempt')
    began, ended = observer.stamp(driver['started']), observer.stamp(driver['finished'])
    wall = driver.get('host_wall_s')
    require(driver.get('deadline_et') == coverage.DEADLINE.isoformat()
            and artifacts.digest(driver.get('bounds')) == artifacts.digest(coverage.BOUNDS)
            and type(wall) in (int, float) and math.isfinite(wall)
            and 0 <= wall <= coverage.launch_budget(began)
            and began <= ended <= coverage.DEADLINE and abs((ended-began).total_seconds()-wall) <= 1,
            'failed coverage fixed bounds/deadline or elapsed interval differ')
    require(lane.get('host') == 'mbit10' and type(lane.get('node')) is int and lane['node'] == 0
            and lane.get('lease_name') == 'mbit10-evaluation-node0'
            and type(lane.get('lease_generation')) is int and lane['lease_generation'] == 321
            and type(lane.get('exit_code')) is int and lane['exit_code'] == 1
            and read(audit['outer_exit'], 64).strip() == b'1'
            and driver.get('lane') == 'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 321)',
            'failed coverage exits/lane differ')
    require(observer.stamp(lane['started_utc']) <= observer.stamp(driver['started'])
            <= observer.stamp(driver['finished']) < observer.stamp(lane['ended_utc']) + timedelta(seconds=1)
            and observer.stamp(lane['ended_utc']) <= observer.stamp(lease['released_at'])
            <= observer.stamp(audit['observed_at']) <= current
            and lease.get('state') == 'released' and lease['lease']['generation'] == 321
            and lease['lease']['lease_name'] == lane['lease_name'], 'coverage terminal interval/release differs')
    require(observed.get('state') == 'failed' and observed.get('sampling_complete') is False
            and observed.get('cleanup_verified') is False and observed.get('observer_kind') == 'in_process_driver'
            and observed['resource_samples'] == driver['rss']['samples']
            and audit['process_observations'] == driver['process_observations'],
            'failed coverage observations were changed or relabeled')
    samples = [json.loads(line) for line in read(observed['resource_samples'], 16 * 1024**2).splitlines() if line.strip()]
    require(samples and all(isinstance(row.get('processes'), list) and row['processes'] for row in samples),
            'failed coverage observed process samples are missing')
    ancestry = observed['ancestry']
    require(ancestry and observed['driver_identity'] == observed['observer_identity']
            and observed['driver_identity']['pid'] == observed['driver_pid'] == driver['driver_pid']
            and all(observed['driver_identity'][key] == ancestry[0][key] for key in ('pid', 'start_ticks')),
            'coverage driver/observer identity differs')
    rows = ancestry + observed['owned_processes'] + [row for sample in samples for row in sample['processes']]
    expected = {(row['pid'], row['start_ticks']) for row in rows}
    declared = {(row['pid'], row['start_ticks']) for row in audit['owned_processes']}
    require(expected <= declared, 'coverage audit omits observed owned identities')
    pane = observed['launcher_identity']
    require((pane['pid'], pane['start_ticks']) == (3053339, 494729548)
            and pane['pid'] == observed['pane_pid']
            and (pane['pid'], pane['start_ticks']) in {(row['pid'], row['start_ticks']) for row in ancestry}
            and audit.get('cleanup_state') == 'terminal_no_live_owned_processes'
            and audit.get('owned_processes_absent') is False and audit.get('owned_processes_nonrunning') is True,
            'coverage pane/terminal ownership claim differs')
    coverage.a3.verify_terminal_processes(audit['owned_processes'], proc,
                                        launcher_identity=(pane['pid'], pane['start_ticks']))
    return driver


def execute(attempt, pins, env):
    ids = {'proposal': pins['proposal']['id'], 'candidate': pins['candidate']['id'],
           'source_snapshot': pins['source_snapshot']['id'], 'package': pins['proposal']['profile_package'],
           'model': pins['model']['build_evaluation'], 'target': pins['model']['target']}
    values = {key: attempt.stage('before-' + key, public_command('get', rid), BOUNDS['get_seconds'], PUBLIC_ROOT, env=env)
              for key, rid in ids.items()}
    verify_inputs(values, pins)
    attempt.sample(force=True)
    result = attempt.stage('compile', public_command('dx100-compile', REQUEST, '--runs-dir', RAW, '--lane', 0),
                           BOUNDS['api_seconds'], PUBLIC_ROOT, env=env, require_success=False)
    fresh = attempt.stage('after-evaluation', public_command('get', RUN_ID), BOUNDS['get_seconds'], PUBLIC_ROOT, env=env)
    chain = attempt.stage('after-chain', public_command('get', RUN_ID, '--chain'), BOUNDS['get_seconds'], PUBLIC_ROOT, env=env)
    require(artifacts.digest(result) == artifacts.digest(fresh), 'fresh public build result differs')
    require(fresh.get('id') == RUN_ID and fresh.get('candidate') == pins['candidate']['id']
            and fresh.get('outcome', {}).get('state') == 'complete'
            and fresh['outcome']['stage'] == 'candidate_build' and fresh.get('evidence_kind') == 'execution'
            and fresh.get('gain_claim') is False and fresh['build']['adapter'] == 'dx100.complete_call.v2',
            'public result does not establish only the requested actual build')
    require(artifacts.digest(fresh.get('request')) == artifacts.digest(json.loads(REQUEST.read_text()))
            and fresh.get('correctness', {}).get('state') == 'unverified'
            and fresh.get('profiling', {}).get('state') == 'incomplete' and not fresh.get('timing'),
            'public result changes the fixed request or overstates build-only evidence')
    require(fresh['build']['compiler_sha256'] == pins['compiler']['sha256']
            and artifacts.file_hash(fresh['build']['binary']) == fresh['build']['binary_sha256'],
            'compiled binary/compiler evidence changed')
    coverage.a3.reference(fresh['build']['driver'])
    store = Store(PUBLIC_ROOT / 'records')
    require(all(artifacts.digest(store.get(rid)) == artifacts.digest(values[key]) for key, rid in ids.items()),
            'a retained origin record or provider budget changed during build')
    require(chain.get('root') == RUN_ID
            and artifacts.digest(chain.get('records', {}).get(RUN_ID)) == artifacts.digest(fresh)
            and all(artifacts.digest(chain['records'].get(rid)) == artifacts.digest(values[key])
                    for key, rid in ids.items()), 'fresh public chain omits or changes original creation records')
    require(all(row.get('returncode') == 0 for row in attempt.receipt['stages']),
            'a public stage failed despite its result content')
    attempt.receipt.update(state='complete', evaluation_sha256=artifacts.digest(fresh),
                           build= fresh['build'], provider_budget_unchanged=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('expected-commit', 'outer-started', 'outer-deadline', 'coverage-commit', 'coverage-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--coverage-completion', type=Path, required=True)
    for name in ('pane-pid', 'pane-start-ticks'):
        parser.add_argument('--' + name, type=int, required=True)
    args = parser.parse_args()
    clock = Clock(observer.stamp(args.outer_started), observer.stamp(args.outer_deadline))
    require(socket.gethostname().split('.')[0] == 'mbit10', 'T17 build requires mbit10')
    require(not RAW.exists() and not BUILD.exists(), 'fixed T17 output already exists; no retry')
    pane = {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}
    owned = owned_descendants()
    attempt = Attempt(RAW, BUILD, clock, owned, pane)
    error = None
    try:
        attempt.receipt['ancestry'] = observer.ancestry(attempt.receipt['driver_identity'], pane)
        attempt.sample(force=True)
        attempt.receipt['runtime'] = runtime_tree(ROOT, args.expected_commit)
        attempt.receipt['public_runtime'] = runtime_tree(PUBLIC_ROOT, PUBLIC_COMMIT)
        require(subprocess.check_output(['git', 'rev-parse', 'HEAD^'], cwd=PUBLIC_ROOT, text=True, timeout=5).strip()
                == CODE_COMMIT, 'provider checkout code parent differs')
        require(REQUEST.stat().st_size == 551 and artifacts.file_hash(REQUEST) == REQUEST_SHA
                and artifacts.file_hash(OBSERVATION) == OBSERVATION_SHA, 'fixed request/preparation changed')
        pins = json.loads(OBSERVATION.read_text())
        attempt.receipt.update(request=ref(REQUEST), preparation=ref(OBSERVATION),
            rss_basis='linux.proc_pid_stat.field24.v1',
            python={'path': str(Path(sys.executable).absolute()), 'resolved': str(Path(sys.executable).resolve()),
                    'sha256': artifacts.file_hash(Path(sys.executable).resolve()),
                    'version': sys.version})
        store = Store(PUBLIC_ROOT / 'records')
        require(store.get(RUN_ID) is None, 'T17 evaluation already exists; no retry')
        lease = lease_observation(store.get('mbit10', 'machine'), 0)
        require(not lease['leases']['mbit10-evaluation-node1']['kernel_held'], 'other socket must remain idle')
        attempt.receipt.update(lane=lease['verified_lane'], leases=lease, load_average=os.getloadavg())
        def idle_guard():
            value = lease_observation(store.get('mbit10', 'machine'), 0)
            require(value['verified_lane'] == attempt.receipt['lane']
                    and not value['leases']['mbit10-evaluation-node1']['kernel_held'],
                    'own lane changed or other socket became active')
            return value
        attempt.guard = idle_guard
        # This is a failed-run cleanup barrier, not correctness acceptance.
        audit_ref = {'path': str(args.coverage_completion), 'sha256': args.coverage_sha256}
        require(args.coverage_sha256 == COVERAGE_AUDIT_SHA, 'exact failed coverage cleanup audit is required')
        driver = coverage_cleanup(audit_ref, args.coverage_commit, now())
        a3_audit = json.loads(coverage.a3.reference(driver['prerequisites']['a3']['audit']))
        a3_driver = json.loads(coverage.a3.reference(a3_audit['driver']))
        coverage.validate_terminal_cleanup(a3_audit, a3_driver, now())
        for role in ('paired', 'provider'):
            coverage.a3.validate_completion(driver['prerequisites'][role]['audit'], role, now())
        attempt.receipt['coverage_cleanup'] = audit_ref
        model = Path(pins['model']['root'])
        require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=model, text=True, timeout=5).strip()
                == pins['model']['revision'] and subprocess.run(['git', 'diff', '--quiet', 'HEAD'], cwd=model, timeout=5).returncode == 0,
                'model checkout changed')
        env = dict(os.environ)
        removed = ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE',
                   'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH', 'CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH')
        for name in removed:
            env.pop(name, None)
        env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', TMPDIR='/data1/yanruj/tmp', PATH='/usr/bin:/bin')
        require(Path(env['TMPDIR']).is_dir(), 'existing data1 temporary directory is unavailable')
        attempt.receipt['controlled_environment'] = {**dict.fromkeys(removed),
            **{key: env[key] for key in ('PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'TMPDIR', 'PATH')}}
        execute(attempt, pins, env)
        require(runtime_tree(ROOT, args.expected_commit) == attempt.receipt['runtime']
                and runtime_tree(PUBLIC_ROOT, PUBLIC_COMMIT) == attempt.receipt['public_runtime'],
                'runtime source changed during the fixed attempt')
    except BaseException as exc:
        error = exc
    code = attempt.finish(error)
    print(json.dumps({'id': RUN_ID, 'state': attempt.receipt['state'], 'receipt': ref(RAW / 'driver.json')}))
    return code


if __name__ == '__main__':
    with interruption_signals():
        raise SystemExit(main())
