"""Parent-owned, NOT RUN preparation for ONE archived 388b Linux fixture.

This dispatcher copies no source and invokes no scientific control main. Its only
payload is the already reviewed fixture through GNU timeout and socket_lane 1.
Every actual gate is evaluated in a future parent-selected invocation, not here.
"""
import argparse, ast, datetime, hashlib, json, os, re, shlex, signal, stat, subprocess, sys
from pathlib import Path

SSH_CAP_S = 600
REMOTE_SOURCE = r'''import ctypes,datetime,hashlib,importlib.util,json,os,re,shutil,signal,socket,stat,subprocess,sys,time
from pathlib import Path
UID=114316761
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
PRIMARY=Path('/data1/yanruj/ArchEvolve')
PROJECT=Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project')
MEMACC=Path('/data1/yanruj/Memacc-repro-20260925')
WRAPPER_REL='AgenticRefiner/scripts/host/socket_lane.sh'
WRAPPER=MEMACC/WRAPPER_REL
WRAPPER_SHA='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
HELPER=Path('/data1/yanruj/lanl17-control-20261006.py')
HELPER_SHA='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
EVIDENCE=Path('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
LIFECYCLE=PRIMARY/EVIDENCE/'14-export-reader-lifecycle-supervisor-controls-20261007-a1'
SUPERVISOR=LIFECYCLE/'lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py'
FIXTURE=LIFECYCLE/'lanl14_export_reader_early_nonzero_linux_fixture_20261007_a1.py'
SELECTED=PRIMARY/EVIDENCE/'14-lossless-report-export-controls-20261007-a1/lanl14_final_export_lossless_gzip_20261007_a1.py'
SOURCE_PINS={str(SUPERVISOR):[14547,'503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f'],
 str(FIXTURE):[16418,'388b9b1be3ce29c3d677ab2796c049793bf763504d4be7ad8e9f399c94354624'],
 str(SELECTED):[22967,'928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e']}
TOOLS={ '/usr/bin/python3.12':[8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'],
 '/usr/bin/timeout':[39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'],
 '/usr/bin/bash':[1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'],
 '/usr/bin/git':[4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb']}
ROOT=Path('/data/yanruj/EvolveSWDB_runs/lanl14-lifecycle-administration-20261007-a3')
DISPATCH=ROOT/'dispatch'
OUTPUT=ROOT/'lanl14-export-reader-control-early-nonzero-a1'
JOB='swdb-lanl14-lifecycle-early-nonzero-20261007-a3'
REPORT=Path('/data/yanruj/EvolveSWDB_runs/lanl-generality-final-20261007-a1')
LEASE_ROOT=Path('/data1/yanruj/lact-host-lease')
STARTUP_ABSENT=('BASH_ENV','ENV','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH','SOCKET_LANE_REEXEC','SOCKET_LANE_NODE_DIR','LACT_LEASE_ROOT','LACT_LEASE_NAME','LACT_NUMACTL','LOCKDIR')
OVERRIDES={'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(PROJECT),'LC_ALL':'C','PATH':'/usr/bin:/bin',
 'OMP_NUM_THREADS':'1','OMP_THREAD_LIMIT':'1','OMP_DYNAMIC':'FALSE','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
class Refused(RuntimeError):pass
class Interrupted(BaseException):pass
DEADLINE=time.monotonic()+540
def require(value,reason):
 if not value:raise Refused(reason)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def seal(value):return {**value,'identity_sha256':digest(value)}
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked(path,*,directory=False,owner=UID):
 p=Path(path);require(p.is_absolute() and '..' not in p.parts,'absolute nonsymlink path required')
 for part in (p,*p.parents):require(not part.is_symlink(),'symlink component refused')
 s=p.stat();require(s.st_uid==owner and (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)),'path owner/type differs')
 return p
def read_json(path,maximum=8*1024*1024):
 p=checked(path);s=p.stat();require(0<s.st_size<=maximum,'metadata bound differs');raw=p.read_bytes()
 require(len(raw)==s.st_size and ((read_after := p.stat()).st_dev,read_after.st_ino,read_after.st_mode,read_after.st_nlink,read_after.st_uid,read_after.st_gid,read_after.st_size,read_after.st_mtime_ns,read_after.st_ctime_ns)==(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns),'metadata changed during read')
 return json.loads(raw),{'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def private(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 require(stat.S_IMODE(checked(path).stat().st_mode)==0o600 and Path(path).read_bytes()==raw,'private returned bytes differ')
def private_json(path,data,maximum=16384):
 raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();require(len(raw)<=maximum,'compact receipt bound exceeded');private(path,raw)
 return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity_sha256':data.get('identity_sha256')}
def git(root,*args):
 env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0','LC_ALL':'C'}
 remaining=DEADLINE-time.monotonic();require(remaining>0,'dispatcher metadata deadline exceeded')
 child=subprocess.run(['/usr/bin/git','-C',str(root),*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(25,remaining),env=env)
 require(child.returncode==0,'fixed read-only Git command failed; private prose omitted')
 require(len(child.stdout)<=8*1024*1024,'Git output bound exceeded');return child.stdout
def text_git(root,*args):return git(root,*args).decode().strip()
def source_state(revision):
 checked('/data1/yanruj',directory=True);require(stat.S_IMODE(Path('/data1/yanruj').stat().st_mode)==0o700,'owned private data1 parent differs')
 checked(PRIMARY,directory=True);checked(PROJECT,directory=True);checked(MEMACC,directory=True)
 require(text_git(PRIMARY,'branch','--show-current')=='yanrujhou_main','primary branch differs')
 require(text_git(PRIMARY,'rev-parse','HEAD')==text_git(PRIMARY,'rev-parse','origin/yanrujhou_main')==revision,'delivered primary/origin revision differs')
 require(not git(PRIMARY,'diff','--name-only') and not git(PRIMARY,'diff','--cached','--name-only'),'primary tracked/staged changes retained; refusing')
 require(git(PRIMARY,'status','--porcelain')==b'?? swdb-project/records/.retention.lock\n','only original untracked primary retention lock is allowed')
 retention=checked(PRIMARY/'swdb-project/records/.retention.lock');retention_status=retention.stat();retention_raw=retention.read_bytes()
 require(retention_status.st_size==len(retention_raw)==0 and hashlib.sha256(retention_raw).hexdigest()=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' and ((retention_after := retention.stat()).st_dev,retention_after.st_ino,retention_after.st_mode,retention_after.st_nlink,retention_after.st_uid,retention_after.st_gid,retention_after.st_size,retention_after.st_mtime_ns,retention_after.st_ctime_ns)==(retention_status.st_dev,retention_status.st_ino,retention_status.st_mode,retention_status.st_nlink,retention_status.st_uid,retention_status.st_gid,retention_status.st_size,retention_status.st_mtime_ns,retention_status.st_ctime_ns),'original empty owned retention lock differs')
 require(text_git(PROJECT.parent,'rev-parse','HEAD')==C and not git(PROJECT.parent,'status','--porcelain'),'immutable C worktree differs; ignored history is retained')
 projections={'primary_retention_lock':{'path':str(retention),'bytes':0,'sha256':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','uid':retention_status.st_uid,'device':retention_status.st_dev,'inode':retention_status.st_ino,'mode':stat.S_IMODE(retention_status.st_mode)}}
 for root in (PRIMARY/'swdb-project',PROJECT):
  paths=sorted((root/'swdb').rglob('*.py'));require(len(paths)==185,'portable module count differs')
  files={p.relative_to(root/'swdb').as_posix():file_sha(checked(p)) for p in paths}
  # artifacts.digest/estimator_identity use ensure_ascii=True by default.
  bundle=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
  require(bundle==F6,'portable source bundle differs')
  yaml=[p for p in (root/'records').rglob('*') if p.is_file() and p.suffix in ('.yaml','.yml')]
  require(len(yaml)==(665 if root==PROJECT else 686),'immutable C/delivered primary catalog count differs')
  projections[str(root)]={'modules':185,'estimator_sha256':bundle,'canonical_yaml_count':len(yaml)}
 for path,(size,expected) in SOURCE_PINS.items():
  p=checked(path);raw=p.read_bytes();require(len(raw)==size and hashlib.sha256(raw).hexdigest()==expected and not p.stat().st_mode&0o022,'archived selected source differs')
  require(raw==git(PRIMARY,'show',revision+':'+p.relative_to(PRIMARY).as_posix()),'archive live bytes differ from delivered Git blob')
 require(file_sha(checked(HELPER))==HELPER_SHA,'original physical cleanup helper differs')
 require(file_sha(checked(PROJECT/'swdb/processes.py'))==PROCESSES_SHA,'frozen stop_group source differs')
 return projections
def native_state():
 require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact Linux mbit10 non-root account required')
 require(str(Path(sys.executable).resolve())=='/usr/bin/python3.12','native dispatcher interpreter differs')
 facts={}
 for path,(size,expected) in TOOLS.items():
  p=checked(path,owner=0);raw=p.read_bytes();s=p.stat()
  require(len(raw)==size and hashlib.sha256(raw).hexdigest()==expected and raw[:4]==b'\x7fELF' and s.st_mode&0o111 and not s.st_mode&0o022,'native root-owned ELF pin differs')
  facts[path]={'bytes':size,'sha256':expected,'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode)}
 for name in STARTUP_ABSENT:require(name not in os.environ,'startup override refused; value omitted')
 for name,expected in (('python3','/usr/bin/python3.12'),('bash','/usr/bin/bash')):
  actual=shutil.which(name,path=OVERRIDES['PATH']);require(actual and str(Path(actual).resolve())==expected,'wrapper PATH tool resolution differs')
 require(shutil.which('numactl',path=OVERRIDES['PATH']) is not None,'NUMA wrapper executable unavailable')
 return facts
def wrapper_state():
 dirty=git(MEMACC,'status','--porcelain');git(MEMACC,'fetch','origin','yanrujhou_main')
 expected=git(MEMACC,'show','origin/yanrujhou_main:'+WRAPPER_REL);actual=checked(WRAPPER).read_bytes()
 require(actual==expected and hashlib.sha256(actual).hexdigest()==WRAPPER_SHA,'fresh upstream wrapper authority differs')
 hostlock=MEMACC/'AgenticRefiner/scripts/host/hostlock.sh'
 require(checked(hostlock).read_bytes()==git(MEMACC,'show','origin/yanrujhou_main:AgenticRefiner/scripts/host/hostlock.sh'),'wrapper companion authority differs')
 require(git(MEMACC,'status','--porcelain')==dirty,'MemAcc dirty-file status changed; originals retained')
 return {'path':str(WRAPPER),'sha256':WRAPPER_SHA,'upstream_commit':text_git(MEMACC,'rev-parse','origin/yanrujhou_main'),
  'authority_ref':'origin/yanrujhou_main','dirty_status_sha256':hashlib.sha256(dirty).hexdigest(),'dirty_status_bytes':len(dirty),'dirty_files_not_modified_by_dispatcher':True}
def process(pid):
 p=Path('/proc')/str(pid);s=p.stat();fields=(p/'stat').read_text().rsplit(')',1)[1].split()
 require(s.st_uid==UID and fields[0]!='Z','lease holder UID/live state differs')
 return p,fields[19]
def lease_state():
 rows={name:read_json(LEASE_ROOT/(name+'.meta.json'))[0] for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
 require(rows['mbit10-evaluation-node1']['state']==rows['mbit10-evaluation']['state']=='released','node1/legacy not released')
 require(rows['mbit10-evaluation-node0']['state']=='held','required independent ticket14 node0 holder absent')
 lease=rows['mbit10-evaluation-node0']['lease'];require(lease['generation']==510 and lease['lease_name']=='mbit10-evaluation-node0','ticket14 generation 510 differs')
 pid=lease['daemon_pid'];require(type(pid)is int and pid>1,'lease holder PID differs');proc,stamp=process(pid)
 argv=proc.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
 require(argv[:4]==['bash',str(WRAPPER),'0','swdb-lanl14-reports-final-20261007-a1'],'ticket14 wrapper ownership differs')
 require(argv.count('--record')==1 and argv[argv.index('--record')+1]==str(REPORT/'control/lane.json') and argv.count('--')==1,'ticket14 lane record route differs')
 lane,pin=read_json(REPORT/'control/lane.json');lane=lane['socket_lane'];cpus=Path('/sys/devices/system/node/node0/cpulist').read_text().strip()
 child=['python3',str(REPORT/'control/helper.py'),'run','--manifest',str(REPORT/'manifest.json')]
 require(argv[argv.index('--')+1:]==lane['command']==child,'ticket14 child command binding differs')
 require(lane['job']==argv[3] and lane['node']==0 and lane['lease_generation']==510 and lane['lease_name']==lease['lease_name'] and lane['exit_code']==-1,'ticket14 live lane identity differs')
 require(lane['cpus_allowed_list']==cpus and lane['numa_memory_policy']=='bind:0','ticket14 lane confinement differs')
 require(os.readlink(proc/'fd/9')==str(LEASE_ROOT/'mbit10-evaluation-node0.lease'),'ticket14 authoritative FD9 differs')
 status=dict(line.split(':',1) for line in (proc/'status').read_text().splitlines() if ':' in line)
 require(status['Cpus_allowed_list'].strip()==cpus and (proc/'numa_maps').read_text().splitlines()[0].split()[1]=='bind:0','ticket14 actual confinement differs')
 require(process(pid)[1]==stamp,'ticket14 PID/start changed')
 require(file_sha(checked(REPORT/'control/helper.py'))=='e79e4b2e295f07967a1f4f67e7501c35d9d402101330ac9347f98cfb282bf63a','actual ticket14 helper source differs')
 return {'node0':{'state':'held','generation':510,'pid':pid,'start_time':stamp,'job':argv[3],'lane_original':pin},'node1':'released','legacy':'released'}
def capacity():
 data=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines());memory=int(data['MemAvailable'].split()[0])*1024
 disks={p:os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ('/data1','/data')}
 require(memory>=80*1024**3 and disks['/data1']>=21*1024**3 and disks['/data']>=2*1024**3,'administrative fixture capacity gate failed')
 return {'memory_available_bytes':memory,'free_disk_bytes':disks,'load_average':list(os.getloadavg()),'data_fixture_minimum_bytes':2*1024**3}
def load_cleanup():
 spec=importlib.util.spec_from_file_location('lanl14_dispatch_original_cleanup',HELPER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 spec2=importlib.util.spec_from_file_location('lanl14_dispatch_frozen_stop_group',PROJECT/'swdb/processes.py');module2=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(module2)
 return module,module2.stop_group
def main():
 revision,dispatcher_sha,remote_sha=sys.argv[1:];require(re.fullmatch('[a-f0-9]{40}',revision) and re.fullmatch('[a-f0-9]{64}',dispatcher_sha) and re.fullmatch('[a-f0-9]{64}',remote_sha),'explicit source/revision pins required')
 os.umask(0o077);native=native_state()
 require(file_sha(checked(HELPER))==HELPER_SHA and file_sha(checked(PROJECT/'swdb/processes.py'))==PROCESSES_SHA,'original cleanup/stop_group bytes differ')
 helper,stop_group=load_cleanup();require(ctypes.CDLL(None).prctl(36,1,0,0,0)==0,'dispatcher subreaper unavailable')
 checked(ROOT.parent,directory=True);require(not os.path.lexists(ROOT),'fresh administrative container required');ROOT.mkdir(mode=0o700);DISPATCH.mkdir(mode=0o700)
 require(stat.S_IMODE(checked(ROOT,directory=True).stat().st_mode)==stat.S_IMODE(checked(DISPATCH,directory=True).stat().st_mode)==0o700,'private container differs')
 argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','360s','/usr/bin/bash',str(WRAPPER),'1',JOB,
  '--record',str(DISPATCH/'lane.json'),'--lease-timeout-s','30','--','/usr/bin/python3.12','-B',str(FIXTURE),
  '--fixture-sha',SOURCE_PINS[str(FIXTURE)][1],'--supervisor',str(SUPERVISOR),'--supervisor-sha',SOURCE_PINS[str(SUPERVISOR)][1],
  '--helper',str(HELPER),'--project',str(PROJECT),'--selected-source',str(SELECTED),'--python','/usr/bin/python3.12',
  '--python-sha',TOOLS['/usr/bin/python3.12'][1],'--cwd',str(PROJECT),'--output',str(OUTPUT)]
 child=None;rc=None;failure=None;cleanup=None;errors=[];started=now();sources=None;wrapper=None;leases=None;resources=None;prereg_pin=None
 def interrupted(number,frame):raise Interrupted(number)
 previous={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP,signal.SIGALRM)}
 for s in previous:signal.signal(s,interrupted)
 signal.alarm(max(1,int(DEADLINE-time.monotonic())))
 try:
  sources=source_state(revision);wrapper=wrapper_state();leases=lease_state();resources=capacity()
  prereg=seal({'format':'swdb.lanl14-parent-early-nonzero-dispatch-preregistration.v1','canonical_ensure_ascii':False,'created_utc':now(),
   'delivered_revision':revision,'scientific_source_revision':C,'estimator_sha256':F6,'dispatcher_sha256':dispatcher_sha,'remote_program_sha256':remote_sha,
   'argv':argv,'environment_overrides':OVERRIDES,'cwd':str(PROJECT),'native_tools':native,'source_pins':SOURCE_PINS,'source_state':sources,
   'wrapper':wrapper,'leases_before':leases,'capacity_before':resources,'fixture_only':True,'one_attempt':True,'source_staging':False,'selected_control_main_invoked':False,
   'scientific_admission':False,'scope':'ONE original early-exit7 fixture; default alignment retained; no scientific result or production control admission.'})
  prereg_pin=private_json(DISPATCH/'preregistration.json',prereg)
  require(source_state(revision)==sources and lease_state()==leases,'pre-launch source/lease recheck differs');native_state();capacity()
  require(DEADLINE-time.monotonic()>=460,'complete GNU/cleanup window no longer available; refusing before fixture')
  out_fd=os.open(DISPATCH/'wrapper.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  err_fd=os.open(DISPATCH/'wrapper.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(out_fd,'wb') as out,os.fdopen(err_fd,'wb') as err:
   child=subprocess.Popen(argv,cwd=PROJECT,env={**os.environ,**OVERRIDES,'A5_PREREGISTRATION_SHA256':prereg['identity_sha256']},stdout=out,stderr=err,start_new_session=True)
   rc=child.wait(timeout=440)
 except BaseException as exc:failure=type(exc).__name__
 finally:
  signal.alarm(0)
  for s in previous:signal.signal(s,signal.SIG_IGN)
  try:stop_group(child,grace_seconds=15)
  except BaseException as exc:errors.append('stop_group:'+type(exc).__name__)
  try:cleanup=helper.cleanup_owned()
  except BaseException as exc:cleanup={'subreaper':True,'survivors':{'unknown':'cleanup failed'}};errors.append('cleanup_owned:'+type(exc).__name__)
  try:
   if sources is not None:require(source_state(revision)==sources,'post-run scientific/source bytes differ')
   native_state()
   if wrapper is not None:require(hashlib.sha256(git(MEMACC,'status','--porcelain')).hexdigest()==wrapper['dirty_status_sha256'],'MemAcc dirty status changed')
   final_leases=lease_state()
  except BaseException as exc:final_leases=None;errors.append('final_gates:'+type(exc).__name__)
  if cleanup is None or cleanup.get('survivors'):errors.append('cleanup_survivors')
  cleanup_pin=private_json(DISPATCH/'dispatcher-cleanup.json',cleanup or {},maximum=8*1024*1024)
  private(DISPATCH/'wrapper-exit-code.txt',(('unavailable' if rc is None else str(rc))+'\n').encode())
  originals={}
  for name in ('wrapper.stdout','wrapper.stderr','lane.json','wrapper-exit-code.txt'):
   p=DISPATCH/name
   if p.exists():require(stat.S_IMODE(checked(p).stat().st_mode)==0o600,'original privacy differs');originals[name]={'bytes':p.stat().st_size,'sha256':file_sha(p)}
  lane_ok=False
  if (DISPATCH/'lane.json').exists():
   value,_=read_json(DISPATCH/'lane.json');lane=value['socket_lane']
   lane_ok=lane.get('node')==1 and lane.get('job')==JOB and lane.get('lease_name')=='mbit10-evaluation-node1' and type(lane.get('lease_generation'))is int and lane['lease_generation']>0 and lane.get('exit_code')==0 and lane.get('command')==argv[argv.index('--')+1:] and lane.get('preregistration_sha256')==prereg['identity_sha256'] and lane.get('cpus_allowed_list')==Path('/sys/devices/system/node/node1/cpulist').read_text().strip() and lane.get('numa_memory_policy')=='bind:1' and lane.get('aligned_to') not in (None,'','none') and not lane.get('record_errors')
  fixture_pin=None;passed=False
  if (OUTPUT/'receipt.json').exists():
   data,fixture_pin=read_json(OUTPUT/'receipt.json',16384)
   require(data.get('canonical_ensure_ascii') is False and seal({k:v for k,v in data.items() if k!='identity_sha256'})==data,'original fixture False seal differs')
   passed=data.get('passed') is True and data.get('cases_expected')==data.get('cases_passed')==1 and data.get('worker_exit')==7 and data.get('fixture_script_sha256')==SOURCE_PINS[str(FIXTURE)][1] and data.get('supervisor_sha256')==SOURCE_PINS[str(SUPERVISOR)][1] and data.get('selected_source_sha256')==SOURCE_PINS[str(SELECTED)][1] and data.get('estimator_sha256')==F6 and data.get('native_python_sha256')==TOOLS['/usr/bin/python3.12'][1] and data.get('scientific_admission') is False and data.get('selected_exporter_or_reader_main_invoked') is False and data.get('cleanup',{}).get('survivor_count')==0
  success=rc==0 and failure is None and not errors and passed and lane_ok
  receipt=seal({'format':'swdb.lanl14-parent-early-nonzero-dispatch-result.v1','canonical_ensure_ascii':False,'started_utc':started,'ended_utc':now(),
   'passed':success,'fixture_only':True,'wrapper_exit':rc,'failure_type':failure,'cleanup_errors':errors,'preregistration':prereg_pin,'fixture_original':fixture_pin,'completed_node1_lane_bound':lane_ok,
   'originals':originals,'dispatcher_cleanup_original':cleanup_pin,'leases_after':final_leases,'dispatcher_sha256':dispatcher_sha,'remote_program_sha256':remote_sha,
   'delivered_revision':revision,'scientific_source_revision':C,'estimator_sha256':F6,'one_attempt':True,'scientific_admission':False,'selected_control_main_invoked':False,
   'scope':'Actual administrative fixture result only when this future main is selected. No scientific/native application result or production control admission.'})
  pin=private_json(DISPATCH/'receipt.json',receipt)
  for s,v in previous.items():signal.signal(s,v)
 print(json.dumps({'receipt':pin,'passed':success,'wrapper_exit':rc,'scientific_admission':False},ensure_ascii=False))
 return 0 if success else 1
try:sys.exit(main())
except Exception as exc:
 print(json.dumps({'failure_type':type(exc).__name__,'scientific_admission':False,'diagnostic_prose_omitted':True}),file=sys.stderr);sys.exit(2)
'''

def require(value, reason):
    if not value:
        raise RuntimeError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def checked_local(path, *, directory=False):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute local path required')
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'local symlink component refused')
    status = path.stat()
    require(status.st_uid == os.getuid() and (stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode)), 'local owner/type differs')
    return path

def private_file(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    require(Path(path).read_bytes() == raw, 'local returned bytes differ')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivered-revision', required=True)
    parser.add_argument('--dispatcher-sha256', required=True)
    parser.add_argument('--output-directory', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[a-f0-9]{40}', args.delivered_revision), 'exact delivered revision required')
    require(re.fullmatch('[a-f0-9]{64}', args.dispatcher_sha256), 'exact dispatcher source pin required')
    source = checked_local(Path(__file__).absolute()); original = source.read_bytes()
    require(sha(original) == args.dispatcher_sha256, 'dispatcher source differs')
    # Syntax inspection here is local metadata preparation, never a helper import.
    ast.parse(REMOTE_SOURCE)
    folder = Path(args.output_directory)
    require(folder.is_absolute() and folder.parent == Path('/private/tmp') and not os.path.lexists(folder), 'fresh local private tmp directory required')
    require(not folder.parent.is_symlink(), 'local parent symlink refused')
    os.umask(0o077); folder.mkdir(mode=0o700)
    require(stat.S_IMODE(checked_local(folder, directory=True).stat().st_mode) == 0o700, 'local privacy differs')
    remote_sha = sha(REMOTE_SOURCE.encode())
    remote_command = shlex.join(['/usr/bin/python3.12', '-B', '-', args.delivered_revision, args.dispatcher_sha256, remote_sha])
    argv = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', 'mbit10', remote_command]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    private_file(folder/'start.json', (json.dumps({'started_utc':started,'dispatcher_sha256':args.dispatcher_sha256,'remote_program_sha256':remote_sha,
        'delivered_revision':args.delivered_revision,'ssh_argv':argv,'ssh_cap_s':SSH_CAP_S,'one_attempt':True,'scientific_admission':False}, sort_keys=True)+'\n').encode())
    child = None; code = None; failure = None
    def interrupted(number, frame):
        raise InterruptedError(number)
    previous = {s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    for s in previous:
        signal.signal(s, interrupted)
    out_fd = os.open(folder/'ssh.stdout', os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    err_fd = os.open(folder/'ssh.stderr', os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(out_fd,'wb') as out, os.fdopen(err_fd,'wb') as err:
            child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=out, stderr=err, start_new_session=True)
            child.communicate(REMOTE_SOURCE.encode(), timeout=SSH_CAP_S)
            code = child.returncode
    except BaseException as exc:
        failure = type(exc).__name__
    finally:
        for s in previous:
            signal.signal(s, signal.SIG_IGN)
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=5)
        require(source.read_bytes() == original and sha(original) == args.dispatcher_sha256, 'dispatcher source changed')
        streams = {name:{'bytes':(folder/name).stat().st_size,'sha256':sha((folder/name).read_bytes())} for name in ('ssh.stdout','ssh.stderr')}
        receipt = {'format':'swdb.lanl14-parent-early-nonzero-ssh-custody.v1','canonical_ensure_ascii':False,'started_utc':started,
            'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ssh_exit':code,'failure_type':failure,'streams':streams,
            'dispatcher_sha256':args.dispatcher_sha256,'remote_program_sha256':remote_sha,'delivered_revision':args.delivered_revision,
            'one_attempt':True,'scientific_admission':False,'remote_fixture_admission_inherited_only_from_original_remote_receipt':True}
        receipt['identity_sha256']=sha(json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
        raw=(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
        require(len(raw)<=16384,'bounded local custody required');private_file(folder/'receipt.json',raw)
        for s,v in previous.items():
            signal.signal(s,v)
    print(json.dumps({'receipt':str(folder/'receipt.json'),'identity_sha256':receipt['identity_sha256'],'file_sha256':sha(raw),'ssh_exit':code,'failure_type':failure,'scientific_admission':False}))
    return 0 if code == 0 and failure is None else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({'failure_type':type(exc).__name__,'diagnostic_prose_omitted':True,'scientific_admission':False}),file=sys.stderr)
        sys.exit(2)
