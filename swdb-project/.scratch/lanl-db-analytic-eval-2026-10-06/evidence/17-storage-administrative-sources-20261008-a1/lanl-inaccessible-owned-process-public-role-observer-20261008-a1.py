import os,pathlib,json,hashlib,datetime,time,re
P=pathlib.Path;started=time.monotonic();read_bytes=0

def read(p,cap):
 global read_bytes
 assert time.monotonic()-started<45
 with p.open('rb') as f:b=f.read(cap+1)
 assert len(b)<=cap
 read_bytes+=len(b);assert read_bytes<=4*1024*1024
 return b

def public(pid):
 p=P('/proc')/str(pid);st=p.stat();b=read(p/'stat',16384);r=b[b.rfind(b')')+2:].split();wanted={'Name','State','Pid','PPid','TracerPid','Uid','Gid','Threads','CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs','Seccomp'}
 fields={k:v.strip() for line in read(p/'status',65536).decode().splitlines() if ':' in line for k,v in [line.split(':',1)] if k in wanted};c=read(p/'cgroup',65536)
 return {'pid':pid,'proc_owner':st.st_uid,'stat_identity':{'start_ticks':int(r[19]),'ppid':int(r[1]),'pgrp':int(r[2]),'session':int(r[3]),'state':r[0].decode()},'status':fields,'comm':read(p/'comm',256).decode().strip(),'cgroup_pin':{'bytes':len(c),'sha256':hashlib.sha256(c).hexdigest()}}

out={'format':'swdb.inaccessible-owned-process-public-role-observation.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observer_pid':os.getpid(),'observer_parent_pid':os.getppid(),'candidates':[],'unobserved':[],'scope':'Only finite public child/parent identity for currently inaccessible owned FD directories; no FD names/targets, argv/environment/auth/protected reference bodies or cleanup/reference-free conclusion.'}
procs=list(P('/proc').glob('[0-9]*'));assert len(procs)<=10000
for p in procs:
 assert time.monotonic()-started<45
 try:
  if p.stat().st_uid!=os.getuid():continue
  try:os.listdir(p/'fd');continue
  except PermissionError:pass
  first=public(int(p.name));parent=public(first['stat_identity']['ppid']);last=public(int(p.name));parent_last=public(parent['pid'])
  out['candidates'].append({'child':first,'parent':parent,'final_child_anchor':last['stat_identity'],'final_parent_anchor':parent_last['stat_identity'],'same_PID_start_parent':first['stat_identity']['start_ticks']==last['stat_identity']['start_ticks'] and first['stat_identity']['ppid']==last['stat_identity']['ppid'] and parent['stat_identity']['start_ticks']==parent_last['stat_identity']['start_ticks']})
  assert len(out['candidates'])<=32
 except (FileNotFoundError,ProcessLookupError):out['unobserved'].append({'pid':int(p.name),'reason':'disappeared'})
 except PermissionError:out['unobserved'].append({'pid':int(p.name),'reason':'public_identity_inaccessible'})
btime=read(P('/proc/stat'),1048576);out.update(boot_btime=next(int(l.split()[1]) for l in btime.splitlines() if l.startswith(b'btime ')),clk_tck=os.sysconf('SC_CLK_TCK'),read_bytes=read_bytes,elapsed_seconds=time.monotonic()-started)
b=(json.dumps(out,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode();assert len(b)<=65536;print(b.decode(),end='')
