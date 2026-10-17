"""Created 2026-10-09 ET. SOURCE ONLY four exact PID/inode public metadata diagnostic.
No argv arguments, env/auth/maps/status bodies, target-file contents, mutation or waiver.
Observational root-owned kernel stat/status reads never alter native/no-use proof guards.
"""
import argparse,datetime,hashlib,json,os,pwd,re,signal,socket,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
BASE=Path('/data1/yanruj');PRIMARY=BASE/'ArchEvolve';SOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a5';ER=BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a5'
INPUT={'expected_ER_commit':'f5014746da61005be2d75cee16f8a834afa19321'}
H=BASE/'lanl17-control-cleanup60-20261007-a4.py';M2=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json')
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
ARGS=None
PUBLIC_COMMANDS={'python','python3','python3.12','bash','sh','node','codex','claude','timeout','tmux','ssh','git','sudo','strace','nvidia-smi','sleep','tee'}
SELECTED=[{'error_class': 'PermissionError', 'pid': 359656, 'proc_inode': 37081472, 'reason_sha256': 'b41330758d69c64d53b998a307d178a8c3c44316615b96b2bdda499b5cb4fd40', 'state': 'unknown', 'uid': 114316761}, {'error_class': 'ValueError', 'pid': 2299635, 'proc_inode': 66712273, 'reason_sha256': '681d4d67d6b333a2d7d1cd56f7f040b3484eeabbe3fe14ef9b42f7f4e80b708d', 'state': 'unknown', 'uid': 114316761}, {'error_class': 'PermissionError', 'pid': 2332693, 'proc_inode': 66980537, 'reason_sha256': 'ec30fdb393a0e837624c79a38a0bfaae00cd0928cc50d70ddd20050d10d4dbb3', 'state': 'unknown', 'uid': 114316761}, {'error_class': 'ValueError', 'pid': 3570805, 'proc_inode': 55298043, 'reason_sha256': '681d4d67d6b333a2d7d1cd56f7f040b3484eeabbe3fe14ef9b42f7f4e80b708d', 'state': 'unknown', 'uid': 114316761}]
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

def hex64(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'actual_SHA');return v

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

def metadata_bytes(v):
    return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()

def error_metadata(exc,path):
    return {'state':'unknown','error_class':type(exc).__name__,'errno':getattr(exc,'errno',None),'path_sha256':digest(os.fsencode(path)),'reason_sha256':digest(str(exc).encode())}

def public_class(raw):
    name=os.path.basename(os.fsdecode(raw).removesuffix(' (deleted)'))
    return name if name in PUBLIC_COMMANDS else 'unclassified_public_executable'

def selected_file(p,name,cap):
    # This observational reader is never used by native_snapshot or no-use proofs.
    need(name in ('stat','status'),'selected_kernel_file_name');q=p/name;tick();s=q.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid in (0,UID),'selected_kernel_file_regular_allowed_observational_owner')
    fd=os.open(q,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'selected_kernel_file_open_race');raw=f.read(cap+1)
        need(len(raw)<=cap and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(q.lstat()),'selected_kernel_file_cap_stat_race')
    return raw,{'file_stat':stamp(s),'file_owner_equals_account':s.st_uid==UID,'root_owner_is_observation_only_not_guard_waiver':s.st_uid==0}

def stat_projection(raw,pid):
    need(raw.endswith(b'\n') and raw.split(b' ',1)[0]==str(pid).encode(),'selected_stat_PID_shape');end=raw.rfind(b')');start=raw.find(b'(');need(0<start<end,'selected_stat_comm_shape')
    comm=raw[start+1:end];need(len(comm)<=64,'public_comm_cap');tail=raw[end+1:].split();need(len(tail)>=20 and re.fullmatch(rb'[RSDTtZXxIWPK]',tail[0]) is not None,'selected_stat_state_shape')
    parent=int(tail[1]);ticks=int(tail[19]);need(0<=parent<2**31 and 0<ticks<2**63,'selected_stat_identity_values')
    return {'pid':pid,'ppid':parent,'start_ticks':ticks,'state_code':tail[0].decode('ascii'),'comm':comm.decode('utf-8')}

def status_projection(raw,pid):
    need(raw.endswith(b'\n'),'selected_status_complete');wanted={'Name','State','Pid','PPid','Tgid','Uid','Gid','CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs','Seccomp','CoreDumping','Dumpable'};out={}
    for line in raw.splitlines():
        tick();key,sep,value=line.partition(b':')
        if not sep:continue
        name=key.decode('ascii')
        if name not in wanted:continue
        need(name not in out,'selected_status_duplicate_field');value=value.strip()
        if name=='Name':need(len(value)<=256,'public_status_Name_cap');out[name]=value.decode('utf-8')
        elif name=='State':need(value and re.fullmatch(rb'[RSDTtZXxIWPK]',value[:1]) is not None,'status_state');out[name]=value[:1].decode('ascii')
        elif name in ('Uid','Gid'):
            vals=value.split();need(len(vals)==4 and all(x.isdigit() for x in vals),'status_UID_GID_shape');nums=[int(x) for x in vals];need(all(0<=x<2**32 for x in nums),'status_UID_GID_cap');out[name]=nums
        elif name.startswith('Cap'):need(re.fullmatch(rb'[0-9a-fA-F]{1,16}',value) is not None,'status_capabilities_shape');out[name]=value.decode('ascii')
        else:need(value.isdigit() and 0<=int(value)<2**32,'status_integer_metadata');out[name]=int(value)
    need(out.get('Pid')==pid and all(x in out for x in ('Name','State','Uid','Gid')),'selected_status_PID_identity');return out

def argv0_metadata(p):
    # Read exactly through first NUL one byte at a time; never read argv1 or later.
    q=p/'cmdline';tick();s=q.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid in (0,UID),'selected_cmdline_regular_allowed_observational_owner');fd=os.open(q,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);raw=bytearray();terminated=False
    with os.fdopen(fd,'rb',buffering=0) as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'selected_argv0_open_race')
        for unused in range(4097):
            tick();b=f.read(1)
            if not b:break
            if b==b'\0':terminated=True;break
            raw.extend(b)
        need(len(raw)<=4096 and (terminated or not raw) and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(q.lstat()),'selected_argv0_cap_stat_race')
    return {'state':'observed','argv0_bytes':len(raw),'argv0_sha256':digest(raw),'argv0_public_classification':public_class(bytes(raw)) if raw else 'empty_argv0_observation_only','first_argument_only_no_later_arguments_read':True,'file_stat':stamp(s)}

def alias_metadata(p,name):
    need(name in ('cwd','root','exe'),'selected_alias_name');q=p/name;tick();link_stat=None
    try:
        s=q.lstat();link_stat=stamp(s);need(stat.S_ISLNK(s.st_mode) and s.st_uid in (0,UID),'selected_kernel_alias_symlink_allowed_observational_owner');target=os.readlink(q);need(len(os.fsencode(target))<=4096 and stamp(q.lstat())==stamp(s),'selected_alias_cap_stat_race')
        out={'state':'observed','alias':name,'link_stat':stamp(s),'target_path_sha256':digest(os.fsencode(target)),'target_body_or_stat_followed':False}
        if name=='exe':out['exe_public_classification']=public_class(os.fsencode(target))
        return out
    except (OSError,ValueError,UnicodeError) as exc:return error_metadata(exc,q)|{'alias':name,'link_stat_if_lstat_succeeded':link_stat}

def operation(p,name,parse,pid):
    try:
        raw,pin=selected_file(p,name,8192 if name=='stat' else 65536);return {'state':'observed','metadata':parse(raw,pid),**pin}
    except (OSError,ValueError,IndexError,UnicodeError) as exc:return error_metadata(exc,p/name)

def diagnose(selector):
    pid=selector['pid'];p=Path('/proc')/str(pid);out={'selector_original':selector,'pid':pid,'state':'unknown','guard_waiver':False,'quiescence_proven':False}
    try:
        tick();s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_ino==selector['proc_inode'] and s.st_uid==selector['uid']==UID,'exact_selected_owned_PID_inode_current');out['proc_directory_stat_before']=stamp(s)
        first=operation(p,'stat',stat_projection,pid);status=operation(p,'status',status_projection,pid);out['kernel_stat_before']=first;out['status_before']=status
        try:argv=argv0_metadata(p)
        except (OSError,ValueError,UnicodeError) as exc:argv=error_metadata(exc,p/'cmdline')
        out['argv0']=argv;aliases={name:alias_metadata(p,name) for name in ('cwd','root','exe')};out['alias_permissions']=aliases
        final=operation(p,'stat',stat_projection,pid);status_after=operation(p,'status',status_projection,pid);out['kernel_stat_after']=final;out['status_after']=status_after
        now=p.lstat();out['proc_directory_stat_after']=stamp(now);need(stamp(now)==stamp(s) and now.st_ino==selector['proc_inode'],'selected_directory_identity_race')
        need(first['state']==final['state']=='observed' and first['metadata']['pid']==final['metadata']['pid']==pid and first['metadata']['start_ticks']==final['metadata']['start_ticks'],'selected_start_identity_unknown_or_reused')
        need(status['state']==status_after['state']=='observed' and status['metadata']['Uid']==status_after['metadata']['Uid'] and status['metadata']['Gid']==status_after['metadata']['Gid'],'selected_status_identity_race_or_unknown')
        for name,old in aliases.items():need(alias_metadata(p,name)==old,'selected_alias_observation_race')
        if argv['state']=='observed':need(argv0_metadata(p)==argv,'selected_argv0_continuity')
        out['state']='observed_identity_with_unwaived_permission_diagnostics';out['identity_observation_complete']=True
    except (OSError,ValueError,IndexError,UnicodeError) as exc:out['identity_observation_complete']=False;out['identity_error']=error_metadata(exc,p)
    out['raw_cmdline_status_stat_environment_maps_or_alias_targets_returned']=False;return out

def transport_identity():
    own,argv,exe=process_identity(os.getpid());need(exe=='/usr/bin/python3.12' and len(argv)==7 and argv[:4]==[b'/usr/bin/python3.12',b'-I',b'-B',b'-c'],'exact_native_inline_argv')
    need(argv[5:]==[b'--source-sha256',ARGS.source_sha256.encode()] and digest(argv[4])==ARGS.source_sha256 and own['ppid']==os.getppid(),'exact_self_source_argument');parent,pargv,pexe=process_identity(own['ppid'])
    need(pexe=='/usr/bin/timeout' and pargv==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=60s',b'60s',*argv],'exact_GNU60_parent');return {'self':own,'parent':parent,'source_sha256':ARGS.source_sha256}

def controls():
    out={}
    for p,n,h in ((H,38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),(M2,292401,'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1')):
        raw,pin=original(p,n);need(len(raw)==n and digest(raw)==h,'current_H_M2_pins');out[str(p)]=pin
    return out

def observe():
    need(sys.platform=='linux' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10' and sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_owned_isolated_account')
    transport=transport_identity();sources=current_sources();native=native_snapshot();control=controls();gitpin=root_tool_pin('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb');rows=[diagnose(x) for x in SELECTED]
    after_native=native_continuity(native);need(current_sources()==sources and controls()==control and transport_identity()==transport and root_tool_pin('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb')==gitpin,'current_source_H_M2_native_Git_transport_continuity')
    result={'format':'swdb.lanl17-generality-exact-four-process-public-metadata-diagnostic.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_observation_completed':True,'state':'bounded_selected_process_diagnostics','kernel_release':os.uname().release,'source':sources,'current_H_M2':control,'native_before':native,'native_after':after_native,'selected_processes':rows,'observational_root_owned_stat_status_reads_only':True,'native_and_no_use_kernel_owner_guard_unchanged':True,'no_permission_owner_state_or_name_waiver':True,'other_PIDs_not_diagnosed':True,'no_kill_reap_attach_or_environment_read':True,'backup_eligibility_only':False,'backup_created':False,'removal_admitted':False,'index_clearance':False,'scientific_admission':False}
    need(len(metadata_bytes(result))<=65536,'bounded_diagnostic_return');return result

def main():
    global ARGS
    p=Parser(add_help=False);p.add_argument('--source-sha256',required=True);ARGS=p.parse_args();hex64(ARGS.source_sha256);sys.stdout.buffer.write(metadata_bytes(observe()))

def interrupted(number,frame):raise ValueError('selected_process_metadata_deadline_or_signal')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(45)
try:main()
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,RecursionError,StopIteration,subprocess.SubprocessError) as exc:
    print(json.dumps({'format':'swdb.lanl17-generality-exact-four-process-public-metadata-diagnostic.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_observation_completed':False,'state':'unknown','backup_eligibility_only':False,'backup_created':False,'removal_admitted':False,'index_clearance':False,'scientific_admission':False,'error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())},sort_keys=True,allow_nan=False))
