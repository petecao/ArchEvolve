from pathlib import Path
import json,os,datetime,hashlib,stat
roots={'source9-layout8-v2': '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-owned-source9-layout8-public-v2'}
result={"observed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"runs":{},"leases":{},"raw_payload_transferred":False}
for key,raw in roots.items():
 p=Path(raw);r={"raw_root":raw,"metadata":{},"pins":{},"selected_processes":[],"process_read_failures":[],"process_exit_races":[]};result["runs"][key]=r
 for name in ["lane.json","launch.json","outer-resources.json","resources.json","source-after.json","closed-result.json","mixed-result.json","component/result.json","mixed-progress.json","component/commands.json","component/caller.ast.gzip.json","component/caller.ast.identity.json","owned-source9-layout-public-v2-profile/result.json","owned-source9-layout-public-v2-profile/primary-error.json"]:
  f=p/name
  if f.is_file() and not f.is_symlink():
   size=f.stat().st_size
   if size<=262144:
    data=f.read_bytes();r["pins"][name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()};r["metadata"][name]=json.loads(data)
 if "lane.json" in r["metadata"] and r["metadata"]["lane.json"]["socket_lane"].get("ended_utc"):
  count=total=0;aliases=[];special=[]
  for base,dirs,files in os.walk(p,followlinks=False):
   for name in dirs+files:
    f=Path(base)/name;st=f.lstat()
    if stat.S_ISREG(st.st_mode):count+=1;total+=st.st_size
    elif stat.S_ISLNK(st.st_mode):aliases.append({"path":str(f.relative_to(p)),"target":os.readlink(f)})
    elif not stat.S_ISDIR(st.st_mode):special.append(str(f.relative_to(p)))
  r["settled_extent"]={"regular_files":count,"bytes":total,"aliases":aliases,"special":special}
 for proc in Path('/proc').iterdir():
  if not proc.name.isdecimal():continue
  try:
   if proc.stat().st_uid!=os.getuid():continue
   cmd=(proc/'cmdline').read_bytes()
   if raw.encode() in cmd:r['selected_processes'].append(int(proc.name))
  except FileNotFoundError:r['process_exit_races'].append(int(proc.name))
  except PermissionError:r['process_read_failures'].append(int(proc.name))
for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json'):result['leases'][p.name]=json.loads(p.read_bytes())
result['free_bytes']={str(p):os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in (Path('/data1'),Path('/data'))}
print(json.dumps(result,sort_keys=True))
