"""2026-10-08 ET: parent-Mac private SSH custody for ONE future fresh NORMAL dispatch.
SOURCE ONLY / NOT RUN. Existing immutable 28d remains the only campaign launcher.
A successful SSH transport is not lane acquisition, campaign completion or admission.
"""
import argparse,datetime,hashlib,json,os,re,resource,shlex,signal,stat,subprocess,sys,types
from pathlib import Path
MAX_SOURCE=1024*1024
MAX_STREAM=16*1024*1024
MAX_RETURN=16384
MAX_METADATA=32*1024*1024
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
STARTUP=('BASH_ENV','ENV','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES')
R='5e12a9796432654d88def24ecea617d16ca605b2'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
H='/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py'
H_SHA='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
M2='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4/manifest.json'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a4'
B08_SHA='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
CIDS=tuple('extensa-gem5-bfs-20261006-p'+str(i) for i in range(1,5))
PUBLISHED_OVERRIDES={'PATH': '/usr/bin:/bin:/usr/local/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONSAFEPATH': '1', 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath', 'GIT_CONFIG_VALUE_0': '/data1/yanruj/lanl17-dx100-hooks-20261008-a1', 'SWDB_DX100_BINDING_REQUEST': '/data1/yanruj/lanl17-dx100-deployment-20261008-a1/request.json', 'SWDB_DX100_BINDING_REQUEST_SHA256': 'afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822'}

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

def strict_json(raw):
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,'duplicate_JSON_key');d[k]=v
  return d
 def bad(v):raise Refusal('nonfinite_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def checked_time(value):
 require(isinstance(value,str),'explicit_UTC_time');d=datetime.datetime.fromisoformat(value);require(d.tzinfo is not None,'UTC_timezone_required');return d

BOOT="import datetime,hashlib,json,os,pwd,re,shutil,signal,stat,subprocess,sys,time\nfrom pathlib import Path\nUID=114316761\nBASE=Path('/data1/yanruj');PRIMARY=BASE/'ArchEvolve'\nR='5e12a9796432654d88def24ecea617d16ca605b2'\nF6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'\nH=BASE/'lanl17-control-cleanup60-20261007-a4.py'\nH_SHA='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'\nS=BASE/'ArchEvolve-lanl17-source-20261007-a4'\nRAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4')\nNATIVE=[('/usr/bin/python3.12',8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),('/usr/bin/timeout',39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),('/usr/bin/bash',1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),('/usr/bin/git',4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),('/usr/bin/node',91392840,'3b442520134d4247f8d97ad4dc2d1443bdad6f0ebef670f06295743e864a37aa'),('/usr/bin/numactl',36080,'f3944bcd7848d64424f8daf27f350b03d7f3281b2fb9be5eaaba0ddd0e72efb8'),('/usr/bin/strace',2087432,'28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001'),('/usr/bin/tmux',1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd')]\nMAX_METADATA=32*1024*1024\nDEADLINE=time.monotonic()+180\nclass Refused(ValueError):pass\ndef require(ok,code):\n if not ok:raise Refused(code)\ndef left():\n n=DEADLINE-time.monotonic();require(n>0,'dispatch_bootstrap_deadline');return n\ndef sha(b):return hashlib.sha256(b).hexdigest()\ndef stamp(s):return tuple(getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns'))\ndef strict(b):\n def pairs(items):\n  d={}\n  for k,v in items:require(k not in d,'duplicate_key');d[k]=v\n  return d\n def bad(v):raise Refused('nonfinite_JSON')\n return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)\ndef canonical(p):require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical_nonsymlink_path')\ndef exact(p,size,digest,owner,mode=None):\n left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and s.st_size==size and (mode is None or stat.S_IMODE(s.st_mode)==mode),'exact_file_identity')\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);h=hashlib.sha256();n=0\n with os.fdopen(fd,'rb') as f:\n  require(stamp(os.fstat(f.fileno()))==stamp(s),'exact_open_stat')\n  while True:\n   left();b=f.read(min(1024*1024,size-n+1))\n   if not b:break\n   n+=len(b);require(n<=size,'exact_read_size');h.update(b)\n  require(n==size and h.hexdigest()==digest and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'exact_returned_bytes_stat')\n return stamp(s)\ndef read(p,maximum):\n left();canonical(p);s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o022 and s.st_size<=maximum,'bounded_metadata_identity')\n fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)\n with os.fdopen(fd,'rb') as f:\n  require(stamp(os.fstat(f.fileno()))==stamp(s),'metadata_open_stat');b=f.read(maximum+1)\n  require(len(b)==s.st_size<=maximum and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'metadata_returned_bytes_stat')\n return b,stamp(s)\ndef sealed(v):\n identity=v['identity_sha256'];require(re.fullmatch('[a-f0-9]{64}',identity) and v.get('canonical_ensure_ascii',True) is True,'original_default_or_explicit_True_policy')\n require(sha(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==identity,'original_True_seal')\ndef git(root,*args):\n left();r=subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(120,left()))\n require(r.returncode==0 and not r.stderr and len(r.stdout)<=16*1024*1024,'read_only_Git');return r.stdout\ndef tree(root,ref):\n rows=git(root,'ls-tree','-rz',ref,'--','swdb-project/swdb')\n return {r.split(b'\\t',1)[1]:r.split(b'\\t',1)[0] for r in rows.split(b'\\0') if r and r.split(b'\\t',1)[1].endswith(b'.py')}\ndef released():\n out={}\n for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):\n  b,s=read(BASE/'lact-host-lease'/(name+'.meta.json'),32768);v=strict(b);require(v['state']=='released','serial_first_all_three_leases_released');out[name]=(sha(b),s)\n return out\ndef fresh_attempt():\n cid=CONFIG['campaign']\n for p in (RAW/'attempts'/cid/'attempt-1',RAW/'campaign-runs/extensa'/cid):require(not os.path.lexists(p),'fresh_normal_attempt_and_campaign_absent')\ndef run():\n require(sys.platform=='linux' and os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and not sys.flags.optimize,'native_host_account')\n require(Path('/proc/self/exe').resolve(strict=True)==Path('/usr/bin/python3.12'),'native_bootstrap_Python')\n require(os.environ.get('HOME')==pwd.getpwuid(UID).pw_dir and os.environ.get('CODEX_HOME')=='/data1/yanruj/.codex' and os.environ.get('SWDB_LANL17_ORIGINAL_CODEX_HOME')=='/data1/yanruj/.codex','preserved_account_home_and_original_token')\n canonical(BASE);bs=BASE.lstat();require(stat.S_ISDIR(bs.st_mode) and bs.st_uid==UID and stat.S_IMODE(bs.st_mode)==0o700,'private_BASE')\n for p in (PRIMARY,S,S/'swdb-project',RAW):canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and p.lstat().st_uid==UID,'owned_required_directory')\n for route,size,digest in NATIVE:exact(Path(route),size,digest,0,0o755)\n for name,wanted in (('python3','/usr/bin/python3.12'),('timeout','/usr/bin/timeout'),('bash','/usr/bin/bash'),('git','/usr/bin/git'),('tmux','/usr/bin/tmux'),('numactl','/usr/bin/numactl'),('strace','/usr/bin/strace')):\n  route=shutil.which(name);require(route and Path(route).resolve(strict=True)==Path(wanted),'original_helper_native_PATH_route')\n hs=exact(H,38195,H_SHA,UID)\n require(not H.lstat().st_mode&0o022,'reviewed_helper_physical_mode')\n hook=exact(BASE/'lanl17-dx100-hooks-20261008-a1/post-checkout',17300,'d340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527',UID,0o700)\n request=exact(BASE/'lanl17-dx100-deployment-20261008-a1/request.json',13676,CONFIG['published_environment_overrides']['SWDB_DX100_BINDING_REQUEST_SHA256'],UID,0o600)\n require(re.fullmatch('[a-f0-9]{40}',CONFIG['expected_primary']),'explicit_actual_primary')\n require(git(PRIMARY,'rev-parse','HEAD').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'rev-parse','origin/yanrujhou_main').strip().decode()==CONFIG['expected_primary'] and git(PRIMARY,'branch','--show-current').strip()==b'yanrujhou_main','actual_primary_revision')\n require(not git(PRIMARY,'diff','--name-only') and not git(PRIMARY,'diff','--cached','--name-only') and git(PRIMARY,'status','--porcelain','--untracked-files=all').strip()==b'?? swdb-project/records/.retention.lock','primary_tracked_clean_exact_retention')\n exact(PRIMARY/'swdb-project/records/.retention.lock',0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',UID)\n py=tree(S,R);require(len(py)==185 and tree(PRIMARY,CONFIG['expected_primary'])==py,'source_primary185_Git_equality')\n require(git(S,'rev-parse','HEAD').strip().decode()==R and not git(S,'status','--porcelain'),'actual_M2_source_clean_R')\n pins={};docs={}\n for key in ('manifest','publication','before'):\n  pin=CONFIG['originals'][key];p=Path(pin['remote_path']);b,s=read(p,MAX_METADATA);require(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'original_remote_input_bytes');v=strict(b);sealed(v);require(v['identity_sha256']==pin['identity_sha256'],'original_remote_input_identity');pins[key]=s;docs[key]=v\n m=docs['manifest'];pub=docs['publication'];before=docs['before']\n require(Path(CONFIG['originals']['manifest']['remote_path'])==RAW/'manifest.json' and m['source']==str(S) and m['raw']==str(RAW) and m['source_commit']==R and m['estimator_sha256']==F6 and m['helper_sha256']==H_SHA,'exact_actual_M2_scope')\n require(pub['format']=='swdb.lanl17-freeze-publication-custody.v1' and pub['source_commit']==R and pub['manifest_sha256']==m['identity_sha256'] and pub['policy_sha256']==m['policy']['identity_sha256'] and pub['completed_export_exit_code']==0 and pub['application_outcomes_opened']==0 and pub['freeze_export_commit']==m['freeze_export']['commit'],'genuine_FIRST_publication')\n require(before['format']=='swdb.lanl17-attempt-control-custody.v2' and before['phase']=='before' and before['campaign']==CONFIG['campaign'] and before['attempt']==1 and before['resume'] is False and before['baselines_only'] is False and before['state']['present'] is False and before['manifest_identity_sha256']==m['identity_sha256'] and before['source_commit']==R and before['estimator_sha256']==F6,'genuine_fresh_normal_before_custody')\n require(before['freeze_publication_pin']['sha256']==CONFIG['originals']['publication']['sha256'] and before['manifest_file_pin']['sha256']==CONFIG['originals']['manifest']['sha256'],'before_original_input_links')\n valid=datetime.datetime.fromisoformat(CONFIG['valid_until_utc']);require(valid.tzinfo is not None and datetime.datetime.now(datetime.timezone.utc)<=valid,'explicit_parent_dispatch_window')\n require(all(os.environ.get(k)==v for k,v in CONFIG['published_environment_overrides'].items()),'published_exact_environment')\n leases=released();fresh_attempt()\n # No new campaign/provider/source deadline. Existing 28d owns live capacity,\n # fresh fetched wrapper, official provider, source/input/config checks and launch.\n require(released()==leases,'lease_generation_drift_before_dispatch');fresh_attempt()\n for key,pin in CONFIG['originals'].items():require(read(Path(pin['remote_path']),MAX_METADATA)[1]==pins[key],'original_metadata_stat_changed_before_dispatch')\n require(exact(H,38195,H_SHA,UID)==hs and exact(BASE/'lanl17-dx100-hooks-20261008-a1/post-checkout',17300,'d340f59f529d146ce4070843fc3314b0ab0b98cb1bacd79b2e9d61b726d07527',UID,0o700)==hook and exact(BASE/'lanl17-dx100-deployment-20261008-a1/request.json',13676,CONFIG['published_environment_overrides']['SWDB_DX100_BINDING_REQUEST_SHA256'],UID,0o600)==request,'sources_and_published_inputs_before_exec')\n require(datetime.datetime.now(datetime.timezone.utc)<=valid,'parent_window_before_dispatch');left()\n os.chdir(S/'swdb-project');os.umask(0o077)\n argv=['/usr/bin/python3.12','-B',str(H),'dispatch','--manifest',str(RAW/'manifest.json'),'--campaign',CONFIG['campaign'],'--node',str(CONFIG['node']),'--attempt','1']\n require(argv==CONFIG['direct_dispatch_argv'],'exact_original_dispatch_argv')\n # Silent bootstrap; stdout belongs to original 28d's dispatch result.\n signal.alarm(0);os.execv(argv[0],argv)\ndef interrupted(number,frame):raise Refused('dispatch_bootstrap_signal_'+str(number))\nfor number in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,interrupted)\nsignal.alarm(180)\ntry:run()\nexcept BaseException as exc:\n body=json.dumps({'format':'swdb.lanl17-campaign-dispatch-bootstrap-failure-original.v1','sealed':False,'error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'campaign_dispatch_result_not_assessed':True},separators=(',',':')).encode()\n sys.stderr.buffer.write(body+b'\\n');raise SystemExit(2)\n"
PRESTARTUP='for key in "${!GIT_@}"; do unset "$key" || exit 2; done\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONINSPECT PYTHONOPTIMIZE LD_PRELOAD LD_LIBRARY_PATH BASH_ENV ENV || exit 2\nexport PATH=/usr/bin:/bin:/usr/local/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONSAFEPATH=1\nexport GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/data1/yanruj/lanl17-dx100-hooks-20261008-a1\nexport SWDB_DX100_BINDING_REQUEST=/data1/yanruj/lanl17-dx100-deployment-20261008-a1/request.json SWDB_DX100_BINDING_REQUEST_SHA256=afaac0bf5e02b742318fcd1709546622f212ea73117d17e9e6e1c7ff13278822\nexec "$@"\n'

def direct_argv(campaign,node):
 return ['/usr/bin/python3.12','-B',H,'dispatch','--manifest',M2,'--campaign',campaign,'--node',str(node),'--attempt','1']

def original_inputs(a):
 rows={};docs={}
 for key in ('manifest','publication','before'):
  path=getattr(a,key+'_local_original');digest=getattr(a,key+'_sha256');remote=getattr(a,key+'_remote')
  require(re.fullmatch('[a-f0-9]{64}',digest),'explicit_original_SHA')
  rp=Path(remote);require(rp.is_absolute() and '..' not in rp.parts and str(rp).startswith(('/data1/yanruj/','/data/yanruj/EvolveSWDB_runs/')),'explicit_original_remote_route')
  pin,raw=read_exact(path,digest,MAX_METADATA,os.geteuid());doc=strict_json(raw)
  identity=doc['identity_sha256'];require(re.fullmatch('[a-f0-9]{64}',identity) and doc.get('canonical_ensure_ascii',True) is True,'original_default_or_explicit_True_policy')
  require(sha(json.dumps({k:v for k,v in doc.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==identity,'original_True_seal')
  rows[key]={'local_original':pin,'remote_path':remote,'bytes':pin['bytes'],'sha256':digest,'identity_sha256':identity,'original_canonical_ensure_ascii':True,'original_flag_present':'canonical_ensure_ascii' in doc};docs[key]=doc
 m,p,b=docs['manifest'],docs['publication'],docs['before']
 require(a.manifest_remote==M2 and m['format']=='swdb.lanl17-parent-population.v1' and m['source']==S and m['source_commit']==R and m['estimator_sha256']==F6 and m['helper_sha256']==H_SHA and m['source_clean'] is True,'actual_frozen_M2')
 require(re.fullmatch('[a-f0-9]{40}',m['freeze_export']['commit']) and re.fullmatch('[a-f0-9]{64}',m['policy']['identity_sha256']),'genuine_EF_and_policy_pins')
 require(p['format']=='swdb.lanl17-freeze-publication-custody.v1' and p['source_commit']==R and p['manifest_sha256']==m['identity_sha256'] and p['policy_sha256']==m['policy']['identity_sha256'] and p['completed_export_exit_code']==0 and p['application_outcomes_opened']==0 and p['freeze_export_commit']==m['freeze_export']['commit'],'FIRST_publication_before_outcomes_required')
 require(b['format']=='swdb.lanl17-attempt-control-custody.v2' and b['phase']=='before' and b['campaign']==a.campaign and b['attempt']==1 and b['resume'] is False and b['baselines_only'] is False and b['state']['present'] is False,'genuine_first_normal_before_required')
 require(b['source_commit']==R and b['estimator_sha256']==F6 and b['helper_sha256']==H_SHA and b['collector_sha256']==B08_SHA and b['manifest_identity_sha256']==m['identity_sha256'] and b['policy']==m['policy'] and b['actual_project_directory']==S+'/swdb-project' and b['actual_git_worktree_root']==S and b['source_clean'] is True,'before_scientific_source_and_scope')
 require(b['execution_account']['uid']==b['execution_account']['effective_uid']==114316761 and b['execution_account']['user']=='yanruj' and b['execution_account']['host']=='mbit10' and b['execution_account']['platform']=='linux','before_actual_account')
 for key,field in (('manifest','manifest_file_pin'),('publication','freeze_publication_pin')):
  v=b[field];require(v['path']==rows[key]['remote_path'] and v['bytes']==rows[key]['bytes'] and v['sha256']==rows[key]['sha256'],'before_original_file_links')
 require(b['invocation_inventory']['provider_directories']==[] and b['invocation_inventory']['synthesis_directory_present'] is False,'fresh_before_has_no_provider_or_synthesis_directory')
 now=datetime.datetime.now(datetime.timezone.utc);exclusive=checked_time(a.parent_exclusive_checked_utc);end=checked_time(a.valid_until_utc)
 require(all(x.utcoffset().total_seconds()==0 for x in (exclusive,end)) and checked_time(p['checked_utc'])<=checked_time(b['checked_utc'])<=exclusive<=now<=end,'explicit_parent_exclusive_dispatch_time_window')
 require(a.parent_exclusive_state_unchanged_reviewed is True,'parent_actual_exclusive_before_state_review_required')
 return rows,docs

def main():
 os.umask(0o077);p=Parser(description=__doc__,allow_abbrev=False)
 for n in ('source-sha256','ssh-sha256','expected-primary','parent-exclusive-checked-utc','valid-until-utc'):p.add_argument('--'+n,required=True)
 for n in ('local-processes','capture-directory'):p.add_argument('--'+n,required=True,type=Path)
 for key in ('manifest','publication','before'):
  p.add_argument('--'+key+'-local-original',required=True,type=Path);p.add_argument('--'+key+'-remote',required=True);p.add_argument('--'+key+'-sha256',required=True)
 p.add_argument('--ssh-bytes',required=True,type=int);p.add_argument('--node',required=True,type=int,choices=(0,1));p.add_argument('--campaign',required=True,choices=CIDS)
 p.add_argument('--transport-wait-s',required=True,type=int);p.add_argument('--parent-exclusive-state-unchanged-reviewed',action='store_true')
 a=p.parse_args()
 require(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'parent_native_Mac_flags')
 require(not any(k in os.environ for k in STARTUP),'local_startup_override')
 require(re.fullmatch('[a-f0-9]{40}',a.expected_primary),'explicit_actual_primary')
 for v in (a.source_sha256,a.ssh_sha256):require(re.fullmatch('[a-f0-9]{64}',v),'explicit_SHA')
 require(210<=a.transport_wait_s<=3600,'explicit_finite_administrative_transport_wait')
 own=Path(__file__).absolute();ownpin,_=read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())
 ssh=Path('/usr/bin/ssh');sshpin,_=read_exact(ssh,a.ssh_sha256,128*1024*1024,0);require(sshpin['bytes']==a.ssh_bytes and os.access(ssh,os.X_OK),'pinned_native_local_SSH')
 procspin,procsraw=read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid());require(procspin['bytes']==912,'exact_owned_SSH_cleanup')
 originals,docs=original_inputs(a)
 root=a.capture_directory;require(root.parent==Path('/private/tmp') and re.fullmatch('lanl17-normal-campaign-dispatch-capture-[a-z0-9-]{1,70}',root.name) and not os.path.lexists(root),'fresh_private_capture')
 root.mkdir(mode=0o700);require(root.lstat().st_uid==os.geteuid() and stat.S_IMODE(root.lstat().st_mode)==0o700,'capture0700')
 helpers=types.ModuleType('lanl17_dispatch_local_pinned_processes');helpers.__file__=str(a.local_processes)
 exec(compile(procsraw,str(a.local_processes),'exec'),helpers.__dict__) # Future exact reviewed local cleanup primitive only.
 config={'expected_primary':a.expected_primary,'campaign':a.campaign,'node':a.node,'attempt':1,'resume':False,'baselines_only':False,'direct_dispatch_argv':direct_argv(a.campaign,a.node),'published_environment_overrides':PUBLISHED_OVERRIDES,'originals':originals,'parent_exclusive_checked_utc':a.parent_exclusive_checked_utc,'valid_until_utc':a.valid_until_utc,'parent_exclusive_state_unchanged_reviewed':True,'serial_first_all_three_leases_required':True}
 stdin=('CONFIG='+repr(config)+'\n'+BOOT).encode();require(len(stdin)<=64*1024,'bootstrap_stdin_cap')
 with private_file(root/'stdin.py') as f:f.write(stdin);f.flush();os.fsync(f.fileno())
 stdinpin=stream_pin(root/'stdin.py')
 remote=['/usr/bin/bash','--noprofile','--norc','-p','-c',PRESTARTUP,'reviewed-lanl17-campaign-dispatch-prestartup','/usr/bin/python3.12','-B','-s','-']
 argv=[str(ssh),'-T','-o','BatchMode=yes','-o','ConnectTimeout=30','mbit10','exec '+shlex.join(remote)]
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();started=now()
 start=original_json(root/'start.json',{'format':'swdb.lanl17-normal-campaign-dispatch-parent-SSH-start.v1','sealed':False,'started_utc':started,'execution_not_yet_started':True,'public_SSH_argv':argv,'direct_dispatch_argv':direct_argv(a.campaign,a.node),'explicit_child_environment_overrides':PUBLISHED_OVERRIDES,'HOME_CODEX_HOME_original_token_preserved':True,'authentication_contents_read':False,'bootstrap_stdin':stdinpin,'bootstrap_source_sha256':sha(BOOT.encode()),'prestartup_source_sha256':sha(PRESTARTUP.encode()),'bootstrap_preflight_s':180,'local_wait_s':a.transport_wait_s,'local_wait_is_transport_only_not_campaign_cap':True,'source':ownpin,'local_SSH':sshpin,'local_owned_cleanup_source':procspin,'genuine_original_inputs':originals,'parent_exclusive_checked_utc':a.parent_exclusive_checked_utc,'parent_valid_until_utc':a.valid_until_utc,'parent_exclusive_state_unchanged_reviewed':True,'serial_first_all_three_leases_required':True,'original_generated_campaign_child_s':87000,'original_generated_campaign_GNU_s':88200,'original_generated_campaign_KILL_s':60,'selected_dispatch_lane_and_campaign_completion_not_assessed':True,'no_retry':True})
 watched=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP);old={n:signal.getsignal(n) for n in watched}
 def interrupt(number,frame):raise CaptureSignal(number)
 child=None;code=None;failure=None;timeout=False;received=None;cleanup_failure=None;postpins=False
 try:
  for n in watched:signal.signal(n,interrupt)
  try:
   require(read_exact(own,a.source_sha256,MAX_SOURCE,os.geteuid())[0]==ownpin and read_exact(ssh,a.ssh_sha256,128*1024*1024,0)[0]==sshpin and read_exact(a.local_processes,PROCESSES_SHA,MAX_SOURCE,os.geteuid())[0]==procspin,'immediate_local_source_native_pins')
   require(original_inputs(a)[0]==originals,'immediate_actual_original_inputs')
   require(stream_pin(root/'stdin.py')==stdinpin,'unchanged_stdin_original')
   with (root/'stdin.py').open('rb') as inp,private_file(root/'stdout') as out,private_file(root/'stderr') as err:
    child=subprocess.Popen(argv,stdin=inp,stdout=out,stderr=err,start_new_session=True,preexec_fn=ssh_file_limit)
    try:child.wait(timeout=a.transport_wait_s);code=child.returncode
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
   for key,pin in originals.items():require(read_exact(Path(pin['local_original']['path']),pin['sha256'],MAX_METADATA,os.geteuid())[0]==pin['local_original'],'postflight_actual_original_input_stat')
   require(stream_pin(root/'stdin.py')==stdinpin,'postflight_stdin_original');postpins=True
  except BaseException as exc:failure='Postflight:'+type(exc).__name__
  value={'format':'swdb.lanl17-normal-campaign-dispatch-parent-SSH-transport.v1','sealed':False,'started_utc':started,'ended_utc':now(),'start_original':start,'SSH_exit_code':code,'timed_out':timeout,'signal_received':received,'failure_type':failure,'owned_SSH_cleanup_error':cleanup_failure,'original_private_streams':{n:stream_pin(root/n) for n in ('stdout','stderr') if (root/n).exists()},'local_source_native_input_before_after_pins_equal':postpins,'remote_dispatch_lane_and_campaign_completion_not_assessed':True,'remote_termination_or_cleanup_not_inferred_from_SSH_exit':True,'scientific_or_campaign_admission':False,'remote_artifacts_not_removed_or_retried':True}
  resultpin=original_json(root/'transport.json',value)
  compact={'transport_original':resultpin,'SSH_exit_code':code,'timed_out':timeout,'signal_received':received,'failure_type':failure,'owned_SSH_cleanup_error':cleanup_failure,'remote_dispatch_lane_and_campaign_completion_not_assessed':True,'original_dispatch_prereg_wrapper_and_actual_custody_review_required':True}
  output=json.dumps(compact,separators=(',',':'),allow_nan=False).encode();require(len(output)<=MAX_RETURN,'compact_return_bound');sys.stdout.buffer.write(output+b'\n')
  return 0 if code==0 and failure is None and cleanup_failure is None and not timeout else 2
 finally:
  for n,handler in old.items():signal.signal(n,handler)
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as exc:
  print(json.dumps({'status':'local_normal_campaign_dispatch_capture_refusal','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'remote_dispatch_lane_and_campaign_completion_not_assessed':True},separators=(',',':')));raise SystemExit(2)
