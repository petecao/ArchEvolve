#!/usr/bin/env python3
"""Execute an operator-selected native BFS proposal under an existing frozen policy.

Created: 2026-09-25 (Eastern Time). This bounded driver does not select intent,
workloads, profitability thresholds, or a new protocol. Unfavorable results stay.
Updated: 2026-09-26 (Eastern Time).

The optional --existing-candidate ID route retains --proposal as the exact
original JSON request. It reopens that proposal's first completed candidate
through public get, validates its source/package/diff bindings, and never submits
or invokes a rewrite provider again. Prior repair history is not resumable by this
narrow route; a new build/correctness failure can still use --repair-config under
the proposal's existing repair budget. --provider-config is incompatible with
reuse. Omitting --existing-candidate preserves the fresh-submit behavior.
Reuse reconstructs the retained patch in an owned temporary source directory:
at most 4096 source files / 64 MiB, a 10 MiB patch, and 60 seconds capped by the
remaining campaign deadline. The reconstructed tree is removed on every exit.

--reassessment adds an explicit, immutable-origin four-to-one-thread transition
for --existing-candidate only. Its manifest binds fresh assessment packages and
an already-frozen protocol; provider and repair options are forbidden in this
mode. It never edits or resubmits the original proposal.
"""
import argparse
import copy
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile, profile_package, rewrite, workflow
from swdb.store import Store
from scripts.bfs_process import interruption_signals, finish_legacy_group


# Prospective native supervision only. Legacy callers retain their own semantics.
NATIVE_BOUNDS = {'outer_seconds': 14400, 'work_seconds': 14370, 'cleanup_seconds': 30,
    'sampled_rss_bytes': 16*1024**3, 'artifact_bytes': 16*1024**3, 'build_bytes': 4*1024**3,
    'node_available_bytes': 20*1024**3, 'global_available_bytes': 24*1024**3,
    'raw_reserve_bytes': 30*1024**3, 'build_reserve_bytes': 10*1024**3,
    'sample_interval_seconds': 5, 'sample_gap_seconds': 30}
PYTHON_INPUTS = {**dict.fromkeys(('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE')),
                'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1'}


def require(value, reason):
    if not value: raise ValueError(reason)


def timestamp(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'aware timestamp required')
    return result


def now():
    return datetime.now(ZoneInfo('America/New_York'))


def reference(path):
    path = Path(path)
    return {'path':str(path.absolute()), 'sha256':artifacts.file_hash(path)}


def read_reference(ref, maximum=32*1024**2):
    path = Path(ref['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'unsafe/missing retained reference')
    with path.open('rb') as stream: raw = stream.read(maximum+1)
    require(len(raw) <= maximum and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'retained reference changed')
    return json.loads(raw)


def validate_root_entries(root, commit):
    """Reject ignored or untracked root entries that can shadow Python imports."""
    tracked = subprocess.check_output(['git','ls-tree','--name-only',commit],
                                      cwd=root,text=True,timeout=10).splitlines()
    require(tracked and len(tracked) <= 4096, 'tested root Git inventory is missing or oversized')
    actual = {entry.name for entry in Path(root).iterdir()}
    require(actual <= set(tracked) | {'.git'}, 'tested root contains an untracked import or metadata entry')
    return sorted(actual)


def campaign_runtime(commit, root=ROOT):
    require(isinstance(commit,str) and re.fullmatch('[a-f0-9]{40}',commit), 'prospective code commit required')
    paths = ('scripts','swdb','schemas','vocab','tools/bfs_native','tests','pyproject.toml')
    def git(*args): return subprocess.check_output(['git',*args],cwd=root,timeout=10)
    require(git('rev-parse','HEAD').decode().strip() == commit, 'campaign checkout differs from reviewed commit')
    validate_root_entries(root, commit)
    names = git('ls-tree','-r','--name-only',commit,'--',*paths).decode().splitlines()
    actual = {'pyproject.toml'} | {str(p.relative_to(root)) for folder in paths[:-1]
        for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(names and len(names) <= 4096 and actual == set(names)
            and not git('diff',commit,'--',*paths), 'campaign runtime inventory differs or contains shadow files')
    require(all(not (root/name).is_symlink() for name in names)
            and not any((root/name).exists() for name in ('sitecustomize.py','usercustomize.py')), 'runtime shadow/symlink detected')
    return {'root':str(root),'commit':commit,'files':{name:artifacts.file_hash(root/name) for name in names},
            'python':reference(Path(sys.executable).resolve()),'python_version':sys.version}


def campaign_inputs(args):
    return {'id':args.id,'candidate':args.existing_candidate,'proposal':reference(args.proposal),
        'reassessment':reference(args.reassessment) if getattr(args,'reassessment',None) else None,
        'packages':args.packages,'protocol':args.protocol,'lane':args.lane,'records':str(args.records),
        'runs_dir':str(args.runs_dir),'source_runs_dir':str(args.source_runs_dir),'build_root':str(args.build_root)}


def validate_linux_proof(ref, admission):
    proof = read_reference(ref)
    require(proof.get('format') == 'swdb.bfs.linux-fixture.v1'
            and proof.get('kind') == 'native_campaign_owned_cleanup' and proof.get('host') == 'mbit10'
            and proof.get('platform') == 'linux' and proof.get('evidence_kind') == 'contract_fixture'
            and proof.get('state') == 'passed' and type(proof.get('returncode')) is int and proof['returncode'] == 0
            and proof.get('code_commit') == admission['code_commit']
            and artifacts.digest(proof.get('runtime')) == artifacts.digest(admission['runtime'])
            and timestamp(proof['started']) <= timestamp(proof['finished']) <= timestamp(admission['prepared_at']),
            'exact Linux owned-process fixture proof is required')
    require((timestamp(proof['finished'])-timestamp(proof['started'])).total_seconds()<=90,
            'Linux ownership fixture exceeded its 90-second bound')
    command = proof.get('command',[])
    selector = 'tests/test_bfs_native_execution.py::test_linux_campaign_reaps_detached_child'
    require(isinstance(command,list) and len(command)>3 and command[1:3] == ['-m','pytest']
            and str(Path(command[0]).resolve()) == admission['runtime']['python']['path']
            and selector in command and '--junitxml='+proof['junit']['path'] in command, 'Linux fixture command differs')
    for key, maximum in (('stdout',16*1024**2),('junit',4*1024**2)):
        item = proof[key]; path = Path(item['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'Linux fixture artifact unavailable')
        with path.open('rb') as stream: raw = stream.read(maximum+1)
        require(len(raw)<=maximum and hashlib.sha256(raw).hexdigest()==item['sha256'], 'Linux fixture artifact changed')
        if key == 'junit': cases = ET.fromstring(raw).findall('.//testcase')
    require(cases and all(not any(case.find(k) is not None for k in ('failure','error','skipped')) for case in cases)
            and {'test_linux_campaign_reaps_detached_child[False]','test_linux_campaign_reaps_detached_child[True]'}
                <= {case.get('name') for case in cases}, 'Linux ownership fixtures failed, skipped or omitted')
    return ref


class NativeSupervision:
    """One native clock, resource guard, and owned-tree cleanup allowance."""
    def __init__(self, driver, *, lifecycle=None):
        if lifecycle is None:
            from scripts import bfs_owned_execution as lifecycle
        self.lifecycle, self.driver, self.args = lifecycle, driver, driver.args
        args = self.args
        self.begin, self.end = timestamp(args.outer_started), timestamp(args.outer_deadline)
        entered = now().isoformat()
        current = now()
        require(self.end-self.begin == timedelta(seconds=NATIVE_BOUNDS['outer_seconds'])
                and 0 <= (current-self.begin).total_seconds() <= 5
                and args.total_seconds == NATIVE_BOUNDS['outer_seconds'], 'original four-hour outer clock is required')
        self.deadline = time.monotonic()+(self.end-current).total_seconds()
        self.samples = driver.folder/'owned-resources.jsonl'; self.last = self.begin
        self.machine = None; self.guard = None; self.owner = None
        path = driver.folder/'cleanup-ledger.json'
        binding = lifecycle.SharedCleanup.create(path,self.end.isoformat(),deadline=self.deadline)
        self.budget = lifecycle.SharedCleanup(path,binding,self.deadline)
        self.owner = lifecycle.Owned(self.budget)
        ident = lifecycle.identity(os.getpid()); pane = {'pid':args.pane_pid,'start_ticks':args.pane_start_ticks}
        driver.receipt.update(format='swdb.bfs.native-campaign-driver.v2',started=entered,
            outer_started=self.begin.isoformat(),outer_deadline=self.end.isoformat(),supervision_bounds=copy.deepcopy(NATIVE_BOUNDS),
            cleanup_budget={'path':str(path),'binding':binding,'budget_seconds':30},cleanup_verified=False,
            process_observations={'driver_identity':ident,'pane_identity':pane,'ancestry':lifecycle.ancestry(ident,pane)},
            resource_scope='driver and all observed owned descendants across sessions',hard_memory_quota=False)
        self.guard = lifecycle.Monitor(self.observe)

    def remaining(self, cleanup=False):
        return min(self.deadline-time.monotonic(),(self.end-now()).total_seconds())-(0 if cleanup else 30)

    def check(self, cleanup=False):
        require(self.remaining(cleanup)>0, 'native original shared deadline exhausted')
        if self.guard and self.guard.last_started is not None: self.guard.check()

    def account(self):
        from scripts.bfs_dx100_coverage_execution import artifact_bytes
        total = artifact_bytes([self.args.runs_dir,self.args.source_runs_dir,self.args.build_root])
        total += sum(p.lstat().st_size for p in self.args.records.rglob(self.args.id+'*.yaml'))
        builds = artifact_bytes([self.args.build_root])
        free = {}
        for key,path,minimum in (('raw_free_bytes',self.args.runs_dir,NATIVE_BOUNDS['raw_reserve_bytes']),
                ('build_free_bytes',self.args.source_runs_dir,NATIVE_BOUNDS['build_reserve_bytes']),
                ('build_volume_free_bytes',self.args.build_root,NATIVE_BOUNDS['build_reserve_bytes'])):
            stat = os.statvfs(path); free[key] = stat.f_bavail*stat.f_frsize
            require(free[key]>=minimum,'native free-space reserve exhausted')
        require(total<=NATIVE_BOUNDS['artifact_bytes'] and builds<=NATIVE_BOUNDS['build_bytes'], 'native artifact/build bound exceeded')
        self.check_clock()
        return {'observed_at':now().isoformat(),'artifact_bytes':total,'build_bytes':builds,**free}

    def check_clock(self):
        require(self.remaining(True)>0,'native outer deadline exhausted')

    def observe(self):
        sample = self.owner.sample(); sample['accounting'] = self.account()
        sampled = timestamp(sample['sampled_at'])
        require(0 <= (sampled-self.last).total_seconds() <= 30,'native resource coverage gap exceeded')
        self.last = sampled
        if self.machine is not None:
            sample['lane'] = profile._verified_lane(self.machine,self.args.lane)
        require(sample['rss_bytes']<=NATIVE_BOUNDS['sampled_rss_bytes'],'native sampled RSS exceeds16GiB')
        with self.samples.open('a') as stream: stream.write(json.dumps(sample)+'\n')
        self.driver.receipt['peak_sampled_rss_bytes'] = max(self.driver.receipt.get('peak_sampled_rss_bytes',0),sample['rss_bytes'])
        return sample

    def capacity(self):
        from scripts.dx100_capacity import capacity
        node = int(self.args.lane[-1])
        raw = {'node':Path(f'/sys/devices/system/node/node{node}/meminfo').read_text(),
            'zones':Path('/proc/zoneinfo').read_text(),'global':Path('/proc/meminfo').read_text()}
        value = capacity(raw['node'],raw['zones'],raw['global'],node,os.sysconf('SC_PAGE_SIZE'))
        require(value['estimated_available_kib']*1024>=NATIVE_BOUNDS['node_available_bytes']
                and value['global_available_kib']*1024>=NATIVE_BOUNDS['global_available_bytes'], 'native capacity admission failed')
        return {'observed_at':now().isoformat(),'inputs':raw,'estimate':value,
                'required_node_bytes':NATIVE_BOUNDS['node_available_bytes'],'required_global_bytes':NATIVE_BOUNDS['global_available_bytes']}

    def admit(self):
        self.guard.start()
        ref = {'path':str(self.args.supervision_admission),'sha256':self.args.supervision_sha256}
        value = read_reference(ref); self.driver.receipt['supervision_admission'] = ref
        require(value.get('format')=='swdb.bfs.native-campaign-admission.v1' and value.get('id')==self.args.id
                and value.get('code_commit')==self.args.expected_commit
                and artifacts.digest(value.get('bounds'))==artifacts.digest(NATIVE_BOUNDS)
                and artifacts.digest(value.get('inputs'))==artifacts.digest(campaign_inputs(self.args))
                and timestamp(value['prepared_at'])<=self.begin, 'native admission input/budget identity differs')
        runtime = campaign_runtime(self.args.expected_commit)
        require(artifacts.digest(value.get('runtime'))==artifacts.digest(runtime),'native runtime differs from admission')
        validate_linux_proof(value['linux_proof'],value)
        self.driver.receipt['runtime'] = runtime
        self.machine = Store(self.args.records).get('mbit10','machine')
        profile._verified_lane(self.machine,self.args.lane)
        require(not any(rid==self.args.id or rid.startswith(self.args.id+'.') for rid in Store(self.args.records).by_id),
                'campaign record IDs already exist; no retry')
        self.driver.receipt['capacity_admission'] = self.capacity()
        self.check(); self.driver.save()

    def finalize(self, error=None):
        receipt = self.driver.receipt
        if error is not None: receipt.update(state='failed',reason=f'{type(error).__name__}: {error}')
        failure = None
        try:
            receipt['cleanup'] = self.owner.finish()
            require(receipt['cleanup'].get('state') == 'all_owned_descendants_absent'
                    and not receipt['cleanup'].get('errors'),'native cleanup has observation/signal errors')
        except BaseException as exc: failure=failure or exc
        receipt['process_observations']['owned_processes'] = list(self.owner.history.copy().values())
        if failure is not None: receipt.update(state='failed',cleanup_error=f'{type(failure).__name__}: {failure}')
        try:
            # Keep nominal sampling active through owned teardown. The final
            # stopped-monitor segment is itself limited to one five-second
            # cleanup reservation, including its hashes and durable writes.
            with self.budget.reservation() as until:
                self.guard.stop(until)
                self.guard.observe()
                receipt['process_observations']['owned_processes'] = list(self.owner.history.values())
                receipt['resource_samples'] = reference(self.samples)
                for _ in range(2):
                    receipt['final_accounting'] = self.account()
                    receipt['cleanup_accounting'] = self.budget.snapshot()
                    receipt.update(finished=now().isoformat(),host_wall_s=(now()-self.begin).total_seconds())
                    self.driver.save(); self.account()
                    require(time.monotonic()<=until,'native finalization exceeded its cleanup reservation')
                    require((now()-self.last).total_seconds()<=30,'native final telemetry gap exceeded')
        except BaseException as exc:
            failure=failure or exc
            receipt.update(state='failed',finalization_error=f'{type(exc).__name__}: {exc}')
            receipt['process_observations']['owned_processes'] = list(self.owner.history.copy().values())
            # Never borrow an uncharged emergency write. If the shared ledger
            # is exhausted, the nonzero outer result/terminal audit must reject
            # the last saved state even when its final failure write is absent.
            try:
                with self.budget.reservation(): self.driver.save()
            except BaseException as persist_error:
                receipt['failure_persistence_error'] = f'{type(persist_error).__name__}: {persist_error}'
        if error is not None: raise error from failure
        if failure is not None: raise failure


def validate_inputs(packages, frozen, proposal, get, lane, expected_artifact, *, origin_package=None):
    """Check the exact inputs before any proposal is sent or benchmark is run."""
    if len(packages) != 2 or len({p['id'] for p in packages}) != 2:
        raise ValueError('exactly two distinct baseline packages are required')
    bfs_protocol.verify_immutable(frozen)
    settings = frozen['settings']
    from swdb.bfs_native import validate_runtime_policy
    frozen_runtime = validate_runtime_policy(settings.get('native_runtime'), settings['threads'])
    if settings['mode'] != 'native' or settings['targets']['baseline'] != settings['targets']['candidate']:
        raise ValueError('campaign requires an already-frozen native comparison on one target')
    target = settings['targets']['candidate']
    if target['id'] != 'mbit10' or target['configuration'].get('lane') != lane:
        raise ValueError('frozen target must identify this exact mbit10 lane')
    if settings['roi'] != 'bfs.complete_call.v1':
        raise ValueError('campaign requires the protected native BFS complete-call ROI')
    by_family, identities = {}, set()
    for package in packages:
        profile_package.verify(package)
        if package.get('completeness') != 'complete' or package.get('evidence', {}).get('classification') != 'execution':
            raise ValueError('both baseline packages must contain complete real execution evidence')
        evaluation = get(package['evaluation'])
        candidate = get(package['candidate'])
        source = get(candidate['source_snapshot'])
        workload = get(evaluation['context']['workload']['id'])
        bfs_protocol.verify_immutable(workload)
        if (evaluation['outcome']['state'] != 'complete' or evaluation['correctness']['state'] != 'passed'
                or evaluation['evidence_kind'] != 'execution' or evaluation['request'].get('fixture') is True):
            raise ValueError('baseline package has no real passed primary evaluation')
        primary_runtime = validate_runtime_policy(
            evaluation.get('build', {}).get('native_runtime'), settings['threads'])
        if artifacts.digest(primary_runtime) != artifacts.digest(frozen_runtime):
            raise ValueError('baseline package primary native runtime differs from the frozen assessment')
        expected_context = profile_package._context(evaluation)
        if (package['evidence']['evaluation_sha256'] != artifacts.digest(evaluation)
                or any(artifacts.digest(package['context'].get(key)) != artifacts.digest(value) for key, value in expected_context.items())
                or package['context'].get('primary_binary_sha256') != evaluation.get('build', {}).get('binary_sha256')
                or artifacts.digest(package['context'].get('build')) != artifacts.digest(evaluation.get('build'))
                or evaluation.get('candidate') != candidate['id']):
            raise ValueError('baseline package primary source/context evidence changed')
        implementation = get(package['implementation'])
        if (candidate.get('artifact_role') != 'source_baseline' or candidate.get('proposal')
                or candidate['artifact']['sha256'] != source['artifact']['sha256']
                or candidate['artifact']['sha256'] != expected_artifact['sha256']
                or any(item['implementation'] != implementation['id'] for item in (candidate, source, evaluation))
                or implementation['function'] != 'DOBFS'
                or any(item['context'].get('function') != implementation['function'] for item in (candidate, source))):
            raise ValueError('baseline package must measure the unchanged pinned application source and entry point')
        artifacts.verify(candidate['artifact'])
        if (workload['id'] not in frozen['workload_identities']
                or workload['identity_sha256'] != frozen['workload_identities'][workload['id']]
                or workload['definition']['canonical_sha256'] != evaluation['context']['workload']['canonical_sha256']):
            raise ValueError('baseline workload differs from its frozen canonical graph')
        expected = {'sources': workload['definition']['sources'], 'target': target['id'],
                    'target_configuration': target['configuration'], 'threads': settings['threads'], 'roi': settings['roi']}
        if any(artifacts.digest(package['context'].get(k)) != artifacts.digest(v) for k, v in expected.items()):
            raise ValueError('baseline package sources/target/threads/ROI differ from the frozen assessment')
        family = workload['definition']['family']
        if family in by_family:
            raise ValueError('baseline packages repeat a graph family')
        by_family[family] = {'package': package, 'evaluation': evaluation, 'candidate': candidate, 'workload': workload}
        identities.add((package['implementation'], candidate['artifact']['sha256']))
    if set(by_family) != {'kronecker', 'uniform_random'} or len(identities) != 1:
        raise ValueError('packages must cover both families for the same implementation and exact source')
    if set(settings['workloads']) != {row['workload']['id'] for row in by_family.values()}:
        raise ValueError('protocol workload set must exactly match the two declared package workloads')
    first = packages[0] if origin_package is None else origin_package
    if (proposal.get('message_version') != '1.0' or proposal.get('profile_package') != first['id']
            or proposal.get('source_snapshot') != first['source_snapshot']
            or proposal.get('implementation') != first['implementation']
            or proposal.get('source_sha256') != first['context']['source_sha256']):
        raise ValueError('operator proposal must exactly target the first supplied package and its source')
    if proposal.get('producer', {}).get('test_client') is not True:
        raise ValueError('campaign demonstrations must identify their test-client producer')
    if proposal.get('payload', {}).get('kind') not in {'patch', 'structured_instructions'}:
        raise ValueError('native campaign requires the assigned patch or structured-instructions route')
    expected_route = {'dx100-bfs-scalar': 'patch', 'gapbs-bfs-do': 'structured_instructions'}
    if expected_route.get(first['implementation']) != proposal['payload']['kind']:
        raise ValueError('proposal route does not match this source-specific native campaign')
    return by_family


def reassessment_options(args):
    if getattr(args, 'reassessment', None):
        if not getattr(args, 'existing_candidate', None):
            raise ValueError('--reassessment requires --existing-candidate')
        if args.provider_config or args.repair_config:
            raise ValueError('--reassessment forbids provider and repair configuration')


def validate_reassessment(manifest, proposal, candidate_id, packages, frozen, get, lane, expected_artifact):
    """Bind origin and assessment separately; missing old runtime stays unknown."""
    from swdb.bfs_native import RUNTIME_INHERITED, controlled_environment, validate_runtime_policy

    def require(condition, reason):
        if not condition: raise ValueError('reassessment: ' + reason)

    def same(left, right):
        return artifacts.digest(left) == artifacts.digest(right)

    def shape(value, keys, label):
        require(isinstance(value, dict) and set(value) == set(keys), label + ' has an unsupported shape')

    def binding(reference, record):
        shape(reference, ('id', 'sha256'), 'record reference')
        require(isinstance(reference['id'], str) and isinstance(reference['sha256'], str)
                and re.fullmatch('[0-9a-f]{64}', reference['sha256']) is not None
                and isinstance(record, dict) and record.get('id') == reference['id']
                and artifacts.digest(record) == reference['sha256'], 'record identity or digest differs')

    shape(manifest, ('version', 'kind', 'origin', 'assessment', 'transition'), 'manifest')
    require(type(manifest['version']) is int and manifest['version'] == 1
            and manifest['kind'] == 'native_candidate_reassessment', 'manifest version/kind is unsupported')
    origin, assessment, transition = (manifest[key] for key in ('origin', 'assessment', 'transition'))
    shape(origin, ('proposal', 'candidate', 'profile_package', 'source_snapshot', 'request_sha256', 'baseline_packages'), 'origin')
    shape(assessment, ('protocol', 'packages'), 'assessment')
    shape(transition, ('from_threads', 'to_threads', 'native_runtime'), 'transition')
    require(type(transition['from_threads']) is int and transition['from_threads'] == 4
            and type(transition['to_threads']) is int and transition['to_threads'] == 1,
            'only the explicit requested four-to-one-thread transition is supported')
    require(isinstance(assessment['packages'], list) and len(assessment['packages']) == len(packages) == 2,
            'exactly two ordered assessment packages are required')
    binding(assessment['protocol'], frozen)
    for reference, package in zip(assessment['packages'], packages): binding(reference, package)
    old = {}
    for kind in ('proposal', 'candidate', 'profile_package', 'source_snapshot'):
        reference = origin[kind]
        shape(reference, ('id', 'sha256'), kind + ' reference')
        old[kind] = get(reference['id']); binding(reference, old[kind])
    require(candidate_id == old['candidate']['id'] and old['proposal']['id'] == proposal['id']
            and old['profile_package']['id'] == proposal['profile_package']
            and old['source_snapshot']['id'] == proposal['source_snapshot']
            and origin['request_sha256'] == artifacts.digest(proposal)
            and same(old['proposal'].get('request'), proposal), 'original request or selected candidate changed')
    fresh_runtime = validate_runtime_policy(transition['native_runtime'], 1)
    expected_runtime = {'version': 1, 'environment': {**controlled_environment(1), **dict.fromkeys(RUNTIME_INHERITED)}}
    require(same(fresh_runtime, expected_runtime)
            and same(frozen['settings'].get('native_runtime'), fresh_runtime), 'fresh requested runtime differs')
    rows = validate_inputs(packages, frozen, proposal, get, lane, expected_artifact,
                           origin_package=old['profile_package'])
    source, origin_package = old['source_snapshot'], old['profile_package']
    source_root = artifacts.verify(source['artifact'])
    require(source['artifact']['sha256'] == expected_artifact['sha256']
            and same(source['artifact']['files'], expected_artifact['files']), 'origin source manifest changed')
    artifacts.check_protections(source_root, source['protections'])
    historical, runtime_evidence = {}, {}
    require(isinstance(origin['baseline_packages'], list) and len(origin['baseline_packages']) == 2,
            'both historical baseline packages are required')
    historical_ids = []
    for reference in origin['baseline_packages']:
        shape(reference, ('id', 'sha256'), 'historical package reference')
        package = get(reference['id']); binding(reference, package); profile_package.verify(package)
        historical_ids.append(package['id'])
        require(package.get('completeness') == 'complete'
                and package.get('evidence', {}).get('classification') == 'execution'
                and package.get('implementation') == proposal['implementation'],
                'origin must retain both real complete baseline packages')
        primary = get(package['evaluation'])
        require(primary.get('outcome', {}).get('state') == 'complete'
                and primary.get('correctness', {}).get('state') == 'passed'
                and primary.get('evidence_kind') == 'execution' and primary.get('request', {}).get('fixture') is not True
                and package['evidence']['evaluation_sha256'] == artifacts.digest(primary)
                and type(primary.get('context', {}).get('threads')) is int and primary['context']['threads'] == 4
                and all(same(package['context'].get(key), val) for key, val in profile_package._context(primary).items())
                and same(package['context'].get('build'), primary.get('build')),
                'origin primary/configuration evidence is unavailable or changed')
        baseline = get(primary['candidate'])
        require(primary['candidate'] == package['candidate'] and baseline.get('artifact_role') == 'source_baseline'
                and not baseline.get('proposal') and baseline['artifact']['sha256'] == proposal['source_sha256']
                and same(baseline.get('protections'), source.get('protections')),
                'origin primary did not measure the unchanged protected source')
        controlled = primary['build'].get('execution_environment')
        require(same(controlled, controlled_environment(4)), 'origin lacks its recorded controlled runtime inputs')
        old_runtime = primary['build'].get('native_runtime')
        if 'native_runtime' in primary['build']:
            old_runtime = validate_runtime_policy(old_runtime, 4)
            require(all(same(old_runtime['environment'][key], fresh_runtime['environment'][key])
                        for key in fresh_runtime['environment'] if key != 'OMP_NUM_THREADS'),
                    'recorded origin runtime changed beyond the declared thread transition')
        runtime_evidence[package['id']] = {'controlled': copy.deepcopy(controlled), 'policy': copy.deepcopy(old_runtime),
                                          'unobserved': list(RUNTIME_INHERITED) if old_runtime is None else []}
        wid = primary['context']['workload']['id']
        require(wid not in historical, 'historical baseline packages duplicate a graph')
        historical[wid] = primary
    require(origin_package['id'] in historical_ids and len(set(historical_ids)) == 2,
            'historical baseline set omits the exact original creation package')
    require(set(historical) == {row['workload']['id'] for row in rows.values()}, 'assessment graph set changed')
    selected = {row['id']: row for row in origin_package.get('regions', []) if row.get('id') in proposal['regions']}
    require(set(selected) == set(proposal['regions']), 'origin selected region is unavailable')
    selected = {rid: profile_package._region(row, source_root) for rid, row in selected.items()}
    fresh_sources = []
    build_keys = ('compiler', 'compiler_version', 'flags', 'template_sha256', 'wrapper_sha256', 'binary_sha256')
    semantic_keys = ('id', 'kind', 'path', 'byte_range', 'source_sha256', 'text', 'lines')
    for row in rows.values():
        package, evaluation = row['package'], row['evaluation']
        primary = historical[row['workload']['id']]
        snapshot = get(package['source_snapshot']); fresh_sources.append({'id': snapshot['id'], 'sha256': artifacts.digest(snapshot)})
        require(snapshot.get('implementation') == source.get('implementation') == proposal['implementation']
                and snapshot.get('application') == source.get('application')
                and snapshot.get('revision') == source.get('revision')
                and same(snapshot['artifact']['files'], source['artifact']['files'])
                and snapshot['artifact']['sha256'] == source['artifact']['sha256']
                and same(snapshot.get('protections'), source['protections'])
                and same(row['candidate'].get('protections'), source['protections'])
                and same({k:v for k,v in snapshot.get('context', {}).items() if k != 'code'},
                         {k:v for k,v in source.get('context', {}).items() if k != 'code'}),
                'assessment source/protections/application semantics differ from origin')
        fresh_root = artifacts.verify(snapshot['artifact'])
        artifacts.check_protections(fresh_root, snapshot['protections'])
        require(all(key in primary['build'] and same(evaluation['build'].get(key), primary['build'][key]) for key in build_keys),
                'assessment compiler/build policy differs from origin')
        require(same(evaluation['build'].get('execution_environment'), controlled_environment(1))
                and evaluation['context'].get('function') == primary['context'].get('function') == 'DOBFS',
                'assessment controlled runtime or BFS entry point differs')
        require(all(same(evaluation['context'].get(key), primary['context'].get(key)) for key in ('sources','roi','target','backend_configuration')),
                'assessment sources/ROI/target differ from origin')
        require(all(key in primary['context']['workload'] and same(evaluation['context']['workload'].get(key), primary['context']['workload'][key])
                    for key in ('canonical_sha256','adjacency_order_sha256','canonical_file_sha256')),
                'origin graph identity differs from assessment')
        regions = {region['id']: region for region in package.get('regions', [])}
        for rid, region in selected.items():
            require(rid in regions, 'selected region is unavailable in fresh assessment package')
            fresh = profile_package._region(regions[rid], fresh_root)
            require(all(same(fresh.get(key), region.get(key)) for key in semantic_keys),
                    'selected region source semantics differ in fresh assessment')
    return rows, {'manifest_sha256': artifacts.digest(manifest), 'origin': copy.deepcopy(origin),
        'assessment': copy.deepcopy(assessment), 'assessment_sources': fresh_sources,
        'origin_runtime_evidence': runtime_evidence, 'transition': copy.deepcopy(transition),
        'original_constraints_sha256': artifacts.digest(proposal['constraints']),
        'original_payload_sha256': artifacts.digest(proposal['payload']),
        'required_operations_sha256': artifacts.digest(proposal.get('required_operations', [])),
        'provider_calls': False, 'repair_calls': False, 'gain_claim': False}


def validate_existing_candidate(request, submitted, candidate, source, package, replay):
    """Revalidate retained creation bindings; this makes no measurement claim."""
    def require(condition, reason):
        if not condition:
            raise ValueError('existing candidate: ' + reason)

    require(workflow._request_error(request) is None, 'original proposal request is invalid')
    require(submitted.get('kind') == 'proposal' and submitted.get('id') == request['id']
            and artifacts.digest(submitted.get('request')) == artifacts.digest(request)
            and submitted.get('payload_sha256') == artifacts.digest(request['payload'])
            and submitted.get('producer') == request['producer'], 'proposal/request identity differs')
    require(submitted.get('outcome') == {'state': 'candidate_created', 'stage': 'rewriting', 'reason': None},
            'proposal is not at its completed initial rewrite')
    attempts = submitted.get('attempts', [])
    require(len(attempts) == 1 and attempts[0].get('number') == 1
            and attempts[0].get('stage') == 'rewriting' and attempts[0].get('state') == 'completed'
            and attempts[0].get('candidate') == candidate.get('id')
            and not any(key in attempts[0] for key in ('parent_candidate', 'trigger_evaluation')),
            'prior or incomplete repair/rewrite history cannot be resumed')
    budget = submitted.get('repair_budget')
    require(budget is None or (isinstance(budget, dict) and type(budget.get('repairs')) is int and budget['repairs'] == 0),
            'a consumed repair budget cannot be reset by reuse')
    require(candidate.get('kind') == 'candidate' and candidate.get('id') == request['id'] + '.candidate-1'
            and submitted.get('candidate') == candidate['id'] and candidate.get('proposal') == submitted['id']
            and candidate.get('parent_candidate') is None and candidate.get('state') == 'unverified'
            and candidate.get('producer') == request['producer'], 'candidate is not the exact original rewrite result')
    profile_package.verify(package)
    require(package.get('kind') == 'profile_package' and package.get('id') == request['profile_package']
            and submitted.get('profile_package') == package['id']
            and source.get('kind') == 'source_snapshot' and source.get('id') == request['source_snapshot']
            and all(row.get('source_snapshot') == source['id'] for row in (submitted, candidate, package))
            and all(row.get('implementation') == request['implementation'] for row in (candidate, source, package))
            and source.get('artifact', {}).get('sha256') == request['source_sha256']
            and package.get('context', {}).get('source_sha256') == request['source_sha256']
            and set(request['regions']) <= {row.get('id') for row in package.get('regions', [])},
            'source/profile/implementation/region bindings differ')
    require(candidate.get('context') == source.get('context')
            and candidate.get('protections') == source.get('protections'), 'candidate source context or protections differ')
    source_path = artifacts.verify(source['artifact'])
    candidate_path = artifacts.verify(candidate['artifact'])
    require(candidate['artifact']['sha256'] != source['artifact']['sha256'], 'candidate contains no source change')
    artifacts.check_protections(source_path, source['protections'])
    artifacts.check_protections(candidate_path, source['protections'])
    diff = Path(candidate.get('diff', ''))
    require(diff.is_absolute() and diff.is_file() and not diff.is_symlink()
            and diff.stat().st_size <= 10 * 1024**2
            and artifacts.file_hash(diff) == candidate.get('diff_sha256'), 'candidate diff is unavailable or changed')
    patch = request['payload']['content']
    if request['payload']['kind'] == 'patch':
        require(budget is None and 'provider' not in submitted and 'provider' not in attempts[0],
                'initial supplied patch unexpectedly contains provider or repair state')
    else:
        provider = submitted.get('provider', {})
        observed = attempts[0].get('provider', {})
        require(submitted.get('provider', {}).get('kind') == 'claude'
                and observed.get('classification') == 'rewrite_provider'
                and observed.get('state') == 'completed' and type(observed.get('returncode')) is int
                and observed['returncode'] == 0 and observed.get('provider') == provider,
                'interpreted reuse lacks a completed real rewrite provider receipt')
        require(isinstance(budget, dict) and set(budget) == {'max_repairs', 'total_seconds', 'used_seconds', 'repairs'}
                and type(budget.get('max_repairs')) is int and 0 <= budget['max_repairs'] <= 5
                and type(budget.get('total_seconds')) is int and 1 <= budget['total_seconds'] <= 3600
                and type(budget.get('used_seconds')) in (int, float) and math.isfinite(budget['used_seconds'])
                and 0 <= budget['used_seconds'] <= budget['total_seconds']
                and all(budget[key] == provider.get(key) for key in ('max_repairs', 'total_seconds'))
                and budget['used_seconds'] == observed.get('host_wall_s'),
                'retained provider time/repair allowance is missing or inconsistent')
        interpretation = submitted.get('interpretation', {})
        require(not interpretation.get('unresolved') and bool(interpretation.get('interpretation')), 'interpretation is unresolved')
        patch = interpretation.get('patch')
    require(isinstance(patch, str) and patch.strip() and diff.read_text() == patch,
            'candidate diff differs from the exact retained patch/interpretation')
    binding = replay(request, source, candidate, patch)
    return {'mode': 'existing_candidate', 'proposal': submitted['id'], 'proposal_sha256': artifacts.digest(submitted),
            'candidate': candidate['id'], 'candidate_sha256': artifacts.digest(candidate),
            'candidate_artifact_sha256': candidate['artifact']['sha256'],
            'source_snapshot': source['id'], 'source_snapshot_sha256': artifacts.digest(source),
            'profile_package': package['id'], 'profile_package_sha256': artifacts.digest(package),
            'diff': {'path': str(diff), 'sha256': candidate['diff_sha256']},
            'repair_budget': budget, 'patch_binding': binding, 'gain_claim': False}


class Driver:
    def __init__(self, args):
        self.args = args
        self.started = time.monotonic()
        self.supervision = None
        self.folder = args.runs_dir / (args.id + '.driver')
        self.folder.mkdir(exist_ok=False)
        self.database = self.folder / 'swdb.sqlite'
        self.receipt = {'id': args.id, 'state': 'running', 'protocol': args.protocol,
                        'database': str(self.database),
                        'stages': [], 'families': {}, 'candidate_rounds': [], 'repair_attempts': [],
                        'gain_claim': False, 'acceptance': 'reported separately by bfs-coverage',
                        'lane': args.lane, 'bounds': {'driver_seconds': args.total_seconds,
                        'evaluation_seconds': 1200, 'profile_seconds': 1200, 'max_repairs': int(bool(args.repair_config))}}
        self.save()

    def save(self):
        pending = self.folder / 'driver.pending.json'
        pending.write_text(json.dumps(self.receipt, indent=2, allow_nan=False))
        pending.replace(self.folder / 'driver.json')

    def call(self, command, *rest, timeout=180, required=True):
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest), '--records', str(self.args.records),
                '--db', str(self.database), '--format', 'json']
        return self.execute(command, argv, timeout=timeout, required=required)

    def execute(self, command, argv, *, timeout=180, required=True):
        args = self.args
        profile._verified_lane(Store(args.records).get('mbit10', 'machine'), args.lane)
        remaining = args.total_seconds - (time.monotonic() - self.started)
        if remaining <= 0:
            raise TimeoutError('native campaign total wall budget exhausted')
        supervised = self.supervision
        if supervised:
            supervised.check()
            remaining = supervised.remaining()
            require(remaining >= timeout, 'native campaign lacks the full next stage allowance')
        for path, reserve in ((args.runs_dir, 30), (args.source_runs_dir, 10)):
            stat = os.statvfs(path)
            if stat.f_bavail * stat.f_frsize < reserve * 1024**3:
                raise RuntimeError(f'{path} free-space reserve is below {reserve} GiB')
        index = len(self.receipt['stages'])
        output, error = self.folder / f'{index:03}-{command}.json', self.folder / f'{index:03}-{command}.stderr'
        entry = {'command': argv, 'state': 'running', 'started':now().isoformat(),
                 'stdout': str(output), 'stderr': str(error)}
        if supervised and command in {'evaluate','evaluate-pair','bfs-profile'}:
            entry['capacity'] = supervised.capacity()
        self.receipt['stages'].append(entry)
        self.save()
        before = time.monotonic()
        child = direct = original_error = cleanup_error = None
        deadline = supervised.deadline if supervised else self.started+args.total_seconds
        until = min(before+timeout, deadline-(30 if supervised else 0))
        env = None
        if supervised:
            env = dict(os.environ)
            for key,value in PYTHON_INPUTS.items():
                if value is None: env.pop(key,None)
                else: env[key]=value
        try:
            with output.open('w') as stdout, error.open('w') as stderr:
                child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                if supervised:
                    direct = supervised.lifecycle.identity(child.pid)
                    supervised.owner.remember(direct); entry['identity']=direct; self.save()
                while child.poll() is None:
                    if supervised: supervised.check()
                    allowance=until-time.monotonic()
                    if allowance<=0: raise subprocess.TimeoutExpired(argv,min(timeout,remaining))
                    try: child.wait(timeout=min(.25,allowance) if supervised else allowance)
                    except subprocess.TimeoutExpired:
                        if not supervised: raise
                require(time.monotonic()<=until,'native public stage exceeded its work deadline')
            entry.update(state='complete' if child.returncode == 0 else 'failed')
        except BaseException as exc:
            original_error=exc
            entry.update(state='interrupted_or_timeout' if isinstance(exc,(TimeoutError,InterruptedError,subprocess.TimeoutExpired))
                         else 'failed',reason=f'{type(exc).__name__}: {exc}')
        finally:
            entry.update(work_finished=now().isoformat(),work_wall_s=time.monotonic()-before)
            try:
                if supervised:
                    entry['cleanup']=supervised.owner.finish(child,direct)
                    require(entry['cleanup'].get('state') == 'all_owned_descendants_absent'
                            and not entry['cleanup'].get('errors'),'owned cleanup had observation/signaling errors')
                else: finish_legacy_group(child,deadline)
            except BaseException as exc:
                cleanup_error=exc;entry.update(state='failed',cleanup_error=f'{type(exc).__name__}: {exc}')
            def persist():
                entry.update(returncode=child.returncode if child is not None else None,finished=now().isoformat(),
                         host_wall_s=time.monotonic() - before,
                         stdout_sha256=artifacts.file_hash(output) if output.is_file() else None,
                         stderr_sha256=artifacts.file_hash(error) if error.is_file() else None)
                self.save()
                if supervised: supervised.account()
                if time.monotonic()>deadline: raise TimeoutError('native final hashing/persistence exceeded total budget')
            try:
                if supervised:
                    with supervised.budget.reservation(): persist()
                else: persist()
            except BaseException as exc:
                cleanup_error=cleanup_error or exc
                entry.update(state='failed',finalization_error=f'{type(exc).__name__}: {exc}')
                try:
                    if supervised:
                        with supervised.budget.reservation(): self.save()
                    else: self.save()
                except BaseException as persist_error:
                    entry['failure_persistence_error']=f'{type(persist_error).__name__}: {persist_error}'
        if original_error is not None: raise original_error from cleanup_error
        if cleanup_error is not None: raise cleanup_error
        try:
            with output.open('rb') as stream: raw=stream.read(32*1024**2+1)
            require(len(raw)<=32*1024**2,'native public JSON output exceeds 32 MiB')
            result = json.loads(raw)
        except (ValueError, OSError): result = None
        if supervised: supervised.check()
        elif time.monotonic()>deadline: raise TimeoutError('native result read exceeded total budget')
        if required and (child.returncode != 0 or not isinstance(result, dict)):
            raise RuntimeError(f'{command} failed; inspect retained {output} and {error}')
        return result

    def request(self, command, value, *rest, **kwargs):
        path = self.retain_request(value)
        return self.call(command, path, *rest, **kwargs)

    def retain_request(self, value):
        if not isinstance(value.get('id'), str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', value['id']):
            raise ValueError('request ID must use record identifier syntax')
        path = self.folder / (value['id'] + '.request.json')
        if path.exists(): raise ValueError('driver request ID would overwrite retained evidence')
        path.write_text(json.dumps(value, indent=2, allow_nan=False))
        return path

    def replay_candidate(self, request, source, candidate, patch):
        """Bind source+authorized edits to the artifact under the caller's deadline."""
        files = source['artifact']['files']
        if len(files) > 4096 or sum(row['bytes'] for row in files) > 64 * 1024**2:
            raise ValueError('existing candidate replay exceeds the 4096-file/64-MiB source bound')
        proof = {'id': request['id'] + '.candidate-binding', 'source': source['artifact'], 'patch': patch,
                 'editable_files': request['constraints']['editable_files'], 'protections': source['protections']}
        path = self.retain_request(proof)
        script = ('import json,sys; from pathlib import Path; from swdb import artifacts,workflow; '
                  'data=json.loads(Path(sys.argv[1]).read_text()); '
                  'result=workflow.apply_patch(artifacts.verify(data["source"]),Path(sys.argv[2]),'
                  'data["patch"],data["editable_files"],data["protections"]); print(json.dumps(result))')
        with tempfile.TemporaryDirectory(prefix=self.args.id + '.candidate-binding-', dir=self.args.source_runs_dir) as scratch:
            result = self.execute('candidate-binding', [sys.executable, '-c', script, str(path), str(Path(scratch) / 'source')], timeout=60)
            if (result.get('sha256') != candidate['artifact']['sha256']
                    or result.get('files') != candidate['artifact']['files']):
                raise ValueError('existing candidate bytes differ from replaying the exact authorized patch on its source')
            artifacts.verify(candidate['artifact'])
        return {'source_sha256': source['artifact']['sha256'], 'candidate_sha256': result['sha256'],
                'request': {'path': str(path), 'sha256': artifacts.file_hash(path)},
                'result': {'path': self.receipt['stages'][-1]['stdout'], 'sha256': self.receipt['stages'][-1]['stdout_sha256']},
                'temporary_source_retained': False}

    def acquire_candidate(self, proposal):
        reassessment_options(self.args)
        existing = getattr(self.args, 'existing_candidate', None)
        if not existing:
            extra = ['--provider-config', self.args.provider_config] if self.args.provider_config else []
            return self.request('submit', proposal, '--runs-dir', self.args.source_runs_dir, *extra,
                                timeout=1000, required=False)
        if self.args.provider_config:
            raise ValueError('--provider-config cannot accompany --existing-candidate; reuse never invokes a provider')
        path = self.retain_request(proposal)
        submitted = self.call('get', proposal['id'])
        candidate = self.call('get', existing)
        if candidate.get('id') != existing:
            raise ValueError('public get returned another existing candidate identity')
        source = self.call('get', proposal['source_snapshot'])
        package = self.call('get', proposal['profile_package'])
        reuse = validate_existing_candidate(proposal, submitted, candidate, source, package, self.replay_candidate)
        reason = workflow.check_capabilities(proposal, Store(self.args.records))
        if reason:
            raise ValueError('existing candidate capability requirements are unresolved: ' + reason)
        chain = self.call('get', proposal['id'], '--chain')
        if (chain.get('root') != proposal['id'] or any(artifacts.digest(chain.get('records', {}).get(row['id'])) != artifacts.digest(row)
                for row in (submitted, candidate, source, package))):
            raise ValueError('existing candidate changed during public chain retrieval')
        reuse['request'] = {'path': str(path), 'sha256': artifacts.file_hash(path)}
        self.receipt['candidate_acquisition'] = reuse
        self.save()
        return submitted

    def evaluation_request(self, name, candidate, workload, frozen, role):
        settings = frozen['settings']
        request = {'message_version': '1.0', 'id': name, 'candidate': candidate, 'machine': 'mbit10',
            'protocol': frozen['id'], 'protocol_role': role, 'threads': settings['threads'],
            'repetitions': settings['sampling']['repetitions'], 'sources': workload['definition']['sources'],
            'roi': settings['roi'], 'target_configuration': settings['targets'][role]['configuration'],
            'workload': {'id': workload['id']}, 'comparison_baseline': self.receipt['implementation'],
            'build': {key: settings['builds'][role][key] for key in ('compiler', 'flags')},
            'budget': {'build_seconds': 180, 'run_seconds': 60, 'total_seconds': 1200}}
        if getattr(self,'supervision',None): request['build_directory']=str(self.args.build_root/name)
        return request

    def evaluate(self, name, candidate, workload, frozen, role):
        return self.request('evaluate', self.evaluation_request(name, candidate, workload, frozen, role),
                            '--runs-dir', self.args.runs_dir, '--lane', self.args.lane,
                            timeout=1260, required=False)

    def evaluate_pair(self, prefix, baseline, candidate, workload, frozen):
        request = {'message_version': '1.0', 'id': prefix + '.pair',
            'collection': frozen['settings']['sampling']['collection'], 'budget': {'total_seconds': 2400}}
        for role, artifact in (('baseline', baseline), ('candidate', candidate)):
            name = prefix + ('.baseline.evaluation' if role == 'baseline' else '.evaluation')
            request[role] = self.evaluation_request(name, artifact, workload, frozen, role)
            request[role]['budget']['total_seconds'] = 2400
        pair = self.request('evaluate-pair', request, '--runs-dir', self.args.runs_dir, '--lane', self.args.lane,
                            timeout=2460, required=False)
        values = {role: (self.call('get', pair[role + '_evaluation'], required=False)
                        if pair and pair.get(role + '_evaluation') else None) for role in ('baseline', 'candidate')}
        return pair, values['baseline'], values['candidate']

    def collect(self, prefix, evaluation, baseline_profile, repetitions=1):
        if not evaluation or evaluation.get('outcome', {}).get('state') != 'complete': return None
        request = {'message_version': '1.0', 'id': prefix + '.profile',
            'evaluation': evaluation['id'], 'memory': True, 'correspondence': baseline_profile, 'repetitions': repetitions,
            'budget': {'discovery_seconds': 120, 'build_seconds': 180, 'run_seconds': 600, 'total_seconds': 1200}}
        if getattr(self,'supervision',None): request['build_directory']=str(self.args.build_root/request['id'])
        observed = self.request('bfs-profile', request,
            '--runs-dir', self.args.runs_dir, '--lane', self.args.lane, timeout=1260, required=False)
        if not observed or not observed.get('id'): return None
        package = self.request('profile-package', {'message_version': '1.0', 'id': prefix + '.package',
            'implementation': evaluation['implementation'], 'evaluation': evaluation['id'], 'region_profile': observed['id'],
            'context': profile_package._context(evaluation)}, required=False)
        if package and package.get('id'):
            self.call('profile-strategies', package['id'], required=False)
            self.call('get', package['id'], '--chain', required=False)
        return package

    def run(self):
        args = self.args
        reassessment_options(args)
        frozen = self.call('get', args.protocol)
        packages = [self.call('get', rid) for rid in args.packages]
        proposal = json.loads(args.proposal.read_text())
        bfs_protocol._validate_settings(frozen['settings'], Store(args.records))
        paired = frozen['settings']['sampling'].get('collection') is not None
        self.receipt.setdefault('bounds', {})['evaluation_seconds'] = 2400 if paired else 1200
        if paired:
            self.receipt['bounds']['pair_seconds'] = 2400
        implementation = self.call('get', packages[0]['implementation'])
        expected_artifact = artifacts.identify(artifacts.source_root(Store(args.records), implementation))
        if getattr(args, 'reassessment', None):
            if not args.reassessment.is_file() or args.reassessment.stat().st_size > 1024**2:
                raise ValueError('reassessment manifest is missing or exceeds 1 MiB')
            raw = args.reassessment.read_bytes()
            manifest = json.loads(raw)
            rows, transition = validate_reassessment(manifest, proposal, args.existing_candidate,
                packages, frozen, lambda rid: self.call('get', rid), args.lane, expected_artifact)
            retained = self.folder / 'reassessment.json'
            with retained.open('xb') as stream: stream.write(raw)
            transition['manifest'] = {'path': str(retained), 'sha256': artifacts.file_hash(retained)}
            self.receipt['reassessment'] = transition
        else:
            rows = validate_inputs(packages, frozen, proposal, lambda rid: self.call('get', rid), args.lane, expected_artifact)
        if getattr(args, 'existing_candidate', None) and args.provider_config:
            raise ValueError('--provider-config cannot accompany --existing-candidate; reuse never invokes a provider')
        if (proposal['payload']['kind'] == 'structured_instructions' and not args.provider_config
                and not getattr(args, 'existing_candidate', None)):
            raise ValueError('interpreted proposal requires operator-supplied --provider-config')
        for file in (args.provider_config, args.repair_config):
            if file:
                config = rewrite.configuration(file)
                if config['kind'] != 'claude': raise ValueError('real campaign cannot use an external fixture provider')
        self.receipt.update(implementation=proposal['implementation'], proposal=proposal['id'],
            proposal_sha256=artifacts.digest(proposal), protocol_sha256=frozen['identity_sha256'],
            inputs=[{'id': package['id'], 'sha256': artifacts.digest(package)} for package in packages],
            repository_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
        self.save()
        submitted = self.acquire_candidate(proposal)
        if getattr(args, 'reassessment', None):
            origin = manifest['origin']
            acquisition = self.receipt['candidate_acquisition']
            for kind in ('proposal', 'candidate', 'profile_package', 'source_snapshot'):
                if (acquisition[kind] != origin[kind]['id']
                        or acquisition[kind+'_sha256'] != origin[kind]['sha256']):
                    raise ValueError('reassessment origin changed during exact candidate acquisition')
            self.receipt['reassessment']['repair_budget_preserved'] = copy.deepcopy(acquisition['repair_budget'])
            self.save()
        if not submitted or submitted.get('outcome', {}).get('state') != 'candidate_created':
            self.receipt.update(state='proposal_non_success', proposal_outcome=(submitted or {}).get('outcome'))
            return
        candidate = submitted['candidate']
        regional = [pair for pair in frozen['settings'].get('region_pairs', [])
                    if pair.get('evidence') == 'native_diagnostic_profile.v1']
        diagnostic_repetitions = regional[0]['diagnostic_repetitions'] if regional else 1
        baselines, baseline_packages = {}, {}
        for family, row in ([] if paired else rows.items()):
            prefix = args.id + '.' + family.replace('_', '-')
            baseline = self.evaluate(prefix + '.baseline', row['candidate']['id'], row['workload'], frozen, 'baseline')
            baselines[family] = baseline
            baseline_packages[family] = (self.collect(prefix + '.baseline', baseline,
                row['package']['region_profile'], diagnostic_repetitions) if regional else None)
            self.receipt['families'][family] = {'workload': row['workload']['id'], 'baseline': baseline and baseline['id'],
                                               'baseline_package': (baseline_packages[family] or {}).get('id'),
                                               'baseline_outcome': (baseline or {}).get('outcome')}
            self.save()
        for round_number in (1, 2):
            current = {'number': round_number, 'candidate': candidate, 'families': {}}
            self.receipt['candidate_rounds'].append(current)
            self.save()
            repairable = []
            for family, row in rows.items():
                prefix = args.id + '.' + family.replace('_', '-') + f'.candidate-{round_number}'
                pair = None
                if paired:
                    pair, baseline, evaluation = self.evaluate_pair(prefix, row['candidate']['id'], candidate, row['workload'], frozen)
                    baselines[family] = baseline
                    baseline_packages[family] = (self.collect(prefix + '.baseline', baseline,
                        row['package']['region_profile'], diagnostic_repetitions) if regional else None)
                    self.receipt['families'][family] = {'workload': row['workload']['id'],
                        'baseline': baseline and baseline['id'], 'pair': pair and pair['id'],
                        'baseline_package': (baseline_packages[family] or {}).get('id'),
                        'baseline_outcome': (baseline or {}).get('outcome')}
                else:
                    evaluation = self.evaluate(prefix + '.evaluation', candidate, row['workload'], frozen, 'candidate')
                package = self.collect(prefix, evaluation, row['package']['region_profile'], diagnostic_repetitions)
                baseline = baselines[family]
                comparison = None
                if evaluation and baseline:
                    regional_evidence = ({'region_packages': {baseline['id']: (baseline_packages[family] or {}).get('id'),
                        evaluation['id']: (package or {}).get('id')}} if regional else {})
                    comparison = self.request('compare-evaluations', {'message_version': '1.0', 'id': prefix + '.comparison',
                        'protocol': frozen['id'], 'baseline_evaluation': baseline['id'], 'candidate_evaluation': evaluation['id'],
                        'comparison_baseline': proposal['implementation'], **regional_evidence}, required=False)
                current['families'][family] = {'evaluation': evaluation and evaluation['id'],
                    'baseline_evaluation': baseline and baseline['id'], 'pair': pair and pair['id'],
                    'outcome': (evaluation or {}).get('outcome'), 'profile_package': package and package['id'],
                    'package_completeness': (package or {}).get('completeness'),
                    'comparison': comparison and comparison['id'], 'decision': (comparison or {}).get('decision')}
                if evaluation:
                    self.call('get', evaluation['id'], '--chain', required=False)
                    if ((evaluation['outcome']['state'] == 'failed' and evaluation['outcome']['stage'] == 'build')
                            or evaluation['correctness']['state'] == 'failed'):
                        repairable.append(evaluation['id'])
                self.save()
            if getattr(args, 'reassessment', None) or not repairable or not args.repair_config or round_number == 2: break
            repaired = self.call('repair', repairable[0], '--runs-dir', args.source_runs_dir,
                                 '--provider-config', args.repair_config, timeout=1000, required=False)
            self.receipt['repair_attempts'].append({'trigger': repairable[0], 'outcome': (repaired or {}).get('outcome'),
                                                   'candidate': (repaired or {}).get('candidate')})
            self.save()
            if not repaired or repaired.get('outcome', {}).get('state') != 'candidate_created': break
            candidate = repaired['candidate']
        final = self.receipt['candidate_rounds'][-1]
        compatible = {'gain', 'regression', 'no_gain', 'inconclusive'}
        complete = all((row.get('outcome') or {}).get('state') == 'complete'
                       and row.get('package_completeness') == 'complete'
                       and (row.get('decision') or {}).get('state') in compatible for row in final['families'].values())
        self.receipt.update(state='evaluated' if complete else 'incomplete', final_candidate=candidate)
        self.call('get', proposal['id'], '--chain', required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--packages', nargs=2, required=True, help='two fresh assessment baseline packages; without reassessment the proposal targets the first')
    parser.add_argument('--protocol', required=True)
    parser.add_argument('--proposal', type=Path, required=True, help='operator-authored JSON request; intent is never synthesized by this driver')
    parser.add_argument('--existing-candidate', help='reuse this exact initial candidate of the retained --proposal request; no submit or provider rerun')
    parser.add_argument('--reassessment', type=Path, help='explicit origin/fresh-assessment manifest; existing candidate only, no providers or repairs')
    parser.add_argument('--provider-config', type=Path)
    parser.add_argument('--repair-config', type=Path, help='optional provider configuration authorizing at most one build/correctness repair')
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--source-runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--lane', choices=['mbit10-evaluation-node0', 'mbit10-evaluation-node1'], required=True)
    parser.add_argument('--total-seconds', type=int, default=14400)
    parser.add_argument('--supervision-admission',type=Path)
    parser.add_argument('--supervision-sha256')
    parser.add_argument('--expected-commit')
    parser.add_argument('--outer-started')
    parser.add_argument('--outer-deadline')
    parser.add_argument('--pane-pid',type=int)
    parser.add_argument('--pane-start-ticks',type=int)
    parser.add_argument('--build-root',type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id): parser.error('id must use record identifier syntax')
    if args.existing_candidate and not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.existing_candidate):
        parser.error('existing-candidate must use record identifier syntax')
    if args.existing_candidate and args.provider_config:
        parser.error('--provider-config cannot accompany --existing-candidate')
    try: reassessment_options(args)
    except ValueError as exc: parser.error(str(exc))
    if not 1 <= args.total_seconds <= 14400: parser.error('total-seconds must be in [1,14400]')
    supervision = bool(args.supervision_admission)
    required_supervision = ('supervision_admission','supervision_sha256','expected_commit','outer_started',
                            'outer_deadline','pane_pid','pane_start_ticks','build_root')
    if any(getattr(args,key) is not None for key in required_supervision) and not all(
            getattr(args,key) is not None for key in required_supervision):
        parser.error('prospective supervision requires admission/hash/code/outer clock/pane/build root together')
    if args.existing_candidate and not supervision:
        parser.error('actual existing-candidate campaigns require prospective owned supervision')
    for key in ('records', 'proposal', 'provider_config', 'repair_config', 'reassessment','supervision_admission'):
        if getattr(args, key) is not None: setattr(args, key, getattr(args, key).resolve())
    if socket.gethostname().split('.')[0] != 'mbit10': parser.error('native campaign requires mbit10')
    if supervision:
        for path in (args.runs_dir,args.source_runs_dir,args.build_root):
            if path.exists() or not path.is_absolute() or path != path.resolve():
                parser.error('supervised raw/source/build roots must be distinct new absolute paths')
        roots=(args.runs_dir,args.source_runs_dir,args.build_root)
        if any(a==b or a in b.parents or b in a.parents for i,a in enumerate(roots) for b in roots[i+1:]):
            parser.error('supervised output roots must be disjoint')
        if not args.build_root.is_relative_to('/data1/yanruj'):
            parser.error('supervised build root must use /data1/yanruj')
        args.build_root = artifacts.external_directory(args.build_root)
    args.runs_dir = artifacts.external_directory(args.runs_dir)
    args.source_runs_dir = artifacts.external_directory(args.source_runs_dir)
    if not args.source_runs_dir.is_relative_to('/data1/yanruj'):
        parser.error('source/provider artifacts must use /data1/yanruj')
    if not any(args.runs_dir.is_relative_to(base) for base in ('/data1/yanruj', '/data/yanruj')):
        parser.error('raw outputs must use an authorized host volume')
    if args.runs_dir.is_relative_to(args.source_runs_dir) or args.source_runs_dir.is_relative_to(args.runs_dir):
        parser.error('raw and source/provider artifact trees must be disjoint')
    if not supervision: profile._verified_lane(Store(args.records).get('mbit10', 'machine'), args.lane)
    driver = Driver(args)
    with interruption_signals():
        error = None
        try:
            if supervision:
                driver.supervision = NativeSupervision(driver)
                driver.supervision.admit()
            driver.run()
            if driver.supervision:
                require(artifacts.digest(campaign_runtime(args.expected_commit))==artifacts.digest(driver.receipt['runtime']),
                        'native runtime changed during the campaign')
                driver.supervision.check()
        except BaseException as exc:
            error = exc
            driver.receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        finally:
            if driver.supervision:
                driver.supervision.finalize(error)
            else:
                driver.receipt['host_wall_s'] = time.monotonic() - driver.started
                driver.save()
                if time.monotonic()-driver.started>args.total_seconds:
                    error = error or TimeoutError('native final persistence exceeded total budget')
                    driver.receipt.update(state='failed',reason=str(error));driver.save()
                if error is not None: raise error
                print(json.dumps(driver.receipt, indent=2))
    return 0 if driver.receipt['state'] == 'evaluated' else 1


if __name__ == '__main__':
    raise SystemExit(main())
