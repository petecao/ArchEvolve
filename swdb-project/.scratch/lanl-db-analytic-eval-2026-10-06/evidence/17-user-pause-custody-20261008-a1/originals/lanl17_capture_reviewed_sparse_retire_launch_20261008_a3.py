"""SOURCE ONLY: parent-local private capture for ONE future sparse retirement launch.
No guard completion, retirement, capacity or science admission is inferred.
"""
import argparse,datetime,hashlib,json,os,re,resource,shlex,signal,stat,subprocess,sys,types
from pathlib import Path
MAX_SOURCE=1024*1024
MAX_STREAM=16*1024*1024
MAX_RETURN=16384
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES')
class Refusal(ValueError):pass
class CaptureSignal(BaseException):
 def __init__(self,number):self.number=number
class Parser(argparse.ArgumentParser):
 def error(self,message):raise Refusal('argument_contract')
def require(ok,code):
 if not ok:raise Refusal(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def read_exact(path,expected,maximum,owner):
 path=Path(path);require(path.is_absolute() and '..' not in path.parts,'absolute_path')
 for p in (path,*path.parents):require(not p.is_symlink(),'no_symlink')
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1 and not before.st_mode&0o022 and 0<before.st_size<=maximum,'source_owner_mode_size')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  require(stamp(os.fstat(fd))==stamp(before),'opened_stat')
  blocks=[];total=0
  while total<=maximum:
   b=os.read(fd,min(1024*1024,maximum-total+1))
   if not b:break
   blocks.append(b);total+=len(b)
  raw=b''.join(blocks)
  require(len(raw)==before.st_size and sha(raw)==expected and stamp(os.fstat(fd))==stamp(before)==stamp(path.lstat()),'returned_bytes')
 finally:os.close(fd)
 return {'path':str(path),'bytes':len(raw),'sha256':expected,'stat':stamp(before)},raw

def private_file(path):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 require(stat.S_IMODE(os.fstat(fd).st_mode)==0o600,'private0600');return os.fdopen(fd,'wb')
def original_json(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
 require(len(raw)<=MAX_RETURN,'original_metadata_bound')
 with private_file(path) as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {'path':str(path),'bytes':len(raw),'sha256':sha(raw),'sealed':False}
def stream_pin(path):
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid() and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and before.st_size<=MAX_STREAM,'private_original_stream')
 h=hashlib.sha256()
 with path.open('rb') as f:
  require(stamp(os.fstat(f.fileno()))==stamp(before),'stream_open_stat')
  while block:=f.read(1024*1024):h.update(block)
  require(stamp(os.fstat(f.fileno()))==stamp(before)==stamp(path.lstat()),'stream_closed_stat')
 return {'path':str(path),'bytes':before.st_size,'sha256':h.hexdigest(),'mode':'0600','sealed':False}
def ssh_file_limit():resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_STREAM,MAX_STREAM))
WRAPPER_SHA='e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec'
GUARD_SHA='d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
BOOT="import hashlib,json,os,re,sys,stat\nfrom pathlib import Path\nUID=114316761\nBASE=Path('/data1/yanruj')\nW_SHA='e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec'\nG_SHA='d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'\ndef stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))\ndef exact(p,size,digest,owner,mode):\n assert p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))\n s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==mode and s.st_size==size\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)\n with os.fdopen(fd,'rb') as f:\n  b=f.read(size+1);assert len(b)==size and hashlib.sha256(b).hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())\n return stamp(s)\nassert os.uname().sysname=='Linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and not sys.flags.optimize\nassert Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12')\nassert BASE.resolve(strict=True)==BASE and not any(q.is_symlink() for q in (BASE,*BASE.parents))\ns=BASE.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700\nwrapper=Path(sys.argv[1]);guard=Path(sys.argv[2]);receipt_sha=sys.argv[3];receipt_id=sys.argv[4];receipt_size=int(sys.argv[5]);tail=sys.argv[6:]\nassert wrapper.parent==guard.parent and wrapper.parent.parent==BASE and wrapper.parent.name.startswith('lanl17-sparse-retirement-source-')\np=wrapper.parent;s=p.lstat();assert p.resolve(strict=True)==p and not p.is_symlink() and stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700\nassert wrapper.name=='lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py'\nassert guard.name=='lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py'\nwp=exact(wrapper,24114,W_SHA,UID,0o600);gp=exact(guard,180887,G_SHA,UID,0o600)\nfor p,size,digest in [(Path('/usr/bin/python3.12'),8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),(Path('/usr/bin/timeout'),39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),(Path('/usr/bin/bash'),1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1')]:exact(p,size,digest,0,0o755)\nfor key in list(os.environ):\n if key.startswith('GIT_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','BASH_ENV','ENV'):os.environ.pop(key)\nos.environ['PATH']='/usr/bin:/bin:/usr/local/bin'\nos.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PYTHONNOUSERSITE']='1'\nassert exact(wrapper,24114,W_SHA,UID,0o600)==wp and exact(guard,180887,G_SHA,UID,0o600)==gp\ndef strict(raw):\n def pairs(rows):\n  d={}\n  for k,v in rows:assert k not in d;d[k]=v\n  return d\n return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))\ndef original(p,cap,digest,size=None):\n assert p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))\n s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=cap\n assert size is None or s.st_size==size\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)\n with os.fdopen(fd,'rb') as f:\n  raw=f.read(cap+1);assert len(raw)==s.st_size and hashlib.sha256(raw).hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())\n return raw,{'path':str(p),'bytes':len(raw),'sha256':digest,'stat':{k:getattr(s,'st_'+k) for k in ('dev','ino','mode','nlink','uid','gid','size','mtime_ns','ctime_ns')}}\ndef option(name):\n assert tail.count(name)==1 and tail.index(name)+1<len(tail)\n return tail[tail.index(name)+1]\nassert wrapper.parent==BASE/'lanl17-sparse-retirement-source-20261008-a2'\nassert tail.count('--retire')==1 and re.fullmatch('[a-f0-9]{64}',receipt_sha) and re.fullmatch('[a-f0-9]{64}',receipt_id) and 0<receipt_size<=262144\ninspection=Path(option('--inspection-directory'));assert inspection==BASE/'lanl17-detached-sparse-default-a3'\nassert inspection.resolve(strict=True)==inspection and not any(q.is_symlink() for q in (inspection,*inspection.parents))\nins=inspection.lstat();assert stat.S_ISDIR(ins.st_mode) and ins.st_uid==UID and stat.S_IMODE(ins.st_mode)==0o700\ncontrol=Path(option('--control-directory'));assert control!=inspection and option('--attempt')!='a3'\nassert Path(option('--plan'))!=BASE/'lanl-sparse-retirement-parent-plan-20261008-a3.json'\nrows=[tail[i+1] for i,v in enumerate(tail) if v=='--select'];expected=option('--expected-primary')\nsraw,spin=original(inspection/'status.json',16384,option('--inspection-status-sha256'))\noraw,opin=original(inspection/'guard.stdout',262144,option('--inspection-stdout-sha256'))\nstatus=strict(sraw);returned=strict(oraw)\nassert status['format']=='swdb.lanl17-detached-library-sparse-administration-status.v1' and status['sealed'] is False and status['state']=='guard_completed' and type(status['guard_exit_code']) is int and status['guard_exit_code']==0 and status['retire_requested'] is False and 'error_class' not in status\nassert status['expected_primary']==expected and status['selected_rows']==rows and status['guard_attempt']=='a3' and status['guard_stdout']==opin\nassert status['inputs']['wrapper']['sha256']==W_SHA and status['inputs']['wrapper']['bytes']==24114 and status['inputs']['guard']['sha256']==G_SHA and status['inputs']['guard']['bytes']==180887\nassert status['inputs']['service_review']['sha256']=='fcf92eee1c4b8bdfaed979dc8bedab004c6c4b7e2b1410c7614bc92d60349f4a'\noldplan=status['reviewed_plan'];assert oldplan['file']['path']==str(BASE/'lanl-sparse-retirement-parent-plan-20261008-a3.json') and oldplan['file']['sha256']=='e2fb42a2bde17b3d9aab4c0d2121903a22dd3d7f29d7caab85acf22638677c02' and oldplan['identity_sha256']=='4d3e5845e0a844d5181d0c6025f49c955ccbdcdc64b03491b78b01519765cd58'\nrpath=BASE/'lanl-library-preserving-sparse-retirement-20261008-a3/receipt.json'\nassert returned['format']=='swdb.library-preserving-sparse-retirement-return.v1' and returned['path']==str(rpath) and returned['sha256']==receipt_sha and returned['identity_sha256']==receipt_id and type(returned['bytes']) is int and returned['bytes']==receipt_size and returned['admitted'] is True and type(returned['retired_count']) is int and returned['retired_count']==0 and returned['failure'] is None\nrs=rpath.parent.lstat();assert rpath.parent.resolve(strict=True)==rpath.parent and not any(q.is_symlink() for q in (rpath.parent,*rpath.parent.parents)) and stat.S_ISDIR(rs.st_mode) and rs.st_uid==UID and stat.S_IMODE(rs.st_mode)==0o700\nrraw,rpin=original(rpath,262144,receipt_sha,receipt_size);receipt=strict(rraw)\nencoded=json.dumps({k:v for k,v in receipt.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()\nassert receipt['format']=='swdb.library-preserving-sparse-retirement-guard.v1' and receipt['canonical_ensure_ascii'] is True and receipt['identity_sha256']==receipt_id==hashlib.sha256(encoded).hexdigest()\nassert receipt['retire_requested'] is False and receipt['admitted'] is True and receipt['retired_rows']==[] and receipt['failure'] is None and receipt['selected_rows']==rows and receipt['expected_primary']==expected and receipt['guard_source_sha256']==G_SHA and receipt['scientific_admission'] is False and receipt['capacity_admission'] is False\nassert receipt['reviewed_plan_file_sha256']==oldplan['file']['sha256'] and receipt['reviewed_plan_identity_sha256']==oldplan['identity_sha256']\nassert original(inspection/'status.json',16384,option('--inspection-status-sha256'))==(sraw,spin) and original(inspection/'guard.stdout',262144,option('--inspection-stdout-sha256'))==(oraw,opin) and original(rpath,262144,receipt_sha,receipt_size)==(rraw,rpin)\nassert stamp(inspection.lstat())==stamp(ins) and stamp(rpath.parent.lstat())==stamp(rs)\nos.umask(0o077)\nargv=['/usr/bin/python3.12','-B',str(wrapper),'--source-sha256',W_SHA,'--guard-source',str(guard),*tail]\nos.execv(argv[0],argv)\n"
PRESTARTUP="for key in \"${!GIT_@}\"; do unset \"$key\" || exit 2; done\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT PYTHONOPTIMIZE LD_PRELOAD LD_LIBRARY_PATH BASH_ENV ENV || exit 2\nexport PATH=/usr/bin:/bin:/usr/local/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONSAFEPATH=1\nexec \"$@\"\n"
def main():
 os.umask(0o077)
 p=Parser(description=__doc__)
 for n in ('source-sha256','ssh-sha256','expected-primary','plan-sha256','attempt','control-directory','inspection-status-sha256','inspection-stdout-sha256','inspection-receipt-sha256','inspection-receipt-identity-sha256'):p.add_argument('--'+n,required=True)
 for n in ('wrapper','guard','plan','local-processes','capture-directory','inspection-directory'):p.add_argument('--'+n,required=True,type=Path)
 p.add_argument('--ssh-bytes',required=True,type=int);p.add_argument('--inspection-receipt-bytes',required=True,type=int);p.add_argument('--select',action='append',required=True)
 a=p.parse_args()
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_local_account_flags')
 for v in (a.source_sha256,a.ssh_sha256,a.plan_sha256,a.inspection_status_sha256,a.inspection_stdout_sha256,a.inspection_receipt_sha256,a.inspection_receipt_identity_sha256):require(re.fullmatch('[a-f0-9]{64}',v),'exact_SHA')
 require(re.fullmatch('[a-f0-9]{40}',a.expected_primary) and re.fullmatch('a[1-9][0-9]*',a.attempt),'exact_revision_attempt')
 require(1<=len(a.select)<=18 and len(set(a.select))==len(a.select) and all(re.fullmatch('ArchEvolve-lanl-[A-Za-z0-9-]{1,96}',v) for v in a.select),'explicit_ordered_rows')
 base=Path('/data1/yanruj');control=Path(a.control_directory)
 require(control.parent==base and control.name.startswith('lanl17-detached-sparse-') and len(control.name)<=48,'explicit_private_control_route')
 require(a.wrapper.parent==a.guard.parent and a.wrapper.parent.parent==base and a.wrapper.parent.name.startswith('lanl17-sparse-retirement-source-'),'exact_future_private_source_route')
 require(a.wrapper.name=='lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py' and a.guard.name=='lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py','selected_G5_W2_basenames')
 require(a.plan.parent==base and a.plan.name.startswith('lanl-sparse-retirement-parent-plan-'),'exact_guard_plan_route')
 require(a.inspection_directory==base/'lanl17-detached-sparse-default-a3' and control!=a.inspection_directory and a.attempt!='a3','actual_prior_default_distinct_retirement_routes')
 require(a.wrapper.parent==base/'lanl17-sparse-retirement-source-20261008-a2' and 0<a.inspection_receipt_bytes<=262144,'exact_selected_copied_source_and_original_receipt_bound')
 require(a.plan!=base/'lanl-sparse-retirement-parent-plan-20261008-a3.json','separately_fresh_retirement_plan_required')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0);require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'actual_local_SSH_pin')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid());require(procspin['bytes']==912,'existing_local_owned_SSH_cleanup_source')
 helpers=types.ModuleType('lanl17_sparse_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future reuse of the exact reviewed owned-SSH primitive.
 root=a.capture_directory
 require(root.parent==Path('/private/tmp') and re.fullmatch('lanl17-sparse-retire-launch-[a-z0-9-]{1,80}',root.name) and not os.path.lexists(root),'fresh_private_local_route')
 root.mkdir(mode=0o700);require(stat.S_IMODE(root.lstat().st_mode)==0o700 and root.lstat().st_uid==os.geteuid(),'capture0700')
 tail=['--control-directory',str(control),'--expected-primary',a.expected_primary,'--plan',str(a.plan),'--plan-sha256',a.plan_sha256,'--attempt',a.attempt]
 for name in a.select:tail.extend(['--select',name])
 tail.extend(['--retire','--inspection-directory',str(a.inspection_directory),'--inspection-status-sha256',a.inspection_status_sha256,'--inspection-stdout-sha256',a.inspection_stdout_sha256])
 target=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','90s','/usr/bin/python3.12','-B','-s','-c',BOOT,str(a.wrapper),str(a.guard),a.inspection_receipt_sha256,a.inspection_receipt_identity_sha256,str(a.inspection_receipt_bytes),*tail]
 remote=['/usr/bin/bash','--noprofile','--norc','-p','-c',PRESTARTUP,'reviewed-sparse-prestartup',*target]
 argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();started=now()
 prereg=original_json(root/'preregistration.json',{'format':'swdb.lanl17-sparse-retire-launch-original-start.v1','sealed':False,'execution_not_yet_started':True,'started_utc':started,'actual_public_argv_sha256':sha(json.dumps(argv,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()),'actual_public_argv_serialization':'json separators comma/colon, ensure_ascii=True, ordered actual argv list','actual_public_argv_bytes':len(json.dumps(argv,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()),'actual_public_argv_count':len(argv),'SSH_option_argv':argv[:-1],'remote_command_bytes':len(argv[-1].encode()),'remote_command_sha256':sha(argv[-1].encode()),'target_wrapper_argv':['/usr/bin/python3.12','-B',str(a.wrapper),'--source-sha256',WRAPPER_SHA,'--guard-source',str(a.guard),*tail],'bootstrap_sha256':sha(BOOT.encode()),'prestartup_sanitizer_sha256':sha(PRESTARTUP.encode()),'prestartup_native_pins_are_separate_parent_preflight':True,'explicit_child_environment_overrides':{'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONSAFEPATH':'1'},'child_startup_routing_and_GIT_overrides_removed':True,'HOME_CODEX_HOME_auth_or_full_environment_read_or_dumped':False,'source':ownpin,'parent_native':sshpin,'owned_SSH_cleanup_source':procspin,'selected_wrapper':{'path':str(a.wrapper),'bytes':24114,'sha256':WRAPPER_SHA},'selected_guard':{'path':str(a.guard),'bytes':180887,'sha256':GUARD_SHA},'local_wait_s':180,'GNU_remote_s':90,'GNU_KILL_s':60,'inherited_worker_wait_s':3735,'retirement_requested':True,'original_default_custody_required':{'directory':str(a.inspection_directory),'status_sha256':a.inspection_status_sha256,'stdout_sha256':a.inspection_stdout_sha256,'receipt_sha256':a.inspection_receipt_sha256,'receipt_identity_sha256':a.inspection_receipt_identity_sha256,'receipt_bytes':a.inspection_receipt_bytes},'selected_guard_completion_capacity_science_admission':False,'no_retry':True})
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
  result={'format':'swdb.lanl17-sparse-retire-launch-original-transport.v1','sealed':False,'started_utc':started,'ended_utc':now(),'preregistration':prereg,'SSH_exit_code':exitcode,'timed_out':timedout,'signal_received':received_signal,'failure_type':failure,'original_private_streams':{n:stream_pin(root/n) for n in ('stdout','stderr') if (root/n).exists()},'remote_guard_completion_not_assessed':True,'remote_descendant_cleanup_not_inferred_from_SSH_exit':True,'default_or_capacity_or_scientific_admission':False,'source_unchanged':False}
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
