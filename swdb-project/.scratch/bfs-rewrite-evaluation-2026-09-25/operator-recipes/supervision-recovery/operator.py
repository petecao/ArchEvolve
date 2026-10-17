#!/usr/bin/env python3
"""Fixed 600-second Linux proof group operator. Created 2026-09-27 ET.

Operational orchestration only: child ownership remains in the existing runners.
No retries, scientific workloads, runtime edits, or standard third proof kind.
"""
import argparse
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy
import shlex
import socket
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

LEASE_ROOT = Path('/data1/yanruj/lact-host-lease')
ET = ZoneInfo('America/New_York')
BASE = Path('/data/yanruj/EvolveSWDB_runs')
ID = 'bfs-supervision-recovery-linux-20260926-a1'
GROUP = BASE/(ID+'.dispatch')
IDS = {'owned_cleanup':'bfs-simulator-owned-linux-20260926-a5',
       'dx100_interruption':'bfs-simulator-interruption-linux-20260926-a5'}
ROOTS = [p for name in IDS.values() for p in (BASE/name, BASE/(name+'.dispatch'))]+[GROUP]
KINDS = ('supplement','owned_cleanup','dx100_interruption')
ENV_REMOVE = ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE','PYTHONOPTIMIZE',
              'PYTEST_ADDOPTS','PYTEST_PLUGINS','LD_PRELOAD','LD_LIBRARY_PATH')


def require(value, reason):
    if not value: raise RuntimeError(reason)


def now(): return datetime.now(ET)
def stamp(): return now().isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path':str(path),'sha256':sha(path)}
def read(path): return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def remaining(end, reserve=0, at=None):
    seconds=(datetime.fromisoformat(end)-(at or now())).total_seconds()-reserve
    require(math.isfinite(seconds) and seconds>0,'original deadline exhausted')
    return seconds


def environment():
    env={k:v for k,v in os.environ.items() if k not in ENV_REMOVE}
    env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PATH='/usr/bin:/bin')
    return env


def load_config(path):
    c=read(path)
    if c.get('manifest') and not Path(c['manifest']).is_absolute():
        c['manifest']=str(path.resolve().parent/c['manifest'])
    for key in ('runtime','commit','python','python_sha256','pytest_version','pytest_sha256',
                'manifest','manifest_sha256','helper','helper_sha256','hostlock','hostlock_sha256',
                'helper_upstream_comparison','operator_sha256','node'):
        require(c.get(key) is not None,'unresolved configuration: '+key)
    require(type(c['node']) is int and c['node'] in (0,1),'invalid prospective node')
    require(re.fullmatch('[0-9a-f]{40}',c['commit']) is not None,'invalid runtime commit')
    for key in ('python_sha256','pytest_sha256','manifest_sha256','helper_sha256','hostlock_sha256','operator_sha256'):
        require(re.fullmatch('[0-9a-f]{64}',c[key]) is not None,'invalid hash: '+key)
    require(sha(__file__)==c['operator_sha256'],'operator changed')
    require(Path(c['runtime']).is_absolute() and Path('/data1/yanruj') in Path(c['runtime']).parents,'runtime outside data1')
    return c


def guard(c):
    """Only stdlib is loaded until the complete Git-exported inventory matches."""
    root=Path(c['runtime']);require(root==root.resolve(),'unsafe runtime root')
    require(sha(c['manifest'])==c['manifest_sha256'],'manifest changed')
    manifest=read(c['manifest']);require(manifest['commit']==c['commit'],'manifest commit differs')
    rows=manifest['files'];require(isinstance(rows,dict) and 0<len(rows)<=8192,'invalid inventory')
    actual=set(); walked=0; deadline=time.monotonic()+15
    for folder,dirs,files in os.walk(root,followlinks=False):
        walked+=1;require(walked<=8192 and time.monotonic()<deadline,'runtime inventory observation exceeded bound')
        if Path(folder)==root: dirs[:]=[d for d in dirs if d!='.git'];files=[f for f in files if f!='.git']
        for name in dirs+files: require(not (Path(folder)/name).is_symlink(),'symlink in runtime')
        for name in files:
            path=Path(folder)/name; rel=str(path.relative_to(root));actual.add(rel)
            require(rel in rows and path.stat().st_size==rows[rel]['bytes'] and sha(path)==rows[rel]['sha256'],'runtime file changed: '+rel)
        require(len(actual)<=8192,'runtime inventory exceeds bound')
    require(actual==set(rows),'missing runtime file')
    got=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],timeout=5,text=True).strip()
    require(got==c['commit'],'runtime HEAD differs')
    require(sha(Path(c['python']).resolve())==c['python_sha256'],'Python changed')


def free_lane(c):
    require(sha(c['helper'])==c['helper_sha256'] and sha(c['hostlock'])==c['hostlock_sha256'],'helper bytes changed')
    comparison=c['helper_upstream_comparison'];require(comparison.get('reviewed') is True and comparison.get('host_subtree_equal') is True,'helper upstream comparison unresolved')
    snapshots={}
    lease_root=Path(LEASE_ROOT)
    for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
        meta=read(lease_root/(name+'.meta.json'))
        lock=lease_root/(name+'.lease')
        with lock.open('r') as stream:
            try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);held=False;fcntl.flock(stream,fcntl.LOCK_UN)
            except BlockingIOError: held=True
        require(read(lease_root/(name+'.meta.json'))==meta,'lease metadata changed during kernel observation')
        require((meta['state']=='held')==held,'lease metadata/kernel disagree')
        snapshots[name]={'metadata':meta,'kernel_held':held}
        if name in ('mbit10-evaluation','mbit10-evaluation-node'+str(c['node'])):
            require(not held and meta['state']=='released','prospective lane unavailable')
    return snapshots


def capacity(c):
    result={}
    for path,reserve in ((BASE,30*1024**3),(Path('/data1'),10*1024**3)):
        fs=os.statvfs(path);available=fs.f_bavail*fs.f_frsize
        require(available>=reserve,'insufficient free disk reserve');result[str(path)]=available
    # The caller completed guard(c); reuse the pinned capacity estimator.
    estimator=runpy.run_path(str(Path(c['runtime'])/'scripts/dx100_capacity.py'))['capacity']
    inputs={'global':Path('/proc/meminfo').read_text(),
            'node':Path('/sys/devices/system/node/node'+str(c['node'])+'/meminfo').read_text(),
            'zones':Path('/proc/zoneinfo').read_text()}
    estimate=estimator(inputs['node'],inputs['zones'],inputs['global'],c['node'],os.sysconf('SC_PAGE_SIZE'))
    require(estimate['global_available_kib']*1024>=24*1024**3
            and estimate['estimated_available_kib']*1024>=20*1024**3,'insufficient available memory')
    return {**result,'inputs':inputs,'estimate':estimate,'required_node_bytes':20*1024**3,
            'required_global_bytes':24*1024**3,'load_average':list(os.getloadavg())}



def common(c):
    return ['--expected-commit',c['commit'],'--python-sha256',c['python_sha256'],
            '--pytest-version',c['pytest_version'],'--pytest-sha256',c['pytest_sha256']]


def invocation(c, config, script, args):
    return [c['python'],'-I','-B',str(Path(__file__).resolve()),'invoke',str(config),script,*args]


def paths(kind):
    return (GROUP/'supplement',GROUP) if kind=='supplement' else (BASE/IDS[kind],BASE/(IDS[kind]+'.dispatch'))


def stage(c, config, kind, pane):
    guard(c);free_lane(c);capacity(c)
    raw,dispatch=paths(kind)
    require(not raw.exists(),'stage root exists; no retry')
    begin=now();end=begin+timedelta(seconds=90)
    fields=Path('/proc/'+str(pane)+'/stat').read_text().rsplit(')',1)[1].split()
    ticks=int(fields[19]);prefix='supplement-' if kind=='supplement' else ''
    lane=dispatch/(prefix+'lane.json');exit_path=dispatch/(prefix+'outer.exit')
    write(dispatch/(prefix+'launch.json'),{'outer_started':begin.isoformat(),'outer_deadline':end.isoformat(),'pane_identity':{'pid':pane,'start_ticks':ticks}})
    args=common(c)+['--outer-started',begin.isoformat(),'--outer-deadline',end.isoformat(),'--pane-pid',str(pane),'--pane-start-ticks',str(ticks),'--lane',str(c['node'])]
    script='scripts/bfs_supervision_supplement.py' if kind=='supplement' else 'scripts/bfs_linux_fixture.py'
    args=[('run' if kind=='supplement' else kind),*args]
    command=['timeout','--signal=TERM','--kill-after=30s',str(remaining(end.isoformat(),30))+'s',
             'bash',c['helper'],str(c['node']),ID+'.supplement' if kind=='supplement' else IDS[kind],
             '--lease-timeout-s','0','--record',str(lane),'--',*invocation(c,config,script,args)]
    with (dispatch/(prefix+'outer.stdout')).open('xb') as out,(dispatch/(prefix+'outer.stderr')).open('xb') as err:
        result=subprocess.run(command,stdout=out,stderr=err,env=environment()).returncode
    write(exit_path,result)
    require(result==0,'fixture helper failed; retained failure, no retry')


def audit_stage(c, config, kind, end):
    raw,dispatch=paths(kind);prefix='supplement-' if kind=='supplement' else ''
    lane=dispatch/(prefix+'lane.json');exit_path=dispatch/(prefix+'outer.exit')
    require(read(exit_path)==0,'stage failed')
    if kind=='supplement':
        args=['audit',*common(c)]
        for name,path in [('preflight',GROUP/'preflight.json'),('lane-receipt',lane),('outer-exit',exit_path)]:args += ['--'+name,str(path),'--'+name+'-sha256',sha(path)]
        script='scripts/bfs_supervision_supplement.py'
    else:
        args=['standard',kind,'--expected-supervisor-commit',c['commit'],'--node',str(c['node']),
              '--generation',str(read(lane)['socket_lane']['lease_generation'])]
        for name,path in [('pending',raw/'proof.pending.json'),('lane',lane),('outer-exit',exit_path),('ledger',raw/'cleanup-ledger.json')]:args += ['--'+name,str(path),'--'+name+'-sha256',sha(path)]
        script='scripts/bfs_linux_fixture_audit.py'
    require(remaining(end)>=60,'group cannot admit complete audit allowance')
    began=now();clock=time.monotonic()
    write(dispatch/(prefix+'audit-wrapper-attempt.json'),{'started':began.isoformat()})
    with (dispatch/(prefix+'audit.stdout')).open('xb') as out,(dispatch/(prefix+'audit.stderr')).open('xb') as err:
        result=subprocess.run(['timeout','--signal=TERM','--kill-after=1s','59s',*invocation(c,config,script,args)],stdout=out,stderr=err,env=environment()).returncode
    finished=now();wall=time.monotonic()-clock
    write(GROUP/(kind+'.audit-wrapper.exit'),result)
    require(result==0 and wall<=60,'audit failed or exceeded original bound; no retry')
    if kind!='supplement':
        proof=read(raw/'proof.json');proof_ref=ref(raw/'proof.json')
        completion={'state':'complete','returncode':0,'outer_seconds':60,'host_wall_s':wall,
                    'proof':proof_ref,'terminal_audit':proof['terminal_audit'],
                    'audit_started':began.isoformat(),'audit_finished':finished.isoformat()}
        write(dispatch/'audit-receipt.json',completion)
        write(GROUP/(kind+'.readback.json'),{'id':IDS[kind],'wrapper_returncode':0,
            'wrapper_exit':ref(GROUP/(kind+'.audit-wrapper.exit')),'audit_receipt':ref(dispatch/'audit-receipt.json'),
            'proof':proof_ref,'terminal_audit':proof['terminal_audit'],'finished':stamp()})


def run(c, config, outer_started, outer_deadline, ownership):
    require(socket.gethostname().split('.')[0]=='mbit10' and sys.platform=='linux','requires mbit10')
    require(os.environ.get('TMUX'),'requires a named tmux caller')
    began=datetime.fromisoformat(outer_started);end=outer_deadline
    require(datetime.fromisoformat(end)-began==timedelta(seconds=600) and 0<=(now()-began).total_seconds()<=5,'group original entry clock invalid')
    guard(c);leases=free_lane(c);resources=capacity(c)
    require(all(not p.exists() for p in ROOTS),'group root exists; no retry')
    final=BASE/(ID+'.final.json');require(not final.exists(),'final receipt exists')
    require(remaining(end)>=450,'preflight consumed fixed stage allowances');GROUP.mkdir();ownership['created']=True
    write(GROUP/'preflight.json',{'id':ID,'code_commit':c['commit'],'observed_at':began.isoformat(),
        'outer_deadline':end,'config':ref(config),'leases':leases,'capacity':resources,'evidence_kind':'contract_fixture'})
    for index,kind in enumerate(KINDS):
        require(remaining(end)>=(len(KINDS)-index)*150,'insufficient group time for fixed remaining stages')
        raw,dispatch=paths(kind)
        if kind!='supplement':dispatch.mkdir()
        session=ID+'-'+kind
        require(subprocess.run(['tmux','has-session','-t',session],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'stage session exists')
        command=shlex.join([c['python'],'-I','-B',str(Path(__file__).resolve()),'stage',str(config),kind])+' "$BASHPID" >'+shlex.quote(str(dispatch/(kind+'.pane.stdout')))+' 2>'+shlex.quote(str(dispatch/(kind+'.pane.stderr')))
        subprocess.run(['tmux','new-session','-d','-s',session,'bash -c '+shlex.quote(command)],check=True,env=environment())
        wait_end=time.monotonic()+95
        while subprocess.run(['tmux','has-session','-t',session],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
            require(time.monotonic()<wait_end and remaining(end)>0,'stage pane exceeded bound; retain failure for owned recovery')
            time.sleep(.1)
        audit_stage(c,config,kind,end)
    guard(c)
    sys.path.insert(0,c['runtime'])
    from scripts import bfs_simulator_batch as batch
    from scripts import bfs_linux_fixture_audit as auditor
    snapshots=[]
    for kind in KINDS:
        raw,dispatch=paths(kind)
        terminal=read(raw/('terminal-validation.json' if kind=='supplement' else 'terminal-audit.json'))
        driver=read(terminal['driver']['path']);pane=driver['process_observations']['pane_identity']
        union={(r['pid'],r['start_ticks']):r for r in terminal['owned_processes']}
        snapshots.append({'kind':kind,'observed_at':stamp(),'processes':auditor.process_snapshot(union,(pane['pid'],pane['start_ticks']))})
    write(GROUP/'final-process-closure.json',snapshots)
    plan=read(Path(c['runtime'])/'.scratch/bfs-rewrite-evaluation-2026-09-25/requests/bfs-t15-supervision-recovery-simulator-batch-20260926-a1.json')
    actual={'preflight':ref(GROUP/'preflight.json'),'finished':stamp(),
      'audits':{k:ref(paths(k)[1]/'audit-receipt.json') for k in IDS},
      'auditor_readbacks':{k:ref(GROUP/(k+'.readback.json')) for k in IDS},
      'supplement':ref(GROUP/'supplement.readback.json'),'raw_bytes':batch.allocated_bytes(ROOTS)}
    admission={'code_commit':c['commit'],'runtime_sha256':batch.runtime_identity(),'python':{'path':c['python']},
       'prepared_at':stamp(),'preparation_reservation':actual,'linux_cleanup_tests':[ref(paths(k)[0]/'proof.json') for k in IDS]}
    batch.validate_preparation_reservation(plan,admission)
    require(remaining(end)>0,'group final readback exceeded bound')
    write(final,{'format':'swdb.bfs.supervision-group-closure.v1','created':'2026-09-27','state':'complete',
                 'finished':stamp(),'admission_fragment':admission,'charged_roots':[str(p) for p in ROOTS],
                 'scope':'Contract fixtures only; no empirical acceptance or gain.'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('run','stage','invoke'));parser.add_argument('config',type=Path)
    args,rest=parser.parse_known_args();c=load_config(args.config)
    if args.mode=='run':
        require(len(rest)==2,'original group clocks required')
        ownership={'created':False}
        try:run(c,args.config.resolve(),rest[0],rest[1],ownership)
        except BaseException as exc:
            if ownership['created'] and not (GROUP/'operator-failure.json').exists():
                try:
                    write(GROUP/'operator-failure.json',{'created':'2026-09-27','observed_at':stamp(),
                        'state':'failed','error_type':type(exc).__name__,'error':str(exc)[:4096],'retry_allowed':False})
                except Exception as persistence_error:
                    print('Failure receipt could not be retained: '+str(persistence_error),file=sys.stderr)
            raise
    elif args.mode=='stage':require(len(rest)==2 and rest[0] in KINDS,'invalid stage arguments');stage(c,args.config.resolve(),rest[0],int(rest[1]))
    else:
        require(rest and rest[0] in ('scripts/bfs_supervision_supplement.py','scripts/bfs_linux_fixture.py','scripts/bfs_linux_fixture_audit.py'),'unapproved invocation')
        guard(c);script=Path(c['runtime'])/rest[0];sys.argv=[str(script),*rest[1:]];runpy.run_path(str(script),run_name='__main__')


if __name__=='__main__':main()
