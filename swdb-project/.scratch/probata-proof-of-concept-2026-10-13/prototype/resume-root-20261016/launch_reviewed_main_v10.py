"""2026-10-16 ET. Resumed main-source profile; bounded source budget, optional isolated sparse source, raw on /data, guarded lane."""
import base64,hashlib,json,pathlib,re,subprocess,sys
if sys.flags.optimize:raise ValueError('nonoptimized launcher required for admission assertions')
sha,kind,seconds,node,command_path,change_review_path=sys.argv[1:]
assert re.fullmatch('[0-9a-f]{40}',sha) and re.fullmatch('[a-z0-9-]{1,60}',kind)
seconds=int(seconds);node=int(node)
assert 60 <= seconds <= 21600 and node in (0,1)
command=json.loads(pathlib.Path(command_path).read_text())
assert isinstance(command,list) and command and all(isinstance(s,str) for s in command)
review=json.loads(pathlib.Path(change_review_path).read_text())
rss_cap=review.get('rss_cap_bytes',8589934592)
assert type(rss_cap) is int and rss_cap in (4294967296,8589934592)
run_unset=review.get('run_environment_unset',[])
assert run_unset in ([],['LIBRARY_PATH'])
SPARSE_SOURCE_SPEC={'date': '2026-10-16 ET', 'mode': 'isolated-shared-sparse-a102-v1', 'source_commit': 'a102e275cd23352aea8c268be3761d8a330b9be0', 'roots': ['swdb', 'schemas', 'vocab', 'library/methods/probata-draft-1.yaml', 'tests/fixtures/proof/methods/contract-fixture-1.yaml'], 'files': 424, 'bytes': 6184848, 'package_files': 336, 'inventory_sha256': '48d1dd271ee125508ddd6bc523089a2bf31e410629f70fdd29a0aeb4fdc9ff20', 'metadata_headroom_bytes': 1073741824, 'consumer_oids': {'swdb': '8a7b8844c50be710680ed7a7a4d9d96de3f994ff', 'schemas': '3f29308dbf4523b4970a973b4d9cb79cecab1aee', 'vocab': '4534a8a7d09e9b500caad1e6a13a3fe17823ce41', 'library/methods/probata-draft-1.yaml': 'eef43f6012a25696d32234d82f371ca022cb3004', 'tests/fixtures/proof/methods/contract-fixture-1.yaml': '494d26e2d1fc9aae6524e1287bb54d0f56e9b3d3'}}
source_checkout=review.get('source_checkout')
assert source_checkout is None or source_checkout==SPARSE_SOURCE_SPEC
assert source_checkout is None or sha==SPARSE_SOURCE_SPEC['source_commit']
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
cfg={'sha':sha,'kind':kind,'seconds':seconds,'node':node,'command':command,'change_review':review_pin,'raw_root':raw_root,'control_files':controls,'rss_cap_bytes':rss_cap,'run_environment_unset':run_unset,'source_checkout':source_checkout}
script='cfg='+repr(cfg)+'\n'+r'''
import base64,datetime,hashlib,json,os,pathlib,pwd,shlex,shutil,stat,subprocess,sys
P=pathlib.Path
assert not sys.flags.optimize,'nonoptimized remote admission required'
sha=cfg['sha'];node=cfg['node'];seconds=cfg['seconds']
source=P('/data1/yanruj/probata-resume-20261016-'+sha[:8])
old=P('/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative')
control=P('/data1/yanruj/Memacc-evolveswdb-lane');repo=P('/data1/yanruj/ArchEvolve')
def cmd(a):return subprocess.check_output(a,text=True).strip()
"""2026-10-16 ET. Inert fresh isolated shared-Git sparse source preparation.

Embedded into root launcher V10. Never touches sparse config in the primary,
registers a worktree, follows a selected source symlink or removes an old path.
"""


def sparse_git(root,*arguments,input=None):
 env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C',
      'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
 argv=['/usr/bin/git','--no-optional-locks','--no-replace-objects',
       '-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',
       '-c','core.preloadIndex=false','-c','index.threads=1',
       '-C',str(root),*arguments]
 return subprocess.check_output(argv,input=input,env=env,timeout=120)


def sparse_pin(path,limit=1024**2):
 assert path.resolve(strict=True)==path and stat.S_ISREG(path.lstat().st_mode)
 before=path.stat();assert before.st_size<=limit
 raw=path.read_bytes();after=path.stat()
 fields=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 assert fields(before)==fields(after) and len(raw)==before.st_size
 return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':fields(before)}


def sparse_primary_snapshot(repo):
 common=repo/'.git';assert common.resolve(strict=True)==common and common.is_dir()
 configs={}
 for p in [common/'config',common/'config.worktree',*sorted((common/'worktrees').glob('*/config.worktree'))]:
  configs[str(p)]={'absent':True} if not os.path.lexists(p) else sparse_pin(p)
 lock=repo/'swdb-project/records/.retention.lock'
 return {'configs':configs,'retention_lock':sparse_pin(lock),
         'worktree_registration_sha256':hashlib.sha256(sparse_git(repo,'worktree','list','--porcelain','-z')).hexdigest()}


def sparse_inventory(data):
 rows=[]
 for part in data.split(b'\0'):
  if not part:continue
  meta,name=part.split(b'\t',1);mode,kind,oid,size=meta.decode().split();path=name.decode()
  assert mode in ('100644','100755') and kind=='blob' and path.startswith('swdb-project/')
  assert '..' not in P(path).parts and not any(ord(c)<32 for c in path)
  rows.append({'path':path,'mode':mode,'oid':oid,'bytes':int(size)})
 assert len(rows)==len({r['path'] for r in rows})
 return rows


def sparse_materialize(repo,source,sha,spec):
 assert sha==spec['source_commit'] and source==P('/data1/yanruj/probata-resume-20261016-'+sha[:8])
 assert not os.path.lexists(source),'sparse route requires a fresh isolated clone; never replace/reconfigure an old source'
 roots=['swdb-project/'+name for name in spec['roots']]
 rows=sparse_inventory(sparse_git(repo,'ls-tree','-rlz',sha,'--',*roots))
 serialized=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
 assert len(rows)==spec['files'] and sum(r['bytes'] for r in rows)==spec['bytes']
 assert hashlib.sha256(serialized).hexdigest()==spec['inventory_sha256']
 assert {name:sparse_git(repo,'rev-parse',sha+':swdb-project/'+name).decode().strip()
         for name in spec['roots']}==spec['consumer_oids']
 reserve=spec['bytes']+spec['metadata_headroom_bytes']
 assert shutil.disk_usage('/data1').free>=10*1024**3+reserve
 before=sparse_primary_snapshot(repo)
 sparse_git(repo,'clone','--shared','--no-checkout','--no-hardlinks','--no-tags',str(repo),str(source))
 own=source/'.git'
 assert own.resolve(strict=True)==own and own.is_dir() and not own.is_symlink()
 assert P(sparse_git(source,'rev-parse','--absolute-git-dir').decode().strip())==own
 common=P(sparse_git(source,'rev-parse','--git-common-dir').decode().strip())
 assert (common if common.is_absolute() else source/common).resolve(strict=True)==own
 assert (own/'objects/info/alternates').read_text()==str(repo/'.git/objects')+'\n'
 # This is an ordinary isolated clone, never worktree sparse-checkout. Only its
 # own private config and pattern file are written before the first checkout.
 sparse_git(source,'config','--local','core.sparseCheckout','true')
 sparse_git(source,'config','--local','core.sparseCheckoutCone','false')
 sparse_git(source,'config','--local','index.sparse','false')
 patterns=''.join('/'+name+('/' if name in ('swdb-project/swdb','swdb-project/schemas','swdb-project/vocab') else '')+'\n' for name in roots)
 with (own/'info/sparse-checkout').open('xb') as stream:stream.write(patterns.encode())
 sparse_git(source,'checkout','--detach',sha)
 assert sparse_git(source,'rev-parse','HEAD').decode().strip()==sha
 assert sparse_git(source,'rev-parse','--abbrev-ref','HEAD').decode().strip()=='HEAD'
 assert not sparse_git(source,'status','--porcelain','--untracked-files=all','--ignored')
 expected={r['path'] for r in rows};found=set();pending=[source]
 allowed_dirs={str(parent) for name in expected for parent in P(name).parents if str(parent)!='.'}
 while pending:
  parent=pending.pop();assert parent.resolve(strict=True)==parent and stat.S_ISDIR(parent.lstat().st_mode)
  with os.scandir(parent) as stream:children=list(stream)
  for item in children:
   p=P(item.path);relative=str(p.relative_to(source));st=p.lstat()
   if p==own:
    assert stat.S_ISDIR(st.st_mode);continue
   if stat.S_ISDIR(st.st_mode):assert relative in allowed_dirs;pending.append(p)
   else:assert stat.S_ISREG(st.st_mode) and relative in expected;found.add(relative)
 assert found==expected,'sparse checkout physical membership must equal all424 selected Git leaves'
 physical=sparse_git(source,'hash-object','--no-filters','--stdin-paths',input=''.join(str(source/r['path'])+'\n' for r in rows).encode()).decode().splitlines()
 assert physical==[r['oid'] for r in rows]
 for row in rows:
  p=source/row['path'];assert p.stat().st_size==row['bytes']
  assert bool(p.stat().st_mode&0o111)==(row['mode']=='100755')
 assert sparse_primary_snapshot(repo)==before,'primary config/registration/retention-lock changed'
 assert shutil.disk_usage('/data1').free>=10*1024**3,'source mount10GiB floor remains mandatory after sparse materialization'
 return expected,{'mode':spec['mode'],'source_commit':sha,'files':len(rows),'bytes':spec['bytes'],
                  'inventory_sha256':spec['inventory_sha256'],'consumer_oids':spec['consumer_oids'],
                  'private_git_config':sparse_pin(own/'config'),'private_sparse_patterns':patterns,
                  'shared_object_store':str(repo/'.git/objects'),'primary_before_after':before,
                  'scope':'Exact small physical consumer projection of complete retained Git commit. Primary config/worktree registration/retention lock and1433 source/raw unchanged; no historical full physical checkout claim.'}

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
sparse=cfg['source_checkout']
if sparse is not None:assert not os.path.lexists(source),'isolated sparse source must be fresh'
source_reserve=(sparse['bytes']+sparse['metadata_headroom_bytes']) if sparse is not None else (0 if source.exists() else 2*1024**3)
assert shutil.disk_usage('/data1').free>=10*1024**3+source_reserve,'source mount needs10GiB floor plus reviewed new-source byte budget; all raw remains on /data'
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
sparse_files=None
if sparse is not None:
 sparse_files,pre['source_checkout']=sparse_materialize(repo,source,sha,sparse)
else:
 if not source.exists():subprocess.run(['git','-C',str(repo),'worktree','add','--detach',str(source),sha],check=True,stdout=sys.stderr)
assert cmd(['git','-C',str(source),'rev-parse','HEAD'])==sha
assert cmd(['git','-C',str(source),'rev-parse','--abbrev-ref','HEAD'])=='HEAD'
assert not cmd(['git','-C',str(source),'status','--porcelain'])
for name,h in changes.items():
 if sparse_files is not None and name not in sparse_files:
  # Full production changes were already independently hashed from exact sha in
  # primary Git above; excluded blobs remain in the complete shared object graph.
  assert not os.path.lexists(source/name),name
  continue
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
launch.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),node=node,timeout_seconds=seconds,rss_cap_bytes=cfg['rss_cap_bytes'],source=str(source),source_commit=sha,log_name='acceptance.log',readers=review['readers'],planned_raw_budget_bytes=review['planned_raw_budget_bytes'])
launch['command']=[s.replace('{SOURCE}',str(source)).replace('{OUTPUT}',str(out)) for s in cfg['command']]
launch['reviewed_wrapper_reuse']={n:hashlib.sha256((old/n).read_bytes()).hexdigest() for n in ('execute.py','watch.py')}
assert launch['reviewed_wrapper_reuse']=={'execute.py':'ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612','watch.py':'4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c'}
(out/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
guard_pins={}
for n in ('execute.py','watch.py'):
 original=(old/n).read_bytes()
 assert hashlib.sha256(original).hexdigest()==launch['reviewed_wrapper_reuse'][n],n
 assert original.count(b'cap_bytes=8589934592,')==1,n
 adapted=original.replace(b'cap_bytes=8589934592,',('cap_bytes='+str(cfg['rss_cap_bytes'])+',').encode())
 assert adapted.replace(('cap_bytes='+str(cfg['rss_cap_bytes'])+',').encode(),b'cap_bytes=8589934592,')==original,n
 (out/n).write_bytes(adapted)
 guard_pins[n]={'original_sha256':hashlib.sha256(original).hexdigest(),'actual_sha256':hashlib.sha256(adapted).hexdigest()}
assert hashlib.sha256((old/'run.sh').read_bytes()).hexdigest()=='650f815cb7562767829d94e8868da56990c98301376b999af6c659fbe499fcf3'
run=(old/'run.sh').read_text()
assert hashlib.sha256(run.encode()).hexdigest()=='650f815cb7562767829d94e8868da56990c98301376b999af6c659fbe499fcf3'
assert str(old) in run and '/data1/yanruj/probata-composed-0e7f2327' in run
assert run.count('SWDB_VERIFIER_RSS_CAP_BYTES=8589934592')==1
adapted_run=run.replace(str(old),str(out)).replace('/data1/yanruj/probata-composed-0e7f2327',str(source)).replace('SWDB_VERIFIER_RSS_CAP_BYTES=8589934592','SWDB_VERIFIER_RSS_CAP_BYTES='+str(cfg['rss_cap_bytes']))
if cfg['run_environment_unset']:
 selector_line='"$PROBATA_PYTHON" "$PROBATA_OUTPUT/watch.py"'
 assert adapted_run.count(selector_line)==1
 adapted_run=adapted_run.replace(selector_line,'unset LIBRARY_PATH\n'+selector_line)
(out/'run.sh').write_text(adapted_run)
guard_pins['run.sh']={'original_sha256':hashlib.sha256(run.encode()).hexdigest(),'actual_sha256':hashlib.sha256(adapted_run.encode()).hexdigest()}
(out/'root-guard-adaptation.json').write_text(json.dumps({'rss_cap_bytes':cfg['rss_cap_bytes'],'timeout_seconds':seconds,'run_environment_unset':cfg['run_environment_unset'],'files':guard_pins,'scope':'Exact resource-literal substitution only; reviewed original wrappers and launch remain retained'},indent=2)+'\n')
launch['reviewed_wrapper_originals']=launch['reviewed_wrapper_reuse']
launch['reviewed_wrapper_reuse']={n:guard_pins[n]['actual_sha256'] for n in ('execute.py','watch.py')}
(out/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
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
