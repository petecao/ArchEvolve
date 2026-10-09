#!/usr/bin/env python3
"""SOURCE ONLY, NOT RUN: metadata-only local original32 request author.

Reads only its own source and one explicit parent-reviewed compact metadata
input. Does not open any descriptor, YAML, catalog, control or receipt body.
Creates two source32 requests and an UNEXECUTED argv worksheet for one CID.
Actual content checks remain the unchanged remote source32/assembler/6a duties.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

R='5e12a9796432654d88def24ecea617d16ca605b2'
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
H='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
B='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
A='6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
P='32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
PLAN='e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170'
CAMPAIGN='13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d'
SEARCH='348b07b38a7955a65b5c13629dd8234453609f152a78d27524df6bf840a989e7'
INDEX='7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5'
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5'
PRODUCER='/data1/yanruj/lanl17-custody-source-20261007-a3/capture-producer.py'
M2ID='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
M2SHA='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'
POLICY={'id':'extensa-gem5-bfs-20261006-p1.agreement.5bae2f42d9078864','identity_sha256':'5bae2f42d9078864caad73e81a16007edb6458f0b101628ded04a7ef3aedbf7d','frozen_at':'2026-10-08T16:05:25.347884+00:00'}
MAX=8*1024*1024
STAT=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
class Refused(ValueError):pass
def require(ok,why):
 if not ok:raise Refused(why)
def fields(v,names):
 require(isinstance(v,dict) and set(v)==set(names),'Closed metadata field set differs');return v
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def hex64(v):require(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v),'Exact original SHA required');return v
def token(v):require(isinstance(v,str) and len(v)<=256 and re.fullmatch('[A-Za-z0-9_.:/+-]+',v),'Closed public metadata token required');return v
def utc(v):
 require(isinstance(v,str),'Explicit UTC string required');d=datetime.datetime.fromisoformat(v)
 require(d.tzinfo is not None and d.utcoffset()==datetime.timedelta(0),'Explicit UTC required');return d
def absolute(v):
 require(isinstance(v,str),'Explicit path required');p=Path(v)
 require(p.is_absolute() and '..' not in p.parts and not {'.ssh','.codex','.aws','auth.json','provider.json','prompt.txt','feedback.txt'}.intersection(p.parts),'Closed absolute metadata path required');return p
def remote(v):
 p=absolute(v);require(str(p).startswith(('/data/yanruj/','/data1/yanruj/')),'Remote original namespace required');return p
def exclusive_remote(v):
 p=remote(v);require(not any(p.is_relative_to(Path(root)) or Path(root).is_relative_to(p) for root in (S,RAW)),'Fresh output namespace must be external to whole S/RAW');return p
def strict(raw):
 def pairs(rows):
  out={}
  for k,v in rows:require(k not in out,'Duplicate JSON key');out[k]=v
  return out
 def bad(v):raise Refused('Nonfinite JSON literal')
 value=json.loads(raw,object_pairs_hook=pairs,parse_constant=bad);nodes=[0]
 def walk(v,depth=0):
  nodes[0]+=1;require(depth<=40 and nodes[0]<=200000,'Finite metadata structure exceeded')
  if isinstance(v,dict):
   for k,x in v.items():require(isinstance(k,str) and len(k)<=512,'Bounded metadata key required');walk(x,depth+1)
  elif isinstance(v,list):
   for x in v:walk(x,depth+1)
  elif isinstance(v,str):require(len(v)<=4096 and 'FUTURE' not in v and 'ACTUAL_' not in v,'Unfilled/bounded original metadata required')
  else:require(v is None or type(v) in (bool,int),'Closed metadata values required')
 walk(value);return value
def regular(p):
 require(p.is_absolute() and '..' not in p.parts and all(not x.is_symlink() for x in (p,*p.parents)),'Owned nonsymlink input required')
 q=p.stat();require(stat.S_ISREG(q.st_mode) and q.st_uid==os.getuid() and q.st_nlink==1 and stat.S_IMODE(q.st_mode)==0o600 and q.st_size<=MAX,'Own0600 bounded single-link metadata required');return q
def read_original(p,expected):
 before=regular(p);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  opened=os.fstat(f.fileno());raw=f.read(MAX+1);ended=os.fstat(f.fileno())
 after=regular(p);require(all(getattr(before,k)==getattr(opened,k)==getattr(ended,k)==getattr(after,k) for k in STAT),'Metadata changed on read')
 require(len(raw)==before.st_size and sha(raw)==hex64(expected),'Exact metadata bytes/SHA differ');return raw
def source_pin(v):
 fields(v,('path','bytes','sha256'));remote(v['path']);hex64(v['sha256'])
 require(type(v['bytes'])is int and 0<v['bytes']<=32*1024*1024,'Bounded original source size required')
def descriptor(v):
 require(isinstance(v,dict) and type(v.get('sealed'))is bool,'Explicit original seal classification required')
 keys=['path','bytes','sha256','encoding','sealed','writer_source']
 if v['sealed']:keys+=['identity_sha256','canonical_ensure_ascii','canonical_policy_sources']
 fields(v,keys);remote(v['path']);hex64(v['sha256']);source_pin(v['writer_source'])
 require(type(v['bytes'])is int and 0<=v['bytes']<=32*1024*1024,'Bounded original size required')
 require(v['encoding'] in {'json','yaml','integer_exit','hash_only'},'Closed original encoding required')
 if v['sealed']:
  require(v['encoding']=='json' and type(v['canonical_ensure_ascii'])is bool,'Explicit original canonical JSON policy required');hex64(v['identity_sha256'])
  require(isinstance(v['canonical_policy_sources'],list) and 1<=len(v['canonical_policy_sources'])<=16,'Original policy source pins required')
  for x in v['canonical_policy_sources']:source_pin(x)
  require(all(x['sha256']==v['writer_source']['sha256'] for x in v['canonical_policy_sources']),'Only original own-writer canonical policy accepted in these roles')
def ids(v):
 require(isinstance(v,list) and len(v)<=4096 and len(v)==len(set(v)),'Explicit unique bounded original ID list required')
 for x in v:token(x)
def emit(root,name,value):
 raw=(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode();require(len(raw)<=MAX,'Output metadata exceeds bound')
 p=root/name;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 read_original(p,sha(raw));return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True,type=Path);ap.add_argument('--input-sha256',required=True);ap.add_argument('--author-sha256',required=True)
 args=ap.parse_args();start=time.monotonic()
 def timeout(signum,frame):raise Refused('Metadata author deadline exceeded')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(45)
 own=Path(__file__).absolute();read_original(own,args.author_sha256);raw=read_original(args.input,args.input_sha256);v=strict(raw)
 fields(v,('format','campaign','original_inputs','trajectory_observations','selection_observations','remote_routes','parent_review','output_directory'))
 require(v['format']=='swdb.lanl17-original32-request-author-input.v1','Exact input format required');cid=v['campaign']
 require(cid in {f'extensa-gem5-bfs-20261006-p{i}' for i in range(1,5)},'Fixed original campaign required')
 pins=v['original_inputs'];require(isinstance(pins,dict) and 7<=len(pins)<=4096,'Explicit bounded original inventory required')
 required={'manifest_M2','summary','after_custody','record_index','validation_exit','validation_stdout','validation_stderr'}
 require(required<=set(pins) and all(k in required or k.startswith(('public_candidate_export:','refusal_custody:')) for k in pins),'Only exact trajectory input roles accepted')
 for k,x in pins.items():token(k);descriptor(x)
 sizes={H:38195,B:24818,INDEX:33445,CAMPAIGN:79456,P:46165}
 for x in pins.values():
  w=x['writer_source'];require(w['sha256'] in sizes and w['bytes']==sizes[w['sha256']],'Fixed original writer source/size required')
 require(sum(x['bytes'] for x in pins.values())<=512*1024*1024,'Original declared bytes exceed source32 limit')
 m=pins['manifest_M2'];require(m['path']==RAW+'/manifest.json' and m['bytes']==292401 and m['sha256']==M2SHA and m['sealed'] is True and m['identity_sha256']==M2ID and m['canonical_ensure_ascii'] is True and m['writer_source']['sha256']==H,'Exact original M2 descriptor required; M2 itself has no canonical flag')
 summary_path=RAW+'/campaign-runs/extensa/'+cid+'/records/campaign_summaries/'+cid+'.summary.yaml'
 require(pins['summary']['path']==summary_path and pins['summary']['sealed'] is False and pins['summary']['encoding']=='yaml' and pins['summary']['writer_source']['sha256']==CAMPAIGN,'Exact original public summary route/source required')
 require(pins['after_custody']['sealed'] is True and pins['after_custody']['encoding']=='json' and pins['after_custody']['canonical_ensure_ascii'] is True and pins['after_custody']['writer_source']['sha256']==B,'OriginalB08 AFTER required')
 require(pins['record_index']['sealed'] is False and pins['record_index']['encoding']=='json' and pins['record_index']['writer_source']['sha256']==INDEX,'Original full7a index required')
 for role,suffix,encoding in (('validation_exit','exit-code.txt','integer_exit'),('validation_stdout','stdout','hash_only'),('validation_stderr','stderr','hash_only')):
  x=pins[role];require(x['path']==RAW+'/validate-'+cid+'.'+suffix and x['sealed'] is False and x['encoding']==encoding and x['writer_source']['sha256']==H,'Original28 persisted full validation output required')
 for name,x in pins.items():
  if name.startswith('public_candidate_export:'):require(x['path']==RAW+'/export-'+cid+'.stdout' and x['sealed'] is False and x['encoding']=='json' and x['writer_source']['sha256']==H,'Original28 persisted public export required')
 require(sum(k.startswith('public_candidate_export:') for k in pins)<=1,'One original28 combined public export perCID required')
 routes=fields(v['remote_routes'],('trajectory_request','trajectory_output','candidate_selection_request','candidate_selection_output'))
 ps=[exclusive_remote(x) for x in routes.values()];require(len(set(ps))==4 and all(not (a.is_relative_to(b) or b.is_relative_to(a)) for i,a in enumerate(ps) for b in ps[i+1:]),'Distinct external request/output routes required')
 require(not any(str(p)==x['path'] for p in ps for x in pins.values()),'Request/output cannot overwrite original input')
 t=fields(v['trajectory_observations'],('administrative_enforcement','outcome_accesses_without_component','public_export_candidate_ids','infrastructure_iteration_provider_partition'))
 admin=fields(t['administrative_enforcement'],('basis','accepted','source_commit','campaign_source_sha256','search_source_sha256','state_file_sha256','summary_sha256','terminal','unsaved_provider_or_step_events_independently_replayed','summary_time_disk_usage_independently_reconstructed','terminal_premise'))
 require(admin['basis']=='explicit_parent_attestation_of_original_source_enforcement' and type(admin['accepted'])is bool and admin['source_commit']==R and admin['campaign_source_sha256']==CAMPAIGN and admin['search_source_sha256']==SEARCH,'Explicit original source enforcement observation required')
 hex64(admin['state_file_sha256']);hex64(admin['summary_sha256']);token(admin['terminal'])
 require(admin['unsaved_provider_or_step_events_independently_replayed'] is False and admin['summary_time_disk_usage_independently_reconstructed'] is False and t['infrastructure_iteration_provider_partition'] is None,'Normal original history cannot acquire reconstructed events/accounting')
 if admin['terminal'] in {'lane_hours','disk'}:
  z=fields(admin['terminal_premise'],('state','prospective_refusal_may_occur_below_used_limit'));require(z=={'state':'parent_attested_from_original_source_enforcement','prospective_refusal_may_occur_below_used_limit':True},'Exact original below-limit enforcement premise required')
 else:require(admin['terminal_premise'] is None,'No invented terminal premise')
 ids(t['public_export_candidate_ids']);require(isinstance(t['outcome_accesses_without_component'],list) and len(t['outcome_accesses_without_component'])<=4096,'Explicit genuine missing-component observations required')
 for row in t['outcome_accesses_without_component']:
  fields(row,('event_sha256','component_id','basis','accepted','source_commit','refusal_class','refusal_stage','refusal_boundary','original_refusal_source_sha256','refusal_custody_pin'));hex64(row['event_sha256']);hex64(row['original_refusal_source_sha256']);token(row['component_id']);token(row['refusal_stage'])
  require(row['basis']=='explicit_parent_attestation_of_preflight_or_evaluator_refusal' and type(row['accepted'])is bool and row['source_commit']==R,'Explicit original refusal observation required')
  p=fields(row['refusal_custody_pin'],('path','bytes','sha256','identity_sha256','canonical_ensure_ascii'));name='refusal_custody:'+row['event_sha256']
  require(name in pins and {k:pins[name][k] for k in p}==p,'Separately captured original32 refusal pin required')
 selection=fields(v['selection_observations'],('basis','accepted','candidate_ids','completed_materialized_candidate_ids','original_named_candidate_ids','selection_completeness_independently_derived_by_auditor','checked_utc'))
 require(selection['basis']=='explicit_parent_check_of_original_28d_non_rejected_completed_selection' and type(selection['accepted'])is bool and selection['selection_completeness_independently_derived_by_auditor'] is False,'Explicit original selection check required')
 for key in ('candidate_ids','completed_materialized_candidate_ids','original_named_candidate_ids'):ids(selection[key])
 require(selection['original_named_candidate_ids']==sorted(selection['candidate_ids']) and set(selection['candidate_ids'])<=set(selection['completed_materialized_candidate_ids']) and selection['candidate_ids']==t['public_export_candidate_ids'],'Named and full completed populations must be explicit and consistent')
 review=fields(v['parent_review'],('basis','author_sha256','payload_sha256','checked_utc','all_four_normal_custody_originals_reviewed','finalize_completion_originals_reviewed','full_index_and_validation_continuity_reviewed','original_summary_after_and_selection_reviewed','conditional_refusal_custody_reviewed','remote_routes_scope_and_freshness_reviewed','actual_inputs_approved','fixtures'))
 require(review['basis']=='explicit_parent_review_of_original32_actual_metadata_inputs' and review['author_sha256']==args.author_sha256 and review['payload_sha256']==digest({k:x for k,x in v.items() if k!='parent_review'}),'Exact actual payload/author review binding required')
 for key in ('all_four_normal_custody_originals_reviewed','finalize_completion_originals_reviewed','full_index_and_validation_continuity_reviewed','original_summary_after_and_selection_reviewed','conditional_refusal_custody_reviewed','remote_routes_scope_and_freshness_reviewed','actual_inputs_approved'):require(review[key] is True,'Explicit actual parent review required: '+key)
 require(review['fixtures'] is False,'Actual observations cannot be fixtures');checked=utc(review['checked_utc']);now=datetime.datetime.now(datetime.timezone.utc)
 require(utc(POLICY['frozen_at'])<=utc(selection['checked_utc'])<=checked<=now,'Actual original review chronology required')
 root=absolute(v['output_directory']);require(root.parent.is_dir() and root.parent.stat().st_uid==os.getuid() and all(not x.is_symlink() for x in (root,*root.parents)) and root.is_relative_to(Path('/private/tmp')) and not root.exists(),'Fresh local private author output required')
 ctx={'source_commit':R,'source_C':C,'estimator_sha256':F6,'helper_sha256':H,'source_path':S,'manifest_identity_sha256':M2ID,'policy':POLICY,'campaign':cid,'account':{'platform':'linux','host':'mbit10','uid':114316761,'user':'yanruj'}}
 root.mkdir(mode=0o700);outputs={};argvs={}
 for kind,obs in (('trajectory',t),('candidate_selection',selection)):
  selected=pins if kind=='trajectory' else {k:x for k,x in pins.items() if k in {'manifest_M2','summary'} or k.startswith('public_candidate_export:')}
  request={'format':'swdb.lanl17-parent-capture-request.v1','producer_sha256':P,'source_plan_sha256':PLAN,'auditor_sha256':A,'collector_sha256':B,'capture':kind,'context':ctx,'observations':obs,'inputs':selected,'read_roots':['/data/yanruj/EvolveSWDB_runs','/data1/yanruj']}
  request['identity_sha256']=digest(request);outputs[kind]=emit(root,kind+'-request.json',request)
  outputs[kind].update(identity_sha256=request['identity_sha256'],canonical_ensure_ascii=True,remote_request_path=routes[kind+'_request'])
  argvs[kind]=['/usr/bin/python3.12','-B',PRODUCER,'--request',routes[kind+'_request'],'--request-sha256',outputs[kind]['sha256'],'--output',routes[kind+'_output']]
 require(time.monotonic()-start<45,'Author finite deadline exceeded');read_original(args.input,args.input_sha256);read_original(own,args.author_sha256)
 plan={'format':'swdb.lanl17-original32-unexecuted-request-plan.v1','state':'authored_for_exact_parent_review_not_run','campaign':cid,'author_sha256':args.author_sha256,'input_sha256':args.input_sha256,'parent_review_sha256':digest(review),'request_pins':outputs,'argv':argvs,'producer_sha256':P,'remote_timeout_seconds':300,'local_timeout_seconds':420,'scientific_admission':False,'descriptor_bodies_read':0,'source32_or_project_executed':False}
 meta=emit(root,'request-action-plan-NOTRUN.json',plan);signal.alarm(0);print(json.dumps({'state':plan['state'],'campaign':cid,'requests':outputs,'action_plan':meta,'scientific_admission':False,'descriptor_bodies_read':0}))
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError) as exc:
  print(json.dumps({'state':'refused','exception_class':type(exc).__name__,'message_sha256':sha(str(exc).encode()),'raw_original_values_transferred':False}),file=sys.stderr);raise SystemExit(2)
