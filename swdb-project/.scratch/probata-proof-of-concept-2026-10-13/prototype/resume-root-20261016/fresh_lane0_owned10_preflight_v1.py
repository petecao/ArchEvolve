from pathlib import Path
import os,json,datetime
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'leases':{},'selected_tools':[],'read_failures':[],'exit_races':[],'scope':'Finite owned cmdline/tool scan; preserve all unrelated process state.'}
for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json'):r['leases'][p.name]=json.loads(p.read_bytes())
names={'frama-c','frama-c.exe','why3server','alt-ergo','z3','cvc5','cbmc','clang','clang++','clang-22','pytest'}
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  if p.stat().st_uid!=os.getuid():continue
  a=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v]
  selected=bool(a) and (Path(a[0]).name in names or any(Path(x).name in {'pytest','socket_lane.sh'} for x in a[:4]))
  if selected:r['selected_tools'].append({'pid':int(p.name),'argv_head':[x[:160] for x in a[:4]]})
 except FileNotFoundError:r['exit_races'].append(int(p.name))
 except PermissionError:r['read_failures'].append(int(p.name))
r['free_bytes']={p:os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ['/data1','/data']}
print(json.dumps(r,sort_keys=True))
