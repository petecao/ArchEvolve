import base64,datetime,hashlib,json,os,pwd,re,signal,socket,stat,sys,time
from pathlib import Path
UID=114316761
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
END=time.monotonic()+45
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
need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','native_host_account')
need(Path('/proc/self/exe').resolve()==Path('/usr/bin/python3.12') and sys.flags.dont_write_bytecode,'native_python')
signal.alarm(45)
p=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/attempts/extensa-gem5-bfs-20261006-p3/attempt-1/lane.json')
q=Path('/data1/yanruj/lact-host-lease/mbit10-evaluation-node0.meta.json')
b,pin=metadata(p,32768);nb,npin=metadata(q,32768);lane=strict(b)['socket_lane'];native=strict(nb)
need(type(lane) is dict and type(lane.get('node')) is int and lane.get('node')==0 and lane.get('job')=='swdb-lanl17-20261007-a5-p3-a1' and lane.get('lease_name')=='mbit10-evaluation-node0' and type(lane.get('lease_generation')) is int and lane['lease_generation']>0 and type(lane.get('exit_code')) is int and lane['exit_code'] in(-1,0) and 'record_errors' not in lane,'actual_p2_lane_binding')
need(type(native.get('state')) is str and native['state'] in ('held','released') and type(native.get('lease')) is dict and native['lease'].get('lease_name')=='mbit10-evaluation-node0' and type(native['lease'].get('generation')) is int and native['lease']['generation']==lane['lease_generation'],'actual_acquired_generation_matches_native')
for path,cap,raw,pinned in ((p,32768,b,pin),(q,32768,nb,npin)):
 newer,newpin=metadata(path,cap);need(newer==raw and newpin==pinned,'actual_lane_native_snapshot_changed')
print(json.dumps({'format':'swdb.lanl17-p2-native-acquired-generation-originals-readonly.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scientific_admission':False,'generation':lane['lease_generation'],'native_state':native['state'],'holder_and_native_release_not_inferred':True,'files':{str(p):{**pin,'base64':base64.b64encode(b).decode()},str(q):{**npin,'base64':base64.b64encode(nb).decode()}}},sort_keys=True))
