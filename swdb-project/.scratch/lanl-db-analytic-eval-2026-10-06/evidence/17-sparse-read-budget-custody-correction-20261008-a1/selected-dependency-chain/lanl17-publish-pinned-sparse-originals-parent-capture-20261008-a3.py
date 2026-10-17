import ast,datetime,hashlib,json,os,pathlib,shlex,signal,subprocess,sys
T=pathlib.Path('/private/tmp')
SOURCE=T/'lanl_publish_parent_sparse_plan_review_originals_20261008_a2.py'
DIGEST='5e667fa8ca26ece4825631e5d51feca490f3e154688a38399518bf9c237df2d9'
INSTALL='''import hashlib,os,pathlib,stat,sys
BASE=pathlib.Path('/data1/yanruj')
P=BASE/'lanl17-publish-sparse-parent-originals-20261008-a3.py'
SHA='5e667fa8ca26ece4825631e5d51feca490f3e154688a38399518bf9c237df2d9'
assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==114316761
assert sys.flags.dont_write_bytecode and sys.flags.no_user_site and not sys.flags.optimize
assert BASE.resolve(strict=True)==BASE and not any(q.is_symlink() for q in (BASE,*BASE.parents))
s=BASE.lstat();assert stat.S_IMODE(s.st_mode)==0o700 and s.st_uid==114316761 and s.st_dev==2097 and s.st_ino==54132737
assert not any(k.startswith('GIT_') for k in os.environ)
assert not os.path.lexists(P)
parts=[];remaining=16126
while remaining:
 b=os.read(0,min(65536,remaining));assert b;parts.append(b);remaining-=len(b)
body=b''.join(parts);assert hashlib.sha256(body).hexdigest()==SHA
fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 f=os.fstat(fd);assert (f.st_dev,f.st_ino,f.st_uid,f.st_gid,f.st_mode)==(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)
 out=os.open(P.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
 try:
  n=0
  while n<len(body):
   written=os.write(out,body[n:]);assert written>0;n+=written
  os.fsync(out);v=os.fstat(out);assert v.st_uid==114316761 and v.st_nlink==1 and stat.S_IMODE(v.st_mode)==0o600
 finally:os.close(out)
 os.fsync(fd)
finally:os.close(fd)
assert P.read_bytes()==body
sys.argv=[str(P),'--source-sha256',SHA]
exec(compile(body,str(P),'exec'),{'__name__':'__main__','__file__':str(P),'__builtins__':__builtins__})
'''
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def original(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
packet=pathlib.Path(sys.argv[1]);capture=pathlib.Path(sys.argv[2]);expected=sys.argv[3]
assert packet.parent==T and capture.parent==T and not capture.exists()
source=SOURCE.read_bytes();assert len(source)==16126 and hashlib.sha256(source).hexdigest()==DIGEST
payload=packet.read_bytes();assert len(payload)<=4210689 and hashlib.sha256(payload).hexdigest()==expected
assert pin(pathlib.Path('/usr/bin/ssh'))['sha256']=='c7f9f9779c1dd141b04889c6cb214859d0702687e7fde34511bb5fa7af8951f1'
a=ast.parse((T/'lanl17_capture_exact_administrative_fetch_two_source_copy_20261008_a1_r1.py').read_bytes());pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PRESTARTUP' for x in n.targets))
remote=['/usr/bin/bash','--noprofile','--norc','-p','-c',pre,'reviewed-sparse-original-publication-prestartup','/usr/bin/timeout','--signal=TERM','--kill-after=60s','120s','/usr/bin/python3.12','-B','-s','-c',INSTALL];argv=['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
os.umask(0o077);capture.mkdir(mode=0o700);start=datetime.datetime.now(datetime.timezone.utc).isoformat();original(capture/'start.json',(json.dumps({'sealed':False,'started_utc':start,'argv':argv,'installer_bytes':len(INSTALL.encode()),'installer_sha256':hashlib.sha256(INSTALL.encode()).hexdigest(),'publisher_source':pin(SOURCE),'packet':pin(packet),'guard_or_scientific_mains_invoked':False},sort_keys=True)+'\n').encode())
fds=[os.open(capture/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600) for n in ['stdout','stderr']];p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=fds[0],stderr=fds[1],start_new_session=True);timed=False
try:
 try:p.communicate(input=source+payload,timeout=200)
 except subprocess.TimeoutExpired:
  timed=True;os.killpg(p.pid,signal.SIGTERM)
  try:p.communicate(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=5)
finally:
 for fd in fds:os.fsync(fd);os.close(fd)
result={'sealed':False,'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'timed_out':timed,'stdout':pin(capture/'stdout'),'stderr':pin(capture/'stderr'),'SSH_exit_never_infers_remote_completion':True};original(capture/'transport.json',(json.dumps(result,sort_keys=True)+'\n').encode());print(json.dumps(result));assert p.returncode==0 and not timed
returned=json.loads((capture/'stdout').read_bytes());assert not returned.get('failed') and len(returned['originals'])==2;assert (capture/'stderr').stat().st_size==0
print(json.dumps({'publication_two_originals':returned['originals'],'selected_guard_mains_invoked':False}))
