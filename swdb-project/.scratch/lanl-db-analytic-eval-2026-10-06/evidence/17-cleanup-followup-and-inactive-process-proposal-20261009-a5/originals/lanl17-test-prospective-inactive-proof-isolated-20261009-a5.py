"""Created 2026-10-09 ET. Isolated extracted-AST proof tests; no live proc/target imports."""
import ast,copy,datetime,errno,hashlib,json,os,pathlib,stat,types
from zoneinfo import ZoneInfo
BASE=pathlib.Path('/private/tmp/lanl17_pre_full_index_host_observation_20261008_a5_r5.py')
PATCH=pathlib.Path('/private/tmp/lanl17-pre-index-inactive-zombie-proof-prospective-20261009-a5.patch')
UID=114316761;PID=12345
raw=BASE.read_bytes();patch=PATCH.read_text();old=raw.decode();sha=lambda b:hashlib.sha256(b).hexdigest()
assert len(raw)==36052 and sha(raw)=='be2f68c21a72b4de5deee05f17f48a8cd09342cf3a6e7e17280ff72414dc3fd4'
# Reconstruct the single unified hunk without applying/writing any source file.
lines=old.splitlines(keepends=True);out=[];pos=0
import re
pl=patch.splitlines(keepends=True);i=2
while i<len(pl):
 m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n',pl[i]);assert m
 start=int(m[1])-1;out.extend(lines[pos:start]);pos=start;i+=1
 while i<len(pl) and not pl[i].startswith('@@ '):
  x=pl[i]
  if x[0] in ' -':assert lines[pos]==x[1:];pos+=1
  if x[0] in ' +':out.append(x[1:])
  i+=1
out.extend(lines[pos:]);derived=''.join(out)
assert len(derived.encode())==38606 and sha(derived.encode())=='711e4c7f99365c879f872781813a868e2a0365b8b6ee4d407f6747a6bca690f2'
def nodes(s):return {n.name:n for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=nodes(old);b=nodes(derived);assert set(a)==set(b)
assert [k for k in a if ast.dump(a[k],include_attributes=False)!=ast.dump(b[k],include_attributes=False)]==['inactive_owned_identity']
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
def stamp(s):return {k:getattr(s,'st_'+k) for k in FIELDS}
def record(mode,uid,ino):return dict(dev=24,ino=ino,mode=mode,uid=uid,gid=UID,nlink=1,size=0,mtime_ns=10,ctime_ns=10)
def obj(d):return types.SimpleNamespace(**{'st_'+k:v for k,v in d.items()})
def need(ok,why):
 if not ok:raise ValueError(why)
class File:
 def __init__(self,fs,fd):self.fs=fs;self.fd=fd
 def __enter__(self):return self
 def __exit__(self,*unused):self.fs.close(self.fd)
 def fileno(self):return self.fd
 def read(self,n):
  role=self.fs.fds[self.fd];self.fs.event('read',role)
  seq=self.fs.body_sequence.get(role)
  count=self.fs.counts[('read',role)]
  body=seq[min(count-1,len(seq)-1)] if seq else self.fs.bodies[role]
  return body[:n]
class FakeOS:
 O_RDONLY=0;O_DIRECTORY=1;O_NOFOLLOW=2;O_CLOEXEC=4
 def __init__(self,owner=0,state='Z'):
  self.rows={'dir':record(stat.S_IFDIR|0o555,UID,90)}
  self.rows.update({k:record(stat.S_IFREG|0o444,owner,100+i) for i,k in enumerate(('stat','status','cmdline'))})
  self.bodies={'cmdline':b'', 'stat':self.stat_body(state), 'status':self.status_body(state)}
  self.body_sequence={};self.counts={};self.faults={};self.fds={};self.nextfd=7;self.opened=0;self.closed=0
 def stat_body(self,state='Z',pid=PID,parent=42,start=77):return (f'{pid} (name can ) include parenthesis) {state} {parent} '+' '.join(['0']*17)+f' {start}\n').encode()
 def status_body(self,state='Z',pid=PID,tgid=PID,parent=42,uids=None):
  uids=uids or [UID]*4
  return (f'Name:\tignored\nState:\t{state} ('+('zombie' if state=='Z' else 'dead' if state=='X' else 'sleeping')+f')\nTgid:\t{tgid}\nPid:\t{pid}\nPPid:\t{parent}\nUid:\t'+'\t'.join(map(str,uids))+'\n').encode()
 def event(self,op,role):
  key=(op,role);self.counts[key]=self.counts.get(key,0)+1;fault=self.faults.get((op,role,self.counts[key]))
  if isinstance(fault,BaseException):raise fault
  return fault
 def snapshot(self,op,role):
  mod=self.event(op,role);d=self.rows[role].copy()
  if mod:d.update(mod)
  return obj(d)
 def open(self,p,flags,dir_fd=None):
  role=p.role if isinstance(p,Path) else p
  if dir_fd is not None:assert self.fds[dir_fd]=='dir'
  self.event('open',role);fd=self.nextfd;self.nextfd+=1;self.fds[fd]=role;self.opened+=1;return fd
 def close(self,fd):assert fd in self.fds;self.fds.pop(fd);self.closed+=1
 def fdopen(self,fd,mode):assert mode=='rb';self.event('fdopen',self.fds[fd]);return File(self,fd)
 def fstat(self,fd):return self.snapshot('fstat',self.fds[fd])
 def stat(self,name,dir_fd,follow_symlinks):assert self.fds[dir_fd]=='dir' and follow_symlinks is False;return self.snapshot('lstat',name)
FS=None
class Path:
 def __init__(self,s):self.s=str(s);self.role='proc' if self.s=='/proc' else 'dir'
 @property
 def name(self):return self.s.rsplit('/',1)[-1]
 @property
 def parent(self):return Path(self.s.rsplit('/',1)[0])
 def __eq__(self,other):return isinstance(other,Path) and self.s==other.s
 def lstat(self):return FS.snapshot('path_lstat','dir')
 def stat(self):return FS.snapshot('path_stat','dir')
 def iterdir(self):assert self.s=='/proc';return [Path('/proc/'+str(PID))]
 def __str__(self):return self.s
 def __truediv__(self,x):return Path(self.s+'/'+str(x))
 def encode(self):return self.s.encode()
RESULTS=[]
def namespace(fs):
 global FS;FS=fs
 ns={'os':fs,'stat':stat,'UID':UID,'Path':Path,'stamp':stamp,'need':need,'tick':lambda:None}
 # Only the proposed function and original caller AST execute in this mock namespace.
 exec(compile(ast.Module(body=[b['inactive_owned_identity']],type_ignores=[]),'<isolated-extracted-proof>','exec'),ns)
 return ns

def case(name,setup=lambda f:None,accept=False,integration=False,expect_closed=True,owner=0,state='Z'):
 fs=FakeOS(owner,state);setup(fs);ns=namespace(fs);err=None;got=None
 try:
  if integration:
   ns.update({'digest':lambda x:sha(x),'SOURCE':Path('/source'),'RAW':Path('/raw'),'H':Path('/helper'),'owned_cmdline':lambda p,ps:fs.bodies['cmdline'],'process_identity':lambda pid:({'pid':pid,'proc_inode':90,'cmdline_sha256':sha(fs.bodies['cmdline'])},fs.bodies['cmdline'][:-1].split(b'\0'),'/exe'),'kernel_bytes':lambda p,cap,owner:fs.bodies['stat']})
   exec(compile(ast.Module(body=[a['consumers']],type_ignores=[]),'<isolated-original-caller>','exec'),ns)
   got=ns['consumers']({'self':{'pid':999},'parent':{'pid':998}})
   valid=got['no_live_owned_source_RAW_consumers'] is accept and bool(got['unknown_processes']) is (not accept)
  else:
   got=ns['inactive_owned_identity'](Path('/proc/'+str(PID)),obj(fs.rows['dir']));valid=accept and got=={'pid':PID,'uid':UID,'proc_inode':90,'start_ticks':77,'state':state}
 except (OSError,ValueError,IndexError,UnicodeError) as e:err=type(e).__name__;valid=not accept
 closed=not fs.fds
 RESULTS.append({'case':name,'passed':bool(valid and (closed or not expect_closed)),'outcome':'accepted' if err is None else err,'all_FDs_closed':closed})
for owner in (0,UID):
 for state in ('Z','X'):case(f'good-owner{owner}-{state}',accept=True,owner=owner,state=state)
for body in (b'\0',b'x',b'x\0'):case('nonempty-cmdline-'+body.hex(),lambda f,z=body:f.bodies.update(cmdline=z))
for state in ('S','R','D','T','t','I'):case('nonterminal-'+state,lambda f,z=state:f.bodies.update(stat=f.stat_body(z),status=f.status_body(z)))
case('stat-status-state-mismatch',lambda f:f.bodies.update(status=f.status_body('X')))
for i in range(4):
 case('foreign-status-UID-position'+str(i),lambda f,i=i:f.bodies.update(status=f.status_body(uids=[UID if k!=i else 0 for k in range(4)])))
for field in ('Pid','Tgid','PPid'):
 case('wrong-status-'+field,lambda f,field=field:f.bodies.update(status=f.bodies['status'].replace((field+':\t'+str(PID if field!='PPid' else 42)).encode(),(field+':\t999').encode())))
for field in ('Pid','Tgid','PPid','Uid','State'):
 case('duplicate-'+field,lambda f,field=field:f.bodies.update(status=f.bodies['status']+(field+':\t1\n').encode()))
 case('missing-'+field,lambda f,field=field:f.bodies.update(status=b'\n'.join(z for z in f.bodies['status'].split(b'\n') if not z.startswith((field+':').encode()))))
case('noninteger-Pid',lambda f:f.bodies.update(status=f.bodies['status'].replace(b'Pid:\t12345',b'Pid:\tnan')))
case('truncated-status',lambda f:f.bodies.update(status=f.bodies['status'].rstrip(b'\n')))
case('truncated-stat',lambda f:f.bodies.update(stat=f.bodies['stat'].rstrip(b'\n')))
case('wrong-stat-PID',lambda f:f.bodies.update(stat=f.stat_body(pid=PID+1)))
case('zero-start',lambda f:f.bodies.update(stat=f.stat_body(start=0)))
for role,cap in (('stat',8192),('status',65536)):
 case('oversize-'+role,lambda f,role=role,cap=cap:f.bodies.update({role:f.bodies[role]+b'x'*(cap+1)}))
 case('body-change-'+role,lambda f,role=role:f.body_sequence.update({role:[f.bodies[role],f.bodies[role].replace(b'ignored',b'changed') if role=='status' else f.stat_body(start=78)]}))
for field in FIELDS:
 case('directory-nine-stat-race-'+field,lambda f,field=field:f.faults.update({('fstat','dir',2):{field:f.rows['dir'][field]+1}}))
 case('leaf-nine-stat-race-'+field,lambda f,field=field:f.faults.update({('fstat','stat',4):{field:f.rows['stat'][field]+1}}))
for role in ('stat','status','cmdline'):
 case('symlink-'+role,lambda f,role=role:f.rows[role].update(mode=stat.S_IFLNK|0o777))
 case('foreign-owner-'+role,lambda f,role=role:f.rows[role].update(uid=123))
 case('directory-type-'+role,lambda f,role=role:f.rows[role].update(mode=stat.S_IFDIR|0o555))
 for op in ('lstat','open','read'):
  case('EACCES-'+op+'-'+role,lambda f,role=role,op=op:f.faults.update({(op,role,1):PermissionError(errno.EACCES,'mock only')}))
 case('missing-'+role,lambda f,role=role:f.faults.update({('lstat',role,1):FileNotFoundError(errno.ENOENT,'mock only')}))
case('directory-wrong-UID',lambda f:f.rows['dir'].update(uid=0))
case('directory-reused-inode',lambda f:f.faults.update({('path_lstat','dir',1):{'ino':91}}))
case('directory-open-EACCES',lambda f:f.faults.update({('open','dir',1):PermissionError(errno.EACCES,'mock only')}))
case('cmdline-repopulates',lambda f:f.body_sequence.update(cmdline=[b'',b'x']))
case('fdopen-OSerror',lambda f:f.faults.update({('fdopen','stat',1):OSError(errno.EMFILE,'mock only')}))
case('caller-good-inactive',accept=True,integration=True)
case('caller-nonterminal-unknown',lambda f:f.bodies.update(stat=f.stat_body('S'),status=f.status_body('S')),integration=True)
case('caller-UID-mismatch-unknown',lambda f:f.bodies.update(status=f.status_body(uids=[UID,0,UID,UID])),integration=True)
case('caller-EACCES-unknown',lambda f:f.faults.update({('read','stat',1):PermissionError(errno.EACCES,'mock only')}),integration=True)
now=datetime.datetime.now(datetime.timezone.utc)
result={'format':'swdb.lanl17-isolated-prospective-inactive-proof-tests.v1','prepared_ET':now.astimezone(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET'),'prepared_utc':now.isoformat(),'original_sha256':sha(raw),'patch_sha256':sha(patch.encode()),'prospective_sha256':sha(derived.encode()),'unchanged_top_level_functions_classes':34,'full_observer_imported_or_executed':False,'live_proc_remote_or_repository_modified':False,'selection_or_no_use_or_scientific_admission':False,'case_count':len(RESULTS),'passed':sum(r['passed'] for r in RESULTS),'failures':[r for r in RESULTS if not r['passed']],'case_columns':['name','passed','outcome','all_FDs_closed'],'cases':[[r['case'],r['passed'],r['outcome'],r['all_FDs_closed']] for r in RESULTS]}
# Keep result compact; no fake/raw status bodies are exported.
encoded=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode();assert len(encoded)<8192
path='/private/tmp/lanl17-prospective-inactive-proof-isolated-results-20261009-a5.json'
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(encoded)
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2));print('RESULT_PIN',len(encoded),sha(encoded));print('HARNESS_PIN',len(pathlib.Path(__file__).read_bytes()),sha(pathlib.Path(__file__).read_bytes()))
