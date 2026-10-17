import json,stat,hashlib,signal
from pathlib import Path
signal.alarm(10)
paths={'legacy':'/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative/run.sh','actual':'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2/run.sh','environment':'/data1/yanruj/probata-verifiers/env.sh'}
rows={}
for name,value in paths.items():
 p=Path(value);before=p.lstat()
 if p.resolve(strict=True)!=p or not stat.S_ISREG(before.st_mode)or before.st_size>16384:raise ValueError('bounded physical shell source required')
 data=p.read_bytes();after=p.lstat();fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
 if any(getattr(before,k)!=getattr(after,k)for k in fields):raise ValueError('source changed')
 rows[name]={'path':value,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'content':data.decode()}
print(json.dumps({'schema':'passive-exact-launch-shell-source-1','rows':rows,'shell_or_native_or_child_executed':False},sort_keys=True))
