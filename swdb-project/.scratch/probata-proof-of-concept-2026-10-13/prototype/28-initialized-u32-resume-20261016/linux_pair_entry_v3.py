"""2026-10-16 ET. INERT root-only initialized-u32 pair; root supplies fresh exact published source/policy.

Root selects a clean exact source checkout after preservation/capacity admission.
Original PARTIAL initialized-u32 result711 versus1107; original counters plus cells0/1 frame.
All eight reviewed guards unchanged; complete current source/runtime closure.
Entry authoring grants no actual tool admission, source/body theorem, hardware progress or whole28 acceptance.
"""
import contextlib,hashlib,json,os,pathlib,re,shlex,shutil,stat,subprocess,sys
from pathlib import Path
if not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode:raise SystemExit("actual profile requires isolated nonoptimized Python with -B")
# Root supplies reviewed exact policy after publishing the new source freeze.
if len(sys.argv)!=5:raise SystemExit('usage: entry PROJECT RAW_ROOT POLICY POLICY_SHA256')
policy_path=pathlib.Path(sys.argv[3]);policy_bytes=policy_path.read_bytes()
if not re.fullmatch('[a-f0-9]{64}',sys.argv[4])or hashlib.sha256(policy_bytes).hexdigest()!=sys.argv[4]:raise SystemExit('root-pinned Linux policy bytes changed')
EXPECTED=json.loads(policy_bytes)
if not re.fullmatch('[a-f0-9]{40}',EXPECTED.get('source_commit','')):raise SystemExit('exact published source SHA required')
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

project=pathlib.Path(sys.argv[1]).resolve();output=pathlib.Path(sys.argv[2]).resolve();repo=project.parent
if output.is_relative_to(repo) or not output.is_dir():raise SystemExit('raw root must exist outside checkout')
bootstrap_cache=output/'bootstrap-source-cache'
if bootstrap_cache.exists()or bootstrap_cache.is_symlink():raise SystemExit('fresh nonexistent bootstrap source-cache prefix required')
sys.pycache_prefix=str(bootstrap_cache)
os.environ.update(PYTHONPYCACHEPREFIX=str(bootstrap_cache),PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
os.chdir(project);sys.path.insert(0,str(project))
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

# 2026-10-16 ET. Exact inherited root alias repair; producer stays absolute-only.
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
ambient=ambient_check(os.environ,EXPECTED['config']['path'],project)
linux_receipt=validate_linux_launch(EXPECTED,repo,output,policy_path,sys.argv[4],__file__,os.environ)
if sys.executable!=EXPECTED['linux_launch_binding']['python']:raise ValueError('selected Linux Python invocation differs')
linux_receipt['live_lane']=verified_linux_lane(EXPECTED['linux_launch_binding']['node'])
role_digest=hashlib.sha256(json.dumps(linux_receipt,sort_keys=True,separators=(',',':')).encode()).hexdigest()
os.environ['SWDB_LINUX_REVIEWED_ADMISSION']=role_digest
# The existing shell runner accepts a generic admission marker. This marker
# derives from a verified Linux role and explicitly asserts no Mac counted slot.
os.environ['SWDB_VERIFIER_RUN_TOKEN']='linux-reviewed:'+role_digest
(output/'initialized-linux-role-admission.json').write_text(json.dumps(linux_receipt,sort_keys=True,indent=2)+'\n')
source_check()
closure=consumer_closure(project,repo,EXPECTED)
(output/'initialized-source-consumer-closure-before.json').write_text(json.dumps(closure,indent=2,sort_keys=True)+'\n')
compiler_selector=normalize_compiler_selector(os.environ,EXPECTED['linux_clang_components'])
compiler_binding=compiler_preflight(os.environ,EXPECTED['linux_clang_components'])
os.environ['SWDB_CLANG']=shlex.join(EXPECTED['linux_clang_components']['command'])
verified={}
for name,want in EXPECTED['tools'].items():
 path=shutil.which(name)
 if path is None or pathlib.Path(path).resolve()!=pathlib.Path(want['path']).resolve():raise SystemExit('tool selection mismatch: '+name)
 got=pin(path)
 if got['sha256']!=want['sha256']:raise SystemExit('tool bytes changed: '+name)
 verified[name]=got
artifacts=[]
for path,sha in EXPECTED['wp_artifacts'].items():
 got=pin(path)
 if got['sha256']!=sha:raise SystemExit('WP artifact bytes changed')
 artifacts.append(got)
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
stdlib_result=stdlib_check()
stdlib=pathlib.Path(stdlib_result['path']);stdsha=stdlib_result['sha256']
config=pin(EXPECTED['config']['path'])
if config['sha256']!=EXPECTED['config']['sha256']:raise SystemExit('Why3 configuration changed')
os.environ.update(SWDB_FRAMA_C=verified['frama-c']['path'],SWDB_OCAMLFIND=verified['ocamlfind']['path'],WHY3CONFIG=config['path'],SWDB_WHY3_CONFIG=config['path'],SWDB_CBMC='none',SWDB_DX100_REGISTER_ACTUAL='0',SWDB_DX100_INITIALIZED_REGISTER_ACTUAL='1',SWDB_DX100_ALLOCATION_ACTUAL='0',SWDB_DX100_STREAM_ACTUAL='0',SWDB_DX100_SIZE_ACTUAL='0',SWDB_DX100_SELECTOR_ACTUAL='0',SWDB_DX100_SELECTOR_ACTUAL_LINEUP=json.dumps(EXPECTED['actual_initialized_lineup'],sort_keys=True,separators=(',',':')),SWDB_VERIFIER_RSS_CAP_BYTES='8589934592',PYTHONDONTWRITEBYTECODE='1')
packages={};prefix=pathlib.Path(verified['frama-c']['path']).parent.parent
surfaces={}
for name,path in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
 surfaces[name]=import_surface(path,EXPECTED['portable_import_surfaces'][name])
for name in ('frama-c.kernel','frama-c-wp.core','findlib'):
 done=subprocess.run([verified['ocamlfind']['path'],'query',name],capture_output=True,text=True,timeout=10)
 path=pathlib.Path(done.stdout.strip()).resolve()
 valid=done.returncode==0 and path.is_dir() and path.is_relative_to((prefix/'lib').resolve())
 if name=='frama-c-wp.core':valid=valid and path==pathlib.Path(next(p for p in EXPECTED['wp_artifacts'] if p.endswith('/core/wp.cmxs'))).parent.resolve()
 packages[name]={'path':str(path),'accepted':valid,'exit_code':done.returncode}
 if not valid:raise SystemExit('OCaml binding mismatch: '+name)
(output/'selected-initialized-tool-metadata.json').write_text(json.dumps({'created':'2026-10-16 ET','source_commit':EXPECTED['source_commit'],'tools':verified,'wp_artifacts':artifacts,'config':config,'stdlib':{'path':str(stdlib),'count':stdlib_result['count'],'sha256':stdsha},'packages':packages,'compiler_selector_normalization':compiler_selector,'compiler_preflight':compiler_binding,'portable_import_surfaces':surfaces,'ambient_wp_names':ambient,'actual_initialized_lineup':EXPECTED['actual_initialized_lineup'],'reporter':EXPECTED['reporter'],'source_files':EXPECTED['source_files'],'scope':'Admission metadata, not a proof result.'},indent=2,sort_keys=True)+'\n')
from swdb import c_lowering,stdlib_provenance
import pytest
selection=['tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[correct-initialized-result]','tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[wrong-crossregister-result]']
class Count:
 selected=None
 @pytest.hookimpl(trylast=True)
 def pytest_collection_finish(self,session):self.selected=[row.nodeid for row in session.items]
count=Count()
with (output/'initialized-collection.log').open('x') as log:
 with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
  result=int(pytest.main(['--collect-only','-q','-p','no:cacheprovider',*selection],plugins=[count]))
(output/'initialized-collection.json').write_text(json.dumps({'cwd':str(project),'expected':selection,'selected':count.selected,'exit_code':result},indent=2)+'\n')
if result or count.selected!=selection:raise SystemExit('exact actual register collection refused')
tool=c_lowering.locate();identity=c_lowering.identity()
if identity['naming_rules']!=EXPECTED['naming']:raise SystemExit('register naming identity changed')
# The composite includes runtime context. Exact committed module hashes above
# admit source; this project-context identity is frozen here and must equal every
# actual record's lowerer pins in the independent cold audit.
lowerer=identity.get('c_lowering')
if not isinstance(lowerer,dict) or lowerer.get('id')!='swdb-c-lowering-9' or not isinstance(lowerer.get('sha256'),str) or len(lowerer['sha256'])!=64 or any(c not in '0123456789abcdef' for c in lowerer['sha256']):raise SystemExit('missing actual composite translator identity')
project_runtime=stdlib_provenance.runtime_identity(tool)
components=compiler_components(project_runtime,EXPECTED['linux_clang_components'])
runtime={'cwd':str(project),'lowering_identity':identity,'runtime':project_runtime,'accepted_linux_components':components,'retained_basis':EXPECTED['retained_runtime_basis'],'reporter':EXPECTED['reporter'],'admission_basis':'Exact source commit and 496 selected source hashes plus complete physical/Git source-consumer membership and opaque blob equality; naming pin; selected tool/plugin/config/header runtime checks. No Mac composite used as Linux expectation.','cold_audit_requirement':'Every actual record must carry this exact lowering identity and its project-context runtime; bootstrap monorepo context stays separate.','scope':'Actual project-context provenance; not a proof result.'}
(output/'initialized-project-runtime-provenance.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n')
source_check()
closure=consumer_closure(project,repo,EXPECTED)
(output/'initialized-source-consumer-closure-after-bootstrap.json').write_text(json.dumps(closure,indent=2,sort_keys=True)+'\n')
profile=output/'initialized-profile';assert not profile.exists() and not profile.is_symlink()
os.environ.update(PROBATA_OUTPUT=str(profile),PROBATA_PYTHON=sys.executable)
command=['/bin/bash',str(project/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-initialized-u32-resume-20261016/run_initialized_register_acceptance.sh'),EXPECTED['source_commit'],'pair']
(output/'initialized-exec-argv.json').write_text(json.dumps(command,indent=2)+'\n')
os.execv(command[0],command)
