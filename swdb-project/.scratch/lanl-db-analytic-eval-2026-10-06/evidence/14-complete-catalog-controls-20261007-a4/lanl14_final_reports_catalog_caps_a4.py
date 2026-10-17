"""Parent-only public nine-pair freeze/estimate/report. Prepared 2026-10-07 ET.

No SSH, provider, native benchmark, timing or observer mutation. Import and
portable controls are inert. Final tested source/complete bundle/target hashes
are supplied prospectively after generic 11/17 integration. All leases must be
released before prepare/dispatch/export. Historical observations stay immutable.
"""
import argparse,ctypes,hashlib,importlib.util,json,os,re,shlex,shutil,signal,socket,subprocess,sys
from pathlib import Path

COUNT_HELPER_SHA='b797a19f0d80a1a91b852a360c19e59beba4fa082ce88c38cbec029670e7deda'
COUNT_EXPORTER_SHA='7d77776f7b2582ae24c6be8254f34ea9fff632d777a8297c7d2fe8437f71ec09'
EVIDENCE='.scratch/lanl-db-analytic-eval-2026-10-06/evidence/'
THREADS={'cpu':1,'dx100':4,'maple':2}
TARGETS={'cpu':'mbit10','dx100':'dx100-e4fc4af-functional-analytic-v1','maple':'maple-isca2022'}
CHARS={
 ('bfs','dx100'):'bfs.functional.kron-g16.t4.characterization.objects.a2',
 ('bfs','cpu'):'bfs.kron-g16.t1.characterization.objects.a1',
 ('bc','cpu'):'bc.kron-g16.t1.characterization.objects.a1',
 ('pagerank','cpu'):'pagerank.jacobi.kron-g16.cpu.t1.characterization.generality.a1',
 ('pagerank','dx100'):'pagerank.jacobi.kron-g16.dx100.t4.characterization.generality.a1',
 ('pagerank','maple'):'pagerank.jacobi.kron-g16.maple.t2.characterization.generality.a1',
 ('bfs','maple'):'bfs.kron-g16.bfs-maple.t2.characterization.generality.a1',
 ('bc','maple'):'bc.kron-g16.bc-maple.t2.characterization.generality.a1',
 ('bc','dx100'):'bc.kron-g16.bc-dx100.t4.characterization.generality.a1'}
OLD_FILES={
 'bfs.kron-g16.t1.characterization.objects.a1':'cda2c51423c167249fd760f359ee0ead180bcb2e2d4db2c722c9b724120458ba',
 'bc.kron-g16.t1.characterization.objects.a1':'d12b5f57c61007219d367942ee554db1d27ee1d8614e2c1279e1164230f534e8',
 'bfs.functional.kron-g16.t4.characterization.objects.a2':'dfbb5791ebe8bf63b544a548541fd8b5a7eeb8e033fe3aef2316c4c7467e325a'}
CPU_ALLOWED={'bfs.kron-g16.t1.characterization.objects.a1','bc.kron-g16.t1.characterization.objects.a1',
 'bfs.kron-g17.t1.characterization.objects.a1','bc.kron-g17.t1.characterization.objects.a1'}

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def count_helper(path):
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==COUNT_HELPER_SHA,'Keep original active count dispatcher immutable'
 return load(path,'lanl14_frozen_counts')
def modules(h,source):return {p.relative_to(source/'swdb-project/swdb').as_posix():h.sha(p) for p in sorted((source/'swdb-project/swdb').rglob('*.py'))}
def public_imports(source):
 sys.dont_write_bytecode=True;sys.path.insert(0,str(source/'swdb-project'))
 from swdb import artifacts,access,analytic_binding,analytic_count_reuse,analytic_trial_scope
 from swdb.store import Store
 from swdb.estimate_protocol import estimator_identity
 return artifacts,access,analytic_binding,analytic_count_reuse,analytic_trial_scope,Store,estimator_identity
def get(store,rid,kind):
 value=store.get(rid,kind);assert value is not None,(kind,rid);return value
def pin(h,store,rid):
 value=get(store,rid,store.by_id[rid].kind)
 return {'path':store.path_of(rid),'id':rid,'kind':value['kind'],'sha256':h.digest(value),'file_sha256':h.sha(store.dir/store.path_of(rid))}
def require_bundle(h,source,manifest):
 assert modules(h,source)==manifest['module_hashes'] and h.digest(modules(h,source))==manifest['estimator_sha256'],'Final estimator/mechanism source changed'
def require_observer(h,source,data):
 llvm=source/'swdb-project/swdb/llvm';receipt=data['binding']['execution_receipt'];obs=data['observation_contract']
 assert receipt['plugin_source_sha256']==h.sha(llvm/'Characterize.cpp') and receipt['runtime_source_sha256']==h.sha(llvm/'CountingRuntime.cpp'),'Observer source changed; new counts required'
 assert receipt['pipeline_version']=='source-normalized-v2' and receipt['passes']==['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']
 assert obs['runtime_bundle_sha256']==h.digest({n:h.sha(llvm/n) for n in ('CountingRuntime.cpp','LiveObjects.hpp','LogicalCommands.hpp')})
 scope=obs['object_scope_contract'];assert scope['observer_sha256']==h.sha(llvm/'ObjectScopes.hpp') and scope['runtime_sha256']==h.sha(llvm/'ObjectScopeRuntime.hpp')
 if 'observer_bundle_sha256' in obs:assert obs['observer_bundle_sha256']==h.digest({n:h.sha(llvm/n) for n in ('Characterize.cpp','SemanticCommands.hpp')})
def fresh_access_scope(data):
 for trial in data['trials']:
  facts=[]
  for region in trial['regions']:
   facts+=list(region['operation_counts'].values())+list(region['dynamic_counts'].values())
   for access in region['access_patterns']:facts.extend(access[n] for n in ('element_count','bytes_accessed'))
  for call in trial['unmodeled_calls']:facts.extend(call[n] for n in ('execution_count','size_bytes'))
  assert all(f.get('scope')=='per_trial' for f in facts),'Fresh six-count trial scopes must be per_trial'
def argument_scope(data,kernel,target):
 expected=['-g','16','-k','16','-n','5']
 if kernel=='bc' and target in {'cpu','maple'}:expected+=['-i','1']
 assert data['source']['run_arguments']==expected,'Exact registered original run arguments differ'
def cpu_allowlist(h,store,target):
 rows=target['extensions']['cpu_services_binding']['characterization_allowlist']
 assert len(rows)==4 and {r['id'] for r in rows}==CPU_ALLOWED,'Exact four BF/BC T1 service scope only; no Jacobi transfer'
 for row in rows:assert row['sha256']==h.digest(get(store,row['id'],'workload_characterization')),'CPU service source pin changed'
 for mechanism in target['mechanisms']:
  allowed=mechanism.get('selector',{}).get('characterization_allowlist')
  if allowed is not None:assert sorted(allowed,key=lambda r:r['id'])==sorted(rows,key=lambda r:r['id']),'CPU mechanism allowlist differs'
 return rows
def count_receipt(h,source,path,store):
 receipt=h.checked(path);assert receipt['format']=='swdb.lanl14-generality-counts-compact.v1' and receipt['dispatcher_sha256']==COUNT_HELPER_SHA and receipt['exporter_sha256']==COUNT_EXPORTER_SHA
 assert receipt['raw_transferred'] is False and receipt['application_timings']==receipt['provider_calls']==0 and receipt['cleanup_survivors']=={}
 assert receipt['added_export_time_verification']=={'fields':['element_count','bytes_accessed'],'scope':'per_trial','every_trial_access_checked':True}
 assert len(receipt['new_records'])==10 and len(receipt['cases'])==6 and {c['case'] for c in receipt['cases']}==set(h.CASES)
 for row in receipt['new_records']:
  actual=pin(h,store,row['id']);assert actual['kind']==row['kind'] and actual['path']==row['path'] and actual['sha256']==row['sha256'] and actual['file_sha256']==row['file_sha256']
 for row in receipt['cases']:
  assert row['export_time_access_scope_verification']['passed'] is True
  assert row['characterization']['id']==h.CASES[row['case']]['characterization'] and row['lane']['exit_code']==0 and row['lane']['ended_utc']
 return {'file_sha256':h.sha(path),'identity_sha256':receipt['identity_sha256'],'source_commit':receipt['source_commit'],'six_fresh_cases':True,'export_time_bytes_accessed_scope_checked':True}
def admission(h,source,records,targets,receipt_path):
 artifacts,access,binding,reuse,legacy,Store,identity=public_imports(source);store=Store(records)
 assert not store.problems
 count_proof=count_receipt(h,source,receipt_path,store);rows=[]
 cpu_allowlist(h,store,get(store,targets['cpu']['id'],'target_description'))
 for (kernel,target),rid in CHARS.items():
  data=get(store,rid,'workload_characterization');td=get(store,targets[target]['id'],'target_description')
  assert h.digest(td)==targets[target]['sha256'] and td['threads']==THREADS[target] and td['target']==TARGETS[target]
  assert data['binding']['state']=='verified' and data['evidence_kind']=='execution' and data['coverage']['whole_timed_call'] is True
  assert data['binding']['threads']==THREADS[target] and len(data['trials'])==5 and [t['position'] for t in data['trials']]==list(range(5))
  assert data['binding']['roi']==('gapbs.functional_trial_lambda.v1' if target=='dx100' or kernel=='pagerank' else 'gapbs.trial_lambda.v1')
  argument_scope(data,kernel,target)
  assert not binding.verify_binding(data,store,require_available=False),'Registered source/input/ROI proof failed'
  require_observer(h,source,data)
  scope=[]
  if rid in OLD_FILES:assert h.sha(records/store.path_of(rid))==OLD_FILES[rid],'Historical count/receipt bytes are immutable'
  if (kernel,target) in [('bfs','cpu'),('bc','cpu')]:
   for trial in data['trials']:
    normalized,proof=legacy.reconcile_trial(data,trial,store);assert proof is not None and normalized!=trial,'Strict sealed legacy window not admitted'
    assert proof['characterization_sha256']==h.digest(data) and proof['position']==trial['position'];scope.append(proof)
  else:fresh_access_scope(data) if rid not in OLD_FILES else None
  reuse_proof=reuse.resolve(data,td)
  if target=='dx100' and kernel in ('bfs','bc'):assert reuse_proof is not None,'Complete target observation policy missing'
  if kernel=='pagerank':assert data['source']['sha256']==h.RECIPE_PINS['apps/gapbs/src/pr_spmv.cc'] and data['subject']=={'kind':'implementation','id':'gapbs-pr-jacobi-analytic-v1'} and all(t['sources']==[] for t in data['trials'])
  if target=='maple':assert td['extensions']['estimate_only'] is True and td['extensions']['accuracy_validation'] is False and td['extensions']['paired_timing'] is None
  subject=get(store,data['subject']['id'],data['subject']['kind']);implementation=subject['implementation'] if subject['kind']=='candidate' else subject['id']
  source_ids=[subject['id']]
  snapshot=data['binding']['subject_source_identity'].get('source_snapshot')
  if snapshot:source_ids.append(snapshot)
  rows.append({'kernel':kernel,'target':target,'characterization':pin(h,store,rid),'subject':pin(h,store,subject['id']),'implementation':pin(h,store,implementation),
   'target_description':pin(h,store,td['id']),'input':data['input'],'roi':data['binding']['roi'],'threads':THREADS[target],
   'run_arguments':data['source']['run_arguments'],'sources':source_ids,'count_reuse':reuse_proof,'legacy_trial_scope_proofs':scope})
 assert rows[0]['kernel']=='bfs' and rows[0]['target']=='dx100','Fresh final DX BFS reference executes first'
 return rows,count_proof

def prepare(args):
 h=count_helper(args.count_helper);h.host();assert re.fullmatch('[a-f0-9]{40}',args.source_sha) and args.source_sha==args.tested_source_sha
 assert re.fullmatch('[a-f0-9]{64}',args.estimator_sha256) and re.fullmatch('codex/[A-Za-z0-9._/-]+|yanrujhou_main',args.source_ref)
 assert re.fullmatch('[a-z0-9][a-z0-9-]{0,40}',args.tag)
 source=Path(args.source).resolve();raw=Path(args.raw).resolve()
 assert str(source).startswith('/data1/yanruj/ArchEvolve-lanl-') and str(raw).startswith('/data/yanruj/EvolveSWDB_runs/lanl-') and not source.exists() and not raw.exists()
 leases=h.free_all();capacity=h.capacity();wrapper=h.wrapper_identity();assert h.sha(args.cleanup_helper)==h.CLEANUP_SHA
 h.git(h.PRIMARY,'fetch','origin',args.source_ref);assert h.git(h.PRIMARY,'rev-parse','origin/'+args.source_ref)==args.source_sha
 h.git(h.PRIMARY,'worktree','add','--detach',source,args.source_sha);h.clean(source,args.source_sha);h.source_pins(source)
 _,_,_,_,_,_,identity=public_imports(source);assert identity()==args.estimator_sha256==h.digest(modules(h,source)),'Explicit final tested complete estimator bundle required'
 targets={name:{'id':getattr(args,name+'_target'),'sha256':getattr(args,name+'_sha256')} for name in THREADS}
 assert targets['cpu']['id']=='mbit10.cpu.lanl20261006.t1.services.v1' and targets['dx100']['id']=='dx100-e4fc4af-functional-analytic-v1.t4.estimated.a2' and targets['maple']['id']=='maple-isca2022.fpga-reference.t2'
 cleanup_path=source/'swdb-project'/EVIDENCE/'17-linux-cleanup-smoke-mbit10-20261006-a1.json';cleanup=h.cleanup_admission(source,cleanup_path)
 records=source/'swdb-project/records';rows,count_proof=admission(h,source,records,targets,args.count_receipt)
 raw.mkdir(parents=True);shutil.copytree(records,raw/'records');shutil.copytree(source/'swdb-project/library',raw/'library');(raw/'temporary').mkdir()
 before={'records':h.inventory(records),'library':h.inventory(source/'swdb-project/library'),'apps':h.inventory(source/'swdb-project/apps')}
 h.dump(raw/'protected.json',h.seal(before))
 manifest=h.seal({'format':'swdb.lanl14-final-reports-manifest.v1','created_utc':h.now(),'tag':args.tag,'source':str(source),'source_commit':args.source_sha,'tested_source_sha':args.tested_source_sha,
  'source_ref':args.source_ref,'raw':str(raw),'estimator_sha256':args.estimator_sha256,'module_hashes':modules(h,source),'targets':targets,'pairs':rows,'fresh_count_receipt':count_proof,
  'helper':{'path':str(Path(__file__).resolve()),'sha256':h.sha(__file__)},'count_helper':{'path':str(Path(args.count_helper).resolve()),'sha256':COUNT_HELPER_SHA},
  'cleanup_helper':{'path':str(Path(args.cleanup_helper).resolve()),'sha256':h.CLEANUP_SHA},'cleanup_proof':cleanup,'wrapper':wrapper,'leases_before':leases,'capacity_before':capacity,
  'protected_sha256':h.digest(before),'reporter_sha256':h.sha(source/'swdb-project/scripts/generality_report.py'),
  'limits':{'threads_max':4,'thread_limit':16,'provider_calls':0,'application_timings':0,'freeze_s':6000,'estimate_s':4000,'validate_s':3600,'report_s':3600,'outer_s':108000},
  'scope':'Fresh final-bundle public estimates of nine exact counted scopes. No new measured performance, PR CPU service/error-band transfer, MAPLE accuracy, or fabricated accelerator observation.'})
 h.dump(raw/'manifest.json',manifest);h.clean(source,args.source_sha);print(json.dumps({'manifest':str(raw/'manifest.json'),'identity_sha256':manifest['identity_sha256'],'pairs':9,'final_estimator_sha256':args.estimator_sha256}))
def checked_manifest(path):
 raw=json.loads(Path(path).read_text());h=count_helper(raw['count_helper']['path']);h.host();m=h.checked(path);source=Path(m['source']);h.clean(source,m['source_commit']);require_bundle(h,source,m)
 assert h.sha(__file__)==m['helper']['sha256'] and h.wrapper_identity()['sha256']==m['wrapper']['sha256'] and h.sha(m['cleanup_helper']['path'])==h.CLEANUP_SHA
 assert h.cleanup_admission(source,m['cleanup_proof']['path'])==m['cleanup_proof'];assert h.sha(source/'swdb-project/scripts/generality_report.py')==m['reporter_sha256']
 return h,m
def dispatch(args):
 h,m=checked_manifest(args.manifest);h.free_all();h.capacity();raw=Path(m['raw']);control=raw/'control';assert not control.exists();control.mkdir();shutil.copyfile(__file__,control/'helper.py')
 job='swdb-lanl14-reports-'+m['tag'];child=['python3',str(control/'helper.py'),'run','--manifest',str(raw/'manifest.json')]
 h.dump(control/'dispatch.json',h.seal({'manifest_sha256':m['identity_sha256'],'node':args.node,'job':job,'command':child}))
 argv=['timeout','--signal=TERM','--kill-after=40s','108000s','bash',m['wrapper']['path'],str(args.node),job,'--record',str(control/'lane.json'),'--lease-timeout-s','30','--no-align','--',*child]
 h.free_all();shell=' '.join(shlex.quote(x) for x in argv)+' > '+shlex.quote(str(control/'wrapper.stdout'))+' 2> '+shlex.quote(str(control/'wrapper.stderr'))
 shell+='; lanl14_report_exit=$?; printf "%s\\n" "$lanl14_report_exit" > '+shlex.quote(str(control/'wrapper-exit-code.txt'))
 h.command(['tmux','new-session','-d','-s',job,shell]);print(json.dumps({'job':job,'node':args.node,'control':str(control),'manifest_sha256':m['identity_sha256']}))
def run(args):
 h,m=checked_manifest(args.manifest);source=Path(m['source']);raw=Path(m['raw']);records=raw/'records';control=raw/'control'
 artifacts,access,_,reuse,_,Store,identity=public_imports(source)
 from swdb import provider_guard
 from swdb.processes import stop_group
 lane=provider_guard.verified_lane();assert '(verified:' in lane and ctypes.CDLL(None).prctl(36,1,0,0,0)==0
 cleanup=load(m['cleanup_helper']['path'],'lanl14_final_cleanup');child=None;status=0
 before=h.checked(raw/'protected.json');assert h.digest({k:v for k,v in before.items() if k!='identity_sha256'})==m['protected_sha256']
 assert h.inventory(records)==before['records'] and h.inventory(raw/'library')==before['library']
 def interrupted(signum,frame):raise InterruptedError('final reports signal '+str(signum))
 for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,interrupted)
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(source/'swdb-project'),'TMPDIR':str(raw/'temporary'),'OMP_NUM_THREADS':'1','OMP_THREAD_LIMIT':'16','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
 def invoke(argv,label,seconds):
  nonlocal child
  h.clean(source,m['source_commit']);require_bundle(h,source,m);h.dump(raw/(label+'-argv.json'),list(map(str,argv)))
  try:
   with (raw/(label+'.stdout')).open('w') as out,(raw/(label+'.stderr')).open('w') as err:
    child=subprocess.Popen(list(map(str,argv)),cwd=source/'swdb-project',env=env,stdout=out,stderr=err,start_new_session=True)
    assert child.wait(timeout=seconds)==0,label+' public command failed; preserve attempt'
  finally:stop_group(child,grace_seconds=15);child=None;assert cleanup.cleanup_owned()['survivors']=={}
  return (raw/(label+'.stdout')).read_text()
 try:
  invoke(['python3','-m','swdb','validate','--records',records,'--library',raw/'library'],'before-validate',3600)
  pairs=[];store=Store(records)
  for row in m['pairs']:
   kernel,target=row['kernel'],row['target'];name=kernel+'-'+target;char=get(store,row['characterization']['id'],'workload_characterization');td=get(store,row['target_description']['id'],'target_description')
   assert h.digest(char)==row['characterization']['sha256'] and h.sha(records/row['characterization']['path'])==row['characterization']['file_sha256']
   request={'message_version':'1.0','id':f"generality.{kernel}.{target}.kron-g16.t{row['threads']}.protocol.{m['tag']}",'version':1,
    'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':td['id'],'threads':row['threads'],'inputs':[row['input']],
     'input_run_arguments':{row['input']:row['run_arguments']},'roi':row['roi'],'sources':row['sources']}}
   request_path=raw/(name+'-freeze.json');h.dump(request_path,request)
   protocol=json.loads(invoke(['python3','-m','swdb','freeze-protocol',request_path,'--records',records,'--format','json'],name+'-freeze',6000))
   assert protocol['settings']['estimator_sha256']==m['estimator_sha256'] and protocol['settings']['target_description']['sha256']==h.digest(td)
   estimate_id=f"generality.{kernel}.{target}.kron-g16.t{row['threads']}.estimate.{m['tag']}"
   estimate=json.loads(invoke(['python3','-m','swdb','estimate','--records',records,'--characterization',char['id'],'--target-description',td['id'],'--protocol',protocol['id'],'--id',estimate_id,'--format','json'],name+'-estimate',4000))
   assert estimate['estimator_sha256']==m['estimator_sha256'] and estimate['characterization_sha256']==h.digest(char) and estimate['protocol_sha256']==protocol['identity_sha256']
   assert estimate['ratio'] is None and estimate['baseline'] is None and estimate['basis']=='estimated' and len(estimate['trials'])==5
   if row['legacy_trial_scope_proofs']:assert estimate['extensions']['legacy_trial_scope_reconciliations']==row['legacy_trial_scope_proofs']
   if kernel=='pagerank' and target=='cpu':assert estimate['error_band'] is None and estimate['seconds'] is None,'Jacobi lacks CPU service/band transfer'
   if target=='maple':assert estimate['error_band'] is None and estimate['seconds'] is None,'MAPLE reported facts do not fill effective services'
   if row['count_reuse'] is not None:assert estimate['count_reuse']==row['count_reuse']
   store.add(__import__('swdb.store',fromlist=['Record']).Record('protocols/'+protocol['id']+'.yaml',protocol));store.add(__import__('swdb.store',fromlist=['Record']).Record('estimates/'+estimate['id']+'.yaml',estimate))
   pairs.append({k:row[k] for k in ('kernel','target','subject','implementation','characterization')}|{'protocol':pin(h,store,protocol['id']),'estimate':pin(h,store,estimate['id'])})
  request=h.seal({'format':'swdb.generality-report-request.v1','updated':'2026-10-07 ET','scope':m['scope'],'reference':{'kernel':'bfs','target':'dx100'},'pairs':pairs})
  h.dump(raw/'report-request.json',request)
  invoke(['python3',source/'swdb-project/scripts/generality_report.py','--records',records,'--request',raw/'report-request.json','--output',raw/'report'],'nine-report',3600)
  report=h.checked(raw/'report/report.json');assert report['code_equality']['estimator_sha256']==m['estimator_sha256'] and report['code_equality']['module_hashes']==m['module_hashes'] and report['code_equality']['estimator_and_mechanism_diff']==[]
  validation=invoke(['python3','-m','swdb','validate','--records',records,'--library',raw/'library'],'final-validate',3600).strip();assert validation.startswith('OK: ')
  after=h.inventory(records);added=h.preservation(before['records'],after);assert len(added)==18 and all(p.startswith(('protocols/','estimates/')) and p.endswith('.yaml') for p in added)
  assert h.inventory(raw/'library')==before['library'] and h.inventory(source/'swdb-project/apps')==before['apps'];h.clean(source,m['source_commit']);require_bundle(h,source,m)
  acceptance=h.seal({'format':'swdb.lanl14-final-reports-acceptance.v1','completed_utc':h.now(),'manifest_sha256':m['identity_sha256'],'source_commit':m['source_commit'],'source_clean':True,
   'final_estimator_sha256':m['estimator_sha256'],'fresh_dx_bfs_reference':pairs[0]['estimate'],'report_sha256':report['identity_sha256'],'request_sha256':request['identity_sha256'],
   'added_record_paths':added,'prior_record_library_app_bytes_preserved':True,'validation':validation,'verified_lane':lane,'all_nine_public_estimates':True,'provider_calls':0,'application_timings':0,'raw_transferred':False})
  h.dump(control/'acceptance.json',acceptance)
 except BaseException as exc:status=1;(control/'runner-error.txt').write_text(type(exc).__name__+': '+str(exc)+'\n')
 finally:
  for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
  stop_group(child,grace_seconds=15);result=cleanup.cleanup_owned();h.dump(control/'final-cleanup.json',result);assert result['survivors']=={}
  (control/'runner-exit-code.txt').write_text(str(status)+'\n');(control/'completed.txt').write_text(h.now()+'\n')
 return status

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 prep=sub.add_parser('prepare')
 for name in ('source-sha','tested-source-sha','source-ref','source','raw','tag','estimator-sha256','count-helper','count-receipt','cleanup-helper'):prep.add_argument('--'+name,required=True)
 for target in THREADS:
  prep.add_argument('--'+target+'-target',required=True);prep.add_argument('--'+target+'-sha256',required=True)
 for name in ('dispatch','run'):
  child=sub.add_parser(name);child.add_argument('--manifest',required=True)
  if name=='dispatch':child.add_argument('--node',type=int,choices=(0,1),required=True)
 args=p.parse_args()
 if args.command=='prepare':prepare(args)
 elif args.command=='dispatch':dispatch(args)
 else:return run(args)
 return 0

if __name__=='__main__':raise SystemExit(main())
