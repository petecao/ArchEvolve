"""2026-10-16 ET. Exact reviewed function definitions; inert until root admission."""
import contextlib,hashlib,json,os,pathlib,re,shlex,shutil,stat,subprocess,sys
from pathlib import Path

def consumer_closure(project,repository,expected):
    commit=expected['source_commit'];trees=expected['source_consumer_trees']
    def git(*a,input=None):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repository),*a],input=input,timeout=180)
    for relative,tree in trees.items():
        if git('rev-parse','--verify',commit+':swdb-project/'+relative).decode().strip()!=tree['oid']:
            raise ValueError('source consumer Git tree/blob differs: '+relative)
    packed=git('ls-tree','-r','-z',commit,'--',*['swdb-project/'+x for x in trees])
    wanted=[]
    for entry in packed.split(b'\0'):
        if not entry:continue
        meta,name=entry.decode().split('\t',1);mode,kind,oid=meta.split()
        if mode not in {'100644','100755'}or kind!='blob' or not name.startswith('swdb-project/'):
            raise ValueError('source consumer requires exact regular Git blobs')
        relative=name.removeprefix('swdb-project/');p=project/relative
        if '\n'in str(p)or '\r'in str(p)or str(p).startswith('"'):raise ValueError('unreviewed source path encoding')
        wanted.append({'relative':relative,'git_blob':oid,'path':str(p)})
    found=set()
    for relative in trees:
        root=project/relative
        if root.is_symlink()or not(root.is_file()or root.is_dir()):raise ValueError('source consumer root changed')
        for p in ([root]if root.is_file()else root.rglob('*')):
            if p.is_symlink()or not(p.is_file()or p.is_dir()):raise ValueError('source consumer symlink/special input')
            if p.is_file():found.add(str(p.relative_to(project)))
    if found!={r['relative']for r in wanted}:raise ValueError('source consumer physical membership differs from exact admitted Git tree')
    # hash-object streams physical files and emits only40-byte object names.
    # It never captures the1.33GB catalog body or invokes a content filter.
    physical_oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n'for r in wanted).encode()).decode().splitlines()
    if physical_oids!=[r['git_blob']for r in wanted]:raise ValueError('source consumer physical bytes differ from immutable admitted Git blob')
    for row in wanted:
        p=Path(row['path']);h=hashlib.sha256()
        with p.open('rb')as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        row.update(sha256=h.hexdigest(),bytes=p.stat().st_size)
    return {'source_commit':commit,'trees':trees,'files':wanted,'count':len(wanted),
            'total_bytes':sum(r['bytes']for r in wanted),'physical_git_blob_equality':True,
            'scope':'Opaque source-byte identity only. Existing fixture helper selects/parses YAML header/reference closure; no unrelated scientific evidence or held-out source semantics inspected.'}


def pin(p):
 p=pathlib.Path(p);return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def ambient_check(env,config,source):
 if env.get('PYTHONPATH')not in (None,'',str(source)):raise ValueError('ambient PYTHONPATH differs from exact selected project')
 overrides=['PYTHONOPTIMIZE','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE','CPATH','CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','OBJC_INCLUDE_PATH','INCLUDE','SDKROOT','PYTEST_ADDOPTS','PYTEST_PLUGINS','OCAMLPATH']
 if any(env.get(name)for name in overrides):raise ValueError('ambient Python/compiler/pytest/OCaml override needs separate review')
 forbidden=sorted(k for k in env if k.startswith(('FRAMAC_WP','WP_')) or k=='SWDB_PROOF_REPORT_OUT')
 if forbidden:raise ValueError('forbidden ambient WP names: '+','.join(forbidden))
 for name in ('WHY3CONFIG','SWDB_WHY3_CONFIG'):
  if name in env and str(pathlib.Path(env[name]).resolve())!=str(pathlib.Path(config).resolve()):
   raise ValueError('ambient Why3 configuration differs from exact admitted path: '+name)
 return forbidden


def validate_linux_launch(expected,repository,raw,policy_file,policy_sha,entry_file,environment):
 binding=expected['linux_launch_binding'];raw=Path(raw).resolve();repository=Path(repository).resolve()
 if environment.get('PROBATA_OUTPUT')!=str(raw):raise ValueError('Linux coordinator output marker differs')
 if environment.get('SWDB_VERIFIER_LOCK')!=str(raw/'verifier.lock')or environment.get('SWDB_VERIFIER_RSS_CAP_BYTES')!='8589934592':raise ValueError('Linux outer lock/RSS context differs')
 launch_path=raw/'launch.json';launch=json.loads(launch_path.read_bytes())
 if Path(launch['source']).resolve()!=repository or launch.get('source_commit')!=expected['source_commit']:raise ValueError('Linux launch exact source differs')
 if launch.get('rss_cap_bytes')!=8589934592 or launch.get('workers')!=1 or launch.get('timeout_seconds')!=1200 or launch.get('node')!=binding['node']:raise ValueError('Linux whole-tree worker/budget/lane differs')
 entry_file=Path(entry_file).resolve();policy_file=Path(policy_file).resolve()
 if entry_file.parent!=raw/'control'or policy_file.parent!=raw/'control':raise ValueError('Linux controller metadata must use fresh raw control namespace')
 if pin(entry_file)['sha256']!=binding['entry_sha256']:raise ValueError('Linux controller entry bytes differ')
 wanted=[expected['tools']['opam']['path'],'exec','--switch=framac-33','--',binding['python'],'-I','-B',str(entry_file),str(repository/'swdb-project'),str(raw),str(policy_file),policy_sha]
 if launch.get('command')!=wanted:raise ValueError('Linux exact controller/expectation command differs')
 for name,digest in binding['wrappers'].items():
  if launch.get('reviewed_wrapper_reuse',{}).get(name)!=digest or pin(raw/name)['sha256']!=digest:raise ValueError('Linux outer execute/watch bytes differ')
 return {'launch':pin(launch_path),'source_commit':expected['source_commit'],'node':binding['node'],'rss_cap_bytes':8589934592,'whole_seconds':1200,'workers':1,'Mac_counted_token_required':False,'scope':'reviewed Linux execute/watch whole-tree watchdog; not a Mac counted run'}


def verified_linux_lane(node):
 # Bind environment assertions to the live kernel and held socket lease.
 lane=os.environ.get('LACT_SOCKET_LANE_PID','');generation=os.environ.get('LACT_SOCKET_LANE_GENERATION','')
 if not lane.isdigit()or not generation.isdigit():raise ValueError('live socket-lane ancestor/generation required')
 pid=os.getpid();ancestors=[]
 for _ in range(64):
  if pid<=1 or pid==int(lane):break
  ancestors.append(pid);tail=Path('/proc/'+str(pid)+'/stat').read_text().rsplit(') ',1)[1].split();pid=int(tail[1])
 if pid!=int(lane)or b'socket_lane.sh'not in Path('/proc/'+lane+'/cmdline').read_bytes():raise ValueError('claimed socket-lane process is not actual wrapper ancestor')
 def cpu_set(text):
  result=set()
  for part in text.strip().split(','):
   ends=part.split('-');first=int(ends[0]);last=int(ends[-1]);result.update(range(first,last+1))
  return result
 allowed=set(os.sched_getaffinity(0));node_cpus=cpu_set(Path('/sys/devices/system/node/node'+str(node)+'/cpulist').read_text())
 if not allowed or allowed!=node_cpus:raise ValueError('CPU affinity is not exact selected NUMA node')
 first=Path('/proc/self/numa_maps').read_text().splitlines()[0].split()
 if len(first)<2 or first[1]!='bind:'+str(node):raise ValueError('NUMA memory policy is not selected node bind')
 lease_root=Path('/data1/yanruj/lact-host-lease');name='mbit10-evaluation-node'+str(node);lease=lease_root/(name+'.lease')
 descriptor=Path('/proc/'+lane+'/fd/9')
 if descriptor.resolve()!=lease or (descriptor.stat().st_dev,descriptor.stat().st_ino)!=(lease.stat().st_dev,lease.stat().st_ino):raise ValueError('socket-lane ancestor does not hold selected lease fd9')
 metadata=json.loads((lease_root/(name+'.meta.json')).read_bytes());owner=metadata.get('lease',{})
 if metadata.get('state')!='held'or str(owner.get('daemon_pid'))!=lane or str(owner.get('generation'))!=generation:raise ValueError('live socket lease ownership/generation differs')
 return {'lease':name,'generation':int(generation),'ancestor_pid':int(lane),'ancestor_chain':ancestors,'cpus':sorted(allowed),'memory_policy':'bind:'+str(node),'fd9_matches_lease':True}


def import_surface(root,wanted):
 root=pathlib.Path(root)
 if root.is_symlink() or not root.is_dir():raise ValueError('selected import root changed')
 found=[]
 for p in sorted(root.rglob('*')):
  mode=p.lstat().st_mode
  if stat.S_ISLNK(mode) or not(stat.S_ISREG(mode) or stat.S_ISDIR(mode)):raise ValueError('nonregular import input')
  if stat.S_ISREG(mode):found.append({'relative':str(p.relative_to(root)),'sha256':pin(p)['sha256']})
 if found!=wanted:raise ValueError('selected full import-tree membership/hash differs: '+str(root))
 return {'path':str(root),'files':found,'count':len(found)}


def normalize_compiler_selector(env,wanted):
 command=wanted['command']
 if not isinstance(command,list)or len(command)!=1 or not isinstance(command[0],str)or not pathlib.Path(command[0]).is_absolute():
  raise ValueError('compiler normalization requires one admitted absolute command')
 expected=wanted['command_executable']
 if pathlib.Path(command[0]).resolve()!=pathlib.Path(expected['path']).resolve():
  raise ValueError('compiler normalization command and pinned wrapper differ')
 try:selected=shlex.split(env.get('SWDB_CLANG',shlex.join(command)))
 except (ValueError,TypeError):raise ValueError('malformed inherited Clang selector')from None
 observed=None
 if selected!=command:
  if selected!=['clang++']:raise ValueError('inherited Clang selector is not the exact reviewed alias')
  executable=shutil.which('clang++',path=env.get('PATH'))
  if executable is None or pathlib.Path(executable).resolve()!=pathlib.Path(expected['path']).resolve():
   raise ValueError('reviewed Clang alias resolves to another physical wrapper')
  if not pathlib.Path(executable).is_file()or pin(executable)['sha256']!=expected['sha256']:
   raise ValueError('reviewed Clang alias wrapper bytes differ')
  observed=pin(executable)
 env['SWDB_CLANG']=shlex.join(command)
 return {'input_tokens':selected,'selected_absolute_tokens':list(command),'reviewed_alias_used':selected==['clang++'],
         'resolved_alias_wrapper':observed,'scope':'exact root-export alias normalized only after pinned path/bytes check; producer absolute-command requirement unchanged'}


def compiler_preflight(env,wanted):
 command=wanted['command']
 if not isinstance(command,list) or len(command)!=1 or not isinstance(command[0],str) or not pathlib.Path(command[0]).is_absolute():
  raise ValueError('compiler command must be one selected absolute executable')
 try:selected=shlex.split(env.get('SWDB_CLANG',shlex.join(command)))
 except (ValueError,TypeError):raise ValueError('malformed ambient Clang command') from None
 if selected!=command:raise ValueError('ambient Clang command differs from admitted exact tokens')
 executable=shutil.which(command[0])
 expected=wanted['command_executable']
 if executable is None or pathlib.Path(executable).resolve()!=pathlib.Path(expected['path']).resolve():
  raise ValueError('selected Clang wrapper path differs before compiler execution')
 physical={}
 for name,row in [('command_executable',expected),('driver',wanted['driver'])]:
  path=pathlib.Path(row['path'])
  if not path.is_file() or pin(path)['sha256']!=row['sha256']:
   raise ValueError('Clang '+name+' bytes differ before compiler execution')
  physical[name]=pin(path)
 return {'command':list(command),'physical_components':physical}


def compiler_components(runtime,wanted):
 if any(k not in runtime for k in wanted) or {k:runtime[k]for k in wanted}!=wanted:
  raise ValueError('actual Linux Clang parser/driver/wrapper/header components differ')
 return {k:runtime[k]for k in wanted}


def source_check():
 head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,timeout=30).strip()
 dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain','--untracked-files=all'],text=True,timeout=30)
 if head!=EXPECTED['source_commit'] or dirty.strip():raise SystemExit('stream source is not exact clean admitted commit')
 for name,sha in EXPECTED['source_files'].items():
  if pin(project/name)['sha256']!=sha:raise SystemExit('stream profile source hash changed: '+name)


def load_controller_module_v4(name):
 import types
 if name not in EXPECTED['controller_files']:raise ValueError('unlisted controller input')
 path=policy_path.parent/name
 if path.is_symlink()or not path.is_file()or path.parent!=output/'control':raise ValueError('regular raw/control input required')
 data=path.read_bytes();wanted=EXPECTED['controller_files'][name]
 if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('controller input bytes differ: '+name)
 module=types.ModuleType('t28_reviewed_'+name.removesuffix('.py'))
 module.__file__=str(path)
 exec(compile(data,str(path),'exec'),module.__dict__)
 return module,data


def controller_root_observer_v4():
 if EXPECTED['root_observer_file']!='t28-linux-runtime-observer-v2-actual-20261016.json':raise ValueError('exact root observation metadata name required')
 path=policy_path.parent/EXPECTED['root_observer_file']
 wanted=EXPECTED['controller_files'][path.name]
 if path.is_symlink()or not path.is_file():raise ValueError('regular root observation metadata required')
 data=path.read_bytes()
 if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('root observation metadata bytes differ')
 return data


def runtime_surface_check_v4(label):
 controls={}
 names={Path(__file__).name,policy_path.name,*EXPECTED['controller_files']}
 if {path.name for path in policy_path.parent.iterdir()}!=names:raise ValueError('exact staged controller membership differs')
 if hashlib.sha256(policy_path.read_bytes()).hexdigest()!=sys.argv[4]or pin(__file__)['sha256']!=EXPECTED['linux_launch_binding']['entry_sha256']:raise ValueError('entry/policy bytes changed')
 for name,wanted in EXPECTED['controller_files'].items():
  path=policy_path.parent/name
  if path.name!=name or path.parent!=output/'control'or path.is_symlink()or not path.is_file():raise ValueError('regular closed controller basename required')
  data=path.read_bytes()
  if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('staged controller input changed: '+name)
  controls[name]=wanted
 python=closed_v4.verify_python_metadata(EXPECTED['python_surface_binding'])
 files={}
 for name,digest in EXPECTED['runtime_files'].items():
  row=pin(name)
  if row['sha256']!=digest:raise ValueError('complete physical runtime component differs: '+name)
  files[name]=row['sha256']
 meta=EXPECTED['framac_kernel_meta_origin']['pin']
 if Path(meta['path']).stat().st_size!=meta['bytes']or files.get(meta['path'])!=meta['sha256']:raise ValueError('fresh Frama kernel META physical pin differs')
 packages={}
 for name,root in EXPECTED['ocaml_packages'].items():
  root_path=Path(root)
  wanted=[{'relative':str(Path(path).relative_to(root_path)),'sha256':digest}for path,digest in EXPECTED['runtime_files'].items()if Path(path).is_relative_to(root_path)]
  wanted.sort(key=lambda row:Path(row['relative']).parts)
  if not wanted:raise ValueError('complete package file inventory is empty: '+name)
  packages[name]=import_surface(root_path,wanted)
 prefix=Path(EXPECTED['tools']['frama-c']['path']).parent.parent
 portable={name:import_surface(root,EXPECTED['portable_import_surfaces'][name])for name,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]}
 headers=header_surface_check_v4(EXPECTED['linux_header_surfaces'],EXPECTED['linux_clang_components']['headers'],closed_v4)
 receipt={'controller_files':controls,'python':python,'runtime_files':files,'ocaml_packages':packages,'portable_import_surfaces':portable,'linux_headers':headers,'scope':'Physical content/membership closure only; no solver or theorem result'}
 (output/('initialized-runtime-'+label+'.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 return receipt


def header_surface_check_v4(surfaces,wanted,closed):
 if set(surfaces)!={'libc++','clang-resource'}:raise ValueError('exact two LLVM header roots required')
 aggregate=hashlib.sha256();count=0;receipts={}
 for label in ('libc++','clang-resource'):
  expected=surfaces[label];root=Path(expected['path'])
  if closed._resolution(root,[])!=root or root.is_symlink()or not root.is_dir():raise ValueError('canonical physical LLVM header root required')
  rows=[]
  for path in sorted(root.rglob('*')):
   mode=path.lstat().st_mode
   if stat.S_ISLNK(mode)or not(stat.S_ISREG(mode)or stat.S_ISDIR(mode)):raise ValueError('LLVM header symlink/special input')
   if stat.S_ISDIR(mode):continue
   row,_unused=closed._regular(path)
   row={'relative':str(path.relative_to(root)),'bytes':row['bytes'],'sha256':row['sha256']}
   rows.append(row);aggregate.update(label.encode()+b'\0'+row['relative'].encode()+b'\0'+bytes.fromhex(row['sha256']));count+=1
  digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
  if len(rows)!=expected['count']or digest!=expected['inventory_sha256']:raise ValueError('complete LLVM header membership/content differs')
  receipts[label]={'path':str(root),'count':len(rows),'inventory_sha256':digest}
 identity={'id':'llvm-standard-resource-headers','sha256':aggregate.hexdigest(),'files':count}
 if identity!=wanted:raise ValueError('selected LLVM production header aggregate differs')
 return {'surfaces':receipts,'aggregate':identity}


def observe_startup_role_v4(plan,role,environment,cache):
 request=roles_v4.role_request_v2(plan,role=role,environment=environment,cache=cache)
 command=[EXPECTED['linux_launch_binding']['python']]
 if role=='entry-isolated':command+=['-I']
 command+=['-B','-X','pycache_prefix='+str(cache),'-c',observer_source_v4.decode(),json.dumps(request,sort_keys=True)]
 done=subprocess.run(command,cwd=project,env=environment,capture_output=True,text=True,timeout=30)
 evidence={'role':role,'argv_prefix':command[:command.index('-c')+1],'request':request,'exit_code':done.returncode,'stdout':done.stdout,'stderr':done.stderr,'observer_source_sha256':hashlib.sha256(observer_source_v4).hexdigest()}
 (output/('initialized-python-'+role+'.json')).write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 if done.returncode or done.stderr:raise ValueError('actual guarded Python startup role refused: '+role)
 observed=json.loads(done.stdout)
 receipt=roles_v4.check_role_observation_v2(request,observed)
 (output/('initialized-python-'+role+'-accepted.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 return receipt


def stdlib_check():
 root=pathlib.Path(EXPECTED['why3_stdlib'])
 if root.is_symlink() or not root.is_dir():raise SystemExit('standard library root is not a real directory')
 rows=[]
 for path in sorted(root.rglob('*')):
  mode=path.lstat().st_mode
  if stat.S_ISLNK(mode):raise SystemExit('standard library contains a symlink')
  if stat.S_ISDIR(mode):continue
  if not stat.S_ISREG(mode) or path.suffix!='.mlw':raise SystemExit('standard library has non-.mlw or special content')
  rows.append({'path':str(path.relative_to(root)),'sha256':pin(path)['sha256']})
 digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if len(rows)!=EXPECTED['stdlib_count'] or digest!=EXPECTED['stdlib_sha256']:raise SystemExit('standard library changed')
 return {'path':str(root),'count':len(rows),'sha256':digest}

