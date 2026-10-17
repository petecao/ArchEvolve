import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,12))
import hashlib,json,os,signal,stat,sys
from pathlib import Path
signal.alarm(15)
ROWS=[{'local': 'original-first-ABI.json', 'pin': {'bytes': 127394, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/component/abi.ast.json', 'sha256': '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'}}, {'local': 'original-first-probe.cpp', 'pin': {'bytes': 1588, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10/control/compiler_abi_probe_v1.cpp', 'sha256': 'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34'}}, {'local': 'original-memory-ABI.json', 'pin': {'bytes': 127541, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1/component/abi.ast.json', 'sha256': '493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c'}}, {'local': 'original-memory-probe.cpp', 'pin': {'bytes': 1588, 'path': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1/control/compiler_abi_probe_v1.cpp', 'sha256': 'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34'}}]
PY_SHA='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
def stable(st):return {k:getattr(st,k)for k in('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')}
def readonly(event,args):
 if event=='open':
  _path,mode,flags=args
  if(isinstance(mode,str)and any(c in mode for c in'wax+'))or flags&(1|2|64|512|1024):raise PermissionError('read-only compact ABI transfer')
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.'))or event in{'os.system','ctypes.dlopen','os.mkdir','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime'}:raise PermissionError('no child/native/network/mutation')
sys.addaudithook(readonly)
assert sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_user_site and sys.flags.safe_path
assert dict(os.environ)=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
assert str(Path(sys.executable).resolve())=='/usr/bin/python3.12'
assert hashlib.sha256(Path('/usr/bin/python3.12').read_bytes()).hexdigest()==PY_SHA
def leases():
 value={p.name:json.loads(p.read_bytes())for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
 assert len(value)==3 and all(row['state']=='released'for row in value.values());return value
before_leases=leases();metadata=[];payload=[]
for row in ROWS:
 selected=row['pin'];path=Path(selected['path']);before=path.lstat()
 assert selected['bytes']in(127394,127541,1588)and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode)and before.st_size==selected['bytes']
 with path.open('rb')as handle:raw=handle.read(selected['bytes']+1)
 after=path.lstat()
 assert len(raw)==selected['bytes']and hashlib.sha256(raw).hexdigest()==selected['sha256']and stable(before)==stable(after)
 metadata.append(dict(local=row['local'],pin=selected,before=stable(before),after=stable(after)));payload.append(raw)
assert sum(map(len,payload))==258111
after_leases=leases()
header=json.dumps(dict(schema='exact-compact-two-ABI-transfer-1',files=metadata,total_payload_bytes=258111,leases_before=before_leases,leases_after=after_leases,original_raw_unchanged=True,compiler_native_project_execution=False),sort_keys=True,separators=(',',':')).encode()+b'\n'
assert len(header)<=16384
sys.stdout.buffer.write(header)
for raw in payload:sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()
