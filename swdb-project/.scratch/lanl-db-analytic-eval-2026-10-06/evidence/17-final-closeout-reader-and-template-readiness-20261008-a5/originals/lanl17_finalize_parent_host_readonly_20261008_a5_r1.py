"""2026-10-08 ET: bounded future FINALIZE host preflight; read-only metadata, not admission."""
import datetime, hashlib, json, os, pwd, shutil, signal, socket, stat, subprocess, sys, time
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
def read():
    need(os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10','native_account_host')
    sources={}
    for p in (PRIMARY,SOURCE):
        need(p.resolve(strict=True)==p,'source_canonical')
        x={'branch':run(['/usr/bin/git','-C',str(p),'rev-parse','--abbrev-ref','HEAD']).strip(),'head':run(['/usr/bin/git','-C',str(p),'rev-parse','HEAD']).strip(),'tracked_status':run(['/usr/bin/git','-C',str(p),'status','--porcelain','--untracked-files=no'])}
        need(x['head']==R and x['tracked_status']=='','frozen_source_R_clean');sources[str(p)]=x
    need(sources[str(PRIMARY)]['branch']=='yanrujhou_main','primary_branch')
    origin=run(['/usr/bin/git','-C',str(PRIMARY),'rev-parse','origin/yanrujhou_main']).strip();need(origin==R,'primary_origin_R')
    b,m2pin=original(RAW/'manifest.json',400000);need(len(b)==292401 and digest(b)==M2_SHA,'exact_original_M2')
    leases={};lease_pins={};locks={};daemons={}
    proc_locks=Path('/proc/locks').read_bytes();need(len(proc_locks)<=1024*1024,'kernel_lock_cap')
    for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
        p=BASE/'lact-host-lease'/(name+'.meta.json');raw,pin=original(p);d=strict(raw);need(type(d) is dict and d['state']=='released','all_three_native_released');leases[name]=d;lease_pins[name]=pin
        lp=BASE/'lact-host-lease'/(name+'.lease');_,lpin=original(lp,4096);s=lp.lstat();key=f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}'
        matches=[line for line in proc_locks.decode().splitlines() if key in line.split()];need(not matches,'all_three_no_matching_kernel_holder_or_waiter')
        locks[name]={'lease_original':lpin,'matching_rows':matches}
        pid=d.get('lease',{}).get('daemon_pid');need(type(pid) is int and pid>0,'original_native_daemon_pid')
        process=Path('/proc')/str(pid);fd=process/'fd'/'9';exists=process.exists();matched=False
        if exists:
            need(process.stat().st_uid==UID,'native_daemon_owned')
            try: f=fd.stat();matched=f.st_dev==s.st_dev and f.st_ino==s.st_ino
            except FileNotFoundError: pass
        need(not matched,'all_three_no_matching_daemon_FD9');daemons[name]={'pid':pid,'exists':exists,'FD9_matches_selected_lease':matched}
    stops={}
    for n in range(1,5):
        cid=f'extensa-gem5-bfs-20261006-p{n}';p=RAW/'attempts'/cid/'attempt-1'/'stopped-receipt.json';b,pin=original(p,65536);d=strict(b)
        seal=d.get('identity_sha256');v=json.dumps({k:v for k,v in d.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode();need(digest(v)==seal,'original_stop_true_seal')
        need(d['campaign']==cid and d['source_commit']==R and d['source_clean_after'] is True and d['public_exit_code']==d['runner_exit_code']==0 and not d.get('infrastructure_error') and not d['process_cleanup']['survivors'],'all_four_normal_stops')
        stops[cid]={'original':pin,'identity_sha256':seal,'ended_utc':d['ended_utc']}
    process_matches=[];own_count=0
    for p in Path('/proc').iterdir():
        tick()
        if not p.name.isdecimal() or int(p.name)==os.getpid(): continue
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
    after_locks=Path('/proc/locks').read_bytes();need(len(after_locks)<=1024*1024,'after_kernel_lock_cap')
    for name,d in leases.items():
        raw,pin=original(BASE/'lact-host-lease'/(name+'.meta.json'));need(strict(raw)==d and pin==lease_pins[name],'native_lease_continuity')
        p=Path(locks[name]['lease_original']['path']);_,pin=original(p,4096);need(pin==locks[name]['lease_original'],'native_lockfile_continuity')
        s=p.lstat();key=f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}';need(not any(key in line.split() for line in after_locks.decode().splitlines()),'after_no_kernel_holder_or_waiter')
        fd=Path('/proc')/str(daemons[name]['pid'])/'fd'/'9'
        try:f=fd.stat();need(not (f.st_dev==s.st_dev and f.st_ino==s.st_ino),'after_no_matching_daemon_FD9')
        except FileNotFoundError:pass
    return {'format':'swdb.lanl17-finalize-parent-host-readonly.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host_metadata_ready':True,'scientific_admission':False,'source':sources,'primary_origin':origin,'manifest_original':m2pin,'leases':leases,'lease_originals':lease_pins,'kernel_locks':locks,'kernel_snapshot_before':{'bytes':len(proc_locks),'sha256':digest(proc_locks)},'kernel_snapshot_after':{'bytes':len(after_locks),'sha256':digest(after_locks)},'daemon_FD9':daemons,'four_stop_originals':stops,'owned_processes_checked':own_count,'live_source_campaign_consumers':process_matches,'finalize_routes_absent':absent,'mem':mem,'free_bytes':free,'load':os.getloadavg(),'processes_top35_comm_only':procs,'cpu_activity':cpu,'gpu':gpu,'point_in_time_only':True,'requires_parent_exclusive_no_reuse_and_fresh_original_admission':True,'source_F6_native_controls_hooks_proofs_rechecked_by_original_FINALIZE_bootstrap':True,'raw_body_auth_log_or_other_user_cmdline_returned':False}
def interrupted(n,f):raise ValueError('host_metadata_signal_or_deadline')
for n in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(n,interrupted)
signal.alarm(45)
try:
    d=read();b=(json.dumps(d,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=65536,'host_output_cap');sys.stdout.buffer.write(b)
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,subprocess.SubprocessError) as e:
    print(json.dumps({'format':'swdb.lanl17-finalize-parent-host-readonly.v1','host_metadata_ready':False,'scientific_admission':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason_sha256':digest(str(e).encode()),'error_class':type(e).__name__},sort_keys=True))
