"""2026-10-08 ET: fresh local review of retained originals, no remote/control execution."""
import base64, datetime, hashlib, json, os
from pathlib import Path

ROOT = Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
R = '5e12a9796432654d88def24ecea617d16ca605b2'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
M2 = '66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'

def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(d): return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def utc(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def pin(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':digest(b)}

for n, generation, calls_expected in ((1,511,9),(2,512,7)):
    checks=[]; originals={}; cid=f'extensa-gem5-bfs-20261006-p{n}'
    def check(ok,label):
        if not ok: raise ValueError(f'p{n}: {label}')
        checks.append(label)
    inventory=json.loads((ROOT/f'17-p{n}-normal-stop-release-after-20261008-a5/original-inventory.json').read_bytes())
    for row in inventory['files']:
        b=Path(row['source']).read_bytes(); archived=(ROOT/f'17-p{n}-normal-stop-release-after-20261008-a5'/row['archive']).read_bytes()
        check(b==archived and len(b)==row['bytes'] and digest(b)==row['sha256'],'exact_archived_original:'+row['archive'])
    def read(label,path,sealed=True):
        p=Path(path); originals[label]=pin(p); d=json.loads(p.read_bytes())
        if sealed: check(digest(canonical({k:v for k,v in d.items() if k!='identity_sha256'}))==d['identity_sha256'],label+':canonical_true_seal')
        return d
    after=read('after',f'/private/tmp/lanl17-p{n}-after-capture-20261008-a5/custody.json')
    release=read('release',f'/private/tmp/lanl17-p{n}-release32-capture-20261008-a5/lanl17-p{n}-release-custody-20261008-a5.json')
    request=read('request',f'/private/tmp/lanl17-p{n}-release-request-finalized-20261008-a5.json')
    dispatch=read('dispatch',f'/private/tmp/lanl17-p{n}-dispatch-original-collect-capture-20261008-a5/dispatch-preregistration.json')
    before_paths={row['source'] for row in inventory['files'] if f'p{n}-before-capture-' in row['source'] and row['source'].endswith('/custody.json')}
    # BEFORE and dispatch may be in the earlier immutable dispatch archive.
    before=read('before',next(iter(before_paths)) if before_paths else f'/private/tmp/lanl17-p{n}-before-capture-20261008-a5/custody.json')
    terminal_paths=[row['source'] for row in inventory['files'] if row['source'].endswith('/stopped-receipt.json')]
    check(len(set(terminal_paths))==1,'one_retained_terminal_original')
    stop=read('stop',terminal_paths[0]); terminal=Path(terminal_paths[0]).parent
    lane=read('lane',terminal/'lane.json',False)['socket_lane']
    check(lane['lease_generation']==generation and lane['node']==0 and lane['job']==f'swdb-lanl17-20261007-a5-p{n}-a1' and lane['exit_code']==0 and 'record_errors' not in lane,'actual_lane_generation_job_zero_exit')
    for filename in ('runner.exit-code.txt','wrapper.exit-code.txt'):
        p=terminal/filename; originals[filename]=pin(p);check(p.read_bytes()==b'0\n','original_zero:'+filename)
    check(stop['source_commit']==R and stop['source_clean_after'] is True and stop['runner_exit_code']==stop['public_exit_code']==0,'clean_R_normal_stop')
    check(not stop['process_cleanup']['survivors'] and not stop.get('infrastructure_error'),'no_owned_survivor_or_infrastructure_error')
    check(utc(lane['started_utc'])<=utc(stop['started_utc'])<utc(stop['ended_utc'])<utc(lane['ended_utc'])+datetime.timedelta(seconds=1),'original_native_whole_second_precision')
    check(after['source_commit']==R and after['estimator_sha256']==F6 and after['manifest_identity_sha256']==M2 and after['source_clean'] is True,'frozen_clean_source_manifest')
    check(after['campaign']==cid and after['attempt']==1 and after['phase']=='after' and after['resume'] is False and after['baselines_only'] is False,'actual_nonresume_substantive_attempt')
    check(after['before_identity_sha256']==before['identity_sha256'] and after['dispatch_identity_sha256']==dispatch['identity_sha256'] and after['stopped_identity_sha256']==stop['identity_sha256'],'original_custody_links')
    check(after['released']==release and release['lease_generation']==generation and release['lease_released'] is True and release['node']==0,'embedded_exact_release')
    check(release['dispatch_identity']==dispatch['identity_sha256'] and release['stopped_identity']==stop['identity_sha256'] and release['runner_exit_code']==release['public_exit_code']==release['wrapper_exit_code']==0,'release_original_bindings_and_zero_exits')
    check(release['lane_record_sha256']==originals['lane']['sha256'] and release['wrapper_exit_file_sha256']==originals['wrapper.exit-code.txt']['sha256'],'original_lane_and_wrapper_byte_links')
    prov=release['parent_capture_provenance'];check(prov['capture_request_file_sha256']==originals['request']['sha256'] and prov['capture_request_identity_sha256']==request['identity_sha256'],'exact_request_original_provenance')
    check(prov['original_inputs']==request['inputs'] and all(request['context'].get(k)==v for k,v in prov['context_pins'].items()),'documented_context_subset_and_exact_inputs')
    check(prov['observations_sha256']==digest(canonical(request['observations'])),'original_observations_digest')
    s=after['state']['projection'];ledger=s['ledger']; rows=s['iterations']
    check(s['stopped'] is True and s['stop_reason']=='plateau' and s['setup_done'] is True and not s['pauses'],'normal_retained_plateau_state')
    check(ledger['iterations_completed']==ledger['plateau']==4 and len(ledger['iterations'])==len(rows)==4,'four_completed_substantive_iterations')
    check(all(i['outcome']=='not_improved' and i['advanced_plateau'] is True and i['plateau_counter']==i['index'] for i in ledger['iterations']),'original_plateau_progress')
    calls=ledger['calls'];check(len(calls)==calls_expected and len({c['invocation'] for c in calls})==calls_expected and all(c['counted'] is True and c['outcome']=='completed' for c in calls),'distinct_completed_counted_calls')
    bridge=s['setup_calls']+[c for i in rows for c in i['provider_calls']]
    fields=('role','invocation','outcome','counted')
    check([{k:c[k] for k in fields} for c in calls]==[{k:c[k] for k in fields} for c in bridge],'setup_iteration_provider_ledger_bridge')
    check(sum(len(i['candidates']) for i in rows)==8 and all(i['ended'] and utc(i['started'])<utc(i['ended']) for i in rows),'eight_candidate_rows_completed_iterations')
    inv=after['invocation_inventory']['provider_directories']
    check({i['invocation'] for i in inv}=={c['invocation'] for c in calls} and all(i['provider_receipt_present'] is True for i in inv),'provider_existence_bridge_not_outcome_inference')
    check(after['raw_state_snapshots_transferred'] is False and after['provider_prompts_auth_logs_argv_read'] is False,'privacy_boundary')
    native_times=[]
    for suffix in ('before32','preexec32','before-after','after-after'):
        p=Path(f'/private/tmp/lanl17-p{n}-native-release-query-capture-{suffix}-20261008-a5/native-observation-original.json')
        if not p.exists() and suffix=='preexec32': continue # p1 exact original chain has before32 plus before/afterAFTER.
        d=read('native_'+suffix,p,False)
        check(d['release_ready'] is True and d['normal_exit_set_only'] is True and not d['unknown_reasons'] and not d['not_ready_reasons'] and d['required_generation']==generation,'original_native_ready:'+suffix)
        check(d['native_metadata']['state']=='released' and d['native_metadata']['generation']==generation and all(not d[k]['matching_rows'] for k in ('kernel_locks_before','kernel_locks_after')) and all(d[k]['FD9_matches_selected_lease'] is False for k in ('daemon_before','daemon_after')),'released_no_kernel_or_FD9_holder:'+suffix)
        raw=base64.b64decode(d['native_metadata']['raw_base64']);check(digest(raw)==d['native_metadata']['original_file_pin']['sha256'],'raw_native_original_pin:'+suffix)
        for filename,v in d['attempt_metadata'].items():
            q=terminal/filename;check(pin(q)['sha256']==v['original_file_pin']['sha256'] and pin(q)['bytes']==v['original_file_pin']['bytes'],'unchanged_final_terminal:'+suffix+':'+filename)
        native_times.append((suffix,utc(d['checked_utc'])))
    check(utc(stop['ended_utc'])<=native_times[0][1]<=utc(release['checked_utc'])<=dict(native_times)['before-after']<=utc(after['checked_utc'])<=dict(native_times)['after-after'],'historical_no_reuse_custody_chronology')
    check(all(a[1]<=b[1] for a,b in zip(native_times,native_times[1:])),'historical_native_chronology')
    out=Path(f'/private/tmp/lanl17-p{n}-normal-custody-root-rereview-20261008-r1.json')
    d={'format':'swdb.lanl17-retained-original-normal-custody-root-rereview.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'PASS','campaign':cid,'generation':generation,'iterations':4,'candidate_rows':8,'completed_counted_calls':calls_expected,'checks':checks,'originals':originals,'review_source':pin(Path(__file__)),'scope':'Fresh local rereview of historical exact originals only; no remote/custody repetition; not current lane clearance or final numerical/D30/scientific admission','scientific_admission':False}
    b=(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(b)
    print(out,len(b),digest(b),len(checks),'PASS')
