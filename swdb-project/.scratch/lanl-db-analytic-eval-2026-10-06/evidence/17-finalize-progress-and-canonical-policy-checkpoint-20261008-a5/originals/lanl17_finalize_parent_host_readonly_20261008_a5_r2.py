"""2026-10-08 ET: bounded future FINALIZE host preflight R2; read-only metadata, not admission."""
import datetime, hashlib, json, os, pwd, re, shutil, signal, socket, stat, subprocess, sys, time
from pathlib import Path

UID=114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
BASE=Path('/data1/yanruj')
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
SOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a5'
PRIMARY=BASE/'ArchEvolve'
M2_SHA='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
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
def run(argv):
    tick();p=subprocess.run(argv,capture_output=True,timeout=min(15,max(.1,END-time.monotonic())),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0'},stdin=subprocess.DEVNULL)
    need(p.returncode==0 and len(p.stdout)<=65536 and len(p.stderr)<=65536,'metadata_command_exit_or_cap');return p.stdout.decode()

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

def transport_identity():
    need(len(sys.argv)==2 and sys.argv[0]=='-c' and re.fullmatch(r'[0-9a-f]{64}',sys.argv[1]) is not None,'source_SHA_argument')
    own,argv,exe=process_identity(os.getpid())
    need(exe=='/usr/bin/python3.12' and len(argv)==6 and argv[:4]==[b'/usr/bin/python3.12',b'-I',b'-B',b'-c'],'native_inline_self_argv')
    source=argv[4];shaarg=argv[5];need(digest(source)==sys.argv[1] and shaarg==sys.argv[1].encode(),'self_exact_inline_source_SHA')
    need(own['ppid']==os.getppid(),'self_actual_parent')
    parent,pargv,pexe=process_identity(own['ppid'])
    expected=[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=60s',b'60s',*argv]
    need(pexe=='/usr/bin/timeout' and pargv==expected,'exact_owned_immediate_GNU_timeout_parent')
    return {'self':own,'parent':parent,'inline_source_sha256':sys.argv[1],'only_exact_immediate_timeout_parent_excluded':True}

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

def read():
    need(os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10','native_account_host')
    transport=transport_identity()
    sources={}
    for p in (PRIMARY,SOURCE):
        need(p.resolve(strict=True)==p,'source_canonical')
        x={'branch':run(['/usr/bin/git','-C',str(p),'rev-parse','--abbrev-ref','HEAD']).strip(),'head':run(['/usr/bin/git','-C',str(p),'rev-parse','HEAD']).strip(),'tracked_status':run(['/usr/bin/git','-C',str(p),'status','--porcelain','--untracked-files=no'])}
        need(x['head']==R and x['tracked_status']=='','frozen_source_R_clean');sources[str(p)]=x
    need(sources[str(PRIMARY)]['branch']=='yanrujhou_main','primary_branch')
    origin=run(['/usr/bin/git','-C',str(PRIMARY),'rev-parse','origin/yanrujhou_main']).strip();need(origin==R,'primary_origin_R')
    b,m2pin=original(RAW/'manifest.json',400000);need(len(b)==292401 and digest(b)==M2_SHA,'exact_original_M2')
    leases={};lease_pins={};lock_proofs={};daemons={};identities={}
    for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
        p=BASE/'lact-host-lease'/(name+'.meta.json');raw,pin=original(p,32768);d=strict(raw)
        leases[name]=native_projection(d,name);lease_pins[name]=pin
        lp=BASE/'lact-host-lease'/(name+'.lease');_,lpin=original(lp,4096);identity=selected_lease_identity(lpin);identities[name]=identity
        proof=locks(identity);need(not proof['matching_rows'],'all_three_no_matching_kernel_holder_or_waiter')
        lock_proofs[name]={'lease_original':lpin,'proof_before':proof}
        daemons[name]=daemon_ready(leases[name]['daemon_pid'],identity)
    stops={}
    for n in range(1,5):
        cid=f'extensa-gem5-bfs-20261006-p{n}';p=RAW/'attempts'/cid/'attempt-1'/'stopped-receipt.json';b,pin=original(p,65536);d=strict(b)
        seal=d.get('identity_sha256');v=json.dumps({k:v for k,v in d.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode();need(digest(v)==seal,'original_stop_true_seal')
        need(d['campaign']==cid and d['source_commit']==R and d['source_clean_after'] is True and d['public_exit_code']==d['runner_exit_code']==0 and not d.get('infrastructure_error') and not d['process_cleanup']['survivors'],'all_four_normal_stops')
        stops[cid]={'original':pin,'identity_sha256':seal,'ended_utc':d['ended_utc']}
    process_matches=[];own_count=0
    for p in Path('/proc').iterdir():
        tick()
        if not p.name.isdecimal() or int(p.name) in (transport['self']['pid'],transport['parent']['pid']): continue
        try:
            if p.stat().st_uid!=UID: continue
            own_count+=1;need(own_count<=4096,'owned_process_count_cap')
            with (p/'cmdline').open('rb') as f:b=f.read(65537)
            need(len(b)<=65536 and p.stat().st_uid==UID,'owned_cmdline_cap_or_identity_changed')
            if any(x.encode() in b for x in (str(SOURCE),str(RAW),'/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py')):
                fields=(p/'stat').read_text().rsplit(')',1)[1].split()
                if fields[0] not in ('Z','X'):process_matches.append({'pid':int(p.name),'state':fields[0],'start_ticks':int(fields[19])})
        except (FileNotFoundError,ProcessLookupError): continue
    need(not process_matches,'no_owned_source_or_campaign_consumers')
    absent={str(p):not os.path.lexists(p) for p in (Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5'),BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a5',RAW/'final-export.json',RAW/'final-agreement-report.argv.json',RAW/'final-agreement-report.stdout',RAW/'final-agreement-report.stderr',RAW/'final-agreement-report.exit-code.txt')};need(all(absent.values()),'fresh_FINALIZE_routes')
    mem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k=='MemAvailable'}
    free={p:shutil.disk_usage(p).free for p in ('/data1','/data')};need(mem['MemAvailable']>=85899345920 and free['/data1']>=22548578304 and free['/data']>=25769803776,'unchanged_serial_floors')
    procs=run(['/usr/bin/ps','-eo','user,pid,ppid,pcpu,pmem,comm','--sort=-pcpu']).splitlines()[:35]
    cpu=run(['/usr/bin/mpstat','-P','ALL','1','1']) if Path('/usr/bin/mpstat').exists() else 'unavailable'
    gpu=run(['/usr/bin/nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader']) if Path('/usr/bin/nvidia-smi').exists() else 'unavailable'
    for name,d in leases.items():
        raw,pin=original(BASE/'lact-host-lease'/(name+'.meta.json'),32768)
        need(native_projection(strict(raw),name)==d and pin==lease_pins[name],'native_lease_continuity')
        p=Path(lock_proofs[name]['lease_original']['path']);_,pin=original(p,4096)
        need(pin==lock_proofs[name]['lease_original'],'native_lockfile_continuity')
        proof=locks(identities[name]);need(not proof['matching_rows'],'after_no_kernel_holder_or_waiter')
        lock_proofs[name]['proof_after']=proof
        after=daemon_ready(d['daemon_pid'],identities[name]);need(after==daemons[name],'daemon_identity_FD9_continuity')
    need(transport_identity()==transport,'exact_self_timeout_transport_continuity')
    return {'format':'swdb.lanl17-finalize-parent-host-readonly.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host_metadata_ready':True,'scientific_admission':False,'source':sources,'primary_origin':origin,'manifest_original':m2pin,'leases':leases,'lease_originals':lease_pins,'kernel_locks':lock_proofs,'transport_identity':transport,'daemon_FD9':daemons,'four_stop_originals':stops,'owned_processes_checked':own_count,'live_source_campaign_consumers':process_matches,'finalize_routes_absent':absent,'mem':mem,'free_bytes':free,'load':os.getloadavg(),'processes_top35_comm_only':procs,'cpu_activity':cpu,'gpu':gpu,'point_in_time_only':True,'requires_parent_exclusive_no_reuse_and_fresh_original_admission':True,'source_F6_native_controls_hooks_proofs_rechecked_by_original_FINALIZE_bootstrap':True,'native_metadata_projection_closed_scalar_only':True,'raw_body_auth_log_or_other_user_cmdline_returned':False}
def interrupted(n,f):raise ValueError('host_metadata_signal_or_deadline')
for n in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(n,interrupted)
signal.alarm(45)
try:
    d=read();b=(json.dumps(d,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=65536,'host_output_cap');sys.stdout.buffer.write(b)
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,subprocess.SubprocessError) as e:
    print(json.dumps({'format':'swdb.lanl17-finalize-parent-host-readonly.v1','host_metadata_ready':False,'state':'unknown','scientific_admission':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason_sha256':digest(str(e).encode()),'error_class':type(e).__name__},sort_keys=True))
