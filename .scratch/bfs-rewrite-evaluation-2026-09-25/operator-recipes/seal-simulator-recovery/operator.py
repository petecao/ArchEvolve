#!/usr/bin/env python3
"""Fixed T16-only admission and existing batch launch. Prepared 2026-09-27 ET.

No simulator lifecycle is duplicated here. This operator never repairs old
receipts, renews an original deadline, or retries an existing batch ID.
"""
import argparse
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
GROUP_OP=HERE.parent/'supervision-recovery/operator.py'
GROUP_OP_SHA='c40875e68a2c28e0c5b47517d63d0b2c40f26e51414c43f4d253154c8d77b992'
PIN='923cf33b955104fdf96705b648933e7d486a3810'
BASE=Path('/data/yanruj/EvolveSWDB_runs')
GROUP_FINAL=BASE/'bfs-seal-recovery-linux-20260927-a1.final.json'
ROOTS={'t16':Path('/data1/yanruj/EvolveSWDB_t16_seal_recovery_runtime_20260927_a1')}
PROOFS={
 'a3':('bfs-dx100-bringup-20260925/witness-a3-dispatch1/terminal-validation.json','21ee990e45c9da567579aedbcab2e0554ab457fdcabd69f40c478d78e2d4c3e9'),
 'paired':('bfs-native-paired-pilot-20260926-a1.dispatch/terminal-validation.json','d9979ec1a493de0184f9e4b93fb9fbe2c20d8a6bb029ce28ef43d7c4b66551db'),
 'provider':('bfs-provider-initial-20260926-a1/terminal-validation.json','1f455257e4542f67555389195be532de3a131d677083f4e5372c6afcdf02ad1c'),
 'coverage':('bfs-dx100-coverage-20260926-a2.dispatch/terminal-validation.json','6df37b96da525b36e79a351096bf8e565550a61050f247d798e8366f9a1f3815')}


def require(ok,why):
    if not ok:raise ValueError(why)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def ref(path):return {'path':str(path),'sha256':sha(path)}


def setup(kind,config_path):
    require(kind=='t16','seal recovery is T16-only')
    require(isinstance(PIN,str) and len(PIN)==40 and all(c in '0123456789abcdef' for c in PIN),
            'reviewed immutable seal runtime is not pinned')
    require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10','requires mbit10/Linux')
    require(sys.flags.isolated and sys.dont_write_bytecode and not sys.flags.optimize,'requires isolated -I -B Python with assertions')
    require(sha(GROUP_OP)==GROUP_OP_SHA,'reviewed shared admission helper changed')
    op=runpy.run_path(str(GROUP_OP));c=read(config_path)
    require(c['runtime']==str(ROOTS[kind]) and c['commit']==PIN and type(c['node']) is int and c['node'] in (0,1),'fixed runtime/node differs')
    for key in ('manifest','helper','hostlock','python'):
        require(Path(c[key]).is_absolute(),'configuration paths must be absolute')
    op['guard'](c)
    sys.path.insert(0,c['runtime'])
    from scripts import bfs_simulator_batch as batch
    from scripts import bfs_simulator_recovery as recovery
    from swdb import artifacts
    from swdb.store import Store
    fullkind=kind+'-seal-recovery'
    plan=read(batch.PLAN_DIR/(recovery.IDS[fullkind]+'.json'));batch.validate_plan(plan,fullkind)
    return op,c,batch,recovery,artifacts,Store,plan


def schedule(batch,recovery,plan,prepared):
    charges=batch.preparation_charges(plan)
    end=recovery.hard_end(plan)
    latest=end-timedelta(seconds=plan['bounds']['series_seconds']+plan['bounds']['cleanup_seconds'])
    require(prepared<=latest,'original full-series latest start has elapsed')
    return charges,{'not_before':prepared.isoformat(),'latest_start':latest.isoformat(),'absolute_end':end.isoformat()}


def prepare(kind,config_path):
    op,c,b,recovery,artifacts,Store,plan=setup(kind,config_path)
    runs=BASE/plan['id'];dispatch=Path(str(runs)+'.dispatch')
    require(not runs.exists() and not dispatch.exists(),'fresh batch and dispatch IDs required')
    require(c.get('proofgroup') == ref(GROUP_FINAL),'closed fresh proof group changed or unsealed')
    group=read(GROUP_FINAL);require(group['state']=='complete','proof group is not complete')
    fragment=group['admission_fragment'];require(fragment['code_commit']==PIN,'proof runtime commit differs')
    require('linux_proof_runtime' not in fragment,'fresh group cannot carry a historical proof alias')
    require(fragment['runtime_sha256']==b.runtime_identity(),'fresh proof runtime map differs before admission assembly')
    prepared=b.now();charges,clock=schedule(b,recovery,plan,prepared)
    store=Store(ROOTS[kind]/'records');protocols={}
    if kind=='t16':
        for role,rid in [('artifact','bfs-author-reference-20260925.b4cbd3924b40e7df'),('control','bfs-author-matched-control-20260925.d02e719e2d375764')]:
            protocols[role]={'id':rid,'sha256':artifacts.digest(store.get(rid))}
    proofs={}
    for key,(name,digest) in PROOFS.items():
        item=ref(BASE/name);require(item['sha256']==digest,'retained prerequisite changed: '+key);proofs[key]=item
    admission={**fragment,'format':'swdb.bfs.simulator-batch-admission.v1','plan_sha256':artifacts.digest(plan),
      'prepared_at':prepared.isoformat(),'clock':clock,'preparation_charges':charges,'code_commit':PIN,
      'runtime_sha256':b.runtime_identity(),'python':ref(Path(c['python']).resolve()),'proofs':proofs,
      'coverage_commit':'5a0b15fe666b2d094a2b2b9847ff5a30ef16fb4f','protocols':protocols}
    b.validate_cleanup_tests(admission);b.validate_preparation_reservation(plan,admission)
    b.validate_inputs(plan,admission,store)
    for row in plan['series']:
        require(not any(rid==row['id'] or rid.startswith(row['id']+'.') for rid in store.by_id)
                and not list(b.BUILD_ROOT.glob(row['id']+'*')),'series ID or build already exists')
    # Recheck before materializing a new dispatch. Admission preparation does
    # not start a guest; elapsed preparation still forfeits the original window.
    require(b.now()<=b.stamp(clock['latest_start']),'admission preparation exhausted original start window')
    op['guard'](c);dispatch.mkdir()
    op['write'](dispatch/'admission.json',admission)
    op['write'](dispatch/'operator-preparation.json',{'created':'2026-09-27','config':ref(config_path),
       'recipe':ref(__file__),'proofgroup':ref(GROUP_FINAL),'prepared_at':b.now().isoformat(),'empirical_execution':False})
    print(json.dumps(ref(dispatch/'admission.json')))


def launch(kind,config_path,admission_sha,pane_pid,pane_ticks):
    # Original clock starts before host/runtime inspection; all startup must fit
    # the batch supervisor's existing 30-second telemetry bound.
    from datetime import datetime
    from zoneinfo import ZoneInfo
    start=datetime.now(ZoneInfo('America/New_York'))
    op,c,b,recovery,artifacts,Store,plan=setup(kind,config_path)
    runs=BASE/plan['id'];dispatch=Path(str(runs)+'.dispatch');path=dispatch/'admission.json'
    require(sha(path)==admission_sha and not runs.exists() and not (dispatch/'launch.json').exists(),'admission changed or batch already attempted')
    preparation=read(dispatch/'operator-preparation.json')
    require(preparation['config']==ref(config_path) and preparation['recipe']==ref(__file__),'prepared operator/config changed')
    ad=read(path);require(b.stamp(ad['clock']['not_before'])<=start<=b.stamp(ad['clock']['latest_start']),'outside original launch window')
    charges=b.preparation_charges(plan);require(ad['preparation_charges']==charges,'historical costs changed')
    remaining=plan['bounds']['batch_seconds']-sum(row['elapsed_seconds'] for row in charges)
    end=min(recovery.hard_end(plan),start+timedelta(seconds=remaining))
    require((end-start).total_seconds()>=plan['bounds']['series_seconds']+30,'cannot fit full original series')
    leases=op['free_lane'](c);capacity=op['capacity'](c)
    from scripts import bfs_owned_execution as own
    pane=own.identity(pane_pid);require(pane and pane['start_ticks']==pane_ticks and os.getppid()==pane_pid,'exact direct launching pane required')
    current=b.now();require((current-start).total_seconds()<25,'launch inspection consumed telemetry startup bound')
    argv=['timeout','--signal=TERM','--kill-after=30s',str((end-current).total_seconds()-30)+'s',
      'bash',c['helper'],str(c['node']),plan['id'],'--record',str(dispatch/'lane.json'),'--',
      str(Path(c['python']).resolve()),'-s','-B',str(ROOTS[kind]/'scripts/bfs_simulator_batch.py'),kind+'-seal-recovery',
      '--admission',str(path),'--admission-sha256',admission_sha,'--runs-dir',str(runs),'--lane',str(c['node']),
      '--outer-started',start.isoformat(),'--outer-deadline',end.isoformat(),'--pane-pid',str(pane_pid),'--pane-start-ticks',str(pane_ticks)]
    op['write'](dispatch/'launch.json',{'created':'2026-09-27','outer_started':start.isoformat(),'outer_deadline':end.isoformat(),
      'remaining_seconds':remaining,'command':argv,'leases':leases,'capacity':capacity,'pane_identity':pane,'recipe':ref(__file__)})
    os.execvpe(argv[0],argv,op['environment']())


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','launch'));p.add_argument('kind',choices=ROOTS)
    p.add_argument('config',type=Path);p.add_argument('--admission-sha256');p.add_argument('--pane-pid',type=int);p.add_argument('--pane-start-ticks',type=int)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.kind,a.config.resolve())
    else:launch(a.kind,a.config.resolve(),a.admission_sha256,a.pane_pid,a.pane_start_ticks)


if __name__=='__main__':main()
