"""2026-10-16 ET. Local once-only exact root-admitted1433 retirement orchestration.

Run only after ticket28 reports complete protected SSH-window settlement.
Remote stdin/argv remain byte-exact to the independently admitted packet.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
EV=POC/'evidence'
PREFIX='retire-1433-source-v1-'
SSH=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10']


def pin(path):
    b=path.read_bytes()
    return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def save(name,value):
    p=EV/(PREFIX+name+'-20261016.json')
    with p.open('xb')as stream:stream.write((json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    return p


def invoke(name,argv,source,timeout,stdout_cap,stderr_cap):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
    try:
        done=subprocess.run(argv,input=source,capture_output=True,timeout=timeout)
        code=done.returncode;out=done.stdout;err=done.stderr;uncertain=False
    except subprocess.TimeoutExpired as exc:
        code=None;out=exc.stdout or b'';err=exc.stderr or b'';uncertain=True
    op=EV/(PREFIX+name+'-stdout-20261016.json');ep=EV/(PREFIX+name+'-stderr-20261016.txt')
    for p,b in [(op,out),(ep,err)]:
        with p.open('xb')as stream:stream.write(b)
    r={'started_utc':start,'elapsed_seconds':time.monotonic()-clock,'argv':argv,
       'stdin_sha256':hashlib.sha256(source).hexdigest(),'exit_code':code,
       'uncertain_transport_result':uncertain,'stdout':pin(op),'stderr':pin(ep),
       'within_output_cap':len(out)<=stdout_cap and len(err)<=stderr_cap}
    save(name+'-invocation',r)
    return r,out


def main():
    admission=EV/'retire-1433-source-v1-root-admission-20261016.json'
    assert pin(admission)['sha256']=='c0794e17ed980b34636b818c05eedda5aa7e45ff052777599f837beb2e663938'
    assert pin(HERE/'source-packet.json')['sha256']=='64005ca55bab1ca5b48b75843e4d19d00155a4af399a0be05576af63c912b1ef'
    packet=json.loads((HERE/'source-packet.json').read_bytes())
    for row in packet['files']:assert pin(Path(row['path']))==row
    assert pin(HERE/'retirement.py')['sha256']=='80210f84476b23add326c10912ebf84e6fbf3965cb1ab04967b9cad4f40a41b2'
    assert pin(HERE/'command.json')['sha256']=='3e7c37e45c6f8975fd6d997eed5443903c79dd8f7e3a63de5e2e8d1a16309cb3'
    command=json.loads((HERE/'command.json').read_bytes())
    check=b'''from pathlib import Path
import datetime,json,subprocess
env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def call(a):return subprocess.check_output(a,text=True,timeout=10,env=env).strip()
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uptime':call(['/usr/bin/uptime']),'disk':call(['/usr/bin/df','-B1','/data1','/data']),'logged_sessions':len(call(['/usr/bin/who']).splitlines()),'leases':{},'sources':{}}
for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
 p=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');v=json.loads(p.read_bytes());r['leases'][name]={'state':v['state'],'lease':v.get('lease')}
for p in ('/data1/yanruj/probata-resume-20261016-1433b8f5','/data1/yanruj/ArchEvolve'):
 a=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',p];r['sources'][p]={'branch':call(a+['rev-parse','--abbrev-ref','HEAD']),'commit':call(a+['rev-parse','HEAD'])}
print(json.dumps(r,sort_keys=True))
'''
    pre,out=invoke('connection-preflight',[*SSH,'/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/python3','-I','-B','-'],check,45,65536,16384)
    assert pre['exit_code']==0 and pre['within_output_cap']
    fresh=json.loads(out);assert all(r['state']=='released'for r in fresh['leases'].values())
    assert fresh['sources']['/data1/yanruj/probata-resume-20261016-1433b8f5']=={'branch':'HEAD','commit':'1433b8f58baa63538d1e8aa8a33d9ce566826407'}
    # Exclusive token BEFORE the sole mutation-bearing SSH attempt. A failed or
    # uncertain transport result is retained and must never be retried here.
    save('actual-attempt',{'date':'2026-10-16 ET','entry':pin(HERE/'retirement.py'),
        'command':pin(HERE/'command.json'),'root_admission':pin(admission),'once_only':True,
        'protected_SSH_window_released_by_ticket28_before_invocation':True})
    actual,out=invoke('actual',command['argv'],(HERE/'retirement.py').read_bytes(),320,65536,16384)
    observed=json.loads(out)if out else {}
    success=(actual['exit_code']==0 and actual['within_output_cap'] and
             observed.get('classification')=='EXACT_CLEAN_DETACHED1433_SOURCE_RETIRED_ALL_RAW_RETAINED' and
             observed.get('raw_pre_post_equal')is True)
    report={'date':'2026-10-16 ET','status':'RETIRED_EXACT1433_ALL_RAW_RETAINED'if success else 'ACTUAL_REFUSAL_OR_UNCERTAIN_PRESERVED_NO_RETRY',
            'root_admission':pin(admission),'entry':pin(HERE/'retirement.py'),'command':pin(HERE/'command.json'),
            'connection_preflight':pre,'actual':actual,'retirement_report':observed,
            'scientific_or_source_admission':False,'new_compiler_native_verifier_solver_job':False}
    path=save('actual-execution',report);print(json.dumps(pin(path)));return 0 if success else 1


if __name__=='__main__':raise SystemExit(main())
