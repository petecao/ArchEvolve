import datetime,hashlib,json,pathlib,stat
P=pathlib.Path;root=P('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1')
def pin(path):
 before=path.lstat();assert stat.S_ISREG(before.st_mode) and path.resolve(strict=True)==path
 with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
 after=path.lstat();fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns');assert all(getattr(before,f)==getattr(after,f) for f in fields)
 return {'path':str(path),'bytes':before.st_size,'sha256':sha}
rows=[]
for p in sorted(root.rglob('*')):
 mode=p.lstat().st_mode
 if stat.S_ISDIR(mode):continue
 assert stat.S_ISREG(mode)
 rows.append({'relative':str(p.relative_to(root)),**pin(p)})
selected=['component/compiler-observation.json','component/artifact-manifest.json','component/result.json','component/caller.ast.gzip.json','capture-runtime-before.json','capture-runtime-after.json','capture-zlib-before.json','capture-zlib-after.json','capture-linux-role.json','capture-python-entry-role.json','root-guard-adaptation.json','source-after.json']
metadata={}
for name in selected:
 p=root/name;assert p.stat().st_size<=1048576;metadata[name]=json.loads(p.read_bytes())
print(json.dumps({'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_root':str(root),'rows':rows,'metadata':metadata,'raw_payload_transferred':False},sort_keys=True))
