"""2026-10-16 ET. Root compiler/scripted public persistence admission; no proof credit."""
from pathlib import Path
import dataclasses,datetime,fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time,xml.etree.ElementTree as ET
import psutil
P=Path
def H(p):
 with P(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'path':str(P(p).resolve()),'sha256':H(p),'bytes':P(p).stat().st_size}
fixed={
 '/private/tmp/probata-root-initialized-public-admission-v1-20261016.json':'38bfa0844a560d36060eff9b204538cc20c2ff40368cfbdca8bff1596dfaa806',
 '/private/tmp/probata-t28-initialized-u32-public-control-independent-static-review-v1-188a478e-20261016.md':'d94d7e7ba153b454cd5989652f3e6d39797e9aadca8f11f015b0bb995d3a1656',
 '/private/tmp/probata-t28-initialized-u32-public-control-command-v1-188a478e-20261016.json':'2546552abee265cfc7a5a374e60de115b3e337f52dd130084c431573ce9b48a0',
 '/private/tmp/probata-t28-initialized-u32-public-control-entry-v1-20261016.py':'5557ff0afc1ea95946e657286dfeb6fb7a6175eb9ae3de7aed365bcb42d9bc5c',
 '/private/tmp/probata-mac-compiler-worker-b.py':'873ac0b65eaa7edd4e0f624a86e68141c0e340f9ab1ca6816a07598538548a0e'}
for p,h in fixed.items():assert H(p)==h,p
assert H(sys.executable)=='08fa4dbadc420090dfee2acf433b827ae05541f728d1478d96879122f53b4328'
admission=json.loads(P(next(iter(fixed))).read_bytes());command=json.loads(P(list(fixed)[2]).read_bytes())
project=P(command['cwd']);source=project.parent;raw=P(command['root_creates_fresh_raw_parent']);component=raw/'component'
guard=P(command['guarded_inner_argv'][4]);assert H(guard)=='c6f0d4b8c60fab912dd768c4c8c7e7737d8feca3a110d0de02dec4d38785db57'
assert H(guard.with_name('staged_search.py'))=='125e2562342e6ba684d1189ca29fb48476b73bee30d0fd368f7f7c6b4c6b2419'
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(source),*a],text=True,timeout=30).strip()
def source_checks():
 assert git('rev-parse','HEAD')==admission['source_commit']and not git('status','--porcelain','--untracked-files=all')
 for row in admission['tracked_source_consumer_files']:
  p=source/row['relative'];assert not p.is_symlink()and p.is_file()and p.stat().st_size==row['bytes']and H(p)==row['sha256'],str(p)
 for row in admission['ignored_cache_rows']:assert pin(row['path'])=={k:row[k]for k in ['path','sha256','bytes']}
 for relative in ['swdb-project/swdb','swdb-project/tests']:
  actual={str(p.relative_to(source))for p in(source/relative).rglob('*')if p.is_file()}
  expected={r['relative']for r in admission['tracked_source_consumer_files']+admission['ignored_cache_rows']if r['relative'].startswith(relative+'/')}
  assert actual==expected
source_checks();assert not raw.exists()and not raw.is_symlink()
leases=[P('/tmp/claude/swdb-verifier.lock'),P('/tmp/claude/swdb-verifier.slot2.lock'),P('/tmp/claude/swdb-native-b.lock')]
assert not any(p.exists()for p in leases)
def observations():
 active=[];denied=[];count=0
 for proc in psutil.process_iter(['pid','name','uids']):
  try:
   if proc.info['uids'].real!=os.getuid():continue
   count+=1
   if proc.info['name']in {'frama-c','frama-c.exe','why3','why3server','alt-ergo','z3','cvc5','cbmc','clang++','clang-22','ocamlopt','ocamlopt.opt'}:active.append({'pid':proc.pid,'name':proc.info['name'],'birth':proc.create_time()})
  except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
  except psutil.AccessDenied:denied.append(proc.pid)
 return {'active_selected_tools':active,'inspection_denials':denied,'same_uid_metadata_count':count}
pre=observations();assert not pre['active_selected_tools']and not pre['inspection_denials']
with P('/private/tmp/probata-mac-compiler-worker-b.lock').open('a')as f:
 fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f.fileno(),fcntl.LOCK_UN)
free=shutil.disk_usage('/private/tmp').free;assert free>50*1024**3+256*1024**2
runtime_policy=json.loads(P(admission['runtime_policy']['path']).read_bytes());assert pin(admission['runtime_policy']['path'])==admission['runtime_policy']
for row in runtime_policy['pins']:assert pin(row['path'])==row
for t in admission['runtime_tree_memberships']:
 root=P(t['root']);members=[{'relative':str(p.relative_to(root)),**pin(p)}for p in sorted(root.rglob('*'))if p.is_file()]
 assert len(members)==t['files']and hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest()==t['membership_sha256']
watchdog=project/'swdb/rss_watchdog.py';assert H(watchdog)=='8cbe4f803951cee080581862b69a0b7bf21e35c554dc5cfde4db7d9f2779e5b6'
spec=importlib.util.spec_from_file_location('root_selected_rss_watchdog',watchdog);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
raw.mkdir();pre.update(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),free_bytes=free,available_ram=psutil.virtual_memory().available,memory_pressure=subprocess.check_output(['/usr/bin/memory_pressure','-Q'],text=True,timeout=15),root_entry=pin(__file__),admission=pin(next(iter(fixed))),command=command,outer_seconds=300,outer_cap_bytes=8*1024**3,workers=1,raw_allowance_bytes=256*1024**2,raw_allowance_is_quota=False,scope='real compiler and scripted verifier persistence only; no actual formal result or native caller')
(raw/'root-preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
r=module.run(command['guarded_inner_argv'],log=raw/'outer.log',cap_bytes=8*1024**3,timeout=300,cwd=str(source))
(raw/'outer-receipt.json').write_text(json.dumps(dataclasses.asdict(r),indent=2)+'\n')
sweeps=[]
for _ in range(3):sweeps.append(observations());time.sleep(.05)
source_checks()
for row in runtime_policy['pins']:assert pin(row['path'])==row
summary=json.loads((raw/'guard.log.summary.json').read_bytes())if(raw/'guard.log.summary.json').exists()else None
result=json.loads((component/'result.json').read_bytes())if(component/'result.json').exists()else None
tests=[]
if(component/'junit.xml').exists():
 xml=ET.parse(component/'junit.xml')
 tests=[{'name':n.attrib.get('name'),'classname':n.attrib.get('classname'),'failure':n.find('failure')is not None,'error':n.find('error')is not None,'skipped':n.find('skipped')is not None}for n in xml.findall('.//testcase')]
total=sum(p.stat().st_size for p in raw.rglob('*')if p.is_file())
ok=r.exit_code==0 and not r.out_of_memory and not r.timed_out and result and result['test_exit_code']==0 and result['source_unchanged']and result['runtime_pins_unchanged']and len(tests)==1 and tests[0]['name']=='test_public_initialized_u32_has_ordinary_prewrite_capacity_and_original_partial_frame'and not any(tests[0][k]for k in ['failure','error','skipped'])and total<=256*1024**2 and all(not s['active_selected_tools']and not s['inspection_denials']for s in sweeps)and not any(p.exists()for p in leases)
receipt={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'compiler/scripted public workflow only','workflow_controls_passed':bool(ok),'root_entry':pin(__file__),'raw':str(raw),'raw_bytes_before_root_receipt':total,'resources':dataclasses.asdict(r),'guard':summary,'result':result,'junit':tests,'source_unchanged':True,'runtime_pins_unchanged':True,'finite_settlement_sweeps':sweeps,'leases_present':[str(p)for p in leases if p.exists()],'actual_formal_acceptance':False,'source_body_proof':False,'native_caller_execution':False,'current_0_2':False,'full_ticket28':False}
target=P('/private/tmp/probata-root-initialized-public-execution-v1-20261016.json');assert not target.exists();target.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':pin(target),'workflow_controls_passed':bool(ok),'resources':dataclasses.asdict(r),'junit':tests,'result':result},indent=2));raise SystemExit(0 if ok else 1)
