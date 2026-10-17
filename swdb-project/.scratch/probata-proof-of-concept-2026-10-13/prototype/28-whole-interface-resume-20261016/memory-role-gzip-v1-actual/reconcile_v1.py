"""2026-10-16 ET. Reconcile compact actual byte-transform metadata only.

The reviewed remote complete grammar/gzip/inverse walk is not repeated here.
This does not admit an AST, ABI, source call, native result, or public proof.
"""
from pathlib import Path
import hashlib,json,stat
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent

def need(ok,message):
    if not ok:raise ValueError(message)
def pairs(rows):
    out={}
    for key,value in rows:
        need(key not in out,'duplicate metadata key');out[key]=value
    return out
def read(path,cap=1048576):
    path=Path(path);before=path.lstat()
    need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and before.st_size<=cap,'bounded physical metadata required')
    raw=path.read_bytes();after=path.lstat()
    fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
    need(len(raw)==before.st_size and all(getattr(before,k)==getattr(after,k) for k in fields),'metadata changed')
    return raw
def doc(name):return json.loads(read(HERE/name),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
def pin(path):
    path=Path(path);raw=read(path)
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def extent(path):return {k:pin(path)[k] for k in ('bytes','sha256')}
def rowmap(rows):
    need(type(rows) is list,'producer input list required');out={}
    for row in rows:
        need(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and type(row['sha256']) is str and row['path'] not in out,'closed unique producer pin required')
        out[row['path']]={k:row[k] for k in ('bytes','sha256')}
    return out
run=doc('actual-transform-invocation-v1.json');stdout=doc('actual-transform-stdout-v1.json')
postrun=doc('postflight-invocation-v2.json');before=doc('scoped-preflight-stdout-v2.json');after=doc('postflight-stdout-v2.json')
need(run['returncode']==postrun['returncode']==0 and run['local_refusal'] is postrun['local_refusal'] is None and run['input_source_unchanged'] is True and postrun['source_unchanged'] is True,'settled zero exit/unchanged sources required')
for invoked,out,err in ((run,'actual-transform-stdout-v1.json','actual-transform-stderr-v1.log'),(postrun,'postflight-stdout-v2.json','postflight-stderr-v2.log')):
    need(invoked['stdout']==extent(HERE/out) and invoked['stderr']==extent(HERE/err) and read(HERE/err)==b'','actual stdout/stderr identity differs')
policy=json.loads(read(WHOLE/'memory-role-gzip-v1/source_policy_v1.json'),object_pairs_hook=pairs)
known=policy['physical_inputs'];need(len(known)==911,'exact selected input census')
identity=hashlib.sha256(json.dumps(known,sort_keys=True,separators=(',',':')).encode()).hexdigest()
need(before['known_input_count']==after['known_input_count']==911 and before['known_input_map_sha256']==after['known_input_map_sha256']==identity,'exact pre/post input identity')
for check in (before,after):
    need(check['scoped_preflight_pass'] is True and check['source_commit']=='2baf722fdaa6cba24b859eae3172a6f597417d72' and check['source_clean'] is True,'exact source or scoped process decision differs')
    last=check['scans'][-1]
    need(last['selected_original_readers']==last['unreadable_own_processes']==[] and last['vanished_process_or_descriptor_observations']==0,'finite selected reader settlement differs')
    need(len(check['leases'])==3 and all(row['state']=='released' for row in check['leases'].values()),'fresh lease settlement differs')
completed=after['transform_result'];root=after['transform_output_root'];outputs=after['transform_file_pins']
need(rowmap(completed['input_pins'])==known and completed['selected_inputs_unchanged'] is True,'complete observed selected inputs differ')
need(len(outputs)==after['transform_file_count']==14 and sum(row['bytes'] for row in outputs.values())==after['transform_bytes']==13777031 and all(row['bytes']<=134217728 for row in outputs.values()),'closed physical output census/extent differs')
need(stdout=={'normalization_complete':True,'result':{'path':root+'/result.json',**outputs['result.json']},'source_call_ABI_or_public_admission':False},'flushed settled physical result differs')
need(completed['completion_requires_controller_zero_exit_and_settled_publication'] is True and completed['normalization_complete'] is True and completed['original_compiler_observation_accepted'] is True and completed['original_AST_ABI_source_call_admitted'] is False and completed['source_call_ABI_public_or_full28_admission'] is False and completed['compiler_or_native_or_solver_executed'] is False,'scientific boundaries differ')
transport=after['transport'];census=after['census'];inverse=after['inverse'];n=transport['normalization'];codec=transport['normalized_gzip_codec']
need(n==census,'retained census differs from transport')
need(census['raw_bytes']==537439896 and census['raw_sha256']=='c89c00e8b03717a6ab3c9733d7fbb14aeb46c0d7f2ea4c6d7e87097ad0e9ba67' and census['complete_original_JSON_token_grammar_checked'] is True,'complete original wire identity differs')
need(census['duplicate_events']==census['prospective_role_renames']==census['inverse_manifest_rows']==116 and census['unknown_or_mismatched_duplicate_events']==0 and census['duplicate_group_count']==1 and census['duplicate_groups'][0]['count']==116,'complete duplicate role census differs')
need(codec['compressed_bytes']==12666345 and codec['compressed_sha256']=='8f19a9369b02fde545e7d979d8c5e7852078cc004d8330e7a54ba0c70a7f2aba' and outputs['component/caller.normalized.json.gz']=={'bytes':codec['compressed_bytes'],'sha256':codec['compressed_sha256']},'normalized physical gzip differs')
need(codec['expanded_bytes']==n['normalized_bytes']==177082275 and codec['expanded_sha256']==n['normalized_sha256']=='5895fc09a89f41b352368a16fb32b3c5065e8add0672a06fcb29a6be0afa8319' and n['plain_normalized_file_cap_fit'] is False,'normalized expanded identity/old file-cap boundary differs')
need(n['original_minified_token_bytes']==177080187 and n['original_minified_token_sha256']=='5ddd90248ab0e6bbe298feb5c8ec48e6af28bd3fd9a7a3581cf4330e4f52d08a','original token identity differs')
need(outputs['component/rename-manifest.jsonl']=={'bytes':n['inverse_manifest_bytes'],'sha256':n['inverse_manifest_sha256']} and n['inverse_manifest_bytes']==31776,'complete inverse manifest differs')
inv=inverse['inverse']
need(inverse['complete_normalized_gzip_identity_verified'] is True and inverse['original_wire_identity_is_normalized_identity'] is False and inv['inverse_rows']==116 and inv['original_minified_token_bytes']==n['original_minified_token_bytes'] and inv['original_minified_token_sha256']==n['original_minified_token_sha256'] and inv['normalized_expanded_bytes']==n['normalized_bytes'] and inv['normalized_expanded_sha256']==n['normalized_sha256'] and inv['expanded_file_or_DOM_created'] is False,'complete exact inverse differs')
need(outputs['component/runtime-before.json']==outputs['component/runtime-after.json'] and len(after['fresh_original_v10_role_pins'])==5,'retained full runtime / fresh V10 metadata census differs')
files=['reconcile_v1.py','actual-transform-launch-v1.json','actual-transform-invocation-v1.json','actual-transform-stdout-v1.json','actual-transform-stderr-v1.log','scoped-preflight-invocation-v2.json','scoped-preflight-stdout-v2.json','root-derived-scoped-preflight-v2.py','root-derived-scoped-postflight-v2.py','postflight-invocation-v2.json','postflight-stdout-v2.json','postflight-stderr-v2.log','fresh-original-v10-role-pins-v1.json','postflight-shape-controls-v2.json']
value={'schema':'passive-memory-normalized-gzip-actual-reconciliation-1','date':'2026-10-16 ET','verdict':'PASS_PASSIVE_BYTE_TRANSFORM_ONLY','evidence':[pin(HERE/name) for name in files],
 'zero_exit':True,'empty_stderr':True,'local_wall_seconds':run['local_wall_seconds'],'controller_reported_wall_seconds':completed['wall_seconds'],'source_commit':after['source_commit'],
 'original_memory_compiler_generation':642,'selected_input_count':911,'selected_input_map_sha256':identity,'selected_inputs_unchanged':True,
 'output_root':root,'physical_output_count':14,'physical_output_bytes':after['transform_bytes'],'physical_output_pins':outputs,
 'normalized_gzip_codec':codec,'normalization':{k:n[k] for k in ('raw_bytes','raw_sha256','normalized_bytes','normalized_sha256','original_minified_token_bytes','original_minified_token_sha256','duplicate_events','unknown_or_mismatched_duplicate_events','inverse_manifest_rows','inverse_manifest_bytes','inverse_manifest_sha256','plain_normalized_file_cap_fit')},'inverse':inverse,
 'boundaries':{'remote_complete_walk_reexecuted_by_local_reconciler':False,'actual_DOM_AST_ABI_or_source_call_admitted':False,'current_0_2_public_proof_or_full28_admitted':False,'hardware_body_theorem_required':False,'original_G642_observation_only_boundary_preserved':True,'no_compiler_native_solver_or_proof_rerun':True,'measured_RSS_or_CPU_available':False,'exact_root_admitted_OS_PAM_current_SSH_transport_TCB':True,'unknown_unreadable_process_waiver':False}}
with (HERE/'actual-reconciliation-v1.json').open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(HERE/'actual-reconciliation-v1.json'),sort_keys=True))
