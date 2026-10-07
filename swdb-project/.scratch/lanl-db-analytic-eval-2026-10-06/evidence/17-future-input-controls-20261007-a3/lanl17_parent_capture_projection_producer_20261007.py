#!/usr/bin/env python3
"""PROSPECTIVE parent capture writer, 2026-10-07 ET; not executed.

One explicit SHA-bound request creates one separately sealed parent projection.
Original public/control/index/status bytes are read only and never normalized.
No SWDB, Store, auditor, collector, Git, SSH, native or provider import/command.
This producer does not discover observations or prove substantive trajectories.
Its NEW whole-object seals use ensure_ascii=True explicitly. Original input
writers' policies are required independently; unsealed inputs stay unsealed.
Only the original eight capture formats specified by the approved e342 plan
are emitted. Missing explicit observations/selected original bodies refuse.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import socket
import sys
import yaml
sys.dont_write_bytecode=True

C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
AUDITOR='6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
COLLECTOR='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
HELPER='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
PLAN='e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170'
CAMPAIGN_SOURCE='13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d'
SEARCH_SOURCE='348b07b38a7955a65b5c13629dd8234453609f152a78d27524df6bf840a989e7'
TARGET_SOURCE='727d4399e4bde1996484e3013770e5ab21ef4a30e8fa7313c4697aaa6359211f'
CAPTURES={
 'publication':'swdb.lanl17-freeze-publication-custody.v1',
 'dispatch_state':'swdb.lanl17-dispatch-state-corroboration.v1',
 'release':'swdb.lanl17-attempt-release-custody.v1',
 'unclean_resume':'swdb.lanl17-unclean-resume-admission.v1',
 'refusal':'swdb.lanl17-outcome-refusal-custody.v1',
 'interrupted_bodies':'swdb.lanl17-interrupted-selected-bodies.v1',
 'candidate_selection':'swdb.lanl17-original-public-candidate-selection-custody.v1',
 'trajectory':'swdb.lanl17-trajectory-audit-projection.v2'}
MAX_BYTES=32*1024*1024

class Refused(ValueError):pass
def require(ok,why):
 if not ok:raise Refused(why)
def need(value,key):
 require(key in value,'Required explicit observation/input missing: '+key);return value[key]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(value,*,ensure_ascii=True):
 return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=ensure_ascii,allow_nan=False).encode())
def strict_json(raw):
 def pairs(rows):
  result={}
  for k,v in rows:require(k not in result,'Duplicate JSON key');result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=pairs)
def utc(value):
 d=datetime.datetime.fromisoformat(value);require(d.tzinfo is not None and d.utcoffset().total_seconds()==0,'Explicit UTC observation required');return d
def safe_code(value):
 require(isinstance(value,str) and re.fullmatch('[a-z0-9_.-]+',value),'Closed source reason code required');return value
def token(value):
 require(isinstance(value,str) and len(value)<=256 and re.fullmatch('[A-Za-z0-9_.:/+-]+',value),'Bounded public scalar token required');return value
def hex64(value):require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value),'Exact SHA-256 required');return value
def fields(value,keys):
 require(set(value)==set(keys),'Explicit observation field set differs; no defaults or extra prose accepted');return dict(value)
def regular(path):
 p=Path(path);require(p.is_absolute() and '..' not in p.parts and all(not v.is_symlink() for v in (p,*p.parents)),'Absolute regular path without symlink components required')
 require(p.is_file() and p.stat().st_uid==os.getuid(),'Original/capture source must be an existing own-UID regular file');return p
def hash_file(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

# Exact public safe projection vocabulary/functions are inserted by the
# source-only preparation builder below this marker; no original module runs.
class RecordLoader(getattr(yaml,'CSafeLoader',yaml.SafeLoader)): pass


RecordLoader.yaml_implicit_resolvers={first:[(tag,regexp) for tag,regexp in rows if tag!='tag:yaml.org,2002:timestamp'] for first,rows in RecordLoader.yaml_implicit_resolvers.items()}


def no_duplicates(loader,node,deep=False):
    seen=set()
    for key_node,_ in node.value:
        key=loader.construct_object(key_node,deep=deep)
        if key in seen: raise Refused('Duplicate YAML mapping key')
        seen.add(key)
    return loader.construct_mapping(node,deep=deep)


RecordLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,no_duplicates)


CALL_KEYS=('role','invocation','outcome','counted','model','effort')


CANDIDATE_KEYS=('id','class','artifact_sha256','patch_sha256','level')


STATE_KEYS=('campaign','campaign_sha256','started','stopped','stop_reason','clean_exit','setup_done','resumes','lane_hours','provider_wait_hours','disk_bytes_peak')


PROJECTION_CONTRACT='swdb.lanl17-safe-control-projection.v1'


def public_token(value,nullable=False):
    if value is None and nullable:return None
    require(isinstance(value,str) and len(value)<=256 and re.fullmatch('[A-Za-z0-9_.:/+-]+',value),'bounded public scalar token required')
    return value


def public_scalar(value):
    require(value is None or type(value) in (int,float,bool,str),'public scalar required')
    if isinstance(value,str):return public_token(value)
    if type(value) is float:require(value==value and abs(value)!=float('inf'),'finite public scalar required')
    return value


def public_fields(row,keys):
    require(isinstance(row,dict),'public field mapping required')
    return {k:public_scalar(row[k]) for k in keys if k in row}


def excluded_fields(row,keys):
    # Hash the entire excluded values; do not copy their nested content or text.
    return {k:{'json_type':type(row[k]).__name__,'semantic_sha256':digest(row[k]),'values_exported':False} for k in keys if k in row}


def project_calls(rows):
    require(isinstance(rows,list) and len(rows)<=500,'bounded public call rows required')
    return [{**public_fields(r,CALL_KEYS),'excluded_metadata':excluded_fields(r,('classification',))} for r in rows]


def project_candidate(row):
    result=public_fields(row,CANDIDATE_KEYS)
    result['excluded_provider_values']=excluded_fields(row,('knobs','contracts'))
    certification=row.get('certification')
    result['certification']=None if certification is None else {
        **public_fields(certification,('record','outcome','level_at_summary')),
        'excluded_metadata':excluded_fields(certification,('failed_checks',))}
    comparisons=row.get('comparisons',[])
    require(isinstance(comparisons,list) and len(comparisons)<=32,'bounded comparison rows required')
    result['comparisons']=[{**public_fields(r,('baseline_role','comparison','baseline_evaluation','ratio','lower','upper','relative_ci_width','spread','verdict')),'excluded_metadata':excluded_fields(r,('level_mix',))} for r in comparisons]
    selection=row.get('selection')
    result['selection']=None if selection is None else public_fields(selection,('lower','verdict','ratio'))
    return result


def project_iteration(row):
    result=public_fields(row,('index','started','ended'))
    improved=row.get('improved_classes',[])
    require(isinstance(improved,list) and len(improved)<=32,'bounded improved class IDs required')
    result.update(improved_classes=[public_token(x) for x in improved],provider_calls=project_calls(row.get('provider_calls',[])),
        candidates=[project_candidate(r) for r in row.get('candidates',[])],source_row_sha256=digest(row))
    return result


def project_state(state):
    result=public_fields(state,STATE_KEYS)
    result['projection_contract']=PROJECTION_CONTRACT
    result['ledger']={k:state['ledger'][k] for k in ('iteration','iterations_completed','plateau','calls','iterations','terminal','iteration_calls','setup_calls')}
    result['ledger']['calls']=[public_fields(r,('index','iteration','role','invocation','outcome','counted')) for r in state['ledger']['calls']]
    result['ledger']['iterations']=[public_fields(r,('index','outcome','advanced_plateau','plateau_counter')) for r in state['ledger']['iterations']]
    require(result['ledger']==state['ledger'],'unexpected private/unknown ledger field')
    result['ledger_sha256']=digest(state['ledger'])
    result['iterations']=[project_iteration(r) for r in state['iterations']]
    result['setup_calls']=project_calls(state.get('setup_calls',[]))
    result['pauses']=[{**public_fields(r,('at','resumed_at','iteration')),
        'reason':safe_code(r['reason']),'provider_calls':project_calls(r.get('provider_calls',[])),
        'source_row_sha256':digest(r)} for r in state['pauses']]
    if state.get('interrupted_iteration'):result['interrupted_iteration']=project_iteration(state['interrupted_iteration'])
    result['prepared']=[public_token(x) for x in state.get('prepared',[])]
    result['preflights']=[public_fields(r,('step','state')) for r in state.get('preflights',[])]
    result['baselines']={public_token(k):public_token(v) for k,v in state.get('baselines',{}).items()}
    result['protocol_id']=public_token(state.get('protocol',{}).get('id'),nullable=True)
    result['protocol_identity_sha256']=public_token(state.get('protocol',{}).get('identity_sha256'),nullable=True)
    result['stop_detail_sha256']=digest(state.get('stop_detail'))
    result['source_state_semantic_sha256']=digest(state)
    return result


class Inputs:
 def __init__(self,spec):self.spec=spec;self.pins={};self.data={}
 def read(self,name):
  if name in self.data:return self.data[name]
  pin=need(self.spec['inputs'],name);p=regular(need(pin,'path'))
  require(any(p.is_relative_to(Path(r)) for r in self.spec['read_roots']),'Original input leaves explicit approved read roots')
  forbidden={'.codex','.ssh','.aws','auth.json','provider.json','prompt.txt','feedback.txt'}
  require(not forbidden.intersection(p.parts),'Credential/provider/prompt/feedback source is outside capture scope')
  size=need(pin,'bytes');require(type(size)is int and 0<=size<=MAX_BYTES and p.stat().st_size==size,'Original bounded byte count differs')
  require(hash_file(p)==hex64(need(pin,'sha256')),'Original input file SHA differs')
  encoding=need(pin,'encoding');sealed=need(pin,'sealed');require(type(sealed)is bool,'Explicit original sealed/unsealed classification required')
  require(encoding in {'json','yaml','integer_exit','hash_only'},'Unsupported original input encoding')
  if sealed:
   require(encoding=='json' and type(need(pin,'canonical_ensure_ascii'))is bool,'Original compact writer canonical policy required')
   hex64(need(pin,'identity_sha256'))
  else:require('identity_sha256' not in pin and 'canonical_ensure_ascii' not in pin,'Unsealed originals cannot acquire invented seal fields')
  # The actual writer source must be a separately pinned original file, not a
  # guessed policy from the output suffix. It is hashed, never imported/run.
  writer=need(pin,'writer_source');wp=regular(need(writer,'path'))
  require(any(wp.is_relative_to(Path(r)) for r in self.spec['read_roots']) and not forbidden.intersection(wp.parts),'Original writer leaves approved roots/privacy scope')
  require(wp.stat().st_size==need(writer,'bytes') and hash_file(wp)==hex64(need(writer,'sha256')),'Pinned original writer source differs')
  if encoding=='hash_only':value=None
  else:
   raw=p.read_bytes()
   if encoding=='json':value=strict_json(raw)
   elif encoding=='yaml':value=yaml.load(raw,Loader=RecordLoader)
   else:require(len(raw)<=64 and re.fullmatch(rb'-?[0-9]+\s*',raw),'Original exit file is not an integer');value=int(raw)
  if sealed:require(value['identity_sha256']==pin['identity_sha256']==digest({k:v for k,v in value.items() if k!='identity_sha256'},ensure_ascii=pin['canonical_ensure_ascii']),'Original compact seal differs')
  self.pins[name]=dict(pin);self.data[name]=value;return value
 def compact(self,name,format):
  value=self.read(name);require(self.spec['inputs'][name]['sealed'] is True and value['format']==format,'Exact original compact input required: '+name);return value
 def original(self,name,encoding):
  value=self.read(name);require(self.spec['inputs'][name]['sealed'] is False and self.spec['inputs'][name]['encoding']==encoding,'Original unsealed '+encoding+' input required: '+name);return value
 def recheck(self):
  for pin in self.pins.values():
   require(hash_file(regular(pin['path']))==pin['sha256'],'Original changed during capture')
   w=pin['writer_source'];require(hash_file(regular(w['path']))==w['sha256'],'Original writer changed during capture')

def collector(inputs,name,phase,context):
 value=inputs.compact(name,'swdb.lanl17-attempt-control-custody.v2')
 require(value['phase']==phase and value['collector_sha256']==COLLECTOR and value['helper_sha256']==HELPER and value['estimator_sha256']==F6 and value['source_commit']==context['source_commit'],'Original reviewed collector/source differs')
 require(value['manifest_identity_sha256']==context['manifest_identity_sha256'] and value['projection_contract']=='swdb.lanl17-safe-control-projection.v1','Collector M2/vocabulary differs')
 require(value['policy']==context['policy'],'Original collector frozen policy differs')
 require(value['raw_state_snapshots_transferred'] is False and value['provider_prompts_auth_logs_argv_read'] is False,'Private original values cannot be transferred')
 require(value['execution_account']['uid']==context['account']['uid'] and value['execution_account']['user']==context['account']['user'],'Original actual collector account differs')
 require(value['execution_account']['host']=='mbit10' and value['execution_account']['platform']=='linux' and value['execution_account']['effective_uid']==context['account']['uid'] and value['actual_git_worktree_root']==context['source_path'] and value['actual_project_directory']==str(Path(context['source_path'])/'swdb-project'),'Original collector execution account/source path differs')
 return value
def summary(inputs,context):
 value=inputs.original('summary','yaml');require(value['kind']=='campaign_summary' and value['campaign']==context['campaign'] and value['mode']=='extensa' and value['swdb_commit']==context['source_commit'],'Exact original public summary/source differs');return value
def record_index(inputs):
 value=inputs.original('record_index','json');require(isinstance(value,dict),'Original full record index required')
 for rid,row in value.items():token(rid);require(set(row)=={'kind','sha256','record_sha256'},'Exact bounded public index fields required; extra original fields need a separately reviewed producer');token(row['kind']);hex64(row['sha256']);hex64(row['record_sha256'])
 return value
def selected_records(inputs,index):
 result={}
 for name in sorted(inputs.spec['inputs']):
  if not name.startswith('selected_record:'):continue
  value=inputs.original(name,'yaml');rid=value['id'];require(rid not in result and rid in index,'Original selected body absent/duplicated in validated index')
  row=index[rid];pin=inputs.spec['inputs'][name]
  require(value['kind']==row['kind'] and pin['sha256']==row['sha256'] and digest(value)==row['record_sha256'],'Original selected body file/public identity differs')
  result[rid]=value
 return result
def closure(roots,index,bodies):
 def refs(value):
  if isinstance(value,str):return {value} if value in index else set()
  if isinstance(value,dict):return set().union(*(refs(v) for v in value.values())) if value else set()
  if isinstance(value,list):return set().union(*(refs(v) for v in value)) if value else set()
  return set()
 reached=set();pending=list(roots)
 while pending:
  rid=pending.pop()
  if rid in reached:continue
  require(rid in index and rid in bodies,'Required exact original selected closure body missing: '+rid)
  reached.add(rid);pending.extend(refs({k:v for k,v in bodies[rid].items() if k not in {'id','kind'}})-reached)
 return reached

def build(kind,ctx,observations,inputs):
 R=ctx['source_commit'];o=observations;body={'format':CAPTURES[kind]}
 if kind=='publication':
  o=fields(o,('freeze_export_commit','completed_export_exit_code','application_outcomes_opened','frozen_live_files_verified','checked_utc'))
  m2=inputs.compact('manifest_M2','swdb.lanl17-parent-population.v1');prepare=inputs.compact('prepare_supervisor','swdb.lanl17-metadata-supervisor.v1')
  freeze=inputs.compact('freeze_receipt','swdb.lanl17-freeze-receipt.v1');policy=inputs.original('policy','yaml')
  require(m2['source_commit']==freeze['manifest']['source_commit']==R and m2['source']==ctx['source_path'] and m2['identity_sha256']==ctx['manifest_identity_sha256'] and policy['identity_sha256']==m2['policy']['identity_sha256'],'Original M2/freeze/policy source differs')
  require(m2['helper_sha256']==HELPER and m2['estimator_sha256']==F6 and m2['source_clean'] is True and m2['policy']==ctx['policy'],'Original M2/control/source/policy differs')
  m1=freeze['manifest'];require(m1['identity_sha256']==digest({k:v for k,v in m1.items() if k!='identity_sha256'}) and {k:v for k,v in m2.items() if k not in {'identity_sha256','freeze_export'}}=={k:v for k,v in m1.items() if k!='identity_sha256'},'Original M2 is not byte-sealed M1 plus original freeze export')
  require(o['freeze_export_commit']==m2['freeze_export']['commit'] and freeze['public_policy']==policy and freeze['population_frozen'] is True and freeze['application_outcomes_opened']==0,'Original freeze/policy/publication export binding differs')
  require(prepare['action']=='prepare' and prepare['state']=='child_returned' and prepare['child_exit']==prepare['supervisor_exit']==0 and prepare['fixture'] is False,'Original actual prepare did not succeed')
  require(re.fullmatch('[0-9a-f]{40}',o['freeze_export_commit']) and type(o['completed_export_exit_code'])is int and type(o['application_outcomes_opened'])is int and o['application_outcomes_opened']>=0 and type(o['frozen_live_files_verified'])is bool,'Explicit original publication observations missing')
  require(utc(o['checked_utc'])>=utc(prepare['ended_utc']),'Publication checked before actual prepare completion')
  body.update(o,source_commit=R,manifest_sha256=m2['identity_sha256'],policy_sha256=policy['identity_sha256'],prepare_supervisor_identity=prepare['identity_sha256'],input_model_baseline_pins_sha256=digest(m2['input_model_baseline_pins']))
 elif kind=='dispatch_state':
  o=fields(o,('basis','state_unchanged_under_parent_exclusive_campaign_ownership','parent_checked_pre_dispatch_state_sha256','checked_utc'))
  before=collector(inputs,'before_custody','before',ctx);dispatch=inputs.compact('dispatch','swdb.lanl17-campaign-dispatch.v1')
  require(o['basis']=='explicit_parent_attestation_no_other_campaign_writer_between_capture_and_dispatch' and type(o['state_unchanged_under_parent_exclusive_campaign_ownership'])is bool,'Explicit ownership/time-of-check observation missing')
  expected=before['state']['file']['sha256'] if before['state']['present'] else None;require(o['parent_checked_pre_dispatch_state_sha256']==expected,'Actual checked state hash/absence differs')
  require(before['campaign']==dispatch['campaign']==ctx['campaign'] and before['attempt']==dispatch['attempt']==ctx['attempt'] and dispatch['source_commit']==R,'Original dispatch/state identity differs')
  require(dispatch['manifest_sha256']==ctx['manifest_identity_sha256'] and dispatch['policy']==ctx['policy'],'Original dispatch frozen policy differs')
  utc(o['checked_utc']);body.update(o,source_commit=R,campaign=ctx['campaign'],attempt=ctx['attempt'],before_identity_sha256=before['identity_sha256'],dispatch_identity_sha256=dispatch['identity_sha256'])
 elif kind=='release':
  o=fields(o,('lease_released','lease_generation','checked_utc'))
  dispatch=inputs.compact('dispatch','swdb.lanl17-campaign-dispatch.v1');stop=inputs.compact('stopped','swdb.lanl17-stopped-attempt.v1')
  wrapper=inputs.original('wrapper_exit','integer_exit');runner=inputs.original('runner_exit','integer_exit');inputs.original('lane','hash_only');inputs.original('authoritative_lease_observation','hash_only')
  require(dispatch['campaign']==stop['campaign']==ctx['campaign'] and dispatch['attempt']==ctx['attempt'] and dispatch['source_commit']==stop['source_commit']==R and stop['dispatch_sha256']==dispatch['identity_sha256'],'Original attempt bindings differ')
  require(dispatch['manifest_sha256']==stop['manifest_sha256']==ctx['manifest_identity_sha256'] and dispatch['policy']==stop['policy']==ctx['policy'],'Original attempt M2/policy differs')
  require(runner==stop['runner_exit_code'] and type(stop['public_exit_code'])is int and dispatch['node'] in (0,1) and type(o['lease_released'])is bool and type(o['lease_generation'])is int and o['lease_generation']>=0,'Explicit original exits/release observation missing')
  require(utc(o['checked_utc'])>=utc(stop['ended_utc']),'Release observation precedes original stop')
  body.update(o,source_commit=R,campaign=ctx['campaign'],attempt=ctx['attempt'],dispatch_identity=dispatch['identity_sha256'],stopped_identity=stop['identity_sha256'],node=dispatch['node'],runner_exit_code=runner,public_exit_code=stop['public_exit_code'],wrapper_exit_code=wrapper,lane_record_sha256=inputs.pins['lane']['sha256'],wrapper_exit_file_sha256=inputs.pins['wrapper_exit']['sha256'])
 elif kind=='unclean_resume':
  o=fields(o,('basis','accepted','unaccounted_opened_calls','scientific_source_or_state_changed','checked_utc'))
  prior=collector(inputs,'prior_after_custody','after',ctx);state=prior['state'];require(state['present'] is True and state['projection'].get('stopped') is not True,'ALL stopped terminal states refuse resume, including infrastructure failure')
  require(o['basis']=='explicit_parent_attestation_from_concrete_attempt_custody' and type(o['accepted'])is bool and type(o['unaccounted_opened_calls'])is int and type(o['scientific_source_or_state_changed'])is bool,'Explicit lost-call/source/state observations missing')
  require(o['unaccounted_opened_calls']==0 and o['scientific_source_or_state_changed'] is False,'Unknown/lost calls or source/state repair cannot be waived')
  utc(o['checked_utc']);body.update(o,source_commit=R,prior_after_identity_sha256=prior['identity_sha256'],prior_state_sha256=state['file']['sha256'])
 elif kind=='refusal':
  o=fields(o,('basis','event_index','refusal_class','refusal_stage','refusal_boundary','completed_execution_evidence','raw_logs_or_exception_text_transferred','checked_utc'))
  s=summary(inputs,ctx);require(type(o['event_index'])is int and 0<=o['event_index']<len(s['paired_estimates']['outcome_accesses']),'Explicit actual outcome event selection required')
  event=s['paired_estimates']['outcome_accesses'][o['event_index']];inputs.original('original_refusal_source','hash_only')
  boundaries={'host_preflight_refused':'after_forecast_before_evaluator','evaluator_failed_without_record':'evaluator_invoked_no_record'}
  require(o['basis']=='explicit_parent_attestation_from_original_refusal_source' and o['refusal_class'] in boundaries and o['refusal_boundary']==boundaries[o['refusal_class']] and o['refusal_stage']==event['stage'],'Concrete original refusal class/stage/boundary missing')
  require(o['completed_execution_evidence'] is False and o['raw_logs_or_exception_text_transferred'] is False and utc(o['checked_utc'])>=utc(event['outcome_access_started_at']),'Refusal cannot substitute completed work or transfer raw prose')
  body.update({k:v for k,v in o.items() if k!='event_index'},source_commit=R,event_sha256=digest(event),component_id=event['stage']+'.evaluation',execution_source_sha256=TARGET_SOURCE,original_refusal_source_sha256=inputs.pins['original_refusal_source']['sha256'])
 elif kind=='interrupted_bodies':
  o=fields(o,('candidate_ids','root_ids','record_ids','public_finalize_exported_these_candidates','checked_utc'))
  for key in ('candidate_ids','root_ids','record_ids'):
   require(isinstance(o[key],list) and len(o[key])==len(set(o[key])),'Explicit unique original ID list required')
   for rid in o[key]:token(rid)
  s=summary(inputs,ctx);index=record_index(inputs);bodies=selected_records(inputs,index);interrupted=need(s,'interrupted_iteration')
  actual={r['id'] for r in interrupted['candidates'] if r.get('id')};require(set(o['candidate_ids'])==actual and actual,'Actual materialized interrupted candidate population required')
  roots=set(actual)
  for r in interrupted['candidates']:
   if (r.get('certification')or{}).get('record'):roots.add(r['certification']['record'])
   for comparison in r.get('comparisons',[]):
    cid=comparison['comparison'];require(cid in bodies,'Original interrupted comparison body missing');roots.update((cid,comparison['baseline_evaluation'],bodies[cid]['candidate_evaluation']))
  require(set(o['root_ids'])==roots and set(o['record_ids'])==closure(roots,index,bodies) and o['public_finalize_exported_these_candidates'] is False,'Original interrupted selected-body closure or export boundary differs')
  require(inputs.original('validation_exit','integer_exit')==0,'Original full-index validation did not succeed');utc(o['checked_utc'])
  body.update(o,campaign=ctx['campaign'],record_index_sha256=digest(index),public_full_validation_returncode=0)
 elif kind=='candidate_selection':
  o=fields(o,('basis','accepted','candidate_ids','completed_materialized_candidate_ids','original_named_candidate_ids','selection_completeness_independently_derived_by_auditor','checked_utc'))
  for key in ('candidate_ids','completed_materialized_candidate_ids','original_named_candidate_ids'):
   require(isinstance(o[key],list) and len(o[key])==len(set(o[key])),'Explicit unique original selected ID list required')
   for rid in o[key]:token(rid)
  s=summary(inputs,ctx);named=set()
  for name in sorted(inputs.spec['inputs']):
   if name.startswith('public_candidate_export:'):
    exported=inputs.original(name,'json');require(exported['format']=='swdb.campaign-export.v1' and exported['campaign']==ctx['campaign'] and exported['dry_run'] is False,'Exact original unsealed public named export required')
    require(all(r['level']!='rejected' for r in exported['candidates']),'Rejected original candidate cannot be promoted');named.update(r['id'] for r in exported['candidates'])
  completed={r['id'] for it in s['iterations'] for r in it['candidates'] if r.get('id')}
  require(o['basis']=='explicit_parent_check_of_original_28d_non_rejected_completed_selection' and type(o['accepted'])is bool and o['selection_completeness_independently_derived_by_auditor'] is False,'Original non-rejected selection completeness must be explicitly inherited')
  require(set(o['candidate_ids'])==named and o['original_named_candidate_ids']==sorted(named) and set(o['completed_materialized_candidate_ids'])==completed and named<=completed,'Explicit selected names/population differ from original bodies')
  utc(o['checked_utc']);body.update(o,source_commit=R,helper_sha256=HELPER,campaign=ctx['campaign'],summary_sha256=digest(s))
 else:
  o=fields(o,('administrative_enforcement','outcome_accesses_without_component','public_export_candidate_ids','infrastructure_iteration_provider_partition'))
  s=summary(inputs,ctx);after=collector(inputs,'after_custody','after',ctx);state=after['state'];require(state['present'] is True,'Original released safe state projection is required')
  index=record_index(inputs);exit_code=inputs.original('validation_exit','integer_exit');inputs.original('validation_stdout','hash_only');inputs.original('validation_stderr','hash_only')
  require(exit_code==0,'Original full-catalogue validation is required; index alone is not admission')
  projected=state['projection'];require(projected['campaign']==ctx['campaign'] and projected['campaign_sha256']==s['campaign_file']['sha256'] and projected['projection_contract']=='swdb.lanl17-safe-control-projection.v1','Original b08 state/config differs')
  require(projected['iterations']==[project_iteration(r) for r in s['iterations']] and projected['setup_calls']==project_calls(s['setup']['provider_calls']),'Original safe state/public summary rows differ')
  admin=fields(o['administrative_enforcement'],('basis','accepted','source_commit','campaign_source_sha256','search_source_sha256','state_file_sha256','summary_sha256','terminal','unsaved_provider_or_step_events_independently_replayed','summary_time_disk_usage_independently_reconstructed','terminal_premise'))
  require(admin['basis']=='explicit_parent_attestation_of_original_source_enforcement' and type(admin['accepted'])is bool and admin['source_commit']==R and admin['campaign_source_sha256']==CAMPAIGN_SOURCE and admin['search_source_sha256']==SEARCH_SOURCE,'Concrete original administrative source attestation missing')
  require(admin['state_file_sha256']==state['file']['sha256'] and admin['summary_sha256']==digest(s) and admin['terminal']==s['stop_reason'] and admin['unsaved_provider_or_step_events_independently_replayed'] is False and admin['summary_time_disk_usage_independently_reconstructed'] is False,'Unsaved enforcement/summary-time accounting cannot be reconstructed or guessed')
  if admin['terminal'] in {'lane_hours','disk'}:
   premise=fields(admin['terminal_premise'],('state','prospective_refusal_may_occur_below_used_limit'));require(premise['state']=='parent_attested_from_original_source_enforcement' and premise['prospective_refusal_may_occur_below_used_limit'] is True,'Explicit prospective below-limit source enforcement premise missing')
  else:require(admin['terminal_premise'] is None,'No additional unsaved enforcement premise/prose may be invented')
  named=set()
  for name in sorted(inputs.spec['inputs']):
   if name.startswith('public_candidate_export:'):
    public=inputs.original(name,'json');require(public['format']=='swdb.campaign-export.v1' and public['campaign']==ctx['campaign'] and public['dry_run'] is False,'Exact original unsealed candidate export missing');named.update(r['id'] for r in public['candidates'])
  require(set(o['public_export_candidate_ids'])==named,'Original supplied named export inventory differs; no completeness inferred')
  for rid in o['public_export_candidate_ids']:token(rid)
  require(isinstance(o['outcome_accesses_without_component'],list),'Explicit concrete refusal list required, including [] when none')
  for row in o['outcome_accesses_without_component']:
   fields(row,('event_sha256','component_id','basis','accepted','source_commit','refusal_class','refusal_stage','refusal_boundary','original_refusal_source_sha256','refusal_custody_pin'))
   require(row['basis']=='explicit_parent_attestation_of_preflight_or_evaluator_refusal' and type(row['accepted'])is bool and row['source_commit']==R,'Missing component is not completed execution')
   pin=need(row,'refusal_custody_pin');require(type(pin['canonical_ensure_ascii'])is bool and pin['canonical_ensure_ascii'] is True and pin['identity_sha256'],'Separately captured concrete refusal pin required')
   custody=inputs.compact('refusal_custody:'+row['event_sha256'],'swdb.lanl17-outcome-refusal-custody.v1');original=inputs.pins['refusal_custody:'+row['event_sha256']]
   require({k:original[k] for k in ('path','bytes','sha256','identity_sha256','canonical_ensure_ascii')}==pin and all(custody[k]==row[k] for k in ('event_sha256','component_id','source_commit','refusal_class','refusal_stage','refusal_boundary','original_refusal_source_sha256')),'Exact separately captured refusal body/pin differs')
  partition=o['infrastructure_iteration_provider_partition']
  if partition is not None:
   original=inputs.original('infrastructure_partition','json');require(partition==project_iteration(original) and need(inputs.pins['infrastructure_partition'],'original_state_file_sha256')==state['file']['sha256'],'Exact retained infrastructure provider partition/source missing; no grouping from summary permitted')
  body.update(source_commit=R,campaign=ctx['campaign'],estimator_sha256=F6,manifest_sha256=ctx['manifest_identity_sha256'],summary_sha256=digest(s),record_index=index,record_index_sha256=digest(index),source_state_file_sha256=state['file']['sha256'],state=projected,
   public_validation={'returncode':exit_code,'records_index_sha256':digest(index),'summary_sha256':digest(s),'stdout_sha256':inputs.pins['validation_stdout']['sha256'],'stderr_sha256':inputs.pins['validation_stderr']['sha256']},
   administrative_enforcement=admin,outcome_accesses_without_component=o['outcome_accesses_without_component'],public_export_candidate_ids=o['public_export_candidate_ids'])
  if partition is not None:body['infrastructure_iteration_provider_partition']=partition
 return body

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True,type=Path);p.add_argument('--request-sha256',required=True);p.add_argument('--output',required=True,type=Path)
 a=p.parse_args();request=regular(a.request);require(hash_file(request)==hex64(a.request_sha256),'Exact parent-approved request file SHA differs');raw=request.read_bytes();require(len(raw)<=MAX_BYTES,'Bounded parent request required')
 spec=strict_json(raw);require(spec['format']=='swdb.lanl17-parent-capture-request.v1' and spec['identity_sha256']==digest({k:v for k,v in spec.items() if k!='identity_sha256'},ensure_ascii=True),'Exact separately approved request seal required')
 require(spec['producer_sha256']==hash_file(Path(__file__)) and spec['source_plan_sha256']==PLAN and spec['auditor_sha256']==AUDITOR and spec['collector_sha256']==COLLECTOR,'Prospective approved producer/plan/auditor/collector pins differ')
 kind=spec['capture'];require(kind in CAPTURES,'Only original specified capture formats supported');ctx=spec['context'];account=ctx['account']
 require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and account['platform']=='linux' and account['host']=='mbit10','Actual parent capture executes on Linux mbit10 only')
 require(type(account['uid'])is int and account['uid']>0 and os.getuid()==os.geteuid()==account['uid'] and pwd.getpwuid(account['uid']).pw_name==account['user'],'Explicit original verified parent account required; no pathname inference')
 require(re.fullmatch('[0-9a-f]{40}',ctx['source_commit']) and ctx['source_C']==C and ctx['estimator_sha256']==F6 and ctx['helper_sha256']==HELPER,'Original final R/C/F6/helper must be explicit')
 hex64(ctx['manifest_identity_sha256']);require(isinstance(spec['read_roots'],list) and spec['read_roots'],'Explicit approved original file roots required')
 policy=fields(need(ctx,'policy'),('id','identity_sha256','frozen_at'));token(policy['id']);hex64(policy['identity_sha256']);utc(policy['frozen_at'])
 for r in spec['read_roots']:
  q=Path(r);require(q.is_absolute() and '..' not in q.parts and str(q).startswith(('/data/yanruj/','/data1/yanruj/')) and all(not v.is_symlink() for v in (q,*q.parents)),'Own external original read root required')
 if kind!='publication':require(ctx['campaign'] in {f'extensa-gem5-bfs-20261006-p{i}' for i in range(1,5)},'Original frozen campaign ID required')
 inputs=Inputs(spec);body=build(kind,ctx,need(spec,'observations'),inputs)
 # Every factual flag in body either came from an exact original input or an
 # explicitly required observation. No accepted/complete/released defaults.
 body['parent_capture_provenance']={'producer_sha256':spec['producer_sha256'],'capture_request_file_sha256':a.request_sha256,'capture_request_identity_sha256':spec['identity_sha256'],'canonical_ensure_ascii':True,
  'context_pins':{k:ctx[k] for k in ('source_commit','source_C','estimator_sha256','helper_sha256','manifest_identity_sha256','policy')},
  'original_inputs':inputs.pins,'source_plan_sha256':PLAN,'auditor_sha256':AUDITOR,'collector_sha256':COLLECTOR,'observations_sha256':digest(spec['observations']),
  'scope':'Separate parent capture; original inputs unchanged/unsealed where original. Explicit source enforcement and selection completeness are inherited, never independently manufactured. No normal/substantive trajectory status is inferred.'}
 body['identity_sha256']=digest(body,ensure_ascii=True);encoded=(json.dumps(body,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode();require(len(encoded)<=MAX_BYTES,'Bounded sanitized capture exceeds auditor pin limit')
 output=a.output;require(output.is_absolute() and '..' not in output.parts and not output.exists() and all(not v.is_symlink() for v in (output,*output.parents)),'Fresh explicit external output required')
 require(str(output).startswith('/data/yanruj/') and output.parent.is_dir() and output.parent.stat().st_uid==os.getuid(),'Fresh own external capture directory required')
 require(not output.is_relative_to(Path(need(ctx,'source_path'))) and all(output!=Path(pin['path']) for pin in inputs.pins.values()),'No source/original input may be overwritten')
 inputs.recheck();require(hash_file(request)==a.request_sha256,'Parent-approved request changed during capture')
 fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(encoded)
 inputs.recheck();print(json.dumps({'format':body['format'],'capture':kind,'path':str(output),'bytes':len(encoded),'sha256':sha(encoded),'identity_sha256':body['identity_sha256'],'canonical_ensure_ascii':True,'original_inputs_preserved':True,'auditor_or_collector_or_project_executed':False,'producer_sha256':spec['producer_sha256']}))

if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError) as exc:
  print(str(exc),file=sys.stderr);raise SystemExit(2)
