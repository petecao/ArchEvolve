"""Fixed read-only process-field access diagnostic; no admission or exclusions.
2026-10-08 ET. Never reads environment/authentication or serializes argv/maps.
"""
import datetime, hashlib, json, os, pathlib, signal, socket, time
P=pathlib.Path
UID=114316761
CAP=16*1024*1024
TOTAL=512*1024*1024
start=time.monotonic(); charged=0
assert socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID
def left():
 assert time.monotonic()-start<60
def read(p):
 global charged
 left()
 with p.open('rb') as f:b=f.read(CAP+1)
 charged+=len(b);assert len(b)<=CAP and charged<=TOTAL
 return b
def failure(e):return {'class':type(e).__name__,'errno':getattr(e,'errno',None)}
snapshots={};unreadable_status=[]
procs=sorted((p for p in P('/proc').iterdir() if p.name.isdecimal()),key=lambda p:int(p.name))
assert len(procs)<=10000
for p in procs:
 owner=None
 try:
  owner=p.stat().st_uid;raw=read(p/'status')
  fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in raw.decode().splitlines() if ':' in line}
  snapshots[int(p.name)]={'path':p,'owner':owner,'name':fields['Name'],'uids':list(map(int,fields['Uid'].split())),'ppid':int(fields['PPid']),'state':fields['State'].split()[0],'threads':int(fields['Threads'])}
 except FileNotFoundError:continue
 except PermissionError as e:unreadable_status.append({'pid':int(p.name),'owner':owner,'error':failure(e)})
owned={pid for pid,row in snapshots.items() if UID in row['uids']};relevant=set(owned)
for pid,row in snapshots.items():
 parent=row['ppid'];seen=set()
 while parent in snapshots and parent not in seen:
  seen.add(parent)
  if parent in owned:relevant.add(pid);break
  parent=snapshots[parent]['ppid']
rows=[];links_seen=0
for pid in sorted(relevant):
 left();r=snapshots[pid];p=r['path'];row={k:v for k,v in r.items() if k!='path'};row['pid']=pid;row['access']={}
 try:
  before=read(p/'stat');vals=before[before.rfind(b')')+2:].split();row['start_ticks']=int(vals[19])
 except OSError as e:row['stat_error']=failure(e);rows.append(row);continue
 for name in ('cwd','root','exe'):
  try:
   target=os.readlink(p/name);row['access'][name]={'readable':True,'target_sha256':hashlib.sha256(target.encode()).hexdigest(),'target_bytes':len(target.encode())}
  except OSError as e:row['access'][name]=failure(e)
 try:
  fds=sorted((p/'fd').iterdir());links_seen+=len(fds);assert links_seen<=200000
  errors=[]
  for fd in fds:
   try:os.readlink(fd)
   except OSError as e:errors.append({'fd':fd.name,'error':failure(e)})
  row['access']['fd']={'listed':True,'count':len(fds),'link_errors':errors}
 except OSError as e:row['access']['fd']=failure(e)
 for name in ('cmdline','maps'):
  try:
   body=read(p/name);row['access'][name]={'readable':True,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
  except OSError as e:row['access'][name]=failure(e)
 try:
  after=read(p/'stat');v=after[after.rfind(b')')+2:].split();row['same_pid_start_at_end']=int(v[19])==row['start_ticks'];row['state_at_end']=v[0].decode()
 except OSError as e:row['end_stat_error']=failure(e)
 rows.append(row)
print(json.dumps({'format':'swdb.owned-process-field-access-diagnostic.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_s':time.monotonic()-start,'bytes_read':charged,'relevant_processes':rows,'unreadable_public_statuses':unreadable_status,'no_process_kill_exclusion_or_global_clearance':True,'environment_authentication_argv_maps_or_reference_bodies_serialized':False},sort_keys=True))
