"""Source-only bounded native node0 release observation; no lock or file mutation."""
import base64, datetime, hashlib, json, os, pwd, re, signal, socket, stat, sys, time
from pathlib import Path
UID=114316761
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
BASE=Path('/data1/yanruj')
META=BASE/'lact-host-lease/mbit10-evaluation-node0.meta.json'
LEASE=BASE/'lact-host-lease/mbit10-evaluation-node0.lease'
A=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/attempts/extensa-gem5-bfs-20261006-p1/attempt-1')
R='5e12a9796432654d88def24ecea617d16ca605b2'
M2='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
DISPATCH='ee2d7bebe5a8003403a136b3fd8f62b1d72b743b6b47c1f8f97c4abb31ac53dd'
GENERATION=511
class Refused(ValueError): pass
def need(ok,code):
    if not ok:raise Refused(code)

def tick():need(time.monotonic()<END,'query_deadline')

def stamp(s):return {k:getattr(s,'st_'+k) for k in FIELDS}

def canonical(p):
    need(p.is_absolute() and p.resolve(strict=True)==p
         and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_route')

def metadata(p,cap):
    tick();canonical(p);s=p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1
         and not s.st_mode&0o7000 and 0<=s.st_size<=cap,'metadata_identity_or_cap')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_changed');b=f.read(cap+1)
        need(len(b)==s.st_size<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),
             'metadata_returned_bytes_or_stat_changed')
    return b,{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'stat':stamp(s)}

def strict(b):
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'duplicate_JSON_key');d[k]=v
        return d
    def bad(value):raise Refused('nonfinite_JSON')
    v=json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
    need(type(v) is dict,'metadata_object_required');return v

def digest(b): return hashlib.sha256(b).hexdigest()
def utc(v):
    need(type(v) is str and bool(v),'UTC_missing')
    t=datetime.datetime.fromisoformat(v.replace('Z','+00:00'));need(t.tzinfo is not None,'UTC_offset_missing');return t

def kernel_bytes(p,cap,owner):
    tick();s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==owner,'kernel_identity')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'kernel_open_changed');b=f.read(cap+1)
        need(len(b)<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'kernel_cap_or_stat_changed')
    return b

def lease_identity():
    tick();canonical(LEASE);s=LEASE.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000,'lease_identity')
    return {'path':str(LEASE),'stat':stamp(s),'device_major':os.major(s.st_dev),'device_minor':os.minor(s.st_dev),'inode':s.st_ino}

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
        result.update(FD9='present',FD9_route_sha256=digest(os.fsencode(target)),FD9_route_matches_selected_lease=target==str(LEASE),FD9_matches_selected_lease=False)
        if target==str(LEASE):
            fs=fd.stat();need(stat.S_ISREG(fs.st_mode) and fs.st_uid==UID,'FD9_type_owner')
            result['FD9_stat']=stamp(fs);result['FD9_matches_selected_lease']=(fs.st_dev,fs.st_ino)==(identity['stat']['dev'],identity['inode'])
            need(result['FD9_matches_selected_lease'],'FD9_same_route_different_inode')
    need(p.stat().st_ino==s.st_ino and p.stat().st_uid==UID,'daemon_proc_changed')
    b2=kernel_bytes(p/'stat',8192,UID);need(int(b2.rsplit(b')',1)[1].split()[19])==start,'daemon_PID_reused')
    return result

def artifact(name,cap,kind):
    p=A/name
    if not os.path.lexists(p):return {'present':False,'path':str(p)},None
    b,pin=metadata(p,cap);out={'present':True,'original_file_pin':pin}
    if kind=='integer':need(re.fullmatch(rb'-?[0-9]+\s*',b) is not None,'integer_exit_bytes');v=int(b);out['integer']=v
    else:
        v=strict(b)
        if kind=='lane':
            x=v.get('socket_lane');need(type(x) is dict,'lane_mapping')
            need(type(x.get('node')) is int and x['node']==0 and x.get('job')=='swdb-lanl17-20261007-a5-p1-a1' and x.get('lease_name')=='mbit10-evaluation-node0','lane_scalar_bindings')
            need(type(x.get('lease_generation')) is int and 0<=x['lease_generation']<=2**63-1 and type(x.get('exit_code')) is int and -2**31<=x['exit_code']<2**31,'lane_integer_fields')
            for k in ('started_utc','ended_utc'):
                value=x.get(k);need(value is None or value=='' or (type(value) is str and 0<len(value)<=64 and re.fullmatch(r'[0-9T:.+Z-]+',value) is not None),'lane_UTC_scalar')
                if value:utc(value)
            out['projection']={k:x.get(k) for k in ('node','job','lease_name','lease_generation','started_utc','ended_utc','exit_code')}
            out['record_errors_present']='record_errors' in x
        else:
            expected={'format':'swdb.lanl17-stopped-attempt.v1','campaign':'extensa-gem5-bfs-20261006-p1','source_commit':R,'manifest_sha256':M2,'dispatch_sha256':DISPATCH}
            need(all(v.get(k)==value for k,value in expected.items()),'stopped_scalar_bindings')
            for k in ('started_utc','ended_utc'):
                value=v.get(k);need(type(value) is str and 0<len(value)<=64 and re.fullmatch(r'[0-9T:.+Z-]+',value) is not None,'stopped_UTC_scalar');utc(value)
            need(type(v.get('runner_exit_code')) is int and -2**31<=v['runner_exit_code']<2**31,'stopped_runner_integer')
            need('public_exit_code' in v and (v['public_exit_code'] is None or (type(v['public_exit_code']) is int and -2**31<=v['public_exit_code']<2**31)) and type(v.get('source_clean_after')) is bool,'stopped_public_exit_source_scalar')
            out['projection']={k:v.get(k) for k in (*expected,'started_utc','ended_utc','runner_exit_code','public_exit_code','source_clean_after')}
            error=v.get('infrastructure_error');out['infrastructure_error_present']=error is not None
            if error is not None:out['infrastructure_error_sha256']=digest(json.dumps(error,sort_keys=True,ensure_ascii=True,allow_nan=False).encode())
            cleanup=v.get('process_cleanup');need(type(cleanup) is dict and type(cleanup.get('subreaper')) is bool and type(cleanup.get('terminated_owned_processes')) is list and type(cleanup.get('survivors')) is dict,'cleanup_projection_types')
            need(len(cleanup['terminated_owned_processes'])<=1024 and len(cleanup['survivors'])<=1024,'cleanup_projection_count_cap')
            out['process_cleanup_projection']={'subreaper':cleanup['subreaper'],'terminated_owned_process_count':len(cleanup['terminated_owned_processes']),'survivor_count':len(cleanup['survivors'])}
    return out,v

def observe():
    need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','native_host_account')
    need(Path('/proc/self/exe').resolve()==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_Python_flags')
    result={'format':'swdb.lanl17-native-release-readonly-observation.v1','sealed':False,'scientific_admission':False,'lease_name':'mbit10-evaluation-node0','required_generation':GENERATION,'release_ready':False,'state':'unknown','unknown_reasons':[]}
    snapshots={};values={}
    try:
        identity=lease_identity();b,pin=metadata(META,32768);v=strict(b);lease=v.get('lease');need(type(lease) is dict,'native_lease_mapping')
        need(v.get('state') in ('held','released') and lease.get('lease_name')=='mbit10-evaluation-node0' and type(lease.get('generation')) is int,'native_state_name_generation')
        result['native_metadata']={'raw_base64':base64.b64encode(b).decode('ascii'),'original_file_pin':pin,'state':v['state'],'generation':lease['generation'],'daemon_pid':lease.get('daemon_pid')}
        result['native_lease_file']=identity;firstlocks=locks(identity);firstdaemon=daemon(lease.get('daemon_pid'),identity)
        result['kernel_locks_before']=firstlocks;result['daemon_before']=firstdaemon
        for name,cap,kind in [('lane.json',32768,'lane'),('wrapper.exit-code.txt',64,'integer'),('runner.exit-code.txt',64,'integer'),('stopped-receipt.json',65536,'stopped')]:
            snapshots[name],values[name]=artifact(name,cap,kind)
        result['attempt_metadata']=snapshots
        secondlocks=locks(identity);seconddaemon=daemon(lease.get('daemon_pid'),identity)
        result['kernel_locks_after']=secondlocks;result['daemon_after']=seconddaemon
        b2,pin2=metadata(META,32768);need(b2==b and pin2==pin and lease_identity()==identity,'native_metadata_or_inode_race')
        need(firstlocks==secondlocks and firstdaemon==seconddaemon,'kernel_lock_or_daemon_race')
        for name,cap,kind in [('lane.json',32768,'lane'),('wrapper.exit-code.txt',64,'integer'),('runner.exit-code.txt',64,'integer'),('stopped-receipt.json',65536,'stopped')]:
            again,_=artifact(name,cap,kind);need(again==snapshots[name],'attempt_metadata_race')
        reasons=[]
        if v['state']!='released':reasons.append('native_lease_held')
        if lease['generation']!=GENERATION:reasons.append('native_generation_not511')
        if secondlocks['matching_rows']:reasons.append('native_lease_kernel_lock_or_waiter_present')
        if seconddaemon['FD9_matches_selected_lease']:reasons.append('daemon_FD9_still_open_to_selected_lease')
        if any(not x['present'] for x in snapshots.values()):reasons.append('completed_attempt_metadata_missing')
        if not reasons:
            lane=values['lane.json']['socket_lane'];stop=values['stopped-receipt.json'];wrapper=values['wrapper.exit-code.txt'];runner=values['runner.exit-code.txt']
            need(lane.get('node')==0 and lane.get('lease_name')=='mbit10-evaluation-node0' and type(lane.get('lease_generation')) is int and lane['lease_generation']==GENERATION and lane.get('job')=='swdb-lanl17-20261007-a5-p1-a1','final_lane_binding')
            need(type(lane.get('exit_code')) is int and lane['exit_code']!=-1,'final_lane_exit_missing')
            ended=utc(lane.get('ended_utc'));need(ended>=utc(lane.get('started_utc')),'lane_time_order')
            need(stop.get('format')=='swdb.lanl17-stopped-attempt.v1' and stop.get('campaign')=='extensa-gem5-bfs-20261006-p1' and stop.get('source_commit')==R and stop.get('manifest_sha256')==M2 and stop.get('dispatch_sha256')==DISPATCH,'stopped_binding')
            need(type(stop.get('runner_exit_code')) is int and runner==stop['runner_exit_code'],'runner_stopped_exit_mismatch')
            utc(stop.get('ended_utc'));need(stop.get('source_clean_after') is True,'stopped_source_dirty')
            cleanup=stop.get('process_cleanup');need(type(cleanup) is dict and cleanup.get('subreaper') is True and cleanup.get('survivors')=={},'stopped_owned_cleanup_unknown')
            result['original_exits']={'wrapper':wrapper,'runner':runner,'lane':lane['exit_code'],'public':stop.get('public_exit_code')}
            result['normal_exit_set_only']=wrapper==runner==lane['exit_code']==stop.get('public_exit_code')==0 and 'record_errors' not in lane and stop.get('infrastructure_error') is None
        result['not_ready_reasons']=reasons;result['release_ready']=not reasons;result['state']='release_ready' if not reasons else 'not_release_ready'
    except (OSError,ValueError,KeyError,IndexError,TypeError,UnicodeError) as exc:
        result['unknown_reasons'].append({'class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())});result['state']='unknown';result['release_ready']=False
    result['checked_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['point_in_time_only']=True
    result['requires_parent_node0_no_reuse_and_fresh_before32_before_after_b08']=True
    return result

def interrupted(number,frame):raise Refused('readonly_query_deadline_or_signal')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(45)
try:
    result=observe();encoded=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode();need(len(encoded)<=256*1024,'query_output_cap');sys.stdout.buffer.write(encoded)
except (OSError,ValueError,KeyError,IndexError,TypeError,UnicodeError) as exc:
    sys.stdout.write(json.dumps({'format':'swdb.lanl17-native-release-readonly-observation.v1','sealed':False,'scientific_admission':False,'state':'unknown','release_ready':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())},sort_keys=True)+'\n')
