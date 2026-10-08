"""SOURCE ONLY: ONE parent-local administrative-ref fetch and ONE two-source stdin copy.
No selected guard/wrapper main, default, retirement, capacity or science admission.
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
BOOTSTRAP_SHA='345159afa21734985a9c465602b193d357e9a0a2b8b47ef02b2e8e9fbd4f4932'
COPIER_SHA='9f8e43a01b4be0567ce7c637509222c0903481bea8dd9d6b82dfaf6de79af9de'
EVIDENCE='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-sparse-read-budget-custody-correction-20261008-a1'
PRESTARTUP="for key in \"${!GIT_@}\"; do unset \"$key\" || exit 2; done\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT PYTHONOPTIMIZE LD_PRELOAD LD_LIBRARY_PATH BASH_ENV ENV || exit 2\nexport PATH=/usr/bin:/bin:/usr/local/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONSAFEPATH=1\nexec \"$@\"\n"
FETCH_SOURCE="import datetime,hashlib,json,os,pwd,re,selectors,signal,stat,subprocess,sys,time\nfrom pathlib import Path\nUID=114316761\nBASE=Path('/data1/yanruj')\nPRIMARY=BASE/'ArchEvolve'\nFROZEN='5e12a9796432654d88def24ecea617d16ca605b2'\nADMIN_REF='refs/remotes/origin/codex/lanl17-storage-guard-cost'\nSTOP_SIGNAL=None\nMAX_TOTAL=16*1024*1024\nNATIVES={Path('/usr/bin/git'):(4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),Path('/usr/bin/python3.12'):(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),Path('/usr/bin/bash'):(1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),Path('/usr/bin/timeout'):(39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52')}\nclass Refused(Exception):pass\ndef interrupted(signum,frame):\n    global STOP_SIGNAL\n    if STOP_SIGNAL is None:STOP_SIGNAL=signum\n    for name in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(name,signal.SIG_IGN)\ndef require(ok,code):\n    if not ok:raise Refused(code)\ndef sha(b):return hashlib.sha256(b).hexdigest()\ndef stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}\ndef identity(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid')}\ndef canonical(p):\n    require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'noncanonical_route')\ndef private_base():\n    canonical(BASE);s=BASE.lstat()\n    require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700,'private_base_identity')\n    return identity(s)\ndef read(p,cap,owner,mode=None):\n    canonical(p);s=p.lstat()\n    require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and not s.st_mode&0o7000 and s.st_size<=cap,'regular_file_identity_or_cap')\n    if mode is not None:require(stat.S_IMODE(s.st_mode)==mode,'regular_file_mode')\n    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)\n    with os.fdopen(fd,'rb') as f:\n        b=f.read(cap+1);require(len(b)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'returned_byte_stat_drift')\n    return b,stamp(s)\ndef core_state():\n    base=private_base();canonical(PRIMARY);canonical(PRIMARY/'.git')\n    for p in (PRIMARY,PRIMARY/'.git'):\n        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and s.st_dev==base['dev'] and not s.st_mode&0o5000,'primary_directory_identity')\n        require(not s.st_mode&0o2000 or s.st_gid==base['gid'],'primary_directory_setgid_identity')\n    native={}\n    for p,(size,digest) in NATIVES.items():\n        b,s=read(p,16*1024*1024,0,0o755);require(len(b)==size and sha(b)==digest,'native_pin');native[str(p)]={'sha256':digest,'stat':s}\n    config_b,config_s=read(PRIMARY/'.git/config',256*1024,UID)\n    retention_b,retention_s=read(PRIMARY/'swdb-project/records/.retention.lock',0,UID)\n    require(retention_b==b'','nonempty_original_retention')\n    return {'base_identity':base,'primary_stat':stamp(PRIMARY.lstat()),'common_stat':stamp((PRIMARY/'.git').lstat()),\n            'config':{'bytes':len(config_b),'sha256':sha(config_b),'stat':config_s},\n            'retention':{'bytes':0,'sha256':sha(retention_b),'stat':retention_s},'native':native}\ndef stop(p):\n    if p.poll() is not None:return\n    try:os.killpg(p.pid,signal.SIGTERM)\n    except ProcessLookupError:pass\n    try:p.wait(timeout=5)\n    except subprocess.TimeoutExpired:\n        try:os.killpg(p.pid,signal.SIGKILL)\n        except ProcessLookupError:pass\n        p.wait(timeout=5)\ndef git(*args,allowed=(0,),fetch=False):\n    require(STOP_SIGNAL is None and time.monotonic()<DEADLINE,'copy_interrupted_or_deadline')\n    env=dict(os.environ);env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1',GIT_PAGER='cat')\n    p=subprocess.Popen(['/usr/bin/git','--no-replace-objects','--no-pager','-c','core.fsmonitor=false','-C',str(PRIMARY),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)\n    sel=selectors.DefaultSelector();out=bytearray();err=bytearray();end=min(DEADLINE,time.monotonic()+(120 if fetch else 30))\n    for f,buf in ((p.stdout,out),(p.stderr,err)):os.set_blocking(f.fileno(),False);sel.register(f,selectors.EVENT_READ,buf)\n    try:\n        while sel.get_map():\n            require(STOP_SIGNAL is None and time.monotonic()<end,'readonly_git_interrupted_or_timeout')\n            for key,_ in sel.select(min(0.2,max(0,end-time.monotonic()))):\n                b=os.read(key.fileobj.fileno(),65536)\n                if not b:sel.unregister(key.fileobj);continue\n                key.data.extend(b);require(len(out)+len(err)<=MAX_TOTAL,'readonly_git_stream_cap')\n        p.wait(timeout=max(0.01,min(5,DEADLINE-time.monotonic())))\n        require(STOP_SIGNAL is None and p.returncode in allowed and (fetch or not err),'readonly_git_refused_warning_or_interrupted')\n        return (bytes(out),bytes(err)) if fetch else bytes(out)\n    finally:\n        sel.close();stop(p);p.stdout.close();p.stderr.close()\ndef refs():\n    require(git('rev-parse','HEAD').strip().decode()==FROZEN and git('symbolic-ref','--short','HEAD').strip()==b'yanrujhou_main','frozen_primary_head')\n    for ref in ('refs/heads/yanrujhou_main','refs/remotes/origin/yanrujhou_main','refs/remotes/origin/codex/lanl-analytic-eval'):\n        require(git('rev-parse','--verify',ref).strip().decode()==FROZEN,'frozen_main_ref')\n    require(git('status','--porcelain=v1','--untracked-files=all')==b'?? swdb-project/records/.retention.lock\\n','primary_tracked_or_untracked_change')\n    require(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'primary_tracked_change')\n    return sha(git('for-each-ref','--format=%(refname) %(objectname)'))\ndef ref_inventory():\n raw=git('for-each-ref','--format=%(refname) %(objectname)');rows={}\n for line in raw.splitlines():\n  name,value=line.decode().split(' ');require(name not in rows and re.fullmatch('[a-f0-9]{40}',value),'ref_inventory_shape');rows[name]=value\n return rows\ntry:\n DEADLINE=time.monotonic()+180;os.umask(0o077)\n for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(sig,interrupted)\n require(os.uname().sysname=='Linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','account_or_host')\n require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode and not sys.flags.optimize,'actual_native_python_flags')\n require(not any(k.startswith('GIT_') for k in os.environ) and not any(os.environ.get(k) for k in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','BASH_ENV','ENV')),'prestartup_routing_override')\n require(len(sys.argv)==2 and re.fullmatch('[a-f0-9]{40}',sys.argv[1]) and sys.argv[1]!=FROZEN,'actual_administrative40');revision=sys.argv[1]\n before=core_state();refs();oldrefs=ref_inventory();started=datetime.datetime.now(datetime.timezone.utc).isoformat()\n out,err=git('fetch','--no-tags','--no-write-fetch-head','--no-auto-maintenance','--recurse-submodules=no','origin','refs/heads/codex/lanl17-storage-guard-cost:'+ADMIN_REF,fetch=True)\n sys.stdout.buffer.write(out);sys.stdout.buffer.flush();sys.stderr.buffer.write(err);sys.stderr.buffer.flush()\n require(STOP_SIGNAL is None,'fetch_interrupted');refs();newrefs=ref_inventory();after=core_state()\n expected=dict(oldrefs);expected[ADMIN_REF]=revision;require(newrefs==expected,'only_expected_administrative_ref_changed')\n git('merge-base','--is-ancestor',FROZEN,revision)\n for key in ('base_identity','primary_stat','config','retention','native'):require(after[key]==before[key],'fetch_source_native_config_retention_drift')\n require(identity(PRIMARY.joinpath('.git').lstat())=={k:before['common_stat'][k] for k in ('dev','ino','mode','uid','gid')},'fetch_common_identity_drift')\n receipt={'format':'swdb.lanl17-original-administrative-ref-fetch.v1','sealed':False,'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_primary40':FROZEN,'administrative40':revision,'administrative_ref':ADMIN_REF,'before_refs_sha256':sha(json.dumps(oldrefs,sort_keys=True,separators=(',',':')).encode()),'after_refs_sha256':sha(json.dumps(newrefs,sort_keys=True,separators=(',',':')).encode()),'ref_change_only_exact_admin':True,'before_state':before,'after_state':after,'native_fetch_stdout':{'bytes':len(out),'sha256':sha(out)},'native_fetch_stderr':{'bytes':len(err),'sha256':sha(err)},'selected_control_mains_called':False,'cleanup_capacity_or_scientific_admission':False}\n raw=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode();require(len(raw)+1<=16384,'fetch_receipt_bound');sys.stdout.buffer.write(raw+b'\\n')\nexcept (Refused,OSError,ValueError,UnicodeError,subprocess.SubprocessError) as exc:\n print(json.dumps({'format':'swdb.lanl17-original-administrative-ref-fetch-refusal.v1','sealed':False,'error_class':type(exc).__name__,'error_digest':hashlib.sha256(str(exc).encode()).hexdigest(),'received_signal':STOP_SIGNAL}));raise SystemExit(1)\n"
def main():
 os.umask(0o077);p=Parser(description='SOURCE ONLY: ONE exact admin-ref fetch and ONE Git two-source copy; no selected guard/wrapper mains')
 for name in ('source-sha256','ssh-sha256','bootstrap-sha256','administrative40','destination'):p.add_argument('--'+name,required=True)
 for name in ('bootstrap','local-processes','capture-directory'):p.add_argument('--'+name,required=True,type=Path)
 p.add_argument('--ssh-bytes',required=True,type=int);a=p.parse_args()
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_local_flags')
 for value in (a.source_sha256,a.ssh_sha256,a.bootstrap_sha256):require(re.fullmatch('[a-f0-9]{64}',value),'explicit_source_native_pin')
 require(a.bootstrap_sha256==BOOTSTRAP_SHA and re.fullmatch('[a-f0-9]{40}',a.administrative40) and a.administrative40!='5e12a9796432654d88def24ecea617d16ca605b2','selected_bootstrap_administrative40')
 dest=Path(a.destination);require(dest.parent==Path('/data1/yanruj') and re.fullmatch('lanl17-sparse-retirement-source-[a-z0-9-]{1,80}',dest.name),'exact_fresh_destination_route')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0);require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'actual_local_nativeSSH')
 bootpin,boot=read_exact(a.bootstrap,BOOTSTRAP_SHA,MAX_SOURCE,os.geteuid());require(bootpin['bytes']==5620,'selected_bootstrap_bytes')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid());require(procspin['bytes']==912,'reviewed_owned_SSH_source')
 helpers=types.ModuleType('lanl17_admin_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future exact original owned-local-SSH primitive only.
 root=a.capture_directory;require(root.parent==Path('/private/tmp') and re.fullmatch('lanl17-sparse-admin-fetch-copy-[a-z0-9-]{1,80}',root.name) and not os.path.lexists(root),'fresh_private_capture')
 root.mkdir(mode=0o700);require(root.lstat().st_uid==os.geteuid() and stat.S_IMODE(root.lstat().st_mode)==0o700,'capture0700')
 copyargs=['--copier-source-bytes','12028','--copier-source-sha256',COPIER_SHA,'--administrative40',a.administrative40,'--evidence-directory',EVIDENCE,'--destination',str(dest),'--guard-basename','lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py','--guard-bytes','180887','--guard-sha256',GUARD_SHA,'--wrapper-basename','lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py','--wrapper-bytes','24114','--wrapper-sha256',WRAPPER_SHA]
 stages=[('fetch',FETCH_SOURCE.encode(),[a.administrative40]),('copy',boot,copyargs)];completed=[]
 watched=(signal.SIGTERM,signal.SIGHUP);previous={n:signal.getsignal(n) for n in watched}
 def capture_signal(number,frame):raise CaptureSignal(number)
 try:
  for number in watched:signal.signal(number,capture_signal)
  for stage,payload,tail in stages:
   folder=root/stage;folder.mkdir(mode=0o700)
   target=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','600s','/usr/bin/python3.12','-B','-s','-',*tail]
   remote=['/usr/bin/bash','--noprofile','--norc','-p','-c',PRESTARTUP,'reviewed-sparse-administrative-prestartup',*target]
   argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
   now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();started=now()
   prereg=original_json(folder/'preregistration.json',{'format':'swdb.lanl17-original-admin-fetch-copy-start.v1','sealed':False,'stage':stage,'started_utc':started,'execution_not_yet_started':True,'public_argv':argv,'stdin_source':{'bytes':len(payload),'sha256':sha(payload)},'source':ownpin,'parent_nativeSSH':sshpin,'bootstrap':bootpin,'ownedSSH_cleanup_source':procspin,'prestartup_sha256':sha(PRESTARTUP.encode()),'explicit_child_environment_overrides':{'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONSAFEPATH':'1'},'HOME_CODEX_HOME_auth_fullenv_read_or_dumped':False,'prestartup_native_Bash_timeout_Python_review_required':True,'administrative40':a.administrative40,'destination':str(dest),'GNU_s':600,'GNU_KILL_s':60,'local_wait_s':720,'selected_guard_wrapper_mains_called':False,'no_retry':True,'no_admission':True})
   child=None;exitcode=None;failure=None;timedout=False;received_signal=None
   try:
    require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin and read_exact(a.bootstrap,BOOTSTRAP_SHA,MAX_SOURCE,os.geteuid())[0]==bootpin,'immediate_local_source_pins')
    with private_file(folder/'stdout') as out,private_file(folder/'stderr') as err:
     child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True,preexec_fn=ssh_file_limit)
     try:child.communicate(input=payload,timeout=720);exitcode=child.returncode
     except subprocess.TimeoutExpired:timedout=True;failure='TimeoutExpired'
   except BaseException as exc:
    failure=type(exc).__name__
    if isinstance(exc,CaptureSignal):received_signal=signal.Signals(exc.number).name
   finally:
    for number in watched:signal.signal(number,signal.SIG_IGN)
    try:helpers.stop_group(child,grace_seconds=15)
    except BaseException as exc:failure='OwnedSSHCleanup:'+type(exc).__name__
   result={'format':'swdb.lanl17-original-admin-fetch-copy-transport.v1','sealed':False,'stage':stage,'started_utc':started,'ended_utc':now(),'preregistration':prereg,'SSH_exit_code':exitcode,'timed_out':timedout,'signal_received':received_signal,'failure_type':failure,'original_private_streams':{n:stream_pin(folder/n) for n in ('stdout','stderr') if (folder/n).exists()},'remote_descendant_cleanup_not_inferred_from_SSH_exit':True,'selected_guard_wrapper_mains_called':False,'no_admission':True}
   require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin and read_exact(a.bootstrap,BOOTSTRAP_SHA,MAX_SOURCE,os.geteuid())[0]==bootpin,'postflight_local_source_pins')
   statuspin=original_json(folder/'status.json',result);completed.append({'stage':stage,'status_file':statuspin,'SSH_exit_code':exitcode,'failure_type':failure,'timed_out':timedout})
   if exitcode!=0 or failure is not None or timedout:break
   for number in watched:signal.signal(number,capture_signal)
  compact={'format':'swdb.lanl17-original-admin-fetch-copy-return.v1','sealed':False,'stages':completed,'selected_guard_wrapper_mains_called':False,'actual_remote_receipt_review_required':True,'no_admission':True}
  raw=json.dumps(compact,separators=(',',':')).encode();require(len(raw)+1<=MAX_RETURN,'compact_return_bound');sys.stdout.buffer.write(raw+b'\n')
  return 0 if len(completed)==2 and all(x['SSH_exit_code']==0 and x['failure_type'] is None and not x['timed_out'] for x in completed) else 2
 finally:
  for number,handler in previous.items():signal.signal(number,handler)
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as exc:
  print(json.dumps({'status':'local_refusal','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'no_admission':True},separators=(',',':')));raise SystemExit(2)
