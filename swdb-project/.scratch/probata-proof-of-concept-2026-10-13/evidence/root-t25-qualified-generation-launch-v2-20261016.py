"""2026-10-16 ET. Inert root admission/guard recipe until explicit root dispatch."""
import datetime as D,hashlib as H,json as J,os,pathlib as P,shutil,subprocess as S,sys,time
import psutil
assert __debug__
def sha(p):return H.sha256(P.Path(p).read_bytes()).hexdigest()
command=P.Path('/private/tmp/probata-t25-qualified-generation-command-v1-01771a83-20261016.json');assert sha(command)=='09d8bd5d96c529306eae2e01f9c625c8947a93dcb54aa16769dbcc05b7a75487'
c=J.loads(command.read_text());e=P.Path(c['expected']['path']);entry=P.Path(c['entry']['path'])
assert sha(e)==c['expected']['sha256'] and sha(entry)==c['entry']['sha256']
expected=J.loads(e.read_text());runtime=expected['runtime'];raw=P.Path(c['raw_root']);checkout=P.Path(c['command'][-1]);source=c['source_commit']
guard=P.Path('/private/tmp/probata-resume-t07-private-array/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/counted_verifier.py');assert sha(guard)=='c6f0d4b8c60fab912dd768c4c8c7e7737d8feca3a110d0de02dec4d38785db57'
sys.path.insert(0,str(guard.parent));import staged_search
assert P.Path(staged_search.__file__).resolve()==guard.parent/'staged_search.py' and sha(staged_search.__file__)=='125e2562342e6ba684d1189ca29fb48476b73bee30d0fd368f7f7c6b4c6b2419'
assert P.Path(sys.executable).resolve()==P.Path(runtime['python']['resolved']) and sha(sys.executable)==runtime['python']['sha256']
ps=runtime['psutil_surface'];assert P.Path(psutil.__file__).resolve().is_relative_to(P.Path(ps['path']).resolve())
for row in ps['files']:assert str(P.Path(row['path']).resolve())==row['resolved'] and sha(row['path'])==row['sha256']
assert os.environ.get('PYTHONOPTIMIZE') in (None,'','0')
assert not raw.exists()
assert S.check_output(['/usr/bin/git','--no-replace-objects','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==source
assert not S.check_output(['/usr/bin/git','-C',str(checkout),'status','--porcelain','--untracked-files=all'],text=True).strip()
S.run(['/usr/bin/git','--no-replace-objects','-C',str(checkout),'merge-base','--is-ancestor',source,c['publication_ref']],check=True)
leases=[P.Path('/tmp/claude/swdb-verifier.lock'),P.Path('/tmp/claude/swdb-verifier.slot2.lock')]
wait=time.monotonic()
while any(p.exists() for p in leases) and time.monotonic()-wait<35:time.sleep(.25)
assert not any(p.exists() for p in leases),'shared slot held; no admission'
names={'frama-c','frama-c.exe','alt-ergo','why3','z3','cvc5','why3server'}
def scan():
 seen=[];denied=[]
 for p in psutil.process_iter():
  try:
   if p.uids().real!=os.getuid():continue
   if p.name() in names:seen.append({'pid':p.pid,'birth':p.create_time(),'name':p.name()})
  except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
  except psutil.AccessDenied:denied.append(p.pid)
 return {'at_et':D.datetime.now().astimezone().isoformat(),'selected_same_uid_metadata':seen,'inspection_denial_pids':denied}
pre_scan=scan();assert not pre_scan['selected_same_uid_metadata'],'actual verifier already active'
assert not pre_scan['inspection_denial_pids'],'preflight process metadata unreadable; no admission'
free=shutil.disk_usage('/private/tmp').free;assert free>=50*1024**3+c['child_budget']['output_bytes']
argv=[sys.executable,str(guard),'--log',str(raw/'guard.log'),'--cap-gb','8','--timeout','600','--queue-timeout','30','--owner','t25-qualified-generation-01771a83','--lock',str(leases[0]),'--',*c['command']]
receipt_prefix=P.Path('/private/tmp/probata-root-t25-qualified-generation-v2-20261016')
pre={'at_et':D.datetime.now().astimezone().isoformat(),'source_commit':source,'command':argv,'command_recipe_sha256':sha(command),'entry_sha256':sha(entry),'expected_sha256':sha(e),'guard_sha256':sha(guard),'staged_search_sha256':sha(staged_search.__file__),'source_mode':'310immutableGitblobsfromclean017checkout','shared_leases_absent':True,'pre_scan':pre_scan,'lease_wait_seconds':time.monotonic()-wait,'free_bytes':free,'memory_pressure':S.check_output(['/usr/bin/memory_pressure','-Q'],text=True),'scope':'One generation-only selected global check lemma; actual native reader compile plus WP/Why3 internal task compile. Fresh CVC5 sentinel must never execute. No solver/body/caller/original-v2 acceptance. 600swhole/720souter/8GiBsampledRSS/oneworker,256MiBcheckedbetweenchildren/notquota.'}
P.Path(str(receipt_prefix)+'-preflight.json').write_text(J.dumps(pre,indent=2)+'\n')
raw.mkdir()
with (raw/'root-driver.log').open('w') as log:
 p=S.Popen(argv,cwd=checkout,stdout=log,stderr=S.STDOUT)
 try:code=p.wait(timeout=720)
 except S.TimeoutExpired:
  p.terminate()
  try:code=p.wait(timeout=30)
  except S.TimeoutExpired:
   P.Path(str(receipt_prefix)+'-watchdog.json').write_text(J.dumps({'guard_pid':p.pid,'guard_not_settled':True,'further_admission_forbidden':True})+'\n');raise RuntimeError('owned guard not settled')
observations=[]
for i in range(3):
 observations.append(scan())
 if i<2:time.sleep(.05)
settled={'exit_code':code,'at_et':D.datetime.now().astimezone().isoformat(),'source_commit':source,'source_unchanged':S.check_output(['/usr/bin/git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==source and not S.check_output(['/usr/bin/git','-C',str(checkout),'status','--porcelain','--untracked-files=all'],text=True).strip(),'finite_observations':observations,'shared_lease_paths_present_after':[str(p) for p in leases if p.exists()],'boundary':'Finite sameUID/name/PID/birth scans only; no universal/environment/token absence. Guard receipt owns resource and child cleanup evidence.'}
P.Path(str(receipt_prefix)+'-settlement.json').write_text(J.dumps(settled,indent=2)+'\n');print(J.dumps(settled,indent=2));raise SystemExit(code)
