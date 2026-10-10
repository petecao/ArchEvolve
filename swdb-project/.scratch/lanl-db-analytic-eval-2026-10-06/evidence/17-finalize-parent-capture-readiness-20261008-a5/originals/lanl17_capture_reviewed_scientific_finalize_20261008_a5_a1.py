"""2026-10-08 ET: parent-Mac original SSH custody for one future FINALIZE only.
SOURCE ONLY / NOT RUN. No P4 completion, FINALIZE result, scientific admission or fresh host facts supplied.
"""
import argparse,datetime,hashlib,json,os,re,resource,shlex,signal,stat,subprocess,sys,types
from pathlib import Path
MAX_SOURCE=1024*1024
MAX_STREAM=16*1024*1024
MAX_RETURN=16384
MAX_METADATA=2*1024*1024
LOCAL_WAIT=78720
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES')
R='5e12a9796432654d88def24ecea617d16ca605b2'
G='/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'
CLEAN='/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project'
FINALIZE='/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5'
PROJECT='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5/swdb-project'
M2='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json'
SMOKE='/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json'
SMOKE_ID='18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1'
PROOF='/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json'
PROOF_ID='ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b'
G_SHA='9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'
PUBLISHED_OVERRIDES={'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONSAFEPATH':'1','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':'/data1/yanruj/lanl17-dx100-hooks-20261008-a2','SWDB_DX100_BINDING_REQUEST':'/data1/yanruj/lanl17-dx100-deployment-20261008-a2/request.json','SWDB_DX100_BINDING_REQUEST_SHA256':'a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c'}
class Refusal(ValueError):pass

class CaptureSignal(BaseException):
 def __init__(self,number):self.number=number

class Parser(argparse.ArgumentParser):
 def error(self,message):raise Refusal('argument_contract')

def require(ok,code):
 if not ok:raise Refusal(code)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def stamp(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))

def read_exact(path,expected,maximum,owner):
 path=Path(path);require(path.is_absolute() and '..' not in path.parts,'absolute_path')
 for p in (path,*path.parents):require(not p.is_symlink(),'no_symlink')
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1 and not before.st_mode&0o022 and 0<before.st_size<=maximum,'source_owner_mode_size')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  require(stamp(os.fstat(fd))==stamp(before),'opened_stat')
  blocks=[];total=0
  while total<=maximum:
   b=os.read(fd,min(1024*1024,maximum-total+1))
   if not b:break
   blocks.append(b);total+=len(b)
  raw=b''.join(blocks)
  require(len(raw)==before.st_size and sha(raw)==expected and stamp(os.fstat(fd))==stamp(before)==stamp(path.lstat()),'returned_bytes')
 finally:os.close(fd)
 return {'path':str(path),'bytes':len(raw),'sha256':expected,'stat':stamp(before)},raw

def private_file(path):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 require(stat.S_IMODE(os.fstat(fd).st_mode)==0o600,'private0600');return os.fdopen(fd,'wb')

def original_json(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
 require(len(raw)<=MAX_RETURN,'original_metadata_bound')
 with private_file(path) as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {'path':str(path),'bytes':len(raw),'sha256':sha(raw),'sealed':False}

def stream_pin(path):
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid() and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and before.st_size<=MAX_STREAM,'private_original_stream')
 h=hashlib.sha256()
 with path.open('rb') as f:
  require(stamp(os.fstat(f.fileno()))==stamp(before),'stream_open_stat')
  while block:=f.read(1024*1024):h.update(block)
  require(stamp(os.fstat(f.fileno()))==stamp(before)==stamp(path.lstat()),'stream_closed_stat')
 return {'path':str(path),'bytes':before.st_size,'sha256':h.hexdigest(),'mode':'0600','sealed':False}

def ssh_file_limit():resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_STREAM,MAX_STREAM))
BOOT="import datetime,hashlib,json,os,pwd,re,signal,stat,subprocess,sys,time\nfrom pathlib import Path\nUID=114316761\nBASE=Path('/data1/yanruj');RUNS=Path('/data/yanruj/EvolveSWDB_runs');PRIMARY=BASE/'ArchEvolve'\nC='f893fed400347ed23d92e917d8bde21b75e5375d';R='5e12a9796432654d88def24ecea617d16ca605b2'\nF6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'\nCLEAN=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project'\nG=BASE/'lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'\nH=BASE/'lanl17-control-cleanup60-20261007-a4.py';SUP=BASE/'lanl17-metadata-supervisor-cleanup60-20261007-a4.py'\nSOURCE=BASE/'ArchEvolve-lanl17-source-20261007-a5';RAW=RUNS/'lanl17-actual-campaigns-20261007-a5'\nPREP=RUNS/'lanl17-metadata-prepare-20261007-a5';EF=BASE/'ArchEvolve-lanl17-freeze-evidence-20261007-a5'\nFINALIZE=RUNS/'lanl17-metadata-finalize-20261007-a5';M2=RAW/'manifest.json'\nER=BASE/'ArchEvolve-lanl17-actual-report-evidence-20261007-a5'\nPUB=BASE/'lanl17-dx100-deployment-20261008-a2';HOOKS=BASE/'lanl17-dx100-hooks-20261008-a2'\nFROZEN=[(G,14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),(H,38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),(SUP,8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0')]\nNATIVE=[('/usr/bin/python3.12',8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),('/usr/bin/timeout',39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),('/usr/bin/bash',1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),('/usr/bin/node',91392840,'3b442520134d4247f8d97ad4dc2d1443bdad6f0ebef670f06295743e864a37aa'),('/usr/bin/numactl',36080,'f3944bcd7848d64424f8daf27f350b03d7f3281b2fb9be5eaaba0ddd0e72efb8'),('/usr/bin/strace',2087432,'28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001'),('/usr/bin/tmux',1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd')]\nPROOFS=[(RUNS/'lanl17-cleanup-smoke-20261007-a4/receipt.json','873d36971b55e903731c9ab44a93ba5f1d8f3c563d0cf6dcefb2a48c8a6b063e','18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1',True),(RUNS/'lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json','12546c476589f3eceb6f779f53b710b8bd623c643b3417461fd4f21774c07436','ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b',False)]\nDEADLINE=time.monotonic()+180\nclass Refused(ValueError):pass\ndef require(ok,code):\n if not ok:raise Refused(code)\ndef left():\n n=DEADLINE-time.monotonic();require(n>0,'finalize_bootstrap_deadline');return n\ndef sha(b):return hashlib.sha256(b).hexdigest()\ndef stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))\ndef strict(b):\n def pairs(items):\n  d={}\n  for k,v in items:require(k not in d,'duplicate_key');d[k]=v\n  return d\n def bad(v):raise Refused('nonfinite_JSON')\n return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)\ndef canonical(p):require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_path')\ndef exact(p,size,digest,owner,mode=None):\n left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and s.st_size==size and (mode is None or stat.S_IMODE(s.st_mode)==mode),'exact_file_identity')\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);h=hashlib.sha256();n=0\n with os.fdopen(fd,'rb') as f:\n  require(stamp(os.fstat(f.fileno()))==stamp(s),'exact_open_stat')\n  while True:\n   left();b=f.read(min(1024*1024,size-n+1))\n   if not b:break\n   n+=len(b);require(n<=size,'exact_read_size');h.update(b)\n  require(n==size and h.hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'exact_returned_bytes_stat')\n return stamp(s)\ndef read(p,maximum):\n left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and s.st_size<=maximum,'bounded_metadata_identity')\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)\n with os.fdopen(fd,'rb') as f:\n  require(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_stat');b=f.read(maximum+1)\n  require(len(b)==s.st_size<=maximum and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'metadata_returned_bytes_stat')\n return b,stamp(s)\ndef git(root,*args,absent=False):\n left();r=subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(120,left()))\n if absent:require(r.returncode==1 and not r.stdout,'required_absent_Git_branch');return b''\n require(r.returncode==0 and not r.stderr and len(r.stdout)<=16*1024*1024,'read_only_Git');return r.stdout\ndef tree(root,ref):\n rows=git(root,'ls-tree','-rz',ref,'--','swdb-project/swdb')\n return {r.split(b'\\t',1)[1]:r.split(b'\\t',1)[0] for r in rows.split(b'\\0') if r and r.split(b'\\t',1)[1].endswith(b'.py')}\ndef released():\n out={}\n for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):\n  b,s=read(BASE/'lact-host-lease'/(name+'.meta.json'),32768);v=strict(b);require(v['state']=='released','all_three_leases_released');out[name]=(sha(b),s)\n return out\ndef phase_scopes():\n for p in (SOURCE,RAW,PREP,EF):canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and p.lstat().st_uid==UID,'retained_finalize_directory')\n require(not os.path.lexists(FINALIZE) and not os.path.lexists(ER) and not os.path.lexists(RAW/'final-export.json'),'fresh_finalize_output_routes')\n git(SOURCE,'show-ref','--verify','--quiet','refs/heads/codex/lanl17-actual-report-evidence-20261007-a5',absent=True)\n for cid in ('extensa-gem5-bfs-20261006-p1','extensa-gem5-bfs-20261006-p2','extensa-gem5-bfs-20261006-p3','extensa-gem5-bfs-20261006-p4'):\n  for name in ('validate-'+cid,'export-'+cid):\n   for suffix in ('.argv.json','.stdout','.stderr','.exit-code.txt'):require(not os.path.lexists(RAW/(name+suffix)),'fresh_finalize_public_original_routes')\n for name in ('final-agreement-report','validate-final-export'):\n  for suffix in ('.argv.json','.stdout','.stderr','.exit-code.txt'):require(not os.path.lexists(RAW/(name+suffix)),'fresh_finalize_public_original_routes')\n require(git(SOURCE,'rev-parse','HEAD').strip().decode()==R and not git(SOURCE,'status','--porcelain'),'clean_retained_S_R')\n require(tree(SOURCE,R)==tree(CLEAN.parent,C),'185_S_C_R_Git_source_equality')\n exact(M2,292401,'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1',UID)\n b,s=read(M2,2*1024*1024);v=strict(b)\n require(v['identity_sha256']=='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7' and sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode())==v['identity_sha256'],'original_M2_true_seal')\n require(v['source']==str(SOURCE) and v['raw']==str(RAW) and v['source_commit']==R and v['helper_sha256']==FROZEN[1][2] and v['estimator_sha256']==F6,'original_M2_finalize_scope')\n modules={}\n for p in sorted((SOURCE/'swdb-project/swdb').rglob('*.py')):\n  b,s=read(p,2*1024*1024);modules[p.relative_to(SOURCE/'swdb-project/swdb').as_posix()]=sha(b)\n require(len(modules)==185 and sha(json.dumps(modules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==F6,'S185_physical_F6')\ndef run():\n require(sys.platform=='linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and not sys.flags.optimize,'native_host_account')\n require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'native_bootstrap_Python')\n require(os.environ.get('HOME')==pwd.getpwuid(UID).pw_dir and os.environ.get('CODEX_HOME')=='/data1/yanruj/.codex' and os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')=='/data1/yanruj/.codex','preserved_account_home_and_original_token')\n canonical(BASE);bs=BASE.lstat();require(stat.S_ISDIR(bs.st_mode) and bs.st_uid==UID and stat.S_IMODE(bs.st_mode)==0o700,'private_BASE')\n for p in (RUNS,CLEAN,PRIMARY,PUB,HOOKS):canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and p.lstat().st_uid==UID,'owned_required_directory')\n for route,size,digest in NATIVE:exact(Path(route),size,digest,0,0o755)\n frozen={str(p):exact(p,size,digest,UID) for p,size,digest in FROZEN}\n hook=exact(HOOKS/'post-checkout',20078,'f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a',UID,0o700)\n request=exact(PUB/'request.json',19596,'a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c',UID,0o600)\n require(CONFIG['final_source_commit']==R and CONFIG['expected_primary']==R,'exact_frozen_R_and_primary')\n valid=datetime.datetime.fromisoformat(CONFIG['admission_valid_until_utc']);require(valid.tzinfo is not None and datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_admission_window')\n require(git(PRIMARY,'rev-parse','HEAD').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'rev-parse','origin/yanrujhou_main').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'branch','--show-current').strip()==b'yanrujhou_main','actual_primary_revision')\n require(not git(PRIMARY,'diff','--name-only') and not git(PRIMARY,'diff','--cached','--name-only') and git(PRIMARY,'status','--porcelain','--untracked-files=all').strip()==b'?? swdb-project/records/.retention.lock','primary_tracked_clean_exact_retention')\n exact(PRIMARY/'swdb-project/records/.retention.lock',0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',UID)\n require(git(CLEAN.parent,'rev-parse','HEAD').strip().decode()==C and not git(CLEAN.parent,'status','--porcelain'),'clean_C_source')\n require(git(CLEAN.parent,'rev-parse',R+'^{commit}').strip().decode()==R,'delivered_R_object_in_C')\n pyC,pyR=tree(CLEAN.parent,C),tree(CLEAN.parent,R);require(len(pyC)==185 and pyC==pyR,'185_C_R_Git_source_equality')\n require(tree(PRIMARY,CONFIG['expected_primary'])==pyC,'primary_scientific_python_equivalence')\n modules={}\n for p in sorted((CLEAN/'swdb').rglob('*.py')):\n  b,s=read(p,2*1024*1024);modules[p.relative_to(CLEAN/'swdb').as_posix()]=sha(b)\n require(len(modules)==185 and sha(json.dumps(modules,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==F6,'C185_physical_F6')\n exact(CLEAN/'swdb/processes.py',912,'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289',UID,0o644)\n for p,digest,identity,policy in PROOFS:\n  b,s=read(p,4*1024*1024);v=strict(b);require(sha(b)==digest and v['identity_sha256']==identity and sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=policy).encode())==identity,'original_proof_byte_seal')\n  require(v['passed'] is True and v['cleanup']['subreaper'] is True and v['cleanup']['survivors']=={},'actual_proof_success')\n leases=released();phase_scopes()\n with Path('/proc/meminfo').open('rb') as f:memraw=f.read(65537)\n require(len(memraw)<=65536,'bounded_kernel_meminfo')\n mem={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in memraw.decode().splitlines() if ':' in line}\n require(int(mem['MemAvailable'].split()[0])*1024>=80*1024**3,'unchanged_MemAvailable_floor')\n require(os.statvfs('/data1').f_bavail*os.statvfs('/data1').f_frsize>=max(21*1024**3,CONFIG['parent_required_data1_available_bytes']),'actual_reviewed_storage_floor')\n require(os.statvfs('/data').f_bavail*os.statvfs('/data').f_frsize>=24*1024**3,'unchanged_single_lane_raw_floor')\n overrides={'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONSAFEPATH':'1','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':str(HOOKS),'SWDB_DX100_BINDING_REQUEST':str(PUB/'request.json'),'SWDB_DX100_BINDING_REQUEST_SHA256':'a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c'}\n require(all(os.environ.get(k)==v for k,v in overrides.items()),'published_exact_environment')\n require(released()==leases,'lease_generation_drift_before_finalize');phase_scopes()\n for p,size,digest in FROZEN:require(exact(p,size,digest,UID)==frozen[str(p)],'selected_source_before_exec_changed')\n require(exact(HOOKS/'post-checkout',20078,'f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a',UID,0o700)==hook and exact(PUB/'request.json',19596,'a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c',UID,0o600)==request,'published_inputs_before_exec_changed')\n require(datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_admission_window_before_exec');left()\n os.chdir(SOURCE/'swdb-project');os.umask(0o077)\n argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','78300s','/usr/bin/python3.12',str(G),'--action','finalize','--final-source-sha',R,'--project',str(SOURCE/'swdb-project'),'--control',str(FINALIZE),'--guard-sha256',FROZEN[0][2],'--cleanup-proof',str(PROOFS[0][0]),'--cleanup-proof-identity',PROOFS[0][2],'--supervisor-proof',str(PROOFS[1][0]),'--supervisor-proof-identity',PROOFS[1][2],'--','--manifest',str(M2)]\n require(argv==CONFIG['direct_finalize_argv'],'exact_direct_finalize_argv')\n # Silent preflight: original 9c/fa/public stdout stays its own unprefixed stream.\n signal.alarm(0)\n os.execv(argv[0],argv)\ndef interrupted(number,frame):raise Refused('finalize_bootstrap_signal_'+str(number))\nfor number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)\nsignal.alarm(180)\ntry:run()\nexcept BaseException as exc:\n body=json.dumps({'format':'swdb.lanl17-finalize-bootstrap-failure-original.v1','sealed':False,'error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'guard_exec_success_not_assessed':True},separators=(',',':')).encode()\n sys.stderr.buffer.write(body+b'\\n');raise SystemExit(2)\n"
PRESTARTUP='if [[ "${CODEX_HOME-}" != /data1/yanruj/.codex ]]; then exit 2; fi\nif [[ -n "${SWDB_LANL17_ORIGINAL_CODEX_HOME-}" && "${SWDB_LANL17_ORIGINAL_CODEX_HOME-}" != /data1/yanruj/.codex ]]; then exit 2; fi\nexport SWDB_LANL17_ORIGINAL_CODEX_HOME=/data1/yanruj/.codex || exit 2\nfor key in "${!GIT_@}"; do unset "$key" || exit 2; done\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT PYTHONOPTIMIZE LD_PRELOAD LD_LIBRARY_PATH BASH_ENV ENV || exit 2\nexport PATH=/usr/bin:/bin:/usr/local/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONSAFEPATH=1\nexport GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/data1/yanruj/lanl17-dx100-hooks-20261008-a2\nexport SWDB_DX100_BINDING_REQUEST=/data1/yanruj/lanl17-dx100-deployment-20261008-a2/request.json SWDB_DX100_BINDING_REQUEST_SHA256=a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c\nexec "$@"\n'

def strict_json(raw):
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,'duplicate_JSON_key');d[k]=v
  return d
 def bad(v):raise Refusal('nonfinite_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def direct_argv():
 return ['/usr/bin/timeout','--signal=TERM','--kill-after=60s','78300s','/usr/bin/python3.12',G,'--action','finalize','--final-source-sha',R,'--project',PROJECT,'--control',FINALIZE,'--guard-sha256',G_SHA,'--cleanup-proof',SMOKE,'--cleanup-proof-identity',SMOKE_ID,'--supervisor-proof',PROOF,'--supervisor-proof-identity',PROOF_ID,'--','--manifest',M2]
def checked_time(value):
 require(isinstance(value,str),'explicit_UTC_time');d=datetime.datetime.fromisoformat(value);require(d.tzinfo is not None,'UTC_timezone_required');return d

def admission(path,digest,primary):
 pin,raw=read_exact(path,digest,MAX_METADATA,os.geteuid());doc=strict_json(raw)
 require(doc['format']=='swdb.lanl17-parent-finalize-preflight-admission.v1' and doc['accepted_for_finalize'] is True and doc['scientific_outcome_admission'] is False,'explicit_parent_finalize_admission')
 require(primary==R and doc['expected_primary']==R and doc['final_source_commit']==R and doc['direct_finalize_argv']==direct_argv() and doc['published_environment_overrides']==PUBLISHED_OVERRIDES,'exact_parent_scope')
 require(doc['all_four_normal_terminal_custody_root_and_peer_reviewed'] is True and doc['fresh_host_observation_reviewed'] is True and doc['current_all_three_leases_released_reviewed'] is True and doc['no_lease_reuse_or_campaign_writes_until_finalize_complete'] is True and doc['post_campaign_storage_headroom_reviewed'] is True,'genuine_parent_four_campaign_and_host_review')
 require(type(doc['required_data1_available_bytes']) is int and doc['required_data1_available_bytes']>=21*1024**3,'explicit_reviewed_storage_requirement')
 now=datetime.datetime.now(datetime.timezone.utc);start=checked_time(doc['checked_utc']);end=checked_time(doc['valid_until_utc']);require(start<=now<=end and 0<(end-start).total_seconds()<=300,'explicit_parent_admission_time_window')
 expected={'fresh_host_observation_pin','manifest_M2_pin'}|{cid+'_'+role+'_review_pin' for cid in ('p1','p2','p3','p4') for role in ('root','peer')}
 require(set(doc['original_input_pins'])==expected,'all_four_original_review_and_host_M2_pins')
 originals={}
 for key,p in doc['original_input_pins'].items():
  require(set(p)=={'path','bytes','sha256'} and type(p['bytes']) is int and p['bytes']>0 and re.fullmatch('[a-f0-9]{64}',p['sha256']),'exact_original_input_pin')
  route=Path(p['path']);require(str(route).startswith('/private/tmp/'),'private_original_input_route')
  seen,b=read_exact(route,p['sha256'],MAX_METADATA,os.geteuid());require(seen['bytes']==p['bytes'],'original_input_bytes');originals[key]=(seen,b)
 seen,b=originals['manifest_M2_pin'];require(seen['bytes']==292401 and seen['sha256']=='b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1','exact_M2_original')
 m=strict_json(b);require(m['identity_sha256']=='66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7' and sha(json.dumps({k:v for k,v in m.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==m['identity_sha256'],'M2_original_true_seal')
 host=strict_json(originals['fresh_host_observation_pin'][1]);v=host
 fields=doc['fresh_host_observation_UTC_JSON_path'];require(isinstance(fields,list) and fields and all(isinstance(k,str) for k in fields),'original_observation_time_field')
 for k in fields:v=v[k]
 require(checked_time(v)==checked_time(doc['fresh_host_observation_utc']) and checked_time(v)<=start,'exact_original_fresh_host_time')
 # Review originals remain parent-reviewed custody, not numerical admission.
 # Native account/source/lease/capacity/source pins are rechecked in bootstrap.
 return pin,doc,originals

def main():
 os.umask(0o077);p=Parser(description=__doc__,allow_abbrev=False)
 for n in ('source-sha256','ssh-sha256','parent-admission-sha256','expected-primary'):p.add_argument('--'+n,required=True)
 for n in ('parent-admission','local-processes','capture-directory'):p.add_argument('--'+n,required=True,type=Path)
 p.add_argument('--ssh-bytes',required=True,type=int);a=p.parse_args()
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_native_Mac_flags')
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 for v in (a.source_sha256,a.ssh_sha256,a.parent_admission_sha256):require(re.fullmatch('[a-f0-9]{64}',v),'exact_SHA')
 require(re.fullmatch('[a-f0-9]{40}',a.expected_primary),'exact_primary_revision')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0);require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'pinned_native_local_SSH')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid());require(procspin['bytes']==912,'exact_owned_SSH_cleanup')
 apin,ad,originals=admission(a.parent_admission,a.parent_admission_sha256,a.expected_primary)
 root=a.capture_directory;require(root.parent==Path('/private/tmp') and re.fullmatch('lanl17-scientific-finalize-capture-[a-z0-9-]{1,70}',root.name) and not os.path.lexists(root),'fresh_private_capture')
 root.mkdir(mode=0o700);require(root.lstat().st_uid==os.geteuid() and stat.S_IMODE(root.lstat().st_mode)==0o700,'capture0700')
 helpers=types.ModuleType('lanl17_finalize_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future exact reviewed cleanup primitive only.
 config={'expected_primary':a.expected_primary,'final_source_commit':R,'direct_finalize_argv':direct_argv(),'admission_valid_until_utc':ad['valid_until_utc'],'parent_required_data1_available_bytes':ad['required_data1_available_bytes'],'parent_admission_original':apin,'original_review_M2_and_host_pins':{k:v[0] for k,v in originals.items()},'original_fresh_host_pin':originals['fresh_host_observation_pin'][0]}
 stdin=('CONFIG='+repr(config)+'\n'+BOOT).encode();require(len(stdin)<=64*1024,'bootstrap_stdin_cap')
 with private_file(root/'stdin.py') as f:f.write(stdin);f.flush();os.fsync(f.fileno())
 stdinpin=stream_pin(root/'stdin.py')
 remote=['/usr/bin/bash','--noprofile','--norc','-p','-c',PRESTARTUP,'reviewed-lanl17-finalize-prestartup','/usr/bin/python3.12','-B','-s','-']
 argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();started=now()
 start=original_json(root/'start.json',{'format':'swdb.lanl17-scientific-finalize-parent-SSH-start.v1','sealed':False,'started_utc':started,'execution_not_yet_started':True,'public_SSH_argv':argv,'direct_finalize_argv':direct_argv(),'explicit_child_environment_overrides':PUBLISHED_OVERRIDES,'HOME_CODEX_HOME_original_token_preserved':False,'HOME_CODEX_HOME_preserved':True,'task_marker_restored_to_public_CODEX_HOME':True,'task_marker_value':'/data1/yanruj/.codex','authentication_contents_read':False,'bootstrap_stdin':stdinpin,'bootstrap_source_sha256':sha(BOOT.encode()),'prestartup_source_sha256':sha(PRESTARTUP.encode()),'bootstrap_preflight_s':180,'direct_GNU_s':78300,'direct_GNU_KILL_s':60,'local_wait_s':LOCAL_WAIT,'source':ownpin,'local_SSH':sshpin,'local_owned_cleanup_source':procspin,'parent_admission_original':apin,'four_campaign_review_M2_and_host_original_pins':{k:v[0] for k,v in originals.items()},'selected_finalize_completion_and_scientific_admission_not_assessed':True,'no_retry':True})
 watched=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP);old={n:signal.getsignal(n) for n in watched}
 def interrupt(number,frame):raise CaptureSignal(number)
 child=None;code=None;failure=None;timeout=False;received=None;cleanup_failure=None;postpins=False
 try:
  for n in watched:signal.signal(n,interrupt)
  try:
   require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin and read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid())[0]==procspin,'immediate_local_source_native_pins')
   require(admission(a.parent_admission,a.parent_admission_sha256,a.expected_primary)[0]==apin,'immediate_parent_admission_original')
   for seen,b in originals.values():require(read_exact(Path(seen['path']),seen['sha256'],MAX_METADATA,os.geteuid())[0]==seen,'immediate_original_input_stat')
   require(stream_pin(root/'stdin.py')==stdinpin,'unchanged_stdin_original')
   with (root/'stdin.py').open('rb') as inp,private_file(root/'stdout') as out,private_file(root/'stderr') as err:
    child=subprocess.Popen(argv,stdin=inp,stdout=out,stderr=err,start_new_session=True,preexec_fn=ssh_file_limit)
    try:child.wait(timeout=LOCAL_WAIT);code=child.returncode
    except subprocess.TimeoutExpired:timeout=True;failure='TimeoutExpired'
  except BaseException as exc:
   failure=type(exc).__name__
   if isinstance(exc,CaptureSignal):received=signal.Signals(exc.number).name
  finally:
   for n in watched:signal.signal(n,signal.SIG_IGN)
   try:helpers.stop_group(child,grace_seconds=15)
   except BaseException as exc:cleanup_failure=type(exc).__name__
  try:
   require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin and read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid())[0]==procspin,'postflight_local_source_native_pins')
   require(read_exact(a.parent_admission,a.parent_admission_sha256,MAX_METADATA,os.geteuid())[0]==apin,'postflight_admission_original_bytes_stat')
   for seen,b in originals.values():require(read_exact(Path(seen['path']),seen['sha256'],MAX_METADATA,os.geteuid())[0]==seen,'postflight_review_M2_host_original_stat')
   require(stream_pin(root/'stdin.py')==stdinpin,'postflight_stdin_original');postpins=True
  except BaseException as exc:failure='Postflight:'+type(exc).__name__
  value={'format':'swdb.lanl17-scientific-finalize-parent-SSH-transport.v1','sealed':False,'started_utc':started,'ended_utc':now(),'start_original':start,'SSH_exit_code':code,'timed_out':timeout,'signal_received':received,'failure_type':failure,'owned_SSH_cleanup_error':cleanup_failure,'original_private_streams':{n:stream_pin(root/n) for n in ('stdout','stderr') if (root/n).exists()},'local_source_native_admission_input_before_after_pins_equal':postpins,'remote_finalize_completion_not_assessed':True,'remote_termination_or_cleanup_not_inferred_from_SSH_exit':True,'scientific_or_campaign_admission':False,'remote_artifacts_not_removed_or_retried':True}
  resultpin=original_json(root/'transport.json',value)
  compact={'transport_original':resultpin,'SSH_exit_code':code,'timed_out':timeout,'signal_received':received,'failure_type':failure,'owned_SSH_cleanup_error':cleanup_failure,'remote_finalize_completion_not_assessed':True,'remote_original_guard_supervisor_helper_report_ER_review_required':True}
  raw=json.dumps(compact,separators=(',',':'),allow_nan=False).encode();require(len(raw)<=MAX_RETURN,'compact_return_bound');sys.stdout.buffer.write(raw+b'\n')
  return 0 if code==0 and failure is None and cleanup_failure is None and not timeout else 2
 finally:
  for n,handler in old.items():signal.signal(n,handler)
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as exc:
  print(json.dumps({'status':'local_finalize_capture_refusal','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'remote_finalize_completion_not_assessed':True},separators=(',',':')));raise SystemExit(2)
