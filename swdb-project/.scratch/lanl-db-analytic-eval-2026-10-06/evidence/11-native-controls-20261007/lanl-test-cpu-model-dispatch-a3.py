import ast,copy,json,math,tempfile
from pathlib import Path
from types import SimpleNamespace
from swdb import artifacts
from swdb.cpu_error_band import _common
source=Path('/private/tmp/lanl-dispatch-cpu-model-validation-a3.py').read_text();tree=ast.parse(source)
assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNNER_TEMPLATE' for t in n.targets))
runner=ast.literal_eval(assignment.value)
for phase in ('model','development','holdout'):
 compile(runner.replace('SOURCE_VALUE',repr('/tmp/source')).replace('RAW_VALUE',repr('/tmp/raw')).replace('COMMIT_VALUE',repr('1'*40)).replace('PHASE_VALUE',repr(phase)),'prospective-'+phase,'exec')
parsed=ast.parse(runner)
body=next(n for n in ast.walk(parsed) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='phase' and len(n.test.comparators)==1 and isinstance(n.test.comparators[0],ast.Constant) and n.test.comparators[0].value=='model')
with tempfile.TemporaryDirectory(prefix='lanl-dispatch-mock-') as temp:
 root=Path(temp);R=root/'raw';R.mkdir();W=root/'source';W.mkdir();C='1'*40
 chars={(k,g):k+'.kron-g'+str(g)+'.t1.characterization.objects.a1' for g in (16,17) for k in ('bfs','bc')}
 estimates={(k,g):'lanl.cpu.'+k+'.g'+str(g)+'.t1.estimate.v1' for k,g in chars}
 validations={(k,g):'lanl.cpu.'+k+'.g'+str(g)+'.t1.validation.v1' for k,g in chars}
 target='mbit10.cpu.lanl20261006.t1.services.v1';records={}
 for (k,g),rid in chars.items():
  records[rid]={'kind':'workload_characterization','id':rid,'input':'kron-g'+str(g)+'-k16','subject':{'id':'gapbs-'+k+'-baseline'},'source':{'run_arguments':['-g',str(g),'-k','16','-n','5']+(['-i','1'] if k=='bc' else [])}}
 calibration={'kind':'cpu_service_calibration','id':'independent.fixture.service'};records[calibration['id']]=calibration
 binding={'compatibility':[],'calibrations':[{'id':calibration['id'],'sha256':artifacts.digest(calibration)}],'characterization_allowlist':[{'id':rid,'sha256':artifacts.digest(records[rid])} for rid in chars.values()]}
 records[target]={'kind':'target_description','id':target,'extensions':{'cpu_services_binding':binding}}
 class FakeStore:
  def __init__(self,*args):pass
  def get(self,rid,kind=None):
   value=records[rid]
   assert kind is None or value['kind']==kind
   return value
 calls=[];frozen_requests=[]
 def run(args,name,cap=1400):
  args=list(map(str,args));calls.append((name,args,cap))
  if name=='bind':
   assert 'mbit10.cpu.lanl20261006.resource.allocator.a1' in args
   assert 'mbit10.cpu.lanl20261006.resource.allocator-extra.a1' in args
   assert 'mbit10.cpu.lanl20261006.service.allocator.a1' not in args
   assert 'mbit10.cpu.lanl20261006.service.allocator-extra.a1' not in args
   return '{}'
  if name.startswith('freeze-'):
   request=json.loads(Path(args[4]).read_text());frozen_requests.append(request)
   digest=artifacts.digest(request);rid=request['id']+'.'+digest[:16]
   settings=request['settings'];settings={**settings,'estimator_sha256':'2'*64,'target_description':{'id':target,'sha256':artifacts.digest(records[target])}}
   record={'kind':'protocol','id':rid,'identity_sha256':digest,'settings':settings};records[rid]=record;return json.dumps(record)
  if name.startswith('estimate-'):
   char=args[args.index('--characterization')+1];protocol=args[args.index('--protocol')+1];rid=args[args.index('--id')+1]
   assert protocol in records and protocol.count('.')>=2
   c=records[char];p=records[protocol];assert p['settings']['input_run_arguments'][c['input']]==c['source']['run_arguments'];assert p['settings']['sources']==[c['subject']['id']]
   e={'kind':'estimate','id':rid,'seconds':1.0,'evidence_kind':'execution','protocol':protocol,'estimator_sha256':'2'*64,'target_description_sha256':artifacts.digest(records[target]),'characterization_sha256':artifacts.digest(c),'threads':1,'target':'mbit10'};records[rid]=e;return json.dumps(e)
  if name.startswith('collect-'):
   assert cap==2100 and args[args.index('--max-wall-s')+1]=='900'
   char=args[args.index('--characterization')+1];k=char.split('.')[0];g=int(char.split('.kron-g')[1].split('.')[0])
   assert args[args.index('--estimate-protocol')+1]==records[estimates[k,g]]['protocol']
   assert ('--development-band' in args)==(g==17)
   if g==17:assert args[args.index('--development-band')+1]=='lanl.cpu.'+k+'.t1.development-band.v1'
   return '{}'
  if name.startswith('band-'):
   rid=args[args.index('--id')+1];heldout='validate-cpu-error-band' in args
   records[rid]={'kind':'cpu_error_band','id':rid,'state':'validated' if heldout else 'development','width_log':.2,'admission':{'validated':heldout}};return '{}'
  raise AssertionError(name)
 env={'Path':Path,'json':json,'math':math,'R':R,'W':W,'C':C,'phase':'model','store':FakeStore(),'Store':FakeStore,'prefix':['python3','-m','swdb'],'target':target,'protocols':{},'chars':chars,'estimates':estimates,'validations':validations,'development':{k:'lanl.cpu.'+k+'.t1.development-band.v1' for k in ('bfs','bc')},'heldout':{k:'lanl.cpu.'+k+'.t1.heldout-band.v1' for k in ('bfs','bc')},'summary':{'source_commit':C},'run':run,'artifacts':artifacts}
 exec(compile(ast.Module(body=[copy.deepcopy(body)],type_ignores=[]),'model-mock','exec'),env)
 model=env['summary'];assert model['ready_for_development'];assert len(frozen_requests)==2;assert model['protocols']['bfs']['id']!=model['protocols']['bc']['id']
 assert frozen_requests[0]['settings']['target_description']==frozen_requests[1]['settings']['target_description']==target
 assert all(req['settings']['input_run_arguments']['kron-g16-k16']==records[chars[req['id'].split('.')[2],16]]['source']['run_arguments'] for req in frozen_requests)
 _common([records[rid] for rid in estimates.values()])
 model['identity_sha256']=artifacts.digest(model);model_path=root/'model-acceptance.json';model_path.write_text(json.dumps(model))
 class RewritePath(ast.NodeTransformer):
  def visit_Constant(self,n):
   if n.value=='/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3/acceptance.json':return ast.copy_location(ast.Constant(str(model_path)),n)
   return n
 mocked=ast.fix_missing_locations(RewritePath().visit(copy.deepcopy(body)))
 phase_results=[]
 for phase in ('development','holdout'):
  start=len(calls);env.update(phase=phase,summary={'source_commit':C},protocols={});exec(compile(ast.Module(body=[copy.deepcopy(mocked)],type_ignores=[]),phase+'-mock','exec'),env)
  collected=[row for row in calls[start:] if row[0].startswith('collect-')];assert len(collected)==2
  assert all(row[2]==2100 and row[1][row[1].index('--max-wall-s')+1]=='900' for row in collected)
  assert env['summary']['protocols']==model['protocols']
  assert set(env['summary']['bands'])=={'bfs','bc'}
  phase_results.append({'phase':phase,'native_commands_mocked':2,'protocol_ids_preserved':True})
 original=copy.deepcopy(records[estimates['bfs',16]]);records[estimates['bfs',16]]['seconds']=2.0
 before=len(calls);env.update(phase='development',summary={'source_commit':C},protocols={})
 try:exec(compile(ast.Module(body=[copy.deepcopy(mocked)],type_ignores=[]),'tamper-mock','exec'),env)
 except AssertionError:pass
 else:raise AssertionError('changed model estimate was accepted')
 assert len(calls)==before;records[estimates['bfs',16]]=original
 proof={'format':'swdb.cpu-dispatch-helper-mocked-proof.v1','scope':'Local syntax/AST and mocked command/ID/argv/lineage checks only; no remote dispatch, compiler invocation or application execution.','external_helper_sha256':artifacts.file_hash(Path('/private/tmp/lanl-dispatch-cpu-model-validation-a3.py')),'runner_syntax_phases':['model','development','holdout'],'model_freeze_commands_mocked':2,'model_estimate_commands_mocked':4,'per_kernel_exact_input_argv':True,'captured_content_suffixed_ids':True,'same_target_bundle_calibrations':True,'band_common_identity_guard_passed':True,'later_phases':phase_results,'changed_prior_model_estimate_refused_before_native_commands':True,'caps_preserved':{'runner_s':10000,'outer_s':10300,'native_inner_s':900,'native_child_cap_s':2100,'public_s':1400},'public_dispatch_phases':['development','holdout'],'dispatch_started':False}
 proof['identity_sha256']=artifacts.digest(proof);Path('/private/tmp/lanl-cpu-model-dispatch-a3-mocked-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
