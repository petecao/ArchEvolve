"""2026-10-08 ET. One reviewed bounded read-only Git configuration capture."""
import datetime,hashlib,json,os,pathlib,subprocess,time
P=pathlib.Path
src=P('/private/tmp/lanl17_read_git_common_sparse_configuration_20261008_a1.py');raw=src.read_bytes();assert len(raw)==10797 and hashlib.sha256(raw).hexdigest()=='e1b066b907b32bc2bf601bfd95ad694a405f783cbf79b2a0b23c6714354ab423'
argv=['ssh','-T','-o','BatchMode=yes','mbit10','/usr/bin/env']
for name in ('PYTHONPATH','PYTHONHOME','GIT_OPTIONAL_LOCKS','GIT_CONFIG_GLOBAL','GIT_CONFIG_NOSYSTEM','GIT_CONFIG_SYSTEM','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES'):argv.extend(['-u',name])
argv.extend(['/usr/bin/timeout','--signal=TERM','--kill-after=10','90','/usr/bin/python3.12','-B','-s','-','--expected-primary40','5e12a9796432654d88def24ecea617d16ca605b2'])
def pin(p,b):return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
start=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic();cp=subprocess.run(argv,input=raw,capture_output=True,timeout=130)
out=P('/private/tmp/lanl17-git-common-sparse-configuration-query-original-actual-20261008-a1.json');err=out.with_suffix('.stderr');write(out,cp.stdout);write(err,cp.stderr)
r={'format':'swdb.parent-readonly-Git-configuration-original-transport.v1','sealed':False,'source':pin(src,raw),'argv':argv,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,'returncode':cp.returncode,'stdout':pin(out,cp.stdout),'stderr':pin(err,cp.stderr),'remote_mutation_authorized_or_performed_by_this_query':False}
d=P('/private/tmp/lanl17-git-common-sparse-configuration-query-original-actual-20261008-a1.transport.json');write(d,json.dumps(r,indent=2,sort_keys=True,allow_nan=False).encode()+b'\n');print(json.dumps(r,sort_keys=True));assert cp.returncode==0 and not cp.stderr
j=json.loads(cp.stdout);print(json.dumps({k:j[k] for k in ('git_version','primary_HEAD','primary_branch','selected_configuration','include_directives_not_followed_count','before_after_identity_stable')},sort_keys=True))
