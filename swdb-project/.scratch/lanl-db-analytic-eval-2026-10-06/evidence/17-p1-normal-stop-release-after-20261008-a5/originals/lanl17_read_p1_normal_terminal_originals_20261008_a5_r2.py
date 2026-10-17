"""2026-10-08 ET: bounded normal terminal original metadata reader; no file/native mutation."""
import base64,datetime,hashlib,json,os,pwd,re,signal,socket,stat,sys,time
from pathlib import Path
UID=114316761
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
A=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/attempts/extensa-gem5-bfs-20261006-p1/attempt-1')
R='5e12a9796432654d88def24ecea617d16ca605b2'
M2='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7'
DISPATCH='ee2d7bebe5a8003403a136b3fd8f62b1d72b743b6b47c1f8f97c4abb31ac53dd'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
POLICY={'frozen_at':'2026-10-08T16:05:25.347884+00:00','id':'extensa-gem5-bfs-20261006-p1.agreement.5bae2f42d9078864','identity_sha256':'5bae2f42d9078864caad73e81a16007edb6458f0b101628ded04a7ef3aedbf7d'}
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

def digest(b):return hashlib.sha256(b).hexdigest()
def utc(v):
    need(type(v) is str and 0<len(v)<=64,'UTC_type')
    t=datetime.datetime.fromisoformat(v.replace('Z','+00:00'));need(t.tzinfo is not None and t.utcoffset()==datetime.timedelta(0),'UTC_offset');return t

def stop_within_native_end(stop_end,lane_end):
    # Native socket_lane.sh now_utc emits whole seconds; retain that half-open bin.
    t=utc(lane_end);v=utc(stop_end)
    need(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',lane_end) is not None,'native_whole_second_end')
    return v<t+datetime.timedelta(seconds=1)

def read():
    need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','actual_account')
    need(Path('/proc/self/exe').resolve()==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_Python_flags')
    caps={'stopped-receipt.json':65536,'runner.exit-code.txt':64,'wrapper.exit-code.txt':64,'lane.json':32768};rows={};raws={}
    for name,cap in caps.items():raws[name],rows[name]=metadata(A/name,cap)
    stop=strict(raws['stopped-receipt.json']);lane=strict(raws['lane.json']);s=lane.get('socket_lane');need(type(s) is dict,'lane_mapping')
    expected={'format':'swdb.lanl17-stopped-attempt.v1','campaign':'extensa-gem5-bfs-20261006-p1','source_commit':R,'manifest_sha256':M2,'dispatch_sha256':DISPATCH,'policy':POLICY,'estimator_sha256_after':F6,'infrastructure_error':None,'source_clean_after':True,'original_codex_home_restored':True,'account_home_unchanged':True,'raw_transferred':False,'scope':'Actual stopped attempt; no inferred completion, unique pairs or D30 success.'}
    need(all(stop.get(k)==v for k,v in expected.items()),'normal_stopped_bindings')
    stop_keys={'format','started_utc','ended_utc','campaign','source_commit','policy','manifest_sha256','dispatch_sha256','argv_sha256','runner_exit_code','public_exit_code','infrastructure_error','process_cleanup','original_codex_home_restored','account_home_unchanged','source_clean_after','estimator_sha256_after','raw_transferred','scope','identity_sha256'}
    need(set(stop)==stop_keys,'closed_stopped_fields')
    need(type(stop['argv_sha256']) is str and re.fullmatch('[0-9a-f]{64}',stop['argv_sha256']) is not None,'argv_digest_type')
    need(all(type(stop[k]) is bool for k in ('source_clean_after','original_codex_home_restored','account_home_unchanged','raw_transferred')),'stopped_boolean_types')
    identity=stop['identity_sha256'];need(type(identity) is str and re.fullmatch('[0-9a-f]{64}',identity) is not None,'stop_identity_type')
    body={k:v for k,v in stop.items() if k!='identity_sha256'}
    need(digest(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==identity,'original_stop_seal')
    clean=stop.get('process_cleanup');need(type(clean) is dict and set(clean)=={'subreaper','terminated_owned_processes','survivors'} and clean['subreaper'] is True and clean['survivors']=={},'owned_cleanup')
    need(type(clean['terminated_owned_processes']) is list and len(clean['terminated_owned_processes'])<=1024,'cleanup_count')
    for row in clean['terminated_owned_processes']:
        need(type(row) is dict and set(row)=={'pid','start_time','signal'} and type(row['pid']) is int and row['pid']>0 and type(row['start_time']) is str and re.fullmatch('[0-9]{1,32}',row['start_time']) is not None and row['signal'] in ('SIGTERM','SIGKILL'),'closed_cleanup_rows')
    for name in ('runner.exit-code.txt','wrapper.exit-code.txt'):
        need(re.fullmatch(rb'-?[0-9]+\s*',raws[name]) is not None and int(raws[name])==0,'normal_original_integer_exit')
    need(type(stop['runner_exit_code']) is int and type(stop['public_exit_code']) is int and stop['runner_exit_code']==stop['public_exit_code']==0,'normal_public_runner_exit')
    need(s.get('node')==0 and s.get('lease_name')=='mbit10-evaluation-node0' and type(s.get('lease_generation')) is int and s['lease_generation']==511 and s.get('job')=='swdb-lanl17-20261007-a5-p1-a1','final_lane_binding')
    need(type(s.get('exit_code')) is int and s['exit_code']==0 and 'record_errors' not in s,'normal_lane_exit')
    need(utc(s['started_utc'])<=utc(stop['started_utc'])<utc(stop['ended_utc']) and stop_within_native_end(stop['ended_utc'],s['ended_utc']),'original_terminal_time_order')
    for name,cap in caps.items():
        b,pin=metadata(A/name,cap);need(b==raws[name] and pin==rows[name],'terminal_snapshot_race')
    return {'format':'swdb.lanl17-normal-terminal-originals-readonly.v1','sealed':False,'scientific_admission':False,'normal_metadata_ready':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_freshness_and_generation_not_policed_by_this_reader':True,'files':{n:{**rows[n],'base64':base64.b64encode(raws[n]).decode('ascii')} for n in caps}}

def interrupted(n,f):raise Refused('terminal_query_deadline_or_signal')
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(45)
try:
    value=read();b=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=256*1024,'terminal_output_cap');sys.stdout.buffer.write(b)
except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError) as exc:
    sys.stdout.write(json.dumps({'format':'swdb.lanl17-normal-terminal-originals-readonly.v1','sealed':False,'scientific_admission':False,'normal_metadata_ready':False,'error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode()),'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},sort_keys=True)+'\n')
