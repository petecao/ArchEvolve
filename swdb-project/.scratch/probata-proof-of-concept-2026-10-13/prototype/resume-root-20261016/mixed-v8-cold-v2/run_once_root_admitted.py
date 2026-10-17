"""2026-10-16 ET. Exact once-admitted passive mixed V8 cold V2 orchestration.

Run only after lead25's source9 protected SSH window has fully settled.
No source/raw mutation or compiler/prover/native execution. All remote stdin
bytes are frozen and independently reviewed; exclusive token blocks retries.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
EVIDENCE=POC/'evidence'
PREFIX='t25-mixed-v8-cold-v2-'
SSH=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10']


def pin(path):
    b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def save(path,raw):
    with path.open('xb') as stream:stream.write(raw)


def document(name,value):
    path=EVIDENCE/(PREFIX+name+'-20261016.json')
    save(path,(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    return path


def invoke(name,remote,source,timeout,cap):
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
    try:
        done=subprocess.run([*SSH,*remote],input=source,capture_output=True,timeout=timeout)
        code=done.returncode;out=done.stdout;err=done.stderr;uncertain=False
    except subprocess.TimeoutExpired as exc:
        code=None;out=exc.stdout or b'';err=exc.stderr or b'';uncertain=True
    op=EVIDENCE/(PREFIX+name+'-stdout-20261016.json');ep=EVIDENCE/(PREFIX+name+'-stderr-20261016.txt')
    save(op,out);save(ep,err)
    receipt={'started_utc':started,'elapsed_seconds':time.monotonic()-clock,
        'argv':[*SSH,*remote],'exit_code':code,'uncertain_transport_result':uncertain,
        'stdin_sha256':hashlib.sha256(source).hexdigest(),'stdout':pin(op),'stderr':pin(ep),
        'within_output_cap':len(out)<=cap and len(err)<=65536}
    document(name+'-invocation',receipt)
    if not receipt['within_output_cap']:raise ValueError('retained output exceeded bound')
    return receipt,out


def check_scoped(receipt,raw):
    assert receipt['exit_code']==0
    value=json.loads(raw);assert value['scoped_preflight_pass']is True
    assert value['original_generation']==622 and value['source_commit']=='36266e101e0484f3c2cf5f3fae4322d5de648d85'
    for scan in value['scans']:
        for row in scan['exact_inherited_OS_PAM_helpers']:
            if 'current_query_transport'in row:
                b=row['current_query_transport']['daemon_binary']
                assert b['bytes']==925512 and b['sha256']=='95b291d957f87dd200796c4986c97b6f4d970e26ad620ec9174e69c13ec5c137'
    return value


def main():
    admission=EVIDENCE/'t25-mixed-v8-cold-v2-root-once-admission-20261016.json'
    assert pin(admission)['sha256']=='33397b1d1abdecdde54c4754fa064381b87e30afc6272d63b70d421c5db9e506'
    packet=HERE/'source-packet.json'
    assert pin(packet)['sha256']=='010dd0f6952bccfb21667adc4ddd390d96e2c3b388779c241a2b819a1b403a23'
    data=json.loads(packet.read_bytes())
    for row in data['inputs']+data['outputs']:assert pin(Path(row['path']))==row
    assert pin(HERE/'entry.py')['sha256']=='0f67a9ba2392976608431f8fff7ebfe3702b36b825529ff76867e710ef4cba42'
    assert pin(HERE/'command.json')['sha256']=='86bba4d6c76b40b4e035861175380e5151df3468233036a9461318b7ef567a48'
    preflight=HERE.with_name('mixed-v8-cold-v1')/'root-scoped-preflight-v1.py'
    assert pin(preflight)['sha256']=='47503408a206078d83d3dc4c50bbc04da19afd215aeed9118043e0752cef1095'
    check=b'''from pathlib import Path
import json,subprocess,datetime
env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','LC_ALL':'C'}
def call(a):return subprocess.check_output(a,text=True,timeout=10,env=env).strip()
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uptime':call(['/usr/bin/uptime']),'disk':call(['/usr/bin/df','-B1','/data1','/data']),'logged_sessions':len(call(['/usr/bin/who']).splitlines()),'leases':{},'sources':{}}
for name in ['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1']:
 p=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');v=json.loads(p.read_bytes());r['leases'][name]={'state':v['state'],'lease':v.get('lease')}
for p in ['/data1/yanruj/probata-resume-20261016-36266e10','/data1/yanruj/ArchEvolve']:
 a=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',p]
 r['sources'][p]={'branch':call(a+['rev-parse','--abbrev-ref','HEAD']),'commit':call(a+['rev-parse','HEAD'])}
print(json.dumps(r,sort_keys=True))
'''
    connection,raw=invoke('connection-preflight',['/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/python3','-I','-B','-'],check,45,65536)
    assert connection['exit_code']==0
    fresh=json.loads(raw);assert all(v['state']=='released' for v in fresh['leases'].values())
    pre_remote=['/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/python3','-I','-B','-']
    before,b=invoke('preflight-v3',pre_remote,preflight.read_bytes(),45,65536);check_scoped(before,b)
    document('actual-attempt',{'date':'2026-10-16 ET','entry':pin(HERE/'entry.py'),
        'admission':pin(admission),'preflight':before,'once_only':True,
        'lead25_protected_SSH_window_released_before_invocation':True})
    remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','200s','/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/python3','-I','-B','-']
    actual,a=invoke('actual',remote,(HERE/'entry.py').read_bytes(),215,2097152)
    after,b=invoke('postflight-v3',pre_remote,preflight.read_bytes(),45,65536)
    post=json.loads(b)if b else {};observed=json.loads(a)if a else {}
    good=(actual['exit_code']==2 and after['exit_code']==0 and post.get('scoped_preflight_pass')is True and
          len(observed.get('WP_contexts',[]))==6 and len(observed.get('CBMC_contexts',[]))==2 and
          observed.get('scientific_cold_acceptance')is False and observed.get('full_original_solver_task_files_retained')==0)
    report={'date':'2026-10-16 ET','status':'AVAILABLE_EVIDENCE_CAPTURED_EXPECTED_EXIT2'if good else 'REFUSAL_OR_UNCERTAIN_RETAINED_NO_RETRY',
        'admission':pin(admission),'entry':pin(HERE/'entry.py'),'command':pin(HERE/'command.json'),
        'preflight_script':pin(preflight),'connection':connection,'preflight':before,'actual':actual,'postflight':after,
        'actual_classification':observed.get('classification'),'actual_error':observed.get('error'),
        'scientific_or_full_task_source_Heap_Typed_body_caller_default_public_record_acceptance':False,
        'proof_compiler_native_verifier_solver_rerun':False,'remote_mutation':False}
    path=document('actual-execution',report);print(json.dumps(pin(path)))
    check_scoped(after,b)
    return 0 if good else 1


if __name__=='__main__':raise SystemExit(main())
