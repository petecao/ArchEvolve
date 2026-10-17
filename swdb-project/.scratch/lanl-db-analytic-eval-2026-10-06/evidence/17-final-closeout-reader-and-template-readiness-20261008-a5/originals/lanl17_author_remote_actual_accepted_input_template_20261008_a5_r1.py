"""SOURCE-ONLY prospective remote metadata author; NOT RUN.

Accepts a complete already parent-reviewed metadata template, validates its closed
schema and remote namespace, and preserves it byte-for-value in a new unsealed
JSON template. It neither reads any document's body nor runs Git, SWDB, selected
controls, providers, native processes, SSH or an auditor. Parent attestation is
not checked scientific evidence; the unchanged assembler and strict auditor
must inspect actual originals later. No placeholders/default approvals accepted.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import sys
import time

sys.dont_write_bytecode=True
R='5e12a9796432654d88def24ecea617d16ca605b2'
RT='1ab2c8ab147251391a4af75e637114bdd5b0ff27'
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5'
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5'
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(n) for n in range(1,5))
CAMPAIGNS=tuple(RAW+'/campaign-runs/extensa/'+cid for cid in CIDS)
EF='44652dd359e352480065f0c6281730dd61523ea6'
E11='8969d567599cb9f0d071f77936ab283fcb97c137'
E14='43256ee0300a59a03919833075fbb13fb3ba9ab3'
SPEC_PATH='/data1/yanruj/lanl17-custody-source-20261007-a3/spec-writer.py'
SPEC_SHA='339ea0dc1abb6778f0f016e9c03f2b29c5f1916154b668f5416747b2768a9231'
ASM_SHA='de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a'
AUD_SHA='6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
COL_SHA='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
P32='32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
M2_SHA='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'
M2_ID='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
POLICY='extensa-gem5-bfs-20261006-p1.agreement.5bae2f42d9078864'
MAX_METADATA=8*1024*1024
MAX_DOCUMENT=32*1024*1024
MAX_TOTAL=512*1024*1024
MAX_DOCUMENTS=4096
INPUT_FORMAT='swdb.lanl17-remote-actual-parent-template-author-input.v1'
TEMPLATE_FORMAT='swdb.lanl17-actual-input-construction-spec.v1'
ROOT_FIELDS={'freeze_export','report_export','manifest_M2','policy_id','report_id','prepare_supervisor','finalize_supervisor','prepare_preregistration','finalize_preregistration','freeze_publication_custody','final_ticket11_acceptance','final_ticket14_acceptance','collector_source_pin','collector_account','selected_records','campaigns'}
KNOWN={
'helper28d':('28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414',True),
'supervisorfa703':('fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0',False),
'guard9c5d':('9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6',False),
'collectorb08':(COL_SHA,True),
'cpu_reader8b':('8b85e34287a4dc67e5ff0c9a535aefd46a6c2ecf6051a934607f853074f90016',True),
'cpu_export1d1251':('1d1251baeba12c65c40a7a616060e5ff236197ce73f77335534d4a4d83fe32a6',True),
'generality_digest_b797':('b797a19f0d80a1a91b852a360c19e59beba4fa082ce88c38cbec029670e7deda',True),
'parent_capture':(P32,True),
'parent_input_specification':(SPEC_SHA,True),
'generality_reader':('6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570',True),
'generality_export':('928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e',True)}
ROLE_FAMILY={
'manifest_M2':'helper28d','freeze_receipt':'helper28d','agreement_receipt':'helper28d',
'attempt_dispatch':'helper28d','attempt_stopped':'helper28d',
'prepare_supervisor':'supervisorfa703','finalize_supervisor':'supervisorfa703',
'prepare_preregistration':'guard9c5d','finalize_preregistration':'guard9c5d',
'attempt_before':'collectorb08','attempt_after':'collectorb08',
'freeze_publication':'parent_capture','dispatch_state_corroboration':'parent_capture',
'attempt_release':'parent_capture','unclean_resume':'parent_capture','trajectory_projection':'parent_capture',
'outcome_refusal':'parent_capture','interrupted_selected_bodies':'parent_capture','public_candidate_selection':'parent_capture',
'ticket11_admission':'cpu_reader8b','ticket11_export_receipt':'cpu_export1d1251',
'ticket14_admission':'generality_reader','ticket14_export_receipt':'generality_export'}
PRIVATE={'.ssh','.aws','.codex','auth.json','state.json','prompt.txt','feedback.txt','provider.json'}

class Refused(ValueError):pass

def require(ok,code):
    if not ok:raise Refused(code)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def digest(value):return sha(canonical(value))
def exact(value,keys,code):
    require(type(value) is dict and set(value)==set(keys),code)
    return value

def token(value):
    require(type(value) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,256}',value) is not None,'explicit_public_token_required')
    require(not value.startswith(('ACTUAL_','FUTURE_','NOTRUN_','REQUIRED_')),'future_placeholder_refused')
    return value

def hexadecimal(value,n=64):
    require(type(value) is str and re.fullmatch('[0-9a-f]{'+str(n)+'}',value) is not None,'full_original_digest_required')
    return value

def remote_path(value):
    require(type(value) is str,'explicit_remote_path_string_required')
    p=PurePosixPath(value)
    require(p.is_absolute() and p.as_posix()==value and '..' not in p.parts and '\\' not in value and not PRIVATE.intersection(p.parts),'closed_public_remote_path_required')
    require(any(p.is_relative_to(PurePosixPath(prefix)) for prefix in ('/data/yanruj','/data1/yanruj')),'owned_remote_namespace_required')
    return p

def git_path(value):
    require(type(value) is str,'explicit_git_public_path_required')
    p=PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix()==value and value.startswith('swdb-project/') and '..' not in p.parts and '\\' not in value and not PRIVATE.intersection(p.parts),'closed_swdb_git_origin_required')
    return value

def strict_json(raw):
    def pairs(rows):
        value={}
        for k,v in rows:
            require(k not in value,'duplicate_json_key')
            value[k]=v
        return value
    def invalid(_):raise Refused('nonfinite_json_constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)

def structure(value,depth=0,counter=None):
    if counter is None:counter=[0]
    counter[0]+=1
    require(depth<=40 and counter[0]<=200000,'bounded_metadata_structure_required')
    if type(value) is dict:
        require(all(type(k) is str and len(k)<=4096 for k in value),'plain_bounded_metadata_keys_required')
        require('$future' not in value and 'required_actual_input' not in value,'typed_future_input_refused')
        for v in value.values():structure(v,depth+1,counter)
    elif type(value) is list:
        for v in value:structure(v,depth+1,counter)
    elif type(value) is str:
        require(len(value)<=65536 and not value.startswith(('ACTUAL_','FUTURE_','NOTRUN_','REQUIRED_')),'bounded_actual_metadata_string_required')
    else:require(value is None or type(value) in (int,bool) or type(value) is float and math.isfinite(value),'finite_plain_metadata_required')

def existing_private(path):
    p=Path(path)
    require(p.is_absolute() and '..' not in p.parts and all(not x.is_symlink() for x in (p,*p.parents)),'nonsymlink_existing_metadata_path_required')
    st=p.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid==os.getuid() and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_size<=MAX_METADATA,'owned_private_bounded_metadata_original_required')
    return p,st

def read_metadata(path,expected):
    p,st=existing_private(path)
    with p.open('rb') as f:
        require(os.fstat(f.fileno())==st,'metadata_fd_original_differs')
        raw=f.read(MAX_METADATA+1)
    require(p.lstat()==st and len(raw)==st.st_size and sha(raw)==hexadecimal(expected),'metadata_original_pin_differs')
    return p,raw,st

def validate_template(t):
    exact(t,('format','writer','parent_review','documents','root','forbidden_output_roots'),'exact_six_field_unsealed_template_required')
    require(t['format']==TEMPLATE_FORMAT,'selected_SPEC339_template_format_required')
    documents=t['documents'];require(type(documents) is dict and 0<len(documents)<=MAX_DOCUMENTS,'bounded_original_descriptor_inventory_required')
    root=exact(t['root'],ROOT_FIELDS,'exact_auditor_root_fields_required')
    refs={R,EF,E11,E14,hexadecimal(root['report_export']['commit'],40)}
    total=0
    for alias,d in documents.items():
        token(alias);require(type(d) is dict and 'role' in d,'closed_document_descriptor_required')
        role=d['role'];require(role in set(ROLE_FAMILY)|{'control_source','selected_record','original_unsealed_campaign_export'},'undeclared_private_or_raw_document_role_refused')
        fields={'role','origin','bytes','sha256'}
        if role in ROLE_FAMILY:fields|={'identity_sha256','canonical_ensure_ascii','expected_format','writer'}
        elif role=='selected_record':fields|={'id','kind','record_sha256'}
        exact(d,fields,'exact_original_document_fields_required')
        require(type(d['bytes']) is int and 0<=d['bytes']<=MAX_DOCUMENT,'original_document_32MiB_bound_required');total+=d['bytes']
        hexadecimal(d['sha256'])
        origin=d['origin'];require(type(origin) is dict and set(origin) in ({'path'},{'path','commit'}),'exact_original_origin_required')
        if 'commit' in origin:
            require(hexadecimal(origin['commit'],40) in refs,'unapproved_original_git_commit_refused');git_path(origin['path'])
        else:remote_path(origin['path'])
        if role in ROLE_FAMILY:
            hexadecimal(d['identity_sha256']);require(type(d['canonical_ensure_ascii']) is bool,'original_canonical_policy_boolean_required')
            require(type(d['expected_format']) is str and 0<len(d['expected_format'])<=256,'actual_original_expected_format_required')
        elif role=='selected_record':
            token(d['id']);token(d['kind']);hexadecimal(d['record_sha256']);require(origin['path'].endswith('.yaml'),'original_public_selected_YAML_required')
        elif role=='original_unsealed_campaign_export':
            require('commit' not in origin and origin['path'] in {RAW+'/export-'+cid+'.stdout' for cid in CIDS},'original_helper28_export_stdout_route_required')
    require(total<=MAX_TOTAL,'unchanged_original_total_512MiB_budget_required')
    def ref(value,role):
        exact(value,('$original_document',),'exact_original_reference_no_override_required');alias=token(value['$original_document'])
        require(alias in documents and documents[alias]['role']==role,'original_reference_role_differs');return documents[alias]
    def source(alias):
        token(alias);require(alias in documents and documents[alias]['role']=='control_source','writer_source_must_be_original_control_source');return documents[alias]
    def writer(w,family,policy):
        exact(w,('family','source','canonical_policy_sources','canonical_ensure_ascii','basis','parent_reviewed'),'closed_original_writer_source_policy_required')
        require(w['family']==family and w['basis']=='explicit_parent_source_review_of_original_canonical_hashing' and w['parent_reviewed'] is True,'actual_original_writer_source_review_required')
        require(type(w['canonical_ensure_ascii']) is bool and w['canonical_ensure_ascii']==policy==KNOWN[family][1] and source(w['source'])['sha256']==KNOWN[family][0],'immutable_selected_writer_policy_differs')
        policies=w['canonical_policy_sources'];require(type(policies) is list and 0<len(policies)<=8 and len(set(policies))==len(policies),'bounded_unique_original_policy_sources_required')
        policy_hashes={source(a)['sha256'] for a in policies}
        if family=='generality_export':require(KNOWN['generality_digest_b797'][0] in policy_hashes,'original_delegated_b797_canonical_policy_required')
        elif family not in ('generality_reader',):require(KNOWN[family][0] in policy_hashes,'selected_original_canonical_source_required')
    all_selected_ids=[d['id'] for d in documents.values() if d['role']=='selected_record']
    require(len(all_selected_ids)==len(set(all_selected_ids)),'original_selected_document_id_alias_refused')
    for d in documents.values():
        if d['role'] in ROLE_FAMILY:writer(d['writer'],ROLE_FAMILY[d['role']],d['canonical_ensure_ascii'])
    writer(t['writer'],'parent_input_specification',True)
    spec=source(t['writer']['source'])
    require(spec=={'role':'control_source','origin':{'path':SPEC_PATH},'bytes':11868,'sha256':SPEC_SHA} and t['writer']['canonical_policy_sources']==[t['writer']['source']],'exact_remote_SPEC339_self_source_binding_required')
    review=exact(t['parent_review'],('basis','source_C','estimator_sha256','final_R','assembler_sha256','auditor_sha256','collector_sha256','parent_approved_actual_inputs','fixtures_or_replays_allowed'),'closed_original_template_parent_review_required')
    require(review=={'basis':'explicit_parent_review_of_actual_original_inputs_and_selected_public_body_transfer','source_C':C,'estimator_sha256':F6,'final_R':{'commit':R,'tree':RT},'assembler_sha256':ASM_SHA,'auditor_sha256':AUD_SHA,'collector_sha256':COL_SHA,'parent_approved_actual_inputs':True,'fixtures_or_replays_allowed':False},'actual_frozen_parent_original_input_review_required')
    for field,role in (('manifest_M2','manifest_M2'),('prepare_supervisor','prepare_supervisor'),('finalize_supervisor','finalize_supervisor'),('prepare_preregistration','prepare_preregistration'),('finalize_preregistration','finalize_preregistration'),('freeze_publication_custody','freeze_publication'),('collector_source_pin','control_source')):ref(root[field],role)
    require(ref(root['collector_source_pin'],'control_source')['sha256']==COL_SHA and root['collector_account']=={'host':'mbit10','uid':114316761,'user':'yanruj'},'immutable_collector_account_source_required')
    m=ref(root['manifest_M2'],'manifest_M2')
    require(m['origin']=={'path':RAW+'/manifest.json'} and m['bytes']==292401 and m['sha256']==M2_SHA and m['identity_sha256']==M2_ID and m['expected_format']=='swdb.lanl17-parent-population.v1','actual_immutable_M2_descriptor_required')
    require(root['policy_id']==POLICY,'original_global_policy_required');token(root['report_id'])
    for field,role,commit in (('freeze_export','freeze_receipt',EF),('report_export','agreement_receipt',root['report_export']['commit'])):
        e=root[field];fields={'commit','tree','allowed_additions','record_paths','receipt'}
        if field=='freeze_export':fields|={'configuration_paths','provider_configuration_path','campaign_configuration_paths'}
        exact(e,fields,'closed_original_export_structure_required');require(e['commit']==commit,'actual_export_commit_required');hexadecimal(e['tree'],40)
        receipt=ref(e['receipt'],role);require(receipt['origin'].get('commit')==commit and receipt['origin']['path'].startswith('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/'),'original_export_receipt_Git_origin_required')
        for key in ('allowed_additions','record_paths'):
            require(type(e[key]) is list and e[key] and len(set(e[key]))==len(e[key]),'actual_unique_export_paths_required')
            for path in e[key]:git_path(path)
        require(all(path.startswith('swdb-project/records/') and path.endswith('.yaml') for path in e['record_paths']),'public_export_records_required')
        configs=e.get('configuration_paths',[])
        require(type(configs) is list and len(set(configs))==len(configs),'unique_export_config_paths_required')
        for path in configs:git_path(path)
        require(sorted(e['allowed_additions'])==sorted(e['record_paths']+[receipt['origin']['path']]+configs),'exact_original_export_additions_required')
        if field=='freeze_export':
            require(e['provider_configuration_path'] in configs and type(e['campaign_configuration_paths']) is dict and set(e['campaign_configuration_paths'])==set(CIDS) and set(e['campaign_configuration_paths'].values())<=set(configs),'actual_EF_config_mapping_required')
    for ticket,expected_export,family in ((11,E11,'cpu_reader8b'),(14,E14,'generality_reader')):
        d=root['final_ticket'+str(ticket)+'_acceptance'];fields={'accepted','receipt_identity','receipt_pin','actual_export_commit','actual_export_receipt_pin','actual_export_receipt_identity','selected_reader_source_sha256','reader_source_pin'}
        if ticket==14:fields.add('final_source_commit')
        exact(d,fields,'closed_actual_dependency_acceptance_required');require(d['accepted'] is True and d['actual_export_commit']==expected_export,'actual_original_dependency_parent_acceptance_required')
        receipt=ref(d['receipt_pin'],'ticket'+str(ticket)+'_admission');export=ref(d['actual_export_receipt_pin'],'ticket'+str(ticket)+'_export_receipt');reader=ref(d['reader_source_pin'],'control_source')
        require(receipt['identity_sha256']==d['receipt_identity'] and export['identity_sha256']==d['actual_export_receipt_identity'] and reader['sha256']==d['selected_reader_source_sha256']==KNOWN[family][0] and receipt['writer']['source']==d['reader_source_pin']['$original_document'],'actual_dependency_reader_receipt_seams_required')
        require(export['origin'].get('commit')==expected_export,'original_dependency_export_Git_origin_required')
        if ticket==14:require(d['final_source_commit']=='c4ab2fdbb0b0c57ee9f515522835897f24466d6b','original_actual_ticket14_source_required')
    selected=root['selected_records'];require(type(selected) is list and selected,'original_selected_body_list_required')
    ids=[ref(x,'selected_record')['id'] for x in selected];require(len(ids)==len(set(ids)),'selected_record_id_alias_refused')
    rows=root['campaigns'];require(type(rows) is list and len(rows)==4 and {r['campaign'] for r in rows}==set(CIDS),'exact_four_actual_campaigns_required')
    for row in rows:
        required={'campaign','projection','attempts','public_candidate_exports','public_candidate_export_selection_custody'}
        require(type(row) is dict and required<=set(row)<=required|{'interrupted_selected_body_custody'},'closed_campaign_fields_required')
        ref(row['projection'],'trajectory_projection');ref(row['public_candidate_export_selection_custody'],'public_candidate_selection')
        if 'interrupted_selected_body_custody' in row:ref(row['interrupted_selected_body_custody'],'interrupted_selected_bodies')
        exports=row['public_candidate_exports'];require(type(exports) is list,'actual_export_list_not_future_required')
        for export in exports:ref(export,'original_unsealed_campaign_export')
        require(type(row['attempts']) is list and 0<len(row['attempts'])<=256,'bounded_actual_attempt_history_required')
        for attempt in row['attempts']:
            roles={'dispatch':'attempt_dispatch','stopped':'attempt_stopped','release_custody':'attempt_release','before_custody':'attempt_before','after_custody':'attempt_after','dispatch_state_corroboration':'dispatch_state_corroboration'}
            exact(attempt,roles,'closed_actual_attempt_custody_fields_required')
            for field,role in roles.items():ref(attempt[field],role)
    forbidden=t['forbidden_output_roots'];require(type(forbidden) is list and forbidden and len(set(forbidden))==len(forbidden),'explicit_unique_forbidden_roots_required')
    paths={str(remote_path(p)) for p in forbidden}
    require({S,RAW,*CAMPAIGNS}<=paths,'whole_source_raw_campaign_output_exclusions_required')
    return paths

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--input-sha256',required=True)
    parser.add_argument('--author-sha256',required=True);parser.add_argument('--parent-review-sha256',required=True)
    parser.add_argument('--metadata-deadline-seconds',type=int,required=True);parser.add_argument('--output-directory',required=True)
    args=parser.parse_args();require(60<=args.metadata_deadline_seconds<=120,'explicit_60_to_120_second_metadata_deadline_required')
    require(sys.platform=='linux' and os.getuid()==os.geteuid()==114316761,'actual_remote_uid_platform_required')
    deadline=time.monotonic()+args.metadata_deadline_seconds
    def alarm_handler(_signum,_frame):raise Refused('finite_metadata_deadline_exceeded')
    old=signal.signal(signal.SIGALRM,alarm_handler);signal.alarm(args.metadata_deadline_seconds)
    try:
        own,own_raw,own_stat=read_metadata(__file__,args.author_sha256)
        source_pin={'path':str(own),'bytes':len(own_raw),'sha256':sha(own_raw)}
        original,raw,original_stat=read_metadata(args.input,args.input_sha256);value=strict_json(raw);structure(value)
        exact(value,('format','template','parent_review','namespace','output_directory','metadata_deadline_seconds'),'closed_remote_template_author_input_required')
        require(value['format']==INPUT_FORMAT and value['metadata_deadline_seconds']==args.metadata_deadline_seconds and value['output_directory']==args.output_directory,'exact_actual_author_input_command_binding_required')
        namespace=exact(value['namespace'],('repository','source_root','spec_writer_path','campaign_roots'),'closed_actual_remote_execution_namespace_required')
        require(namespace=={'repository':S,'source_root':S,'spec_writer_path':SPEC_PATH,'campaign_roots':list(CAMPAIGNS)},'immutable_remote_namespace_required')
        review=exact(value['parent_review'],('basis','author_source_sha256','template_semantic_sha256','namespace_semantic_sha256','actual_originals_parent_reviewed','remote_namespace_parent_reviewed','selected_public_body_scope_parent_reviewed','future_placeholders_allowed','reviewed_utc'),'closed_actual_author_parent_review_required')
        require(review['basis']=='explicit_parent_review_of_actual_original_metadata_and_remote_template_namespace' and review['author_source_sha256']==sha(own_raw) and review['template_semantic_sha256']==digest(value['template']) and review['namespace_semantic_sha256']==digest(namespace) and digest(review)==hexadecimal(args.parent_review_sha256),'exact_actual_parent_review_digest_required')
        require(all(review[k] is True for k in ('actual_originals_parent_reviewed','remote_namespace_parent_reviewed','selected_public_body_scope_parent_reviewed')) and review['future_placeholders_allowed'] is False,'actual_parent_review_required_no_future_or_default_approval')
        checked=datetime.datetime.fromisoformat(review['reviewed_utc'].replace('Z','+00:00'))
        require(checked.tzinfo is not None and checked<=datetime.datetime.now(datetime.timezone.utc),'actual_review_time_required')
        forbidden=validate_template(value['template'])
        output=remote_path(args.output_directory);require(all(not output.is_relative_to(PurePosixPath(root)) for root in forbidden),'fresh_author_output_outside_all_source_raw_campaign_roots_required')
        destination=Path(str(output));parent=destination.parent
        require(not destination.exists() and not destination.is_symlink() and all(not p.is_symlink() for p in (parent,*parent.parents)),'fresh_nonsymlink_author_output_required')
        pst=parent.stat();require(stat.S_ISDIR(pst.st_mode) and pst.st_uid==os.getuid() and stat.S_IMODE(pst.st_mode)==0o700,'actual_owned_private_existing_output_parent_required')
        template_raw=(json.dumps(value['template'],indent=2,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode()
        require(len(template_raw)<=MAX_METADATA and 'identity_sha256' not in value['template'],'bounded_UNSEALED_template_required')
        custody={'format':'swdb.lanl17-remote-actual-parent-template-author-custody.v1','written_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'metadata_template_authored_for_parent_review_not_original_admission','scientific_admission':False,'author_source_pin':source_pin,'original_author_input_pin':{'path':str(original),'bytes':len(raw),'sha256':sha(raw)},'parent_review_sha256':digest(review),'template_semantic_sha256':digest(value['template']),'namespace':namespace,'new_unsealed_template_pin':{'path':str(destination/'parent-template.json'),'bytes':len(template_raw),'sha256':sha(template_raw)},'original_document_or_record_bodies_read':0,'Git_SWDB_control_provider_native_SSH_auditor_actions':0,'template_facts_generated_or_original_inputs_rewritten':False,'canonical_ensure_ascii':True}
        custody['identity_sha256']=digest(custody);custody_raw=(json.dumps(custody,indent=2,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode();require(len(custody_raw)<=MAX_METADATA,'bounded_author_custody_required')
        require(read_metadata(str(original),sha(raw))[1]==raw and read_metadata(str(own),sha(own_raw))[1]==own_raw and time.monotonic()<deadline and parent.stat()==pst,'original_metadata_source_parent_unchanged_before_publication')
        destination.mkdir(mode=0o700)
        for filename,body in (('parent-template.json',template_raw),('author-custody.json',custody_raw)):
            fd=os.open(destination/filename,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
        dfd=os.open(destination,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
        try:os.fsync(dfd)
        finally:os.close(dfd)
        for filename,body in (('parent-template.json',template_raw),('author-custody.json',custody_raw)):
            require(read_metadata(str(destination/filename),sha(body))[1]==body,'exact_new_metadata_output_readback_required')
        require(time.monotonic()<deadline,'finite_metadata_publication_deadline_required')
        print(json.dumps({'format':custody['format'],'state':custody['state'],'template_pin':custody['new_unsealed_template_pin'],'custody_pin':{'path':str(destination/'author-custody.json'),'bytes':len(custody_raw),'sha256':sha(custody_raw),'identity_sha256':custody['identity_sha256'],'canonical_ensure_ascii':True},'scientific_admission':False},sort_keys=True,allow_nan=False))
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)

if __name__=='__main__':
    try:main()
    except (Refused,KeyError,TypeError,ValueError,OSError,OverflowError,RecursionError) as error:
        print(json.dumps({'format':'swdb.lanl17-remote-actual-parent-template-author-refusal.v1','state':'refused','error_class':type(error).__name__,'scientific_admission':False},sort_keys=True),file=sys.stderr)
        raise SystemExit(3)
