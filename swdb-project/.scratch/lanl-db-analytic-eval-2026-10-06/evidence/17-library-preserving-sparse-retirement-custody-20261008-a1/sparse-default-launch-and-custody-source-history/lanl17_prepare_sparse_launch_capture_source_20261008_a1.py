from pathlib import Path
import ast,difflib,hashlib,os
D=Path('/private/tmp');old=D/'lanl14_capture_reviewed_reader_ssh_20261008_a1_r1.py';new=D/'lanl17_capture_reviewed_sparse_default_launch_20261008_a1.py'
text=old.read_text();prefix=text[:text.index('def main():')]
prefix=prefix.replace('"""SOURCE ONLY parent-local private capture for ONE future reviewed reader.\nThis source cannot clear remote export/admission gates or authorize its own run.\n"""','"""SOURCE ONLY: parent-local private capture for ONE future sparse default launch.\nNo guard completion, retirement, capacity or science admission is inferred.\n"""')
boot='''import hashlib,os,sys,stat
from pathlib import Path
UID=114316761
BASE=Path('/data1/yanruj')
W_SHA='1127d1fba8e004153cf086cace7d19ccd901e85902f9ad91924407922c85c6ca'
G_SHA='4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'
def stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))
def exact(p,size,digest,owner,mode):
 assert p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==mode and s.st_size==size
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  b=f.read(size+1);assert len(b)==size and hashlib.sha256(b).hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())
 return stamp(s)
assert os.uname().sysname=='Linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and not sys.flags.optimize
assert Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12')
assert BASE.resolve(strict=True)==BASE and not any(q.is_symlink() for q in (BASE,*BASE.parents))
s=BASE.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
wrapper=Path(sys.argv[1]);guard=Path(sys.argv[2]);tail=sys.argv[3:]
assert wrapper.parent==guard.parent and wrapper.parent.parent==BASE and wrapper.parent.name.startswith('lanl17-sparse-retirement-source-')
p=wrapper.parent;s=p.lstat();assert p.resolve(strict=True)==p and not p.is_symlink() and stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
assert wrapper.name=='lanl17_detach_library_preserving_sparse_administration_20261008_a1_r1.py'
assert guard.name=='lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py'
wp=exact(wrapper,24115,W_SHA,UID,0o600);gp=exact(guard,166145,G_SHA,UID,0o600)
for p,size,digest in [(Path('/usr/bin/python3.12'),8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),(Path('/usr/bin/timeout'),39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52')]:exact(p,size,digest,0,0o755)
for key in list(os.environ):
 if key.startswith('GIT_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','BASH_ENV','ENV'):os.environ.pop(key)
os.environ['PATH']='/usr/bin:/bin:/usr/local/bin'
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PYTHONNOUSERSITE']='1'
assert exact(wrapper,24115,W_SHA,UID,0o600)==wp and exact(guard,166145,G_SHA,UID,0o600)==gp
os.umask(0o077)
argv=['/usr/bin/python3.12','-B',str(wrapper),'--source-sha256',W_SHA,'--guard-source',str(guard),*tail]
os.execv(argv[0],argv)
'''
main=r'''def main():
 os.umask(0o077)
 p=Parser(description=__doc__)
 for n in ('source-sha256','ssh-sha256','expected-primary','plan-sha256','attempt','control-directory'):p.add_argument('--'+n,required=True)
 for n in ('wrapper','guard','plan','local-processes','capture-directory'):p.add_argument('--'+n,required=True,type=Path)
 p.add_argument('--ssh-bytes',required=True,type=int);p.add_argument('--select',action='append',required=True)
 a=p.parse_args()
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_local_account_flags')
 for v in (a.source_sha256,a.ssh_sha256,a.plan_sha256):require(re.fullmatch('[a-f0-9]{64}',v),'exact_SHA')
 require(re.fullmatch('[a-f0-9]{40}',a.expected_primary) and re.fullmatch('a[1-9][0-9]*',a.attempt),'exact_revision_attempt')
 require(1<=len(a.select)<=18 and len(set(a.select))==len(a.select) and all(re.fullmatch('ArchEvolve-lanl-[A-Za-z0-9-]{1,96}',v) for v in a.select),'explicit_ordered_rows')
 base=Path('/data1/yanruj');control=Path(a.control_directory)
 require(control.parent==base and control.name.startswith('lanl17-detached-sparse-') and len(control.name)<=48,'explicit_private_control_route')
 require(a.wrapper.parent==a.guard.parent and a.wrapper.parent.parent==base and a.wrapper.parent.name.startswith('lanl17-sparse-retirement-source-'),'exact_future_private_source_route')
 require(a.wrapper.name=='lanl17_detach_library_preserving_sparse_administration_20261008_a1_r1.py' and a.guard.name=='lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py','selected_R2_basenames')
 require(a.plan.parent==base and a.plan.name.startswith('lanl-sparse-retirement-parent-plan-'),'exact_guard_plan_route')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0);require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'actual_local_SSH_pin')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid());require(procspin['bytes']==912,'existing_local_owned_SSH_cleanup_source')
 helpers=types.ModuleType('lanl17_sparse_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future reuse of the exact reviewed owned-SSH primitive.
 root=a.capture_directory
 require(root.parent==Path('/private/tmp') and re.fullmatch('lanl17-sparse-default-launch-[a-z0-9-]{1,80}',root.name) and not os.path.lexists(root),'fresh_private_local_route')
 root.mkdir(mode=0o700);require(stat.S_IMODE(root.lstat().st_mode)==0o700 and root.lstat().st_uid==os.geteuid(),'capture0700')
 tail=['--control-directory',str(control),'--expected-primary',a.expected_primary,'--plan',str(a.plan),'--plan-sha256',a.plan_sha256,'--attempt',a.attempt]
 for name in a.select:tail.extend(['--select',name])
 remote=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','90s','/usr/bin/python3.12','-B','-s','-c',BOOT,str(a.wrapper),str(a.guard),*tail]
 argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();started=now()
 prereg=original_json(root/'preregistration.json',{'format':'swdb.lanl17-sparse-default-launch-original-start.v1','sealed':False,'execution_not_yet_started':True,'started_utc':started,'public_argv':argv,'target_wrapper_argv':['/usr/bin/python3.12','-B',str(a.wrapper),'--source-sha256',WRAPPER_SHA,'--guard-source',str(a.guard),*tail],'bootstrap_sha256':sha(BOOT.encode()),'explicit_child_environment_overrides':{'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'},'child_startup_routing_and_GIT_overrides_removed':True,'HOME_CODEX_HOME_auth_or_full_environment_read_or_dumped':False,'source':ownpin,'parent_native':sshpin,'owned_SSH_cleanup_source':procspin,'selected_wrapper':{'path':str(a.wrapper),'bytes':24115,'sha256':WRAPPER_SHA},'selected_guard':{'path':str(a.guard),'bytes':166145,'sha256':GUARD_SHA},'local_wait_s':180,'GNU_remote_s':90,'GNU_KILL_s':60,'inherited_worker_wait_s':3735,'default_only':True,'selected_guard_completion_capacity_science_admission':False,'no_retry':True})
 watched=(signal.SIGTERM,signal.SIGHUP);previous={number:signal.getsignal(number) for number in watched}
 def capture_signal(number,frame):raise CaptureSignal(number)
 try:
  for number in watched:signal.signal(number,capture_signal)
  child=None;exitcode=None;failure=None;timedout=False;received_signal=None
  try:
   require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin,'immediate_immutable_sources')
   with private_file(root/'stdout') as out,private_file(root/'stderr') as err:
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,preexec_fn=ssh_file_limit)
    try:child.wait(timeout=180);exitcode=child.returncode
    except subprocess.TimeoutExpired:timedout=True;failure='TimeoutExpired'
  except BaseException as exc:
   failure=type(exc).__name__
   if isinstance(exc,CaptureSignal):received_signal=signal.Signals(exc.number).name
  finally:
   for number in watched:signal.signal(number,signal.SIG_IGN)
   try:helpers.stop_group(child,grace_seconds=15)
   except BaseException as exc:failure='OwnedSSHCleanup:'+type(exc).__name__
  result={'format':'swdb.lanl17-sparse-default-launch-original-transport.v1','sealed':False,'started_utc':started,'ended_utc':now(),'preregistration':prereg,'SSH_exit_code':exitcode,'timed_out':timedout,'signal_received':received_signal,'failure_type':failure,'original_private_streams':{n:stream_pin(root/n) for n in ('stdout','stderr') if (root/n).exists()},'remote_guard_completion_not_assessed':True,'remote_descendant_cleanup_not_inferred_from_SSH_exit':True,'default_or_capacity_or_scientific_admission':False,'source_unchanged':False}
  require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin,'postflight_local_source_SSH_pins')
  result['source_unchanged']=True;resultpin=original_json(root/'status.json',result)
  compact={'status_file':resultpin,'SSH_exit_code':exitcode,'timed_out':timedout,'signal_received':received_signal,'failure_type':failure,'selected_guard_completion_not_assessed':True,'postflight_remote_original_receipts_required':True}
  raw=json.dumps(compact,separators=(',',':'),allow_nan=False).encode();require(len(raw)<=MAX_RETURN,'compact_return_bound');sys.stdout.buffer.write(raw+b'\n')
  return 0 if exitcode==0 and failure is None and not timedout else 2
 finally:
  for number,handler in previous.items():signal.signal(number,handler)
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as exc:
  print(json.dumps({'status':'local_refusal','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'selected_guard_completion_not_assessed':True},separators=(',',':')));raise SystemExit(2)
'''
text=prefix+"WRAPPER_SHA='1127d1fba8e004153cf086cace7d19ccd901e85902f9ad91924407922c85c6ca'\nGUARD_SHA='4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'\nBOOT="+repr(boot)+'\n'+main
# Newly created metadata remains bounded16KiB; original stream/source caps unchanged.
text=text.replace("require(len(raw)<=MAX_SOURCE,'original_metadata_bound')","require(len(raw)<=MAX_RETURN,'original_metadata_bound')")
ast.parse(text);ast.parse(boot)
fd=os.open(new,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(text)
diff=D/'lanl17-sparse-default-launch-capture-complete-readerR1-derivation-20261008-a1.diff'
raw=''.join(difflib.unified_diff(old.read_text().splitlines(True),text.splitlines(True),fromfile=str(old),tofile=str(new))).encode()
fd=os.open(diff,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw)
for p in [new,diff]:b=p.read_bytes();print(str(p),len(b),hashlib.sha256(b).hexdigest())
