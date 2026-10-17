"""2026-10-16 ET. Local orchestration of the once-root-admitted passive probe.

Writes compact local evidence only. The remote stdin entry and scoped pre/post
scripts are transmitted byte-exact; no compiler/prover/native or raw mutation.
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
PREFIX='t25-owned-transfer10-encoding-v2-'
SSH=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10']


def pin(path):
    b=path.read_bytes()
    return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def save(path,raw):
    with path.open('xb') as stream:stream.write(raw)


def document(name,value):
    path=EVIDENCE/(PREFIX+name+'-20261016.json')
    save(path,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
    return path


def invoke(name,remote,source,timeout,cap):
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
    done=subprocess.run([*SSH,*remote],input=source,capture_output=True,timeout=timeout)
    out=EVIDENCE/(PREFIX+name+'-stdout-20261016.json')
    err=EVIDENCE/(PREFIX+name+'-stderr-20261016.txt')
    save(out,done.stdout);save(err,done.stderr)
    receipt={'started_utc':started,'elapsed_seconds':time.monotonic()-clock,
             'argv':[*SSH,*remote],'exit_code':done.returncode,
             'stdin_sha256':hashlib.sha256(source).hexdigest(),'stdout':pin(out),'stderr':pin(err),
             'within_output_cap':len(done.stdout)<=cap and len(done.stderr)<=65536}
    document(name+'-invocation',receipt)
    if not receipt['within_output_cap']:raise ValueError('retained output exceeded bound')
    return done,receipt


def main():
    admission=EVIDENCE/'t25-owned-transfer10-encoding-v2-root-admission-20261016.json'
    assert pin(admission)['sha256']=='7bc2b5e3bd34e3ebb969249ddb504ca404eb94745c8060abaa1ad6481fea4d8d'
    packet=json.loads((HERE/'source-packet.json').read_bytes())
    assert pin(HERE/'source-packet.json')['sha256']=='d06f9d08846cfe469d3673a7ebb9ad7d6b2c09d71bb8fef88ea79e055948aa10'
    for row in packet['inputs']+packet['outputs']:assert pin(Path(row['path']))==row
    entry=(HERE/'entry.py').read_bytes()
    assert hashlib.sha256(entry).hexdigest()=='1c6fbfb2026f4d4ba70610c1bd9cdfe83ee0b0e3a4b069bcad9d7bc51566fb2e'
    preflight=HERE.parent/'cold-g621-encoding-v1/root-admitted-scoped-preflight-v3.py'
    preflight_bytes=preflight.read_bytes()
    check=b'''from pathlib import Path
import json,os,subprocess,datetime
env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','LC_ALL':'C'}
def call(a):return subprocess.check_output(a,text=True,timeout=10,env=env).strip()
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uptime':call(['/usr/bin/uptime']),'disk':call(['/usr/bin/df','-B1','/data1','/data']),'logged_sessions':len(call(['/usr/bin/who']).splitlines()),'leases':{},'sources':{}}
for name in ['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1']:
 p=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');v=json.loads(p.read_bytes());r['leases'][name]={'state':v['state'],'lease':v.get('lease')}
for p in ['/data1/yanruj/probata-resume-20261016-d7f685c6','/data1/yanruj/ArchEvolve']:
 a=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',p]
 r['sources'][p]={'branch':call(a+['rev-parse','--abbrev-ref','HEAD']),'commit':call(a+['rev-parse','HEAD'])}
print(json.dumps(r,sort_keys=True))
'''
    connection,connection_receipt=invoke('connection-preflight',
        ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/python3','-I','-B','-'],check,45,65536)
    assert connection.returncode==0
    pre_remote=['/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/timeout','--signal=TERM','--kill-after=5s','35s','/usr/bin/python3','-I','-B','-']
    before,before_receipt=invoke('preflight-v3',pre_remote,preflight_bytes,45,65536)
    assert before.returncode==0 and json.loads(before.stdout)['scoped_preflight_pass'] is True
    # This local exclusive attempt token is written before the sole invocation.
    # An uncertain transport result is not automatically retried.
    document('actual-attempt',{'date':'2026-10-16 ET','entry':pin(HERE/'entry.py'),
        'admission':pin(admission),'preflight':before_receipt,'once_only':True})
    remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','90s','/usr/bin/env','-i',
            'HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/python3','-I','-B','-']
    done,actual_receipt=invoke('actual',remote,entry,105,262144)
    after,after_receipt=invoke('postflight-v3',pre_remote,preflight_bytes,45,65536)
    observed=json.loads(done.stdout)
    good=(done.returncode==2 and after.returncode==0 and json.loads(after.stdout)['scoped_preflight_pass'] is True
          and observed['tasks_observed']==20 and observed['selected_pre_post_equal'] is True
          and observed['scientific_acceptance'] is False and observed['full_semantic_adoption'] is False)
    report={'date':'2026-10-16 ET','status':'ACTUAL_ONCE_METADATA_CAPTURED_POSTFLIGHT_PASSED' if good else 'ACTUAL_CAPTURE_REQUIRES_REVIEW',
            'admission':pin(admission),'entry':pin(HERE/'entry.py'),'command':pin(HERE/'command.json'),
            'preflight_script':pin(preflight),'connection':connection_receipt,'preflight':before_receipt,
            'actual':actual_receipt,'postflight':after_receipt,'all_selected20_input_pre_post_equal':observed.get('selected_pre_post_equal'),
            'mathematical_source_body_Typed_caller_default_or_public_record_acceptance':False,
            'proof_native_compiler_verifier_solver_rerun':False,'remote_raw_mutation':False,
            'OS_PAM_current_SSH_identity_TCB':'Exact preflightV3 only; unrelated unreadables and unresolved PID/descriptor races refuse.'}
    path=document('actual-execution',report)
    print(json.dumps(pin(path)))
    return 0 if good else 1


if __name__=='__main__':raise SystemExit(main())
