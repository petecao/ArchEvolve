"""Local read-only reconciliation of original actual metadata; no selected main."""
import datetime,hashlib,json,pathlib
P=pathlib.Path
def require(v,s):
 if not v:raise ValueError(s)
def digest(v,ascii=True):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=ascii).encode()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def original_seal(v,ascii):
 require(v['identity_sha256']==digest({k:x for k,x in v.items() if k!='identity_sha256'},ascii),'original seal policy')
local=P('/private/tmp/lanl14-reader-ssh-capture-20261008-a1'); remote=P('/private/tmp/lanl14-reader-actual-originals-20261008-a1')
lp=load(local/'preregistration.json');ls=load(local/'status.json');co=load(local/'stdout')
pr=load(remote/'remote-reader-preregistration.json');sr=load(remote/'remote-reader-receipt.json');cl=load(remote/'remote-reader-cleanup.json');ad=load(remote/'remote-reader-stdout.json')
tr=load(P('/private/tmp/lanl14-reader-actual-postflight-originals-transfer-20261008-a1.json'))
ex=load(P('/private/tmp/lanl14-reviewed-export-r5-actual-20261008-a1/remote-pure-E-receipt.json'))
original_seal(sr,False);original_seal(ad,True);original_seal(ex,True)
require(sr['canonical_ensure_ascii'] is False and 'canonical_ensure_ascii' not in ad and 'admitted' not in ad,'original policy and result shape')
require(ls['SSH_exit_code']==0 and ls['timed_out'] is False and ls['signal_received'] is None and ls['failure_type'] is None and ls['source_unchanged'] is True,'local lifecycle')
require(sr['state']=='child_returned' and sr['child_exit']==sr['returned_child_exit']==sr['supervisor_exit']==0 and sr['timed_out'] is False and sr['signal_received'] is None and sr['error_type'] is None and sr['cleanup_errors']==[] and sr['fixture'] is False and sr['supervision_success'] is True,'remote lifecycle')
require(sr['scientific_admission'] is False and sr['child_scientific_result_assessed'] is False and sr['cleanup']['subreaper'] is True and sr['cleanup']['survivor_count']==0 and cl=={'subreaper':True,'terminated_owned_processes':[],'survivors':{}},'original cleanup')
require(co['receipt_sha256']==hashlib.sha256((remote/'remote-reader-receipt.json').read_bytes()).hexdigest() and co['identity_sha256']==sr['identity_sha256'] and co['supervisor_exit']==0 and co['cleanup_survivor_count']==0,'local original summary')
require(sr['cleanup']['original_private_cleanup']=={'sha256':hashlib.sha256((remote/'remote-reader-cleanup.json').read_bytes()).hexdigest(),'bytes':79},'original cleanup hash')
av=pr['public_argv'];tail=av[av.index('--')+1:];child=['/usr/bin/python3.12','-B',av[av.index('--selected-source')+1],*tail]
require(sr['argv_sha256']==digest(child,False) and sr['timeout_s']==14400 and pr['GNU_outer_s']==14520 and pr['GNU_KILL_s']==60 and lp['outer_seconds']==16500 and lp['metadata_preflight_s']==lp['metadata_postflight_reserve_s']==600,'unchanged original invocation caps')
for n in ('stdout','stderr'):
 p=remote/('remote-reader-stdout.json' if n=='stdout' else 'remote-reader-stderr');raw=p.read_bytes()
 require(sr['original_private_streams'][n]=={'bytes':len(raw),'mode':384},'remote original stream')
 require(hashlib.sha256(raw).hexdigest()==tr['originals'][p.name]['pin']['sha256'],'transfer exact bytes')
 require((local/n).stat().st_size==ls['original_private_streams'][n]['bytes'] and hashlib.sha256((local/n).read_bytes()).hexdigest()==ls['original_private_streams'][n]['sha256'],'local stream exact bytes')
require((remote/'remote-reader-stderr').read_bytes()==b'' and (local/'stderr').read_bytes()==b'','genuine empty streams')
require(pr['expected_primary']=='a9c02e918374070ff2654e3f9696bd550230cbbb' and pr['export_commit']==ad['export_commit']=='43256ee0300a59a03919833075fbb13fb3ba9ab3' and pr['source_commit']==ad['final_source_commit']=='c4ab2fdbb0b0c57ee9f515522835897f24466d6b','actual graph pins')
require(ad['format']=='swdb.lanl14-selected-nine-export-admission.v1' and ad['source_clean'] is True and ad['prior_tracked_blobs_unchanged'] is True and ad['new_canonical_records']==18,'selected actual admission')
require(ad['receipt_file_sha256']=='02b369f0624964fa4293f563a7b51e142dc369101147ac7fe848503c4b50eb5d' and ad['receipt_identity_sha256']==ex['identity_sha256'] and ad['report_identity_sha256']==ex['report_transfer']['report_identity_sha256'],'E receipt/report')
require(ad['report_transfer']==ex['report_transfer'] and ad['estimator_sha256']==pr['F6']==sr['estimator_sha256']=='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3' and sr['estimator_modules']==185,'same bundle and transfer')
require(ad['provider_calls']==ad['application_timings']==ad['reader_native_compiler_provider_remote_actions']==0 and ad['full_catalogue_validation']=='OK: 704 record(s) valid','inherited public validation and no new science')
require(ad['direct_observations']['lane_exit_code']==0 and ad['direct_observations']['cleanup_survivors']=={} and ad['direct_observations']['runner_acceptance_identity_sha256']=='2c11ad81b02524e325b7e1b3fed3061e37ef832f7fa979c08b2c24151774e81b','original run admission')
expected=[('bfs','dx100'),('bfs','cpu'),('bc','cpu'),('pagerank','cpu'),('pagerank','dx100'),('pagerank','maple'),('bfs','maple'),('bc','maple'),('bc','dx100')]
require([(p['kernel'],p['target']) for p in ad['pairs']]==expected,'nine exact pairs')
targets={'cpu':'9fec46b1ab4c8ac2e8e501e61cf137c075ec40b6eef128a247cf28dd54fca76b','dx100':'f436047a21f77eda649f99aa5ceb5b5c8cb13e4ab7eed770441e7faad07aaf02','maple':'74face99dcf178f0c9d7e057b77a840245fff0f2f33e500db677516cbd3ee7e8'}
for p in ad['pairs']:
 require(p['trials']==5 and len(p['trial_regions'])==5 and p['threads']=={'cpu':1,'dx100':4,'maple':2}[p['target']] and p['ratio'] is None and p['error_band'] is None and p['estimate_only']==(p['target']=='maple') and p['configuration_pins']['target_description_sha256']==targets[p['target']],'pair scoped disclosures')
 expected_seconds={('bfs','cpu'):0.08459283293734217,('bc','cpu'):0.64771215194357}.get((p['kernel'],p['target']))
 require(p['seconds']==expected_seconds,'no invented whole call value')
 require(set(p['configuration_pins'])=={'characterization_sha256','counted_payload_sha256','source_ir_sha256','observation_contract_sha256','build_flags_sha256','source_identity_sha256','target_description_sha256','observation_policy_sha256','roi','run_arguments_sha256'},'complete original configuration pins')
require(tr['postflight']['all_checks_passed'] is True and tr['postflight']['selected_owned_processes']==[] and tr['postflight']['visibility_errors']==[],'separate actual postflight')
out={'format':'swdb.lanl14-parent-original-reader-actual-assessment.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_accepts_selected_nine_actual_admission':True,'original_reader_identity_sha256':ad['identity_sha256'],'original_reader_file_sha256':hashlib.sha256((remote/'remote-reader-stdout.json').read_bytes()).hexdigest(),'original_supervisor_identity_sha256':sr['identity_sha256'],'original_supervisor_scientific_admission_false_preserved':True,'original_result_no_admitted_field':True,'original_defaultTrue_and_explicitFalse_seals_verified':True,'local_SSH_and_remote_supervisor_and_child_exit':0,'timed_out':False,'survivors':{},'postflight_checked_utc':tr['checked_utc'],'postflight_file_sha256':hashlib.sha256(P('/private/tmp/lanl14-reader-actual-postflight-originals-transfer-20261008-a1.json').read_bytes()).hexdigest(),'export_commit':ad['export_commit'],'source_commit':ad['final_source_commit'],'F6':ad['estimator_sha256'],'canonical_records':704,'new_records':18,'nine_pairs':9,'trials':45,'scientific_accuracy_or_measured_speedup_claimed':False,'provider_calls_and_application_timings':0,'pure_E_prior_parent_graph_and_22_additions_acceptance_inherited':True}
out['identity_sha256']=digest(out,True)
path=P('/private/tmp/lanl14-reader-original-actual-parent-assessment-20261008-a1.json')
with path.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out,indent=2))
