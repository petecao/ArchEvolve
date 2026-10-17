"""2026-10-16 ET. Git-only source synchronization after user-requested pause."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
P=Path;expected=sys.argv[1];assert len(expected)==40 and all(c in '0123456789abcdef'for c in expected)
repo='/Users/yanrujhou/CLionProjects/ArchEvolve'
def localgit(*a):return subprocess.check_output(['/usr/bin/git','-C',repo,*a],text=True,timeout=60).strip()
assert localgit('branch','--show-current')=='yanrujhou_main'and localgit('rev-parse','HEAD')==expected
published=localgit('ls-remote','--heads','origin','refs/heads/yanrujhou_main');assert published.split()[0]==expected
remote='expected='+repr(expected)+'\n'+r'''
from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,time
import psutil
P=Path;repo=P('/data1/yanruj/ArchEvolve')
def git(*a):return subprocess.check_output(['/usr/bin/git','-c','core.hooksPath=/dev/null','-c','submodule.recurse=false','-C',str(repo),*a],text=True,timeout=120).strip()
def source_state(root):
 return {k:subprocess.check_output(['/usr/bin/git','-C',str(root),*a],text=True,timeout=30).strip()for k,a in [('commit',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain','--untracked-files=all'])]}
protected={str(p):source_state(p)for p in sorted(P('/data1/yanruj').glob('probata-reviewed-*'))if(p/'.git').exists()}
leases={p.name:json.loads(p.read_bytes())for p in P('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')};assert len(leases)==3 and all(v['state']=='released'for v in leases.values())
locks={}
for n in ['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1']:
 p=P('/data1/yanruj/lact-host-lease')/(n+'.lease');assert p.is_file()
 with p.open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[n]=True;fcntl.flock(f,fcntl.LOCK_UN)
tools={'frama-c','frama-c.exe','why3','why3server','alt-ergo','z3','cvc5','cbmc','clang++','clang-18','clang-22','ocamlopt','ocamlopt.opt'}
scans=[]
for _ in range(3):
 active=[];denied=[]
 for proc in psutil.process_iter(['pid','name','uids']):
  try:
   if proc.info['uids'].real!=os.getuid():continue
   if proc.info['name']in tools:active.append({'pid':proc.pid,'name':proc.info['name'],'birth':proc.create_time()})
  except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
  except psutil.AccessDenied:denied.append(proc.pid)
 scans.append({'active':active,'denied':denied});time.sleep(.05)
assert all(not s['active']and not s['denied']for s in scans)
before=source_state(repo);assert before['branch']=='yanrujhou_main'and not git('diff','--name-only')and not git('diff','--cached','--name-only')
untracked=git('ls-files','--others','--exclude-standard').splitlines();assert untracked==['swdb-project/records/.retention.lock'],untracked
untracked_before={n:{'sha256':hashlib.sha256((repo/n).read_bytes()).hexdigest(),'bytes':(repo/n).stat().st_size,'mode':(repo/n).stat().st_mode}for n in untracked}
pre={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary':before,'protected':protected,'untracked':untracked_before,'leases':leases,'kernel_locks':locks,'finite_process_scans':scans,'free_bytes':{r:shutil.disk_usage(r).free for r in ['/data1','/data']},'uptime':subprocess.check_output(['uptime'],text=True,timeout=10).strip()}
assert pre['free_bytes']['/data1']>20*1024**3 and pre['free_bytes']['/data']>20*1024**3
fetch=git('fetch','--no-tags','--recurse-submodules=no','origin','yanrujhou_main');assert git('rev-parse','FETCH_HEAD')==expected
git('merge-base','--is-ancestor','HEAD',expected)
merge=git('merge','--no-stat','--ff-only',expected)
after=source_state(repo);assert after['branch']=='yanrujhou_main'and after['commit']==expected and after['status']==before['status']
untracked_after={n:{'sha256':hashlib.sha256((repo/n).read_bytes()).hexdigest(),'bytes':(repo/n).stat().st_size,'mode':(repo/n).stat().st_mode}for n in untracked};assert untracked_after==untracked_before
protected_after={str(p):source_state(p)for p in sorted(P('/data1/yanruj').glob('probata-reviewed-*'))if(p/'.git').exists()};assert protected_after==protected
print(json.dumps({'date_ET':'2026-10-16','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_main':expected,'preflight':pre,'after':after,'untracked_preserved':untracked_after,'protected_sources_unchanged':True,'protected_after':protected_after,'fetch_stdout':fetch,'merge_stdout':merge,'source_only_sync':True,'compiler_tests_native_formal_evaluation_executed':False,'raw_evidence_modified':False,'scope':'Git-only fast-forward of idle clean-tracked primary source; every existing frozen reviewed checkout and raw remains intact'},indent=2))
'''
target=P('/private/tmp/probata-root-paused-main-mbit10-sync-20261016.json');assert not target.exists()
r=subprocess.run(['ssh','mbit10','/data1/yanruj/venvs/swdb-test/bin/python','-B','-'],input=remote,text=True,capture_output=True,timeout=180)
P(str(target)+'.stderr').write_text(r.stderr)
try:result=json.loads(r.stdout)
except Exception:result={'unparsed_stdout':r.stdout,'ssh_exit':r.returncode,'stderr':r.stderr}
result.update(local_main=expected,published_main=published.split()[0],root_entry={'path':__file__,'sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest()},ssh_exit=r.returncode)
target.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'receipt':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'exit':r.returncode,'after':result.get('after'),'protected_sources_unchanged':result.get('protected_sources_unchanged'),'unparsed':result.get('unparsed_stdout'),'stderr':r.stderr},indent=2));raise SystemExit(r.returncode)
