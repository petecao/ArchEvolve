"""SOURCE ONLY: bounded metadata author for a distinct corrected DEFAULT request.
No SSH/Git/operational imports, source mutation, seal generation or admission.
Original failed DEFAULT and the full prior request/proof/protection scope remain.
"""
import argparse,copy,datetime,hashlib,itertools,json,os,pathlib,re,stat,time
T=pathlib.Path('/private/tmp');BASE='/data1/yanruj';FROZEN='5e12a9796432654d88def24ecea617d16ca605b2'
G=('lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py',180887,'d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301')
W=('lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py',24114,'e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec')
PUBLISHER=(BASE+'/lanl17-publish-sparse-parent-originals-20261008-a3.py',16126,'5e667fa8ca26ece4825631e5d51feca490f3e154688a38399518bf9c237df2d9')
FIXED={
 'request':('lanl17-actual-sparse-default-parent-request-20261008-a2.json',527815,'fbf346baa605ade9ddd46477e9ea4cb5aba9bc753b2eca9e165f00bb70787173'),
 'publication':('lanl17-sparse-default-original-publication-actual-20261008-a2/stdout',1408,'1584a2fdb0dba84c7d3c33574a944b9c0c56cc76dea41c04a5ffdd121ef5bbe3'),
 'failure_receipt':('lanl17-detached-sparse-default-a1-originals-20261008/guard-receipt/receipt.json',27392,'3ac1a3ed99d22862db3f3c8ad894127ab58035273d057bfe7e56b7cb7645da22'),
 'cost':('lanl17-sparse-R2-corrected-read-budget-source-review-20261008-a1.md',5772,'4ced54a540e3db9049efbfb334e551d04f64c60277fa7852f1d8c9e3bfa72eba'),
 'guard_review':('lanl17-sparse-retirement-guard-r3-r4-r5-independent-full-source-review-20261008-a1.md',9534,'3d65a55669a9d0369fad64dae6ece007f1f559781563c874c59eb859fb69d927'),
 'chain_review':('lanl17-selected-sparse-R5-W2-pin-chain-independent-source-review-20261008-a1.md',7984,'3fce20a2e69d8e5cd50630d608f7c94e97c337e79b7b00a79216cdf51cd6f329'),
}
MUTABLE={'checked_at','selection_reason','allocation_decision','fresh_capacity_and_cost','parent_review_facts','protected_file_pins','additional_protected_paths'}
class Refused(Exception):pass
def need(value,reason):
 if not value:raise Refused(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def strict(raw):
 def pairs(rows):
  result={}
  for key,value in rows:need(key not in result,'duplicate_JSON_key');result[key]=value
  return result
 def bad(value):raise Refused('nonfinite_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
class Inputs:
 def __init__(self):self.started=time.monotonic();self.total=0;self.files=[]
 def read(self,path,digest,size=None):
  p=pathlib.Path(path);need(time.monotonic()-self.started<=90,'metadata_deadline')
  need(p.is_absolute() and p.is_relative_to(T) and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'local_original_route')
  before=p.lstat();need(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid() and before.st_nlink==1 and before.st_size<=2*1024*1024,'local_original_identity_or_cap')
  if size is not None:need(before.st_size==size,'fixed_original_size')
  fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
  with os.fdopen(fd,'rb') as f:
   raw=f.read(2*1024*1024+1);need(len(raw)==before.st_size and stamp(before)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'local_original_read_changed')
  self.total+=len(raw);need(self.total<=16*1024*1024 and sha(raw)==digest,'metadata_cumulative_cap_or_pin')
  pin={'path':str(p),'bytes':len(raw),'sha256':digest,'stat':stamp(before)};self.files.append(pin);return raw,pin
 def close(self):
  need(time.monotonic()-self.started<=90,'metadata_deadline')
  for pin in self.files:need(stamp(pathlib.Path(pin['path']).lstat())==pin['stat'],'local_original_final_stat_changed')
def fresh_age(value):
 at=datetime.datetime.fromisoformat(value);need(at.tzinfo is not None and 0<=(datetime.datetime.now(datetime.timezone.utc)-at).total_seconds()<=120,'fresh_capacity_age')
def main():
 os.umask(0o077);a=argparse.ArgumentParser(description=__doc__)
 for name in ('source-sha256','fresh-capacity','fresh-capacity-sha256','copy-original','copy-original-sha256','failed-custody-sha256','output'):a.add_argument('--'+name,required=True)
 args=a.parse_args();inputs=Inputs();inputs.read(pathlib.Path(__file__).absolute(),args.source_sha256)
 documents={};fixed_pins={}
 for key,(name,size,digest) in FIXED.items():
  raw,pin=inputs.read(T/name,digest,size);fixed_pins[key]=pin
  if key in ('request','publication','failure_receipt'):documents[key]=strict(raw)
 request=documents['request'];failure=documents['failure_receipt']
 need(request['sealed'] is False and 'identity_sha256' not in request and request['expected_primary']==FROZEN,'original_unsealed_request_scope')
 need(failure['admitted'] is False and failure['failure']=='cumulative_read_limit' and failure['retire_requested'] is False and failure['retired_rows']==[] and failure['completed_retirements']==[],'preserved_original_failed_default_scope')
 raw,custody_pin=inputs.read(T/'lanl17-detached-sparse-default-a1-originals-20261008/local-custody.json',args.failed_custody_sha256);custody=strict(raw)
 need(custody['sealed'] is False and custody['semantic_or_success_or_capacity_admission'] is False and custody['missing_original_names']==[] and len(custody['originals'])==9,'complete_original_failed_custody')
 for entry in custody['originals']:inputs.read(entry['local_path'],entry['sha256'],entry['bytes'])
 raw,copy_pin=inputs.read(args.copy_original,args.copy_original_sha256);copy_result=strict(raw)
 need(copy_result['format']=='swdb.git-only-sparse-retirement-two-source-private-copy.v1' and copy_result['sealed'] is False and copy_result['primary40']==FROZEN and copy_result['selected_mains_invoked'] is False and copy_result['cleanup_capacity_or_scientific_admission'] is False and copy_result['primary_common_config_native_retention_refs_unchanged'] is True,'genuine_copy_original_scope')
 source_directory=BASE+'/lanl17-sparse-retirement-source-20261008-a2';need(copy_result['destination']==source_directory and len(copy_result['source_copies'])==2,'fresh_selected_two_source_copy_route')
 copied={row['role']:row for row in copy_result['source_copies']}
 for role,expected in (('guard',G),('wrapper',W)):
  row=copied[role];need(row['private_path']==source_directory+'/'+expected[0] and row['bytes']==expected[1] and row['sha256']==expected[2],'actual_selected_source_copy_pin')
 raw,fresh_pin=inputs.read(args.fresh_capacity,args.fresh_capacity_sha256);fresh=strict(raw)
 need(fresh['format']=='swdb.sparse-parent-fresh-capacity-original.v1' and fresh['sealed'] is False and fresh['script_mains_or_retirement_or_capacity_admission_performed'] is False,'fresh_capacity_original_scope');fresh_age(fresh['checked_at'])
 need(set(fresh['released_leases'])=={'mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'} and all(v=='released' for v in fresh['released_leases'].values()) and fresh['reserved_paths_still_absent']==request['reserved_absent_paths'],'fresh_released_leases_reserved_routes')
 need(len(fresh['private_control_copies'])==4,'old_and_new_two_source_copy_pins_required')
 for role,expected in (('guard',G),('wrapper',W)):
  matches=[p for p in fresh['private_control_copies'] if p['path']==source_directory+'/'+expected[0]]
  need(len(matches)==1 and matches[0]['bytes']==expected[1] and matches[0]['sha256']==expected[2] and matches[0]['stat']==copied[role]['private_stat'],'fresh_selected_copy_stable_stat')
 out=copy.deepcopy(request);allocation=out['allocation_decision'];pool=allocation['per_row_planning'];need(len(pool)==16,'original_sixteen_row_planning_pool')
 q=allocation['required_floor_Q_bytes'];allowance=allocation['administrative_planning_allowance_bytes'];need(q==25547235328 and allowance==67108864,'original_Q_and_whole_operation_allowance_unchanged')
 free=fresh['actual_free_bytes']['/data1'];need(type(free) is int and free>=0,'fresh_available_bytes');deficit=max(0,q-free);threshold=deficit+allowance;choices=[]
 for count in range(1,len(pool)+1):
  for subset in itertools.combinations(pool,count):
   total=sum(row['discounted_estimate_after_extra_original_admin_allowance_bytes'] for row in subset)
   if total>=threshold:choices.append((count,total,tuple(sorted(row['name'] for row in subset))))
  if choices:break
 need(choices,'conditional_pool_no_fit');count,total,names=min(choices);need(list(names)==request['selected_rows'] and count==16,'minimum_selected_subset_changed')
 out['checked_at']=fresh['checked_at'];allocation.update(fresh_free_bytes=free,deficit_D_bytes=deficit,selected_discounted_estimate_bytes=total,conditional_margin_after_administrative_allowance_bytes=total-threshold,minimum_cardinality=count)
 out['selection_reason'] += ' Corrected DEFAULT verifies tracked physical metadata and explicit original source fields; full regular-byte/Git-blob proof remains mandatory immediately before each actual retirement. Historical byte witnesses are fresh in DEFAULT, and no retirement inheritance is authorized by this request.'
 cost=out['fresh_capacity_and_cost'];cost.update(checked_at=fresh['checked_at'],actual_free_data1_bytes=free,actual_free_data_bytes=fresh['actual_free_bytes']['/data'],fresh_capacity_original_pin=fresh_pin,known_source_counter_material_original=fixed_pins['cost'],corrected_default_major_body_core_bytes=14381124025,conditional_retirement_major_body_core_after_prior_success_reuse_bytes=14702545997,old_known_scenario_walk_entries=cost.pop('known_scenario_walk_entries'),old_known_scenario_major_stat_checks=cost.pop('known_scenario_major_stat_checks'),obsolete_original_known_scenario_file_read_bytes=cost.pop('known_scenario_file_read_bytes'),remaining_cost_terms='Source-corrected major-body totals include all345 historical proofs and both full RAW passes. Initial tracked regular bytes are explicitly unverified by DEFAULT, with fresh per-row full byte checks required before actual action. Current role/admin/index/private-witness/proc/plan inputs remain counter debits; 16GiB/400k walk/2Mstat/3600s/256KiB receipt and scientific/CPU/provider caps are unchanged. These are conditional source estimates, not a total upper bound or fit/recovery guarantee. A genuine admitted new DEFAULT and separately fresh retirement plan are still mandatory; the failed a1 original grants no authority.')
 review=out['parent_review_facts'];need(review['actual_default_only'] is True and 'successful_default_original_bindings' not in review,'default_only_without_inherited_success')
 review.update(current_guard_wrapper_source_courier_original=copy_pin,guard_correction_full_source_review_original=fixed_pins['guard_review'],selected_launcher_chain_full_source_review_original=fixed_pins['chain_review'],preserved_failed_default_receipt_original=fixed_pins['failure_receipt'],preserved_failed_default_custody_original=custody_pin,metadata_first_default_regular_bytes_unverified=True,historical_bytes_freshly_read_in_default_only=True,retirement_or_capacity_or_scientific_admission=False)
 existing={p['path']:p for p in out['protected_file_pins']}
 additions=list(fresh['private_control_copies'])+[{'path':PUBLISHER[0],'bytes':PUBLISHER[1],'sha256':PUBLISHER[2]}]
 for row in documents['publication']['originals']:
  need(row['write_completed'] is True,'old_published_original_incomplete');additions.append({k:row[k] for k in ('path','bytes','sha256','stat')})
 for row in custody['originals']:additions.append({'path':row['remote_original_path'],'bytes':row['bytes'],'sha256':row['sha256'],'stat':row['remote_original_stat']})
 for pin in additions:
  if pin['path'] in existing:need(all(existing[pin['path']][k]==pin[k] for k in ('bytes','sha256')),'old_protected_original_changed')
  else:out['protected_file_pins'].append(pin);existing[pin['path']]=pin
 for directory in (source_directory,BASE+'/lanl17-detached-sparse-default-a1',BASE+'/lanl-library-preserving-sparse-retirement-20261008-a1'):
  if directory not in out['additional_protected_paths']:out['additional_protected_paths'].append(directory)
 need(set(out)==set(request) and all(out[k]==request[k] for k in request if k not in MUTABLE) and out['protected_file_pins'][:len(request['protected_file_pins'])]==request['protected_file_pins'] and out['additional_protected_paths'][:len(request['additional_protected_paths'])]==request['additional_protected_paths'],'original_request_proof_scope_or_protections_changed')
 inputs.close();fresh_age(out['checked_at']);destination=pathlib.Path(args.output);need(destination==T/'lanl17-actual-sparse-default-parent-request-20261008-a3.json' and not os.path.lexists(destination),'fresh_exact_corrected_default_request_route')
 raw=canonical(out)+b'\n';need(len(raw)<=2*1024*1024,'request_output_bound');fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'request_short_write');f.flush();os.fsync(f.fileno())
 print(json.dumps({'format':'swdb.corrected-sparse-default-unsealed-request-author-return.v1','sealed':False,'path':str(destination),'bytes':len(raw),'sha256':sha(raw),'checked_at':out['checked_at'],'selected_rows':out['selected_rows'],'conditional_margin_bytes':total-threshold,'selected_control_or_retirement_or_capacity_or_science_run':False},sort_keys=True))
if __name__=='__main__':
 try:main()
 except (Refused,ValueError,OSError,KeyError,TypeError) as error:
  print(json.dumps({'format':'swdb.corrected-sparse-default-request-author-refusal.v1','sealed':False,'error_class':type(error).__name__,'error_sha256':sha(str(error).encode()),'selected_control_or_admission_run':False}));raise SystemExit(2)
