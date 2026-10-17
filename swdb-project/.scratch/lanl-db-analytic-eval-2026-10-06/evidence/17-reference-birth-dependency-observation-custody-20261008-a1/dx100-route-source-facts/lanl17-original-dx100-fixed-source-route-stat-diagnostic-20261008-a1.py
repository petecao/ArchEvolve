import os,stat,json,datetime
from pathlib import Path
assert os.getuid()==os.geteuid()==114316761
paths=['/data1/yanruj', '/data1/yanruj/ArchEvolve', '/data1/yanruj/ArchEvolve/.git', '/data1/yanruj/ArchEvolve/.git/hooks', '/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1', '/data1/yanruj/EvolveSWDB_sources', '/data1/yanruj/EvolveSWDB_sources/bfs-dx100-compile-20260925-a1.source', '/data1/yanruj/EvolveSWDB_sources/bfs-dx100-compile-20260925-a1.source/source', '/data1/yanruj/EvolveSWDB_sources/d9edd7d0042ae3e6', '/data1/yanruj/EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline', '/data1/yanruj/EvolveSWDB_sources/d9edd7d0042ae3e6/typed-library-bfs-gem5-20261003-a2.baseline/source'];rows=[]
for value in paths:
 p=Path(value);row={'path':value}
 try:
  s=p.lstat();row.update(stat={k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')},canonical_nonsymlink=p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)))
 except FileNotFoundError:row['presence']=False
 rows.append(row)
print(json.dumps({'format':'swdb.private.fixed-source-route-stat-original.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'binding_or_capacity_or_cleanup_or_scientific_admission':False},sort_keys=True))
