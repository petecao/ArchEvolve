"""Unexecuted ONE Linux early-exit7 lifecycle fixture, 2026-10-07 ET.

Direct a848 fixture derivative. Only exporter-mode shared supervise(...fixture=True)
is exercised. No selected exporter/reader main or scientific action is invoked.
All actual executable/source/output arguments await parent review.
"""
import argparse,hashlib,importlib.util,json,os,re,signal,socket,stat,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
SUPERVISOR_SHA='503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f'
UID=114316761
WORKER_WAIT_S=100
HARNESS_ALARM_S=240

class FixtureFailure(RuntimeError):pass
class FixtureDeadline(BaseException):pass
class PrivateParser(argparse.ArgumentParser):
 def error(self,message):raise FixtureFailure('fixture argument contract differs; argv omitted')

def require(condition,reason):
 if not condition:raise FixtureFailure(reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def seal(data):return {**data,'identity_sha256':digest(data)}

def checked(path,*,directory=False):
 path=Path(path)
 require(path.is_absolute() and '..' not in path.parts,'absolute fixture path required')
 for part in (path,*path.parents):require(not part.is_symlink(),'fixture symlink component refused')
 status=path.stat()
 require(status.st_uid==UID and (stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode)),'fixture UID/type differs')
 return path

def own_source(expected):
 require(re.fullmatch('[a-f0-9]{64}',expected) is not None,'explicit fixture source SHA required')
 path=checked(Path(__file__).absolute())
 require(0<path.stat().st_size<=8*1024*1024 and not path.stat().st_mode&0o022 and sha(path)==expected,'fixture source pin differs')
 return path

def load_supervisor(path,expected):
 path=checked(path)
 require(expected==SUPERVISOR_SHA and sha(path)==expected and not path.stat().st_mode&0o022,'selected R1 supervisor source differs')
 spec=importlib.util.spec_from_file_location('lanl14_early_nonzero_fixture_supervisor',path)
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 return module

def process_key(pid):
 try:
  folder=Path('/proc')/str(pid);fields=(folder/'stat').read_text().rsplit(')',1)[1].split()
  return {'pid':pid,'uid':folder.stat().st_uid,'start_time':fields[19],'state':fields[0],'ppid':int(fields[1]),'process_group':int(fields[2]),'session':int(fields[3])}
 except (FileNotFoundError,ProcessLookupError):return None

def private_file(path,raw):
 descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(descriptor,'wb') as stream:
  status=os.fstat(stream.fileno())
  require(status.st_uid==UID and stat.S_IMODE(status.st_mode)==0o600 and stat.S_ISREG(status.st_mode),'fixture private file differs')
  stream.write(raw);stream.flush();os.fsync(stream.fileno())

def wait_marker(path,cap=10):
 deadline=time.monotonic()+cap
 while not path.exists() and time.monotonic()<deadline:time.sleep(.02)
 require(path.exists(),'owned process marker missing')
 path=checked(path);require(stat.S_IMODE(path.stat().st_mode)==0o600 and path.stat().st_size<=8192,'marker privacy/bound differs')
 raw=path.read_bytes();value=json.loads(raw)
 require(value['canonical_ensure_ascii'] is False and seal({k:v for k,v in value.items() if k!='identity_sha256'})==value,'fixture marker False seal differs')
 return value,{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'identity_sha256':value['identity_sha256']}

def owned_child(args):
 # Called only as supervisor-owned synthetic session leader. No selected
 # exporter/reader code is imported or run in this role.
 own_source(args.fixture_sha)
 root=checked(args.output,directory=True);require(stat.S_IMODE(root.stat().st_mode)==0o700,'owned fixture directory privacy differs')
 leader=process_key(os.getpid());first=os.fork()
 if first==0:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  second=os.fork()
  if second==0:
   os.setsid()
   payload=seal({'format':'swdb.lanl14-early-nonzero-fixture-owned-processes.v1','fixture':True,'canonical_ensure_ascii':False,
    'leader':leader,'same_group':process_key(os.getppid()),'escaped_session':process_key(os.getpid()),'fixture_script_sha256':args.fixture_sha})
   temporary=root/('owned-children.'+str(os.getpid())+'.tmp')
   private_file(temporary,(json.dumps(payload,ensure_ascii=False)+'\n').encode())
   os.replace(temporary,root/'owned-children.json')  # Same-directory atomic publication.
  while True:time.sleep(1)
 wait_marker(root/'owned-children.json')
 os._exit(7)  # The ONE new path: returned nonzero leader, descendants still live.

def context(args):
 fixture=own_source(args.fixture_sha)
 m=load_supervisor(args.supervisor,args.supervisor_sha)
 ctx=m.load_context(args.helper,args.project,args.selected_source,'exporter',args.python,args.python_sha,args.cwd,args.supervisor_sha)
 require(m.CAPS=={'exporter':18000,'reader':14400},'production administrative caps changed')
 require(m.SOURCES['exporter']=='928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e','selected exporter source differs')
 return fixture,m,ctx

def worker(args):
 fixture,m,ctx=context(args);root=checked(args.output,directory=True)
 command=[str(ctx.python),'-B',str(fixture),'--owned-child','--fixture-sha',args.fixture_sha,'--output',str(root)]
 code,receipt=m.supervise(ctx,'exporter',command,timeout_s=18000,receipt=root/'supervisor-receipt.json',
  stdout=root/'supervisor-child.stdout',stderr=root/'supervisor-child.stderr',fixture=True)
 return code  # Actual supervisor/worker7 must remain visible; no success masking.

def harness(args):
 fixture,m,ctx=context(args)
 root=m.private_control_directory(args.output,ctx)
 prior={sig:signal.getsignal(sig) for sig in (*m.SIGNALS,signal.SIGALRM)}
 def interrupted(number,frame):raise FixtureDeadline(number)
 for sig in prior:signal.signal(sig,interrupted)
 signal.alarm(HARNESS_ALARM_S)
 sibling=None;child=None;results=[];started=m.now();passed=False;failure_type=None;subreaper_enabled=False
 cleanup={'subreaper':False,'survivors':{},'terminated_owned_processes':[],'scope':'No fixture child launched.'}
 observed={};worker_exit=None
 try:
  m.enable_subreaper();subreaper_enabled=True  # Before sibling or worker launch.
  with m.private_stream(root/'sibling.stdout') as out,m.private_stream(root/'sibling.stderr') as err:
   sibling=subprocess.Popen([str(ctx.python),'-B','-c','import time; time.sleep(300)'],stdout=out,stderr=err,start_new_session=True)
   sibling_before=process_key(sibling.pid)
   require(sibling_before and sibling_before['uid']==UID and sibling_before['ppid']==os.getpid(),'unrelated sibling ownership differs')
   observed['sibling_before']=sibling_before
   folder=root/'early-exit7';folder.mkdir(mode=0o700)
   require(stat.S_IMODE(checked(folder,directory=True).stat().st_mode)==0o700,'worker directory privacy differs')
   command=[str(ctx.python),'-B',str(fixture),'--worker','--fixture-sha',args.fixture_sha,
    '--supervisor',str(ctx.supervisor_path),'--supervisor-sha',args.supervisor_sha,'--helper',str(ctx.helper_path),
    '--project',str(ctx.project),'--selected-source',str(ctx.selected_path),'--python',str(ctx.python),'--python-sha',args.python_sha,
    '--cwd',str(ctx.cwd),'--output',str(folder)]
   with m.private_stream(folder/'worker.stdout') as worker_out,m.private_stream(folder/'worker.stderr') as worker_err:
    child=subprocess.Popen(command,stdout=worker_out,stderr=worker_err,start_new_session=True)
    worker_before=process_key(child.pid);observed['worker_before']=worker_before
    require(worker_before and worker_before['uid']==UID and worker_before['ppid']==os.getpid() and sibling_before['pid']!=worker_before['pid'],'worker/sibling ownership differs')
    marker,marker_pin=wait_marker(folder/'owned-children.json')
    keys={name:marker[name] for name in ('leader','same_group','escaped_session')};observed['owned_before']=keys
    require(marker['fixture'] is True and marker['fixture_script_sha256']==args.fixture_sha,'owned marker scope/source differs')
    require(all(row and row['uid']==UID for row in keys.values()),'fixture process UID differs')
    require(keys['leader']['ppid']==child.pid and keys['same_group']['ppid']==keys['leader']['pid'] and keys['escaped_session']['ppid']==keys['same_group']['pid'],'original descendant ancestry differs')
    require(keys['escaped_session']['session']==keys['escaped_session']['pid'] and keys['escaped_session']['session']!=keys['leader']['session'],'fixture did not escape session')
    require(keys['same_group']['session']==keys['leader']['session'] and keys['same_group']['process_group']==keys['leader']['process_group'],'fixture same-group identity differs')
    require(sibling_before['session'] not in {row['session'] for row in keys.values()} and sibling_before['ppid']==os.getpid(),'sibling is not outside worker ancestry/session')
    worker_exit=child.wait(timeout=WORKER_WAIT_S);observed['worker_exit']=worker_exit
   require(worker_exit==7,'original nonzero supervisor/worker exit differs')
   receipt_path=checked(folder/'supervisor-receipt.json');require(receipt_path.stat().st_size<=m.MAX_RECEIPT_BYTES and stat.S_IMODE(receipt_path.stat().st_mode)==0o600,'supervisor receipt private bound differs')
   receipt=json.loads(receipt_path.read_bytes())
   require(receipt['canonical_ensure_ascii'] is False and m.seal({k:v for k,v in receipt.items() if k!='identity_sha256'})==receipt,'supervisor original False seal differs')
   require(receipt['fixture'] is True and receipt['scientific_admission'] is False and receipt['child_scientific_result_assessed'] is False and receipt['supervision_success'] is False,'fixture/non-success/admission scope differs')
   require(receipt['action']=='exporter' and receipt['selected_source_sha256']==m.SOURCES['exporter'] and receipt['timeout_s']==18000,'exporter-mode shared function/cap differs')
   require(receipt['cleanup_implementation_sha256']==m.HELPER_SHA and receipt['processes_py_sha256']==m.PROCESSES_SHA and receipt['estimator_sha256']==m.F6 and receipt['estimator_modules']==185,'frozen source pins differ')
   require(receipt['supervisor_sha256']==args.supervisor_sha and receipt['native_python_sha256']==args.python_sha and receipt['uid']==UID,'supervisor/native/account pins differ')
   require(receipt['state']=='child_failed' and receipt['returned_child_exit']==receipt['child_exit']==receipt['supervisor_exit']==7,'early nonzero status was lost or masked')
   require(receipt['timed_out'] is False and receipt['signal_received'] is None and receipt['error_type'] is None,'unexpected timeout/signal/supervisor error')
   cleanup_path=checked(folder/'cleanup.json');cleanup_raw=cleanup_path.read_bytes();worker_cleanup=json.loads(cleanup_raw)
   require(receipt['cleanup']['original_private_cleanup']=={'bytes':len(cleanup_raw),'sha256':hashlib.sha256(cleanup_raw).hexdigest()},'original worker cleanup bytes differ')
   require(worker_cleanup['subreaper'] is True and worker_cleanup['survivors']=={} and receipt['cleanup']['subreaper'] is True and receipt['cleanup']['survivor_count']==0 and receipt['cleanup_errors']==[],'owned worker cleanup incomplete')
   after={name:process_key(before['pid']) for name,before in keys.items()};observed['owned_after']=after
   for name,before in keys.items():require(after[name] is None or after[name]['start_time']!=before['start_time'],'owned original PID/start survived or remained unreaped')
   sibling_after=process_key(sibling.pid);observed['sibling_after_worker_cleanup']=sibling_after
   require(sibling.poll() is None and sibling_after and sibling_after['start_time']==sibling_before['start_time'] and sibling_after['uid']==UID and sibling_after['ppid']==os.getpid() and sibling_after['state']!='Z','unrelated harness sibling did not survive worker cleanup')
   results.append({'case':'early_nonzero7','passed':True,'supervisor_receipt_sha256':sha(receipt_path),'supervisor_receipt_identity_sha256':receipt['identity_sha256'],'original_marker':marker_pin,'worker_exit':worker_exit,
    'owned_before':keys,'owned_after':after,'unrelated_sibling_before':sibling_before,'unrelated_sibling_after_worker_cleanup':sibling_after,'unrelated_sibling_survived_worker_cleanup':True})
   own_source(args.fixture_sha);m.immutable(ctx);passed=True
 except BaseException as exc:failure_type=type(exc).__name__
 finally:
  signal.alarm(0)
  for sig in prior:signal.signal(sig,signal.SIG_IGN)
  errors=[]
  # Cleanup only the exact fixture Popen groups, then this subreaper's original
  # UID/ancestry/start-checked descendants. The sibling is retired AFTER its
  # survival during the separate worker's cleanup has been recorded.
  for owned in (child,sibling):
   try:ctx.stop_group(owned,grace_seconds=15)
   except BaseException as exc:errors.append('stop_group:'+type(exc).__name__)
  if subreaper_enabled:
   try:cleanup=ctx.helper.cleanup_owned()
   except BaseException as exc:cleanup={'subreaper':True,'survivors':{'unknown':'cleanup failed'},'terminated_owned_processes':[]};errors.append('cleanup_owned:'+type(exc).__name__)
  try:own_source(args.fixture_sha);m.immutable(ctx)
  except BaseException as exc:errors.append('immutable_bytes:'+type(exc).__name__)
  if errors or cleanup.get('survivors') or not subreaper_enabled:passed=False
  cleanup_pin=m.private_json(root/'harness-cleanup.json',cleanup)
  receipt=m.seal({'format':'swdb.lanl14-early-nonzero-supervisor-linux-fixture.v1','updated':'2026-10-07 ET','canonical_ensure_ascii':False,'passed':passed,'started_utc':started,'ended_utc':m.now(),
   'cases':results,'cases_expected':1,'cases_passed':len(results),'fixture':True,'failure_type':failure_type,'observed_before_after':observed,'worker_exit':worker_exit,
   'supervisor_sha256':args.supervisor_sha,'fixture_script_sha256':args.fixture_sha,'selected_source_sha256':m.SOURCES['exporter'],'cleanup_helper_sha256':m.HELPER_SHA,'processes_py_sha256':m.PROCESSES_SHA,'estimator_sha256':m.F6,'estimator_modules':185,'native_python_sha256':args.python_sha,
   'host':socket.gethostname().split('.')[0],'uid':os.getuid(),'subreaper_enabled':subreaper_enabled,'cleanup':{'survivor_count':len(cleanup.get('survivors',{})),'subreaper':cleanup.get('subreaper'),'original_private_cleanup':cleanup_pin},'cleanup_errors':errors,
   'worker_wait_s':WORKER_WAIT_S,'harness_alarm_s':HARNESS_ALARM_S,'production_exporter_cap_s':18000,'scientific_admission':False,'reader_mode_runtime_proof':False,'selected_exporter_or_reader_main_invoked':False,
   'scope':'ONE synthetic early-exit7 process lifecycle case through exporter-mode shared supervise(fixture=True). No selected control main/Store/validate/compiler/evaluator/provider/Git/SSH; no scientific/export/reader admission.'})
  try:m.private_json(root/'receipt.json',receipt,maximum=m.MAX_RECEIPT_BYTES)
  finally:
   for sig,handler in prior.items():signal.signal(sig,handler)
 print(json.dumps({'passed':passed,'receipt_sha256':sha(root/'receipt.json'),'identity_sha256':receipt['identity_sha256'],'cases_passed':len(results),'worker_exit':worker_exit,'cleanup_survivor_count':receipt['cleanup']['survivor_count'],'scientific_admission':False}))
 return 0 if passed else 1

def main():
 require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact non-root Linux mbit10 fixture account required')
 p=PrivateParser(description=__doc__)
 for name in ('supervisor','supervisor-sha','helper','project','selected-source','python','python-sha','cwd'):p.add_argument('--'+name)
 p.add_argument('--fixture-sha',required=True);p.add_argument('--output',required=True)
 roles=p.add_mutually_exclusive_group();roles.add_argument('--worker',action='store_true');roles.add_argument('--owned-child',action='store_true')
 args=p.parse_args()
 if args.owned_child:return owned_child(args)
 require(all((args.supervisor,args.supervisor_sha,args.helper,args.project,args.selected_source,args.python,args.python_sha,args.cwd)),'explicit future source/native/cwd pins required')
 return worker(args) if args.worker else harness(args)

if __name__=='__main__':
 try:sys.exit(main())
 except FixtureFailure as exc:print('lifecycle fixture refused: '+str(exc),file=sys.stderr);sys.exit(2)
