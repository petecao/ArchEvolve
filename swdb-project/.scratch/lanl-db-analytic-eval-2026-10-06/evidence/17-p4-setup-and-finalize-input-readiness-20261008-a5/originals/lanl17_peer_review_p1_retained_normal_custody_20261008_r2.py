"""Independent P1 local metadata-only review; no project/control imports or remote work."""
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat

BASE = Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
ARCHIVE = BASE / '17-p1-normal-stop-release-after-20261008-a5'
CID = 'extensa-gem5-bfs-20261006-p1'
R = '5e12a9796432654d88def24ecea617d16ca605b2'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
M2 = '66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
H = '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
B08 = 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
P32 = '32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
checks = []
pins = {}

def require(condition, label):
    if not condition:
        raise ValueError(label)
    checks.append(label)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def semantic(value):
    return digest(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())

def timestamp(value):
    dt=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    require(dt.tzinfo is not None,'timezone_aware_original_time:'+value)
    return dt

def file_pin(path):
    path=Path(path)
    st=path.lstat()
    require(stat.S_ISREG(st.st_mode) and not path.is_symlink() and st.st_nlink==1,'regular_nonsymlink_single_link:'+path.name)
    require(st.st_size<=16*1024*1024,'bounded_retained_file:'+path.name)
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        require(os.fstat(stream.fileno())==st,'same_original_fd_stat:'+path.name)
        while True:
            block=stream.read(1024*1024)
            if not block:break
            hasher.update(block)
    require(path.lstat()==st,'unchanged_original_stat:'+path.name)
    return {'path':str(path),'bytes':st.st_size,'sha256':hasher.hexdigest()}

def read(label,path,sealed=True):
    pin=file_pin(path);pins[label]=pin
    require(pin['bytes']<=8*1024*1024,'bounded_compact_json:'+label)
    value=json.loads(Path(path).read_bytes())
    require(file_pin(path)==pin,'same_original_readback:'+label)
    if sealed:
        require(value['identity_sha256']==semantic({k:v for k,v in value.items() if k!='identity_sha256'}),'original_canonical_true_identity:'+label)
    return value

# Original archive continuity is checked by hashes only. Diagnostic contents are not parsed or emitted.
inv_path=ARCHIVE/'original-inventory.json'
inv=read('archive_inventory',inv_path,False)
archive_rows={row['source']:row for row in inv['files']}
verified_archive=[]
for row in inv['files']:
    source=file_pin(row['source']); archived=file_pin(ARCHIVE/row['archive'])
    require(source['bytes']==archived['bytes']==row['bytes'] and source['sha256']==archived['sha256']==row['sha256'],'source_archive_exact_bytes:'+row['archive'])
    verified_archive.append({'archive':row['archive'],'bytes':row['bytes'],'sha256':row['sha256']})

before=read('before','/private/tmp/lanl17-p1-before-capture-20261008-a5/custody.json')
dispatch=read('dispatch','/private/tmp/lanl17-p1-dispatch-original-collect-capture-20261008-a5/dispatch-preregistration.json')
corroboration=read('dispatch_state32','/private/tmp/lanl17-p1-dispatch-state-capture-20261008-a5/dispatch-state-custody.json')
request=read('release_request','/private/tmp/lanl17-p1-release-request-finalized-20261008-a5.json')
release=read('release32','/private/tmp/lanl17-p1-release32-capture-20261008-a5/lanl17-p1-release-custody-20261008-a5.json')
after=read('after','/private/tmp/lanl17-p1-after-capture-20261008-a5/custody.json')
terminal=Path('/private/tmp/lanl17-p1-terminal-originals-capture-20261008-a5-r2/decoded-originals')
stop=read('stopped',terminal/'stopped-receipt.json')
lane=read('lane',terminal/'lane.json',False)['socket_lane']
for name in ('runner.exit-code.txt','wrapper.exit-code.txt'):
    pins[name]=file_pin(terminal/name)
    require((terminal/name).read_bytes()==b'0\n','exact_original_zero_exit:'+name)
for label in ('after','release32','release_request','stopped','lane','runner.exit-code.txt','wrapper.exit-code.txt'):
    row=archive_rows[pins[label]['path']]
    require((row['bytes'],row['sha256'])==(pins[label]['bytes'],pins[label]['sha256']),'selected_pin_in_retained_archive:'+label)

for name,value in (('before',before),('after',after)):
    require(value['format']=='swdb.lanl17-attempt-control-custody.v2' and value['phase']==name,'original_b08_phase_format:'+name)
    require(value['source_commit']==R and value['source_clean'] is True and value['estimator_sha256']==F6 and value['manifest_identity_sha256']==M2,'immutable_source_manifest:'+name)
    require(value['helper_sha256']==H and value['collector_sha256']==B08,'selected_source_controls:'+name)
    require(value['campaign']==CID and value['attempt']==1 and value['resume'] is False and value['baselines_only'] is False,'original_substantive_attempt:'+name)
    require(value['execution_account']['uid']==value['execution_account']['effective_uid']==114316761 and value['execution_account']['user']=='yanruj' and value['execution_account']['host']=='mbit10','original_execution_account:'+name)
    require(value['raw_state_snapshots_transferred'] is False and value['provider_prompts_auth_logs_argv_read'] is False,'original_privacy_contract:'+name)
require(before['state']=={'present':False,'file':None,'projection':None},'original_new_attempt_no_preexisting_state')
require(dispatch['source_commit']==R and dispatch['estimator_sha256']==F6 and dispatch['campaign']==CID and dispatch['attempt']==1 and dispatch['node']==0 and dispatch['resume'] is False and dispatch['baselines_only'] is False,'original_dispatch_identity_context')
require(dispatch['limits']=={'child_s':87000,'disk_gb':20,'iterations':8,'lane_hours':24,'outer_s':88200,'plateau':4},'original_scientific_limits_preserved')
require(before['policy']==dispatch['policy']==stop['policy']==after['policy']==request['context']['policy'],'same_original_frozen_policy')
require(corroboration['source_commit']==R and corroboration['before_identity_sha256']==before['identity_sha256'] and corroboration['dispatch_identity_sha256']==dispatch['identity_sha256'],'original_dispatch_state32_links')
require(corroboration['state_unchanged_under_parent_exclusive_campaign_ownership'] is True and corroboration['parent_capture_provenance']['producer_sha256']==P32,'original_dispatch_state32_declared_parent_exclusivity_not_new_observation')
require(lane['lease_generation']==511 and lane['lease_name']=='mbit10-evaluation-node0' and lane['node']==0 and lane['job']=='swdb-lanl17-20261007-a5-p1-a1' and lane['exit_code']==0 and 'record_errors' not in lane,'original_native_lane_generation511_zero_exit')
require(stop['source_commit']==R and stop['source_clean_after'] is True and stop['estimator_sha256_after']==F6 and stop['runner_exit_code']==stop['public_exit_code']==0,'original_clean_normal_stop')
require(not stop['infrastructure_error'] and not stop['process_cleanup']['survivors'],'original_no_infrastructure_error_owned_survivor')
require(timestamp(lane['started_utc'])<=timestamp(stop['started_utc'])<timestamp(stop['ended_utc'])<timestamp(lane['ended_utc'])+datetime.timedelta(seconds=1),'native_whole_second_precision_stop_bracket')
require(after['before_identity_sha256']==before['identity_sha256'] and after['dispatch_identity_sha256']==dispatch['identity_sha256'] and after['stopped_identity_sha256']==stop['identity_sha256'],'after_exact_original_custody_links')
require(after['released']==release and release['source_commit']==R and release['campaign']==CID and release['attempt']==1 and release['lease_generation']==511 and release['node']==0 and release['lease_released'] is True,'after_embedded_exact_original_release32')
require(release['dispatch_identity']==dispatch['identity_sha256'] and release['stopped_identity']==stop['identity_sha256'] and release['runner_exit_code']==release['public_exit_code']==release['wrapper_exit_code']==0,'release32_original_attempt_exit_links')
require(release['lane_record_sha256']==pins['lane']['sha256'] and release['wrapper_exit_file_sha256']==pins['wrapper.exit-code.txt']['sha256'],'release32_original_file_links')
provenance=release['parent_capture_provenance']
require(provenance['producer_sha256']==P32 and provenance['capture_request_file_sha256']==pins['release_request']['sha256'] and provenance['capture_request_identity_sha256']==request['identity_sha256'] and provenance['canonical_ensure_ascii'] is True,'release32_exact_producer_request_provenance')
require(provenance['original_inputs']==request['inputs'] and provenance['observations_sha256']==semantic(request['observations']),'release32_exact_input_observation_provenance')
require(all(request['context'][key]==value for key,value in provenance['context_pins'].items()),'release32_documented_context_subset')

projection=after['state']['projection'];ledger=projection['ledger'];iterations=projection['iterations']
require(after['state']['present'] is True and isinstance(after['state']['original_remote_only'],dict) and after['state']['original_remote_only']['sha256']==after['state']['file']['sha256'] and after['state']['original_remote_only']['bytes']==after['state']['file']['bytes'] and projection['campaign']==CID and projection['stopped'] is True and projection['stop_reason']=='plateau' and projection['setup_done'] is True and not projection['pauses'],'retained_normal_plateau_state_no_resume')
require(ledger['iterations_completed']==ledger['plateau']==4 and len(ledger['iterations'])==len(iterations)==4,'four_substantive_completed_iterations')
require(all(row['outcome']=='not_improved' and row['advanced_plateau'] is True and row['plateau_counter']==row['index'] for row in ledger['iterations']),'four_original_plateau_advances')
require(sum(len(row['candidates']) for row in iterations)==8 and all(timestamp(row['started'])<timestamp(row['ended']) for row in iterations),'eight_actual_proposal_rows_in_completed_iterations')
calls=ledger['calls'];bridge=projection['setup_calls']+[call for row in iterations for call in row['provider_calls']]
require(len(calls)==len({row['invocation'] for row in calls})==9 and all(row['outcome']=='completed' and row['counted'] is True for row in calls),'nine_distinct_counted_completed_provider_calls')
fields=('role','invocation','outcome','counted')
require([{k:row[k] for k in fields} for row in calls]==[{k:row[k] for k in fields} for row in bridge],'exact_setup_iteration_provider_ledger_bridge')
provider_inventory=after['invocation_inventory']['provider_directories']
require({row['invocation'] for row in provider_inventory}=={row['invocation'] for row in calls} and all(row['provider_receipt_present'] is True for row in provider_inventory),'existence_inventory_matches_calls_no_raw_provider_read')

native_times={};native_original_pin=None;terminal_stat_pins=None
for suffix in ('before32','before-after','after-after'):
    observation=read('native_'+suffix,'/private/tmp/lanl17-p1-native-release-query-capture-'+suffix+'-20261008-a5/native-observation-original.json',False)
    require(observation['format']=='swdb.lanl17-native-release-readonly-observation.v1' and observation['sealed'] is False and observation['point_in_time_only'] is True and observation['scientific_admission'] is False,'explicit_dated_unsealed_native_observation:'+suffix)
    require(observation['required_generation']==511 and observation['release_ready'] is True and observation['normal_exit_set_only'] is True and not observation['unknown_reasons'] and not observation['not_ready_reasons'],'original_known_normal_release_ready:'+suffix)
    native=observation['native_metadata'];raw=base64.b64decode(native['raw_base64'],validate=True);native_value=json.loads(raw)
    require(native['state']=='released' and native['generation']==511 and digest(raw)==native['original_file_pin']['sha256'] and len(raw)==native['original_file_pin']['bytes'],'exact_original_native_metadata_pin:'+suffix)
    require(native_value['state']=='released' and native_value['active_session'] is None and native_value['lease']['generation']==511,'native_original_released_no_active_session:'+suffix)
    if native_original_pin is None:native_original_pin=native['original_file_pin']
    else:require(native_original_pin==native['original_file_pin'],'native_original_full_stat9_and_bytes_unchanged:'+suffix)
    require(all(not observation[k]['matching_rows'] for k in ('kernel_locks_before','kernel_locks_after')) and all(observation[k]['FD9_matches_selected_lease'] is False for k in ('daemon_before','daemon_after')),'no_selected_kernel_lock_or_daemonFD9_in_original_observation:'+suffix)
    actual={}
    for filename,metadata in observation['attempt_metadata'].items():
        original=metadata['original_file_pin'];local=file_pin(terminal/filename)
        require(local['bytes']==original['bytes'] and local['sha256']==original['sha256'],'unchanged_terminal_original_byte_pin:'+suffix+':'+filename)
        require(set(original['stat'])=={'dev','ino','mode','uid','gid','size','mtime_ns','ctime_ns','nlink'} and stat.S_ISREG(original['stat']['mode']) and original['stat']['uid']==114316761 and original['stat']['nlink']==1 and original['stat']['size']==original['bytes'],'terminal_original_stat9_owned_regular:'+suffix+':'+filename)
        actual[filename]=original
    if terminal_stat_pins is None:terminal_stat_pins=actual
    else:require(actual==terminal_stat_pins,'terminal_stat9_and_byte_continuity:'+suffix)
    require(observation['original_exits']=={'lane':0,'public':0,'runner':0,'wrapper':0},'normal_complete_original_exit_set:'+suffix)
    native_times[suffix]=timestamp(observation['checked_utc'])
require(timestamp(stop['ended_utc'])<=native_times['before32']<=timestamp(release['checked_utc'])<=native_times['before-after']<=timestamp(after['checked_utc'])<=native_times['after-after'],'historical_native_release32_after_no_reuse_chronology')
for name,folder in (('terminal',terminal.parent),('release32',Path(pins['release32']['path']).parent),('after',Path(pins['after']['path']).parent)):
    transport=read(name+'_transport',folder/'transport.json',False)
    require(transport['SSH_exit_code']==0 and transport['error_type'] is None and transport['remote_completion_not_inferred'] is True,'original_transport_success_not_remote_completion_inference:'+name)
    for stream in ('stdout','stderr'):
        actual=file_pin(folder/stream)
        require(transport['private_original_streams'][stream]=={k:actual[k] for k in ('bytes','sha256')},'transport_exact_stream_pin_only:'+name+':'+stream)

# No root verdict was needed for these checks. Bind its exact file for subsequent parent pin choice only.
root_review=file_pin('/private/tmp/lanl17-p1-normal-custody-root-rereview-20261008-r1.json')
require(root_review['bytes']==17534 and root_review['sha256']=='60520c58326d20ed2b74846e444aab4fe31deb1d136c419351f41b1dae504615','identified_root_review_not_used_as_primary_evidence')
result={'format':'swdb.lanl17-retained-original-normal-custody-peer-rereview.v1',
        'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'PASS',
        'campaign':CID,'attempt':1,'native_generation':511,'normal_terminal':'plateau4',
        'iterations_completed':4,'candidate_rows':8,'completed_counted_provider_calls':9,
        'root_review_pin':root_review,'independent_original_checks':checks,'original_pins':pins,
        'archive_hash_only_checked_files':verified_archive,'review_source_pin':file_pin(__file__),
        'current_lane_clearance':False,'scientific_admission':False,'numerical_pair_or_D30_admission':False,
        'remote_actions':0,'custody_repeated':False,'project_or_control_imports':0,'raw_state_summary_provider_bodies_read':False,
        'scope':'Fresh independent local review of retained original historical P1 terminal/release32/AFTER/native observations and original source/control links only. Dated generation511 release evidence through original AFTER; not current mbit10 readiness, final strict6a readiness, scientific completion, or a resumed attempt. Archive diagnostics are hashed without parsing/emitting their content.'}
raw=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
out=Path('/private/tmp/lanl17-p1-normal-custody-peer-rereview-20261008-r2.json')
fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as stream:stream.write(raw)
print(str(out),len(raw),digest(raw),len(checks),'PASS')
