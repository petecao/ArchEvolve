"""SOURCE ONLY parent-local private capture for ONE future reviewed reader.
This source cannot clear remote export/admission gates or authorize its own run.
"""
import argparse,datetime,hashlib,json,os,re,resource,shlex,stat,subprocess,sys,types
from pathlib import Path
MAX_SOURCE=1024*1024
MAX_STREAM=16*1024*1024
MAX_RETURN=16384
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES')
class Refusal(ValueError):pass
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
 require(len(raw)<=MAX_SOURCE,'original_metadata_bound')
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
def main():
 os.umask(0o077)
 p=Parser(description=__doc__)
 for n in ('source-sha256','bootstrap-sha256','ssh-sha256','expected-primary','export-commit','receipt-sha256','receipt-identity-sha256','report-relative'):p.add_argument('--'+n,required=True)
 for n in ('bootstrap','local-processes','capture-directory'):p.add_argument('--'+n,required=True,type=Path)
 p.add_argument('--ssh-bytes',required=True,type=int)
 p.add_argument('--metadata-seconds',required=True,type=int)
 p.add_argument('--outer-seconds',required=True,type=int)
 a=p.parse_args()
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_local_account_flags')
 for value in (a.source_sha256,a.bootstrap_sha256,a.ssh_sha256,a.receipt_sha256,a.receipt_identity_sha256):require(re.fullmatch('[a-f0-9]{64}',value),'exact_SHA')
 for value in (a.expected_primary,a.export_commit):require(re.fullmatch('[a-f0-9]{40}',value),'exact_commit')
 require(60<=a.metadata_seconds<=3600 and 2*a.metadata_seconds+15300<=a.outer_seconds<=24000,'explicit_outer_pre_post_reserve')
 require(a.report_relative in {'.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-generality-final-final-20261007-a1-report.json','.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-generality-final-final-20261007-a1-report.json.gz'},'actual_report_route')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 bootpin,boot=read_exact(a.bootstrap,a.bootstrap_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0)
 require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'actual_local_SSH_executable_pin')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid())
 require(procspin['bytes']==912,'existing_local_owned_SSH_cleanup_source')
 helpers=types.ModuleType('lanl14_reader_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future metadata-only primitive reuse.
 root=a.capture_directory
 require(root.is_absolute() and root.parent==Path('/private/tmp') and re.fullmatch('lanl14-reader-ssh-capture-[a-z0-9-]{1,80}',root.name) and not root.exists() and not root.is_symlink(),'fresh_private_local_route')
 root.mkdir(mode=0o700);require(stat.S_IMODE(root.lstat().st_mode)==0o700 and root.lstat().st_uid==os.geteuid(),'capture0700')
 # Hash verified before parsing/executing returned stdin; no source-copy family.
 loader="import hashlib,sys; b=sys.stdin.buffer.read(1048577); pin=sys.argv[1]; (len(b)<=1048576 and hashlib.sha256(b).hexdigest()==pin) or sys.exit(2); sys.argv=sys.argv[2:]; exec(compile(b,'<reviewed-reader-stdin-bootstrap>','exec'),{'__name__':'__main__','__file__':'<reviewed-reader-stdin-bootstrap>','__source_sha256__':pin})"
 remote=['/usr/bin/python3.12','-B','-c',loader,a.bootstrap_sha256,'reviewed-reader-bootstrap','--expected-primary',a.expected_primary,'--export-commit',a.export_commit,'--receipt-sha256',a.receipt_sha256,'--receipt-identity-sha256',a.receipt_identity_sha256,'--report-relative',a.report_relative,'--metadata-seconds',str(a.metadata_seconds)]
 argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
 started=now()
 prereg=original_json(root/'preregistration.json',{'format':'swdb.lanl14-original-parent-reader-SSH-capture.v1','sealed':False,'execution_not_yet_started':True,'started_utc':started,'public_argv':argv,'explicit_environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},'inherited_environment_or_auth_dumped':False,'parent_native':sshpin,'source':ownpin,'remote_bootstrap':bootpin,'owned_SSH_cleanup_source':procspin,'outer_seconds':a.outer_seconds,'metadata_preflight_s':a.metadata_seconds,'metadata_postflight_reserve_s':a.metadata_seconds,'GNU_remote_s':14520,'GNU_KILL_s':60,'unchanged_reader_wait_s':14400,'private_local_stream_max_bytes':MAX_STREAM,'remote_native_initial_startup_pin_is_separate_parent_preflight':True,'admission_assessed':False,'scientific_admission':False,'no_retry':True})
 child=None;exitcode=None;failure=None;timedout=False
 try:
  require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(a.bootstrap,a.bootstrap_sha256,MAX_SOURCE,os.geteuid())[0]==bootpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin,'immediate_immutable_sources')
  with private_file(root/'stdout') as out,private_file(root/'stderr') as err:
   child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},preexec_fn=ssh_file_limit)
   try:child.communicate(input=boot,timeout=a.outer_seconds);exitcode=child.returncode
   except subprocess.TimeoutExpired:timedout=True;failure='TimeoutExpired'
 except BaseException as exc:failure=type(exc).__name__
 finally:
  # This original primitive terminates only the owned local SSH group; it does
  # not prove remote descendants ended. Original503f + parent follow-up own that.
  try:helpers.stop_group(child,grace_seconds=15)
  except BaseException as exc:failure='OwnedSSHCleanup:'+type(exc).__name__
 result={'format':'swdb.lanl14-original-parent-reader-SSH-capture-result.v1','sealed':False,'started_utc':started,'ended_utc':now(),'preregistration':prereg,'SSH_exit_code':exitcode,'timed_out':timedout,'failure_type':failure,'original_private_streams':{n:stream_pin(root/n) for n in ('stdout','stderr') if (root/n).exists()},'remote_reader_admission_not_assessed':True,'remote_descendant_cleanup_not_inferred_from_SSH_exit':True,'scientific_admission':False,'source_unchanged':False}
 require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(a.bootstrap,a.bootstrap_sha256,MAX_SOURCE,os.geteuid())[0]==bootpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin,'postflight_local_source_SSH_pins')
 result['source_unchanged']=True
 resultpin=original_json(root/'status.json',result)
 compact={'status_file':resultpin,'SSH_exit_code':exitcode,'timed_out':timedout,'failure_type':failure,'scientific_admission':False,'postflight_remote_original_receipts_required':True}
 raw=json.dumps(compact,separators=(',',':'),allow_nan=False).encode();require(len(raw)<=MAX_RETURN,'compact_return_bound');sys.stdout.buffer.write(raw+b'\n')
 return 0 if exitcode==0 and failure is None and not timedout else 2
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as exc:
  print(json.dumps({'status':'local_refusal','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'scientific_admission':False},separators=(',',':')));raise SystemExit(2)
