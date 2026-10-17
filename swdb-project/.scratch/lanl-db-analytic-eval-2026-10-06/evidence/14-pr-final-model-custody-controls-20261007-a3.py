import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

runner=Path('/private/tmp/lanl14-pr-final-local-runner-20261007-a3.py')
spec=importlib.util.spec_from_file_location('local_runner',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sealed(value):value['identity_sha256']=digest({k:v for k,v in value.items() if k!='identity_sha256'});return value
class FixtureStore:
 def __init__(self,data,paths):self.data=data;self.paths=paths
 def get(self,rid,kind=None):
  value=self.data.get(rid);return value if value is not None and (kind is None or value['kind']==kind) else None
 def path_of(self,rid):return self.paths[rid]
with tempfile.TemporaryDirectory(prefix='lanl14-model-custody-controls-',dir='/private/tmp') as temp:
 records=Path(temp)/'records';records.mkdir();data={};paths={};pins=[]
 target={'id':m.TARGET,'kind':'target_description'};target_sha=digest(target);data[m.TARGET]=target
 protocols={}
 for kernel in ('bfs','bc'):
  rid=f'fixture.{kernel}.protocol';protocol={'id':rid,'kind':'protocol','settings':{'estimator_sha256':m.BUNDLE,'target_description':{'sha256':target_sha}}};data[rid]=protocol;protocols[kernel]={'id':rid,'sha256':digest(protocol)}
 rows=[]
 for kernel in ('bfs','bc'):
  for scale in (16,17):
   char=f'{kernel}.kron-g{scale}.t1.characterization.objects.a1';data[char]={'id':char,'kind':'workload_characterization'}
   rid=f'lanl.cpu.{kernel}.g{scale}.t1.estimate.v1';estimate={'id':rid,'kind':'estimate','seconds':1.0,'evidence_kind':'execution','estimator_sha256':m.BUNDLE,'target_description_sha256':target_sha,'characterization':char,'characterization_sha256':digest(data[char]),'protocol':protocols[kernel]['id']};data[rid]=estimate
   rows.append({key:estimate[key] for key in ('id','seconds','evidence_kind','estimator_sha256','target_description_sha256','characterization_sha256','protocol')}|{'sha256':digest(estimate)})
 for rid,value in data.items():
  rel=rid+'.yaml';path=records/rel;path.write_text(json.dumps(value)+'\n');paths[rid]=rel
  if value['kind']!='workload_characterization':pins.append({'id':rid,'kind':value['kind'],'path':rel,'sha256':digest(value),'file_sha256':m.sha(path),'bytes':path.stat().st_size})
 store=FixtureStore(data,paths)
 acceptance=sealed({'source_commit':m.MODEL_C,'phase':'model','source_clean':True,'raw_transferred':False,'application_performance_timings_collected':False,'ready_for_development':True,'target_sha256':target_sha,'validation':'OK: fixture records valid','estimates':rows,'protocols':protocols,'prior_record_bytes_preserved':665})
 receipt=sealed({'format':'swdb.prospective-native-model-compact-receipt.v1','phase':'model','source_commit':m.MODEL_C,'source_clean':True,'raw_transferred':False,'acceptance':acceptance,'lane':{'exit_code':0,'ended_utc':'fixture','node':0,'numa_memory_policy':'bind:0'},'new_records':pins,'prior_records_preserved':665})
 def check(value):return m.validate_model_receipt(value,store=store,records=records,target_sha256=target_sha,digest=digest,file_hash=m.sha)
 results=[];assert len(check(receipt)['verified_new_records'])==7;results.append('positive independent metadata fixture')
 def refusal(name,mutate,re_nested=False,re_outer=True):
  value=copy.deepcopy(receipt);mutate(value)
  if re_nested:sealed(value['acceptance'])
  if re_outer:sealed(value)
  try:check(value)
  except (ValueError,KeyError,TypeError):results.append(name);return
  raise AssertionError(name+' incorrectly accepted')
 refusal('outer receipt seal',lambda v:v.update(source_clean=False),re_outer=False)
 refusal('nested acceptance seal',lambda v:v['acceptance'].update(ready_for_development=False))
 refusal('source C identity',lambda v:v.update(source_commit='0'*40))
 refusal('nonmodel phase',lambda v:v.update(phase='development'))
 refusal('application timings',lambda v:v['acceptance'].update(application_performance_timings_collected=True),True)
 refusal('readiness false',lambda v:v['acceptance'].update(ready_for_development=False),True)
 refusal('missing exported record',lambda v:v['new_records'].pop())
 refusal('changed exported file pin',lambda v:v['new_records'][0].update(file_sha256='0'*64))
 refusal('escaping source path',lambda v:v['new_records'][0].update(path='../escape.yaml'))
 refusal('nonpositive estimate',lambda v:v['acceptance']['estimates'][0].update(seconds=0),True)
 refusal('nonexecution estimate',lambda v:v['acceptance']['estimates'][0].update(evidence_kind='contract_fixture'),True)
 refusal('changed F6 bundle',lambda v:v['acceptance']['estimates'][0].update(estimator_sha256='0'*64),True)
 refusal('different real target',lambda v:v['acceptance'].update(target_sha256='0'*64),True)
 refusal('changed semantic source pin',lambda v:v['new_records'][0].update(sha256='0'*64))
 refusal('duplicated estimate admission',lambda v:v['acceptance']['estimates'].__setitem__(1,v['acceptance']['estimates'][0]),True)
 refusal('failed lane',lambda v:v['lane'].update(exit_code=1))
 first=records/pins[0]['path'];original=first.read_bytes();first.write_bytes(original+b' ')
 try:check(receipt)
 except ValueError:results.append('actual exported file tamper')
 else:raise AssertionError('tampered file accepted')
 finally:first.write_bytes(original)
 assert check(receipt)['ready_for_development'] is True
 proof={'format':'swdb.lanl14-local-model-custody-controls.v1','updated':'2026-10-07 ET','scope':'Independent metadata/file fixture only; no actual target/model acceptance, provider/native/compiler/remote execution.','runner_sha256':m.sha(runner),'controls':results,'passed':len(results),'actual_execution':False}
 proof['identity_sha256']=digest(proof);out=Path('/private/tmp/lanl14-pr-final-model-custody-controls-proof-20261007-a3.json');out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'passed':len(results),'proof':str(out),'runner_sha256':proof['runner_sha256'],'identity_sha256':proof['identity_sha256']}))
