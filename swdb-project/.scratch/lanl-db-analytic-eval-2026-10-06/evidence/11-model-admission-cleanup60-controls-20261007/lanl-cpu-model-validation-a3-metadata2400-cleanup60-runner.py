import sys;sys.dont_write_bytecode=True
from pathlib import Path
import datetime,hashlib,json,math,os,shutil,signal,subprocess,time
S=Path(SOURCE_VALUE);R=Path(RAW_VALUE);C=COMMIT_VALUE;phase=PHASE_VALUE;W=S/'swdb-project';status=0;child=None;deadline=time.monotonic()+18000
os.environ.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'compiler-temp'))
sys.path.insert(0,str(W))
from swdb.processes import stop_group
import ctypes,importlib.util
cleanup_path=Path('/data1/yanruj/lanl17-control-20261006.py')
assert hashlib.sha256(cleanup_path.read_bytes()).hexdigest()=='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
assert hashlib.sha256((W/'swdb/processes.py').read_bytes()).hexdigest()=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
proof=json.loads((W/'.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-linux-cleanup-smoke-mbit10-20261006-a1.json').read_text())['receipt']
assert proof['passed'] is True and proof['helper_sha256']=='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec' and proof['cleanup']['survivors']=={}
assert proof['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert sys.platform=='linux' and ctypes.CDLL(None).prctl(36,1,0,0,0)==0
spec=importlib.util.spec_from_file_location('cpu_owned_cleanup',cleanup_path);cleanup=importlib.util.module_from_spec(spec);spec.loader.exec_module(cleanup)

def clean():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==C
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=S,text=True)
def stop(signum,frame):raise RuntimeError('runner signal '+str(signum))
for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stop)
def run(args,name,cap=2400):
    global child
    remaining=min(cap,deadline-time.monotonic()-45);assert remaining>0
    with (R/(name+'.stdout')).open('w') as out,(R/(name+'.stderr')).open('w') as err:
        child=subprocess.Popen(list(map(str,args)),cwd=W,stdout=out,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=remaining)
        finally:
            stop_group(child,grace_seconds=15);child=None
            cleaned=cleanup.cleanup_owned()
            (R/(name+'.cleanup.json')).write_text(json.dumps(cleaned,indent=2)+'\n')
            assert cleaned['survivors']=={},'owned descendants survived stage cleanup'
    assert code==0,name+' exit '+str(code)
    return (R/(name+'.stdout')).read_text()

try:
 clean();(R/'started.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
 before_records=W/'records' if phase=='model' else Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+('model' if phase=='development' else 'development')+'-20261006-a3/records')
 shutil.copytree(before_records,R/'records');(R/'library').symlink_to(W/'library',target_is_directory=True)
 prior_files={str(p.relative_to(R/'records')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'records').rglob('*.yaml')}
 sys.path.insert(0,str(W));from swdb import artifacts;from swdb.store import Store
 store=Store(R/'records');prefix=['python3','-m','swdb'];target='mbit10.cpu.lanl20261006.t1.services.v1';protocols={}
 chars={ (kernel,scale):kernel+'.kron-g'+str(scale)+'.t1.characterization.objects.a1' for scale in (16,17) for kernel in ('bfs','bc') }
 estimates={(k,g):'lanl.cpu.'+k+'.g'+str(g)+'.t1.estimate.v1' for k,g in chars}
 validations={(k,g):'lanl.cpu.'+k+'.g'+str(g)+'.t1.validation.v1' for k,g in chars}
 development={k:'lanl.cpu.'+k+'.t1.development-band.v1' for k in ('bfs','bc')};heldout={k:'lanl.cpu.'+k+'.t1.heldout-band.v1' for k in ('bfs','bc')}
 summary={'format':'swdb.prospective-native-model-acceptance.v1','updated':'2026-10-06 ET','phase':phase,'source_commit':C,'source_clean':True,'raw_transferred':False,'application_performance_timings_collected':phase!='model'}
 if phase=='model':
  calibrations=['service.clock.a2','resource.allocator.a1','resource.allocator-extra.a1','resource.memory.a1','resource.float-memory.a1','service.byte-read.a1','resource.bulk-total.a1','resource.bulk-total.a2','service.openmp.a1']
  args=['python3','-m','swdb.cpu_service_binding','--records',R/'records','--target-description','mbit10.cpu.lanl20261006a2.v2.t1','--characterization',chars['bfs',16]]
  for pair in [('bc',16),('bfs',17),('bc',17)]:args+=['--scope-characterization',chars[pair]]
  for suffix in calibrations:args+=['--calibration','mbit10.cpu.lanl20261006.'+suffix]
  args+=['--memory-footprint-bytes','8388608','--memory-cas-policy','max_constructed_success_failure_median','--bulk-profile-policy','max_constructed_profiles_median','--bulk-copy-calibration','mbit10.cpu.lanl20261006.resource.bulk-total.a1','--openmp-next-policy','max_constructed_success_failure_median']
  for k,g in chars:args+=['--openmp-projection',W/('.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-'+k+'.g'+str(g)+'-projection-mbit10-20261006-a1.json')]
  args+=['--id',target,'--format','json'];run(args,'bind')
  for kernel in ('bfs','bc'):
   observed=[store.get(chars[kernel,g],'workload_characterization') for g in (16,17)]
   assert len({c['subject']['id'] for c in observed})==1
   arguments={c['input']:c['source']['run_arguments'] for c in observed}
   assert len(arguments)==2
   request_id='lanl.cpu.'+kernel+'.t1.native-model.v1'
   request={'message_version':'1.0','id':request_id,'version':1,'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':target,'inputs':list(arguments),'input_run_arguments':arguments,'sources':[observed[0]['subject']['id']],'roi':'gapbs.trial_lambda.v1','threads':1}}
   p=R/(kernel+'-protocol-request.json');p.write_text(json.dumps(request,indent=2)+'\n')
   frozen=json.loads(run([*prefix,'freeze-protocol',p,'--records',R/'records','--format','json'],'freeze-'+kernel))
   assert frozen['id']==request_id+'.'+frozen['identity_sha256'][:16]
   protocols[kernel]=frozen['id']
  for pair,char in chars.items():
   k,g=pair;run([*prefix,'estimate','--records',R/'records','--characterization',char,'--target-description',target,'--protocol',protocols[k],'--id',estimates[pair],'--format','json'],'estimate-'+k+'-g'+str(g))
  store=Store(R/'records');rows=[]
  for pair,rid in estimates.items():
   e=store.get(rid,'estimate');rows.append({'id':rid,'sha256':artifacts.digest(e),'seconds':e['seconds'],'evidence_kind':e['evidence_kind'],'protocol':e['protocol'],'estimator_sha256':e['estimator_sha256'],'target_description_sha256':e['target_description_sha256'],'characterization_sha256':e['characterization_sha256']})
  target_record=store.get(target,'target_description');binding=target_record['extensions']['cpu_services_binding']
  assert not [row for row in binding['compatibility'] if row['missing'] or any(scope['missing'] for scope in row.get('scopes',[]))],'independent service transfer compatibility missing'
  summary.update(estimates=rows,target_sha256=artifacts.digest(target_record),protocols={k:{'id':rid,'sha256':artifacts.digest(store.get(rid,'protocol'))} for k,rid in protocols.items()},calibrations=binding['calibrations'],characterizations=binding['characterization_allowlist'],ready_for_development=all(type(row['seconds']) in (int,float) and math.isfinite(row['seconds']) and row['seconds']>0 and row['evidence_kind']=='execution' for row in rows),conditional_resource_scope='gross memory and allocator resources use maximum with counted compute; gross bulk loops remain additive opaque constructed overhead; allocator recipe frozen after independent service collection before application timing; inferred 8MiB scenario; logical request denominator; no physical or proved application-bound claim')
  (R/'frozen-model.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
  assert summary['ready_for_development'],'unknown whole-call result retained; no application timing authorized'
 else:
  model_path=Path('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3/acceptance.json')
  model=json.loads(model_path.read_text())
  assert model['identity_sha256']==artifacts.digest({k:v for k,v in model.items() if k!='identity_sha256'})
  assert model['source_commit']==C and model['ready_for_development'] is True
  assert artifacts.digest(store.get(target,'target_description'))==model['target_sha256']
  for row in model['estimates']:
   estimate=store.get(row['id'],'estimate');assert artifacts.digest(estimate)==row['sha256']
  for pin in model['calibrations']+model['characterizations']:
   assert artifacts.digest(store.get(pin['id']))==pin['sha256']
  for pin in model['protocols'].values():
   assert artifacts.digest(store.get(pin['id'],'protocol'))==pin['sha256']
  summary['frozen_model_acceptance']={'path':str(model_path),'identity_sha256':model['identity_sha256']}
  scale=16 if phase=='development' else 17
  protocols={k:store.get(estimates[k,scale],'estimate')['protocol'] for k in ('bfs','bc')}
  assert all(protocols[k]==model['protocols'][k]['id'] for k in protocols)
  summary['protocols']=model['protocols']
  for kernel in ('bfs','bc'):
   pair=(kernel,scale);args=[*prefix,'collect-cpu-native-validation','--records',R/'records','--characterization',chars[pair],'--estimate-protocol',protocols[kernel],'--id',validations[pair],'--output',R/(kernel+'.g'+str(scale)),'--machine','mbit10','--lane','mbit10-evaluation-node0','--llvm-bin','/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin','--run-library-path','/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu','--max-wall-s','900','--format','json']
   if phase=='holdout':args+=['--development-band',development[kernel]]
   run(args,'collect-'+kernel+'-g'+str(scale),3600)
  bands={}
  for kernel in ('bfs','bc'):
   args=[*prefix,'freeze-cpu-error-band' if phase=='development' else 'validate-cpu-error-band','--records',R/'records','--id',development[kernel] if phase=='development' else heldout[kernel],'--format','json']
   if phase=='holdout':args+=['--development-band',development[kernel]]
   args+=['--estimate',estimates[kernel,scale],'--validation',validations[kernel,scale]]
   run(args,'band-'+kernel);store=Store(R/'records');b=store.get(development[kernel] if phase=='development' else heldout[kernel],'cpu_error_band')
   bands[kernel]={'id':b['id'],'sha256':artifacts.digest(b),'state':b['state'],'width_log':b['width_log'],'admission':b['admission']}
  summary['bands']=bands
  if phase=='development':summary['ready_for_holdout']=all(b['state']=='development' and b['width_log'] is not None for b in bands.values())
 summary['validation']=run([*prefix,'validate','--records',R/'records'],'validate',2400).strip();assert summary['validation'].startswith('OK: ')
 assert all((R/'records'/rel).is_file() and hashlib.sha256((R/'records'/rel).read_bytes()).hexdigest()==digest for rel,digest in prior_files.items()),'prior canonical record bytes changed'
 summary['prior_record_bytes_preserved']=len(prior_files)
 clean();summary['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();summary['identity_sha256']=artifacts.digest(summary)
 (R/'acceptance.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
except BaseException as exc:status=1;(R/'runner-error.txt').write_text(type(exc).__name__+': '+str(exc)+'\n')
finally:
 for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
 stop_group(child,grace_seconds=15);child=None
 final_cleanup=cleanup.cleanup_owned();(R/'final-cleanup.json').write_text(json.dumps(final_cleanup,indent=2)+'\n');assert final_cleanup['survivors']=={}
 (R/'runner-exit-code.txt').write_text(str(status)+'\n');(R/'completed.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
sys.exit(status)
