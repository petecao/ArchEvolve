"""Local p1-only normal-path request author. No remote/control/scientific execution."""
import argparse,base64,copy,datetime,hashlib,json,os,re,stat,sys
from pathlib import Path
R='5e12a9796432654d88def24ecea617d16ca605b2'
H='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
N='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
Q='df19c76a0a3c667f5d1b901677c72641a0f367e6971b4ee2e37a62871bbc7626'
P='32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
DRAFT='0c7b8fd601b07c8e61f1e6709aeeefeb11de619a1b1e2d10c5a77086a86eba08'
M2SHA='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'
DSHA='7e63d49398eb8f8e2f0d9332b84c1350276acd5b50b9287b2d0b694ec565a6b4'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5'
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5'
A=RAW+'/attempts/extensa-gem5-bfs-20261006-p1/attempt-1'
QUERY='/data1/yanruj/lanl17-p1-native-release-query-20261008-a5-r2.py'
OBS='/data1/yanruj/lanl17-p1-native-release-observation-20261008-a5.json'
REQUEST='/data/yanruj/EvolveSWDB_runs/lanl17-p1-release-request-20261008-a5.json'
OUTPUT='/data/yanruj/EvolveSWDB_runs/lanl17-p1-release-custody-20261008-a5.json'
PRODUCER='/data1/yanruj/lanl17-custody-source-20261007-a3/capture-producer.py'
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
SEEN=[]
class Refused(ValueError):pass

def need(v,code):
    if not v:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in FIELDS}
def canonical_json(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def strict(b):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate_JSON_key');out[k]=v
        return out
    def bad(v):raise Refused('nonfinite_JSON')
    v=json.loads(b,object_pairs_hook=pairs,parse_constant=bad);need(type(v) is dict,'JSON_object');return v

def read(p,cap,expected=None,size=None):
    need(p.is_absolute() and p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)),'local_canonical_file')
    s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and s.st_nlink==1 and not s.st_mode&0o7022 and 0<s.st_size<=cap,'owned_bounded_local_file')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'local_open_changed');b=f.read(cap+1)
        need(len(b)==s.st_size<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'local_bytes_stat_race')
    if expected is not None:need(sha(b)==expected,'local_original_SHA')
    if size is not None:need(len(b)==size,'local_original_size')
    SEEN.append((p,cap,sha(b),stamp(s)));return b

def utc(v):
    need(type(v) is str and 0<len(v)<=64,'UTC_type');t=datetime.datetime.fromisoformat(v.replace('Z','+00:00'))
    need(t.tzinfo is not None and t.utcoffset()==datetime.timedelta(0),'actual_UTC_required');return t

def sealed(v):
    need(v.get('canonical_ensure_ascii',True) is True and type(v.get('identity_sha256')) is str and re.fullmatch('[0-9a-f]{64}',v['identity_sha256']) is not None,'original_True_seal_policy')
    need(sha(canonical_json({k:x for k,x in v.items() if k!='identity_sha256'}))==v['identity_sha256'],'original_seal')

def native_pin(pin,path,b):
    need(set(pin)=={'path','bytes','sha256','stat'} and pin['path']==path and type(pin['bytes']) is int and pin['bytes']==len(b) and pin['sha256']==sha(b),'native_original_pin')
    s=pin['stat'];need(type(s) is dict and set(s)==set(FIELDS) and all(type(s[k]) is int for k in FIELDS),'native_stat_fields')
    need(stat.S_ISREG(s['mode']) and not s['mode']&0o7000 and s['uid']==114316761 and s['nlink']==1 and s['size']==len(b),'native_stat_identity')

def no_future(v):
    if isinstance(v,dict):need('required_future_input' not in v,'unresolved_future_input');[no_future(x) for x in v.values()]
    elif isinstance(v,list):[no_future(x) for x in v]

def write(p,b):
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return {'path':str(p),'bytes':len(b),'sha256':sha(b)}

def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    for name in ('originals-directory','terminal-metadata-original','native-observation-original','manifest-original','dispatch-original','native-wrapper-source','output-request','output-action-config'):p.add_argument('--'+name,required=True,type=Path)
    for name in ('terminal-metadata-sha256','native-observation-sha256','fresh-live-checked-utc','valid-until-utc'):p.add_argument('--'+name,required=True)
    for name in ('fresh-live-generation511-no-holder-and-sourceR-reviewed','normal-terminal-state-summary-reviewed','node0-reserved-through-after-custody'):p.add_argument('--'+name,action='store_true')
    a=p.parse_args();need(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'local_parent_flags')
    need(a.fresh_live_generation511_no_holder_and_sourceR_reviewed and a.normal_terminal_state_summary_reviewed and a.node0_reserved_through_after_custody,'explicit_fresh_parent_normal_release_source_and_no_reuse_attestation')
    for value in (a.terminal_metadata_sha256,a.native_observation_sha256):need(re.fullmatch('[0-9a-f]{64}',value) is not None,'explicit_original_SHA')
    for out in (a.output_request,a.output_action_config):need(out.parent==Path('/private/tmp') and not os.path.lexists(out) and not out.is_symlink(),'fresh_private_output')
    need(a.output_request!=a.output_action_config,'distinct_outputs')
    base=Path('/private/tmp');draft=strict(read(base/'lanl17-p1-release-request-draft-r1-20261008-a5.json',32768,DRAFT,12307));spec=copy.deepcopy(draft['request_template']);ctx=spec['context']
    need(draft['executable'] is False and spec['capture']=='release' and ctx['source_commit']==R and ctx['source_path']==S and ctx['campaign']=='extensa-gem5-bfs-20261006-p1' and type(ctx['attempt']) is int and ctx['attempt']==1,'reviewed_p1_scope')
    read(base/'lanl17_parent_helpers_cleanup60_a4.py',65536,H,38195);read(a.native_wrapper_source,32768,N,10510)
    read(base/'lanl17_read_p1_native_release_observation_20261008_a5_r2.py',32768,Q,15125)
    read(base/'lanl17_parent_capture_projection_producer_a3_20261007.py',65536,P,46165)
    read(base/'lanl17_read_p1_normal_terminal_originals_20261008_a5_r1.py',32768,'bdf2f6bbe2893549f04ab41bbb06ffd0d698603e17098bc1aca0842f5eaf47e7',7544)
    m=strict(read(a.manifest_original,1048576,M2SHA,292401));dispatch=strict(read(a.dispatch_original,65536,DSHA,44229));sealed(m);sealed(dispatch)
    need(m['source_commit']==R and m['source']==S and m['raw']==RAW and m['source_clean'] is True and m['helper_sha256']==H and m['estimator_sha256']==ctx['estimator_sha256'] and m['identity_sha256']==ctx['manifest_identity_sha256'] and m['policy']==ctx['policy'],'frozen_M2_context')
    need(dispatch['identity_sha256']==spec['inputs']['dispatch']['identity_sha256'] and dispatch['source_commit']==R and dispatch['manifest_sha256']==m['identity_sha256'] and dispatch['policy']==ctx['policy'] and dispatch['campaign']==ctx['campaign'] and type(dispatch['attempt']) is int and dispatch['attempt']==1 and type(dispatch['node']) is int and dispatch['node']==0 and dispatch['resume'] is False and dispatch['baselines_only'] is False,'original_dispatch_bindings')
    native_raw=read(a.native_observation_original,262144,a.native_observation_sha256);native=strict(native_raw)
    need(native['format']=='swdb.lanl17-native-release-readonly-observation.v1' and native['sealed'] is False and native['scientific_admission'] is False and native['state']=='release_ready' and native['release_ready'] is True and native['normal_exit_set_only'] is True and native['unknown_reasons']==[] and native['not_ready_reasons']==[],'actual_R2_normal_release_ready')
    need(native['lease_name']=='mbit10-evaluation-node0' and type(native['required_generation']) is int and native['required_generation']==511 and native['original_exits']=={'wrapper':0,'runner':0,'lane':0,'public':0} and all(type(x) is int for x in native['original_exits'].values()),'actual_R2_generation_exits')
    nb=base64.b64decode(native['native_metadata']['raw_base64'],validate=True);need(len(nb)<=32768,'native_metadata_cap');native_pin(native['native_metadata']['original_file_pin'],'/data1/yanruj/lact-host-lease/mbit10-evaluation-node0.meta.json',nb)
    nm=strict(nb);need(nm['state']=='released' and nm['lease']['lease_name']=='mbit10-evaluation-node0' and type(nm['lease']['generation']) is int and nm['lease']['generation']==511 and type(nm['lease']['daemon_pid']) is int and nm['lease']['daemon_pid']>0,'native_original_released511')
    need(native['native_metadata']['state']=='released' and native['native_metadata']['generation']==511 and native['native_metadata']['daemon_pid']==nm['lease']['daemon_pid'],'native_projection_matches_raw')
    lease=native['native_lease_file'];need(lease['path']=='/data1/yanruj/lact-host-lease/mbit10-evaluation-node0.lease' and type(lease['stat']) is dict and set(lease['stat'])==set(FIELDS) and lease['inode']==lease['stat']['ino'] and lease['stat']['uid']==114316761 and lease['stat']['nlink']==1 and stat.S_ISREG(lease['stat']['mode']) and all(type(lease[k]) is int and lease[k]>=0 for k in ('device_major','device_minor','inode')),'native_lease_inode_identity')
    need(native['kernel_locks_before']==native['kernel_locks_after'] and native['kernel_locks_after']['path']=='/proc/locks' and native['kernel_locks_after']['matching_rows']==[],'native_no_matching_kernel_lock')
    need(native['daemon_before']==native['daemon_after'] and native['daemon_after']['pid']==nm['lease']['daemon_pid'] and native['daemon_after']['FD9'] in ('absent','process_absent') and native['daemon_after']['FD9_matches_selected_lease'] is False,'native_no_holder_FD9')
    terminal=strict(read(a.terminal_metadata_original,262144,a.terminal_metadata_sha256));need(terminal['format']=='swdb.lanl17-normal-terminal-originals-readonly.v1' and terminal['sealed'] is False and terminal['scientific_admission'] is False and terminal['normal_metadata_ready'] is True,'actual_normal_terminal_metadata')
    caps={'stopped-receipt.json':65536,'wrapper.exit-code.txt':64,'runner.exit-code.txt':64,'lane.json':32768};need(set(terminal['files'])==set(caps) and set(native['attempt_metadata'])==set(caps),'four_exact_original_names');raws={}
    for name,cap in caps.items():
        b=read(a.originals_directory/name,cap);row=terminal['files'][name];need(set(row)=={'path','bytes','sha256','stat','base64'},'terminal_original_fields')
        need(base64.b64decode(row['base64'],validate=True)==b,'terminal_returned_original_bytes');pin={k:row[k] for k in ('path','bytes','sha256','stat')};native_pin(pin,A+'/'+name,b)
        need(native['attempt_metadata'][name]['present'] is True and native['attempt_metadata'][name]['original_file_pin']==pin,'terminal_pin_including_stat_matches_R2');raws[name]=b
    stop=strict(raws['stopped-receipt.json']);sealed(stop);lane=strict(raws['lane.json'])['socket_lane']
    stopkeys={'format','started_utc','ended_utc','campaign','source_commit','policy','manifest_sha256','dispatch_sha256','argv_sha256','runner_exit_code','public_exit_code','infrastructure_error','process_cleanup','original_codex_home_restored','account_home_unchanged','source_clean_after','estimator_sha256_after','raw_transferred','scope','identity_sha256'};need(set(stop)==stopkeys,'original_closed_stop_fields')
    expected={'format':'swdb.lanl17-stopped-attempt.v1','campaign':ctx['campaign'],'source_commit':R,'manifest_sha256':m['identity_sha256'],'dispatch_sha256':dispatch['identity_sha256'],'policy':ctx['policy'],'estimator_sha256_after':ctx['estimator_sha256'],'infrastructure_error':None,'source_clean_after':True,'original_codex_home_restored':True,'account_home_unchanged':True,'raw_transferred':False};need(all(stop[k]==v for k,v in expected.items()),'original_normal_stop_context')
    need(stop['scope']=='Actual stopped attempt; no inferred completion, unique pairs or D30 success.' and type(stop['argv_sha256']) is str and re.fullmatch('[0-9a-f]{64}',stop['argv_sha256']) is not None,'closed_H_scope_and_argv_hash')
    need(all(type(stop[k]) is bool for k in ('source_clean_after','original_codex_home_restored','account_home_unchanged','raw_transferred')),'strict_H_stop_boolean_types')
    need(type(stop['runner_exit_code']) is int and type(stop['public_exit_code']) is int and stop['runner_exit_code']==stop['public_exit_code']==0,'normal_public_runner_exits')
    for name in ('wrapper.exit-code.txt','runner.exit-code.txt'):need(re.fullmatch(rb'-?[0-9]+\s*',raws[name]) is not None and int(raws[name])==0,'normal_original_integer_exits')
    clean=stop['process_cleanup'];need(type(clean) is dict and set(clean)=={'subreaper','terminated_owned_processes','survivors'} and clean['subreaper'] is True and clean['survivors']=={} and type(clean['terminated_owned_processes']) is list and len(clean['terminated_owned_processes'])<=1024,'normal_cleanup')
    for row in clean['terminated_owned_processes']:need(type(row) is dict and set(row)=={'pid','start_time','signal'} and type(row['pid']) is int and row['pid']>0 and type(row['start_time']) is str and re.fullmatch('[0-9]{1,32}',row['start_time']) is not None and row['signal'] in ('SIGTERM','SIGKILL'),'closed_cleanup_PID_metadata')
    need(type(lane) is dict and type(lane['node']) is int and lane['node']==0 and lane['job']=='swdb-lanl17-20261007-a5-p1-a1' and lane['lease_name']=='mbit10-evaluation-node0' and type(lane['lease_generation']) is int and lane['lease_generation']==511 and type(lane['exit_code']) is int and lane['exit_code']==0 and 'record_errors' not in lane,'normal_final_lane511')
    now=datetime.datetime.now(datetime.timezone.utc);fresh=utc(a.fresh_live_checked_utc);end=utc(a.valid_until_utc)
    need(utc(dispatch['checked_utc'])<=utc(stop['started_utc'])<utc(stop['ended_utc']) and utc(lane['started_utc'])<=utc(stop['started_utc']) and utc(stop['ended_utc'])<=utc(lane['ended_utc'])<=utc(native['checked_utc'])<=utc(terminal['checked_utc'])<=fresh<=now<=end,'actual_terminal_and_fresh_parent_chronology')
    spec['observations']={'lease_released':True,'lease_generation':511,'checked_utc':a.fresh_live_checked_utc}
    copied_helper={'path':A+'/helper.py','bytes':38195,'sha256':H}
    for name,basename in (('stopped','stopped-receipt.json'),('wrapper_exit','wrapper.exit-code.txt'),('runner_exit','runner.exit-code.txt'),('lane','lane.json')):
        desc=spec['inputs'][name];desc['bytes']=len(raws[basename]);desc['sha256']=sha(raws[basename]);need(desc['path']==A+'/'+basename,'fixed_original_remote_path')
    spec['inputs']['stopped'].update(identity_sha256=stop['identity_sha256'],canonical_ensure_ascii=True,writer_source=copied_helper,canonical_policy_sources=[copy.deepcopy(copied_helper)])
    spec['inputs']['runner_exit']['writer_source']=copy.deepcopy(copied_helper)
    wrapper={'path':m['wrapper']['path'],'bytes':10510,'sha256':N};need(m['wrapper']['sha256']==N,'frozen_native_wrapper');spec['inputs']['lane']['writer_source']=wrapper
    writer={'path':QUERY,'bytes':15125,'sha256':Q};spec['inputs']['authoritative_lease_observation'].update(path=OBS,bytes=len(native_raw),sha256=sha(native_raw),writer_source=writer)
    spec['read_roots']=[S,RAW,wrapper['path'],OBS,QUERY];spec['identity_sha256']=sha(canonical_json({k:v for k,v in spec.items() if k!='identity_sha256'}));no_future(spec)
    need(set(spec)=={'format','identity_sha256','producer_sha256','source_plan_sha256','auditor_sha256','collector_sha256','capture','context','observations','inputs','read_roots'} and set(spec['inputs'])=={'manifest_M2','dispatch','stopped','wrapper_exit','runner_exit','lane','authoritative_lease_observation'},'exact_producer32_schema')
    for desc in spec['inputs'].values():
        need(set(desc)=={'path','bytes','sha256','encoding','sealed','writer_source'}|({'identity_sha256','canonical_ensure_ascii','canonical_policy_sources'} if desc['sealed'] else set()),'exact_descriptor_schema')
        need(set(desc['writer_source'])=={'path','bytes','sha256'} and type(desc['bytes']) is int and 0<=desc['bytes']<=33554432,'bounded_exact_descriptor')
    request_raw=(json.dumps(spec,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    stage=lambda path,b:{'path':path,'bytes':len(b),'sha256':sha(b),'base64':base64.b64encode(b).decode('ascii')}
    config={'source_pins':[{'path':PRODUCER,'bytes':46165,'sha256':P},copied_helper,wrapper,writer],'stage':[stage(OBS,native_raw),stage(REQUEST,request_raw)],'argv':['/usr/bin/python3.12','-B',PRODUCER,'--request',REQUEST,'--request-sha256',sha(request_raw),'--output',OUTPUT],'collect':[OUTPUT],'remote_seconds':300,'local_seconds':420}
    action_raw=(json.dumps(config,sort_keys=True,allow_nan=False)+'\n').encode()
    for path,cap,digest,before in list(SEEN):need(path.lstat() and stamp(path.lstat())==before and sha(read(path,cap,digest))==digest,'local_original_changed_before_authoring')
    need(datetime.datetime.now(datetime.timezone.utc)<=end,'fresh_parent_validity_expired')
    outputs=[write(a.output_request,request_raw),write(a.output_action_config,action_raw)]
    print(json.dumps({'source_only_request_author':True,'remote_or_producer_executed':False,'scientific_completion_not_inferred':True,'fresh_live_checked_utc':a.fresh_live_checked_utc,'valid_until_utc':a.valid_until_utc,'request_identity_sha256':spec['identity_sha256'],'outputs':outputs,'fresh_before32_before_after_b08_and_node0_no_reuse_still_required':True},sort_keys=True))

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,OSError,IndexError) as exc:
        print(json.dumps({'format':'swdb.lanl17-p1-local-release-author-refusal.v1','error_class':type(exc).__name__,'reason_sha256':sha(str(exc).encode()),'remote_or_producer_executed':False,'scientific_completion_not_inferred':True}),file=sys.stderr);raise SystemExit(2)
