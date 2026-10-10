"""2026-10-08 ET. ONE fresh four-input RAW hash query; no original overwritten."""
import datetime,hashlib,json,os,pathlib,subprocess,time
P=pathlib.Path
source=P('/private/tmp/lanl17-readonly-O7-original-input-file-hashes-20261008-a1.py');raw=source.read_bytes();assert len(raw)==2559 and hashlib.sha256(raw).hexdigest()=='ddcf60b8aaae4b7bb04558e58168986f7ef024d97f37238b40e3420f0fddc27a'
argv=['ssh','-T','-o','BatchMode=yes','mbit10','/usr/bin/env','-u','PYTHONPATH','-u','PYTHONHOME','-u','PYTHONOPTIMIZE','/usr/bin/timeout','--signal=TERM','--kill-after=10','150','/usr/bin/python3.12','-B','-s','-']
def pin(p,b):return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
start=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic();cp=subprocess.run(argv,input=raw,capture_output=True,timeout=190)
out=P('/private/tmp/lanl17-O7-four-original-inputs-fresh-whole-hash-observation-actual-20261008-a2.json');err=out.with_suffix('.stderr');write(out,cp.stdout);write(err,cp.stderr)
r={'format':'swdb.parent-readonly-original-O7-four-input-hash-transport.v1','sealed':False,'source':pin(source,raw),'argv':argv,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,'returncode':cp.returncode,'stdout':pin(out,cp.stdout),'stderr':pin(err,cp.stderr),'scientific_application_invoked_or_RAW_bodies_transferred':False}
transport=P('/private/tmp/lanl17-O7-four-original-inputs-fresh-whole-hash-observation-actual-20261008-a2.transport.json');write(transport,json.dumps(r,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n');print(json.dumps(r,sort_keys=True));assert cp.returncode==0 and not cp.stderr
j=json.loads(cp.stdout);assert len(j['files'])==4 and all(x['original_hash_matches'] is True for x in j['files']);print(json.dumps({'exact_original_hash_matches':4,'bytes_read':j['bytes_read'],'raw_bodies_transferred':False},sort_keys=True))
