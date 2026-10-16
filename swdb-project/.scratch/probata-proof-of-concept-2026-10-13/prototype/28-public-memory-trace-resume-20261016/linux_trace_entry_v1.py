"""2026-10-16 ET. INERT root-only Linux public abstract-memory trace entry.
No body, hardware or whole ticket28 acceptance follows from this execution packet.
"""
import contextlib, hashlib, json, os, pathlib, re, shlex, shutil, stat, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

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

def compiler_preflight(env,wanted):
 command=wanted['command']
 if not isinstance(command,list) or len(command)!=1 or not isinstance(command[0],str) or not Path(command[0]).is_absolute():
  raise ValueError('unreviewed compiler command shape')
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

# 2026-10-16 ET. Inert root-only execution body; no bootstrap at import.
PACKET = '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-public-memory-trace-resume-20261016'
TEST_FUNCTION = 'test_actual_public_abstract_memory_trace'
CONSUMER_ROOTS = {'apps/dx100/benchmarks/API', 'library', 'pyproject.toml', 'records',
                  'schemas', 'swdb', 'tests/conftest.py', 'tests/fixtures', 'tests/testkit', 'vocab', PACKET}


def hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_policy(policy):
    if not isinstance(policy, dict) or policy.get('admitted') is not True:
        raise ValueError('root fresh explicit runtime/source admission is required')
    commit = policy.get('source_commit')
    if not isinstance(commit, str) or re.fullmatch('[a-f0-9]{40}', commit) is None:
        raise ValueError('next exact published source commit is unknown')
    if not isinstance(policy.get('source_root'), str) or not Path(policy['source_root']).is_absolute():
        raise ValueError('exact published checkout source root is unknown')
    if policy.get('raw_name') != 'probata-resume-20261016-t28-memory-trace-' + commit[:8] + '-v1':
        raise ValueError('fresh memory-trace raw namespace differs')
    if policy.get('guard') != {'workers': 1, 'rss_cap_bytes': 8589934592, 'timeout_seconds': 1200}:
        raise ValueError('root whole-tree one-worker/8GiB/1200-second guard differs')
    if set(policy.get('source_consumer_trees', {})) != CONSUMER_ROOTS:
        raise ValueError('complete current source consumer root set differs')
    if any(re.fullmatch('[a-f0-9]{40}', str(row.get('oid', ''))) is None for row in policy['source_consumer_trees'].values()):
        raise ValueError('complete source consumer Git tree/blob pins are unknown')
    if not policy.get('source_files') or not policy.get('runtime_files'):
        raise ValueError('complete root physical source/runtime pins are required')
    if set(policy.get('python_import_surfaces', {})) != {'stdlib', 'site_packages'}:
        raise ValueError('complete Python stdlib/site-packages import surfaces required')
    if set(policy.get('portable_import_surfaces', {})) != {'why3_stdlib', 'wp_why3_support', 'why3_drivers'}:
        raise ValueError('complete inherited typechecker import surfaces required')
    if set(policy.get('ocaml_packages', {})) != {'frama-c.kernel', 'frama-c-wp.core', 'findlib'}:
        raise ValueError('complete inherited OCaml package bindings required')
    if set(policy.get('linux_clang_components', {})) != {'command', 'command_executable', 'driver', 'headers', 'parser'}:
        raise ValueError('complete selected Linux Clang wrapper/driver/parser/header identity required')
    command = policy['linux_clang_components']['command']
    if not isinstance(command, list) or len(command) != 1 or not isinstance(command[0], str) or not Path(command[0]).is_absolute():
        raise ValueError('Clang must be one absolute pinned wrapper command')
    if command[0] != policy['linux_clang_components']['command_executable']['path']:
        raise ValueError('absolute Clang wrapper command and component path differ')
    tools = policy.get('tools', {})
    if not {'cbmc', 'frama-c', 'opam', 'python', 'ocamlfind', 'ocamlopt', 'why3', 'gcc', 'z3', 'cvc5', 'alt-ergo'} <= tools.keys() or tools['cbmc'].get('version') != '6.11':
        raise ValueError('fresh root-pinned CBMC6.11 and complete tools are unknown')
    if tools['frama-c'].get('version') != '33.0':
        raise ValueError('fresh root-pinned Frama33 typechecker required')
    if policy.get('junit') != {'tests': 25, 'errors': 0, 'failures': 0, 'skipped': 0}:
        raise ValueError('exact25/no-skip JUnit contract differs')
    selection = policy.get('selection')
    prefix = PACKET + '/test_public_actual.py::' + TEST_FUNCTION + '['
    if (not isinstance(selection, list) or len(selection) != 25 or len(set(selection)) != 25 or
            any(not isinstance(node, str) or not node.startswith(prefix) or not node.endswith(']') for node in selection)):
        raise ValueError('exact25 fixed test nodes required')
    for group in ('source_files', 'runtime_files'):
        for name, digest in policy[group].items():
            if (not isinstance(name, str) or not isinstance(digest, str) or
                    re.fullmatch('[a-f0-9]{64}', digest) is None or
                    group == 'runtime_files' and not Path(name).is_absolute()):
                raise ValueError('malformed exact physical ' + group + ' pin')
    for name, tool in tools.items():
        if (not Path(tool.get('path', '')).is_absolute() or
                re.fullmatch('[a-f0-9]{64}', str(tool.get('sha256', ''))) is None):
            raise ValueError('malformed absolute physical tool pin: ' + name)
    return policy


def junit_census(path, expected_nodes, expected_classname):
    root = ET.parse(path).getroot()
    suites, cases = list(root.iter('testsuite')), list(root.iter('testcase'))
    if (root.tag != 'testsuites' or len(list(root.iter('testsuites'))) != 1 or len(suites) != 1 or
            suites[0].get('tests') != '25' or len(cases) != 25 or
            any(suites[0].get(key) != '0' for key in ('errors', 'failures', 'skipped')) or
            any(next(root.iter(key), None) is not None for key in ('error', 'failure', 'skipped'))):
        raise ValueError('JUnit is not exactly25 executed/no-error/no-failure/no-skip')
    wanted = {node.split('::')[-1] for node in expected_nodes}
    if ({case.get('name') for case in cases} != wanted or
            any(case not in list(suites[0]) or case.get('classname') != expected_classname for case in cases)):
        raise ValueError('JUnit exact trace names/class membership differ')
    return {'accepted': True, 'cases': 25, 'skipped': 0,
            'scope': 'workflow census only; every abstract proof/refutation and cold audit remain separate'}


def main(argv):
    if (not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode):
        raise ValueError('root actual profile requires isolated nonoptimized Python -I -B')
    if len(argv) != 5:
        raise ValueError('usage: entry PROJECT RAW_ROOT POLICY POLICY_SHA256')
    project, raw, policy_path = Path(argv[1]).resolve(), Path(argv[2]).resolve(), Path(argv[3]).resolve()
    repository = project.parent
    policy_bytes = policy_path.read_bytes()
    if re.fullmatch('[a-f0-9]{64}', argv[4]) is None or hashlib.sha256(policy_bytes).hexdigest() != argv[4]:
        raise ValueError('root-pinned policy file bytes changed')
    expected = validate_policy(json.loads(policy_bytes))
    if project != Path(expected['source_root']).resolve():
        raise ValueError('exact selected checkout source root differs')
    if (not raw.is_dir() or raw.is_symlink() or raw.name != expected['raw_name'] or
            raw.is_relative_to(repository) or repository.is_relative_to(raw)):
        raise ValueError('fresh source-disjoint external raw root is required')
    profile = raw / 'memory-trace-profile'
    if profile.exists() or profile.is_symlink():
        raise ValueError('fresh nonexistent memory trace profile required')
    cache = raw / 'bootstrap-source-cache'
    if cache.exists() or cache.is_symlink():
        raise ValueError('fresh nonexistent bootstrap cache prefix required')
    ambient_check(os.environ, expected['config']['path'], project)
    launch = validate_linux_launch(expected, repository, raw, policy_path, argv[4], __file__, os.environ)
    if sys.executable != expected['linux_launch_binding']['python']:
        raise ValueError('selected Python invocation differs')
    launch['live_lane'] = verified_linux_lane(expected['linux_launch_binding']['node'])
    role = hash_json(launch)
    os.environ['SWDB_LINUX_REVIEWED_ADMISSION'] = role
    os.environ['SWDB_VERIFIER_RUN_TOKEN'] = 'linux-reviewed:' + role
    (raw / 'memory-trace-linux-role-admission.json').write_text(json.dumps(launch, indent=2, sort_keys=True) + '\n')
    sys.pycache_prefix = str(cache)
    os.environ.update(PYTHONPYCACHEPREFIX=str(cache), PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    os.chdir(project)

    def source_check():
        git = ['/usr/bin/git', '--no-replace-objects', '-C', str(repository)]
        head = subprocess.check_output([*git, 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
        dirty = subprocess.check_output([*git, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=30)
        if head != expected['source_commit'] or dirty.strip():
            raise ValueError('selected source is not exact clean published commit')
        for name, digest in expected['source_files'].items():
            if pin(project / name)['sha256'] != digest:
                raise ValueError('selected source bytes changed: ' + name)

    source_check()
    closure = consumer_closure(project, repository, expected)
    (raw / 'memory-trace-source-consumers-before.json').write_text(json.dumps(closure, indent=2, sort_keys=True) + '\n')
    compiler_selector = normalize_compiler_selector(os.environ, expected['linux_clang_components'])
    compiler = compiler_preflight(os.environ, expected['linux_clang_components'])
    for name, digest in expected['runtime_files'].items():
        if pin(name)['sha256'] != digest:
            raise ValueError('fresh physical runtime component differs: ' + name)
    for name, wanted in expected['tools'].items():
        if pin(wanted['path'])['sha256'] != wanted['sha256']:
            raise ValueError('fresh physical tool differs: ' + name)
        if name not in {'cbmc', 'python'}:
            selected = shutil.which(name)
            if selected is None or Path(selected).resolve() != Path(wanted['path']).resolve():
                raise ValueError('selected inherited tool path differs: ' + name)
    if pin(sys.executable)['sha256'] != expected['tools']['python']['sha256']:
        raise ValueError('Python executable bytes differ')
    surfaces = {name: import_surface(row['path'], row['files'])
                for name, row in expected['python_import_surfaces'].items()}
    # The WP contracts are typechecked, never used as proof axioms by this CBMC
    # profile. Its existing Frama/OCaml/Why3 runtime contract remains exact.
    if pin(expected['config']['path'])['sha256'] != expected['config']['sha256']:
        raise ValueError('root-pinned Why3 configuration differs')
    for name, digest in expected['wp_artifacts'].items():
        if pin(name)['sha256'] != digest:
            raise ValueError('typechecker plugin artifact differs')
    for name, row in expected['portable_import_surfaces'].items():
        import_surface(row['path'], row['files'])
    prefix = Path(expected['tools']['frama-c']['path']).parent.parent
    for name, wanted in expected['ocaml_packages'].items():
        result = subprocess.run([expected['tools']['ocamlfind']['path'], 'query', name], capture_output=True, text=True, timeout=10)
        found = Path(result.stdout.strip()).resolve()
        if result.returncode or found != Path(wanted).resolve() or not found.is_dir() or not found.is_relative_to((prefix / 'lib').resolve()):
            raise ValueError('inherited actual OCaml package binding differs: ' + name)
        if name == 'frama-c-wp.core' and found != Path(next(path for path in expected['wp_artifacts'] if path.endswith('/core/wp.cmxs'))).parent.resolve():
            raise ValueError('WP package and pinned actual plugin differ')
    for tool, flag, version in [('cbmc', '--version', '6.11'), ('frama-c', '-version', '33.0')]:
        result = subprocess.run([expected['tools'][tool]['path'], flag], capture_output=True, text=True, timeout=30)
        if result.returncode or re.search(r'(?<![0-9.])' + re.escape(version) + r'(?![0-9.])', result.stdout + result.stderr) is None:
            raise ValueError('fresh selected runtime version differs: ' + tool)
    os.environ.update(SWDB_CLANG=shlex.join(expected['linux_clang_components']['command']),
                      SWDB_CBMC=expected['tools']['cbmc']['path'], SWDB_FRAMA_C=expected['tools']['frama-c']['path'],
                      SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'],
                      WHY3CONFIG=expected['config']['path'], SWDB_WHY3_CONFIG=expected['config']['path'],
                      SWDB_VERIFIER_RSS_CAP_BYTES='8589934592')
    profile.mkdir()
    for name in ('tmp', 'cache'):
        (profile / name).mkdir()
    os.environ.update(TMPDIR=str(profile / 'tmp'), XDG_CACHE_HOME=str(profile / 'cache'),
                      SWDB_VERIFIER_LOCK=str(raw / 'verifier.lock'), SWDB_T28_TRACE_ACTUAL='1')
    actual_environment = {name: os.environ[name] for name in ('SWDB_CLANG', 'SWDB_CBMC', 'SWDB_FRAMA_C',
                          'SWDB_OCAMLFIND', 'WHY3CONFIG', 'SWDB_WHY3_CONFIG', 'SWDB_VERIFIER_RSS_CAP_BYTES', 'SWDB_VERIFIER_LOCK')}
    os.environ['SWDB_T28_TRACE_ACTUAL_ENVIRONMENT'] = json.dumps(actual_environment, sort_keys=True)
    sys.path[:0] = [str(project), str(project / 'tests'), str(project / PACKET)]
    from swdb import c_lowering, stdlib_provenance, proof_setup
    import pytest
    tool = c_lowering.locate()
    runtime = stdlib_provenance.runtime_identity(tool)
    compiler_components(runtime, expected['linux_clang_components'])
    identity = c_lowering.identity()
    if identity['naming_rules'] != expected['naming']:
        raise ValueError('selected source-context naming identity differs')
    metadata = {'date': '2026-10-16 ET', 'source_commit': expected['source_commit'],
                'lowering': identity, 'runtime': runtime, 'proof_setup': proof_setup.identity(),
                'compiler_selector_normalization': compiler_selector,
                'compiler_preflight': compiler, 'python_import_surfaces': surfaces,
                'runtime_files': expected['runtime_files'], 'tools': expected['tools'],
                'scope': 'current Linux source/runtime identity; no proof or hardware acceptance'}
    (profile / 'runtime-provenance.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    packet_policy = json.loads((project / PACKET / 'actual-policy.json').read_bytes())
    nodes = [PACKET + '/test_public_actual.py::' + TEST_FUNCTION + '[' + row['name'] + ']' for row in packet_policy['cases']]
    if nodes != expected['selection']:
        raise ValueError('exact source-bound25-node selection differs')

    class Count:
        selected = None
        @pytest.hookimpl(trylast=True)
        def pytest_collection_finish(self, session):
            self.selected = [row.nodeid for row in session.items]

    count = Count()
    with (profile / 'collection.log').open('x') as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            result = int(pytest.main(['--collect-only', '-q', '--rootdir', str(project), '-p', 'no:cacheprovider', *nodes], plugins=[count]))
    (profile / 'collection.json').write_text(json.dumps({'exit_code': result, 'selected': count.selected, 'expected': nodes}, indent=2) + '\n')
    if result or count.selected != nodes:
        raise ValueError('public trace collection is not exact25')
    source_check()
    consumer_closure(project, repository, expected)
    arguments = ['-q', '--tb=short', '--rootdir', str(project), '-p', 'no:cacheprovider',
                 '--basetemp', str(profile / 'pytest'), '--junitxml', str(profile / 'junit.xml'), *nodes]
    (profile / 'pytest-arguments.json').write_text(json.dumps(arguments, indent=2) + '\n')
    with (profile / 'pytest.log').open('x') as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            result = int(pytest.main(arguments))
    (profile / 'exit-code.txt').write_text(str(result) + '\n')
    census = junit_census(profile / 'junit.xml', nodes, expected['junit_classname'])
    (profile / 'junit-census.json').write_text(json.dumps(census, indent=2, sort_keys=True) + '\n')
    source_check()
    closure = consumer_closure(project, repository, expected)
    (raw / 'memory-trace-source-consumers-after.json').write_text(json.dumps(closure, indent=2, sort_keys=True) + '\n')
    for name, digest in expected['runtime_files'].items():
        if pin(name)['sha256'] != digest:
            raise ValueError('physical runtime component changed during suite: ' + name)
    for name, wanted in expected['tools'].items():
        if pin(wanted['path'])['sha256'] != wanted['sha256']:
            raise ValueError('physical tool changed during suite: ' + name)
    for name, row in expected['python_import_surfaces'].items():
        if import_surface(row['path'], row['files']) != surfaces[name]:
            raise ValueError('Python import surface changed during suite: ' + name)
    for name, row in expected['portable_import_surfaces'].items():
        import_surface(row['path'], row['files'])
    if pin(expected['config']['path'])['sha256'] != expected['config']['sha256']:
        raise ValueError('Why3 configuration changed during suite')
    for name, digest in expected['wp_artifacts'].items():
        if pin(name)['sha256'] != digest:
            raise ValueError('typechecker plugin artifact changed during suite')
    if cache.exists() or cache.is_symlink():
        raise ValueError('unexpected bytecode cache output')
    return result


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
