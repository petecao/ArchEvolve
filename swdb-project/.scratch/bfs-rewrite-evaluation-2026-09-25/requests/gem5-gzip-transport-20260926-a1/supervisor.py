#!/usr/bin/env python3
"""One no-guest gem5 gzip transport smoke. Created 2026-09-26 ET."""
import argparse
from datetime import datetime, timedelta
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import time

RUNTIME = Path('/data1/yanruj/EvolveSWDB_simulator_campaign_20260926_a2')
COMMIT = '8c39ae09406dad0da253b21dbe2c87e263f8c5fb'
RUN_ID = 'bfs-gem5-gzip-transport-20260926-a1'
RAW = Path('/data/yanruj/EvolveSWDB_runs') / RUN_ID
DISPATCH = Path(str(RAW) + '.dispatch')
MODEL = Path('/data1/yanruj/DX100-bfs-e4fc4af/build/X86/gem5.opt')
MODEL_SHA = 'f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b'
PYTHON_SHA = 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
ENV = {**dict.fromkeys(('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE',
    'PYTHONOPTIMIZE','PYTEST_ADDOPTS','PYTEST_PLUGINS','LD_PRELOAD','LD_LIBRARY_PATH')),
    'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}
if __name__ == '__main__' and (not sys.flags.no_user_site or sys.flags.optimize or
        any(os.environ.get(k) != v for k,v in ENV.items())):
    raise SystemExit('declared isolated Python environment required')
sys.path.insert(0, str(RUNTIME))
from scripts import bfs_owned_execution as own
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_native_campaign import campaign_runtime
from scripts.bfs_simulator_batch import allocated_bytes, lease_observation
from swdb import artifacts
from swdb.store import Store

def require(value, reason):
    if not value: raise ValueError(reason)

def ref(path):
    return {'path':str(path), 'sha256':artifacts.file_hash(path)}

def transport_check(folder, check):
    """Bounded streaming decode must reach gzip EOF/CRC after normal gem5 exit."""
    compressed = folder/'gem5/transport.gz'
    plain = folder/'gem5/post-switch.log'
    with compressed.open('rb') as stream:
        require(stream.read(2) == b'\x1f\x8b', 'missing native gzip header')
    digest = hashlib.sha256(); total = 0; parts = []
    with gzip.open(compressed,'rb') as stream:
        while True:
            check()
            block = stream.read(65536)
            if not block: break
            total += len(block)
            require(total <= 1024**2, 'two-event decoded trace exceeds 1 MiB')
            digest.update(block); parts.append(block)
    raw = b''.join(parts)
    require(plain.stat().st_size <= 1024**2, 'two-event plain trace exceeds 1 MiB')
    other = plain.read_bytes()
    pattern = lambda tick: rb'(?m)^\s*' + str(tick).encode() + rb':.*executed @ ' + str(tick).encode() + rb'\s*$'
    require(len(re.findall(pattern(1),raw)) == 1 and not re.search(pattern(2),raw),
            'gzip does not contain exactly the first executed exit')
    require(len(re.findall(pattern(2),other)) == 1 and not re.search(pattern(1),other),
            'plain switched trace does not contain exactly the second executed exit')
    stdout = folder/'gem5.stdout'
    require(stdout.stat().st_size <= 1024**2, 'smoke stdout oversized')
    text = stdout.read_bytes()
    require(text.count(b'GZIP_TRANSPORT_NO_GUEST_OK ticks=2') == 1 and b'executed @' not in text,
            'stdout marker or debug-output separation differs')
    check()
    return {'state':'passed','gzip':ref(compressed),'decoded_bytes':total,
        'decoded_sha256':digest.hexdigest(),'gzip_eof_crc_verified':True,
        'plain_switched_trace':ref(plain),'stdout':ref(stdout),'stderr':ref(folder/'gem5.stderr'),
        'empty_root':True,'systems':0,'cpus':0,'guest_workloads':0,'simulation_ticks':2,
        'gzip_executed_tick':1,'plain_executed_tick':2,'runtime_transport_only':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--outer-started',required=True);p.add_argument('--outer-deadline',required=True)
    p.add_argument('--pane-pid',type=int,required=True);p.add_argument('--pane-start-ticks',type=int,required=True)
    p.add_argument('--config-sha256',required=True)
    p.add_argument('--supervisor-source-commit',required=True)
    a=p.parse_args()
    require(re.fullmatch(r'[0-9a-f]{40}',a.supervisor_source_commit), 'full supervisor Git commit required')
    begin=datetime.fromisoformat(a.outer_started);end=datetime.fromisoformat(a.outer_deadline)
    require(begin.utcoffset() is not None and end-begin==timedelta(seconds=90), 'original 90-second clock differs')
    elapsed=(datetime.now(own.ET)-begin).total_seconds()
    require(0 <= elapsed <= 5,'startup exceeded original outer allowance')
    deadline=time.monotonic()+(end-datetime.now(own.ET)).total_seconds();work_end=deadline-30
    require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10','mbit10/Linux required')
    require(not RAW.exists() and RAW==RAW.resolve() and DISPATCH.is_dir(),'fresh fixed raw root required')
    config=DISPATCH/'empty-root.py'
    require(not config.is_symlink() and artifacts.file_hash(config)==a.config_sha256,'config differs')
    RAW.mkdir();(RAW/'tmp').mkdir()
    binding=own.SharedCleanup.create(RAW/'cleanup-ledger.json',end.isoformat(),deadline=deadline)
    budget=own.SharedCleanup(RAW/'cleanup-ledger.json',binding,deadline);owner=own.Owned(budget)
    driver=own.identity(os.getpid());pane={'pid':a.pane_pid,'start_ticks':a.pane_start_ticks}
    receipt={'id':RUN_ID,'created':'2026-09-26','state':'running','started':a.outer_started,
        'outer_deadline':a.outer_deadline,'code_commit':COMMIT,'runtime_commit':COMMIT,
        'supervisor_source_commit':a.supervisor_source_commit,
        'source_provenance':'caller verifies auxiliary Git blobs; code_commit identifies borrowed runtime only',
        'stages':[],'automatic_retry_allowed':False,
        'evidence_kind':'no_guest_transport_contract','bounds':{'outer_seconds':90,'work_seconds':60,
        'cleanup_seconds':30,'sampled_rss_bytes':2*1024**3,'combined_output_bytes':512*1024**2},
        'cleanup_verified':False,'process_observations':{'driver_identity':driver,'pane_identity':pane,
        'ancestry':own.ancestry(driver,pane)},'config':ref(config),'supervisor':ref(Path(__file__).resolve()),
        'cleanup_budget':{'path':str(budget.path),'binding':binding,'budget_seconds':30}}
    samples=RAW/'resource-samples.jsonl';machine=None;guard=None;failure=None
    def check_work():
        require(time.monotonic()<work_end and datetime.now(own.ET)<end-timedelta(seconds=30),
                'original 60-second work allowance exhausted')
        if guard:guard.check()
    def observe():
        require(time.monotonic()<deadline and datetime.now(own.ET)<end,'original outer allowance exhausted')
        row=owner.sample();require(row['rss_bytes']<=2*1024**3,'sampled tree exceeds 2 GiB')
        row['output_bytes']=allocated_bytes([RAW,DISPATCH])
        require(row['output_bytes']<=512*1024**2,'combined output exceeds 512 MiB')
        for root,reserve in ((RAW.parent,30*1024**3),(Path('/data1'),10*1024**3)):
            st=os.statvfs(root);require(st.f_bavail*st.f_frsize>=reserve,'free-space reserve violated')
        if machine is not None:row['lane']=lease_observation(machine,1)
        with samples.open('a') as stream:
            stream.write(json.dumps(row)+'\n');stream.flush()
        return row
    with interruption_signals():
        try:
            guard=own.Monitor(observe);guard.start()
            machine=Store(RUNTIME/'records').get('mbit10');observe()
            receipt['runtime']=campaign_runtime(COMMIT)
            require(artifacts.file_hash(Path(sys.executable).resolve())==PYTHON_SHA,'Python changed')
            receipt['model']=ref(MODEL)
            require(receipt['model']['sha256']==MODEL_SHA,'model binary changed')
            check_work()
            command=[str(MODEL),'--debug-flags=Event','--debug-file=transport.gz',
                     '--outdir='+str(RAW/'gem5'),str(config)]
            env=dict(os.environ);env['TMPDIR']=str(RAW/'tmp')
            own.run_stage(receipt,RAW,command,timeout=work_end-time.monotonic(),deadline=work_end,
                cwd=RUNTIME,owned=owner,monitor=check_work,env=env,
                output=RAW/'gem5.stdout',stderr=RAW/'gem5.stderr')
            receipt['transport']=transport_check(RAW,check_work)
            require(campaign_runtime(COMMIT)==receipt['runtime'],'supervisor runtime changed')
            check_work();receipt['state']='complete'
        except BaseException as exc:
            failure=exc;receipt.update(state='failed',reason=f'{type(exc).__name__}: {exc}')
        finally:
            if guard:guard.interrupt=False
            try:receipt['cleanup']=own.verified_finish(owner)
            except BaseException as exc:
                failure=failure or exc;receipt.update(state='failed',cleanup_error=f'{type(exc).__name__}: {exc}')
            try:
                if guard:
                    with budget.reservation() as until:guard.stop(until)
                with budget.reservation():
                    observe()
                    receipt['process_observations']['owned_processes']=list(owner.history.values())
                    receipt['resource_samples']=ref(samples)
                    receipt['resource_validation']=own.validate_samples(samples,a.outer_started,own.stamp())
                    receipt['cleanup_accounting']=budget.snapshot()
                    receipt.update(finished=own.stamp(),elapsed_seconds=(datetime.now(own.ET)-begin).total_seconds())
                    save_receipt(RAW,receipt)
                    observe()
                    receipt['resource_samples']=ref(samples)
                    receipt['resource_validation']=own.validate_samples(samples,a.outer_started,own.stamp())
                    receipt['finished']=own.stamp();save_receipt(RAW,receipt)
                    require(time.monotonic()<deadline and allocated_bytes([RAW,DISPATCH])<=512*1024**2,
                            'final persistence exceeded original bounds')
            except BaseException as exc:
                failure=failure or exc;receipt.update(state='failed',finalization_error=f'{type(exc).__name__}: {exc}')
                try:
                    with budget.reservation():save_receipt(RAW,receipt)
                except BaseException as secondary:
                    failure.add_note('Failure persistence: '+str(secondary))
        if failure is not None:raise failure
    # No independently passed proof is published here; host audits actual exit,
    # all retained identities, settled ledger, lease release, and final bytes.
if __name__=='__main__':main()
