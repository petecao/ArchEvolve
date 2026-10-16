"""2026-10-16 ET. Read-only final local/remote finite idle checks for user pause."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time
import psutil
P=Path
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(P(p).read_bytes()).hexdigest(),'bytes':P(p).stat().st_size}
tools={'frama-c','frama-c.exe','why3','why3server','alt-ergo','z3','cvc5','cbmc','clang++','clang-22','ocamlopt','ocamlopt.opt'}
own={os.getpid(),*[p.pid for p in psutil.Process().parents()]}
def scan():
 active=[];denied=[];count=0
 for proc in psutil.process_iter(['pid','name','uids']):
  try:
   if proc.info['uids'].real!=os.getuid()or proc.pid in own:continue
   count+=1
   name=proc.info['name']
   if name in tools:active.append({'pid':proc.pid,'name':name,'birth':proc.create_time()})
   elif name.startswith('python'):
    argv=proc.cmdline()
    if any('probata-mac-compiler-worker-b.py'in a or 'counted_verifier.py'in a or 'probata-t28-initialized-u32-public-control-entry'in a for a in argv):active.append({'pid':proc.pid,'name':name,'birth':proc.create_time(),'argv':argv})
  except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
  except psutil.AccessDenied:denied.append(proc.pid)
 return {'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_active':active,'inspection_denials':denied,'same_uid_count':count}
scans=[]
for _ in range(3):scans.append(scan());time.sleep(.05)
leases=[P('/tmp/claude/swdb-verifier.lock'),P('/tmp/claude/swdb-verifier.slot2.lock'),P('/tmp/claude/swdb-native-b.lock')]
with P('/private/tmp/probata-mac-compiler-worker-b.lock').open('a')as f:
 try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);free_B=True;fcntl.flock(f,fcntl.LOCK_UN)
 except BlockingIOError:free_B=False
local={'finite_scans':scans,'lease_paths_present':[str(p)for p in leases if p.exists()],'B_flock_available':free_B,'free_bytes':shutil.disk_usage('/private/tmp').free,'memory_available':psutil.virtual_memory().available,'scope':'finite metadata/selected-name and owned runner scans, not universal process absence'}
remote=r'''
from pathlib import Path
import datetime,fcntl,json,os,shutil,subprocess,time
import psutil
P=Path
root=P('/data1/yanruj/lact-host-lease');metas={p.name:json.loads(p.read_bytes())for p in sorted(root.glob('mbit10-evaluation*.meta.json'))}
expected=['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'];locks={}
for name in expected:
 p=root/(name+'.lease')
 if not p.is_file():locks[name]={'exists':False};continue
 with p.open('rb')as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);free=True;fcntl.flock(f,fcntl.LOCK_UN)
  except BlockingIOError:free=False
 locks[name]={'exists':True,'kernel_flock_available':free}
tools={'frama-c','frama-c.exe','why3','why3server','alt-ergo','z3','cvc5','cbmc','clang++','clang-18','clang-22','ocamlopt','ocamlopt.opt'}
scans=[]
for _ in range(3):
 active=[];denied=[];count=0
 for proc in psutil.process_iter(['pid','name','uids']):
  try:
   if proc.info['uids'].real!=os.getuid():continue
   count+=1
   if proc.info['name']in tools:active.append({'pid':proc.pid,'name':proc.info['name'],'birth':proc.create_time()})
  except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
  except psutil.AccessDenied:denied.append(proc.pid)
 scans.append({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_active':active,'inspection_denials':denied,'same_uid_count':count});time.sleep(.05)
repo='/data1/yanruj/ArchEvolve'
def git(*a):return subprocess.check_output(['/usr/bin/git','-C',repo,*a],text=True,timeout=30).strip()
print(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata':metas,'kernel_lease_checks':locks,'finite_scans':scans,'free_bytes':{r:shutil.disk_usage(r).free for r in ['/data1','/data']},'available_ram':psutil.virtual_memory().available,'uptime':subprocess.check_output(['uptime'],text=True,timeout=10).strip(),'primary_source':{'branch':git('branch','--show-current'),'commit':git('rev-parse','HEAD'),'status':git('status','--porcelain','--untracked-files=all')},'scope':'read-only selected-name finite scans and nonblocking kernel lease checks; no actual job/source synchronization or evidence/raw modification'},indent=2))
'''
r=subprocess.run(['ssh','mbit10','/data1/yanruj/venvs/swdb-test/bin/python','-B','-'],input=remote,text=True,capture_output=True,timeout=90)
target=P('/private/tmp/probata-root-pause-idle-closure-20261016.json');assert not target.exists()
try:remote_data=json.loads(r.stdout)
except Exception:remote_data={'unparsed_stdout':r.stdout}
clear_local=not local['lease_paths_present']and free_B and all(not s['selected_active']and not s['inspection_denials']for s in scans)
clear_remote=r.returncode==0 and len(remote_data.get('metadata',{}))==3 and all(v['state']=='released'for v in remote_data.get('metadata',{}).values())and all(v.get('kernel_flock_available')for v in remote_data.get('kernel_lease_checks',{}).values())and len(remote_data.get('kernel_lease_checks',{}))==3 and all(not s['selected_active']and not s['inspection_denials']for s in remote_data.get('finite_scans',[]))
out={'date_ET':'2026-10-16','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'user_requested_pause':True,'root_inspector':pin(__file__),'Mac':local,'mbit10':remote_data,'ssh_exit':r.returncode,'ssh_stderr':r.stderr,'finite_idle_closure_pass':bool(clear_local and clear_remote),'no_new_evaluations':True,'scope':'Pause settlement only; never a proof claim or universal process absence'}
target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'receipt':pin(target),'finite_idle_closure_pass':out['finite_idle_closure_pass'],'Mac_leases':local['lease_paths_present'],'B_free':free_B,'mbit10_locks':remote_data.get('kernel_lease_checks'),'mbit10_active':[s['selected_active']for s in remote_data.get('finite_scans',[])]},indent=2));raise SystemExit(0 if out['finite_idle_closure_pass']else 1)
