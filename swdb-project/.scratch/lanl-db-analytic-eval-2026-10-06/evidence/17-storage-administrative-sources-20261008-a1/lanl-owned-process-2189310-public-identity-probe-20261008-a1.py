import os,pathlib,json,hashlib,datetime,time,re,stat
P=pathlib.Path;start=time.monotonic();reads=0

def read(p,cap):
 global reads
 assert time.monotonic()-start<45
 with p.open('rb') as f:b=f.read(cap+1)
 assert len(b)<=cap
 reads+=len(b);assert reads<=3*1024*1024
 return b

def public(pid):
 p=P('/proc')/str(pid);s=p.stat();raw=read(p/'stat',16384);fields=raw[raw.rfind(b')')+2:].split();status=read(p/'status',65536).decode();wanted={'Name','State','Tgid','Pid','PPid','TracerPid','Uid','Gid','Threads','CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs','Seccomp'}
 values={k:v.strip() for line in status.splitlines() if ':' in line for k,v in [line.split(':',1)] if k in wanted}
 group=read(p/'cgroup',65536);units=re.findall(rb'(?:^|/)((?:user@[0-9]+|session-[0-9]+)\.(?:service|scope))(?:/|\n|$)',group)
 return {'pid':pid,'proc_directory':{'uid':s.st_uid,'gid':s.st_gid,'mode':s.st_mode},'stat_identity':{'pid':int(raw.split(b' ',1)[0]),'start_ticks':int(fields[19]),'ppid':int(fields[1]),'pgrp':int(fields[2]),'session':int(fields[3]),'state':fields[0].decode()},'status_fields':values,'comm':read(p/'comm',256).decode().strip(),'cgroup':{'bytes':len(group),'sha256':hashlib.sha256(group).hexdigest(),'closed_unit_labels':[x.decode() for x in units]}}

out={'format':'swdb.owned-process-public-identity-observation.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Public process and parent identity only; no argv, environment, auth, protected FD/cwd/root/exe/maps body or access; no cleanup/reference-free claim.'}
try:
 first=public(2189310);parent=public(first['stat_identity']['ppid']);boot=read(P('/proc/stat'),1048576);out.update(child=first,parent=parent,boot_btime=next(int(line.split()[1]) for line in boot.splitlines() if line.startswith(b'btime ')),clk_tck=os.sysconf('SC_CLK_TCK'));child_final=public(2189310);parent_final=public(parent['pid']);out['final_anchors']={'child':child_final['stat_identity'],'parent':parent_final['stat_identity']};out['stable_identity']=all(x['stat_identity']==y['stat_identity'] and x['status_fields'].get('Uid')==y['status_fields'].get('Uid') and x['cgroup']==y['cgroup'] for x,y in ((first,child_final),(parent,parent_final)))
except (OSError,ValueError,AssertionError,StopIteration) as e:out.update(stable_identity=False,error={'type':type(e).__name__,'description':str(e)})
out['read_bytes']=reads;out['elapsed_seconds']=time.monotonic()-start
b=(json.dumps(out,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode();assert len(b)<=65536;print(b.decode(),end='')
