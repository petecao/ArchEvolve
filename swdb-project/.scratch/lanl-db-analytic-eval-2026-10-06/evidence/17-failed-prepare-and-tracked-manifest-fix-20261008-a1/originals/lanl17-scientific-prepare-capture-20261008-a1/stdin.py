CONFIG={'expected_primary': '5e12a9796432654d88def24ecea617d16ca605b2', 'final_source_commit': '5e12a9796432654d88def24ecea617d16ca605b2', 'direct_prepare_argv': ['/usr/bin/timeout', '--signal=TERM', '--kill-after=60s', '18300s', '/usr/bin/python3.12', '/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py', '--action', 'prepare', '--final-source-sha', '5e12a9796432654d88def24ecea617d16ca605b2', '--project', '/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project', '--control', '/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4', '--guard-sha256', '9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6', '--cleanup-proof', '/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json', '--cleanup-proof-identity', '18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1', '--supervisor-proof', '/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json', '--supervisor-proof-identity', 'ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b', '--', '--source-sha', '5e12a9796432654d88def24ecea617d16ca605b2', '--cleanup-proof', '/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json', '--source-ref', 'codex/lanl-analytic-eval', '--source', '/data1/yanruj/ArchEvolve-lanl17-source-20261007-a4', '--raw', '/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4', '--tag', '20261007-a4'], 'admission_valid_until_utc': '2026-10-08T15:35:55.375150+00:00', 'parent_required_data1_available_bytes': 25547235328, 'parent_admission_original': {'path': '/private/tmp/lanl17-parent-prepare-storage-admission-original-20261008-a1.json', 'bytes': 3893, 'sha256': '10677fea33a13d511c365b8595d79464683029e12df301667175d2d61c193505', 'stat': (16777229, 350149625, 33152, 501, 0, 1, 3893, 1791472855375498188, 1791472855375498188)}, 'original_retirement_pin': {'path': '/private/tmp/lanl17-detached-sparse-retire-a4-originals-20261008/guard-receipt/receipt.json', 'bytes': 64569, 'sha256': '93e99138ae34869de92f46d81f0b2ccd5f3da8097555dc92f7f772f17dc22b29', 'stat': (16777229, 350148932, 33152, 501, 0, 1, 64569, 1791472649817655995, 1791472649817655995)}, 'original_fresh_host_pin': {'path': '/private/tmp/lanl17-post-retirement-host-capture-20261008-a1/stdout', 'bytes': 12462, 'sha256': 'bac2fd9f4cbaf1f0eca7f17e9ac28f1d8bdf71759b3f044742469f2f36046f2b', 'stat': (16777229, 350149100, 33152, 501, 0, 1, 12462, 1791472700139127471, 1791472700139127471)}}
import datetime,hashlib,json,os,pwd,re,signal,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
BASE=Path('/data1/yanruj');RUNS=Path('/data/yanruj/EvolveSWDB_runs');PRIMARY=BASE/'ArchEvolve'
C='f893fed400347ed23d92e917d8bde21b75e5375d';R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
CLEAN=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project'
G=BASE/'lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'
H=BASE/'lanl17-control-cleanup60-20261007-a4.py';SUP=BASE/'lanl17-metadata-supervisor-cleanup60-20261007-a4.py'
SOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a4';RAW=RUNS/'lanl17-actual-campaigns-20261007-a4'
PREP=RUNS/'lanl17-metadata-prepare-20261007-a4';EF=BASE/'ArchEvolve-lanl17-freeze-evidence-20261007-a4'
PUB=BASE/'lanl17-dx100-deployment-20261008-a1';HOOKS=BASE/'lanl17-dx100-hooks-20261008-a1'
FROZEN=[(G,14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),(H,38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),(SUP,8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0')]
NATIVE=[('/usr/bin/python3.12',8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),('/usr/bin/timeout',39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),('/usr/bin/bash',1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),('/usr/bin/node',91392840,'3b442520134d4247f8d97ad4dc2d1443bdad6f0ebef670f06295743e864a37aa'),('/usr/bin/numactl',36080,'f3944bcd7848d64424f8daf27f350b03d7f3281b2fb9be5eaaba0ddd0e72efb8'),('/usr/bin/strace',2087432,'28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001'),('/usr/bin/tmux',1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd')]
PROOFS=[(RUNS/'lanl17-cleanup-smoke-20261007-a4/receipt.json','873d36971b55e903731c9ab44a93ba5f1d8f3c563d0cf6dcefb2a48c8a6b063e','18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1',True),(RUNS/'lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json','12546c476589f3eceb6f779f53b710b8bd623c643b3417461fd4f21774c07436','ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b',False)]
DEADLINE=time.monotonic()+180
class Refused(ValueError):pass
def require(ok,code):
 if not ok:raise Refused(code)
def left():
 n=DEADLINE-time.monotonic();require(n>0,'prepare_bootstrap_deadline');return n
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
def git(root,*args,absent=False):
 left();r=subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(120,left()))
 if absent:require(r.returncode==1 and not r.stdout,'required_absent_Git_branch');return b''
 require(r.returncode==0 and not r.stderr and len(r.stdout)<=16*1024*1024,'read_only_Git');return r.stdout
def tree(root,ref):
 rows=git(root,'ls-tree','-rz',ref,'--','swdb-project/swdb')
 return {r.split(b'\t',1)[1]:r.split(b'\t',1)[0] for r in rows.split(b'\0') if r and r.split(b'\t',1)[1].endswith(b'.py')}
def released():
 out={}
 for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
  b,s=read(BASE/'lact-host-lease'/(name+'.meta.json'),32768);v=strict(b);require(v['state']=='released','all_three_leases_released');out[name]=(sha(b),s)
 return out
def absent_scopes():
 for p in (SOURCE,RAW,PREP,EF):require(not os.path.lexists(p),'reserved_prepare_route_not_fresh')
 git(PRIMARY,'show-ref','--verify','--quiet','refs/heads/codex/lanl17-freeze-evidence-20261007-a4',absent=True)
def run():
 require(sys.platform=='linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and not sys.flags.optimize,'native_host_account')
 require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'native_bootstrap_Python')
 require(os.environ.get('HOME')==pwd.getpwuid(UID).pw_dir and os.environ.get('CODEX_HOME')=='/data1/yanruj/.codex' and os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')=='/data1/yanruj/.codex','preserved_account_home_and_original_token')
 canonical(BASE);bs=BASE.lstat();require(stat.S_ISDIR(bs.st_mode) and bs.st_uid==UID and stat.S_IMODE(bs.st_mode)==0o700,'private_BASE')
 for p in (RUNS,CLEAN,PRIMARY,PUB,HOOKS):canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and p.lstat().st_uid==UID,'owned_required_directory')
 for route,size,digest in NATIVE:exact(Path(route),size,digest,0,0o755)
 frozen={str(p):exact(p,size,digest,UID) for p,size,digest in FROZEN}
 hook=exact(HOOKS/'post-checkout',17300,'d340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527',UID,0o700)
 request=exact(PUB/'request.json',13676,'afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822',UID,0o600)
 require(CONFIG['final_source_commit']==R and re.fullmatch('[a-f0-9]{40}',CONFIG['expected_primary']),'exact_frozen_R_and_primary')
 valid=datetime.datetime.fromisoformat(CONFIG['admission_valid_until_utc']);require(valid.tzinfo is not None and datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_admission_window')
 require(git(PRIMARY,'rev-parse','HEAD').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'rev-parse','origin/yanrujhou_main').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'branch','--show-current').strip()==b'yanrujhou_main','actual_primary_revision')
 require(not git(PRIMARY,'diff','--name-only') and not git(PRIMARY,'diff','--cached','--name-only') and git(PRIMARY,'status','--porcelain','--untracked-files=all').strip()==b'?? swdb-project/records/.retention.lock','primary_tracked_clean_exact_retention')
 exact(PRIMARY/'swdb-project/records/.retention.lock',0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',UID)
 require(git(CLEAN.parent,'rev-parse','HEAD').strip().decode()==C and not git(CLEAN.parent,'status','--porcelain'),'clean_C_source')
 require(git(CLEAN.parent,'rev-parse',R+'^{commit}').strip().decode()==R,'delivered_R_object_in_C')
 pyC,pyR=tree(CLEAN.parent,C),tree(CLEAN.parent,R);require(len(pyC)==185 and pyC==pyR,'185_C_R_Git_source_equality')
 require(tree(PRIMARY,CONFIG['expected_primary'])==pyC,'primary_scientific_python_equivalence')
 modules={}
 for p in sorted((CLEAN/'swdb').rglob('*.py')):
  b,s=read(p,2*1024*1024);modules[p.relative_to(CLEAN/'swdb').as_posix()]=sha(b)
 require(len(modules)==185 and sha(json.dumps(modules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==F6,'C185_physical_F6')
 exact(CLEAN/'swdb/processes.py',912,'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289',UID,0o644)
 for p,digest,identity,policy in PROOFS:
  b,s=read(p,4*1024*1024);v=strict(b);require(sha(b)==digest and v['identity_sha256']==identity and sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=policy).encode())==identity,'original_proof_byte_seal')
  require(v['passed'] is True and v['cleanup']['subreaper'] is True and v['cleanup']['survivors']=={},'actual_proof_success')
 leases=released();absent_scopes()
 with Path('/proc/meminfo').open('rb') as f:memraw=f.read(65537)
 require(len(memraw)<=65536,'bounded_kernel_meminfo')
 mem={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in memraw.decode().splitlines() if ':' in line}
 require(int(mem['MemAvailable'].split()[0])*1024>=80*1024**3,'unchanged_MemAvailable_floor')
 require(os.statvfs('/data1').f_bavail*os.statvfs('/data1').f_frsize>=max(21*1024**3,CONFIG['parent_required_data1_available_bytes']),'actual_reviewed_storage_floor')
 require(os.statvfs('/data').f_bavail*os.statvfs('/data').f_frsize>=24*1024**3,'unchanged_single_lane_raw_floor')
 overrides={'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONSAFEPATH':'1','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':str(HOOKS),'SWDB_DX100_BINDING_REQUEST':str(PUB/'request.json'),'SWDB_DX100_BINDING_REQUEST_SHA256':'afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822'}
 require(all(os.environ.get(k)==v for k,v in overrides.items()),'published_exact_environment')
 require(released()==leases,'lease_generation_drift_before_prepare');absent_scopes()
 for p,size,digest in FROZEN:require(exact(p,size,digest,UID)==frozen[str(p)],'selected_source_before_exec_changed')
 require(exact(HOOKS/'post-checkout',17300,'d340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527',UID,0o700)==hook and exact(PUB/'request.json',13676,'afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822',UID,0o600)==request,'published_inputs_before_exec_changed')
 require(datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_admission_window_before_exec');left()
 os.chdir(CLEAN);os.umask(0o077)
 argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','18300s','/usr/bin/python3.12',str(G),'--action','prepare','--final-source-sha',R,'--project',str(CLEAN),'--control',str(PREP),'--guard-sha256',FROZEN[0][2],'--cleanup-proof',str(PROOFS[0][0]),'--cleanup-proof-identity',PROOFS[0][2],'--supervisor-proof',str(PROOFS[1][0]),'--supervisor-proof-identity',PROOFS[1][2],'--','--source-sha',R,'--cleanup-proof',str(PROOFS[0][0]),'--source-ref','codex/lanl-analytic-eval','--source',str(SOURCE),'--raw',str(RAW),'--tag','20261007-a4']
 require(argv==CONFIG['direct_prepare_argv'],'exact_direct_prepare_argv')
 # Silent preflight: original 9c/fa/public stdout stays its own unprefixed stream.
 signal.alarm(0)
 os.execv(argv[0],argv)
def interrupted(number,frame):raise Refused('prepare_bootstrap_signal_'+str(number))
for number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)
signal.alarm(180)
try:run()
except BaseException as exc:
 body=json.dumps({'format':'swdb.lanl17-prepare-bootstrap-failure-original.v1','sealed':False,'error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'guard_exec_success_not_assessed':True},separators=(',',':')).encode()
 sys.stderr.buffer.write(body+b'\n');raise SystemExit(2)
