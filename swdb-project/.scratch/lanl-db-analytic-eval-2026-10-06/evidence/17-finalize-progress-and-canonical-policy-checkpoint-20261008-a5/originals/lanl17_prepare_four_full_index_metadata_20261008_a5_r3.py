"""2026-10-08 ET. SOURCE-ONLY parent metadata preparation, NOT RUN.
One actual CID per invocation; remote namespace. No catalog/YAML body reads,
control imports, subprocess, science, validation, index execution or SSH.
Two stages preserve the actual a2 original boundary: specification, then bootstrap.
Approvals are required explicit parent attestations, never inferred from a hash.
"""
import argparse,datetime,hashlib,json,math,os,pwd,re,signal,socket,stat,sys,time
from pathlib import Path
UID=114316761
CAP=8*1024**2
END=time.monotonic()+45
R='5e12a9796432654d88def24ecea617d16ca605b2'
TREE='1ab2c8ab147251391a4af75e637114bdd5b0ff27'
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5'
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5'
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(n) for n in range(1,5))
ACCOUNT={'host':'mbit10','platform':'linux','uid':UID,'user':'yanruj'}
CONTROLS={
 'inventory':{'path':'/data1/yanruj/lanl17-input-author-source-20261007-a1/passive_inventory.py','bytes':29653,'sha256':'76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176'},
 'author':{'path':'/data1/yanruj/lanl17-input-author-source-20261007-a1/index_request_author.py','bytes':38266,'sha256':'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'},
 'writer':{'path':'/data1/yanruj/lanl17-index-source-20261007-a1/writer.py','bytes':33445,'sha256':'7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'},
 'envelope':{'path':'/data1/yanruj/lanl17-index-privacy-source-20261007-a1/envelope.py','bytes':38790,'sha256':'1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc'},
 'outer':{'path':'/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/outer_capture.py','bytes':34658,'sha256':'59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544'},
 'bootstrap':{'path':'/data1/yanruj/lanl17-index-private-outer-source-20261007-a1/bootstrap.sh','bytes':6549,'sha256':'0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217'},
 'helper':{'path':'/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py','bytes':38195,'sha256':'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'},
 'auditor':{'path':'/data1/yanruj/lanl17-custody-source-20261007-a3/auditor.py','bytes':115130,'sha256':'6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'},
 'collector':{'path':'/data1/yanruj/lanl17-custody-source-20261007-a2r1/collector.py','bytes':24818,'sha256':'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'}}
M2={'path':RAW+'/manifest.json','bytes':292401,'sha256':'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1','identity_sha256':'66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7','canonical_ensure_ascii':True}
NATIVE={
 '/usr/bin/bash':'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1',
 '/usr/bin/python3.12':'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f',
 '/usr/bin/timeout':'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52',
 '/usr/bin/sha256sum':'4d2db56c867e5324e0084c9e897f6360d37517de77ac96f2bd31494223d69a60',
 '/usr/bin/wc':'9005273a966c875547a4317288bdd92e7b2aa49ad86bc9978121242106405e6b',
 '/usr/bin/mkdir':'430c3f949d7d328cd835722f5bbddeac0956fbdfbbb6a197e0abb1def3ed27e2'}
VALIDATION={'validation_argv':'argv.json','validation_exit':'exit-code.txt','validation_stdout':'stdout','validation_stderr':'stderr'}
STAMP=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
STAT7=('dev','ino','mode','uid','size','mtime_ns','ctime_ns')
SEEN={}
class Refused(ValueError):pass
def need(ok,code):
 if not ok:raise Refused(code)
def tick():need(time.monotonic()<END,'finite_metadata_deadline')
def exact(v,keys,code):need(type(v) is dict and set(v)==set(keys),code);return v
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def digest(v):return sha(canonical(v))
def encoded(v):return (json.dumps(v,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
def strict(b):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d,'duplicate_JSON_key');d[k]=v
  return d
 def bad(_):raise Refused('nonfinite_JSON')
 v=json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
 def walk(x,depth=0):
  need(depth<=40,'metadata_depth')
  if type(x) is dict:
   need(all(type(k) is str for k in x),'metadata_key')
   for y in x.values():walk(y,depth+1)
  elif type(x) is list:
   for y in x:walk(y,depth+1)
  else:need(x is None or type(x) in (bool,str,int) or type(x) is float and math.isfinite(x),'closed_metadata_scalar')
 walk(v);return v
def hash64(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'actual_SHA256');return v
def utc(v):
 need(type(v) is str and len(v)<=40,'actual_UTC');u=datetime.datetime.fromisoformat(v)
 need(u.tzinfo is not None and u.utcoffset().total_seconds()==0,'UTC_offset');return u
def stamp(s):return {k:getattr(s,'st_'+k) for k in STAMP}
def path(v,exists=True):
 need(type(v) is str and len(v)<=1024 and re.fullmatch('/[A-Za-z0-9_./-]+',v) is not None,'closed_absolute_route')
 p=Path(v);need(str(p)==v and '..' not in p.parts and '.' not in p.parts,'canonical_spelling')
 need(p.is_relative_to(Path('/data/yanruj')) or p.is_relative_to(Path('/data1/yanruj')),'owned_remote_namespace')
 need(not any(q.is_symlink() for q in (p,*p.parents)),'nonsymlink_route')
 need(not any(x in p.parts for x in ('.codex','.ssh','.aws')),'sensitive_route_refused')
 need(p.resolve(strict=exists)==p,'canonical_route');return p
def pin(v):
 exact(v,('path','bytes','sha256'),'exact_file_pin');path(v['path']);hash64(v['sha256'])
 need(type(v['bytes']) is int and 0<=v['bytes']<=CAP,'bounded_metadata_pin');return v
def read(v):
 tick();pin(v);p=path(v['path']);s=p.lstat()
 need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000 and s.st_size==v['bytes'],'owned_original_metadata')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  need(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_race');b=f.read(CAP+1)
  need(len(b)==s.st_size and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'metadata_read_race')
 need(sha(b)==v['sha256'],'original_file_SHA');SEEN[v['path']]=(dict(v),stamp(s));return b
def reread():
 for v,s in list(SEEN.values()):
  read(v);need(SEEN[v['path']][1]==s,'original_metadata_changed')
def unsealed(v):need(type(v) is dict and 'identity_sha256' not in v,'unsealed_original_required');return v
def sealed(v,declared_policy_required=True):
 need(type(v) is dict and (not declared_policy_required or v.get('canonical_ensure_ascii') is True),'original_true_policy')
 need(v.get('identity_sha256')==digest({k:x for k,x in v.items() if k!='identity_sha256'}),'original_true_seal');return v
def fresh(v,other=()):
 p=path(v,False);need(not p.exists() and not p.is_symlink(),'fresh_route')
 need(p.parent.is_dir() and p.parent.stat().st_uid==UID,'owned_existing_parent')
 for r in (S,RAW,*other):
  q=Path(r);need(not p.is_relative_to(q) and not q.is_relative_to(p),'disjoint_output_route')
 return p
def metadata_route(v,basename):
 pin(v);p=path(v['path']);need(p.name==basename and not p.is_relative_to(Path(S)) and not p.is_relative_to(Path(RAW)),'fixed_external_metadata_original_route')
def context(cid):return {'source_C':C,'estimator_sha256':F6,'final_R':{'commit':R,'tree':TREE},'account':ACCOUNT,'campaign':cid,'source_path':S,'project':S+'/swdb-project','records_directory':RAW+'/campaign-runs/extensa/'+cid+'/records','manifest_identity_sha256':M2['identity_sha256']}
def request(spec):return {'format':'swdb.lanl17-parent-record-index-request.v1','context':spec['context'],'originals':spec['originals'],'catalog_inventory':spec['catalog_inventory'],'summary_binding':spec['summary_binding'],'limits':spec['limits'],'parent_review':spec['writer_parent_review'],'output_directory':spec['writer_output_directory']}
def attestation(v,cid):
 exact(v,('campaign','records_directory','catalog_inventory_sha256','validation_files_sha256','prior_validation_full_catalogue','catalog_unchanged_since_original_validation','all_campaign_processes_stopped','exclusive_snapshot_ownership_confirmed','no_catalog_consumers_confirmed','all_four_normal_custodies_root_and_peer_reviewed','all_native_leases_currently_released_no_kernel_holder_or_FD9','source_R_F6_current_and_clean','native_tools_current_owned_regular_byte_pins_reviewed','native_Bash_startup_and_1024_byte_ulimit_units_reviewed','HOME_and_public_auth_preserved','all_outputs_currently_fresh_owned_and_disjoint','actual_inputs_parent_approved','fixtures_or_replays_allowed','observed_utc','reviewed_utc','valid_until_utc','native_executable_sha256'),'explicit_parent_attestation')
 need(v['campaign']==cid and v['records_directory']==context(cid)['records_directory'],'attested_catalog_route')
 for k in ('prior_validation_full_catalogue','catalog_unchanged_since_original_validation','all_campaign_processes_stopped','exclusive_snapshot_ownership_confirmed','no_catalog_consumers_confirmed','all_four_normal_custodies_root_and_peer_reviewed','all_native_leases_currently_released_no_kernel_holder_or_FD9','source_R_F6_current_and_clean','native_tools_current_owned_regular_byte_pins_reviewed','native_Bash_startup_and_1024_byte_ulimit_units_reviewed','HOME_and_public_auth_preserved','all_outputs_currently_fresh_owned_and_disjoint','actual_inputs_parent_approved'):need(v[k] is True,'explicit_true_parent_'+k)
 need(v['fixtures_or_replays_allowed'] is False and v['native_executable_sha256']==NATIVE,'no_replays_and_exact_native_pins')
 observed,reviewed,end=map(utc,(v['observed_utc'],v['reviewed_utc'],v['valid_until_utc']));now=datetime.datetime.now(datetime.timezone.utc)
 need(observed<=reviewed<=now<end and 0<(end-observed).total_seconds()<=300,'fresh_parent_attestation_interval')
 return v

def validate_inventory(inv,cid):
 unsealed(inv);need(inv['format']=='swdb.lanl17-passive-one-catalog-inventory.v1' and inv['metadata_is_unsealed'] is True,'original_inventory_format')
 need(inv['context']==context(cid) and inv['reader_source_pin']==CONTROLS['inventory'] and inv['original_index_writer_source_pin']==CONTROLS['writer'] and inv['manifest_M2_pin']==M2,'original_inventory_fixed_context')
 need(inv['metadata_digest_policy']=={'ensure_ascii':True,'sort_keys':True,'separators':[',',':'],'allow_nan':False},'original_inventory_digest_policy')
 rows=inv['catalog_inventory'];need(type(rows) is list and 0<len(rows)<=16384,'bounded_full_inventory');names=[];total=0
 for row in rows:
  exact(row,('path','bytes','sha256','stat'),'original_inventory_row');name=row['path'];need(type(name) is str and len(name)<=4096,'inventory_relative_path')
  p=Path(name);need(not p.is_absolute() and str(p)==name and '..' not in p.parts and not any(x.startswith('.') for x in p.parts) and p.suffix in ('.yaml','.yml'),'eligible_inventory_path')
  hash64(row['sha256']);s=exact(row['stat'],STAT7,'original_inventory_stat7')
  need(all(type(s[k]) is int and s[k]>=0 for k in STAT7) and s['uid']==UID and stat.S_ISREG(s['mode']) and row['bytes']==s['size'] and type(row['bytes']) is int and 0<=row['bytes']<=128*1024**2,'inventory_original_size_stat')
  total+=row['bytes'];names.append(name)
 need(names==sorted(set(names)) and total<=2*1024**3 and inv['catalog_inventory_sha256']==digest(rows),'sorted_unique_full_inventory_digest')
 limits=exact(inv['limits'],('catalog_record_count','catalog_total_bytes','max_catalog_file_bytes','max_catalog_total_bytes','max_output_metadata_bytes','metadata_deadline_seconds'),'original_limits')
 need(limits=={'catalog_record_count':len(rows),'catalog_total_bytes':total,'max_catalog_file_bytes':128*1024**2,'max_catalog_total_bytes':2*1024**3,'max_output_metadata_bytes':CAP,'metadata_deadline_seconds':limits['metadata_deadline_seconds']} and type(limits['metadata_deadline_seconds']) is int and 60<=limits['metadata_deadline_seconds']<=3600,'unchanged_writer_limits')
 utc(inv['read_started_utc']);utc(inv['current_facts_prepared_utc']);return rows,limits

def originals(cid,validation):
 exact(validation,VALIDATION,'four_original_full_validation_pins');raw={}
 for role,suffix in VALIDATION.items():
  need(validation[role]['path']==RAW+'/validate-'+cid+'.'+suffix,'original_helper28_validation_route');raw[role]=read(validation[role])
 need(strict(raw['validation_argv'])==['python3','-m','swdb','validate','--records',context(cid)['records_directory']],'full_original_validation_argv')
 m=re.fullmatch(rb'OK: ([0-9]+) record\(s\) valid\s*',raw['validation_stdout'])
 need(raw['validation_exit'].strip()==b'0' and m is not None and raw['validation_stderr']==b'','original_full_validation_success')
 o={'manifest_M2':dict(M2),'helper_source':CONTROLS['helper'],'auditor_source':CONTROLS['auditor'],'collector_source':CONTROLS['collector'],**validation}
 return o,int(m[1])
def summary(binding,inv,cid):
 if inv['summary_binding'] is not None:
  need(binding==inv['summary_binding'] and inv['summary_selection']=='present','original_present_summary_binding');exact(binding,('state','path','id','record_sha256'),'present_summary_schema');need(binding['state']=='present' and binding['id']==cid+'.summary','present_summary_identity');hash64(binding['record_sha256'])
  need(binding['path'] in {x['path'] for x in inv['catalog_inventory']},'summary_in_full_inventory')
 else:
  exact(binding,('state','id','parent_observed_absence'),'explicit_parent_absence_binding');need(inv['summary_selection']=='parent-binding-required' and binding=={'state':'absent','id':cid+'.summary','parent_observed_absence':True},'honest_explicit_parent_absence')
 return binding

def specification(data,cid,a):
 exact(data,('format','stage','campaign','inventory_original','validation_originals','summary_binding','parent_attestation','author_metadata_deadline_seconds','routes'),'specification_input_schema')
 metadata_route(data['inventory_original'],'catalog-inventory.json');inv=unsealed(strict(read(data['inventory_original'])));rows,limits=validate_inventory(inv,cid);o,count=originals(cid,data['validation_originals']);need(count==len(rows),'original_validation_and_complete_inventory_count')
 need(a['catalog_inventory_sha256']==digest(rows) and a['validation_files_sha256']=={k:data['validation_originals'][k]['sha256'] for k in VALIDATION},'parent_attested_original_pins')
 need(utc(inv['current_facts_prepared_utc'])<=utc(a['observed_utc']),'inventory_before_parent_observation')
 routes=exact(data['routes'],('preparation_output','author_output','writer_output','bootstrap_logs','inner_logs','outer_logs'),'six_fresh_routes');values=list(routes.values())
 for key,v in routes.items():fresh(v,[x for x in values if x!=v]);need(values.count(v)==1,'distinct_output_routes')
 n=data['author_metadata_deadline_seconds'];need(type(n) is int and 60<=n<=3600,'unchanged_author_seconds')
 snapshot={k:a[k] for k in ('campaign','records_directory','catalog_inventory_sha256','validation_files_sha256','prior_validation_full_catalogue','catalog_unchanged_since_original_validation','all_campaign_processes_stopped','exclusive_snapshot_ownership_confirmed','observed_utc')}
 payload={'format':'swdb.lanl17-parent-record-index-request.v1','context':context(cid),'originals':o,'catalog_inventory':rows,'summary_binding':summary(data['summary_binding'],inv,cid),'limits':limits,'output_directory':routes['writer_output']}
 review={'basis':'explicit_parent_review_of_real_quiescent_catalog_and_original_prior_full_validation','writer_sha256':CONTROLS['writer']['sha256'],'reviewed_request_payload_sha256':digest(payload),'actual_inputs_parent_approved':a['actual_inputs_parent_approved'],'fixtures_or_replays_allowed':a['fixtures_or_replays_allowed'],'validated_snapshot':snapshot}
 spec={'format':'swdb.lanl17-parent-record-index-request-author-spec.v1','context':payload['context'],'originals':o,'catalog_inventory':rows,'summary_binding':payload['summary_binding'],'limits':limits,'writer_parent_review':review,'writer_output_directory':routes['writer_output'],'controls':{'index_writer':CONTROLS['writer']},'output_directory':routes['author_output']}
 spec['author_review']={'basis':'explicit_parent_review_of_real_one_catalog_index_request_and_original_snapshot_attestations','author_sha256':CONTROLS['author']['sha256'],'reviewed_specification_payload_sha256':digest(spec),'actual_inputs_parent_approved':a['actual_inputs_parent_approved'],'fixtures_or_replays_allowed':a['fixtures_or_replays_allowed'],'writer_parent_review_sha256':digest(review),'reviewed_utc':a['reviewed_utc']}
 raw=encoded(spec);need(len(raw)<=CAP,'original_specification_cap');specpin={'path':routes['preparation_output']+'/index-author-specification.json','bytes':len(raw),'sha256':sha(raw)}
 argv=['/usr/bin/python3.12','-B',CONTROLS['author']['path'],'--specification',specpin['path'],'--specification-sha256',specpin['sha256'],'--parent-review-sha256',digest(spec['author_review']),'--author-sha256',CONTROLS['author']['sha256'],'--metadata-deadline-seconds',str(n),'--output-directory',routes['author_output']]
 action={'argv':argv,'source_pins':[CONTROLS['author'],CONTROLS['writer'],CONTROLS['helper'],CONTROLS['auditor'],CONTROLS['collector'],{k:M2[k] for k in ('path','bytes','sha256')}],'collect':[],'remote_seconds':n+120,'local_seconds':n+250}
 plan={'format':'swdb.lanl17-full-index-author-preparation.v1','executable':False,'scientific_admission':False,'actual_parent_attestation_inherited':a,'specification_pin':specpin,'author_review_sha256':digest(spec['author_review']),'writer_parent_review_sha256':digest(review),'routes':routes,'expected_unsealed_request_payload_sha256':digest(request(spec)),'expected_request_is_not_an_original':True,'config_template':action,'next_requirement':'Review actual original a2 request/custody before bootstrap stage; current plans are NOTRUN.'}
 return routes['preparation_output'],{'index-author-specification.json':raw,'index-author-action-plan.json':encoded(plan)}

def bootstrap(data,cid,a):
 exact(data,('format','stage','campaign','author_preparation_plan','specification_original','request_original','author_custody_original','actual_author_outputs_parent_reviewed','parent_attestation','bootstrap_parent_remote_seconds','bootstrap_parent_local_seconds','preparation_output'),'bootstrap_input_schema')
 need(data['actual_author_outputs_parent_reviewed'] is True,'explicit_actual_a2_original_review')
 for key,name in (('author_preparation_plan','index-author-action-plan.json'),('specification_original','index-author-specification.json'),('request_original','index-request.json'),('author_custody_original','author-custody.json')):metadata_route(data[key],name)
 plan=unsealed(strict(read(data['author_preparation_plan'])));spec=unsealed(strict(read(data['specification_original'])));req=unsealed(strict(read(data['request_original'])));custody=sealed(strict(read(data['author_custody_original'])))
 need(plan['format']=='swdb.lanl17-full-index-author-preparation.v1' and plan['executable'] is False and plan['scientific_admission'] is False and plan['specification_pin']==data['specification_original'],'original_preparation_binding')
 need(spec['context']==context(cid) and req==request(spec) and req['context']==context(cid),'actual_original_a2_request_equality')
 need(spec['format']=='swdb.lanl17-parent-record-index-request-author-spec.v1' and spec['controls']=={'index_writer':CONTROLS['writer']} and req['originals']['manifest_M2']==M2 and all(req['originals'][role]==CONTROLS[name] for role,name in (('helper_source','helper'),('auditor_source','auditor'),('collector_source','collector'))),'actual_original_fixed_sources')
 need(digest(spec['writer_parent_review'])==plan['writer_parent_review_sha256'] and digest(spec['author_review'])==plan['author_review_sha256'],'original_review_digest_binding')
 need(spec['writer_parent_review']['reviewed_request_payload_sha256']==digest({k:v for k,v in req.items() if k!='parent_review'}) and spec['author_review']['reviewed_specification_payload_sha256']==digest({k:v for k,v in spec.items() if k!='author_review'}),'original_review_payload_bindings')
 need(custody['format']=='swdb.lanl17-parent-record-index-request-author-custody.v1' and custody['state']=='parent_authored_unsealed_index_request_with_inherited_snapshot_review' and custody['actual_campaign_admission'] is False and custody['request_sealed'] is False and custody['bare_index_file_published_or_index_writer_executed'] is False,'actual_author_custody_scope')
 need(custody['request_file_pin']==data['request_original'] and custody['original_unsealed_specification_pin']==data['specification_original'] and custody['author_source_pin']==CONTROLS['author'] and custody['original_index_writer_source_pin']==CONTROLS['writer'] and custody['original_context']==context(cid) and custody['original_eight_pins']==req['originals'],'actual_original_author_links')
 need(custody['author_parent_review_sha256']==digest(spec['author_review']) and custody['writer_parent_review_sha256']==digest(req['parent_review']) and custody['catalog_inventory_sha256']==digest(req['catalog_inventory']) and custody['unsealed_request_payload_sha256']==digest(req),'actual_author_payload_links')
 need(custody['inherited_parent_validated_snapshot']==req['parent_review']['validated_snapshot'] and custody['limits']==req['limits'] and custody['original_summary_binding']==req['summary_binding'],'actual_author_snapshot_limits_summary')
 need(a['catalog_inventory_sha256']==digest(req['catalog_inventory']) and a['validation_files_sha256']=={k:req['originals'][k]['sha256'] for k in VALIDATION} and utc(custody['checked_utc'])<=utc(a['observed_utc']),'fresh_original_author_continuity')
 routes=plan['routes'];need(req['output_directory']==routes['writer_output'] and spec['output_directory']==routes['author_output'],'actual_author_output_routes')
 for key in ('writer_output','bootstrap_logs','inner_logs','outer_logs'):fresh(routes[key],[v for k,v in routes.items() if k!=key])
 out=fresh(data['preparation_output'],list(routes.values())+[str(Path(data['request_original']['path']).parent)])
 w=req['limits']['metadata_deadline_seconds'];need(type(w) is int and 60<=w<=3600,'original_writer_seconds')
 forwarded=['--request',data['request_original']['path'],'--request-sha256',data['request_original']['sha256'],'--request-author-source',CONTROLS['author']['path'],'--request-author-source-sha256',CONTROLS['author']['sha256'],'--parent-review-sha256',digest(req['parent_review']),'--output-directory',routes['writer_output'],'--log-directory',routes['inner_logs'],'--envelope-sha256',CONTROLS['envelope']['sha256'],'--cleanup-helper-source',CONTROLS['helper']['path'],'--python-executable','/usr/bin/python3.12','--python-executable-sha256',NATIVE['/usr/bin/python3.12'],'--timeout-executable','/usr/bin/timeout','--timeout-executable-sha256',NATIVE['/usr/bin/timeout'],'--timeout-family','GNU']
 direct=['/usr/bin/timeout','--signal=TERM','--kill-after=60s',str(w+420)+'s','/usr/bin/python3.12','-B',CONTROLS['envelope']['path'],*forwarded]
 first=[routes['bootstrap_logs'],str(w),'/usr/bin/python3.12','/usr/bin/timeout','/usr/bin/sha256sum','/usr/bin/wc','/usr/bin/mkdir',CONTROLS['outer']['path'],S,RAW,routes['writer_output'],routes['inner_logs'],routes['outer_logs'],M2['path'],M2['sha256'],CONTROLS['outer']['sha256'],NATIVE['/usr/bin/sha256sum'],NATIVE['/usr/bin/wc'],NATIVE['/usr/bin/mkdir'],CONTROLS['bootstrap']['sha256']]
 tail=['--envelope-source',CONTROLS['envelope']['path'],'--outer-log-directory',routes['outer_logs'],'--capture-source-sha256',CONTROLS['outer']['sha256'],'--parent-reviewed-argv-sha256',digest(direct)]
 args=first+forwarded+tail;need(len(first)==20 and len(forwarded)==28 and len(tail)==8 and len(args)==56,'exact_56_bootstrap_vector')
 argv=['/usr/bin/bash','--noprofile','--norc',CONTROLS['bootstrap']['path'],*args]
 remote,local=data['bootstrap_parent_remote_seconds'],data['bootstrap_parent_local_seconds'];need(type(remote) is int and type(local) is int and w+780<=remote<=7200 and remote+85<=local<=9000,'explicit_finite_parent_capture_allowances')
 action={'argv':argv,'source_pins':[CONTROLS[k] for k in ('bootstrap','outer','envelope','writer','author','helper')]+[{k:M2[k] for k in ('path','bytes','sha256')}],'collect':[],'remote_seconds':remote,'local_seconds':local}
 result={'format':'swdb.lanl17-full-index-bootstrap-preparation.v1','executable':False,'scientific_admission':False,'original_request_pin':data['request_original'],'original_author_custody_pin':data['author_custody_original'],'writer_parent_review_sha256':digest(req['parent_review']),'direct_GNU_envelope_argv':direct,'direct_GNU_envelope_argv_sha256':digest(direct),'bootstrap_script_argument_count':56,'complete_bootstrap_argv_sha256':digest(argv),'actual_parent_attestation_inherited':a,'config_template':action,'original_bounds':{'writer':w,'inner_GNU':w+120,'outer_GNU':w+420,'bootstrap_GNU':w+720,'kill_after':60,'diagnostic_bytes':16*1024**2,'returned_structured_bytes':16384},'next_requirement':'Independent complete argv/routes/native/startup/source review before execution; actual sealed inner/outer receipts and bare index pin required afterward. Logs/index stay remote; no index admission from transport0.'}
 return str(out),{'index-bootstrap-action-plan.json':encoded(result)}

def write_files(out,files,a):
 p=fresh(out);reread();need(datetime.datetime.now(datetime.timezone.utc)<utc(a['valid_until_utc']),'attestation_expired_before_write');tick()
 for b in files.values():need(len(b)<=CAP,'bounded_preparation_file')
 p.mkdir(mode=0o700);need(p.stat().st_uid==UID and stat.S_IMODE(p.stat().st_mode)==0o700,'private_output_directory')
 pins=[]
 for name,b in files.items():
  fd=os.open(p/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  v={'path':str(p/name),'bytes':len(b),'sha256':sha(b)};read(v);pins.append(v)
 reread();need(datetime.datetime.now(datetime.timezone.utc)<utc(a['valid_until_utc']),'attestation_expired_before_success');tick()
 return pins

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for k in ('input','input-sha256','helper-sha256'):parser.add_argument('--'+k,required=True)
 args=parser.parse_args();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Refused('metadata_alarm')));signal.alarm(45)
 need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','actual_remote_account')
 own=Path(__file__);read({'path':str(own),'bytes':own.stat().st_size,'sha256':hash64(args.helper_sha256)})
 inp=path(args.input);need(re.fullmatch('lanl17-p[1-4]-full-index-parent-input-(specification|bootstrap)-20261008-a5[.]json',inp.name) is not None and not inp.is_relative_to(Path(S)) and not inp.is_relative_to(Path(RAW)),'fixed_external_parent_input_route');data=strict(read({'path':str(inp),'bytes':inp.stat().st_size,'sha256':hash64(args.input_sha256)}))
 need(data['format']=='swdb.lanl17-full-index-parent-preparation-input.v1' and data['campaign'] in CIDS and data['stage'] in ('specification','bootstrap'),'closed_one_CID_stage')
 cid=data['campaign'];a=attestation(data['parent_attestation'],cid)
 m=sealed(strict(read({k:M2[k] for k in ('path','bytes','sha256')})),False);need(m['identity_sha256']==M2['identity_sha256'] and m['format']=='swdb.lanl17-parent-population.v1' and m['source']==S and m['raw']==RAW and m['source_commit']==R and m['estimator_sha256']==F6 and m['helper_sha256']==CONTROLS['helper']['sha256'] and m['source_clean'] is True,'original_M2_fixed_context')
 for v in CONTROLS.values():read(v)
 out,files=specification(data,cid,a) if data['stage']=='specification' else bootstrap(data,cid,a)
 pins=write_files(out,files,a);signal.alarm(0)
 print(json.dumps({'format':'swdb.lanl17-full-index-parent-preparation-return.v1','output_pins':pins,'stage':data['stage'],'campaign':cid,'controls_executed':False,'catalog_bodies_read':False,'scientific_admission':False,'diagnostic_bodies_returned':False},ensure_ascii=True,allow_nan=False))
if __name__=='__main__':
 try:main()
 except Exception as e:
  print(json.dumps({'format':'swdb.lanl17-full-index-parent-preparation-refusal.v1','exception_class':type(e).__name__,'exception_message_sha256':sha(str(e).encode(errors='replace')),'scientific_admission':False,'raw_text_returned':False},ensure_ascii=True),file=sys.stderr);sys.exit(3)
