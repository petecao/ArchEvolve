#!/usr/bin/env python3
"""One fixed retained-candidate diagnostic build. Interface v1, 2026-09-26 ET.

Original 600-second wrapper clock: 570 work plus shared 30 cleanup. No retry,
provider, repair, guest execution or primary rebuild. See the dated interface doc.
"""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import socket
import sys
import threading
import time

if __name__ == '__main__' and any(k in os.environ for k in ('LD_PRELOAD', 'LD_LIBRARY_PATH')):
    raise SystemExit('unset loader overrides before starting the diagnostic supervisor')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_scalar_v2_builds as scalar
from scripts import bfs_t17_build_only as primary
from scripts import bfs_owned_execution as own
from scripts.bfs_native_campaign import campaign_runtime, read_reference, reference
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_simulator_batch import batch_storage_paths, lease_observation
from scripts.bfs_storage import allocated_bytes
from scripts.dx100_capacity import capacity
from swdb import artifacts
from swdb.store import Store, canonical_path

RUN_ID = 'bfs-t17-diagnostic-build-only-20260926-a1'
PREPARATION = ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25'
REQUEST = PREPARATION/'requests/t17-diagnostic-build-only-20260926-a1.json'
REQUEST_SHA = '272def5a75dd974d8fa46b3ccdd56016ea1ddf0f2af545990fc02cc25405e5c1'
PRIMARY_OBSERVATION = PREPARATION/'observations/t17-build-only-terminal-20260926.json'
PRIMARY_OBSERVATION_SHA = 'a124548a4d1e71003faeb895d9e09d1e060933ba41a99f1d9ae282689c886536'
PRIMARY_ID = 'bfs-t17-build-only-20260926-a1'
PRIMARY_RECORD_SHA = 'd5ed1ec5b43665379a2b8d59cc2b4cbc582502beb62f5184041079e606229215'
PRIMARY_BINARY_SHA = '852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527'
PRIMARY_TERMINAL_SHA = '4495783bea9d86bc5095e917540abef7b65bef6b94c158adaa41dc88f78fe625'
RAW = Path('/data/yanruj/EvolveSWDB_runs')/RUN_ID
DISPATCH = Path(str(RAW)+'.dispatch')
RECORDS = DISPATCH/'record-view/records'
BUILDS = Path('/data1/yanruj/EvolveSWDB_builds')
BOUNDS = {'outer_seconds':600, 'work_seconds':570, 'cleanup_seconds':30,
          'api_seconds':240, 'build_seconds':180, 'get_seconds':15,
          'rss_bytes':16*1024**3, 'artifact_bytes':2*1024**3, 'build_bytes':1024**3,
          'node_bytes':20*1024**3, 'global_bytes':24*1024**3,
          'raw_reserve_bytes':30*1024**3, 'build_reserve_bytes':10*1024**3}
require = own.require
now = scalar.now
stamp = scalar.stamp


class Clock(scalar.Clock):
    """Reuse coherent timing snapshots; only the original whole clock admits work."""
    def __init__(self, begin, end):
        self.begin, self.end = stamp(begin), stamp(end)
        wall, self.entered = now(), time.monotonic()
        self.startup = (wall-self.begin).total_seconds()
        require(self.end-self.begin == timedelta(seconds=600) and 0 <= self.startup <= 30,
                'original 600-second clock with at-most-30-second startup required')
        self.hard = self.entered+(self.end-wall).total_seconds(); self.work = self.hard-30
        self.compile_seconds = 0.; self.compiling = self.finalizing = None
        self.lock = threading.RLock()

    def check(self, cleanup=False):
        require(time.monotonic() < (self.hard if cleanup else self.work)
                and now() < self.end-timedelta(seconds=0 if cleanup else 30),
                'original diagnostic build deadline exhausted')


def load_request():
    require(REQUEST.stat().st_size == 561 and artifacts.file_hash(REQUEST) == REQUEST_SHA,
            'fixed diagnostic request bytes changed')
    request = json.loads(REQUEST.read_text())
    previous = json.loads(primary.REQUEST.read_text())
    require(artifacts.file_hash(primary.REQUEST) == primary.REQUEST_SHA
            and {**previous, 'id':RUN_ID, 'diagnostic_regions':True} == request,
            'diagnostic request changes more than ID and instrumentation')
    return request


def record_inventory():
    require(RECORDS.is_dir() and RECORDS == RECORDS.resolve() and not RECORDS.is_symlink(),
            'exact canonical record view is required')
    rows = []
    for path in sorted(RECORDS.rglob('*')):
        require(not path.is_symlink(), 'record view contains a symlink')
        if path.is_dir(): continue
        if path == RECORDS/'.swdb.lock':
            require(path.is_file() and path.stat().st_size == 0, 'public writer lock differs')
            continue
        require(path.is_file() and path.suffix == '.yaml' and len(rows) < 4096,
                'unexpected or oversized record view')
        rows.append({'path':path.relative_to(RECORDS).as_posix(), 'bytes':path.stat().st_size,
                     'sha256':artifacts.file_hash(path)})
    return rows


def validate_record_view(ref):
    require(Path(ref['path']) == DISPATCH/'record-view-manifest.json', 'record manifest path differs')
    value = read_reference(ref)
    require(value.get('format') == 'swdb.bfs.record-view.v1' and value.get('records') == str(RECORDS)
            and isinstance(value.get('git_provenance'), list) and value['git_provenance']
            and all(isinstance(row,dict) and re.fullmatch('[a-f0-9]{40}',row.get('commit',''))
                    for row in value['git_provenance'])
            and artifacts.digest(value.get('files')) == artifacts.digest(record_inventory()),
            'initial Git record materialization differs from its retained manifest')
    return value


def verify_primary(value, pins):
    require(value.get('id') == PRIMARY_ID and value.get('candidate') == pins['candidate']['id']
            and value.get('outcome',{}).get('state') == 'complete'
            and value['outcome'].get('stage') == 'candidate_build'
            and value.get('evidence_kind') == 'execution' and value.get('gain_claim') is False
            and not value.get('timing') and value.get('correctness',{}).get('state') == 'unverified',
            'original primary is not the retained build-only result')
    require(artifacts.file_hash(RECORDS/canonical_path('evaluation',PRIMARY_ID)) == PRIMARY_RECORD_SHA
            and value['build']['binary_sha256'] == PRIMARY_BINARY_SHA
            and value['build']['adapter'] == 'dx100.complete_call.v2'
            and value['context']['candidate_sha256'] == pins['candidate']['artifact_sha256']
            and artifacts.digest(value['request']) == artifacts.digest(json.loads(primary.REQUEST.read_text())),
            'original primary request/source/binary identity differs')
    require(artifacts.file_hash(value['build']['binary']) == PRIMARY_BINARY_SHA, 'original primary binary changed')
    for name in ('driver','m5ops'):
        require(artifacts.file_hash(value['build'][name]['path']) == value['build'][name]['sha256'],
                'original primary generated input changed')


def verify_diagnostic(value, request, previous, pins, store):
    require(value.get('id') == RUN_ID and value.get('candidate') == pins['candidate']['id']
            and value.get('outcome',{}).get('state') == 'complete'
            and value['outcome'].get('stage') == 'candidate_build' and value.get('evidence_kind') == 'execution'
            and value.get('gain_claim') is False and value.get('timing') == []
            and value.get('correctness',{}).get('state') == 'unverified'
            and value.get('profiling',{}).get('state') == 'incomplete'
            and artifacts.digest(value.get('request')) == artifacts.digest(request)
            and artifacts.digest(store.get(RUN_ID,'evaluation')) == artifacts.digest(value),
            'diagnostic public result is substituted, incomplete or overstates evidence')
    build, context = value['build'], value['context']
    require(build['adapter'] == 'dx100.complete_call.v2'
            and context['candidate_sha256'] == pins['candidate']['artifact_sha256']
            and context['function'] == 'DOBFS' and context['roi'] == 'bfs.complete_call.v1'
            and context['accelerated_requested'] is True and context.get('diagnostic')
            and context['diagnostic']['roi'] == context['roi']
            and artifacts.digest(context['graph_verification']) == artifacts.digest(previous['context']['graph_verification'])
            and context['verifier_source']['symbol'] == 'swdb_original::Graph::verify'
            and build['compiler_sha256'] == pins['compiler']['sha256']
            and build['compiler'] == pins['compiler']['path'] and '-DMAA' in build['flags']
            and build['source_artifact']['sha256'] == pins['candidate']['artifact_sha256'],
            'diagnostic source/compiler/ROI/original-adjacency binding differs')
    require(Path(build['binary']) == BUILDS/RUN_ID/'bfs'
            and artifacts.file_hash(build['binary']) == build['binary_sha256'], 'diagnostic binary path/hash differs')
    for key in ('driver','m5ops'):
        require(artifacts.file_hash(build[key]['path']) == build[key]['sha256'], 'diagnostic generated input changed')
    artifacts.verify(build['source_artifact'])
    for row in value.get('raw_artifacts',[]):
        if row.get('kind') == 'candidate_build': artifacts.verify(row['artifact'])


class Driver(scalar.Driver):
    """Reuse the reviewed monitor/finalizer, with explicit one-build paths and caps."""
    def __init__(self, args, clock):
        self.args, self.clock = args, clock
        self.finalizing = False; self.machine = None; self.guard = self.owner = None
        require(not RAW.exists() and not (BUILDS/RUN_ID).exists()
                and not (BUILDS/(RUN_ID+'.tmp')).exists(), 'diagnostic output already exists; no retry')
        require(DISPATCH.is_dir() and DISPATCH == DISPATCH.resolve(), 'exact wrapper dispatch directory required')
        RAW.mkdir(); self.folder=RAW/(RUN_ID+'.driver'); self.folder.mkdir()
        self.temporary=BUILDS/(RUN_ID+'.tmp'); self.temporary.mkdir()
        self.samples=self.folder/'resources.jsonl'
        self.receipt={'format':'swdb.bfs.t17-diagnostic-build-driver.v1','id':RUN_ID,'created':'2026-09-26',
            'state':'running','started':now().isoformat(),'outer_started':clock.begin.isoformat(),
            'outer_deadline':clock.end.isoformat(),'bounds':BOUNDS,'stages':[],
            'database':str(RAW/'swdb.sqlite'),'provider_calls':0,'guest_executions':0,'gain_claim':False,
            'cleanup_verified':False,'automatic_retry_allowed':False,'request':reference(REQUEST)}
        save_receipt(self.folder,self.receipt)
        ledger=self.folder/'cleanup-ledger.json'
        binding=own.SharedCleanup.create(ledger,clock.end.isoformat(),deadline=clock.hard)
        self.budget=own.SharedCleanup(ledger,binding,clock.hard)
        self.receipt['cleanup_budget']={'path':str(ledger),'binding':binding,'budget_seconds':30}
        self.owner=own.Owned(self.budget)
        ident=own.identity(os.getpid()); pane={'pid':args.pane_pid,'start_ticks':args.pane_start_ticks}
        self.receipt['process_observations']={'driver_identity':ident,'pane_identity':pane,'ancestry':own.ancestry(ident,pane)}
        self.env=scalar.controlled_environment(self.temporary)
        self.receipt['controlled_environment']={**dict.fromkeys(scalar.REMOVED),
            **{key:self.env[key] for key in ('PATH','TMPDIR','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE')}}

    def account(self):
        roots=batch_storage_paths(RAW)
        builds=[self.temporary]+([BUILDS/RUN_ID] if (BUILDS/RUN_ID).exists() else [])
        build_bytes=allocated_bytes(builds); total=allocated_bytes(roots)+build_bytes
        require(total <= BOUNDS['artifact_bytes'] and build_bytes <= BOUNDS['build_bytes'],
                'diagnostic artifact/build ceiling exceeded')
        free={}
        for key,path in (('raw',RAW),('build',BUILDS)):
            value=os.statvfs(path); free[key]=value.f_bavail*value.f_frsize
            require(free[key] >= BOUNDS[key+'_reserve_bytes'], 'diagnostic storage reserve exhausted')
        self.clock.check(self.finalizing)
        return {'observed_at':now().isoformat(),'artifact_bytes':total,'build_bytes':build_bytes,
                'storage_paths':list(map(str,roots+builds)),'free_bytes':free}

    def call(self, command, *, compile=False):
        self.check(); begin=time.monotonic(); timeout=240 if compile else 15
        require(command[0] == ('dx100-compile' if compile else 'get'), 'only fixed public compile/get operations allowed')
        from contextlib import nullcontext
        with self.clock.compile() if compile else nullcontext():
            row=own.run_stage(self.receipt,self.folder,[sys.executable,'-s','-m','swdb',*map(str,command),
                '--records',str(RECORDS),'--db',str(RAW/'swdb.sqlite'),'--format','json'],
                timeout=timeout,deadline=min(self.clock.work,begin+timeout),cwd=ROOT,
                owned=self.owner,monitor=self.guard.check,env=self.env)
        self.check(); output=Path(row['output'])
        require(output.stat().st_size <= 32*1024**2, 'public metadata read bound exceeded')
        return json.loads(output.read_text())

    def execute(self):
        self.guard=own.Monitor(self.observe); self.guard.start()
        runtime=campaign_runtime(self.args.expected_commit)
        require(self.args.admission == DISPATCH/'admission.json'
                and self.args.admission == self.args.admission.resolve()
                and not self.args.admission.is_symlink(),
                'admission must be in the exact canonical accounted dispatch directory')
        ref={'path':str(self.args.admission),'sha256':self.args.admission_sha256}
        admission=read_reference(ref)
        require(admission.get('format') == 'swdb.bfs.t17-diagnostic-build-admission.v1'
                and admission.get('id') == RUN_ID and admission.get('request_sha256') == REQUEST_SHA
                and admission.get('code_commit') == self.args.expected_commit
                and type(admission.get('node')) is int and admission['node'] == self.args.lane
                and stamp(admission['prepared_at']) <= self.clock.begin
                and artifacts.digest(admission.get('runtime')) == artifacts.digest(runtime), 'diagnostic admission differs')
        view=validate_record_view(admission['record_view'])
        self.receipt.update(admission=ref,runtime=runtime,record_view=admission['record_view'],
            linux_ownership_proof=scalar.validate_proof(admission['linux_proof'],runtime,
                stamp(admission['prepared_at']),require_storage_case=True))
        request=load_request(); store=Store(RECORDS)
        require(store.get(RUN_ID) is None, 'diagnostic ID already exists; no retry')
        self.machine=store.get('mbit10','machine')
        self.receipt['leases']=lease_observation(self.machine,self.args.lane)
        raw={'node':Path(f'/sys/devices/system/node/node{self.args.lane}/meminfo').read_text(),
             'zones':Path('/proc/zoneinfo').read_text(),'global':Path('/proc/meminfo').read_text()}
        available=capacity(raw['node'],raw['zones'],raw['global'],self.args.lane,os.sysconf('SC_PAGE_SIZE'))
        require(available['estimated_available_kib']*1024 >= BOUNDS['node_bytes']
                and available['global_available_kib']*1024 >= BOUNDS['global_bytes'], 'diagnostic capacity admission failed')
        self.receipt['capacity']={'inputs':raw,'estimate':available,'observed_at':now().isoformat()}
        require(artifacts.file_hash(primary.OBSERVATION) == primary.OBSERVATION_SHA, 'original source/provider pins changed')
        pins=json.loads(primary.OBSERVATION.read_text())
        require(artifacts.file_hash(PRIMARY_OBSERVATION) == PRIMARY_OBSERVATION_SHA, 'primary observation changed')
        terminal=json.loads(PRIMARY_OBSERVATION.read_text())
        require(terminal['terminal']['sha256'] == PRIMARY_TERMINAL_SHA
                and terminal['evaluation']['sha256'] == PRIMARY_RECORD_SHA, 'original primary provenance differs')
        audit=read_reference(terminal['terminal']); read_reference(terminal['driver'])
        require(audit['driver']['sha256'] == terminal['driver']['sha256'], 'primary terminal driver differs')
        primary.coverage.a3.verify_terminal_processes(audit['owned_processes'],Path('/proc'))
        self.receipt['primary_terminal']=terminal['terminal']
        self.collect(pins,request)
        produced=canonical_path('evaluation',RUN_ID)
        require(artifacts.digest([row for row in record_inventory() if row['path'] != produced])
                == artifacts.digest(view['files']), 'immutable record view changed during diagnostic build')
        require(campaign_runtime(self.args.expected_commit) == runtime, 'runtime changed during diagnostic build')
        self.check(); self.receipt['state']='complete'

    def collect(self,pins,request):
        ids={'proposal':pins['proposal']['id'],'candidate':pins['candidate']['id'],
             'source_snapshot':pins['source_snapshot']['id'],'package':pins['proposal']['profile_package'],
             'model':pins['model']['build_evaluation'],'target':pins['model']['target']}
        values={key:self.call(['get',rid]) for key,rid in ids.items()}
        primary.verify_inputs(values,pins)
        previous=self.call(['get',PRIMARY_ID]); verify_primary(previous,pins); self.check()
        copied=self.folder/'request.json'
        with copied.open('xb') as stream:
            stream.write(REQUEST.read_bytes()); stream.flush(); os.fsync(stream.fileno())
        require(artifacts.file_hash(copied) == REQUEST_SHA, 'retained compile request changed')
        result=self.call(['dx100-compile',str(copied),'--runs-dir',str(RAW),'--lane',str(self.args.lane)],compile=True)
        fresh=self.call(['get',RUN_ID]); chain=self.call(['get',RUN_ID,'--chain'])
        require(artifacts.digest(result) == artifacts.digest(fresh), 'fresh diagnostic result differs')
        verify_diagnostic(fresh,request,previous,pins,Store(RECORDS))
        require(chain.get('root') == RUN_ID and artifacts.digest(chain.get('records',{}).get(RUN_ID)) == artifacts.digest(fresh)
                and all(artifacts.digest(chain['records'].get(rid)) == artifacts.digest(values[key]) for key,rid in ids.items()),
                'fresh diagnostic chain changed or omitted original records')
        require(all(artifacts.digest(Store(RECORDS).get(rid)) == artifacts.digest(values[key]) for key,rid in ids.items()),
                'original records/provider allowance changed')
        verify_primary(Store(RECORDS).get(PRIMARY_ID),pins)
        self.receipt.update(evaluation_sha256=artifacts.digest(fresh),build=fresh['build'],
            primary_binary_sha256=PRIMARY_BINARY_SHA,provider_budget_unchanged=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('expected-commit','outer-started','outer-deadline','admission-sha256'):
        parser.add_argument('--'+key,required=True)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--lane',type=int,choices=(0,1),required=True)
    for key in ('pane-pid','pane-start-ticks'): parser.add_argument('--'+key,type=int,required=True)
    args=parser.parse_args(); clock=Clock(args.outer_started,args.outer_deadline)
    require(socket.gethostname().split('.')[0] == 'mbit10' and sys.platform == 'linux', 'diagnostic build requires mbit10/Linux')
    require(not sys.flags.optimize and sys.flags.no_user_site, 'use Python -s with assertions enabled')
    load_request(); driver=Driver(args,clock); error=None
    try: driver.execute()
    except BaseException as exc: error=exc
    driver.finalize(error)
    with driver.budget.reservation():
        print(json.dumps({'id':RUN_ID,'state':driver.receipt['state'],'driver':reference(driver.folder/'driver.json')}),flush=True)
        driver.clock.check(True)


if __name__ == '__main__':
    with interruption_signals(): main()
