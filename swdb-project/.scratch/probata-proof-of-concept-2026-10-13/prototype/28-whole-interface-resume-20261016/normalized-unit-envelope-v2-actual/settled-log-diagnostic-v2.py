import json,hashlib,signal,stat
from pathlib import Path
signal.alarm(10)
r=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2')
rows={}
for name in ('worker.log','acceptance.log','dispatch.log'):
 p=r/name
 if not p.exists():continue
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode)or s.st_size>16384:raise ValueError('bounded physical traceback log required')
 raw=p.read_bytes();rows[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode()}
print(json.dumps({'schema':'bounded-settled-observer-log-diagnostic-1','logs':rows,'no_child_or_rerun':True},sort_keys=True))
