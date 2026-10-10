"""2026-10-08 ET: SOURCE ONLY bounded FINALIZE phase-health observer.
No completion inference; raw diagnostic/output/record/provider/auth bodies excluded.
"""
import datetime,hashlib,json,os,pwd,re,signal,socket,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
S=Path('/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5')
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
FINALIZE=Path('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5')
R='5e12a9796432654d88def24ecea617d16ca605b2'
H=Path('/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py')
G=Path('/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py')
SUP=Path('/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py')
M2=RAW/'manifest.json'
SOURCE_PINS=((H,38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),(G,14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),(SUP,8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'),(M2,292401,'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'))
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(n) for n in range(1,5))
LEASES=('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')
MAX_PROC=32768
MAX_OWNED=4096
MAX_ROWS=128
class Refused(ValueError):pass
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

def sha(b):return hashlib.sha256(b).hexdigest()
def unknown(exc):return {'state':'unknown','error_class':type(exc).__name__,'reason_sha256':sha(str(exc).encode(errors='replace'))}
def kernel(p,cap,owner):
    tick();s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==owner,'kernel_field_identity')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'kernel_open_changed');b=f.read(cap+1)
        need(len(b)<=cap and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'kernel_field_cap_or_race')
    return b

def fact(p,kind):
    tick()
    if not os.path.lexists(p):return {'state':'absent','path':str(p)}
    try:
        canonical(p);s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000,'phase_file_identity')
        if kind=='stat_only':
            need(s.st_size<=16*1024*1024,'phase_diagnostic_stat_cap')
            return {'state':'present','path':str(p),'stat':stamp(s),'body_read':False}
        cap=64 if kind=='exit' else 32768 if kind=='argv' else 131072
        b,pin=metadata(p,cap);out={'state':'present','file_pin':pin,'body_returned':False}
        if kind=='exit':
            need(re.fullmatch(rb'-?[0-9]+\s*',b) is not None,'exit_integer_bytes');v=int(b);need(-2**31<=v<2**31,'exit_integer_range');out['integer_exit_code']=v
        elif kind=='argv':
            argv=strict(b'{"value":'+b+b'}')['value']
            need(type(argv) is list and 1<=len(argv)<=512 and all(type(v) is str and len(v)<=4096 for v in argv),'public_argv_shape')
            need(argv[:3]==['python3','-m','swdb'] and len(argv)>=4 and argv[3] in ('validate','campaign-export','agreement-report'),'public_argv_command')
            out['public_command']=argv[3];out['argument_count']=len(argv)
        else:strict(b)  # Compact control JSON only; no arbitrary fields projected.
        return out
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:return {'path':str(p),**unknown(exc)}

def git_facts():
    canonical(S);env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
    def query(tail):
        tick();r=subprocess.run(['/usr/bin/git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(S),*tail],env=env,capture_output=True,timeout=min(15,END-time.monotonic()))
        need(r.returncode==0 and r.stderr==b'' and len(r.stdout)<=32768,'read_only_git_result');return r.stdout
    head=query(['rev-parse','HEAD']).strip().decode('ascii');need(re.fullmatch('[0-9a-f]{40}',head) is not None,'source_commit_shape')
    status=query(['status','--porcelain']);return {'head':head,'expected_R':R,'matches_R':head==R,'clean':status==b'','status_bytes':len(status),'status_sha256':sha(status)}

def lock_snapshot():
    b=kernel(Path('/proc/locks'),1024*1024,0);need(not b or b.endswith(b'\n'),'kernel_lock_truncated');rows=[]
    for line in b.splitlines():
        tick();v=line.decode('ascii').split();need(len(v) in (8,9),'kernel_lock_fields');waiter=len(v)==9
        if waiter:need(v[1]=='->','kernel_waiter_marker');v.pop(1)
        need(re.fullmatch('[0-9]+:',v[0]) is not None and re.fullmatch('-?[0-9]+',v[4]) is not None,'kernel_lock_PID')
        m=re.fullmatch('([0-9a-fA-F]+):([0-9a-fA-F]+):([0-9]+)',v[5]);need(m is not None and v[6].isdigit() and (v[7]=='EOF' or v[7].isdigit()),'kernel_lock_identity')
        rows.append({'major':int(m[1],16),'minor':int(m[2],16),'ino':int(m[3]),'pid':int(v[4]),'type':v[1],'waiter':waiter})
    return rows

def daemon_fd9(pid,lease,s):
    need(type(pid) is int and pid>0,'native_daemon_PID');p=Path('/proc')/str(pid)
    if not p.exists():return {'pid':pid,'exists':False,'FD9':'process_absent'}
    ps=p.stat();need(stat.S_ISDIR(ps.st_mode) and ps.st_uid==UID,'native_daemon_owner')
    a=kernel(p/'stat',8192,UID);tail=a.rsplit(b')',1)[1].split();need(len(tail)>=22,'daemon_stat_shape');start=int(tail[19]);need(start>0,'daemon_start_ticks')
    fd=p/'fd/9';out={'pid':pid,'exists':True,'start_ticks':start}
    try:target=os.readlink(fd)
    except FileNotFoundError:out['FD9']='absent'
    else:
        out['FD9']='present';out['FD9_route_sha256']=sha(os.fsencode(target))
        need(target==str(lease),'unexpected_daemon_FD9_route');fs=fd.stat()
        need(stat.S_ISREG(fs.st_mode) and fs.st_uid==UID and (fs.st_dev,fs.st_ino)==(s.st_dev,s.st_ino),'native_FD9_inode')
        out['FD9_matches_lease']=True
    b=kernel(p/'stat',8192,UID);need(int(b.rsplit(b')',1)[1].split()[19])==start and p.stat().st_ino==ps.st_ino,'native_daemon_PID_race')
    return out

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

def leases():
    rows=[];snapshots=[]
    for name in LEASES:
        try:
            meta=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');lease=meta.with_name(name+'.lease')
            b,pin=metadata(meta,32768);v=strict(b);native=native_projection(v,name)
            generation=native['generation']
            canonical(lease);s=lease.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000,'native_lease_identity')
            identity=(os.major(s.st_dev),os.minor(s.st_dev),s.st_ino)
            first=[r for r in lock_snapshot() if (r['major'],r['minor'],r['ino'])==identity];d=daemon_fd9(native['daemon_pid'],lease,s)
            second=[r for r in lock_snapshot() if (r['major'],r['minor'],r['ino'])==identity];d2=daemon_fd9(native['daemon_pid'],lease,s)
            b2,pin2=metadata(meta,32768);need(b==b2 and pin==pin2 and stamp(lease.lstat())==stamp(s) and first==second and d==d2,'native_metadata_lock_or_FD9_race')
            row={'lease_name':name,'state':native['state'],'generation':generation,'native_projection':native,'metadata_pin':pin,'lease_stat':stamp(s),'matching_kernel_lock_rows':first,'daemon':d,'released_no_kernel_holder_or_FD9':native['state']=='released' and not first and d['FD9'] in ('absent','process_absent')}
            rows.append(row);snapshots.append((meta,b,pin,lease,stamp(s)))
        except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError) as exc:rows.append({'lease_name':name,**unknown(exc),'released_no_kernel_holder_or_FD9':False})
    for meta,b,pin,lease,s in snapshots:
        b2,pin2=metadata(meta,32768);need(b2==b and pin2==pin and stamp(lease.lstat())==s,'all_three_native_metadata_race')
    return rows

def process_rows():
    proc={};anchors=set();public=set();seen=0
    for p in Path('/proc').iterdir():
        tick();seen+=1;need(seen<=MAX_PROC,'proc_inventory_bound')
        if not p.name.isdecimal():continue
        try:
            ps=p.stat()
            if ps.st_uid!=UID:continue
            need(len(proc)<MAX_OWNED,'owned_proc_bound');b=kernel(p/'stat',8192,UID);tail=b.rsplit(b')',1)[1].split();need(len(tail)>=22,'process_stat_shape')
            pid=int(p.name);start=int(tail[19]);row={'pid':pid,'parent_pid':int(tail[1]),'start_ticks':start,'state':tail[0].decode('ascii'),'user_cpu_ticks':int(tail[11]),'kernel_cpu_ticks':int(tail[12]),'rss_bytes':int(tail[21])*os.sysconf('SC_PAGE_SIZE'),'proc_inode':ps.st_ino,'uid':UID,'role':None}
            comm=kernel(p/'comm',256,UID).strip()
            if comm in (b'python3',b'python3.12',b'python'):
                argv=kernel(p/'cmdline',32768,UID);tokens=argv.rstrip(b'\0').split(b'\0')
                args=tokens[1:]
                while args and args[0] in (b'-I',b'-B'):args=args[1:]
                if args and str(M2).encode() in args and b'finalize' in args:
                    for source,role in ((H,'helper28_finalize'),(SUP,'supervisorfa_finalize'),(G,'guard9c_finalize')):
                        if args[0]==str(source).encode():row['role']=role;anchors.add(pid);break
                if len(args)>=5 and args[:2]==[b'-m',b'swdb']:
                    command=args[2]
                    if command==b'validate' and args[3]==b'--records' and args[4].decode('utf-8') in {str(RAW/'base/records'),*(str(RAW/'campaign-runs/extensa'/cid/'records') for cid in CIDS)}:row['role']='public_validate';public.add(pid)
                    elif command in (b'campaign-export',b'agreement-report') and any(str(RAW).encode() in x for x in args[3:]):row['role']='public_'+command.decode();public.add(pid)
                if row['role']:
                    row['argv_bytes']=len(argv);row['argv_sha256']=sha(argv);row['exe_is_native_python']=Path('/proc/'+str(pid)+'/exe').resolve(strict=True)==Path('/usr/bin/python3.12')
                    need(row['exe_is_native_python'],'matching_process_native_executable')
            b2=kernel(p/'stat',8192,UID);need(int(b2.rsplit(b')',1)[1].split()[19])==start and p.stat().st_ino==ps.st_ino,'process_PID_reused')
            proc[pid]=row
        except FileNotFoundError:continue  # Process vanished; never call it idle or terminal.
        except (OSError,ValueError,IndexError,UnicodeError) as exc:
            need(False,'owned_process_inventory_unknown_'+type(exc).__name__)
    selected=set(anchors)
    for _ in range(MAX_ROWS):
        new={pid for pid,row in proc.items() if row['parent_pid'] in selected}-selected
        if not new:break
        selected|=new;need(len(selected)<=MAX_ROWS,'owned_descendant_bound')
    else:need(False,'owned_descendant_depth_bound')
    rows=[]
    for pid in sorted(selected):
        row=dict(proc[pid]);row['role']=row['role'] or 'owned_finalize_descendant';rows.append(row)
    return {'anchor_count':len(anchors),'owned_exact_process_tree':rows,'matching_public_processes_outside_anchored_tree_count':len(public-selected),'absent_anchor_is_not_completion':True,'CPU_tick_frequency':os.sysconf('SC_CLK_TCK'),'CPU_deltas_require_same_PID_and_start_ticks':True,'cmdline_or_comm_body_returned':False}

def observe():
    need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','actual_native_account')
    need(Path('/proc/self/exe').resolve()==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_python_flags')
    pins=[]
    for p,n,d in SOURCE_PINS:
        b,pin=metadata(p,n);need(len(b)==n and sha(b)==d,'original_source_or_M2_changed');pins.append(pin)
    files={}
    for name,kind in (('preregistration.json','control'),('supervisor-receipt.json','control'),('helper.stdout','stat_only'),('helper.stderr','stat_only')):files['finalize_'+name]=fact(FINALIZE/name,kind)
    names=[('validate-'+cid) for cid in CIDS]+[('export-'+cid) for cid in CIDS]+['final-agreement-report','validate-final-export']
    for name in names:
        for suffix,kind in (('.argv.json','argv'),('.exit-code.txt','exit'),('.stdout','stat_only'),('.stderr','stat_only')):files[name+suffix]=fact(RAW/(name+suffix),kind)
    files['final-export.json']=fact(RAW/'final-export.json','control')
    source=git_facts();native=leases();processes=process_rows()
    for p,n,d in SOURCE_PINS:
        b,pin=metadata(p,n);need(pin==next(x for x in pins if x['path']==str(p)) and sha(b)==d,'original_source_or_M2_race')
    return {'format':'swdb.lanl17-finalize-progress-metadata-readonly.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only':True,'sealed':False,'scientific_admission':False,'completion_inferred':False,'source':source,'source_and_M2_pins':pins,'native_leases':native,'all_three_currently_released_without_kernel_holder_or_FD9':all(x.get('released_no_kernel_holder_or_FD9') is True for x in native),'processes':processes,'phase_files':files,'raw_diagnostic_output_record_provider_auth_bodies_read':False,'compact_control_and_public_argv_exit_metadata_read':True,'stage_file_presence_is_not_success':True,'requires_original_completion_reader_after_parent_terminal_review':True,'fresh_live_admission_not_replaced':True}

def interrupted(n,f):raise Refused('progress_query_deadline_or_signal')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(45)
try:
    result=observe();raw=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode();need(len(raw)<=262144,'progress_return_bound');sys.stdout.buffer.write(raw)
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,subprocess.SubprocessError) as exc:
    sys.stdout.write(json.dumps({'format':'swdb.lanl17-finalize-progress-metadata-readonly.v1','state':'unknown','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completion_inferred':False,'scientific_admission':False,**unknown(exc)},sort_keys=True)+'\n')
