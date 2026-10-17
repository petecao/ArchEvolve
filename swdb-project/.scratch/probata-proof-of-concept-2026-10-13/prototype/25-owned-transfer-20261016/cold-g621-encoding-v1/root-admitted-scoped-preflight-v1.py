import os,json,hashlib,stat,subprocess,signal,time
from pathlib import Path
signal.alarm(30)
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-d7f685c6-owned-transfer10-public-v2')
SOURCE=Path('/data1/yanruj/probata-resume-20261016-d7f685c6')
SELECTED=SOURCE/'swdb-project/swdb/vector_owned_state.mlw'
EXPECTED='a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'
started=time.monotonic()
def read(path,cap=1048576):
 st=path.lstat()
 if not stat.S_ISREG(st.st_mode) or st.st_size>cap:raise ValueError('bounded regular metadata required')
 with path.open('rb')as f:data=f.read(cap+1)
 if len(data)>cap:raise ValueError('metadata cap')
 return data
for path in (RAW,SOURCE):
 if not stat.S_ISDIR(path.lstat().st_mode)or path.resolve(strict=True)!=path:raise ValueError('physical selected root required')
lane=json.loads(read(RAW/'lane.json'))['socket_lane']
resources=[json.loads(read(RAW/name))for name in ('resources.json','outer-resources.json')]
if lane['lease_generation']!=621 or lane['exit_code']!=0 or not lane.get('ended_utc'):raise ValueError('original G621 is not settled')
if any(r['exit_code'] or r['timed_out']or r['out_of_memory']for r in resources):raise ValueError('original whole guard differs')
git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
head=subprocess.check_output(git+['rev-parse','HEAD'],timeout=10).decode().strip()
dirty=subprocess.check_output(git+['status','--porcelain','--untracked-files=all'],timeout=10)
if head!='d7f685c6fdbd7ff776eb1eaccc40099a2c48dc08'or dirty:raise ValueError('original source is not exact clean')
selected=read(SELECTED)
if hashlib.sha256(selected).hexdigest()!=EXPECTED:raise ValueError('selected original theory differs')
needles=(str(RAW),str(SOURCE));matches=[];unreadable=[];disappeared=0;checked=0;descriptors=0
for directory in sorted(Path('/proc').iterdir(),key=lambda p:p.name):
 if not directory.name.isdigit()or int(directory.name)==os.getpid():continue
 try:
  if directory.stat().st_uid!=os.getuid():continue
  checked+=1
  if checked>4096:raise ValueError('finite own process cap')
  command=(directory/'cmdline').read_bytes()
  if len(command)>1048576:raise ValueError('bounded command metadata')
  found=[n for n in needles if n.encode()in command]
  for name in ('cwd','exe'):
   try:
    value=os.readlink(directory/name)
    found += [n for n in needles if n in value]
   except FileNotFoundError:disappeared+=1
  fds=list((directory/'fd').iterdir())
  if len(fds)>2048:raise ValueError('finite descriptor cap')
  for fd in fds:
   descriptors+=1
   if descriptors>32768:raise ValueError('finite aggregate descriptor cap')
   try:
    value=os.readlink(fd);found += [n for n in needles if n in value]
   except FileNotFoundError:disappeared+=1
  if found:matches.append({'pid':int(directory.name),'selected_roots':sorted(set(found))})
 except FileNotFoundError:disappeared+=1
 except PermissionError:unreadable.append(int(directory.name))
result={'classification':'SCOPED_ORIGINAL_G621_PREFLIGHT','original_generation':621,'original_ended_utc':lane['ended_utc'],'source_commit':head,'source_clean':not dirty,'selected_theory_sha256':EXPECTED,'own_processes_checked':checked,'descriptor_links_checked':descriptors,'vanished_process_or_descriptor_observations':disappeared,'selected_original_readers':matches,'unreadable_own_processes':unreadable,'scoped_preflight_pass':not matches and not unreadable,'elapsed_seconds':time.monotonic()-started,'scope':'Finite current-own-UID process cmdline/cwd/exe/fd metadata for the exact original raw/source only. Unrelated032e science is permitted; no proof/native/tool/version query or raw payload transfer.'}
encoded=json.dumps(result,sort_keys=True).encode()
if len(encoded)>65536:raise ValueError('preflight metadata cap')
print(encoded.decode())
raise SystemExit(0 if result['scoped_preflight_pass']else 1)
