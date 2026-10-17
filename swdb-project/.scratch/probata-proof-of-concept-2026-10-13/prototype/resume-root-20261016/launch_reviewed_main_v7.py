"""2026-10-16 ET. Resumed main-source profile; bounded source budget, raw on /data, guarded lane."""
import base64,hashlib,json,pathlib,re,subprocess,sys
if sys.flags.optimize:raise ValueError('nonoptimized launcher required for admission assertions')
sha,kind,seconds,node,command_path,change_review_path=sys.argv[1:]
assert re.fullmatch('[0-9a-f]{40}',sha) and re.fullmatch('[a-z0-9-]{1,60}',kind)
seconds=int(seconds);node=int(node)
assert 60 <= seconds <= 21600 and node in (0,1)
command=json.loads(pathlib.Path(command_path).read_text())
assert isinstance(command,list) and command and all(isinstance(s,str) for s in command)
review=json.loads(pathlib.Path(change_review_path).read_text())
assert review['source_commit']==sha and review['baseline']=='c978393b119a3614229a37f0f2c8ca2a097c750b'
changes=review['files_after']
assert isinstance(changes,dict)
assert isinstance(review['planned_raw_budget_bytes'],int) and 0<review['planned_raw_budget_bytes']<=4*1024**3
assert isinstance(review['readers'],list) and 'root' in review['readers'] and all(isinstance(x,str) and x for x in review['readers'])
for name,h in changes.items():
 assert name.startswith(('swdb-project/swdb/','swdb-project/library/')) and '..' not in pathlib.PurePosixPath(name).parts
 assert h is None or re.fullmatch('[0-9a-f]{64}',h)
evidence=review['review_evidence']
assert hashlib.sha256(pathlib.Path(evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
review_pin={'path':str(pathlib.Path(change_review_path).resolve()),'sha256':hashlib.sha256(pathlib.Path(change_review_path).read_bytes()).hexdigest(),'content':review}
raw_root=review.get('raw_root')
if raw_root is not None:
 raw=pathlib.PurePosixPath(raw_root)
 assert str(raw)==raw_root and str(raw.parent)=='/data/yanruj/EvolveSWDB_runs'
 assert re.fullmatch('probata-resume-20261016-[a-z0-9-]{1,100}',raw.name) and sha[:8] in raw.name
controls=[]
for row in review.get('control_files',[]):
 assert set(row)=={'path','name','bytes','sha256'} and re.fullmatch('[a-zA-Z0-9_.-]{1,100}',row['name']) and row['name'] not in ('.','..')
 data=pathlib.Path(row['path']).read_bytes()
 assert type(row['bytes']) is int and len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 controls.append({**row,'base64':base64.b64encode(data).decode('ascii')})
assert len({row['name'] for row in controls})==len(controls) and sum(row['bytes'] for row in controls)<=1024**2
cfg={'sha':sha,'kind':kind,'seconds':seconds,'node':node,'command':command,'change_review':review_pin,'raw_root':raw_root,'control_files':controls}
script='cfg='+repr(cfg)+'\n'+r'''
import base64,datetime,hashlib,json,os,pathlib,pwd,shlex,shutil,subprocess,sys
P=pathlib.Path
assert not sys.flags.optimize,'nonoptimized remote admission required'
sha=cfg['sha'];node=cfg['node'];seconds=cfg['seconds']
source=P('/data1/yanruj/probata-resume-20261016-'+sha[:8])
old=P('/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative')
control=P('/data1/yanruj/Memacc-evolveswdb-lane');repo=P('/data1/yanruj/ArchEvolve')
def cmd(a):return subprocess.check_output(a,text=True).strip()
leases={p.name:json.loads(p.read_text()) for p in P('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
assert len(leases)==3
assert leases[f'mbit10-evaluation-node{node}.meta.json']['state']=='released'
assert leases['mbit10-evaluation.meta.json']['state']=='released'
pre={k:cmd(v) for k,v in {'uptime':['uptime'],'disk':['df','-h','/data1','/data'],'memory':['free','-h'],'users':['who'],'cpu':['lscpu'],'numa':['numactl','--hardware'],'kernel':['uname','-a']}.items()}
pre['leases']=leases
forbidden_names={'PYTHONOPTIMIZE','PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES','CPATH','CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','OBJC_INCLUDE_PATH','INCLUDE','SDKROOT','PYTEST_ADDOPTS','OCAMLPATH','WHY3LOADPATH','WHY3LIB','FRAMAC_PLUGIN','FRAMAC_SHARE','OCAMLFIND_CONF','OCAMLFIND_COMMANDS','OCAMLPARAM','OCAMLRUNPARAM'}
ambient=sorted(k for k in os.environ if k in forbidden_names or k.startswith(('FRAMAC_WP','WP_')))
assert sys.flags.isolated and not sys.flags.optimize,'isolated nonoptimized remote metadata interpreter required'
# SSH's PYTHONPATH is ignored by -I; actual lane env is rebuilt via direct env -i below.
assert set(ambient)<= {'PYTHONPATH'},('unreviewed ambient runtime selectors',ambient)
pre['outer_ambient_selector_names']=ambient
pre['outer_pythonpath_boundary']='ignored by isolated metadata interpreter; removed before actual lane process'
assert shutil.disk_usage('/data').free>=4*1024**3+20*1024**3,'raw disk needs20GiB floor plus4GiB reserved budget'
assert shutil.disk_usage('/data1').free>=10*1024**3+(0 if source.exists() else 2*1024**3),'source mount needs10GiB floor plus any new detached source; all raw remains on /data'
pre['cpu_policy']={str(p):p.read_text().strip() if p.exists() else 'unavailable' for p in map(P,['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor','/sys/devices/system/cpu/intel_pstate/no_turbo'])}
gpu=subprocess.run(['nvidia-smi'],text=True,capture_output=True);pre['gpu']={'exit_code':gpu.returncode,'stdout':gpu.stdout,'stderr':gpu.stderr}
subprocess.run(['git','-C',str(control),'-c','fetch.recurseSubmodules=false','fetch','--no-tags','origin','yanrujhou_main'],check=True)
wrapper=control/'AgenticRefiner/scripts/host/socket_lane.sh'
blob=subprocess.check_output(['git','-C',str(control),'show','FETCH_HEAD:AgenticRefiner/scripts/host/socket_lane.sh'])
assert wrapper.read_bytes()==blob
assert hashlib.sha256(blob).hexdigest()=='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
hostlock=control/'AgenticRefiner/scripts/host/hostlock.sh'
hostlock_blob=subprocess.check_output(['git','-C',str(control),'show','FETCH_HEAD:AgenticRefiner/scripts/host/hostlock.sh'])
assert hostlock.read_bytes()==hostlock_blob and hashlib.sha256(hostlock_blob).hexdigest()=='50745f827bac2a3db4fc56fdedc95f6fb57fb4b39cf9b269796c77c0274dc996'
pre['wrapper']={'sha256':hashlib.sha256(blob).hexdigest(),'fetched_commit':cmd(['git','-C',str(control),'rev-parse','FETCH_HEAD'])}
pre['primary_source']={'branch':cmd(['git','-C',str(repo),'rev-parse','--abbrev-ref','HEAD']),'commit':cmd(['git','-C',str(repo),'rev-parse','HEAD'])}
subprocess.run(['git','-C',str(repo),'fetch','--no-tags','origin','yanrujhou_main'],check=True)
subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',sha,'FETCH_HEAD'],check=True)
review=cfg['change_review']['content']; changes=review['files_after']
actual=cmd(['git','-C',str(repo),'diff','--name-only','--no-renames',review['baseline'],sha,'--','swdb-project/swdb','swdb-project/library']).splitlines()
assert set(actual)==set(changes),('reviewed production-change set mismatch',actual,list(changes))
for name,h in changes.items():
 blob=subprocess.run(['git','-C',str(repo),'show',sha+':'+name],capture_output=True)
 if h is None:assert blob.returncode!=0,name
 else:assert blob.returncode==0 and hashlib.sha256(blob.stdout).hexdigest()==h,name
pre['reviewed_source_changes']=cfg['change_review']
if not source.exists():subprocess.run(['git','-C',str(repo),'worktree','add','--detach',str(source),sha],check=True,stdout=sys.stderr)
assert cmd(['git','-C',str(source),'rev-parse','HEAD'])==sha
assert cmd(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'])=='HEAD'
assert not cmd(['git','-C',str(source),'status','--porcelain'])
for name,h in changes.items():
 if h is None:assert not (source/name).exists(),name
 else:assert hashlib.sha256((source/name).read_bytes()).hexdigest()==h,name
pre['source_branch']=cmd(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'])
out=P(cfg['raw_root']) if cfg['raw_root'] is not None else P('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-'+sha[:8]+'-'+cfg['kind'])
assert out.parent==P('/data/yanruj/EvolveSWDB_runs') and not out.is_symlink()
out.mkdir(exist_ok=False)
if cfg['control_files']:
 (out/'control').mkdir(exist_ok=False)
 for row in cfg['control_files']:
  data=base64.b64decode(row['base64'],validate=True)
  assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
  destination=out/'control'/row['name']
  with destination.open('xb') as stream:stream.write(data)
  assert hashlib.sha256(destination.read_bytes()).hexdigest()==row['sha256']
pre['staged_control_files']=[{k:v for k,v in row.items() if k!='base64'} for row in cfg['control_files']]
launch=json.loads((old/'launch.json').read_text())
launch.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),node=node,timeout_seconds=seconds,source=str(source),source_commit=sha,log_name='acceptance.log',readers=review['readers'],planned_raw_budget_bytes=review['planned_raw_budget_bytes'])
launch['command']=[s.replace('{SOURCE}',str(source)).replace('{OUTPUT}',str(out)) for s in cfg['command']]
launch['reviewed_wrapper_reuse']={n:hashlib.sha256((old/n).read_bytes()).hexdigest() for n in ('execute.py','watch.py')}
assert launch['reviewed_wrapper_reuse']=={'execute.py':'ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612','watch.py':'4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c'}
(out/'launch.json').write_text(json.dumps(launch,indent=2)+'\n');(out/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
for n in ('execute.py','watch.py'):(out/n).write_bytes((old/n).read_bytes())
assert hashlib.sha256((old/'run.sh').read_bytes()).hexdigest()=='650f815cb7562767829d94e8868da56990c98301376b999af6c659fbe499fcf3'
run=(old/'run.sh').read_text()
assert str(old) in run and '/data1/yanruj/probata-composed-0e7f2327' in run
(out/'run.sh').write_text(run.replace(str(old),str(out)).replace('/data1/yanruj/probata-composed-0e7f2327',str(source)))
session='probata-resume-20261016-'+sha[:8]+'-'+cfg['kind']
argv=['bash',str(wrapper),str(node),session,'--record',str(out/'lane.json'),'--','timeout','--signal=TERM','--kill-after=60',str(seconds+120),'bash',str(out/'run.sh')]
(out/'dispatch-argv.json').write_text(json.dumps(argv,indent=2)+'\n')
account=pwd.getpwuid(os.getuid())
sanitized={'HOME':account.pw_dir,'USER':account.pw_name,'LOGNAME':account.pw_name,'SHELL':'/bin/bash','PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LANG':'C','LC_ALL':'C'}
(out/'dispatch-environment.json').write_text(json.dumps(sanitized,indent=2)+'\n')
# Multiple tmux argv directly exec env before any shell, independent of server environment.
subprocess.run(['tmux','new-session','-d','-s',session,'-c',str(control/'AgenticRefiner'),'/usr/bin/env','-i',*[k+'='+v for k,v in sanitized.items()],'/bin/bash','-c',shlex.join(argv)+' >'+shlex.quote(str(out/'dispatch.log'))+' 2>&1'],check=True)
print(json.dumps({'launch':launch,'output':str(out),'session':session,'wrapper':pre['wrapper']},indent=2))
'''
r=subprocess.run(['ssh','mbit10','python3','-I','-B','-'],input=script,text=True,capture_output=True)
print(r.stdout);print(r.stderr,file=sys.stderr);sys.exit(r.returncode)
