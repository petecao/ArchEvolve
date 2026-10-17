"""One actual R5->503f->928 export; parent keeps finite envelope and originals."""
import datetime, hashlib, json, os, shlex, subprocess
from pathlib import Path
BOOT = Path('/private/tmp/lanl14-invoke-reviewed-export-r5-20261008-a1.py')
SUP = Path('/private/tmp/lanl14-completed-metadata-supplier-r1-actual-20261008-a1/stdout.json')
MODE = Path('/private/tmp/lanl14-completed21-mode-actual-20261008-a1/remote-receipt.json')
CAPTURE = Path('/private/tmp/lanl14-reviewed-export-r5-actual-20261008-a1')
PRIMARY = 'de2a137c77bbc2ad5f5856e5e456617c47e51d21'
def digest(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,b):
    fd=os.open(CAPTURE/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        assert f.write(b)==len(b)
        f.flush();os.fsync(f.fileno())
    return {'path':str(CAPTURE/name),'bytes':len(b),'sha256':digest(b)}
sup=SUP.read_bytes();mode=MODE.read_bytes()
assert len(sup)==29107 and digest(sup)=='62d3f72960c96084840c03382b9057d06d9d43d90d249d0c6d1390ebc9a15ada'
assert len(mode)==30212 and digest(mode)=='8a838ddbfd636796350cb89b1ccdc759476bf26c970dc9aa9a0d868106be55ad'
s=json.loads(sup);m=json.loads(mode)
assert m['state']=='completed' and m['failure_type'] is None and m['completed_file_count']==21
assert m['scientific_admission'] is False and m['sealed'] is False
assert m['original_inputs']==s['original_completion_inputs']
target=['/data1/yanruj/lanl14-completed-source-controls-20261008-a1/export_invocation_r5.py',
        '--source-sha256','62808f732d3ca492c102bbeb0b0ccab5fcb6ed2c63efd088d8ccdac845d362b7']
for key,value in s['exact_derived_args'].items(): target.extend(['--'+key.replace('_','-'),str(value)])
target.extend(['--mode-receipt-sha256',digest(mode),'--mode-receipt',
               '/data/yanruj/EvolveSWDB_runs/lanl14-report-transfer-mode-administration-20261008-a1/receipt.json',
               '--expected-primary',PRIMARY,'--wrapper-upstream-commit',s['wrapper_upstream_commit'],
               '--metadata-deadline-s','600'])
assert s['exact_derived_args']['report_bytes']==68324111<=100*1024**2
# Whole actual R5 needs its 18,300s child wait plus two600s metadata segments.
#19800s gives300s bootstrap/transport margin; blocked filesystem duration remains unproved.
remote=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','19800s','/usr/bin/python3.12','-B','-',*target[1:]]
argv=['ssh','-oBatchMode=yes','-oConnectTimeout=20','mbit10',shlex.join(remote)]
body=BOOT.read_bytes()
assert len(body)==2970 and digest(body)=='e8cac76d47277618926b55181afe22cf4e9b0f656b649b11371b4c1d8aa95922'
compile(body,str(BOOT),'exec')
assert not os.path.lexists(CAPTURE)
os.mkdir(CAPTURE,0o700)
save('start.json',(json.dumps({'format':'swdb.lanl14-reviewed-export-r5-parent-start.v1','sealed':False,
    'started_utc':now(),'bootstrap':{'path':str(BOOT),'bytes':len(body),'sha256':digest(body)},
    'actual_transport_argv':argv,'actual_remote_outer_argv':remote,'selected_target_sys_argv':target,
    'execution_route':'Returned hash-verified R5 bytes compiled in same native Python-B process; R5 owns unchanged503f/928 child launch.',
    'metadata_deadline_s_each':600,'original_R5_child_wait_s':18300,'whole_GNU_outer_s':19800,
    'whole_GNU_KILL_allowance_s':60,'local_transport_wait_s':20040,'duration_sufficiency':'unproved',
    'expected_primary':PRIMARY,'report_representation':'plain; actual68324111B below100MiB',
    'original_mode_receipt_sha256':digest(mode),'scientific_admission':False,'reader_invoked':False},sort_keys=True)+'\n').encode())
code,out,err,failure=None,b'',b'',None
try:
    child=subprocess.run(argv,input=body,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20040,check=False)
    code,out,err=child.returncode,child.stdout,child.stderr
except subprocess.TimeoutExpired as exc:out,err,failure=exc.stdout or b'',exc.stderr or b'','TimeoutExpired'
except Exception as exc:failure=type(exc).__name__
stdout=save('stdout.json',out);stderr=save('stderr.txt',err)
result={'format':'swdb.lanl14-reviewed-export-r5-parent-exit.v1','sealed':False,'ended_utc':now(),
        'returncode':code,'failure_type':failure,'stdout':stdout,'stderr':stderr,
        'scientific_admission':False,'no_retry_or_remote_cleanup':True,'reader_invoked':False}
save('exit.json',(json.dumps(result,sort_keys=True)+'\n').encode())
print(json.dumps(result,sort_keys=True))
raise SystemExit(code if code is not None else 2)
