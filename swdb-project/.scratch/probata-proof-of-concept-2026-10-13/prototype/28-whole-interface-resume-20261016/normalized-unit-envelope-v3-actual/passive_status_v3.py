"""Bounded compact metadata status only; never acceptance or reexecution."""
import resource,signal,sys
resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456));resource.setrlimit(resource.RLIMIT_CPU,(10,10));signal.alarm(15)
def readonly(event,args):
 if event=='open':
  _path,mode,flags=args
  if (isinstance(mode,str)and any(c in mode for c in 'wax+'))or flags&(1|2|64|512|1024):raise PermissionError('status is read-only')
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.'))or event in {'os.system','ctypes.dlopen','os.mkdir','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime','os.chdir','os.putenv','os.unsetenv','resource.setrlimit'}:raise PermissionError('status child/native/network/mutation refused')
sys.addaudithook(readonly)
from pathlib import Path
import hashlib,json,os,stat,time,datetime
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3');START=time.monotonic();CAP=1048576
if RAW.resolve(strict=True)!=RAW or not stat.S_ISDIR(RAW.lstat().st_mode):raise ValueError('physical selected raw required')
def stable(st):return tuple(getattr(st,k)for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
files={};special=[]
for path in RAW.rglob('*'):
 if len(files)>256 or time.monotonic()-START>10:raise ValueError('bounded raw status census required')
 before=path.lstat();rel=str(path.relative_to(RAW))
 if stat.S_ISDIR(before.st_mode):continue
 if not stat.S_ISREG(before.st_mode)or path.resolve(strict=True)!=path:special.append(rel);continue
 row={'bytes':before.st_size}
 if before.st_size<=4194304:
  with path.open('rb')as stream:row['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
  row['stable_while_hashed']=stable(before)==stable(path.lstat())
 files[rel]=row
selected_names=('lane.json','resources.json','outer-resources.json','source-after.json','envelope-result.json','envelope-finalization-refusal.json','envelope-linux-role.json','observer/unit-observation-result.json')
documents={}
for name in selected_names:
 path=RAW/name
 if name not in files:continue
 if files[name]['bytes']>CAP:documents[name]={'metadata_over_cap':True};continue
 with path.open('rb')as stream:data=stream.read(CAP+1)
 try:documents[name]=json.loads(data)
 except (ValueError,UnicodeError):documents[name]={'currently_incomplete_JSON':True}
processes=[];failures=[];count=0
for path in Path('/proc').iterdir():
 if not path.name.isdigit()or int(path.name)==os.getpid():continue
 try:
  if path.stat().st_uid!=os.getuid():continue
  count+=1
  if count>4096 or time.monotonic()-START>12:raise ValueError('finite own-process status cap')
  command=(path/'cmdline').read_bytes()
  if len(command)>CAP:raise ValueError('bounded command metadata')
  if str(RAW).encode()not in command:continue
  text=(path/'stat').read_text();tail=text.rsplit(')',1)[1].split();status=(path/'status').read_text();rss=next((line.split(':',1)[1].strip()for line in status.splitlines()if line.startswith('VmRSS:')),None)
  processes.append({'pid':int(path.name),'parent':int(tail[1]),'start_ticks':tail[19],'state':tail[0],'comm':(path/'comm').read_text().strip(),'argv0':command.split(b'\0',1)[0].decode(errors='replace')[:256],'argv_sha256':hashlib.sha256(command).hexdigest(),'rss':rss})
 except FileNotFoundError:pass
 except PermissionError:failures.append(int(path.name))
leases={}
for path in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json'):
 if path.stat().st_size>CAP:raise ValueError('bounded lease metadata')
 leases[path.name]=json.loads(path.read_bytes())
value={'schema':'passive-normalized-unit-observer-status-1','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw':str(RAW),'raw_files':files,'raw_count':len(files),'raw_bytes':sum(r['bytes']for r in files.values()),'special':special,'documents':documents,'selected_processes':processes,'own_process_permission_failures':failures,'leases':leases,'wall_seconds':time.monotonic()-START,'status_only_no_acceptance':True,'compiler_native_solver_or_project_import':False}
encoded=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
if len(encoded)>1048576:raise ValueError('compact status output cap')
print(encoded.decode())
