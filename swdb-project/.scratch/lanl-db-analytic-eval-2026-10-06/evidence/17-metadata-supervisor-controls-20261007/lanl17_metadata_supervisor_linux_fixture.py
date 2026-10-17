"""Unexecuted Linux fixture for the separate metadata supervisor.

Owned process fixtures only, never prepare/finalize/campaign/provider execution.
Parent reviews before running on a free lane. Fixture receipts cannot admit any
population, model, performance or D30 result. Exact selected controls stay pinned.
"""
import argparse,hashlib,importlib.util,json,os,signal,socket,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True

class FixtureFailure(RuntimeError):pass
class FixtureDeadline(BaseException):pass

def require(condition,reason):
 if not condition:raise FixtureFailure(reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_supervisor(path,expected):
 require(sha(path)==expected,'supervisor source differs')
 spec=importlib.util.spec_from_file_location('lanl17_metadata_supervisor_fixture_module',path)
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 return module

def process_key(pid):
 try:
  folder=Path('/proc')/str(pid);fields=(folder/'stat').read_text().rsplit(')',1)[1].split()
  return {'pid':pid,'uid':folder.stat().st_uid,'start_time':fields[19],'state':fields[0],'session':int(fields[3])}
 except (FileNotFoundError,ProcessLookupError):return None

def wait_marker(path,cap=8):
 deadline=time.monotonic()+cap
 while not path.exists() and time.monotonic()<deadline:time.sleep(.02)
 require(path.exists(),'owned process marker missing')
 return json.loads(path.read_text())

def owned_child(args):
 # This fixture is launched by supervisor Popen(new session). The first child
 # stays in that group; its child creates an escaped session and ignores TERM.
 root=Path(args.output);leader=process_key(os.getpid())
 first=os.fork()
 if first==0:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  second=os.fork()
  if second==0:
   os.setsid()
   payload={'leader':leader,'same_group':process_key(os.getppid()),'escaped_session':process_key(os.getpid())}
   temporary=root/('owned-children.'+str(os.getpid())+'.tmp')
   with temporary.open('x') as marker:marker.write(json.dumps(payload)+'\n')
   os.replace(temporary,root/'owned-children.json')  # Same-folder atomic publication.
  while True:time.sleep(1)
 wait_marker(root/'owned-children.json')
 if args.case=='returned':os._exit(0)
 # For timeout/TERM cases the leader uses default TERM, while both descendants
 # ignore it. This checks group cleanup and the separately adopted orphan.
 while True:time.sleep(1)

def worker(args):
 m=load_supervisor(args.supervisor,args.supervisor_sha);ctx=m.load_context(args.helper,args.project)
 root=Path(args.output)
 command=[sys.executable,str(Path(__file__).absolute()),'--owned-child','--case',args.case,'--output',str(root)]
 code,receipt=m.supervise(ctx,'prepare' if args.case!='term' else 'finalize',command,
  timeout_s=5 if args.case=='timeout' else 30,receipt=root/'supervisor-receipt.json',
  stdout=root/'fixture-child.stdout',stderr=root/'fixture-child.stderr',fixture=True)
 return code

def harness(args):
 require(sys.platform=='linux' and os.getuid()!=0,'Linux non-root fixture only')
 root=Path(args.output).absolute()
 require(str(root).startswith('/data/yanruj/EvolveSWDB_runs/') and not root.exists() and not root.is_symlink(),'fresh scoped raw fixture output required')
 m=load_supervisor(args.supervisor,args.supervisor_sha);ctx=m.load_context(args.helper,args.project)
 root.mkdir(parents=True);m.enable_subreaper()
 prior={sig:signal.getsignal(sig) for sig in (*m.SIGNALS,signal.SIGALRM)}
 def interrupted(number,frame):raise FixtureDeadline(number)
 for sig in prior:signal.signal(sig,interrupted)
 signal.alarm(120)  # Administrative fixture bound; scientific budgets unchanged.
 sibling=None;child=None;results=[];started=m.now();passed=False;failure_type=None
 try:
  sibling=subprocess.Popen([sys.executable,'-c','import time; time.sleep(180)'],start_new_session=True)
  sibling_before=process_key(sibling.pid)
  for case,expected_code in [('returned',0),('timeout',124),('term',143)]:
   folder=root/case;folder.mkdir()
   command=[sys.executable,str(Path(__file__).absolute()),'--worker','--case',case,
    '--supervisor',str(Path(args.supervisor).absolute()),'--supervisor-sha',args.supervisor_sha,
    '--helper',str(Path(args.helper).absolute()),'--project',str(Path(args.project).absolute()),'--output',str(folder)]
   with (folder/'worker.stdout').open('x') as out,(folder/'worker.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    keys=wait_marker(folder/'owned-children.json')
    require(keys['escaped_session']['session']==keys['escaped_session']['pid'],'fixture did not escape session')
    require(keys['same_group']['session']==keys['leader']['session'],'fixture same-group identity differs')
    require(all(row['uid']==os.getuid() for row in keys.values()),'fixture UID differs')
    if case=='term':
     # Marker was written only after supervisor launched the owned child and
     # installed its signal handlers; TERM targets the supervisor, not child.
     os.kill(child.pid,signal.SIGTERM)
    child_exit=child.wait(timeout=55)
   require(child_exit==expected_code,'supervisor exit differs')
   receipt=json.loads((folder/'supervisor-receipt.json').read_text())
   require(m.seal({k:v for k,v in receipt.items() if k!='identity_sha256'})==receipt,'supervisor receipt seal differs')
   require(receipt['fixture'] is True and receipt['provider_calls']==0 and receipt['application_outcomes']==0,'fixture scope differs')
   require(receipt['helper_sha256']==m.HELPER_SHA and receipt['processes_py_sha256']==m.PROCESSES_SHA and receipt['estimator_sha256']==m.F6,'source pins differ')
   require(receipt['supervisor_sha256']==args.supervisor_sha and receipt['supervisor_exit']==expected_code,'supervisor source/exit pin differs')
   require(receipt['cleanup']['subreaper'] is True and receipt['cleanup']['survivors']=={} and receipt['cleanup_errors']==[],'owned cleanup incomplete')
   require(receipt['state']=={'returned':'child_returned','timeout':'timeout','term':'signal'}[case],'state differs')
   require(receipt['timed_out']==(case=='timeout') and receipt['signal_received']==('SIGTERM' if case=='term' else None),'interruption facts differ')
   for name,before in keys.items():
    after=process_key(before['pid'])
    require(after is None or after['start_time']!=before['start_time'],'owned process survived or remained unreaped')
   sibling_after=process_key(sibling.pid)
   require(sibling.poll() is None and sibling_after and sibling_after['start_time']==sibling_before['start_time'],'unrelated sibling killed')
   results.append({'case':case,'passed':True,'supervisor_receipt_sha256':sha(folder/'supervisor-receipt.json'),
    'supervisor_receipt_identity_sha256':receipt['identity_sha256'],'supervisor_exit':child_exit,
    'owned_before':keys,'owned_after':'terminated_and_reaped','unrelated_sibling_survived':True})
   ctx.stop_group(child,grace_seconds=1);child=None
  require(sha(args.supervisor)==args.supervisor_sha and sha(args.helper)==m.HELPER_SHA and sha(ctx.processes_path)==m.PROCESSES_SHA,'immutable controls changed')
  passed=True
 except BaseException as exc:failure_type=type(exc).__name__
 finally:
  signal.alarm(0)
  for sig in prior:signal.signal(sig,signal.SIG_IGN)
  # Cleanup only exact fixture Popen groups, then this isolated harness's UID/
  # start-time checked descendants adopted after an exceptional worker stop.
  errors=[]
  for owned in (child,sibling):
   try:ctx.stop_group(owned,grace_seconds=1)
   except BaseException as exc:errors.append('stop_group:'+type(exc).__name__)
  try:cleanup=ctx.helper.cleanup_owned()
  except BaseException as exc:cleanup={'survivors':{'unknown':'cleanup failed'}};errors.append('cleanup_owned:'+type(exc).__name__)
  if errors or cleanup.get('survivors'):passed=False
  receipt=m.seal({'format':'swdb.lanl17-metadata-supervisor-linux-fixture.v1','passed':passed,
   'started_utc':started,'ended_utc':m.now(),'cases':results,'fixture':True,'failure_type':failure_type,
   'helper_sha256':m.HELPER_SHA,'supervisor_sha256':args.supervisor_sha,'fixture_script_sha256':sha(__file__),
   'processes_py_sha256':m.PROCESSES_SHA,'estimator_sha256':m.F6,'cleanup':cleanup,'cleanup_errors':errors,
   'host':socket.gethostname().split('.')[0],'uid':os.getuid(),'provider_calls':0,'application_outcomes':0,
   'scope':'Actual owned fixture process cleanup only. No prepare/finalize metadata action, model/population/campaign/performance/D30 admission.'})
  (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
  for sig,handler in prior.items():signal.signal(sig,handler)
 print(json.dumps({'passed':passed,'receipt_sha256':sha(root/'receipt.json'),'identity_sha256':receipt['identity_sha256'],'cases_passed':len(results),'survivors':cleanup['survivors']}))
 return 0 if passed else 1

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--supervisor');p.add_argument('--supervisor-sha');p.add_argument('--helper');p.add_argument('--project')
 p.add_argument('--output',required=True);p.add_argument('--case',choices=('returned','timeout','term'))
 p.add_argument('--worker',action='store_true');p.add_argument('--owned-child',action='store_true')
 args=p.parse_args()
 if args.owned_child:sys.exit(owned_child(args))
 require(all((args.supervisor,args.supervisor_sha,args.helper,args.project)),'explicit source paths/pin required')
 sys.exit(worker(args) if args.worker else harness(args))
