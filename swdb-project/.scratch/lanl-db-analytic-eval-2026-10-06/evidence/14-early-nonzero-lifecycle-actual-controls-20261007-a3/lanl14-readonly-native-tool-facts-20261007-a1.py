"""Read-only native tool/account/source facts; no selected main or fixture."""
import datetime,hashlib,json,os,pathlib,shutil,socket,stat,sys
P=pathlib.Path
assert sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10'
assert os.getuid()==os.geteuid()==114316761
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def file_fact(path):
 p=P(path).resolve(strict=True);s=p.stat()
 assert stat.S_ISREG(s.st_mode) and not s.st_mode&0o022
 assert s.st_uid in (0,os.getuid()) and 0<s.st_size<=128*1024*1024
 with p.open('rb') as f:header=f.read(20)
 return {'path':str(p),'bytes':s.st_size,'sha256':sha(p),'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode),'executable':os.access(p,os.X_OK),'ELF_x86_64':header[:6]==b'\x7fELF\x02\x01' and int.from_bytes(header[18:20],'little')==62}
tools={'python':file_fact(sys.executable)}
for name in ('timeout','bash','git'):
 path=shutil.which(name);assert path
 tools[name]=file_fact(path)
assert all(row['executable'] and row['ELF_x86_64'] for row in tools.values())
wrapper=P('/data1/yanruj/Memacc-repro-20260925/AgenticRefiner/scripts/host/socket_lane.sh')
assert sha(wrapper)=='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
helper=P('/data1/yanruj/lanl17-control-20261006.py')
assert sha(helper)=='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
base=P('/data/yanruj/EvolveSWDB_runs');s=base.stat()
assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and not base.is_symlink()
leases={name:json.loads((P('/data1/yanruj/lact-host-lease')/(name+'.meta.json')).read_bytes())['state'] for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
reserved=('BASH_ENV','ENV','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH','SOCKET_LANE_REEXEC','SOCKET_LANE_NODE_DIR','LACT_LEASE_ROOT','LACT_LEASE_NAME','LACT_NUMACTL','LOCKDIR')
data={'format':'swdb.lanl14-parent-readonly-native-facts.v1','canonical_ensure_ascii':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uid':os.getuid(),'native_tools':tools,'python_version':list(sys.version_info[:3]),'wrapper_sha256':sha(wrapper),'original_cleanup_helper_sha256':sha(helper),'raw_base':{'path':str(base),'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode)},'leases':leases,'reserved_startup_overrides_present':{name:name in os.environ for name in reserved},'capacity_bytes':{mount:os.statvfs(mount).f_bavail*os.statvfs(mount).f_frsize for mount in ('/data1','/data')},'memory_available_bytes':int(next(line.split()[1] for line in P('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024,'load':list(os.getloadavg()),'selected_control_or_fixture_main':False,'source_copy':False,'scientific_admission':False,'scope':'Read-only physical native/source byte pins and account/lane/capacity facts. No version command, Git operation, fixture, evaluator, provider, auth/environment values or original argv read.'}
data['identity_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
print(json.dumps(data,indent=2,ensure_ascii=True,allow_nan=False))
