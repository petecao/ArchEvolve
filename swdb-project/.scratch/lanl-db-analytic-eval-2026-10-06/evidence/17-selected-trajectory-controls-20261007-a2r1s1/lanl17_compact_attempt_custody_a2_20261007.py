"""PROSPECTIVE parent-owned control custody; never launch a campaign.

Before/after unchanged 28d dispatch. No Store, scientific/provider imports,
SSH, auth, prompts, argv or raw-log reads. Original state bytes stay in the
explicit remote custody folder; only allowlisted projections may be exported.
This source has not run. A before receipt is not a lock or a dispatch receipt.
"""
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess,sys
sys.dont_write_bytecode=True
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
HELPER='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
FORMAT='swdb.lanl17-attempt-control-custody.v2'
MAX_BYTES=32*1024*1024
CIDS={f'extensa-gem5-bfs-20261006-p{i}' for i in range(1,5)}
CALL_KEYS=('role','invocation','outcome','counted','model','effort','classification')
CANDIDATE_KEYS=('id','class','artifact_sha256','patch_sha256','contracts','knobs','certification','comparisons','level','selection')
ITERATION_KEYS=('index','started','ended','improved_classes')
STATE_KEYS=('campaign','campaign_sha256','started','stopped','stop_reason','clean_exit','setup_done','resumes','lane_hours','provider_wait_hours','disk_bytes_peak','prepared','preflights','baselines')
def require(ok,why):
    if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def utc(v):
    x=datetime.datetime.fromisoformat(v);require(x.tzinfo is not None and x.utcoffset().total_seconds()==0,'UTC required');return x
def obj(raw):
    def pairs(rows):
        v={}
        for k,x in rows:require(k not in v,'duplicate JSON key');v[k]=x
        return v
    return json.loads(raw,object_pairs_hook=pairs)
def pin(p):
    p=pathlib.Path(p);require(p.is_absolute() and not p.is_symlink() and p.is_file(),'regular absolute pinned file required')
    require(p.stat().st_size<=MAX_BYTES,'compact source exceeds bound');raw=p.read_bytes()
    return raw,{'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def sealed(path,expected):
    raw,p=pin(path);v=obj(raw);require(p['sha256']==expected,'explicit file pin differs')
    require(v['identity_sha256']==digest({k:x for k,x in v.items() if k!='identity_sha256'}),'receipt seal differs')
    p['identity_sha256']=v['identity_sha256'];return v,p

def safe_code(code):
    # Explanations/feedback/guard_reason are intentionally never serialized.
    require(isinstance(code,str) and re.fullmatch('[a-z0-9_.-]+',code),'closed reason code required');return code

def calls(rows):return [{k:r[k] for k in CALL_KEYS if k in r} for r in rows]
def candidate(row):
    result={k:row[k] for k in CANDIDATE_KEYS if k in row}
    # These are public candidate/certification/comparison counters and IDs only;
    # no _patch, feedback, regions, source snippets or rewrite/provider inputs.
    return result

def iteration(row):
    return {**{k:row[k] for k in ITERATION_KEYS if k in row},'provider_calls':calls(row.get('provider_calls',[])),
            'candidates':[candidate(r) for r in row.get('candidates',[])],
            'source_row_sha256':digest(row)}

def project_state(state):
    result={k:state[k] for k in STATE_KEYS if k in state}
    result['ledger']={k:state['ledger'][k] for k in ('iteration','iterations_completed','plateau','calls','iterations','terminal','iteration_calls','setup_calls')}
    result['ledger']['calls']=[{k:r[k] for k in ('index','iteration','role','invocation','outcome','counted')} for r in state['ledger']['calls']]
    result['ledger']['iterations']=[{k:r[k] for k in ('index','outcome','advanced_plateau','plateau_counter')} for r in state['ledger']['iterations']]
    require(result['ledger']==state['ledger'],'unexpected private/unknown ledger field')
    result['ledger_sha256']=digest(state['ledger'])
    result['iterations']=[iteration(r) for r in state['iterations']]
    result['setup_calls']=calls(state.get('setup_calls',[]))
    result['pauses']=[{**{k:r[k] for k in ('at','resumed_at','iteration') if k in r},
                      'reason':safe_code(r['reason']),'provider_calls':calls(r.get('provider_calls',[])),
                      'source_row_sha256':digest(r)} for r in state['pauses']]
    if state.get('interrupted_iteration'):result['interrupted_iteration']=iteration(state['interrupted_iteration'])
    result['protocol_id']=state.get('protocol',{}).get('id')
    result['protocol_identity_sha256']=state.get('protocol',{}).get('identity_sha256')
    # Detail may contain externally supplied STOP text or exception snippets:
    # hash it, never export raw text. Parent can attest its category separately.
    result['stop_detail_sha256']=digest(state.get('stop_detail'))
    result['source_state_semantic_sha256']=digest(state)
    return result

def snapshots(state_path,output):
    p=pathlib.Path(state_path)
    if not p.exists():return {'present':False,'file':None,'projection':None}
    raw,pinned=pin(p);state=obj(raw)
    original=output/'state.original.remote-only.json'
    require(not original.exists(),'never overwrite original state custody')
    fd=os.open(original,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as h:h.write(raw)
    # Original byte snapshots may contain private fields and are remote-only.
    return {'present':True,'file':pinned,'original_remote_only':{'path':str(original),'bytes':len(raw),'sha256':sha(raw)},'projection':project_state(state)}

def invocation_inventory(campaign,cid):
    # Directory names / existence only. Never open provider.json (which may
    # contain full command arrays), prompt.txt, stream logs or role inputs.
    root=campaign/'provider';names=[]
    if root.exists():
        require(root.is_dir() and not root.is_symlink(),'provider directory must be regular')
        entries=list(root.iterdir());require(len(entries)<=500,'bounded invocation inventory required')
        for path in entries:
            require(path.is_dir() and not path.is_symlink() and re.fullmatch(re.escape(cid)+r'\.call[1-9][0-9]*',path.name),'unknown provider directory shape requires parent review')
            names.append({'invocation':path.name,'provider_receipt_present':(path/'provider.json').is_file()})
    names.sort(key=lambda r:int(r['invocation'].rsplit('call',1)[1]))
    synthesis=campaign/'synthesis'
    return {'provider_directories':names,'names_sha256':digest(names),'synthesis_directory_present':synthesis.exists(),
            'provider_receipts_prompts_commands_inputs_opened':False,'scope':'Existence only; directory presence does not prove a provider launch or outcome'}

def git(project,*args):
    return subprocess.check_output(['git','-c','protocol.allow=never','-C',str(project),*args],timeout=60,
        env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'}).decode().strip()

def validate_source(a,m):
    project=pathlib.Path(a.project).resolve(strict=True)
    require(git(project,'rev-parse','HEAD')==a.final_r,'explicit clean final R required')
    require(not git(project,'status','--porcelain'),'source must remain clean')
    require(re.fullmatch('[0-9a-f]{40}',a.final_r),'full final R required')
    modules={p.relative_to(project/'swdb').as_posix():sha(p.read_bytes()) for p in sorted((project/'swdb').rglob('*.py'))}
    require(len(modules)==185 and digest(modules)==F6,'final R Python bundle differs from C/F6')
    helper_raw,_=pin(a.helper);require(sha(helper_raw)==HELPER,'unchanged selected helper required')
    require(m['source_commit']==a.final_r and m['estimator_sha256']==F6 and m['helper_sha256']==HELPER,'manifest source/control differs')
    return {'source_commit':a.final_r,'estimator_sha256':F6,'helper_sha256':HELPER,'source_clean':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=('before','after'));p.add_argument('--project',required=True);p.add_argument('--final-r',required=True)
    p.add_argument('--helper',required=True);p.add_argument('--manifest',required=True);p.add_argument('--manifest-file-sha256',required=True)
    p.add_argument('--campaign',required=True,choices=sorted(CIDS));p.add_argument('--attempt',type=int,required=True)
    p.add_argument('--publication',required=True);p.add_argument('--publication-file-sha256',required=True)
    p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');p.add_argument('--baselines-only',action='store_true')
    p.add_argument('--unclean-resume-admission');p.add_argument('--unclean-resume-admission-file-sha256')
    p.add_argument('--prior-after');p.add_argument('--prior-after-file-sha256');p.add_argument('--before');p.add_argument('--before-file-sha256')
    p.add_argument('--dispatch');p.add_argument('--dispatch-file-sha256');p.add_argument('--stopped');p.add_argument('--stopped-file-sha256')
    p.add_argument('--released');p.add_argument('--released-file-sha256')
    a=p.parse_args();require(a.attempt>0,'positive attempt required')
    m,mp=sealed(a.manifest,a.manifest_file_sha256);source=validate_source(a,m)
    publication,publication_pin=sealed(a.publication,a.publication_file_sha256)
    require(publication['format']=='swdb.lanl17-freeze-publication-custody.v1' and publication['source_commit']==a.final_r and publication['manifest_sha256']==m['identity_sha256'] and publication['policy_sha256']==m['policy']['identity_sha256'],'actual frozen publication differs')
    require(publication['completed_export_exit_code']==0 and publication['application_outcomes_opened']==0 and publication['freeze_export_commit']==m['freeze_export']['commit'],'freeze must be published before campaign action')
    require(m['policy']['id'] and m['policy']['identity_sha256'],'explicit frozen policy required')
    raw=pathlib.Path(m['raw']).resolve(strict=True);require(raw.is_absolute(),'absolute frozen raw root required')
    campaign=raw/'campaign-runs/extensa'/a.campaign;state_path=campaign/'state.json'
    cfg_raw,_=pin(raw/'configs'/(a.campaign+'.yaml'));config_sha=m['configuration_files'][a.campaign+'.yaml']
    require(sha(cfg_raw)==config_sha,'actual frozen configuration bytes differ')
    output=pathlib.Path(a.output)
    require(output.is_absolute() and not output.is_symlink() and not output.exists(),'fresh absolute custody folder required')
    require(not output.is_relative_to(campaign) and not output.is_relative_to(pathlib.Path(m['source'])),'custody outside source/campaign folder required')
    invocations=invocation_inventory(campaign,a.campaign)
    before=prior=dispatch=stop=release=unclean=None
    if a.phase=='before':
        require(state_path.exists()==a.resume,'fresh state absence or explicit resume required')
        if a.resume:
            require(a.attempt>1,'resume cannot be attempt one')
            require(a.prior_after and a.prior_after_file_sha256,'prior released after-custody required for resume')
            prior,prior_pin=sealed(a.prior_after,a.prior_after_file_sha256)
            require(prior['format']==FORMAT and prior['phase']=='after' and prior['attempt']==a.attempt-1,'prior attempt custody differs')
            require(prior['campaign']==a.campaign and prior['manifest_identity_sha256']==m['identity_sha256'] and prior['source_commit']==a.final_r,'resume changes campaign/R/M2')
            require(prior['released']['lease_released'] is True,'prior lane not released')
            if any(prior['released'][k]!=0 for k in ('runner_exit_code','public_exit_code','wrapper_exit_code')):
                require(a.unclean_resume_admission and a.unclean_resume_admission_file_sha256,'unclean prior attempt requires concrete parent lost-call admission')
                unclean,unclean_pin=sealed(a.unclean_resume_admission,a.unclean_resume_admission_file_sha256)
                require(unclean['format']=='swdb.lanl17-unclean-resume-admission.v1' and unclean['basis']=='explicit_parent_attestation_from_concrete_attempt_custody' and unclean['accepted'] is True and unclean['source_commit']==a.final_r and unclean['prior_after_identity_sha256']==prior['identity_sha256'] and unclean['prior_state_sha256']==prior['state']['file']['sha256'],'unclean admission does not bind concrete prior attempt')
                require(unclean['unaccounted_opened_calls']==0 and unclean['scientific_source_or_state_changed'] is False,'unknown/lost calls cannot be waived or inserted into frozen scientific state')
            current,current_pin=pin(state_path)
            require(prior['state']['present'] and prior['state']['file']['sha256']==current_pin['sha256'],'resume input differs from previous released post-state')
            saved=obj(current);known={r['invocation'] for r in saved['ledger']['calls']}
            require({r['invocation'] for r in invocations['provider_directories']}<=known,'unsaved invocation directory requires concrete parent budget review before resume')
            require(invocations==prior['invocation_inventory'],'invocation control facts changed after prior release')
            require(saved.get('stopped') is not True,'public run refuses ALL terminal stopped states, including infrastructure failure')
        else:
            require(a.attempt==1 and not campaign.exists(),'initial fresh campaign directory must remain absent')
    else:
        require(all((a.before,a.before_file_sha256,a.dispatch,a.dispatch_file_sha256,a.stopped,a.stopped_file_sha256,a.released,a.released_file_sha256)),'explicit before/dispatch/stopped/release pins required')
        before,bp=sealed(a.before,a.before_file_sha256);dispatch,dp=sealed(a.dispatch,a.dispatch_file_sha256)
        stop,sp=sealed(a.stopped,a.stopped_file_sha256);release,rp=sealed(a.released,a.released_file_sha256)
        require(before['format']==FORMAT and before['phase']=='before','before custody format differs')
        for v in (before,dispatch,release):require(v['campaign']==a.campaign and v['attempt']==a.attempt,'attempt/campaign mismatch')
        require(stop['campaign']==a.campaign,'stopped campaign mismatch; stopped receipt has no attempt field')
        for v in (before,dispatch,stop):require(v['source_commit']==a.final_r,'attempt source changes')
        require(dispatch['manifest_sha256']==stop['manifest_sha256']==m['identity_sha256'] and dispatch['policy']==stop['policy']==m['policy'],'attempt M2/policy changes')
        require(dispatch['resume']==before['resume']==a.resume and dispatch['baselines_only']==before['baselines_only']==a.baselines_only,'dispatch differs from guarded state action')
        require(stop['dispatch_sha256']==dispatch['identity_sha256'],'stopped dispatch binding differs')
        require(release['format']=='swdb.lanl17-attempt-release-custody.v1' and release['dispatch_identity']==dispatch['identity_sha256'] and release['stopped_identity']==stop['identity_sha256'],'parent release custody differs')
        require(release['lease_released'] is True and release['runner_exit_code']==stop['runner_exit_code'] and release['public_exit_code']==stop['public_exit_code'],'release/exit facts differ')
        attempt_root=raw/'attempts'/a.campaign/('attempt-'+str(a.attempt))
        copied_helper,_=pin(attempt_root/'helper.py');require(sha(copied_helper)==HELPER,'actual stopped attempt helper bytes differ')
        wrapper_raw,wrapper_pin=pin(attempt_root/'wrapper.exit-code.txt');runner_raw,runner_pin=pin(attempt_root/'runner.exit-code.txt');_,lane_pin=pin(attempt_root/'lane.json')
        require(int(wrapper_raw)==release['wrapper_exit_code'] and int(runner_raw)==stop['runner_exit_code']==release['runner_exit_code'],'original wrapper/runner exit bytes differ')
        require(wrapper_pin['sha256']==release['wrapper_exit_file_sha256'] and lane_pin['sha256']==release['lane_record_sha256'],'original lane/wrapper source pins differ')
        require(stop['process_cleanup']['subreaper'] is True and stop['process_cleanup']['survivors']=={} and stop['source_clean_after'] is True,'owned attempt cleanup/source incomplete')
        require(utc(release['checked_utc'])>=utc(stop['ended_utc']) and utc(before['checked_utc'])<=utc(dispatch['checked_utc']),'custody chronology differs')
    output.mkdir(parents=False)
    captured=snapshots(state_path,output)
    if captured['present']:
        v=captured['projection'];require(v['campaign']==a.campaign and v['campaign_sha256']==config_sha,'captured campaign/configuration differs')
        if a.phase=='before':require(v.get('stopped') is not True,'stopped state cannot resume')
    result={'format':FORMAT,'phase':a.phase,'checked_utc':now(),'campaign':a.campaign,'attempt':a.attempt,
        **source,'manifest_identity_sha256':m['identity_sha256'],'manifest_file_pin':mp,'policy':m['policy'],
        'collector_sha256':sha(pathlib.Path(__file__).read_bytes()),'freeze_publication_pin':publication_pin,'resume':a.resume,'baselines_only':a.baselines_only,'state':captured,'invocation_inventory':invocations,
        'raw_state_snapshots_transferred':False,'provider_prompts_auth_logs_argv_read':False,
        'state_control_scope':'Retained state/ledger only; not independent completeness of unsaved provider calls or step-time/DU events',
        'dispatch_to_state_time_of_check_gap':'Parent must immediately corroborate unchanged state before unchanged helper dispatch; this collector does not own a lane lock'}
    if prior:result['prior_after_identity_sha256']=prior['identity_sha256']
    if unclean:result['unclean_resume_admission_pin']=unclean_pin
    if before:result.update(before_identity_sha256=before['identity_sha256'],dispatch_identity_sha256=dispatch['identity_sha256'],stopped_identity_sha256=stop['identity_sha256'],released=release)
    validate_source(a,m)  # No source change during custody capture.
    require(invocation_inventory(campaign,a.campaign)==invocations,'invocation facts changed during custody capture')
    require(state_path.exists()==captured['present'],'state presence changed during custody capture')
    if captured['present']:
        current_state,_=pin(state_path);require(sha(current_state)==captured['file']['sha256'],'state bytes changed during custody capture')
    require(utc(publication['checked_utc'])<=utc(result['checked_utc']),'campaign custody precedes publication')
    result['identity_sha256']=digest(result)
    tmp=output/'custody.tmp';tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(output/'custody.json')
    print(json.dumps({'phase':a.phase,'campaign':a.campaign,'attempt':a.attempt,'custody':str(output/'custody.json'),'identity_sha256':result['identity_sha256'],'campaign_launched':False,'source_or_state_modified':False}))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError):
        print(json.dumps({'state':'refused','campaign_launched':False,'error':'control custody prerequisites failed'}));sys.exit(2)
