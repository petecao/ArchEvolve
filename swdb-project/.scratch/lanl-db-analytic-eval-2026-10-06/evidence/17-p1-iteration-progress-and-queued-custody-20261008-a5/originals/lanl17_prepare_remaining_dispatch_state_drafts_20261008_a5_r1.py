"""Local source-only JSON derivation; no scientific/control imports or execution."""
import copy, datetime, hashlib, json, os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path('/private/tmp')
REQUEST=ROOT/'lanl17-p1-dispatch-state-request-20261008-a5.json'
ACTION=ROOT/'lanl17-p1-dispatch-state-config-20261008-a5.json'
RESUME=Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/resume.md')
MAX_BYTES=33554432
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def future(name,kind,**bounds):return {'required_future_input':name,'type':kind,**bounds}
def publish(p,value):
 b=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(b)
 return {'path':str(p),'bytes':len(b),'sha256':sha(b),'mode':'0600'}
def differences(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  result=[]
  for k in sorted(set(a)|set(b)):
   q=path+'/'+k
   if k not in a or k not in b:result.append(q)
   else:result.extend(differences(a[k],b[k],q))
  return result
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
  return sum((differences(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [path]

request=json.loads(REQUEST.read_bytes());action=json.loads(ACTION.read_bytes())
assert pin(REQUEST)=={'path':str(REQUEST),'bytes':5584,'sha256':'b5198085b8da79dbdf311cdaffcf2bc733904bb85799c5d8ed8b950310cc3eb2'}
assert pin(ACTION)=={'path':str(ACTION),'bytes':8377,'sha256':'e0d57c3782643ff9b9fb4e4566103d737fbfe05aec9a6ef046f66c6275e76b10'}
assert set(request)=={'format','producer_sha256','source_plan_sha256','auditor_sha256','collector_sha256','capture','context','observations','inputs','read_roots','identity_sha256'}
assert request['capture']=='dispatch_state'
assert set(request['inputs'])=={'manifest_M2','before_custody','dispatch'}
assert set(request['observations'])=={'basis','state_unchanged_under_parent_exclusive_campaign_ownership','parent_checked_pre_dispatch_state_sha256','checked_utc'}
date=datetime.datetime.now(ZoneInfo('America/Detroit')).isoformat()
fixed_first={'path':'/data/yanruj/EvolveSWDB_runs/lanl17-first-publication-custody-20261008-a5.json','bytes':7701,'sha256':'e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1','basis':'Already retained original FIRST; future b08 BEFORE must bind it; no new publication observation.'}
rows=[]
expected_paths={
 '/context/campaign','/inputs/before_custody/path','/inputs/before_custody/bytes',
 '/inputs/before_custody/sha256','/inputs/before_custody/identity_sha256',
 '/inputs/dispatch/path','/inputs/dispatch/bytes','/inputs/dispatch/sha256',
 '/inputs/dispatch/identity_sha256','/read_roots/2','/identity_sha256',
 '/observations/state_unchanged_under_parent_exclusive_campaign_ownership',
 '/observations/parent_checked_pre_dispatch_state_sha256','/observations/checked_utc'}
for number in (2,3,4):
 label='p'+str(number);cid='extensa-gem5-bfs-20261006-'+label
 t=copy.deepcopy(request);t['context']['campaign']=cid
 t['inputs']['before_custody']['path']=request['inputs']['before_custody']['path'].replace('lanl17-p1-before-','lanl17-'+label+'-before-')
 t['inputs']['dispatch']['path']=request['inputs']['dispatch']['path'].replace('extensa-gem5-bfs-20261006-p1/attempt-1/','extensa-gem5-bfs-20261006-'+label+'/attempt-1/')
 for role in ('before_custody','dispatch'):
  for field in ('bytes','sha256','identity_sha256'):
   t['inputs'][role][field]=future('actual_'+label+'.'+role+'.'+field,'integer' if field=='bytes' else 'sha256',**({'min':1,'max':MAX_BYTES} if field=='bytes' else {}))
 t['read_roots'][2]=request['read_roots'][2].replace('lanl17-p1-before-','lanl17-'+label+'-before-')
 t['observations']['state_unchanged_under_parent_exclusive_campaign_ownership']=future('actual_'+label+'.state_unchanged_under_parent_exclusive_campaign_ownership','boolean',basis='Explicit fresh parent observation; never copied from p1.')
 t['observations']['parent_checked_pre_dispatch_state_sha256']=future('actual_'+label+'.parent_checked_pre_dispatch_state_sha256','sha256_or_null',basis='Null only for actually observed absent state; otherwise exact original BEFORE state file SHA.')
 t['observations']['checked_utc']=future('actual_'+label+'.dispatch_state_observation_checked_utc','UTC_timestamp',not_before='Actual matching dispatch.checked_utc; actual BEFORE.checked_utc <= dispatch.checked_utc <= this observation.')
 t['identity_sha256']=future('finalized_'+label+'_dispatch_state_request.identity_sha256','sha256',compute_after_all_originals='Sorted compact JSON ensure_ascii=True/allow_nan=False of exact finalized request excluding identity_sha256.')
 assert set(differences(request,t))==expected_paths
 assert t['inputs']['manifest_M2']==request['inputs']['manifest_M2']
 assert {k:v for k,v in t['context'].items() if k!='campaign'}=={k:v for k,v in request['context'].items() if k!='campaign'}
 for role in ('before_custody','dispatch'):
  for field in ('encoding','sealed','writer_source','canonical_ensure_ascii','canonical_policy_sources'):
   assert t['inputs'][role][field]==request['inputs'][role][field]
 wrapper={'format':'swdb.lanl17-dispatch-state-request-source-only-draft.v1',
  'prepared_ET':date,'executable':False,'source_only':True,'scientific_admission':False,
  'derived_from':pin(REQUEST),'fixed_publication_reference':fixed_first,
  'planned_target':{'campaign':cid,'attempt':1,'basis':'Prospective first-attempt routing only; no observed attempt/state/session existence.'},
  'native_lane_generation_or_provider_call_state':'No node, acquired generation, call state or terminal outcome is carried. All actual dispatch admission remains separate.',
  'request_template':t}
 rp=publish(ROOT/('lanl17-'+label+'-dispatch-state-request-draft-r1-20261008-a5.json'),wrapper)
 c=copy.deepcopy(action)
 request_index=c['argv'].index('--request')+1
 request_sha_index=c['argv'].index('--request-sha256')+1
 output_index=c['argv'].index('--output')+1
 c['argv'][request_index]=c['argv'][request_index].replace('lanl17-p1-dispatch-state-request-','lanl17-'+label+'-dispatch-state-request-')
 c['argv'][request_sha_index]=future('finalized_'+label+'_dispatch_state_request.file_sha256','sha256')
 c['argv'][output_index]=c['argv'][output_index].replace('lanl17-p1-dispatch-state-custody-','lanl17-'+label+'-dispatch-state-custody-')
 c['collect']=[c['argv'][output_index]]
 c['stage']=[{'path':c['argv'][request_index],
  'bytes':future('finalized_'+label+'_dispatch_state_request.bytes','integer',min=1,max=MAX_BYTES),
  'sha256':future('finalized_'+label+'_dispatch_state_request.file_sha256','sha256'),
  'base64':future('finalized_'+label+'_dispatch_state_request.exact_base64','base64')}]
 assert c['source_pins']==action['source_pins'] and c['remote_seconds']==300 and c['local_seconds']==420
 ap=publish(ROOT/('lanl17-'+label+'-dispatch-state-action-config-draft-r1-20261008-a5.json'),
  {'format':'swdb.lanl17-dispatch-state-action-source-only-draft.v1','prepared_ET':date,
   'executable':False,'source_only':True,'scientific_admission':False,'derived_from':pin(ACTION),'config_template':c})
 rows.append({'campaign':cid,'request_draft':rp,'action_draft':ap,'exact_changed_request_paths':sorted(expected_paths),
  'manifest_context_controls_writer_and_canonical_policy_exactly_preserved':True,
  'p1_before_dispatch_or_request_identity_pins_invalidated':True,'parent_current_observations_invalidated':True,
  'p1_request_base64_and_file_pins_not_carried':True,'node_or_future_generation_not_assumed':True})

review={'format':'swdb.lanl17-remaining-dispatch-state-source-derivation-review.v1',
 'prepared_ET':date,'source_only':True,'drafts_executable':False,'scientific_admission':False,
 'original_request':pin(REQUEST),'original_action':pin(ACTION),'resume_read':pin(RESUME),
 'producer_source_reviewed':pin(Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-future-input-controls-20261007-a3/lanl17_parent_capture_projection_producer_a3_20261007.py')),
 'request_exact_original_top_keys_and_dispatch_state_observation_keys_preserved':True,
 'exact_three_input_names_and_original_descriptor_key_sets_preserved':True,
 'actual_request_seal_base64_and_original_file_hashes_remain_future':True,
 'full_catalogs_policy_budgets_source_and_limits_changed':False,
 'scientific_or_remote_or_control_execution_tests_imports':False,'drafts':rows,
 'initial_local_derivation_failure':{'state':'preserved_unsealed_local_draft_only','exception':'IndexError','cause':'Wrong positional action argv index; corrected to flag-based value lookup','source':'/private/tmp/lanl17_prepare_remaining_dispatch_state_drafts_20261008_a5.py','partial_request_draft':'/private/tmp/lanl17-p2-dispatch-state-request-draft-20261008-a5.json','remote_or_scientific_action_executed':False}}
review_pin=publish(ROOT/'lanl17-p234-dispatch-state-source-derivation-review-r1-20261008-a5.json',review)
print(json.dumps({'drafts':rows,'review':review_pin,'created_local_source_only':True},indent=2))
