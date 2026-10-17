"""2026-10-08 ET: parent original P4 interim custody review, no controls or scientific admission."""
import base64,datetime,hashlib,json,os
from pathlib import Path
R='5e12a9796432654d88def24ecea617d16ca605b2';CID='extensa-gem5-bfs-20261006-p4';checks=[];pins={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name,path):
 p=Path(path);b=p.read_bytes();pins[name]={'path':str(p),'bytes':len(b),'sha256':sha(b)};return json.loads(b)
def test(ok,name):
 assert ok,name;checks.append(name)
def sealed(v,ascii,name):test(v['identity_sha256']==sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=ascii,allow_nan=False).encode()),name+' original canonical seal')
base='/private/tmp/lanl17-p4-'
a=load('after',base+'after-capture-20261008-a5/custody.json');b=load('before',base+'before-capture-20261008-a5/custody.json');d=load('dispatch',base+'dispatch-original-collect-capture-20261008-a5/dispatch-preregistration.json');s=load('stop',base+'terminal-originals-capture-20261008-a5/decoded-originals/stopped-receipt.json');r=load('release',base+'release32-capture-20261008-a5/release-custody-original.json');q=load('request',base+'release-request-finalized-r2-20261008-a5.json')
for n,v,ascii in [('after',a,False),('before',b,False),('dispatch',d,True),('stop',s,True),('release',r,True),('request',q,True)]:sealed(v,ascii,n)
test(a['before_identity_sha256']==b['identity_sha256'] and a['dispatch_identity_sha256']==d['identity_sha256'] and a['stopped_identity_sha256']==s['identity_sha256'] and a['released']==r,'original BEFORE dispatch stop release AFTER chain')
test(a['campaign']==s['campaign']==r['campaign']==CID and a['attempt']==d['attempt']==r['attempt']==1 and a['resume'] is False and a['baselines_only'] is False,'exact original campaign attempt no resume')
test(a['source_commit']==s['source_commit']==r['source_commit']==R and a['source_clean'] is True and s['source_clean_after'] is True and a['estimator_sha256']==s['estimator_sha256_after']=='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3','clean original R and F6')
test(a['policy']==s['policy']==q['context']['policy']==r['parent_capture_provenance']['context_pins']['policy'],'original frozen global policy')
test(s['infrastructure_error'] is None and s['process_cleanup']['subreaper'] is True and s['process_cleanup']['survivors']=={} and s['original_codex_home_restored'] is True and s['account_home_unchanged'] is True,'normal stop cleanup and account restore')
test(r['lease_generation']==514 and r['lease_released'] is True and r['node']==0 and r['runner_exit_code']==r['public_exit_code']==r['wrapper_exit_code']==0,'original release514 node0 zero exits')
test(r['parent_capture_provenance']['capture_request_file_sha256']==pins['request']['sha256'] and r['parent_capture_provenance']['capture_request_identity_sha256']==q['identity_sha256'] and r['parent_capture_provenance']['original_inputs']==q['inputs'],'release request and seven input provenance')
p=a['state']['projection'];l=p['ledger'];it=p['iterations'];calls=l['calls']
test(p['stopped'] is True and p['stop_reason']=='plateau' and p['setup_done'] is True and l['iterations_completed']==4 and l['plateau']==4 and l['terminal'] is None and len(it)==4,'substantive normal plateau4 terminal state')
test([i['index'] for i in it]==[1,2,3,4] and all(i['ended'] and not i['improved_classes'] for i in it) and all(i['outcome']=='not_improved' and i['advanced_plateau'] is True and i['plateau_counter']==i['index'] for i in l['iterations']),'four completed iteration bridge')
test(len(calls)==7 and len({c['invocation'] for c in calls})==7 and all(c['outcome']=='completed' and c['counted'] is True for c in calls),'seven distinct completed counted provider calls')
bridged=p['setup_calls']+[c for i in it for c in i['provider_calls']]
test({c['invocation'] for c in bridged}=={c['invocation'] for c in calls} and len(bridged)==7 and all(c['outcome']=='completed' and c['counted'] is True for c in bridged),'retained setup iteration provider bridge')
test({c['invocation'] for c in a['invocation_inventory']['provider_directories'] if c['provider_receipt_present'] is True}=={c['invocation'] for c in calls},'original provider receipt existence corroborates ledger')
candidates=[c for i in it for c in i['candidates']];test(len(candidates)==8 and all(c['level']=='rejected' and c['comparisons']==[] for c in candidates),'eight genuine candidate rows all rejected no timing comparisons')
test(a['raw_state_snapshots_transferred'] is False and a['provider_prompts_auth_logs_argv_read'] is False and a['invocation_inventory']['provider_receipts_prompts_commands_inputs_opened'] is False,'raw state and provider bodies remain remote')
for phase in ('before32-capture-r2','before-after-capture','preexec-after-capture','post-after-capture'):
 n=load('native_'+phase,base+'native-'+phase+'-20261008-a5/native-original.json');test(n['release_ready'] is True and n['normal_exit_set_only'] is True and n['required_generation']==514 and n['native_metadata']['state']=='released' and n['kernel_locks_before']['matching_rows']==n['kernel_locks_after']['matching_rows']==[] and n['daemon_before']==n['daemon_after'] and n['daemon_after']['FD9']=='process_absent' and n['unknown_reasons']==n['not_ready_reasons']==[],'native '+phase+' original514 no kernel or FD9 holder')
 if phase=='preexec-after-capture':test(n['checked_utc']<a['checked_utc'],'native before AFTER chronology')
 if phase=='post-after-capture':test(n['checked_utc']>a['checked_utc'],'native after AFTER chronology')
for phase in ('before32-capture-r2','preexec-after-capture','post-after-capture'):
 v=load('source_'+phase,base+'source-'+phase+'-20261008-a5/source-original.json');test(v['primary_origin']==R and v['source']['/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5']=={'head':R,'status':''} and v['source']['/data1/yanruj/ArchEvolve']=={'head':R,'status':'?? swdb-project/records/.retention.lock\n'},'source '+phase+' original cleanR retention exception')
out={'format':'swdb.lanl17-p4-original-normal-custody-root-review.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'PASS','generation':514,'iterations':4,'candidate_rows':8,'materialized_candidate_rows':sum(bool(c['id']) for c in candidates),'completed_counted_calls':7,'checks':checks,'originals':pins,'scientific_admission':False,'scope':'Interim original custody; final full report indexes strict audit numerical and D30 admission remain separate'}
b=(json.dumps(out,indent=2,sort_keys=True)+'\n').encode();p='/private/tmp/lanl17-p4-normal-custody-root-review-20261008-a5.json';fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
print(len(checks),p,len(b),sha(b))
