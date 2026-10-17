"""Ticket 14 exporter/reader administrative lifecycle supervisor, 2026-10-07 ET.

Source-only derivative of fa703. Selected controls and their scientific limits
are unchanged. Explicit administrative allowances are finite and unproved.
Original stdout/stderr remain private on mbit10; only compact custody returns.
"""
import argparse,ctypes,datetime,hashlib,importlib.util,json,math,os,re,signal,socket,stat,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
HELPER_SHA='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
SOURCES={'exporter':'928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e',
 'reader':'6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570'}
CAPS={'exporter':18000,'reader':14400}
UID=114316761
SIGNALS=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP)
ACTIONS=set(SOURCES)
RAW_ROOTS=(Path('/data/yanruj/EvolveSWDB_runs'),Path('/data1/yanruj/EvolveSWDB_runs'))
MAX_RECEIPT_BYTES=16384

class Refusal(ValueError):pass
class PrivateParser(argparse.ArgumentParser):
 def error(self,message):raise Refusal('argument contract differs; original argv omitted')
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

def checked(path,*,directory=False,owned=True):
 path=Path(path)
 require(path.is_absolute() and '..' not in path.parts and len(str(path))<=4096,'explicit absolute nonsymlink path required')
 for part in (path,*path.parents):require(not part.is_symlink(),'symlink component refused')
 status=path.stat()
 require(stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode),'path type differs')
 require(not owned or status.st_uid==UID,'source/private path owner differs')
 return path

def code_file(path,expected,*,native=False):
 require(re.fullmatch('[a-f0-9]{64}',expected) is not None,'exact SHA-256 required')
 path=checked(path,owned=not native);status=path.stat()
 require(0<status.st_size<=(128*1024*1024 if native else 8*1024*1024),'source/native size outside administrative read bound')
 require(not status.st_mode&0o022 and (not native or status.st_uid in (0,UID)),'source/native writable by another account or unexpected owner')
 require(sha(path)==expected,'source/native bytes differ')
 if native:
  with path.open('rb') as stream:header=stream.read(20)
  require(os.access(path,os.X_OK) and len(header)==20 and header[:6]==b'\x7fELF\x02\x01' and int.from_bytes(header[18:20],'little')==62,'pinned executable must be Linux x86_64 ELF')
 return path

def immutable(context):
 code_file(context.helper_path,HELPER_SHA)
 code_file(context.selected_path,SOURCES[context.action])
 code_file(context.processes_path,PROCESSES_SHA)
 code_file(context.supervisor_path,context.supervisor_sha)
 code_file(context.python,context.python_sha,native=True)
 checked(context.project,directory=True);checked(context.cwd,directory=True)
 modules=list((context.project/'swdb').rglob('*.py'))
 require(len(modules)==185,'frozen module count differs')
 for path in modules:
  path=checked(path);require(path.stat().st_size<=8*1024*1024,'frozen source module exceeds administrative read bound')
 require(bundle_identity(context.project)==(185,F6),'frozen C/F6 bundle differs')

def load_context(helper,project,selected,action,python,python_sha,cwd,supervisor_sha):
 require(action in ACTIONS,'only selected exporter/reader admitted')
 require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact non-root mbit10 account required')
 helper=code_file(helper,HELPER_SHA);project=checked(project,directory=True)
 selected=code_file(selected,SOURCES[action]);processes=code_file(project/'swdb/processes.py',PROCESSES_SHA)
 python=code_file(python,python_sha,native=True);cwd=checked(cwd,directory=True)
 require(Path(sys.executable).resolve(strict=True)==python,'supervisor must use the supplied pinned native Python')
 supervisor=code_file(Path(__file__).absolute(),supervisor_sha)
 h=load_module('lanl14_pinned_lifecycle_cleanup',helper)
 p=load_module('lanl14_pinned_processes',processes)
 require(Path(h.cleanup_owned.__code__.co_filename).absolute()==helper,'cleanup implementation differs')
 require(Path(p.stop_group.__code__.co_filename).absolute()==processes,'stop_group implementation differs')
 context=SimpleNamespace(helper=h,helper_path=helper,helper_sha=HELPER_SHA,project=project,processes_path=processes,processes_sha=PROCESSES_SHA,stop_group=p.stop_group,
  selected_path=selected,action=action,python=python,python_sha=python_sha,cwd=cwd,supervisor_path=supervisor,supervisor_sha=supervisor_sha)
 immutable(context)
 return context

def enable_subreaper():
 require(sys.platform=='linux' and os.getuid()!=0,'Linux non-root isolated supervisor required')
 require(ctypes.CDLL(None).prctl(36,1,0,0,0)==0,'Linux child subreaper enable failed')

def private_control_directory(path,context):
 path=Path(path)
 require(path.is_absolute() and '..' not in path.parts and re.fullmatch('lanl14-export-reader-control-[a-z0-9-]{1,80}',path.name) is not None,'explicit fresh administrative control directory required')
 require(any(path.is_relative_to(root) and path!=root for root in RAW_ROOTS),'administrative output must remain under a declared remote raw root')
 require(not path.exists() and not path.is_symlink(),'administrative control directory already exists')
 parent=checked(path.parent,directory=True)
 require(stat.S_IMODE(parent.stat().st_mode)==0o700,'administrative output parent must already be private 0700')
 forbidden=(context.project,context.cwd)
 require(all(not path.is_relative_to(root) and not root.is_relative_to(path) for root in forbidden),'administrative output overlaps a source directory')
 require(all(not code.is_relative_to(path) for code in (context.selected_path,context.helper_path,context.supervisor_path,context.python)),'administrative output contains a code path')
 path.mkdir(mode=0o700)
 require(stat.S_IMODE(checked(path,directory=True).stat().st_mode)==0o700,'administrative directory privacy differs')
 return path

def private_stream(path):
 descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 stream=os.fdopen(descriptor,'wb')
 status=os.fstat(stream.fileno())
 require(status.st_uid==UID and stat.S_IMODE(status.st_mode)==0o600 and stat.S_ISREG(status.st_mode),'private original stream differs')
 return stream

def private_json(path,data,*,maximum=None):
 raw=(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 require(maximum is None or len(raw)<=maximum,'compact receipt bound exceeded')
 with private_stream(path) as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def supervise(context,action,argv,*,timeout_s,receipt,stdout,stderr,fixture=False):
 require(action in ACTIONS,'only selected exporter/reader metadata actions are admitted')
 require(type(timeout_s) in (int,float) and math.isfinite(timeout_s) and timeout_s==CAPS[action],'exact explicit finite selected administrative cap required')
 argv=list(map(str,argv));require(bool(argv) and len(argv)<=256 and sum(len(v.encode()) for v in argv)<=65536,'bounded child argument vector required')
 require(type(fixture) is bool,'internal fixture flag must be explicit boolean')
 if not fixture:
  require(argv[:3]==[str(context.python),'-B',str(context.selected_path)],'metadata child must be exact pinned native Python and selected control')
 immutable(context)
 paths=[Path(p).absolute() for p in (receipt,stdout,stderr)]
 require(len(set(paths))==3 and len({p.parent for p in paths})==1 and all(not p.exists() and not p.is_symlink() for p in paths),'fresh distinct private receipt/log paths required')
 root=checked(paths[0].parent,directory=True)
 require(stat.S_IMODE(root.stat().st_mode)==0o700,'control directory must be private')
 previous={sig:signal.getsignal(sig) for sig in SIGNALS}
 received=None;child=None;child_exit=None;returned_child_exit=None;timed_out=False;subreaper_enabled=False;state='supervisor_error';error_type=None;cleanup_errors=[]
 cleanup={'subreaper':False,'terminated_owned_processes':[],'survivors':{},'scope':'No child launched.'}
 started=now();start=time.monotonic()
 def interrupt(number,frame):raise Interruption(number)
 for sig in SIGNALS:signal.signal(sig,interrupt)
 try:
  enable_subreaper()  # Before child launch; escaped orphans remain owned by this PID.
  subreaper_enabled=True
  with private_stream(paths[1]) as out,private_stream(paths[2]) as err:
   child=subprocess.Popen(argv,stdout=out,stderr=err,cwd=context.cwd,start_new_session=True)
   try:
    child_exit=child.wait(timeout=timeout_s);returned_child_exit=child_exit;state='child_returned' if child_exit==0 else 'child_failed'
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
    try:cleanup=context.helper.cleanup_owned()  # Original 31e UID/ancestry/start-time checks.
    except BaseException as exc:cleanup_errors.append('cleanup_owned:'+type(exc).__name__)
   if child is not None and child.returncode is not None:child_exit=child.returncode
   if cleanup_errors or cleanup.get('survivors') or (subreaper_enabled and cleanup.get('subreaper') is not True):state='cleanup_failed'
   try:immutable(context)
   except BaseException as exc:cleanup_errors.append('immutable_bytes:'+type(exc).__name__);state='cleanup_failed'
   code=0 if state=='child_returned' and child_exit==0 else 124 if state=='timeout' else 128+getattr(signal,received) if state=='signal' else child_exit if type(child_exit) is int and 0<child_exit<=255 else 128-child_exit if type(child_exit) is int and -127<=child_exit<0 else 1
   cleanup_pin=private_json(root/'cleanup.json',cleanup)
   streams={name:({'bytes':checked(path).stat().st_size,'mode':stat.S_IMODE(path.stat().st_mode)} if path.exists() else {'created':False}) for name,path in (('stdout',paths[1]),('stderr',paths[2]))}
   data=seal({'format':'swdb.lanl14-export-reader-administrative-supervisor.v1','updated':'2026-10-07 ET','action':action,'started_utc':started,'ended_utc':now(),'elapsed_control_s':time.monotonic()-start,
    'timeout_s':timeout_s,'timed_out':timed_out,'signal_received':received,'state':state,'returned_child_exit':returned_child_exit,'child_exit':child_exit,'supervisor_exit':code,'argv_sha256':digest(argv),
    'selected_source_sha256':SOURCES[action],'cleanup_implementation_sha256':HELPER_SHA,'processes_py_sha256':PROCESSES_SHA,'estimator_sha256':F6,'estimator_modules':185,'supervisor_sha256':context.supervisor_sha,'native_python_sha256':context.python_sha,'uid':os.getuid(),
    'cleanup':{'subreaper':cleanup.get('subreaper'),'survivor_count':len(cleanup.get('survivors',{})),'terminated_owned_process_count':len(cleanup.get('terminated_owned_processes',[])),'original_private_cleanup':cleanup_pin},
    'cleanup_errors':cleanup_errors,'error_type':error_type,'original_private_streams':streams,'fixture':fixture,'supervision_success':state=='child_returned' and child_exit==0,'scientific_admission':False,'child_scientific_result_assessed':False,
    'canonical_ensure_ascii':False,'scope':'Selected metadata child status and original owned cleanup custody only. Scientific admission remains separate. Full argv/environment/auth and original private stdout/stderr omitted; no retry.'})
   private_json(paths[0],data,maximum=MAX_RECEIPT_BYTES)
  finally:
   for sig,handler in previous.items():signal.signal(sig,handler)
 return code,data

def main():
 p=PrivateParser(description=__doc__)
 p.add_argument('--cleanup-helper',required=True,type=Path);p.add_argument('--project',required=True,type=Path)
 p.add_argument('--selected-source',required=True,type=Path);p.add_argument('--action',required=True,choices=sorted(ACTIONS));p.add_argument('--timeout-s',required=True,type=float)
 p.add_argument('--python',required=True,type=Path);p.add_argument('--python-sha256',required=True);p.add_argument('--supervisor-sha256',required=True)
 p.add_argument('--cwd',required=True,type=Path);p.add_argument('--control-directory',required=True,type=Path)
 p.add_argument('arguments',nargs=argparse.REMAINDER)
 args=p.parse_args();tail=args.arguments
 if tail and tail[0]=='--':tail=tail[1:]
 context=load_context(args.cleanup_helper,args.project,args.selected_source,args.action,args.python,args.python_sha256,args.cwd,args.supervisor_sha256)
 root=private_control_directory(args.control_directory,context)
 code,receipt=supervise(context,args.action,[str(context.python),'-B',str(context.selected_path),*tail],timeout_s=args.timeout_s,receipt=root/'receipt.json',stdout=root/'stdout',stderr=root/'stderr')
 print(json.dumps({'receipt_sha256':sha(root/'receipt.json'),'identity_sha256':receipt['identity_sha256'],'action':receipt['action'],'state':receipt['state'],'supervisor_exit':code,'cleanup_survivor_count':receipt['cleanup']['survivor_count'],'scientific_admission':False}))
 return code

if __name__=='__main__':
 try:sys.exit(main())
 except Refusal as exc:print('administrative supervisor refused: '+str(exc),file=sys.stderr);sys.exit(2)
