"""Created 2026-10-08 ET: SOURCE ONLY pre-full-index observation, NOT RUN.
Closed actual metadata input; no approval or scientific admission inferred.
No provider/log/report stdout/YAML/auth bodies, target imports or index execution.
"""
import argparse,datetime,hashlib,json,os,pwd,re,shutil,signal,socket,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
BASE=Path('/data1/yanruj')
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
SOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a5'
PRIMARY=BASE/'ArchEvolve'
FINALIZE=Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5')
ER=BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a5'
ER_REL=Path('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-actual-report-mbit10-20261007-a5.json')
M2_SHA='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'
M2_ID='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(i) for i in range(1,5))
H=BASE/'lanl17-control-cleanup60-20261007-a4.py'
G=BASE/'lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'
SUP=BASE/'lanl17-metadata-supervisor-cleanup60-20261007-a4.py'
FIXED_SOURCE={
 'helper_source':(str(H),38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),
 'guard_source':(str(G),14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),
 'supervisor_source':(str(SUP),8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0')}
NATIVE={
 '/usr/bin/bash':(1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),
 '/usr/bin/python3.12':(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
 '/usr/bin/timeout':(39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),
 '/usr/bin/sha256sum':(39336,'4d2db56c867e5324e0084c9e897f6360d37517de77ac96f2bd31494223d69a60'),
 '/usr/bin/wc':(55824,'9005273a966c875547a4317288bdd92e7b2aa49ad86bc9978121242106405e6b'),
 '/usr/bin/mkdir':(76296,'430c3f949d7d328cd835722f5bbddeac0956fbdfbbb6a197e0abb1def3ed27e2')}
ROUTE_ROLES=('inventory_output','spec_preparation_output','author_output','writer_output','bootstrap_logs','inner_logs','outer_logs','bootstrap_preparation_output')
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES','POSIXLY_CORRECT')
INPUT_PIN=None
INPUT=None
ARGS=None
def need(ok,reason):
    if not ok: raise ValueError(reason)

def tick(): need(time.monotonic()<END,'host_metadata_deadline')

def digest(b): return hashlib.sha256(b).hexdigest()

def stamp(s): return {k:getattr(s,'st_'+k) for k in FIELDS}

def strict(b):
    def pairs(items):
        d={}
        for k,v in items: need(k not in d,'duplicate_JSON_key');d[k]=v
        return d
    def bad(v): raise ValueError('nonfinite_JSON')
    return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)

def original(p,cap=131072):
    tick();need(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_original')
    s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000 and 0<=s.st_size<=cap,'original_identity_or_cap')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'original_open_changed');b=f.read(cap+1)
        need(len(b)==s.st_size<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'original_read_changed')
    return b,{'path':str(p),'bytes':len(b),'sha256':digest(b),'stat':stamp(s)}

def kernel_bytes(p,cap,owner):
    tick();s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==owner,'kernel_identity')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'kernel_open_changed');b=f.read(cap+1)
        need(len(b)<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'kernel_cap_or_stat_changed')
    return b

def locks(identity):
    b=kernel_bytes(Path('/proc/locks'),1024*1024,0);rows=[]
    need(not b or b.endswith(b'\n'),'locks_truncated_line')
    for raw in b.splitlines():
        tick();parts=raw.decode('ascii').split();need(len(parts) in (8,9),'locks_field_count')
        blocked=len(parts)==9
        if blocked:need(parts[1]=='->','locks_waiter_marker');parts.pop(1)
        need(re.fullmatch(r'[0-9]+:',parts[0]) is not None and re.fullmatch(r'-?[0-9]+',parts[4]) is not None,'locks_id_or_PID')
        m=re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]+):([0-9]+)',parts[5]);need(m is not None,'locks_device_inode')
        need(parts[6].isdigit() and (parts[7]=='EOF' or parts[7].isdigit()),'locks_range')
        major,minor,inode=int(m[1],16),int(m[2],16),int(m[3])
        if (major,minor,inode)==(identity['device_major'],identity['device_minor'],identity['inode']):
            rows.append({'original_row':raw.decode('ascii'),'blocked_waiter':blocked,'pid':int(parts[4]),'type':parts[1],'device_major':major,'device_minor':minor,'inode':inode})
    return {'path':'/proc/locks','bytes':len(b),'sha256':digest(b),'matching_rows':rows}

def daemon(pid,identity):
    need(type(pid) is int and pid>0,'daemon_PID_missing_or_invalid');p=Path('/proc')/str(pid)
    try:s=p.stat()
    except FileNotFoundError:return {'pid':pid,'exists':False,'FD9':'process_absent','FD9_matches_selected_lease':False}
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID,'daemon_proc_owner')
    b=kernel_bytes(p/'stat',8192,UID);parts=b.rsplit(b')',1)[1].split();need(len(parts)>=20,'daemon_stat_shape');start=int(parts[19]);need(start>0,'daemon_start_ticks')
    fd=p/'fd/9';result={'pid':pid,'exists':True,'proc_inode':s.st_ino,'proc_uid':s.st_uid,'start_ticks':start,'start_ticks_not_compared_to_hostlock_sh_timestamp_token':True}
    try:target=os.readlink(fd)
    except FileNotFoundError:result.update(FD9='absent',FD9_matches_selected_lease=False)
    else:
        result.update(FD9='present',FD9_route_sha256=digest(os.fsencode(target)),FD9_route_matches_selected_lease=target==identity['path'],FD9_matches_selected_lease=False)
        if target==identity['path']:
            fs=fd.stat();need(stat.S_ISREG(fs.st_mode) and fs.st_uid==UID,'FD9_type_owner')
            result['FD9_stat']=stamp(fs);result['FD9_matches_selected_lease']=(fs.st_dev,fs.st_ino)==(identity['stat']['dev'],identity['inode'])
            need(result['FD9_matches_selected_lease'],'FD9_same_route_different_inode')
    need(p.stat().st_ino==s.st_ino and p.stat().st_uid==UID,'daemon_proc_changed')
    b2=kernel_bytes(p/'stat',8192,UID);need(int(b2.rsplit(b')',1)[1].split()[19])==start,'daemon_PID_reused')
    return result

def process_identity(pid):
    tick();need(type(pid) is int and pid>0,'process_PID_type');p=Path('/proc')/str(pid)
    s=p.stat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID,'owned_process_identity')
    b=kernel_bytes(p/'stat',8192,UID);parts=b.rsplit(b')',1)[1].split();need(len(parts)>=20,'process_stat_shape')
    need(b.split(b' ',1)[0]==str(pid).encode(),'process_stat_PID')
    parent=int(parts[1]);start=int(parts[19]);need(parent>0 and start>0,'process_parent_start')
    command=kernel_bytes(p/'cmdline',65536,UID);need(command.endswith(b'\0'),'process_cmdline_terminated')
    argv=command[:-1].split(b'\0');exe=os.readlink(p/'exe')
    b2=kernel_bytes(p/'stat',8192,UID);parts2=b2.rsplit(b')',1)[1].split()
    need(p.stat().st_uid==s.st_uid and p.stat().st_ino==s.st_ino and int(parts2[1])==parent and int(parts2[19])==start,'process_identity_race')
    need(kernel_bytes(p/'cmdline',65536,UID)==command and os.readlink(p/'exe')==exe,'process_command_exe_race')
    return {'pid':pid,'ppid':parent,'proc_inode':s.st_ino,'uid':s.st_uid,'start_ticks':start,'cmdline_sha256':digest(command),'exe_route_sha256':digest(os.fsencode(exe))},argv,exe

def native_projection(d,name):
    keys={'active_session','attempt_pid','attempt_start_token','heartbeat_at','lease','recovered_from_generation','released_at','session_note','session_state','state','writer'}
    need(type(d) is dict and set(d)==keys and d['state']=='released' and d['writer']=='hostlock.sh' and d['session_state']=='none','exact_native_hostlock_schema')
    need(all(d[k] is None for k in ('active_session','attempt_pid','attempt_start_token','recovered_from_generation','session_note')),'native_null_auxiliary_fields')
    x=d['lease'];need(type(x) is dict and set(x)=={'acquired_at','daemon_pid','daemon_start_token','generation','host','lease_name','mode','session_id'},'exact_native_lease_schema')
    need(x['host']=='mbit10' and x['lease_name']==name and x['mode'] in ('measure','build_calibrate') and x['session_id'] is None,'native_lease_binding')
    need(type(x['generation']) is int and 0<x['generation']<=2**63-1 and type(x['daemon_pid']) is int and 0<x['daemon_pid']<2**31,'native_generation_daemon_types')
    if name=='mbit10-evaluation-node0':need(x['generation']==514,'actual_P4_generation514_no_reuse')
    need(type(x['daemon_start_token']) is str and re.fullmatch('sh'+str(x['daemon_pid'])+r'-[0-9]{1,32}',x['daemon_start_token']) is not None,'native_daemon_token_shape')
    times={}
    for key,value in (('acquired_at',x['acquired_at']),('heartbeat_at',d['heartbeat_at']),('released_at',d['released_at'])):
        need(type(value) is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',value) is not None,'native_UTC_scalar')
        times[key]=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(times['acquired_at']<=times['released_at']==times['heartbeat_at'],'native_release_chronology')
    return {'state':'released','writer':'hostlock.sh','lease_name':name,'host':'mbit10','mode':x['mode'],'generation':x['generation'],'daemon_pid':x['daemon_pid'],'daemon_start_token':x['daemon_start_token'],'acquired_at':x['acquired_at'],'released_at':d['released_at'],'heartbeat_at':d['heartbeat_at']}

def selected_lease_identity(pin):
    st=pin['stat'];need(stat.S_ISREG(st['mode']) and st['uid']==UID and st['nlink']==1,'pinned_native_lease_identity')
    return {'path':pin['path'],'stat':st,'device_major':os.major(st['dev']),'device_minor':os.minor(st['dev']),'inode':st['ino']}

def daemon_ready(pid,identity):
    proof=daemon(pid,identity)
    need(proof.get('FD9')!='present' or proof.get('FD9_route_matches_selected_lease') is True,'daemon_FD9_foreign_or_deleted_route_unknown')
    need(not proof['FD9_matches_selected_lease'],'native_daemon_FD9_still_held')
    return proof

class Parser(argparse.ArgumentParser):
    def error(self,message):raise ValueError('argument_contract')
def closed(v,keys,why):need(type(v) is dict and set(v)==set(keys),why);return v
def hex64(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'actual_SHA');return v
def utc(v):
    need(type(v) is str and len(v)<=40,'actual_UTC');d=datetime.datetime.fromisoformat(v)
    need(d.tzinfo is not None and d.utcoffset()==datetime.timedelta(0),'UTC_offset');return d
def payload_digest(v):return digest(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def remote_path(v,existing=True):
    need(type(v) is str and len(v)<=1024 and re.fullmatch('/[A-Za-z0-9_./-]+',v) is not None,'closed_remote_route')
    p=Path(v);need(str(p)==v and '..' not in p.parts and '.' not in p.parts,'canonical_route_spelling')
    need(p.is_relative_to(Path('/data/yanruj')) or p.is_relative_to(BASE),'owned_remote_namespace')
    need(not any(x in p.parts for x in ('.codex','.ssh','.aws')) and p.name not in ('auth.json','provider.json','prompt.txt','feedback.txt'),'sensitive_route_refused')
    need(not any(x.is_symlink() for x in (p,*p.parents)) and p.resolve(strict=existing)==p,'canonical_nonsymlink_route');return p
def bounded_input(raw):
    v=strict(raw);count=[0]
    def walk(x,depth=0):
        count[0]+=1;need(depth<=32 and count[0]<=10000,'input_structure_bound')
        if type(x) is dict:
            for k,y in x.items():need(type(k) is str and len(k)<=128,'input_key_bound');walk(y,depth+1)
        elif type(x) is list:
            for y in x:walk(y,depth+1)
        elif type(x) is str:need(len(x)<=1024 and 'FUTURE' not in x and 'ACTUAL_' not in x,'unfilled_or_unbounded_input')
        else:need(x is None or type(x) in (bool,int),'closed_input_scalar')
    walk(v);return v
def input_original(p,expected):
    remote_path(str(p));need(not p.is_relative_to(SOURCE) and not p.is_relative_to(RAW),'external_input_route')
    b,pin=original(p,131072);need(stat.S_IMODE(pin['stat']['mode'])==0o600 and digest(b)==hex64(expected),'own0600_exact_input');return b,pin

def transport_identity():
    own,argv,exe=process_identity(os.getpid())
    expected=[b'/usr/bin/python3.12',b'-I',b'-B',b'-c']
    tail=[b'--input',os.fsencode(ARGS.input),b'--input-sha256',ARGS.input_sha256.encode(),b'--source-sha256',ARGS.source_sha256.encode()]
    need(exe=='/usr/bin/python3.12' and len(argv)==11 and argv[:4]==expected and argv[5:]==tail,'native_inline_exact_input_argv')
    need(digest(argv[4])==ARGS.source_sha256 and own['ppid']==os.getppid(),'self_source_SHA_actual_parent')
    parent,pargv,pexe=process_identity(own['ppid'])
    need(pexe=='/usr/bin/timeout' and pargv==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=60s',b'60s',*argv],'exact_immediate_owned_GNU_timeout_parent')
    return {'self':own,'parent':parent,'inline_source_sha256':ARGS.source_sha256,'input_sha256':ARGS.input_sha256,'only_exact_immediate_timeout_parent_excluded':True}

def expected_original_routes():
    rows={'guard_preregistration':(FINALIZE/'preregistration.json',131072),'supervisor_receipt':(FINALIZE/'supervisor-receipt.json',131072),'helper_stdout':(FINALIZE/'helper.stdout',65536),'final_export':(RAW/'final-export.json',65536),'agreement_receipt':(ER/ER_REL,2*1024*1024),'manifest_M2':(RAW/'manifest.json',400000)}
    for role,(route,n,_) in FIXED_SOURCE.items():rows[role]=(Path(route),n)
    for name in [*('validate-'+cid for cid in CIDS),'validate-final-export']:
        for role,suffix,cap in (('argv','argv.json',32768),('exit','exit-code.txt',64),('stdout','stdout',4096),('stderr','stderr',65536)):rows[name+':'+role]=(RAW/(name+'.'+suffix),cap)
    return rows

def completion_originals(v):
    expected=expected_original_routes();closed(v,expected,'exact_completion_role_map');pins={};bodies={}
    for role,(p,cap) in expected.items():
        x=closed(v[role],('path','bytes','sha256','stat'),'exact_completion_pin')
        need(x['path']==str(p) and type(x['bytes']) is int and 0<=x['bytes']<=cap,'fixed_role_route_or_cap');hex64(x['sha256']);closed(x['stat'],FIELDS,'original_nine_stat_fields')
        need(all(type(x['stat'][k]) is int and x['stat'][k]>=0 for k in FIELDS),'original_stat_integer')
        raw,pin=original(p,cap);need(pin==x,'reviewed_original_bytes_or_stat_changed');pins[role]=pin;bodies[role]=raw
    for role,(route,n,h) in FIXED_SOURCE.items():need(pins[role]['bytes']==n and pins[role]['sha256']==h,'fixed_control_source_pin')
    need(pins['manifest_M2']['bytes']==292401 and pins['manifest_M2']['sha256']==M2_SHA,'exact_original_M2')
    def seal(role,fmt,ascii):
        d=strict(bodies[role]);need(type(d) is dict,'original_control_JSON_object');need(d.get('format')==fmt and d.get('identity_sha256')==digest(json.dumps({k:x for k,x in d.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=ascii,allow_nan=False).encode()),'original_source_policy_seal');return d
    m=seal('manifest_M2','swdb.lanl17-parent-population.v1',True)
    need(m['identity_sha256']==M2_ID and m['source']==str(SOURCE) and m['raw']==str(RAW) and m['source_commit']==R and m['estimator_sha256']==F6 and m['helper_sha256']==FIXED_SOURCE['helper_source'][2],'original_M2_context')
    pre=seal('guard_preregistration','swdb.lanl17-metadata-dispatch-preregistration.v1',False)
    need(pre['action']=='finalize' and pre['final_source_commit']==pre['cleanup_source_commit']==R and pre['project']==str(SOURCE/'swdb-project') and pre['source_code_equivalent_F6'] is True,'original_FINALIZE_guard_context')
    sup=seal('supervisor_receipt','swdb.lanl17-metadata-supervisor.v1',False)
    need(sup['action']=='finalize' and sup['state']=='child_returned' and type(sup['child_exit']) is int and type(sup['supervisor_exit']) is int and sup['child_exit']==sup['supervisor_exit']==0 and sup['timed_out'] is False and sup['signal_received'] is None and sup['error_type'] is None and sup['cleanup_errors']==[] and sup['fixture'] is False and sup['cleanup']['subreaper'] is True and sup['cleanup']['survivors']=={},'original_normal_FINALIZE_cleanup')
    need(sup['helper_sha256']==sup['cleanup_implementation_sha256']==FIXED_SOURCE['helper_source'][2] and sup['supervisor_sha256']==FIXED_SOURCE['supervisor_source'][2] and sup['processes_py_sha256']=='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289' and sup['estimator_sha256']==F6 and sup['uid']==UID,'original_FINALIZE_source_lineage')
    result=strict(bodies['final_export']);helper=strict(bodies['helper_stdout']);need(type(result) is dict and type(helper) is dict,'original_export_helper_JSON_objects')
    need(result==helper and set(result)=={'branch','commit','paths','raw_transferred'} and result['branch']=='codex/lanl17-actual-report-evidence-20261007-a5' and result['commit']==INPUT['expected_ER_commit'] and result['raw_transferred'] is False,'actual_original_ER_commit_binding')
    receipt=seal('agreement_receipt','swdb.lanl17-actual-agreement-compact.v1',True)
    need(receipt['manifest']==m and receipt['source_clean'] is True and receipt['raw_transferred'] is False,'actual_original_ER_receipt_binding')
    for name in [*('validate-'+cid for cid in CIDS),'validate-final-export']:
        folder=RAW/'base/records' if name=='validate-final-export' else RAW/'campaign-runs/extensa'/name.removeprefix('validate-')/'records'
        argv=strict(b'{"argv":'+bodies[name+':argv']+b'}')['argv']
        need(argv==['python3','-m','swdb','validate','--records',str(folder)] and bodies[name+':exit']==b'0\n' and re.fullmatch(rb'OK: [0-9]{1,8} record\(s\) valid\n',bodies[name+':stdout']) is not None and bodies[name+':stderr']==b'','original_validation_quartet_success')
    reviewed_stops=receipt['stopped_attempts'];need(type(reviewed_stops) is list and len(reviewed_stops)==4 and all(type(v) is dict and v.get('campaign')==cid for cid,v in zip(CIDS,reviewed_stops)),'reviewed_ER_four_original_stops')
    return pins,reviewed_stops

def current_sources():
    def git(p,*tail):return run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(p),*tail]).strip()
    out={}
    for p in (PRIMARY,SOURCE):
        need(p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_uid==UID,'owned_source_canonical')
        head=git(p,'rev-parse','HEAD');need(head==R and git(p,'status','--porcelain','--untracked-files=no')=='','source_R_tracked_clean');out[str(p)]={'head':head,'tracked_clean':True}
    need(git(PRIMARY,'branch','--show-current')=='yanrujhou_main' and git(PRIMARY,'rev-parse','origin/yanrujhou_main')==R,'PRIMARY_branch_origin_R')
    need(git(SOURCE,'status','--porcelain')=='','S_clean_full')
    need(git(PRIMARY,'status','--porcelain','--untracked-files=all')=='?? swdb-project/records/.retention.lock','PRIMARY_exact_retention_lock')
    rb,rpin=original(PRIMARY/'swdb-project/records/.retention.lock',0);need(rb==b'','empty_retention_lock_preserved')
    modules={}
    for p in sorted((SOURCE/'swdb-project/swdb').rglob('*.py')):
        raw,pin=original(p,2*1024*1024);modules[p.relative_to(SOURCE/'swdb-project/swdb').as_posix()]=digest(raw)
    need(len(modules)==185 and digest(json.dumps(modules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==F6,'physical185_F6')
    need(git(ER,'rev-parse','HEAD')==INPUT['expected_ER_commit'] and git(ER,'rev-list','--parents','-n','1','HEAD').split()[1:]==[R] and git(ER,'branch','--show-current')=='codex/lanl17-actual-report-evidence-20261007-a5' and git(ER,'status','--porcelain')=='','actual_ER_revision_clean_parent')
    return {'sources':out,'primary_origin':R,'retention_lock_original':rpin,'physical_module_count':185,'physical_F6':F6,'actual_ER_commit':INPUT['expected_ER_commit']}

def run(argv):
    tick();p=subprocess.run(argv,capture_output=True,timeout=min(15,max(.1,END-time.monotonic())),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'},stdin=subprocess.DEVNULL)
    need(p.returncode==0 and len(p.stdout)<=65536 and len(p.stderr)<=65536,'metadata_command_exit_or_cap');return p.stdout.decode()

def root_tool_pin(route,n,h):
    p=Path(route);need(p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)),'native_tool_canonical')
    s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o755 and s.st_size==n<=16*1024*1024,'native_tool_root_regular_size_mode')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);count=0;hasher=hashlib.sha256()
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'native_tool_open_race')
        while True:
            tick();b=f.read(65536)
            if not b:break
            count+=len(b);need(count<=n,'native_tool_byte_cap');hasher.update(b)
        need(count==n and hasher.hexdigest()==h and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'native_tool_hash_or_race')
    return {'path':route,'bytes':n,'sha256':h,'stat':stamp(s)}

def home_startup():
    need(os.environ.get('HOME')==pwd.getpwuid(UID).pw_dir and os.environ.get('CODEX_HOME')=='/data1/yanruj/.codex','current_public_home_route')
    need(all(not os.environ.get(k) for k in STARTUP),'unsafe_startup_or_POSIX_environment')
    need('posix' not in os.environ.get('SHELLOPTS','').split(':') and not any(k.startswith('BASH_FUNC_') for k in os.environ),'unsafe_Bash_posix_or_exported_function_startup')
    home=BASE/'.codex';need(home.resolve(strict=True)==home and not any(x.is_symlink() for x in (home,*home.parents)) and home.is_dir() and home.stat().st_uid==UID,'owned_public_CODEX_HOME')
    auth=home/'auth.json';s=auth.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000,'public_auth_exists_regular_owned')
    return {'HOME_matches_account':True,'CODEX_HOME_public_route_matches':True,'public_auth_exists':True,'public_auth_stat':stamp(s),'authentication_contents_read':False,'authentication_contents_preservation_not_policed':True,'unsafe_startup_environment_absent':True,'POSIXLY_CORRECT_absent':True,'Bash_1024_byte_ulimit_units_observed':False,'Bash_units_and_startup_invocation_require_separate_parent_review':True,'task_marker_not_restored_or_modified':True}

def fresh_outputs(rows):
    need(type(rows) is dict and 1<=len(rows)<=len(ROUTE_ROLES) and set(rows)<=set(ROUTE_ROLES),'closed_explicit_next_stage_output_route_subset');paths=[];out={}
    for role,value in rows.items():
        p=remote_path(value,False);need(not os.path.lexists(p) and p.parent.is_dir() and p.parent.stat().st_uid==UID,'fresh_owned_output_route')
        need(not p.is_relative_to(SOURCE) and not SOURCE.is_relative_to(p) and not p.is_relative_to(RAW) and not RAW.is_relative_to(p),'output_external_to_whole_S_RAW')
        paths.append(p);out[role]={'path':str(p),'absent':True,'owned_existing_parent_stat':stamp(p.parent.stat())}
    need(len(set(paths))==len(paths) and all(not a.is_relative_to(b) and not b.is_relative_to(a) for i,a in enumerate(paths) for b in paths[i+1:]),'output_routes_pairwise_disjoint')
    for cid in CIDS:
        p=RAW/'campaign-runs/extensa'/cid/'records';need(p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)) and p.is_dir() and p.stat().st_uid==UID,'existing_actual_RAW_store_required')
    return out

def owned_cmdline(p,ps):
    # Preserve ancestor's owned-directory scan scope. Strict kernel UID/start
    # guards apply to matching consumers, not every unrelated owned stat file.
    tick();q=p/'cmdline';s=q.lstat();need(stat.S_ISREG(s.st_mode),'owned_cmdline_regular')
    fd=os.open(q,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'owned_cmdline_open_race');raw=f.read(65537)
        need(len(raw)<=65536 and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(q.lstat()),'owned_cmdline_cap_or_race')
    after=p.stat();need(after.st_uid==UID and after.st_ino==ps.st_ino,'owned_cmdline_directory_race')
    need(not raw or raw.endswith(b'\0'),'owned_cmdline_terminated');return raw

def inactive_owned_identity(p,ps):
    # Empty cmdline alone never proves absence. Only exact stable Z/X state can.
    b=kernel_bytes(p/'stat',8192,UID);v=b.rsplit(b')',1)[1].split()
    need(len(v)>=20 and b.split(b' ',1)[0]==p.name.encode() and v[0] in (b'Z',b'X'),'empty_owned_cmdline_not_proved_inactive')
    start=int(v[19]);need(start>0,'inactive_start_positive')
    b2=kernel_bytes(p/'stat',8192,UID);w=b2.rsplit(b')',1)[1].split()
    need(len(w)>=20 and b2.split(b' ',1)[0]==p.name.encode() and w[0] in (b'Z',b'X') and int(w[19])==start and p.stat().st_uid==UID and p.stat().st_ino==ps.st_ino,'inactive_process_identity_race')
    return {'pid':int(p.name),'uid':UID,'proc_inode':ps.st_ino,'start_ticks':start,'state':w[0].decode('ascii')}

def consumers(transport):
    matches=[];unknowns=[];seen=0;owned=0;needles=[str(SOURCE).encode(),str(RAW).encode(),str(H).encode()]
    for p in Path('/proc').iterdir():
        tick();seen+=1;need(seen<=32768,'process_inventory_bound')
        if not p.name.isdecimal() or int(p.name) in (transport['self']['pid'],transport['parent']['pid']):continue
        pid=int(p.name);proof=None
        try:
            ps=p.stat()
            if ps.st_uid!=UID:continue
            owned+=1;need(owned<=4096,'owned_process_bound');proof={'pid':pid,'uid':UID,'proc_inode':ps.st_ino}
            command=owned_cmdline(p,ps)
            argv=command[:-1].split(b'\0') if command else []
            if not argv or not argv[0]:
                proof=inactive_owned_identity(p,ps);need(owned_cmdline(p,ps)==command,'inactive_cmdline_byte_continuity');continue
            matched=any(needle in arg for needle in needles for arg in argv)
            if matched:
                identity,current_argv,exe=process_identity(pid)
                need(identity['proc_inode']==ps.st_ino and identity['cmdline_sha256']==digest(command) and current_argv==argv,'matching_consumer_identity_race')
                proof=identity
                raw=kernel_bytes(p/'stat',8192,UID);parts=raw.rsplit(b')',1)[1].split()
                need(len(parts)>=20 and int(parts[19])==identity['start_ticks'] and p.stat().st_uid==UID and p.stat().st_ino==ps.st_ino,'matching_consumer_final_identity_race')
                if parts[0] not in (b'Z',b'X'):
                    need(len(matches)<128,'matching_consumer_bound');matches.append(identity)
            need(owned_cmdline(p,ps)==command,'owned_cmdline_byte_continuity')
        except (OSError,ValueError,IndexError,UnicodeError) as exc:
            if isinstance(exc,(FileNotFoundError,ProcessLookupError)) and proof is None:continue
            need(len(unknowns)<128,'unknown_process_bound');unknowns.append({**(proof or {}),'state':'unknown','error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())})
    return {'state':'unknown' if unknowns else 'observed','owned_processes_checked':owned,'matching_live_consumers':matches,'unknown_processes':unknowns,'no_live_owned_source_RAW_consumers':not unknowns and not matches,'partial_inventory_cannot_prove_absence':True,'strict_kernel_identity_checked_for_matching_consumers_only':True,'process_argv_or_other_users_bodies_returned':False}



def read():
    need(sys.platform=='linux' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10','native_account_host')
    need(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_isolated_python')
    transport=transport_identity();completion,reviewed_stops=completion_originals(INPUT['completion_originals']);sources=current_sources();tools={p:root_tool_pin(p,n,h) for p,(n,h) in NATIVE.items()};home=home_startup();routes=fresh_outputs(INPUT['fresh_routes'])
    leases={};lpins={};lproofs={};ds={};ids={}
    for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
        b,pin=original(BASE/'lact-host-lease'/(name+'.meta.json'),32768);leases[name]=native_projection(strict(b),name);lpins[name]=pin
        _,pin=original(BASE/'lact-host-lease'/(name+'.lease'),4096);ids[name]=selected_lease_identity(pin);proof=locks(ids[name]);need(not proof['matching_rows'],'no_matching_kernel_holder_or_waiter');ds[name]=daemon_ready(leases[name]['daemon_pid'],ids[name]);lproofs[name]={'lease_original':pin,'proof_before':proof}
    stops={}
    for cid,reviewed_stop in zip(CIDS,reviewed_stops):
        p=RAW/'attempts'/cid/'attempt-1/stopped-receipt.json';b,pin=original(p,65536);v=strict(b);need(v==reviewed_stop,'original_stop_matches_reviewed_ER_chain');utc(v['ended_utc']);need(v['identity_sha256']==payload_digest({k:x for k,x in v.items() if k!='identity_sha256'}),'original_stop_True_seal')
        need(v['campaign']==cid and v['source_commit']==R and v['source_clean_after'] is True and v['manifest_sha256']==M2_ID and v['estimator_sha256_after']==F6 and type(v['public_exit_code']) is int and type(v['runner_exit_code']) is int and v['public_exit_code']==v['runner_exit_code']==0 and v.get('infrastructure_error') is None and v['process_cleanup']['subreaper'] is True and v['process_cleanup']['survivors']=={},'all_four_original_normal_stops')
        stops[cid]={'original':pin,'identity_sha256':v['identity_sha256'],'ended_utc':v['ended_utc']}
    processes=consumers(transport)
    mem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k=='MemAvailable'};free={p:shutil.disk_usage(p).free for p in ('/data1','/data')}
    need(mem['MemAvailable']>=85899345920 and free['/data1']>=22548578304 and free['/data']>=25769803776,'unchanged_serial_floors')
    for name,d in leases.items():
        b,pin=original(BASE/'lact-host-lease'/(name+'.meta.json'),32768);need(native_projection(strict(b),name)==d and pin==lpins[name],'lease_continuity')
        _,pin=original(Path(lproofs[name]['lease_original']['path']),4096);need(pin==lproofs[name]['lease_original'],'lease_inode_continuity');proof=locks(ids[name]);need(not proof['matching_rows'],'after_no_kernel_holder_or_waiter');lproofs[name]['proof_after']=proof;need(daemon_ready(d['daemon_pid'],ids[name])==ds[name],'daemon_FD9_continuity')
    need(completion_originals(INPUT['completion_originals'])==(completion,reviewed_stops) and current_sources()==sources and home_startup()==home and fresh_outputs(INPUT['fresh_routes'])==routes,'completion_source_home_route_continuity')
    for p,(n,h) in NATIVE.items():need(root_tool_pin(p,n,h)==tools[p],'native_tool_continuity')
    for d in stops.values():_,pin=original(Path(d['original']['path']),65536);need(pin==d['original'],'original_stop_continuity')
    need(transport_identity()==transport,'self_parent_transport_continuity');_,pin=input_original(Path(ARGS.input),ARGS.input_sha256);need(pin==INPUT_PIN,'input_original_continuity')
    need(datetime.datetime.now(datetime.timezone.utc)<utc(INPUT['parent_review']['valid_until_utc']),'actual_parent_review_expired')
    ready=processes['no_live_owned_source_RAW_consumers']
    return {'format':'swdb.lanl17-pre-full-index-host-observation.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host_metadata_ready':ready,'state':'observed' if ready else 'unknown' if processes['unknown_processes'] else 'consumers_present','scientific_admission':False,'sealed':False,'read_only':True,'campaign':INPUT['campaign'],'nonce':INPUT['nonce'],'actual_input_pin':INPUT_PIN,'parent_review_payload_sha256':INPUT['parent_review']['payload_sha256'],'actual_reviewed_completion_originals':completion,'source':sources,'native_tools':tools,'startup_HOME':home,'native_leases':leases,'native_lease_originals':lpins,'kernel_locks':lproofs,'daemon_FD9':ds,'four_original_stops':stops,'processes':processes,'fresh_upcoming_output_routes':routes,'mem':mem,'free_bytes':free,'transport_identity':transport,'point_in_time_only':True,'catalog_inventory_or_YAML_read':False,'raw_log_report_stdout_provider_auth_bodies_read':False,'parent_historical_catalog_validation_continuity_not_observed':True,'parent_exclusive_ownership_and_all_four_custody_approval_not_inferred':True,'native_Bash_1024_byte_units_not_observed':True,'fresh_native_and_catalog_continuity_required_through_index':True}

def main():
    global ARGS,INPUT,INPUT_PIN
    p=Parser(add_help=False);p.add_argument('--input',required=True);p.add_argument('--input-sha256',required=True);p.add_argument('--source-sha256',required=True);ARGS=p.parse_args();hex64(ARGS.source_sha256)
    raw,INPUT_PIN=input_original(Path(ARGS.input),ARGS.input_sha256);INPUT=bounded_input(raw)
    closed(INPUT,('format','campaign','nonce','completion_originals','expected_ER_commit','fresh_routes','parent_review'),'closed_actual_input_fields')
    need(INPUT['format']=='swdb.lanl17-pre-full-index-host-observation-input.v1' and INPUT['campaign'] in CIDS,'actual_input_format_CID')
    need(type(INPUT['nonce']) is str and re.fullmatch('[0-9a-f]{32,64}',INPUT['nonce']) is not None,'actual_parent_nonce');need(type(INPUT['expected_ER_commit']) is str and re.fullmatch('[0-9a-f]{40}',INPUT['expected_ER_commit']) is not None,'actual_ER_commit_no_default')
    review=closed(INPUT['parent_review'],('basis','source_sha256','payload_sha256','completion_packet_sha256','completion_root_review_sha256','completion_peer_review_sha256','actual_completion_originals_reviewed','fixtures','checked_utc','valid_until_utc'),'closed_actual_parent_review')
    need(review['basis']=='explicit_parent_review_of_genuine_completed_FINALIZE_and_next_full_index_metadata_routes' and review['source_sha256']==ARGS.source_sha256 and review['payload_sha256']==payload_digest({k:v for k,v in INPUT.items() if k!='parent_review'}) and review['actual_completion_originals_reviewed'] is True and review['fixtures'] is False,'genuine_bound_parent_review')
    for k in ('completion_packet_sha256','completion_root_review_sha256','completion_peer_review_sha256'):hex64(review[k])
    checked,end=utc(review['checked_utc']),utc(review['valid_until_utc']);need(checked<=datetime.datetime.now(datetime.timezone.utc)<end and 0<(end-checked).total_seconds()<=300,'actual_parent_review_interval')
    d=read();b=(json.dumps(d,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=65536,'observation_return_cap');sys.stdout.buffer.write(b)
def interrupted(n,f):raise ValueError('host_metadata_signal_or_deadline')
for n in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(n,interrupted)
signal.alarm(45)
try:main()
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,RecursionError,subprocess.SubprocessError) as e:
    print(json.dumps({'format':'swdb.lanl17-pre-full-index-host-observation.v1','host_metadata_ready':False,'state':'unknown','scientific_admission':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason_sha256':digest(str(e).encode()),'error_class':type(e).__name__},sort_keys=True))
