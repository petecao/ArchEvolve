#!/usr/bin/env python3
"""Private fixed recovery supplement execution and post-exit sealing. 2026-09-27 ET.

This creates no standard proof kind. The operator owns the enclosing 600-second
reservation and invokes audit once, only after the socket helper has exited.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import resource
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_linux_fixture as runner
from scripts import bfs_linux_fixture_audit as audit
from scripts import bfs_owned_execution as own
from scripts import bfs_simulator_batch as batch
from scripts import bfs_simulator_recovery as recovery
from scripts.bfs_process import interruption_signals

GROUP_ID = recovery.GROUP_ID
SELECTORS = recovery.SUPPLEMENT_SELECTORS
GROUP = runner.RAW_BASE/(GROUP_ID+'.dispatch')
FOLDER = GROUP/'supplement'


def close(plan, code, preflight, lane_ref, exit_ref, *, reader,
          inspect=own.identity, leases=audit.lease_snapshot):
    """Read-only terminal observation, then validate and exclusively publish."""
    audit.require(not (GROUP/'supplement.readback.json').exists()
                  and not (FOLDER/'terminal-validation.json').exists(), 'supplement audit already attempted')
    # This durable marker also forbids retry after any failed read or observation.
    audit.write_new(FOLDER/'audit-attempt.json', {'created':'2026-09-27','started':own.stamp(),'code_commit':code})
    driver_ref=audit.reference(FOLDER/'driver.json'); driver=reader.json(driver_ref,4*1024**2)
    audit.require(driver.get('id')==GROUP_ID+'.supplement'
                  and driver.get('kind')=='supervision_supplement'
                  and driver.get('standard_proof_kind') is False
                  and driver.get('state')=='complete' and driver.get('returncode')==0
                  and driver.get('code_commit')==code
                  and driver.get('runtime')==runner.campaign_runtime(code)
                  and driver.get('runtime_sha256')==batch.runtime_identity()
                  and driver.get('pytest')==runner.pytest_identity()
                  and driver.get('python_environment')==runner.PYTHON_INPUTS,
                  'supplement driver/runtime identity differs')
    reader.raw(driver['runtime']['python']); reader.raw(driver['pytest']['module'])
    begin,end=map(batch.stamp,(driver['started'],driver['outer_deadline']))
    lane=reader.json(lane_ref)['socket_lane']; outer=reader.json(exit_ref,32)
    audit.require(type(outer) is int and outer==0 and type(lane.get('node')) is int
                  and lane['node'] in (0,1) and type(lane.get('lease_generation')) is int
                  and lane['lease_generation']>0, 'supplement helper exit or lane differs')
    proc=driver['process_observations']; rows={}
    def include(items):
        audit.require(isinstance(items,list) and len(items)<=own.MAX_IDENTITIES,'supplement identity list exceeds bound')
        for item in items: rows[audit.identity(item)]=item
        audit.require(len(rows)<=own.MAX_IDENTITIES,'supplement identity union exceeds bound')
    include(proc['ancestry']);include(proc['owned_processes'])
    include([proc['driver_identity'],proc['pane_identity']]);include(driver['cleanup']['observed'])
    for stage in driver['stages']:
        include([stage['identity']]);include(stage['cleanup']['observed'])
    for line in reader.raw(driver['resource_samples'],64*1024**2).splitlines():
        include(json.loads(line,object_pairs_hook=audit.unique)['processes'])
    pane=audit.identity(proc['pane_identity']); snapshots=[]; processes=[]; times=[]
    def observe():
        snapshots.append(leases(lane['node'],lane['lease_generation'],lane,begin,end))
        processes.append(audit.process_snapshot(rows,pane,inspect));times.append(own.stamp())
    audit.require(batch.stamp(own.stamp())>=max(batch.stamp(driver['finished']),batch.stamp(lane['ended_utc'])),
                  'supplement helper has not finished')
    observe()
    ledger=audit.ledger_check(reader,audit.reference(FOLDER/'cleanup-ledger.json'),driver,begin,end)
    for name in ('pytest.stdout','pytest.stderr','junit.xml'):reader.raw(audit.reference(FOLDER/name))
    reader.json(preflight);reader.recheck();observe();reader.check()
    terminal={'format':'swdb.bfs.supplement-terminal.v1','id':driver['id'],'state':'complete',
        'code_commit':code,'observed_at':own.stamp(),'driver':driver_ref,'lane':lane_ref,'outer_exit':exit_ref,
        'lease_generation':lane['lease_generation'],'lease_released':True,'complete_retained_identity_union':True,
        'owned_processes':processes[-1],'process_observations':processes,'lease_observations':snapshots,
        'observation_times':times,'cleanup_ledger':ledger,
        'cleanup_state':'terminal_no_live_owned_processes' if any(r['state']=='Z' for r in processes[-1]) else 'terminal_and_reaped',
        'auditor':audit.reference(__file__),'evidence_kind':'contract_fixture','empirical_evidence':False}
    audit.write_new(FOLDER/'terminal-validation.json',terminal)
    value={'format':'swdb.bfs.supervision-supplement.v1','state':'passed','code_commit':code,
        'runtime_sha256':driver['runtime_sha256'],'returncode':0,'started':driver['started'],'finished':driver['finished'],
        'audited_at':own.stamp(),'command':driver['command'],'selectors':SELECTORS,
        'terminal_audit':audit.reference(FOLDER/'terminal-validation.json'),
        'stdout':audit.reference(FOLDER/'pytest.stdout'),'stderr':audit.reference(FOLDER/'pytest.stderr'),
        'junit':audit.reference(FOLDER/'junit.xml')}
    admission={'code_commit':code,'runtime_sha256':driver['runtime_sha256'],
        'python':{'path':driver['command'][0]},'preparation_reservation':{'preflight':preflight,'finished':own.stamp()}}
    target=GROUP/'supplement.readback.json'
    recovery._validate_supplement_value(plan,admission,{'path':str(target)},value)
    reader.recheck();reader.check()
    audit.require(driver['runtime']==runner.campaign_runtime(code)
                  and driver['runtime_sha256']==batch.runtime_identity()
                  and driver['pytest']==runner.pytest_identity(), 'supplement runtime changed during audit')
    # A staged receipt is retained on deadline failure. Only the final hard link
    # publishes a successful result, after all validation and bounded fsync.
    staging=GROUP/'supplement.readback.staging.json';audit.write_new(staging,value);reader.check()
    os.link(staging,target)
    try:
        fd=os.open(GROUP,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        reader.check()
    except BaseException:
        if target.stat().st_ino==staging.stat().st_ino:target.unlink()
        raise
    return audit.reference(target)


def main():
    global GROUP_ID, SELECTORS, GROUP, FOLDER
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--lease-recovery',action='store_true');group.add_argument('--seal-recovery',action='store_true');group.add_argument('--protocol-recovery',action='store_true')
    parser.add_argument('mode',choices=('run','audit'));parser.add_argument('--expected-commit',required=True)
    parser.add_argument('--python-sha256',required=True);parser.add_argument('--pytest-version',required=True)
    parser.add_argument('--pytest-sha256',required=True)
    parser.add_argument('--outer-started');parser.add_argument('--outer-deadline')
    parser.add_argument('--pane-pid',type=int);parser.add_argument('--pane-start-ticks',type=int)
    parser.add_argument('--lane',type=int,choices=(0,1))
    for name in ('preflight','lane-receipt','outer-exit'):
        parser.add_argument('--'+name);parser.add_argument('--'+name+'-sha256')
    args=parser.parse_args();audit_end=time.monotonic()+60
    key='t15-lease-recovery' if args.lease_recovery else 't15-supervision-recovery'
    if args.protocol_recovery:
        key='t16-protocol-recovery'
        GROUP_ID, SELECTORS = recovery.PROTOCOL_GROUP_ID, recovery.PROTOCOL_SUPPLEMENT_SELECTORS
        GROUP=runner.RAW_BASE/(GROUP_ID+'.dispatch');FOLDER=GROUP/'supplement'
    elif args.seal_recovery:
        key='t16-seal-recovery'
        GROUP_ID, SELECTORS = recovery.SEAL_GROUP_ID, recovery.SEAL_SUPPLEMENT_SELECTORS
        GROUP=runner.RAW_BASE/(GROUP_ID+'.dispatch');FOLDER=GROUP/'supplement'
    elif args.lease_recovery:
        GROUP_ID, SELECTORS = recovery.LEASE_GROUP_ID, recovery.LEASE_SUPPLEMENT_SELECTORS
        GROUP=runner.RAW_BASE/(GROUP_ID+'.dispatch');FOLDER=GROUP/'supplement'
    audit.require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10'
                  and Path('/data1/yanruj') in ROOT.parents,'supplement requires mbit10 data1 runtime')
    audit.require(sys.flags.no_user_site and not sys.flags.optimize
                  and all(os.environ.get(k)==v for k,v in runner.PYTHON_INPUTS.items()),'supplement Python environment differs')
    audit.require(own.file_hash(Path(sys.executable).resolve())==args.python_sha256,'supplement Python changed')
    test_runtime=runner.pytest_identity()
    audit.require(test_runtime['version']==args.pytest_version and test_runtime['module']['sha256']==args.pytest_sha256,
                  'supplement pytest changed')
    runtime=runner.campaign_runtime(args.expected_commit)
    audit.require(GROUP==GROUP.resolve() and GROUP.is_dir(),'supplement group root missing or unsafe')
    resource.setrlimit(resource.RLIMIT_AS,(runner.LIMIT_BYTES,runner.LIMIT_BYTES))
    if args.mode=='run':
        begin,end=map(batch.stamp,(args.outer_started,args.outer_deadline))
        deadline=time.monotonic()+(end-datetime.now(own.ET)).total_seconds()
        audit.require(type(args.pane_pid) is int and args.pane_pid>0 and type(args.pane_start_ticks) is int
                      and args.pane_start_ticks>0,'supplement pane identity missing')
        with interruption_signals():
            runner.execute_supplement(FOLDER,begin,end,deadline,args.expected_commit,runtime,
                {'pid':args.pane_pid,'start_ticks':args.pane_start_ticks},args.lane,test_runtime)
    else:
        plan=json.loads((batch.PLAN_DIR/(recovery.IDS[key]+'.json')).read_text())
        batch.validate_plan(plan,key)
        def ref(name):return {'path':getattr(args,name),'sha256':getattr(args,name+'_sha256')}
        print(json.dumps(close(plan,args.expected_commit,ref('preflight'),ref('lane_receipt'),ref('outer_exit'),
                               reader=audit.Reader(audit_end))))


if __name__=='__main__':main()
