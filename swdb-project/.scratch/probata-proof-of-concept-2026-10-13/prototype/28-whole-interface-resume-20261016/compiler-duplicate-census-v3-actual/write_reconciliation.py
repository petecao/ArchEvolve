"""Reconcile already delegated compact outputs only; no remote/AST rerun."""
import hashlib
import json
import math
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;POC=WHOLE.parents[1];V3=WHOLE/'compiler-duplicate-census-v3'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):
    def pairs(rows):
        out={}
        for key,value in rows:assert key not in out;out[key]=value
        return out
    return json.loads(path.read_bytes(),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))
result=doc(HERE/'actual-census-result-v3.json');stdout=HERE/'actual-census-stdout-v3.json';value=doc(stdout);census=value['census']
assert result['returncode']==0 and result['local_refusal'] is None and result['stdout']==pin(stdout) and result['stderr']['bytes']==0
assert result['stdin']==pin(V3/'complete_duplicate_census_v3.py') and result['command']==pin(V3/'complete-census-command-v3.json')
assert math.isfinite(value['wall_seconds']) and 0<value['wall_seconds']<600
assert value['complete_decoder_identity_verified'] is True and value['child_events']==[] and value['strict_policy_relaxed'] is False
assert value['actual_compiler_rerun'] is False and value['AST_source_call_ABI_or_proof_admission'] is False
assert (value['full_raw_bytes'],value['full_raw_sha256'])==(543412150,'cd7f4fa566146b9b061c2084b52b1143efc054d4c4d75cbe4f7911c81e326622')
assert (value['gzip_bytes'],value['gzip_sha256'])==(39192152,'1e01a023699d56da8054533db08de4370e4cd9425b414d1bb772a0efaca3891b')
publication=value['publication'];complete={k:v for k,v in value.items() if k!='publication'}
encoded=json.dumps(complete,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
assert publication['complete_report_bytes']==len(encoded) and publication['complete_report_sha256']==hashlib.sha256(encoded).hexdigest()
assert publication['omitted_event_display_rows']==publication['omitted_group_display_rows']==0
assert census['duplicate_events']==census['prospective_role_renames']==116 and census['unknown_or_mismatched_duplicate_events']==0
assert census['duplicate_group_count']==len(census['duplicate_groups'])==1
group=census['duplicate_groups'][0];signature=group['signature']
assert group['count']==116 and signature['ordinal']==2 and signature['reason']=='UsingType.type.original-and-desugared'
assert signature['key_sha256']==hashlib.sha256(b'type').hexdigest() and signature['node_kind_identity']['decoded_string_sha256']==hashlib.sha256(b'UsingType').hexdigest()
groups=json.dumps(census['duplicate_groups'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
assert census['complete_duplicate_group_census_sha256']==hashlib.sha256(groups).hexdigest()
assert census['original_minified_token_bytes']==178922028 and census['prospective_normalized_token_bytes']==178924116
assert census['prospective_normalized_token_bytes']-census['original_minified_token_bytes']==116*(len(b'"swdbClangDesugaredType"')-len(b'"type"'))
assert census['prospective_normalized_file_cap_fit'] is False and census['prospective_role_normalization_eligible'] is False and census['prospective_normalization_refused'] is True
assert census['complete_original_JSON_token_grammar_checked'] is True and census['ordered_duplicate_pairs_overwritten_or_dropped'] is False
assert census['normalized_AST_retained_or_admitted'] is False and census['actual_source_ABI_or_public_admission'] is False
before=doc(HERE/'actual-preflight-v3-stdout.json');after=doc(HERE/'actual-postflight-v3-stdout.json')
assert before['pins']==after['pins'] and before['current_physical_source_control_decoder_pins']==after['current_physical_source_control_decoder_pins'] and before['original_metadata']==after['original_metadata']
for observation in (before,after):
    assert not any(row['original_raw'] and not row['self_ancestry'] for row in observation['selected_processes'])
    assert observation['original_metadata']['component/result.json']['accepted'] is False
    assert observation['original_metadata']['component/result.json']['error']=={'type':'Refused','message':'duplicate compiler JSON key'}
receipt={'date':'2026-10-16 ET','status':'COMPLETE PASSIVE CENSUS SUCCEEDED; PLAIN NORMALIZED TRANSPORT REFUSED BY FILE EXTENT',
    'actual_source':pin(V3/'complete_duplicate_census_v3.py'),'command':pin(V3/'complete-census-command-v3.json'),
    'admission':pin(POC/'evidence/t28-complete-census-v3-root-admission-20261016.json'),
    'actual_files':[pin(HERE/name) for name in ('dispatch_once.py','preflight_source_v3.py','actual-census-launch-v3.json','actual-census-result-v3.json',
        'actual-census-stdout-v3.json','actual-census-stderr-v3.log','actual-preflight-v3.json','actual-preflight-v3-stdout.json','actual-preflight-v3-stderr.log',
        'actual-postflight-v3.json','actual-postflight-v3-stdout.json','actual-postflight-v3-stderr.log','actual-census-immutability-v3.json','write_reconciliation.py')],
    'counts':{key:census[key] for key in ('raw_bytes','original_minified_token_bytes','prospective_normalized_token_bytes','duplicate_events','duplicate_group_count',
        'unknown_or_mismatched_duplicate_events','objects','arrays','keys','values','max_depth','peak_live_key_charge','peak_live_summary_charge')},
    'identities':{key:census[key] for key in ('raw_sha256','original_minified_token_sha256','prospective_normalized_token_sha256','ordered_graph_merkle_sha256',
        'duplicate_event_census_sha256','complete_duplicate_group_census_sha256')},
    'qualified_duplicate_roles':{'UsingType.type.original-and-desugared':116},'other_duplicate_groups':0,'unknown_duplicate_roles':0,
    'remote_wall_seconds':value['wall_seconds'],'local_wall_seconds':result['local_wall_seconds'],'hard_address_space_bytes':536870912,'measured_peak_RSS':None,
    'sampled_value_pairs':{'retained':len(census['samples']),'different':sum(not row['values_structurally_identical'] for row in census['samples']),
        'all116_value_equality_classified_in_retained_metadata':False},
    'plain_normalized_file_cap_bytes':134217728,'plain_transport_eligibility':False,'plain_transport_refusal_reason':'178924116-byte normalized token stream exceeds 134217728-byte physical file cap',
    'fresh_physical_original_pins_before_after':len(before['pins']),'fresh_selected_source_control_decoder_pins_before_after':len(before['current_physical_source_control_decoder_pins']),
    'all_selected_inputs_unchanged':True,'original_G639_settlement_and_V10_refusal_unchanged':True,'fresh_full_Git_status_claimed':False,
    'checks_independently_recomputed_from_compact_output':['strict unique-key finite JSON','complete publication hash/count','full displayed group census hash/count',
        'exact documented group/key/kind identities','rewrite token extent arithmetic','plain file cap refusal','root-command-source/exit/physical output linkage','pre/post selected physical identities'],
    'producer_observations_not_independently_replayed':['complete original JSON grammar and every ordered Merkle/event token traversal','full original raw/gzip decoder observation','selected bind_zlib startup'],
    'actual_normalized_AST_written':False,'compiler_or_proof_rerun':False,'source_call_ABI_or_public_admission':False,'current0_2_or_full28_acceptance':False}
path=HERE/'actual-reconciliation-v3.json';path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');print(json.dumps(pin(path)))
