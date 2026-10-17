"""2026-10-16 ET: reconcile retained compact passive-transform observations.

This reads only local bounded metadata. The remote full grammar, gzip and inverse
walk are the reviewed controller observation, not independently re-executed here.
"""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def need(ok,message):
    if not ok:raise ValueError(message)
def unique(rows):
    value={}
    for key,item in rows:
        need(key not in value,'duplicate reconciliation key');value[key]=item
    return value
def document(name):
    raw=(HERE/name).read_bytes();need(len(raw)<=32768,'compact metadata bound')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
def pin(name):
    path=HERE/name;raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
before=document('actual-preflight-v2-stdout.json');after=document('actual-postflight-v2-stdout.json')
run=document('actual-transform-result-v2.json');execution=document('root-observed-execution-v2.json')
stdout=document('actual-transform-stdout-v2.json');immutability=document('actual-transform-immutability-v2.json')
need(run['returncode']==execution['returncode']==0 and run['local_refusal'] is execution['local_refusal'] is None,'settled zero exit required')
need((HERE/'actual-transform-stderr-v2.log').read_bytes()==b'' and run['stderr']==execution['stderr']==pin('actual-transform-stderr-v2.log'),'empty stderr linkage')
need(run['stdout']==execution['stdout']==pin('actual-transform-stdout-v2.json'),'stdout linkage')
need(before['pins']==after['pins'] and len(before['pins'])==36 and before['original_refusal']==after['original_refusal']==
    {'type':'Refused','message':'duplicate compiler JSON key'},'original exact selected input/refusal linkage')
need(not before['unrelated_unreadables'] and not after['unrelated_unreadables'] and
    all(row['self_ancestry'] for observation in (before,after) for row in observation['selected_processes']),'finite reader boundaries')
root=after['output'];outputs=after['output_pins'];need(len(outputs)==11,'closed settled output count')
need(sum(row['bytes'] for row in outputs.values())==12987048 and all(row['bytes']<=134217728 for row in outputs.values()),'settled output extents')
need(stdout=={'normalization_complete':True,'result':{'path':root+'/result.json',**outputs[root+'/result.json']},
    'source_call_ABI_or_public_admission':False},'flushed physical result linkage')
codec=after['normalized_gzip_codec'];n=after['normalization_selected'];inverse=after['inverse']
need(codec['compressed_bytes']==12787585 and codec['compressed_sha256']=='4156be12cc79326a4d7559f3e801b9f41ba9d2e01478ea6040c97fb6588a142b'
    and outputs[root+'/component/caller.normalized.json.gz']=={'bytes':codec['compressed_bytes'],'sha256':codec['compressed_sha256']},'normalized physical gzip linkage')
need(codec['expanded_bytes']==n['normalized_bytes']==178924116 and codec['expanded_sha256']==n['normalized_sha256']==
    '1f0616302273d146fc88e1c676d25c41230432ee8ec259a92ae65f8fbb5755a3','expanded normalized identity linkage')
need(n['original_minified_token_bytes']==178922028 and n['original_minified_token_sha256']==
    'fa44d97fbaff20b5b16300d39128bb29e41d9600ba7db57202b50be09368f366' and n['plain_normalized_file_cap_fit'] is False,'original token/plain extent linkage')
need(n['inverse_manifest_rows']==116 and n['inverse_manifest_bytes']==31776 and outputs[root+'/component/rename-manifest.jsonl']==
    {'bytes':n['inverse_manifest_bytes'],'sha256':n['inverse_manifest_sha256']},'complete manifest linkage')
need(inverse['complete_normalized_gzip_identity_verified'] is True and inverse['original_wire_identity_is_normalized_identity'] is False
    and inverse['inverse']['inverse_rows']==116 and inverse['inverse']['original_minified_token_sha256']==n['original_minified_token_sha256']
    and inverse['inverse']['normalized_expanded_sha256']==n['normalized_sha256'] and inverse['inverse']['expanded_file_or_DOM_created'] is False,'complete inverse linkage')
need(after['result_selected']['completion_requires_controller_zero_exit_and_settled_publication'] is True and
    after['result_selected']['original_capture_accepted'] is False and after['result_selected']['source_call_ABI_public_or_full28_admission'] is False,
    'separate original/scientific boundaries')
value={'schema':'passive-normalized-gzip-actual-reconciliation-1','date':'2026-10-16 ET','verdict':'PASS_PASSIVE_BYTE_TRANSFORM_ONLY',
    'source':pin('reconcile.py'),'launch':pin('actual-transform-launch-v2.json'),'root_execution':pin('root-observed-execution-v2.json'),
    'transport_result':pin('actual-transform-result-v2.json'),'before':pin('actual-preflight-v2-stdout.json'),
    'after':pin('actual-postflight-v2-stdout.json'),'immutability':pin('actual-transform-immutability-v2.json'),
    'zero_exit':True,'stderr_bytes':0,'local_wall_seconds':run['local_wall_seconds'],
    'controller_reported_wall_seconds':after['result_selected']['wall_seconds'],'selected_inputs_equal':36,
    'output_root':root,'physical_outputs':outputs,'physical_output_files':11,'physical_output_bytes':12987048,
    'normalized_gzip_codec':codec,'normalization':n,'inverse':inverse,
    'boundaries':{'remote_complete_walk_reexecuted_by_reconciler':False,'independent_actual_DOM_source_ABI_or_call_admission':False,
        'source_to_selected_Clang_binary_attestation_established':False,'original_V10_refusal_preserved':True,
        'original_plain_normalized_file_cap_refusal_preserved':True,'no_compiler_native_solver_or_proof_rerun':True,
        'measured_RSS_or_CPU_available':False,'root_owned_SSH_timeout_env_and_current_ancestor_TCB':True}}
with (HERE/'actual-reconciliation-v2.json').open('x') as handle:handle.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin('actual-reconciliation-v2.json'),sort_keys=True))
