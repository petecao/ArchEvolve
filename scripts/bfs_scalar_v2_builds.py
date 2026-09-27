#!/usr/bin/env python3
"""Four fixed unchanged scalar v2 compilations. Interface v1, 2026-09-26 ET.

Preparation only until a reviewed admission is supplied in a free owned lane.
One original 1200-second clock; public compile API only, no guest/provider/retry.
"""
import argparse
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import threading
import time
import xml.etree.ElementTree as XML

if __name__ == '__main__' and any(key in os.environ for key in ('LD_PRELOAD','LD_LIBRARY_PATH')):
    raise SystemExit('unset loader overrides before starting the scalar supervisor')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_owned_execution as own
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_native_campaign import campaign_runtime, read_reference, reference
from scripts.bfs_simulator_batch import allocated_bytes, batch_storage_paths, lease_observation
from scripts.dx100_capacity import capacity
from swdb import artifacts
from swdb.store import Store, canonical_path

RUN_ID = 'bfs-scalar-v2-preparation-20260926-a1'
MANIFEST = ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/requests/scalar-v2-20260926-a1.preparation.json'
MANIFEST_SHA = '055f1b4ef92f74c9d04b24ea6b9542998802686253caebd28d0ee5837e814383'
RAW = Path('/data/yanruj/EvolveSWDB_runs')/RUN_ID
BUILDS = Path('/data1/yanruj/EvolveSWDB_builds')
RECORDS = ROOT/'records'
PROOF_FILES = ('scripts/bfs_owned_execution.py', 'scripts/bfs_owned_rss.py',
               'scripts/bfs_process.py', 'tests/test_bfs_owned_execution.py')
BOUNDS = {'outer_seconds':1200, 'work_seconds':1170, 'cleanup_seconds':30,
          'api_seconds':240, 'compile_seconds':120, 'ancillary_seconds':210,
          'rss_bytes':16*1024**3, 'artifact_bytes':16*1024**3, 'build_bytes':4*1024**3,
          'node_bytes':20*1024**3, 'global_bytes':24*1024**3,
          'raw_reserve_bytes':30*1024**3, 'build_reserve_bytes':10*1024**3}
REMOVED = ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE','PYTHONOPTIMIZE',
           'PYTEST_PLUGINS','GCC_EXEC_PREFIX','COMPILER_PATH','LIBRARY_PATH','CPATH',
           'CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','LD_PRELOAD','LD_LIBRARY_PATH')
require = own.require


def now(): return datetime.now(own.ET)


def stamp(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.utcoffset() is not None, 'original clock must be timezone-aware')
    return parsed


class Clock:
    def __init__(self, begin, end):
        self.begin, self.end = stamp(begin), stamp(end)
        wall, self.entered = now(), time.monotonic()
        self.startup = (wall-self.begin).total_seconds()
        require(self.end-self.begin == timedelta(seconds=1200) and 0 <= self.startup <= 30,
                'original 1200-second outer clock and at-most-30-second startup required')
        self.hard = self.entered + (self.end-wall).total_seconds()
        self.work = self.hard-30
        self.compile_seconds = 0.0
        self.compiling = None
        self.finalizing = None
        self.lock = threading.RLock()

    def ancillary(self):
        with self.lock:
            end = self.finalizing if self.finalizing is not None else time.monotonic()
            active = end-self.compiling if self.compiling is not None else 0
            return self.startup + end-self.entered-self.compile_seconds-active

    def begin_finalization(self):
        with self.lock:
            require(self.compiling is None, 'cannot finalize an active compile call')
            self.finalizing = time.monotonic()

    def check(self, cleanup=False):
        require(time.monotonic() < (self.hard if cleanup else self.work)
                and now() < self.end-timedelta(seconds=0 if cleanup else 30),
                'original scalar preparation deadline exhausted')
        require(self.ancillary() <= 210, 'cumulative 210-second ancillary allowance exhausted')

    @contextmanager
    def compile(self):
        with self.lock:
            require(self.compiling is None and self.finalizing is None, 'compile calls must be sequential work')
            self.check(); self.compiling = time.monotonic()
        try: yield
        finally:
            with self.lock:
                self.compile_seconds += time.monotonic()-self.compiling
                self.compiling = None


def controlled_environment(temporary):
    value=dict(os.environ)
    for key in REMOVED:value.pop(key,None)
    value.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PATH='/usr/bin:/bin',TMPDIR=str(temporary))
    return value


def load_manifest():
    require(MANIFEST.stat().st_size == 31130 and artifacts.file_hash(MANIFEST) == MANIFEST_SHA,
            'fixed preparation manifest changed')
    value = json.loads(MANIFEST.read_text())
    require(value['id'] == RUN_ID and len(value['operations']) == 4, 'fixed operation inventory differs')
    for row in value['operations']:
        path = ROOT/row['request']['path']
        require(artifacts.file_hash(path) == row['request']['sha256'], 'fixed compile request changed')
        request = json.loads(path.read_text())
        require(artifacts.digest(request) == row['request_canonical_sha256'] and request['id'] == row['id']
                and request['budget'] == {'total_seconds':240,'build_seconds':120,'memory_gib':16,'storage_gib':1}
                and request['accelerated'] is False and request['function'] == 'DOBFS'
                and request['roi'] == 'bfs.complete_call.v1', 'compile request scope or bounds differ')
    return value


def validate_proof(ref, runtime, prepared_at):
    """Reuse proof of identical ownership primitives, not proof of this driver."""
    proof = read_reference(ref); audit = read_reference(proof['terminal_audit'])
    driver = read_reference(proof['driver']); pending = read_reference(proof['pending'])
    expected = {'test_linux_owned_stage_reaps_detached_child[False]',
                'test_linux_owned_stage_reaps_detached_child[True]',
                'test_linux_nested_interruption_uses_one_cleanup_budget',
                'test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve'}
    require(proof.get('format') == 'swdb.bfs.linux-fixture.v1' and proof.get('kind') == 'owned_cleanup'
            and proof.get('state') == 'passed' and proof.get('evidence_kind') == 'contract_fixture'
            and proof.get('host') == 'mbit10' and proof.get('platform') == 'linux'
            and proof.get('independent_cleanup_verified') is True and type(proof.get('returncode')) is int
            and proof['returncode'] == 0 and audit.get('state') == 'passed'
            and audit.get('code_commit') == proof['code_commit'] and audit.get('lease_released') is True
            and audit.get('driver') == proof.get('driver') and audit.get('pending') == proof.get('pending')
            and audit.get('kind') == 'owned_cleanup' and audit.get('route') == 'standard',
            'sealed Linux ownership proof is missing or differs')
    require(driver.get('state') == 'complete' and driver.get('kind') == 'owned_cleanup'
            and driver.get('code_commit') == proof['code_commit'] and driver.get('returncode') == 0
            and pending.get('state') == 'tests_passed_cleanup_unverified'
            and pending.get('driver') == proof['driver'] and pending.get('code_commit') == proof['code_commit'],
            'proof no longer binds its successful driver and original pending evidence')
    require(stamp(proof['started']) <= stamp(proof['finished']) <= stamp(proof['audited_at']) <= prepared_at
            and (stamp(proof['finished'])-stamp(proof['started'])).total_seconds() <= 90,
            'Linux proof time/bounds differ')
    tested = driver['runtime']
    require(tested['commit'] == proof['code_commit'] and tested['python'] == runtime['python']
            and all(tested['files'].get(name) == runtime['files'].get(name) and name in runtime['files']
                    and proof.get('runtime_sha256',{}).get(name) == runtime['files'][name]
                    for name in PROOF_FILES), 'tested ownership/Python bytes differ from selected runtime')
    for key, maximum in (('junit',4*1024**2),('stdout',16*1024**2)):
        path = Path(proof[key]['path'])
        require(path.is_absolute() and path == path.resolve() and path.is_file()
                and path.stat().st_size <= maximum and artifacts.file_hash(path) == proof[key]['sha256'],
                'Linux proof output changed or exceeds read bound')
    cases = XML.fromstring(Path(proof['junit']['path']).read_bytes()).findall('.//testcase')
    require(len(cases) == 4 and {case.get('name') for case in cases} == expected
            and all(not any(case.find(k) is not None for k in ('failure','error','skipped')) for case in cases),
            'ownership cases missing, failed or skipped')
    return {'reference':ref, 'actual_proof_commit':proof['code_commit'],
            'driver_commit':runtime['commit'], 'identical_tested_files':{p:runtime['files'][p] for p in PROOF_FILES},
            'scope':'contract proof of reused ownership primitives; not execution proof of this new driver'}


def record_pins(manifest):
    pins = {item['id']:item for item in (manifest['model']['build'],manifest['model']['target'])}
    for row in manifest['operations']:
        for key in ('candidate','source_snapshot','implementation'):
            pins[row[key]['id']] = row[key]
    return pins


def verify_inputs(manifest, store):
    for rid, pin in record_pins(manifest).items():
        data = store.get(rid, pin['kind'])
        require(data and artifacts.digest(data) == pin['canonical_sha256'], 'fixed input record changed: '+rid)
    for row in manifest['operations']:
        require(not store.get(row['id']) and not (BUILDS/row['id']).exists(), 'compile ID/output already exists; no retry')
        candidate = store.get(row['candidate']['id'])
        source = store.get(candidate['source_snapshot'])
        require(candidate['artifact_role'] == 'source_baseline'
                and candidate['artifact']['sha256'] == source['artifact']['sha256'], 'baseline source identity differs')
        path = artifacts.verify(candidate['artifact']); artifacts.check_protections(path,candidate['protections'])
    receipt = manifest['model']['build_receipt']
    require(artifacts.file_hash(receipt['path']) == receipt['sha256'], 'completed model build receipt changed')
    for row in manifest['operations']:
        compiler = row['historical_compiler']
        require(shutil.which('g++-13',path='/usr/bin:/bin') == compiler['compiler']
                and artifacts.file_hash(compiler['compiler']) == compiler['compiler_sha256'], 'compiler identity changed')
        if row['historical_discovery']:
            item=row['historical_discovery']
            require(artifacts.file_hash(Path(item['library']).resolve()) == item['library_sha256'], 'discovery library changed')


def verify_build(value, request, operation, store):
    require(value.get('id') == request['id'] and value.get('outcome',{}).get('state') == 'complete'
            and value['outcome'].get('stage') == 'candidate_build'
            and artifacts.digest(value.get('request')) == artifacts.digest(request)
            and value.get('evidence_kind') == 'execution' and value.get('gain_claim') is False
            and value.get('timing') == [] and value.get('correctness',{}).get('state') == 'unverified',
            'public build is incomplete, substituted, or claims execution')
    canonical = store.get(request['id'],'evaluation')
    require(canonical and artifacts.digest(canonical) == artifacts.digest(value), 'fresh canonical build differs')
    build, context = value['build'], value['context']
    require(build['adapter'] == 'dx100.complete_call.v2' and context['roi'] == request['roi']
            and context['candidate_sha256'] == operation['source_artifact']['sha256']
            and value['candidate'] == request['candidate'] and context['function'] == 'DOBFS'
            and context['accelerated_requested'] is False
            and build['compiler'] == operation['historical_compiler']['compiler']
            and build['compiler_sha256'] == operation['historical_compiler']['compiler_sha256']
            and build['source_artifact']['sha256'] == operation['source_artifact']['sha256']
            and '-DMAA' not in build['flags'],
            'v2 source/compiler/function binding differs')
    require(bool(context.get('diagnostic')) is request['diagnostic_regions'], 'primary/diagnostic role differs')
    binary = Path(build['binary'])
    require(binary == BUILDS/request['id']/'bfs' and not binary.is_symlink()
            and artifacts.file_hash(binary) == build['binary_sha256'], 'compiled binary path/hash differs')
    for key in ('driver','m5ops'):
        require(artifacts.file_hash(build[key]['path']) == build[key]['sha256'], 'generated build input changed')
    artifacts.verify(build['source_artifact'])


class Driver:
    def __init__(self, args, manifest, clock):
        self.args,self.manifest,self.clock = args,manifest,clock
        self.started = now().isoformat(); self.finalizing = False; self.machine = None
        require(not RAW.exists() and not (BUILDS/(RUN_ID+'.tmp')).exists(), 'preparation output exists; no retry')
        dispatch=Path(str(RAW)+'.dispatch')
        require(dispatch.is_dir() and dispatch == dispatch.resolve(), 'exact wrapper dispatch directory required')
        RAW.mkdir(); self.folder=RAW/(RUN_ID+'.driver'); self.folder.mkdir()
        self.temporary=BUILDS/(RUN_ID+'.tmp'); self.temporary.mkdir()
        self.samples=self.folder/'resources.jsonl'; self.guard=None; self.owner=None
        self.receipt={'format':'swdb.bfs.scalar-v2-build-driver.v1','id':RUN_ID,'created':'2026-09-26',
            'state':'running','started':self.started,'outer_started':clock.begin.isoformat(),
            'outer_deadline':clock.end.isoformat(),'bounds':BOUNDS,'stages':[],'builds':[],
            'manifest':reference(MANIFEST),'database':str(RAW/'swdb.sqlite'),'gain_claim':False,
            'automatic_retry_allowed':False,'cleanup_verified':False,'guest_executions':0,'provider_calls':0}
        save_receipt(self.folder,self.receipt)
        path=self.folder/'cleanup-ledger.json'
        binding=own.SharedCleanup.create(path,clock.end.isoformat(),deadline=clock.hard)
        self.budget=own.SharedCleanup(path,binding,clock.hard)
        self.receipt['cleanup_budget']={'path':str(path),'binding':binding,'budget_seconds':30}
        self.owner=own.Owned(self.budget)
        ident=own.identity(os.getpid()); pane={'pid':args.pane_pid,'start_ticks':args.pane_start_ticks}
        self.receipt['process_observations']={'driver_identity':ident,'pane_identity':pane,'ancestry':own.ancestry(ident,pane)}
        self.env=controlled_environment(self.temporary)
        self.receipt['controlled_environment']={**dict.fromkeys(REMOVED),**{k:self.env[k] for k in ('PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE','PATH','TMPDIR')}}

    def account(self):
        paths=batch_storage_paths(RAW)
        builds=[self.temporary]+[BUILDS/row['id'] for row in self.manifest['operations'] if (BUILDS/row['id']).exists()]
        records=[RECORDS/canonical_path('evaluation',row['id']) for row in self.manifest['operations']
                 if (RECORDS/canonical_path('evaluation',row['id'])).exists()]
        build_bytes=allocated_bytes(builds); total=allocated_bytes(paths+records)+build_bytes
        require(total <= BOUNDS['artifact_bytes'] and build_bytes <= BOUNDS['build_bytes'], 'preparation artifact/build ceiling exceeded')
        free={}
        for name,path,bound in (('raw',RAW,BOUNDS['raw_reserve_bytes']),('build',BUILDS,BOUNDS['build_reserve_bytes'])):
            stat=os.statvfs(path); free[name]=stat.f_bavail*stat.f_frsize
            require(free[name]>=bound, 'preparation free-space reserve exhausted')
        self.clock.check(self.finalizing)
        return {'observed_at':now().isoformat(),'artifact_bytes':total,'build_bytes':build_bytes,
                'storage_paths':list(map(str,paths+builds+records)),'free_bytes':free}

    def observe(self):
        sample=self.owner.sample(); sample['accounting']=self.account()
        require(sample['rss_bytes']<=BOUNDS['rss_bytes'],'preparation sampled RSS exceeds16GiB')
        if self.machine is not None: sample['leases']=lease_observation(self.machine,self.args.lane)
        with self.samples.open('a') as stream:stream.write(json.dumps(sample)+'\n')
        return sample

    def check(self):
        self.clock.check(); self.guard.check()

    def call(self, command, *, timeout=15, compile=False):
        self.check(); began=time.monotonic()
        context=self.clock.compile() if compile else nullcontext()
        with context:
            row=own.run_stage(self.receipt,self.folder,[sys.executable,'-s','-m','swdb',*command,
                '--records',str(RECORDS),'--db',str(RAW/'swdb.sqlite'),'--format','json'],
                timeout=timeout,deadline=min(self.clock.work,began+timeout),cwd=ROOT,
                owned=self.owner,monitor=self.guard.check,env=self.env)
        self.check()
        path=Path(row['output'])
        require(path.stat().st_size<=32*1024**2,'public metadata output exceeds32MiB')
        return json.loads(path.read_text())

    def execute(self):
        self.guard=own.Monitor(self.observe); self.guard.start()
        require((now()-self.clock.begin).total_seconds()<=30,'first resource observation exceeded startup bound')
        admission_ref={'path':str(self.args.admission),'sha256':self.args.admission_sha256}
        require(self.args.admission == Path(str(RAW)+'.dispatch')/'admission.json',
                'admission must be in the exact accounted dispatch directory')
        admission=read_reference(admission_ref); runtime=campaign_runtime(self.args.expected_commit)
        require(admission.get('format')=='swdb.bfs.scalar-v2-build-admission.v1' and admission.get('id')==RUN_ID
                and admission.get('manifest_sha256')==MANIFEST_SHA and admission.get('code_commit')==self.args.expected_commit
                and admission.get('node')==self.args.lane and type(admission.get('node')) is int
                and stamp(admission['prepared_at'])<=self.clock.begin
                and artifacts.digest(admission.get('runtime'))==artifacts.digest(runtime),'prospective admission/runtime differs')
        self.receipt.update(admission=admission_ref,runtime=runtime,
            linux_ownership_proof=validate_proof(admission['linux_proof'],runtime,stamp(admission['prepared_at'])))
        store=Store(RECORDS); self.machine=store.get('mbit10','machine')
        self.receipt['leases']=lease_observation(self.machine,self.args.lane)
        raw={'node':Path(f'/sys/devices/system/node/node{self.args.lane}/meminfo').read_text(),
             'zones':Path('/proc/zoneinfo').read_text(),'global':Path('/proc/meminfo').read_text()}
        available=capacity(raw['node'],raw['zones'],raw['global'],self.args.lane,os.sysconf('SC_PAGE_SIZE'))
        require(available['estimated_available_kib']*1024>=BOUNDS['node_bytes']
                and available['global_available_kib']*1024>=BOUNDS['global_bytes'],'preparation capacity admission failed')
        self.receipt['capacity']={'inputs':raw,'estimate':available,'observed_at':now().isoformat()}
        verify_inputs(self.manifest,store); self.check()
        self.collect()
        require(campaign_runtime(self.args.expected_commit)==runtime,'runtime changed during preparation')
        final_store=Store(RECORDS)
        require(artifacts.file_hash(MANIFEST)==MANIFEST_SHA
                and all(artifacts.digest(final_store.get(rid))==pin['canonical_sha256']
                        for rid,pin in record_pins(self.manifest).items()),
                'manifest or immutable input metadata changed during preparation')
        self.check(); self.receipt['state']='complete'

    def collect(self):
        """Only fixed public gets/compiles; failure cannot skip to another cell."""
        for rid,pin in record_pins(self.manifest).items():
            fresh=self.call(['get',rid])
            require(artifacts.digest(fresh)==pin['canonical_sha256'],'fresh public input differs')
        requests=RAW/'requests';requests.mkdir()
        for operation in self.manifest['operations']:
            source=ROOT/operation['request']['path']; copied=requests/source.name
            with copied.open('xb') as stream:stream.write(source.read_bytes());stream.flush();os.fsync(stream.fileno())
            require(artifacts.file_hash(copied)==operation['request']['sha256'],'copied request changed')
            request=json.loads(copied.read_text())
            value=self.call(['dx100-compile',str(copied),'--runs-dir',str(RAW),'--lane',str(self.args.lane)],timeout=240,compile=True)
            verify_build(value,request,operation,Store(RECORDS));self.check()
            chain=self.call(['get',request['id'],'--chain'])
            require(chain.get('root')==request['id']
                    and artifacts.digest(chain.get('records',{}).get(request['id']))==artifacts.digest(value)
                    and all(artifacts.digest(chain['records'].get(operation[key]['id']))
                            == operation[key]['canonical_sha256'] for key in ('candidate','source_snapshot')),
                    'fresh public build chain differs')
            self.receipt['builds'].append({'id':request['id'],'request':reference(copied),
                'canonical_sha256':artifacts.digest(value),'binary':{'path':value['build']['binary'],'sha256':value['build']['binary_sha256']}})

    def finalize(self, error):
        self.finalizing=True;self.clock.begin_finalization();failure=error
        if error:self.receipt.update(state='failed',reason=f'{type(error).__name__}: {error}')
        if self.guard:self.guard.interrupt=False
        def failed(exc,key):
            nonlocal failure
            failure=failure or exc; self.receipt.update(state='failed',**{key:f'{type(exc).__name__}: {exc}'})
        try:self.receipt['cleanup']=own.verified_finish(self.owner)
        except BaseException as exc:failed(exc,'cleanup_error')
        self.receipt['process_observations']['owned_processes']=list(self.owner.history.values())
        try:
            with self.budget.reservation() as until:
                if self.guard:self.guard.stop(until)
                self.observe()
                self.receipt['process_observations']['owned_processes']=list(self.owner.history.values())
                self.receipt['resources']=reference(self.samples)
                self.receipt['resource_validation']=own.validate_samples(self.samples,self.clock.begin.isoformat(),now().isoformat())
                require(self.receipt['resource_validation']['peak_sampled_rss_bytes']<=BOUNDS['rss_bytes'],
                        'retained sampled RSS exceeds16GiB')
                for _ in range(2):
                    self.receipt.update(final_accounting=self.account(),finished=now().isoformat(),
                        ancillary_seconds=self.clock.ancillary(),compile_call_seconds=self.clock.compile_seconds,
                        host_wall_s=(now()-self.clock.begin).total_seconds(),cleanup_accounting=self.budget.snapshot())
                    save_receipt(self.folder,self.receipt);self.account()
                    require(time.monotonic()<=until,'finalization exceeded shared cleanup reservation')
        except BaseException as exc:
            failed(exc,'finalization_error')
            self.receipt['process_observations']['owned_processes']=list(self.owner.history.values())
            try:
                with self.budget.reservation():save_receipt(self.folder,self.receipt)
            except BaseException as secondary:
                if failure:failure.add_note('failure receipt persistence: '+str(secondary))
        if failure:raise failure


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('expected-commit','outer-started','outer-deadline','admission-sha256'):parser.add_argument('--'+key,required=True)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--lane',type=int,choices=(0,1),required=True)
    for key in ('pane-pid','pane-start-ticks'):parser.add_argument('--'+key,type=int,required=True)
    args=parser.parse_args(); clock=Clock(args.outer_started,args.outer_deadline)
    require(socket.gethostname().split('.')[0]=='mbit10' and sys.platform=='linux','scalar builds require mbit10/Linux')
    require(not sys.flags.optimize and sys.flags.no_user_site,'use Python -s with assertions enabled')
    manifest=load_manifest();driver=Driver(args,manifest,clock);error=None
    try:driver.execute()
    except BaseException as exc:error=exc
    driver.finalize(error)
    with driver.budget.reservation():
        print(json.dumps({'id':RUN_ID,'state':driver.receipt['state'],'driver':reference(driver.folder/'driver.json')}),flush=True)
        driver.clock.check(True)


if __name__=='__main__':
    with interruption_signals():main()
