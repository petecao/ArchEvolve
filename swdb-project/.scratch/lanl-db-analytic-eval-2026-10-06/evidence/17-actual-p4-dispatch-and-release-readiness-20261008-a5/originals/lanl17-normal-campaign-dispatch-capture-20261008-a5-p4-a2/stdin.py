CONFIG={'expected_primary': '5e12a9796432654d88def24ecea617d16ca605b2', 'campaign': 'extensa-gem5-bfs-20261006-p4', 'node': 0, 'attempt': 1, 'resume': False, 'baselines_only': False, 'direct_dispatch_argv': ['/usr/bin/python3.12', '-B', '/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py', 'dispatch', '--manifest', '/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json', '--campaign', 'extensa-gem5-bfs-20261006-p4', '--node', '0', '--attempt', '1'], 'published_environment_overrides': {'PATH': '/usr/bin:/bin:/usr/local/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONSAFEPATH': '1', 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath', 'GIT_CONFIG_VALUE_0': '/data1/yanruj/lanl17-dx100-hooks-20261008-a2', 'SWDB_DX100_BINDING_REQUEST': '/data1/yanruj/lanl17-dx100-deployment-20261008-a2/request.json', 'SWDB_DX100_BINDING_REQUEST_SHA256': 'a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c'}, 'originals': {'manifest': {'local_original': {'path': '/private/tmp/lanl17-prepare-completion-decoded-originals-20261008-a1/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json', 'bytes': 292401, 'sha256': 'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1', 'stat': (16777229, 350289582, 33152, 501, 0, 1, 292401, 1791476721510610313, 1791476721510610313)}, 'remote_path': '/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json', 'bytes': 292401, 'sha256': 'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1', 'identity_sha256': '66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7', 'original_canonical_ensure_ascii': True, 'original_flag_present': False}, 'publication': {'local_original': {'path': '/private/tmp/lanl17-first-producer-capture-20261008-a5/publication-custody.json', 'bytes': 7701, 'sha256': 'e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1', 'stat': (16777229, 350297903, 33152, 501, 0, 1, 7701, 1791477336983942697, 1791477336983942697)}, 'remote_path': '/data/yanruj/EvolveSWDB_runs/lanl17-first-publication-custody-20261008-a5.json', 'bytes': 7701, 'sha256': 'e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1', 'identity_sha256': '8ec6987cc6d8c8e9d74df60cfa3e40e5bafbbdfdb0dd87747af645bf82436220', 'original_canonical_ensure_ascii': True, 'original_flag_present': False}, 'before': {'local_original': {'path': '/private/tmp/lanl17-p4-before-capture-20261008-a5/custody.json', 'bytes': 3148, 'sha256': '800e081afd48d92affac16859166b3923e0f519c89bb369f7068a62bfe5c82f4', 'stat': (16777229, 350484420, 33152, 501, 0, 1, 3148, 1791502907671905099, 1791502907671905099)}, 'remote_path': '/data/yanruj/EvolveSWDB_runs/lanl17-p4-before-custody-20261008-a5/custody.json', 'bytes': 3148, 'sha256': '800e081afd48d92affac16859166b3923e0f519c89bb369f7068a62bfe5c82f4', 'identity_sha256': '36948e2eb271e29ac11d8f33fc8f3dc55946f8a51504b875932b94e8888e6a42', 'original_canonical_ensure_ascii': True, 'original_flag_present': False}}, 'parent_exclusive_checked_utc': '2026-10-08T23:41:50.981249+00:00', 'valid_until_utc': '2026-10-08T23:46:50.981249+00:00', 'parent_exclusive_state_unchanged_reviewed': True, 'serial_first_all_three_leases_required': True}
import datetime,hashlib,json,os,pwd,re,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
BASE=Path('/data1/yanruj');PRIMARY=BASE/'ArchEvolve'
R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
H=BASE/'lanl17-control-cleanup60-20261007-a4.py'
H_SHA='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
S=BASE/'ArchEvolve-lanl17-source-20261007-a5'
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
NATIVE=[('/usr/bin/python3.12',8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),('/usr/bin/timeout',39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),('/usr/bin/bash',1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),('/usr/bin/node',91392840,'3b442520134d4247f8d97ad4dc2d1443bdad6f0ebef670f06295743e864a37aa'),('/usr/bin/numactl',36080,'f3944bcd7848d64424f8daf27f350b03d7f3281b2fb9be5eaaba0ddd0e72efb8'),('/usr/bin/strace',2087432,'28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001'),('/usr/bin/tmux',1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd')]
MAX_METADATA=32*1024*1024
DEADLINE=time.monotonic()+180
class Refused(ValueError):pass
def require(ok,code):
 if not ok:raise Refused(code)
def left():
 n=DEADLINE-time.monotonic();require(n>0,'dispatch_bootstrap_deadline');return n
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))
def strict(b):
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,'duplicate_key');d[k]=v
  return d
 def bad(v):raise Refused('nonfinite_JSON')
 return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def canonical(p):require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_path')
def exact(p,size,digest,owner,mode=None):
 left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and s.st_size==size and (mode is None or stat.S_IMODE(s.st_mode)==mode),'exact_file_identity')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);h=hashlib.sha256();n=0
 with os.fdopen(fd,'rb') as f:
  require(stamp(os.fstat(f.fileno()))==stamp(s),'exact_open_stat')
  while True:
   left();b=f.read(min(1024*1024,size-n+1))
   if not b:break
   n+=len(b);require(n<=size,'exact_read_size');h.update(b)
  require(n==size and h.hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'exact_returned_bytes_stat')
 return stamp(s)
def read(p,maximum):
 left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and s.st_size<=maximum,'bounded_metadata_identity')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  require(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_stat');b=f.read(maximum+1)
  require(len(b)==s.st_size<=maximum and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'metadata_returned_bytes_stat')
 return b,stamp(s)
def sealed(v):
 identity=v['identity_sha256'];require(re.fullmatch('[a-f0-9]{64}',identity) and v.get('canonical_ensure_ascii',True) is True,'original_default_or_explicit_True_policy')
 require(sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==identity,'original_True_seal')
def git(root,*args):
 left();r=subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(120,left()))
 require(r.returncode==0 and not r.stderr and len(r.stdout)<=16*1024*1024,'read_only_Git');return r.stdout
def tree(root,ref):
 rows=git(root,'ls-tree','-rz',ref,'--','swdb-project/swdb')
 return {r.split(b'\t',1)[1]:r.split(b'\t',1)[0] for r in rows.split(b'\0') if r and r.split(b'\t',1)[1].endswith(b'.py')}
def released():
 out={}
 for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
  b,s=read(BASE/'lact-host-lease'/(name+'.meta.json'),32768);v=strict(b);require(v['state']=='released','serial_first_all_three_leases_released');out[name]=(sha(b),s)
 return out
def fresh_attempt():
 cid=CONFIG['campaign']
 for p in (RAW/'attempts'/cid/'attempt-1',RAW/'campaign-runs/extensa'/cid):require(not os.path.lexists(p),'fresh_normal_attempt_and_campaign_absent')
def run():
 require(sys.platform=='linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and not sys.flags.optimize,'native_host_account')
 require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'native_bootstrap_Python')
 require(os.environ.get('HOME')==pwd.getpwuid(UID).pw_dir and os.environ.get('CODEX_HOME')=='/data1/yanruj/.codex' and os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')=='/data1/yanruj/.codex','preserved_account_home_and_original_token')
 canonical(BASE);bs=BASE.lstat();require(stat.S_ISDIR(bs.st_mode) and bs.st_uid==UID and stat.S_IMODE(bs.st_mode)==0o700,'private_BASE')
 for p in (PRIMARY,S,S/'swdb-project',RAW):canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and p.lstat().st_uid==UID,'owned_required_directory')
 for route,size,digest in NATIVE:exact(Path(route),size,digest,0,0o755)
 for name,wanted in (('python3','/usr/bin/python3.12'),('timeout','/usr/bin/timeout'),('bash','/usr/bin/bash'),('git','/usr/bin/git'),('tmux','/usr/bin/tmux'),('numactl','/usr/bin/numactl'),('strace','/usr/bin/strace')):
  route=shutil.which(name);require(route and Path(route).resolve(strict=True)==Path(wanted),'original_helper_native_PATH_route')
 hs=exact(H,38195,H_SHA,UID)
 require(not H.lstat().st_mode&0o022,'reviewed_helper_physical_mode')
 hook=exact(BASE/'lanl17-dx100-hooks-20261008-a2/post-checkout',20078,'f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a',UID,0o700)
 request=exact(BASE/'lanl17-dx100-deployment-20261008-a2/request.json',19596,CONFIG['published_environment_overrides']['SWDB_DX100_BINDING_REQUEST_SHA256'],UID,0o600)
 require(re.fullmatch('[a-f0-9]{40}',CONFIG['expected_primary']),'explicit_actual_primary')
 require(git(PRIMARY,'rev-parse','HEAD').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'rev-parse','origin/yanrujhou_main').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'branch','--show-current').strip()==b'yanrujhou_main','actual_primary_revision')
 require(not git(PRIMARY,'diff','--name-only') and not git(PRIMARY,'diff','--cached','--name-only') and git(PRIMARY,'status','--porcelain','--untracked-files=all').strip()==b'?? swdb-project/records/.retention.lock','primary_tracked_clean_exact_retention')
 exact(PRIMARY/'swdb-project/records/.retention.lock',0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',UID)
 py=tree(S,R);require(len(py)==185 and tree(PRIMARY,CONFIG['expected_primary'])==py,'source_primary185_Git_equality')
 require(git(S,'rev-parse','HEAD').strip().decode()==R and not git(S,'status','--porcelain'),'actual_M2_source_clean_R')
 pins={};docs={}
 for key in ('manifest','publication','before'):
  pin=CONFIG['originals'][key];p=Path(pin['remote_path']);b,s=read(p,MAX_METADATA);require(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'original_remote_input_bytes');v=strict(b);sealed(v);require(v['identity_sha256']==pin['identity_sha256'],'original_remote_input_identity');pins[key]=s;docs[key]=v
 m=docs['manifest'];pub=docs['publication'];before=docs['before']
 require(Path(CONFIG['originals']['manifest']['remote_path'])==RAW/'manifest.json' and m['source']==str(S) and m['raw']==str(RAW) and m['source_commit']==R and m['estimator_sha256']==F6 and m['helper_sha256']==H_SHA,'exact_actual_M2_scope')
 require(pub['format']=='swdb.lanl17-freeze-publication-custody.v1' and pub['source_commit']==R and pub['manifest_sha256']==m['identity_sha256'] and pub['policy_sha256']==m['policy']['identity_sha256'] and pub['completed_export_exit_code']==0 and pub['application_outcomes_opened']==0 and pub['freeze_export_commit']==m['freeze_export']['commit'],'genuine_FIRST_publication')
 require(before['format']=='swdb.lanl17-attempt-control-custody.v2' and before['phase']=='before' and before['campaign']==CONFIG['campaign'] and before['attempt']==1 and before['resume'] is False and before['baselines_only'] is False and before['state']['present'] is False and before['manifest_identity_sha256']==m['identity_sha256'] and before['source_commit']==R and before['estimator_sha256']==F6,'genuine_fresh_normal_before_custody')
 require(before['freeze_publication_pin']['sha256']==CONFIG['originals']['publication']['sha256'] and before['manifest_file_pin']['sha256']==CONFIG['originals']['manifest']['sha256'],'before_original_input_links')
 valid=datetime.datetime.fromisoformat(CONFIG['valid_until_utc']);require(valid.tzinfo is not None and datetime.datetime.now(datetime.timezone.utc)<=valid,'explicit_parent_dispatch_window')
 require(all(os.environ.get(k)==v for k,v in CONFIG['published_environment_overrides'].items()),'published_exact_environment')
 leases=released();fresh_attempt()
 # No new campaign/provider/source deadline. Existing 28d owns live capacity,
 # fresh fetched wrapper, official provider, source/input/config checks and launch.
 require(released()==leases,'lease_generation_drift_before_dispatch');fresh_attempt()
 for key,pin in CONFIG['originals'].items():
  b,s=read(Path(pin['remote_path']),MAX_METADATA);require(s==pins[key] and len(b)==pin['bytes'] and sha(b)==pin['sha256'],'original_metadata_bytes_stat_changed_before_dispatch')
 require(exact(H,38195,H_SHA,UID)==hs and exact(BASE/'lanl17-dx100-hooks-20261008-a2/post-checkout',20078,'f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a',UID,0o700)==hook and exact(BASE/'lanl17-dx100-deployment-20261008-a2/request.json',19596,CONFIG['published_environment_overrides']['SWDB_DX100_BINDING_REQUEST_SHA256'],UID,0o600)==request,'sources_and_published_inputs_before_exec')
 require(datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_window_before_dispatch');left()
 os.chdir(S/'swdb-project');os.umask(0o077)
 argv=['/usr/bin/python3.12','-B',str(H),'dispatch','--manifest',str(RAW/'manifest.json'),'--campaign',CONFIG['campaign'],'--node',str(CONFIG['node']),'--attempt','1']
 require(argv==CONFIG['direct_dispatch_argv'],'exact_original_dispatch_argv')
 # Silent bootstrap; stdout belongs to original 28d's dispatch result.
 signal.alarm(0);os.execv(argv[0],argv)
def interrupted(number,frame):raise Refused('dispatch_bootstrap_signal_'+str(number))
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(180)
try:run()
except BaseException as exc:
 body=json.dumps({'format':'swdb.lanl17-campaign-dispatch-bootstrap-failure-original.v1','sealed':False,'error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'campaign_dispatch_result_not_assessed':True},separators=(',',':')).encode()
 sys.stderr.buffer.write(body+b'\n');raise SystemExit(2)
