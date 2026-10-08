import os, stat, json, hashlib, datetime
from pathlib import Path
p=Path('/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261006-a1.lane.json')
def pin(s):
 return {k:getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')}
before=p.lstat()
assert stat.S_ISREG(before.st_mode) and before.st_uid==114316761 and before.st_nlink==1 and before.st_size==988
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
try:
 assert pin(os.fstat(fd))==pin(before)
 body=os.read(fd,4097)
 assert len(body)==before.st_size and pin(os.fstat(fd))==pin(before)
finally:os.close(fd)
assert pin(p.lstat())==pin(before)
value=json.loads(body)
assert isinstance(value,dict)
print(json.dumps({'format':'swdb.original-top-lane-sidecar-readonly-custody.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(p),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'stat':pin(before),'original_metadata':value,'metadata_only':True,'scientific_admission':False},sort_keys=True))
