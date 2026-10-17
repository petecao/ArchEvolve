from pathlib import Path
import hashlib,json,os,pwd,shutil,signal,socket,stat,sys
signal.alarm(30)
assert os.getuid()==os.geteuid()==114316761 and socket.gethostname().split('.')[0]=='mbit10' and sys.flags.dont_write_bytecode and sys.flags.no_user_site
p=Path('/usr/bin/python3.12');b=p.read_bytes();assert len(b)==8020928 and hashlib.sha256(b).hexdigest()=='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
rows=[]
for name in ('git','python3','tmux','numactl','strace','timeout','bash','node'):
 route=shutil.which(name,path='/usr/bin:/bin:/usr/local/bin')
 row={'name':name,'PATH_route':route}
 if route is not None:
  p=Path(route);q=p.resolve(strict=True);s=q.lstat();row.update(resolved=str(q),route_is_symlink=p.is_symlink(),stat={k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')})
 rows.append(row)
out={'format':'swdb.lanl17-necessary-command-route-stat-diagnostic-original.v1','sealed':False,'rows':rows,'only_native_Python_body_read_all_command_bodies_UNOBSERVED':True,'selected_version_or_scientific_execution':False}
b=json.dumps(out,sort_keys=True).encode();assert len(b)<=16384;print(b.decode())
