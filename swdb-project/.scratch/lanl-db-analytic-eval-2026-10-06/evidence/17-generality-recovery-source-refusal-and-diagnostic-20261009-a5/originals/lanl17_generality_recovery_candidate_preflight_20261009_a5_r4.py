"""Created 2026-10-09 ET: SOURCE ONLY recovery preflight, NOT RUN.
Read-only candidate/source/native/consumer inspection; only fresh private metadata
may be written after separate parent execution approval. No backup/removal/index.
"""
import argparse,base64,datetime,hashlib,json,os,pwd,re,shutil,signal,socket,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
BASE=Path('/data1/yanruj')
PRIMARY=BASE/'ArchEvolve'
SOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a5'
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
ER=BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a5'
H=BASE/'lanl17-control-cleanup60-20261007-a4.py'
G=BASE/'lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'
SUP=BASE/'lanl17-metadata-supervisor-cleanup60-20261007-a4.py'
CANDIDATE=BASE/'ArchEvolve-lanl-generality-final-20261007-a1'
CANDIDATE_HEAD='c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
GENERALITY_EXPORT='43256ee0300a59a03919833075fbb13fb3ba9ab3'
EXPECTED_ER='f5014746da61005be2d75cee16f8a834afa19321'
INPUT={'expected_ER_commit':EXPECTED_ER}
OUTPUT=Path('/data/yanruj/EvolveSWDB_runs/lanl17-generality-worktree-recovery-20261009-a1')
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+180
FILE_CAP=1024**3
TREE_CAP=2*1024**3
ENTRY_CAP=65536
METADATA_CAP=8*1024**2
PROTECTED=(PRIMARY,SOURCE,RAW,ER,BASE/'ArchEvolve-lanl17-freeze-evidence-20261007-a5',BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1',Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a5'),Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5'),H,G,SUP,BASE/'lanl17-dx100-hooks-20261008-a2',BASE/'lanl17-dx100-deployment-20261008-a2')
OBSERVED={}
ARGS=None
NATIVE={
 '/usr/bin/bash':(1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),
 '/usr/bin/python3.12':(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
 '/usr/bin/timeout':(39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),
 '/usr/bin/sha256sum':(39336,'4d2db56c867e5324e0084c9e897f6360d37517de77ac96f2bd31494223d69a60'),
 '/usr/bin/wc':(55824,'9005273a966c875547a4317288bdd92e7b2aa49ad86bc9978121242106405e6b'),
 '/usr/bin/mkdir':(76296,'430c3f949d7d328cd835722f5bbddeac0956fbdfbbb6a197e0abb1def3ed27e2')}
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES','POSIXLY_CORRECT')
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

def run(argv):
    tick();p=subprocess.run(argv,capture_output=True,timeout=min(15,max(.1,END-time.monotonic())),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'},stdin=subprocess.DEVNULL)
    need(p.returncode==0 and len(p.stdout)<=65536 and len(p.stderr)<=65536,'metadata_command_exit_or_cap');return p.stdout.decode()

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


def metadata_bytes(v):
    return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()

def transport_identity():
    own,argv,exe=process_identity(os.getpid())
    need(exe=='/usr/bin/python3.12' and len(argv)==9 and argv[:4]==[b'/usr/bin/python3.12',b'-I',b'-B',b'-c'],'exact_native_inline_argv')
    need(argv[5:]==[b'--source-sha256',ARGS.source_sha256.encode(),b'--output-directory',os.fsencode(ARGS.output_directory)] and digest(argv[4])==ARGS.source_sha256 and own['ppid']==os.getppid(),'exact_self_source_and_arguments')
    parent,pargv,pexe=process_identity(own['ppid'])
    need(pexe=='/usr/bin/timeout' and pargv==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=60s',b'240s',*argv],'exact_immediate_GNU240_K60_parent')
    return {'self':own,'parent':parent,'source_sha256':ARGS.source_sha256,'only_exact_immediate_timeout_parent_excluded':True}

def output_route():
    need(ARGS.output_directory==str(OUTPUT),'exact_recovery_metadata_output_route')
    need(not os.path.lexists(OUTPUT) and OUTPUT.parent.resolve(strict=True)==OUTPUT.parent and not any(p.is_symlink() for p in OUTPUT.parents) and OUTPUT.parent.stat().st_uid==UID,'fresh_owned_metadata_output')
    for p in (*PROTECTED,CANDIDATE):need(not OUTPUT.is_relative_to(p) and not p.is_relative_to(OUTPUT),'metadata_output_disjoint_protected_and_candidate')
    return {'path':str(OUTPUT),'initially_absent':True,'parent_stat':stamp(OUTPUT.parent.stat())}

def candidate_registration():
    need(CANDIDATE.resolve(strict=True)==CANDIDATE and not any(p.is_symlink() for p in (CANDIDATE,*CANDIDATE.parents)) and CANDIDATE.is_dir() and CANDIDATE.stat().st_uid==UID,'candidate_root_canonical_owned')
    for p in PROTECTED:need(not CANDIDATE.is_relative_to(p) and not p.is_relative_to(CANDIDATE),'candidate_disjoint_all_protected_roots')
    def git(*tail):return run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(CANDIDATE),*tail]).strip()
    need(git('rev-parse','HEAD')==CANDIDATE_HEAD and git('rev-parse','--abbrev-ref','HEAD')=='HEAD' and git('status','--porcelain','--untracked-files=all')=='','candidate_exact_detached_clean')
    common=Path(git('rev-parse','--git-common-dir'));gitdir=Path(git('rev-parse','--git-dir'))
    need(common==PRIMARY/'.git' and common.resolve(strict=True)==common and common.stat().st_uid==UID,'candidate_exact_PRIMARY_git_common')
    need(gitdir.parent==common/'worktrees' and gitdir.resolve(strict=True)==gitdir and gitdir.stat().st_uid==UID and not any(p.is_symlink() for p in (gitdir,*gitdir.parents)),'owned_canonical_worktree_registration')
    need(not os.path.lexists(gitdir/'locked') and not os.path.lexists(gitdir/'index.lock'),'candidate_registration_not_locked')
    pointer,pin=original(CANDIDATE/'.git',4096);need(pointer==('gitdir: '+str(gitdir)+'\n').encode(),'exact_root_git_pointer')
    backlink,bpin=original(gitdir/'gitdir',4096);need(backlink==(str(CANDIDATE/'.git')+'\n').encode(),'exact_registration_backlink')
    head,hpin=original(gitdir/'HEAD',128);need(head==(CANDIDATE_HEAD+'\n').encode(),'detached_registration_HEAD')
    rows=run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(PRIMARY),'worktree','list','--porcelain']).split('\n\n')
    matches=[r.splitlines() for r in rows if r.splitlines() and r.splitlines()[0]=='worktree '+str(CANDIDATE)]
    need(len(matches)==1 and 'HEAD '+CANDIDATE_HEAD in matches[0] and 'detached' in matches[0] and not any(x.startswith(('locked','prunable')) for x in matches[0]),'exact_unlocked_registered_candidate')
    # Git metadata only; c4 and its parent export must remain in protected common Git.
    git('merge-base','--is-ancestor',CANDIDATE_HEAD,R)
    need(git('rev-parse',GENERALITY_EXPORT+'^{commit}')==GENERALITY_EXPORT and git('rev-list','--parents','-n','1',GENERALITY_EXPORT).split()==[GENERALITY_EXPORT,CANDIDATE_HEAD],'original_generality_export_object_sole_c4_parent')
    modes=git('ls-files','--format=%(objectmode)','-z');need(all(x in ('100644','100755','120000') for x in modes.split('\0') if x),'submodule_or_unknown_tracked_mode_refused')
    return {'candidate':str(CANDIDATE),'head':CANDIDATE_HEAD,'detached':True,'clean_including_untracked':True,'common_git':str(common),'git_directory':str(gitdir),'pointer':pin,'backlink':bpin,'registration_HEAD':hpin,'merged_into_R':True,'original_export_commit':GENERALITY_EXPORT,'original_export_sole_c4_parent':True,'registration_metadata_not_restore_instruction':True}

def protected_reference(p):
    return any(p==q or p.is_relative_to(q) for q in PROTECTED)

def symlink_resolution(row,entries):
    # Resolve only the closed inventoried metadata graph; never stat/read an external target.
    prefix=CANDIDATE.parts;visited=set();links=0;steps=0
    def target_parts(raw,base):
        value=os.fsdecode(raw)
        if value.startswith('/'):
            components=tuple(x for x in value.split('/') if x)
            need(components[:len(prefix)-1]==prefix[1:],'symlink_absolute_target_outside_candidate')
            return [],list(components[len(prefix)-1:])
        return list(base),value.split('/')
    base=row['relative_path'].split('/')[:-1]
    base,pending=target_parts(base64.b64decode(row['target_base64'],validate=True),base)
    while pending:
        tick();steps+=1;need(steps<=65536,'symlink_component_resolution_cap')
        name=pending.pop(0)
        if name in ('','.'):continue
        if name=='..':
            need(bool(base),'symlink_parent_escapes_candidate');base.pop();continue
        relative='/'.join((*base,name));entry=entries.get(relative)
        need(entry is not None,'symlink_dangling_or_uninventoried_target')
        if entry['kind']=='symlink':
            links+=1;need(links<=40,'symlink_cycle_or_link_cap')
            key=(relative,tuple(pending));need(key not in visited,'symlink_cycle');visited.add(key)
            nextbase,nextparts=target_parts(base64.b64decode(entry['target_base64'],validate=True),base)
            base=nextbase;pending=nextparts+pending
        else:
            need(entry['kind']=='directory' or not any(x not in ('','.') for x in pending),'symlink_nondirectory_component')
            base.append(name)
    relative='/'.join(base) or '.';entry=entries.get(relative)
    need(entry is not None and entry['kind'] in ('directory','regular'),'symlink_final_target_not_closed')
    route=CANDIDATE.joinpath(*base);need(not protected_reference(route),'symlink_final_target_protected')
    return {'state':'resolved_internal_metadata_only','relative_path':relative,'kind':entry['kind'],'target_stat':entry['stat'],'symlinks_followed_in_metadata':links,'components_checked':steps,'external_target_stat_or_body_read':False}

def inventory_tree():
    rows=[];total=0;allocated=0;metadata_size=2;references=[];inodes=set()
    todo=[CANDIDATE]
    needles=[os.fsencode(p) for p in PROTECTED];overlap=max(map(len,needles))+1
    patterns=[re.compile(re.escape(x)+rb'(?=[^A-Za-z0-9_.-])') for x in needles]
    while todo:
        tick();p=todo.pop();s=p.lstat();relative=p.relative_to(CANDIDATE).as_posix()
        need(len(rows)<ENTRY_CAP and len(os.fsencode(relative))<=4096 and s.st_uid==UID and not s.st_mode&0o7000,'tree_entry_bounds_owner_or_special_bits')
        need(not any(x in p.parts for x in ('.codex','.ssh','.aws')) and p.name not in ('auth.json','provider.json','prompt.txt','feedback.txt'),'sensitive_candidate_entry_refused')
        row={'relative_path':relative,'stat':stamp(s)};inodes.add((s.st_dev,s.st_ino))
        if stat.S_ISDIR(s.st_mode):
            need(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_tree_directory')
            need(p==CANDIDATE or p.name!='.git','embedded_Git_directory_refused')
            children=sorted(p.iterdir(),key=lambda q:os.fsencode(q.name));need(len(children)<=ENTRY_CAP,'directory_child_bound')
            row['kind']='directory';row['entries_sha256']=digest(b'\0'.join(os.fsencode(q.name) for q in children));todo.extend(reversed(children));need(stamp(p.lstat())==stamp(s),'directory_listing_race')
        elif stat.S_ISREG(s.st_mode):
            need(p==CANDIDATE/'.git' or p.name!='.git','embedded_Git_pointer_refused')
            need(s.st_nlink==1 and 0<=s.st_size<=FILE_CAP,'regular_hardlink_or_file_cap_refused');total+=s.st_size;need(total<=TREE_CAP,'full_tree_byte_cap');allocated+=s.st_blocks*512
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);h=hashlib.sha256();n=0;tail=b'';refs=set()
            with os.fdopen(fd,'rb') as f:
                need(stamp(os.fstat(f.fileno()))==stamp(s),'tree_file_open_race')
                while True:
                    tick();b=f.read(1024*1024)
                    if not b:
                        if p!=CANDIDATE/'.git':refs.update(i for i,x in enumerate(patterns) if x.search(tail+b'\0'))
                        break
                    n+=len(b);need(n<=s.st_size,'tree_file_read_cap');h.update(b)
                    window=tail+b
                    if p!=CANDIDATE/'.git':
                        refs.update(i for i,x in enumerate(patterns) if x.search(window))
                    tail=window[-overlap:]
                need(n==s.st_size and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'tree_file_nine_stat_or_size_race')
            row.update(kind='regular',bytes=n,sha256=h.hexdigest(),allocated_bytes=s.st_blocks*512)
            if refs:references.append({'relative_path':relative,'kind':'regular_literal_mentions','protected_indices':sorted(refs),'sha256':h.hexdigest(),'historical_literal_does_not_itself_prove_physical_dependency':True})
        elif stat.S_ISLNK(s.st_mode):
            target=os.readlink(p);raw=os.fsencode(target);need(len(raw)<=4096 and stamp(p.lstat())==stamp(s),'symlink_metadata_cap_or_race')
            route=Path(os.path.normpath(str(p.parent/target)));need(route.is_absolute(),'symlink_target_absolute_resolution')
            # Never follow or copy a link target. Explicitly refuse external/protected links.
            inside=route.is_relative_to(CANDIDATE) and not protected_reference(route)
            row.update(kind='symlink',target_base64=base64.b64encode(raw).decode(),target_bytes=len(raw),target_sha256=digest(raw),lexically_inside_candidate=inside)
            if not inside:references.append({'relative_path':relative,'kind':'external_or_protected_symlink','target_sha256':digest(raw)})
        else:raise ValueError('nonregular_tree_entry_refused')
        metadata_size+=len(metadata_bytes(row));need(metadata_size<=METADATA_CAP,'tree_metadata_8MiB_cap');rows.append(row)
    entries={row['relative_path']:row for row in rows}
    for row in rows:
        if row['kind']!='symlink':continue
        try:row['target_metadata_resolution']=symlink_resolution(row,entries)
        except (ValueError,OSError,KeyError,TypeError,UnicodeError) as exc:
            row['target_metadata_resolution']={'state':'unknown_or_refused','error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode()),'external_target_stat_or_body_read':False}
            references.append({'relative_path':row['relative_path'],'kind':'ultimate_symlink_resolution_unknown_or_refused','target_sha256':row['target_sha256']})
    need(len(metadata_bytes(rows))<=METADATA_CAP,'resolved_tree_metadata_8MiB_cap')
    return {'entries':rows,'entry_count':len(rows),'regular_bytes':total,'allocated_regular_bytes':allocated,'all_regular_nlink1':True,'ignored_entries_included':True,'protected_reference_observations':references,'mandatory_root_Git_pointer_is_registration_provenance':True},inodes

def alias_bytes(p,cap):
    tick();s=p.lstat();need(stat.S_ISREG(s.st_mode),'owned_alias_file_regular')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'owned_alias_open_race');b=f.read(cap+1)
        need(len(b)<=cap and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'owned_alias_read_cap_or_race')
    return b

def consumer_inventory(transport,inodes):
    matches=[];unknowns=[];owned=0;seen=0;fdcount=0;bytes_read=0
    needles=[os.fsencode(p) for p in (CANDIDATE,SOURCE,RAW,H)]
    def target_match(target,s):
        route=target.removesuffix(' (deleted)')
        return any(x in os.fsencode(route) for x in needles) or (s.st_dev,s.st_ino) in inodes
    for p in Path('/proc').iterdir():
        tick();seen+=1;need(seen<=32768,'process_count_cap')
        if not p.name.isdecimal() or int(p.name) in (transport['self']['pid'],transport['parent']['pid']):continue
        proof=None
        try:
            ps=p.stat()
            if ps.st_uid!=UID:continue
            owned+=1;need(owned<=4096,'owned_process_count_cap');proof={'pid':int(p.name),'uid':UID,'proc_inode':ps.st_ino}
            command=owned_cmdline(p,ps);bytes_read+=len(command);need(bytes_read<=32*1024**2,'process_metadata_read_cap')
            argv=command[:-1].split(b'\0') if command else []
            if not argv or not argv[0]:
                proof=inactive_owned_identity(p,ps);need(owned_cmdline(p,ps)==command,'inactive_command_continuity');continue
            found=any(x in arg for x in needles for arg in argv);routes=[]
            for name in ('cwd','root','exe'):
                q=p/name;target=os.readlink(q);s=q.stat();routes.append((name,digest(os.fsencode(target)),s.st_dev,s.st_ino));found=found or target_match(target,s)
            fds=[]
            for q in sorted((p/'fd').iterdir(),key=lambda q:q.name):
                tick();fdcount+=1;need(fdcount<=65536 and q.name.isdecimal(),'FD_inventory_cap_or_name');target=os.readlink(q);s=q.stat();fds.append((q.name,digest(os.fsencode(target)),s.st_dev,s.st_ino));found=found or target_match(target,s)
            maps=alias_bytes(p/'maps',4*1024**2);bytes_read+=len(maps);need(bytes_read<=32*1024**2,'process_metadata_read_cap')
            for line in maps.splitlines():
                parts=line.split(None,5);need(len(parts) in (5,6),'maps_field_count');device=parts[3].split(b':');need(len(device)==2 and parts[4].isdigit(),'maps_device_inode')
                if int(parts[4]):
                    device_id=os.makedev(int(device[0],16),int(device[1],16));found=found or (device_id,int(parts[4])) in inodes
                if len(parts)==6:found=found or any(x in parts[5] for x in needles)
            # Hash-only routing metadata; no argv/maps/FD target text is returned.
            signature=digest(metadata_bytes({'routes':routes,'fds':fds,'maps_sha256':digest(maps)}))
            if found:
                identity,current_argv,exe=process_identity(int(p.name));need(identity['proc_inode']==ps.st_ino and identity['cmdline_sha256']==digest(command) and current_argv==argv,'matching_consumer_identity_continuity');proof=identity
                raw=kernel_bytes(p/'stat',8192,UID);parts=raw.rsplit(b')',1)[1].split();need(len(parts)>=20 and int(parts[19])==identity['start_ticks'],'matching_consumer_start_race')
                if parts[0] not in (b'Z',b'X'):
                    need(len(matches)<128,'matching_consumers_cap');matches.append({**identity,'alias_metadata_sha256':signature})
            need(owned_cmdline(p,ps)==command and p.stat().st_uid==UID and p.stat().st_ino==ps.st_ino,'owned_consumer_command_directory_continuity')
            # Detect routing changes before claiming non-use, without a UID fallback.
            for name,h,dev,ino in routes:
                q=p/name;s=q.stat();need(digest(os.fsencode(os.readlink(q)))==h and (s.st_dev,s.st_ino)==(dev,ino),'process_route_race')
            nowfds=[]
            for q in sorted((p/'fd').iterdir(),key=lambda q:q.name):
                tick();need(len(nowfds)<65536 and q.name.isdecimal(),'FD_continuity_count_cap');target=os.readlink(q);s=q.stat();nowfds.append((q.name,digest(os.fsencode(target)),s.st_dev,s.st_ino))
            need(nowfds==fds and alias_bytes(p/'maps',4*1024**2)==maps,'FD_maps_continuity')
        except (OSError,ValueError,IndexError,UnicodeError) as exc:
            if isinstance(exc,(FileNotFoundError,ProcessLookupError)) and proof is None:continue
            need(len(unknowns)<128,'process_unknown_cap');unknowns.append({**(proof or {}),'state':'unknown','error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())})
    return {'state':'unknown' if unknowns else 'observed','owned_checked':owned,'matching_live_consumers':matches,'unknowns':unknowns,'no_live_owned_candidate_SOURCE_RAW_H_consumers':not matches and not unknowns,'cwd_root_exe_FD_maps_checked':True,'other_users_not_inspected':True,'partial_or_other_user_inventory_not_deletion_clearance':True,'raw_process_bodies_returned':False}

def native_snapshot():
    out={}
    for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
        b,pin=original(BASE/'lact-host-lease'/(name+'.meta.json'),32768);d=native_projection(strict(b),name)
        _,lease=original(BASE/'lact-host-lease'/(name+'.lease'),4096);identity=selected_lease_identity(lease);proof=locks(identity);need(not proof['matching_rows'],'native_kernel_holder_or_waiter');daemonproof=daemon_ready(d['daemon_pid'],identity)
        out[name]={'native':d,'metadata_original':pin,'lease_original':lease,'kernel':proof,'daemon':daemonproof}
    return out

def native_continuity(before):
    after=native_snapshot()
    for name,v in before.items():
        a=after[name];need(all(a[k]==v[k] for k in ('native','metadata_original','lease_original','daemon')) and not a['kernel']['matching_rows'],'native_release_generation_inode_FD9_continuity')
    return after

def resources():
    mem=kernel_bytes(Path('/proc/meminfo'),65536,0).decode();available=next(int(x.split()[1])*1024 for x in mem.splitlines() if x.startswith('MemAvailable:'))
    free={p:shutil.disk_usage(p).free for p in ('/data1','/data')}
    return {'MemAvailable':available,'free_bytes':free,'memory_80GiB_floor_met':available>=80*1024**3,'original_data1_21GiB_floor_met':free['/data1']>=21*1024**3,'data_after_2GiB_archive_reserve_24GiB_floor_met':free['/data']-TREE_CAP>=24*1024**3,'backup_reserve_bytes':TREE_CAP,'original_index_floors_unchanged':True,'data1_shortfall_does_not_itself_block_backup_preflight':True}

def observe():
    need(sys.platform=='linux' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10','native_owned_account_host')
    need(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12') and sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_isolated_unoptimized_python')
    transport=transport_identity();route=output_route();OBSERVED['resources_before']=resources()
    sources=current_sources();tools={p:root_tool_pin(p,n,h) for p,(n,h) in NATIVE.items()};home=home_startup();native=native_snapshot();registration=candidate_registration()
    controls={}
    for p,n,h in ((H,38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),(G,14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),(SUP,8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'),(RAW/'manifest.json',292401,'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1')):
        b,pin=original(p,n);need(len(b)==n and digest(b)==h,'unchanged_current_control_M2');controls[str(p)]=pin
    first,inodes=inventory_tree();processes=consumer_inventory(transport,inodes);second,afterinodes=inventory_tree();need(first==second and inodes==afterinodes,'full_candidate_SHA_nine_stat_path_closure')
    need(candidate_registration()==registration and current_sources()==sources and home_startup()==home,'candidate_primary_source_ER_HOME_continuity');after_native=native_continuity(native)
    for p,(n,h) in NATIVE.items():need(root_tool_pin(p,n,h)==tools[p],'native_tools_continuity')
    for p,pin in controls.items():_,after=original(Path(p),pin['bytes']);need(after==pin,'current_control_M2_continuity')
    need(transport_identity()==transport,'self_immediate_parent_identity_continuity');need(output_route()==route,'fresh_metadata_output_route_continuity')
    after_resources=resources();OBSERVED['resources_after']=after_resources
    references=first['protected_reference_observations'];eligible=processes['no_live_owned_candidate_SOURCE_RAW_H_consumers'] and not references and after_resources['memory_80GiB_floor_met'] and after_resources['data_after_2GiB_archive_reserve_24GiB_floor_met']
    # Only metadata creation here. The entire candidate and Git sources remain untouched.
    manifest={'format':'swdb.lanl17-generality-worktree-recovery-preflight-inventory.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':registration,'tree':first,'snapshot_sha256':payload_digest(first),'source':sources,'native_tools':tools,'startup_HOME':home,'native_before':native,'native_after':after_native,'controls_M2':controls,'owned_consumer_inventory':processes,'resources':OBSERVED,'transport':transport,'backup_eligibility_only':eligible,'backup_created':False,'removal_admitted':False,'index_clearance':False,'scientific_admission':False,'parent_dependency_and_ownership_history_approval_not_inferred':True}
    blob=metadata_bytes(manifest);need(len(blob)<=METADATA_CAP,'full_metadata_8MiB_cap');os.mkdir(OUTPUT,0o700)
    path=OUTPUT/'preflight-inventory.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
    reread,pin=original(path,METADATA_CAP);need(reread==blob,'metadata_original_readback')
    return {'format':'swdb.lanl17-generality-worktree-recovery-preflight.v1','checked_utc':manifest['checked_utc'],'metadata_observation_completed':True,'state':'eligible_for_separate_backup_review' if eligible else 'unknown' if processes['unknowns'] else 'not_eligible','backup_eligibility_only':eligible,'backup_created':False,'deletion_or_removal_admitted':False,'index_clearance':False,'scientific_admission':False,'candidate':str(CANDIDATE),'head':CANDIDATE_HEAD,'entry_count':first['entry_count'],'regular_bytes':first['regular_bytes'],'allocated_regular_bytes':first['allocated_regular_bytes'],'snapshot_sha256':manifest['snapshot_sha256'],'remote_metadata_original':pin,'protected_reference_count':len(references),'owned_consumers_count':len(processes['matching_live_consumers']),'owned_process_unknown_count':len(processes['unknowns']),'resources':OBSERVED,'metadata_manifest_body_not_returned':True,'raw_auth_provider_source_record_bodies_not_returned':True,'other_users_and_parent_dependency_approval_not_inferred':True,'point_in_time_only_requires_fresh_backup_and_final_no_use_review':True}

def main():
    global ARGS
    p=Parser(add_help=False);p.add_argument('--source-sha256',required=True);p.add_argument('--output-directory',required=True);ARGS=p.parse_args();hex64(ARGS.source_sha256)
    result=observe();b=metadata_bytes(result);need(len(b)<=65536,'compact_return_cap');sys.stdout.buffer.write(b)

def interrupted(number,frame):raise ValueError('recovery_preflight_signal_or_deadline')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(180)
try:main()
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,RecursionError,StopIteration,subprocess.SubprocessError) as exc:
    print(json.dumps({'format':'swdb.lanl17-generality-worktree-recovery-preflight.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_observation_completed':False,'state':'unknown','backup_eligibility_only':False,'backup_created':False,'deletion_or_removal_admitted':False,'index_clearance':False,'scientific_admission':False,'resources_observed_before_error':OBSERVED,'error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())},sort_keys=True,allow_nan=False))
