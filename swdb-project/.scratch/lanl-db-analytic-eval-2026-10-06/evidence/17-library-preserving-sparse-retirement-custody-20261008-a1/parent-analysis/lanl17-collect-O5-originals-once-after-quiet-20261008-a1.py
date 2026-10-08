import datetime,hashlib,json,os,pathlib,subprocess,time
P=pathlib.Path
os.umask(0o077)
now=datetime.datetime.now(datetime.timezone.utc)
quiet_end=datetime.datetime.fromisoformat('2026-10-08T08:44:59.215985+00:00')
assert now>=quiet_end, 'O5 original quiet window has not ended'
source=P('/private/tmp/lanl_read_detached_passive_observer_administration_originals_20261008_a5_r2.py')
b=source.read_bytes();assert len(b)==4820 and hashlib.sha256(b).hexdigest()=='dee4d37d7abd2071d9ab9a536d9aa24bad075ebc96beedb44ffcf984347ea91d'
stem=P('/private/tmp/lanl17-detached-passive-observer-O5-original-custody-capture-actual-20261008-a1')
argv=['ssh','-T','-o','BatchMode=yes','mbit10','/usr/bin/timeout','--signal=TERM','--kill-after=10','90','/usr/bin/python3.12','-B','-s','-P','-','--control-directory','/data1/yanruj/lanl17-detached-observer-a5']
def pin(p):
 data=p.read_bytes();return {'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def publish(suffix,d):
 p=P(str(stem)+suffix)
 with p.open('x') as f:json.dump(d,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 assert (p.stat().st_mode&0o777)==0o600
 return p
publish('.start.json',{'format':'swdb.parent-original-observer-custody-capture-start.v1','sealed':False,'started_utc':now.isoformat(),'argv':argv,'source':pin(source),'quiet_end_original_utc':quiet_end.isoformat(),'source_stdin_not_imported_locally':True})
out=P(str(stem)+'.json');err=P(str(stem)+'.stderr');tick=time.monotonic();timeout=False
with out.open('xb') as fo,err.open('xb') as fe:
 try:cp=subprocess.run(argv,input=b,stdout=fo,stderr=fe,timeout=150);rc=cp.returncode
 except subprocess.TimeoutExpired:timeout=True;rc=None
 fo.flush();os.fsync(fo.fileno());fe.flush();os.fsync(fe.fileno())
transport={'format':'swdb.parent-original-observer-custody-capture-transport.v1','sealed':False,'argv':argv,'source':pin(source),'started_utc':now.isoformat(),'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,'returncode':rc,'transport_timeout':timeout,'stdout':pin(out),'stderr':pin(err),'no_original_observer_success_or_admission_inferred':True}
publish('.transport.json',transport)
print(json.dumps(transport,sort_keys=True))
assert not timeout and rc==0 and err.stat().st_size==0 and out.stat().st_size<=64*1024*1024
