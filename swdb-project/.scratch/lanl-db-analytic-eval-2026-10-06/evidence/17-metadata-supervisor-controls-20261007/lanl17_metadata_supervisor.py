"""Separate parent metadata supervisor; no campaign/provider/scientific action.

Prepare/finalize and their nested exports only. Administrative timeout is explicit
and unproved. Reviewed helper and C/F6/process cleanup bytes remain unchanged.
"""
import argparse,ctypes,datetime,hashlib,importlib.util,json,math,os,signal,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
HELPER_SHA='09136ee553984b2c0cf929a6746f037aa4e1874f863aa2e83e0e0842a8b65ed9'
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
SIGNALS=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP)
ACTIONS={'prepare','finalize'}

class Refusal(ValueError):pass
class Interruption(BaseException):
 def __init__(self,number):self.number=number

def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def seal(data):return {**data,'identity_sha256':digest(data)}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def bundle_identity(project):
 modules={p.relative_to(Path(project)/'swdb').as_posix():sha(p) for p in sorted((Path(project)/'swdb').rglob('*.py'))}
 return len(modules),digest(modules)
def require(condition,reason):
 if not condition:raise Refusal(reason)

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module;spec.loader.exec_module(module);return module

def load_context(helper,project):
 helper=Path(helper).absolute();project=Path(project).absolute();processes=project/'swdb/processes.py'
 require(helper.is_file() and not helper.is_symlink() and sha(helper)==HELPER_SHA,'selected helper hash differs')
 require(processes.is_file() and not processes.is_symlink() and sha(processes)==PROCESSES_SHA,'frozen process cleanup hash differs')
 require(bundle_identity(project)==(185,F6),'frozen C/F6 bundle differs')
 h=load_module('lanl17_pinned_metadata_helper',helper)
 p=load_module('lanl17_pinned_processes',processes)
 require(Path(h.cleanup_owned.__code__.co_filename).absolute()==helper,'cleanup implementation differs')
 require(Path(p.stop_group.__code__.co_filename).absolute()==processes,'stop_group implementation differs')
 return SimpleNamespace(helper=h,helper_path=helper,helper_sha=HELPER_SHA,project=project,processes_path=processes,processes_sha=PROCESSES_SHA,stop_group=p.stop_group,supervisor_sha=sha(__file__))

def enable_subreaper():
 require(sys.platform=='linux' and os.getuid()!=0,'Linux non-root isolated supervisor required')
 require(ctypes.CDLL(None).prctl(36,1,0,0,0)==0,'Linux child subreaper enable failed')

def supervise(context,action,argv,*,timeout_s,receipt,stdout,stderr,fixture=False):
 require(action in ACTIONS,'only prepare/finalize metadata actions are admitted')
 require(type(timeout_s) in (int,float) and math.isfinite(timeout_s) and 0<timeout_s,'explicit finite positive metadata cap required')
 argv=list(map(str,argv));require(bool(argv),'child argument vector is empty')
 if not fixture:
  require(argv[:3]==[sys.executable,str(context.helper_path),action],'metadata child must be exact pinned helper/action')
 require(sha(context.helper_path)==HELPER_SHA and sha(context.processes_path)==PROCESSES_SHA and bundle_identity(context.project)==(185,F6),'cleanup/helper/frozen bundle bytes changed before launch')
 paths=[Path(p).absolute() for p in (receipt,stdout,stderr)]
 require(len(set(paths))==3 and all(not p.exists() and not p.is_symlink() for p in paths),'fresh distinct receipt/log paths required')
 for p in paths:p.parent.mkdir(parents=True,exist_ok=True)
 previous={sig:signal.getsignal(sig) for sig in SIGNALS}
 received=None;child=None;child_exit=None;timed_out=False;subreaper_enabled=False;state='supervisor_error';error_type=None;cleanup_errors=[]
 cleanup={'subreaper':False,'terminated_owned_processes':[],'survivors':{},'scope':'No child launched.'}
 started=now();start=time.monotonic()
 def interrupt(number,frame):raise Interruption(number)
 for sig in SIGNALS:signal.signal(sig,interrupt)
 try:
  enable_subreaper()  # Before child launch; escaped orphans remain owned by this PID.
  subreaper_enabled=True
  with paths[1].open('x') as out,paths[2].open('x') as err:
   child=subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True)
   try:
    child_exit=child.wait(timeout=timeout_s);state='child_returned' if child_exit==0 else 'child_failed'
   except subprocess.TimeoutExpired:
    timed_out=True;state='timeout'
 except Interruption as exc:
  received=signal.Signals(exc.number).name;state='signal'
 except BaseException as exc:
  error_type=type(exc).__name__;state='supervisor_error'
 finally:
  for sig in SIGNALS:signal.signal(sig,signal.SIG_IGN)
  try:
   if subreaper_enabled:
    try:context.stop_group(child,grace_seconds=15)
    except BaseException as exc:cleanup_errors.append('stop_group:'+type(exc).__name__)
    try:cleanup=context.helper.cleanup_owned()  # Pinned UID/ancestry/start-time checks.
    except BaseException as exc:cleanup_errors.append('cleanup_owned:'+type(exc).__name__)
   if child is not None and child.returncode is not None:child_exit=child.returncode
   if cleanup_errors or cleanup.get('survivors') or (subreaper_enabled and cleanup.get('subreaper') is not True):state='cleanup_failed'
   if sha(context.helper_path)!=HELPER_SHA or sha(context.processes_path)!=PROCESSES_SHA or bundle_identity(context.project)!=(185,F6):
    cleanup_errors.append('immutable_bytes_changed');state='cleanup_failed'
   code=0 if state=='child_returned' and child_exit==0 else 124 if state=='timeout' else 128+getattr(signal,received) if state=='signal' else 1
   data=seal({'format':'swdb.lanl17-metadata-supervisor.v1','action':action,'started_utc':started,'ended_utc':now(),'elapsed_control_s':time.monotonic()-start,'timeout_s':timeout_s,'timed_out':timed_out,'signal_received':received,'state':state,'child_exit':child_exit,'supervisor_exit':code,'argv_sha256':digest(argv),'helper_sha256':HELPER_SHA,'cleanup_implementation_sha256':HELPER_SHA,'processes_py_sha256':PROCESSES_SHA,'estimator_sha256':F6,'supervisor_sha256':context.supervisor_sha,'uid':os.getuid(),'cleanup':cleanup,'cleanup_errors':cleanup_errors,'error_type':error_type,'fixture':bool(fixture),'application_outcomes':0,'provider_calls':0,'scope':'Metadata child exit/owned cleanup only; no model/population/campaign/unique-pair/accuracy admission. Full argv/environment/auth omitted.'})
   paths[0].write_text(json.dumps(data,indent=2)+'\n')
  finally:
   for sig,handler in previous.items():signal.signal(sig,handler)
 return code,data

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--helper',required=True,type=Path);p.add_argument('--project',required=True,type=Path)
 p.add_argument('--action',required=True,choices=sorted(ACTIONS));p.add_argument('--timeout-s',required=True,type=float)
 p.add_argument('--receipt',required=True,type=Path);p.add_argument('--stdout',required=True,type=Path);p.add_argument('--stderr',required=True,type=Path)
 p.add_argument('arguments',nargs=argparse.REMAINDER)
 args=p.parse_args();tail=args.arguments
 if tail and tail[0]=='--':tail=tail[1:]
 context=load_context(args.helper,args.project)
 code,receipt=supervise(context,args.action,[sys.executable,str(context.helper_path),args.action,*tail],timeout_s=args.timeout_s,receipt=args.receipt,stdout=args.stdout,stderr=args.stderr)
 print(json.dumps({'receipt_sha256':sha(args.receipt),'identity_sha256':receipt['identity_sha256'],'action':receipt['action'],'state':receipt['state'],'supervisor_exit':code,'survivors':receipt['cleanup']['survivors']}))
 return code

if __name__=='__main__':
 try:sys.exit(main())
 except Refusal as exc:print('metadata supervisor refused: '+str(exc),file=sys.stderr);sys.exit(2)
