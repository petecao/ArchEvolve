# 2026-10-16 ET. Separately versioned root-only controller. Old V1 is preserved.
PACKET = '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-public-memory-trace-resume-20261016'
TEST_FUNCTION = 'test_actual_public_abstract_memory_trace'
CONSUMER_ROOTS = {'apps/dx100/benchmarks/API', 'library', 'pyproject.toml', 'records',
                  'schemas', 'swdb', 'tests/conftest.py', 'tests/fixtures', 'tests/testkit', 'vocab', PACKET}
KERNEL_META_PIN_V2 = {'path': '/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c/META', 'bytes': 2318, 'sha256': '1d41605b5220bc71779ffac319ff9b06950245f5eab9f61894e865ddd9658002'}
CONTROL_NAMES_V2 = {'closed_python_surface.py', 'python_startup_roles_v2.py', 'python_role_observer_v2.py',
                    'cbmc_release_gate.py', 'trace_pytest_child_v2.py', 'python-physical-metadata-v2.json',
                    't28-linux-runtime-observer-v2-actual-20261016.json'}


def validate_policy_v2(policy):
    if not isinstance(policy, dict) or policy.get('admitted') is not True:
        raise ValueError('root fresh explicit runtime/source admission is required')
    commit = policy.get('source_commit')
    if not isinstance(commit, str) or re.fullmatch('[a-f0-9]{40}', commit) is None:
        raise ValueError('exact published source commit is unknown')
    if not isinstance(policy.get('source_root'), str) or not Path(policy['source_root']).is_absolute():
        raise ValueError('exact published checkout source root is unknown')
    if policy.get('raw_name') != 'probata-resume-20261016-t28-memory-trace-' + commit[:8] + '-v2':
        raise ValueError('fresh V2 memory-trace raw namespace differs')
    if policy.get('guard') != {'workers': 1, 'rss_cap_bytes': 8589934592, 'timeout_seconds': 1200}:
        raise ValueError('root one-worker/8GiB/1200-second guard differs')
    if set(policy.get('source_consumer_trees', {})) != CONSUMER_ROOTS:
        raise ValueError('complete source consumer root set differs')
    if any(re.fullmatch('[a-f0-9]{40}', str(row.get('oid', ''))) is None for row in policy['source_consumer_trees'].values()):
        raise ValueError('complete source consumer Git tree/blob pins are unknown')
    for group in ('source_files', 'runtime_files'):
        if not isinstance(policy.get(group), dict) or not policy[group]:
            raise ValueError('complete physical source/runtime pins required')
        for name, digest in policy[group].items():
            if (not isinstance(name, str) or re.fullmatch('[a-f0-9]{64}', str(digest)) is None or
                    group == 'runtime_files' and not Path(name).is_absolute()):
                raise ValueError('malformed physical pin')
    if set(policy.get('control_files', {})) != CONTROL_NAMES_V2:
        raise ValueError('exact V2 closed control input set required')
    if any(re.fullmatch('[a-f0-9]{64}', str(value)) is None for value in policy['control_files'].values()):
        raise ValueError('exact physical control hashes required')
    if set(policy.get('portable_import_surfaces', {})) != {'why3_stdlib', 'wp_why3_support', 'why3_drivers'}:
        raise ValueError('complete inherited typechecker import surfaces required')
    if set(policy.get('ocaml_packages', {})) != {'frama-c.kernel', 'frama-c-wp.core', 'findlib'}:
        raise ValueError('complete inherited OCaml package bindings required')
    components = policy.get('linux_clang_components', {})
    if set(components) != {'command', 'command_executable', 'driver', 'headers', 'parser'}:
        raise ValueError('complete selected compiler identity required')
    command = components['command']
    if (not isinstance(command, list) or len(command) != 1 or not isinstance(command[0], str) or
            not Path(command[0]).is_absolute() or command[0] != components['command_executable']['path']):
        raise ValueError('one exact absolute pinned compiler wrapper required')
    tools = policy.get('tools', {})
    if not {'cbmc', 'frama-c', 'opam', 'python', 'ocamlfind', 'ocamlopt', 'why3', 'gcc', 'z3', 'cvc5', 'alt-ergo'} <= tools.keys():
        raise ValueError('complete selected tool pins required')
    if (policy.get('accepted_cbmc_release_family') != '6.11' or tools['cbmc'].get('version') != '6.11.0' or
            tools['frama-c'].get('version') != '33.0'):
        raise ValueError('root-observed exact CBMC6.11.0/Frama33 required')
    if policy.get('cbmc_version_output') != {'stdout': '6.11.0 (cbmc-6.11.0)\n', 'stderr': ''}:
        raise ValueError('exact raw root-observed CBMC stdout/stderr required')
    for name, tool in tools.items():
        if not Path(tool.get('path', '')).is_absolute() or re.fullmatch('[a-f0-9]{64}', str(tool.get('sha256', ''))) is None:
            raise ValueError('absolute physical tool pin required: ' + name)
    if policy.get('junit') != {'tests': 25, 'errors': 0, 'failures': 0, 'skipped': 0}:
        raise ValueError('exact25/no-skip JUnit contract differs')
    prefix = PACKET + '/test_public_actual.py::' + TEST_FUNCTION + '['
    nodes = policy.get('selection')
    if (not isinstance(nodes, list) or len(nodes) != 25 or len(set(nodes)) != 25 or
            any(not isinstance(node, str) or not node.startswith(prefix) or not node.endswith(']') for node in nodes)):
        raise ValueError('exact25 fixed test nodes required')
    return policy


def check_staged_controllers_v2(raw, expected, *, entry_file, policy_file, policy_sha256):
    control = raw / 'control'
    entry, policy = Path(entry_file), Path(policy_file)
    if entry.parent != control or policy.parent != control or entry.name == policy.name:
        raise ValueError('exact distinct staged entry/policy names required')
    wanted = CONTROL_NAMES_V2 | {entry.name, policy.name}
    if control.is_symlink() or not control.is_dir() or control.resolve() != control:
        raise ValueError('canonical physical staged controller directory required')
    if {path.name for path in control.iterdir()} != wanted:
        raise ValueError('complete staged control basename membership differs')
    for path in control.iterdir():
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('staged control symlink/special/directory refused')
    if (pin(entry)['sha256'] != expected['linux_launch_binding']['entry_sha256'] or
            pin(policy)['sha256'] != policy_sha256):
        raise ValueError('staged entry/policy bytes changed')
    return {'entry': pin(entry), 'policy': pin(policy), 'basenames': sorted(wanted)}


def load_controls_v2(raw, expected):
    import types
    control = raw / 'control'
    if control.is_symlink() or control.resolve() != control:
        raise ValueError('physical source-disjoint control directory required')
    contents = {}
    for name in sorted(CONTROL_NAMES_V2):
        path = control / name
        if path.is_symlink() or not path.is_file() or pin(path)['sha256'] != expected['control_files'][name]:
            raise ValueError('root-pinned closed control bytes differ: ' + name)
        contents[name] = path.read_bytes()
        if hashlib.sha256(contents[name]).hexdigest() != expected['control_files'][name]:
            raise ValueError('closed control bytes changed during read')
    if sum(map(len, contents.values())) > 1048576:
        raise ValueError('closed control data exceeds reviewed1MiB bound')
    modules = {}
    for name in ('closed_python_surface.py', 'python_startup_roles_v2.py', 'cbmc_release_gate.py'):
        module = types.ModuleType('pinned_control_' + name[:-3])
        exec(compile(contents[name], str(control / name), 'exec'), module.__dict__)
        modules[name] = module
    return contents, modules


def ocaml_membership_v2(expected):
    result = {}
    for name, directory in expected['ocaml_packages'].items():
        root = Path(directory)
        prefix = str(root) + '/'
        files = [{'relative': path[len(prefix):], 'sha256': digest}
                 for path, digest in sorted(expected['runtime_files'].items()) if path.startswith(prefix)]
        files.sort(key=lambda row: Path(row['relative']).parts)
        if not files:
            raise ValueError('complete pinned OCaml package membership is empty: ' + name)
        # Reuse the unchanged no-link import_surface contract.
        result[name] = import_surface(str(root), files)
    return result


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


def main_v2(argv):
    if not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError('isolated nonoptimized Python -I -B entry required')
    if len(argv) != 5:
        raise ValueError('usage: entry PROJECT RAW_ROOT POLICY POLICY_SHA256')
    project, raw, policy_path = [Path(value).resolve() for value in argv[1:4]]
    repository = project.parent
    policy_bytes = policy_path.read_bytes()
    if re.fullmatch('[a-f0-9]{64}', argv[4]) is None or hashlib.sha256(policy_bytes).hexdigest() != argv[4]:
        raise ValueError('root-pinned policy bytes differ')
    expected = validate_policy_v2(json.loads(policy_bytes))
    if project != Path(expected['source_root']).resolve():
        raise ValueError('selected source root differs')
    if (not raw.is_dir() or raw.is_symlink() or raw.name != expected['raw_name'] or
            raw.is_relative_to(repository) or repository.is_relative_to(raw)):
        raise ValueError('fresh source-disjoint physical raw root required')
    profile, cache = raw / 'memory-trace-profile', raw / 'bootstrap-source-cache'
    if any(path.exists() or path.is_symlink() for path in (profile, cache)):
        raise ValueError('fresh nonexistent profile/cache required')
    ambient_check(os.environ, expected['config']['path'], project)
    launch = validate_linux_launch(expected, repository, raw, policy_path, argv[4], __file__, os.environ)
    if sys.executable != expected['linux_launch_binding']['python']:
        raise ValueError('selected Python invocation differs')
    launch['live_lane'] = verified_linux_lane(expected['linux_launch_binding']['node'])
    role_digest = hashlib.sha256(json.dumps(launch, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    os.environ.update(SWDB_LINUX_REVIEWED_ADMISSION=role_digest, SWDB_VERIFIER_RUN_TOKEN='linux-reviewed:' + role_digest)
    (raw / 'memory-trace-linux-role-admission.json').write_text(json.dumps(launch, indent=2, sort_keys=True) + '\n')
    os.chdir(project)

    def source_check_v2():
        git = ['/usr/bin/git', '--no-replace-objects', '-C', str(repository)]
        head = subprocess.check_output([*git, 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
        dirty = subprocess.check_output([*git, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=30)
        if head != expected['source_commit'] or dirty.strip():
            raise ValueError('selected source is not clean exact published commit')
        for name, digest in expected['source_files'].items():
            if pin(project / name)['sha256'] != digest:
                raise ValueError('source bytes changed: ' + name)
        return consumer_closure(project, repository, expected)

    before_source = source_check_v2()
    staged_before = check_staged_controllers_v2(raw, expected, entry_file=Path(__file__),
                                               policy_file=policy_path, policy_sha256=argv[4])
    contents, modules = load_controls_v2(raw, expected)
    closed, roles, cbmc = [modules[name] for name in ('closed_python_surface.py', 'python_startup_roles_v2.py', 'cbmc_release_gate.py')]
    physical = json.loads(contents['python-physical-metadata-v2.json'])
    plan = expected['python_startup_roles_v2']
    physical_before = closed.verify_python_metadata(physical)
    plan_receipt = roles.validate_role_plan_v2(plan, metadata=physical, source_project=project,
        root_observer_bytes=contents['t28-linux-runtime-observer-v2-actual-20261016.json'], closed=closed)
    environment = roles.child_environment_v2(os.environ, project=project, raw=raw, cache=cache)
    environment.update(TMPDIR=str(profile / 'tmp'), XDG_CACHE_HOME=str(profile / 'cache'))
    observer_source = contents['python_role_observer_v2.py'].decode()
    observer_function = observer_source.split("if __name__ == '__main__':", 1)[0]
    python = expected['tools']['python']['path']
    if (python != plan['executable'] or sys.executable != python or
            expected['linux_launch_binding']['python'] != python or
            expected['tools']['python']['sha256'] != physical['interpreter']['target_pin']['sha256']):
        raise ValueError('role executable and tool pin differ from closed interpreter')
    # No selected runtime child executes before these physical bytes are checked.
    for name, digest in expected['runtime_files'].items():
        if pin(name)['sha256'] != digest:
            raise ValueError('physical runtime component differs before startup probe: ' + name)
    for name, tool in expected['tools'].items():
        if pin(tool['path'])['sha256'] != tool['sha256']:
            raise ValueError('physical selected tool differs before startup probe: ' + name)
    for role in ('entry-isolated', 'pytest-child'):
        request = roles.role_request_v2(plan, role=role, environment=environment, cache=cache)
        flags = ['-I', '-B', '-X', 'pycache_prefix=' + str(cache)] if role == 'entry-isolated' else ['-B']
        result = subprocess.run([python, *flags, '-c', observer_source, json.dumps(request)],
                                env=environment, capture_output=True, text=True, timeout=30)
        (raw / (role + '-startup-stdout.txt')).write_text(result.stdout)
        (raw / (role + '-startup-stderr.txt')).write_text(result.stderr)
        if result.returncode:
            raise ValueError('actual guarded startup observer refused: ' + role)
        observation = json.loads(result.stdout)
        receipt = roles.check_role_observation_v2(request, observation)
        (raw / (role + '-startup.json')).write_text(json.dumps({'observation': observation, 'receipt': receipt,
            'plan_provenance': plan_receipt}, indent=2, sort_keys=True) + '\n')
    if closed.verify_python_metadata(physical) != physical_before:
        raise ValueError('physical Python changed during role probes')
    compiler_selector = normalize_compiler_selector(environment, expected['linux_clang_components'])
    compiler = compiler_preflight(environment, expected['linux_clang_components'])

    def runtime_check_v2():
        for name, digest in expected['runtime_files'].items():
            if pin(name)['sha256'] != digest:
                raise ValueError('physical runtime component differs: ' + name)
        for name, wanted in expected['tools'].items():
            if pin(wanted['path'])['sha256'] != wanted['sha256']:
                raise ValueError('physical tool differs: ' + name)
            if name not in {'cbmc', 'python'}:
                selected = shutil.which(name, path=environment.get('PATH'))
                if selected is None or Path(selected).resolve() != Path(wanted['path']).resolve():
                    raise ValueError('selected inherited tool differs: ' + name)
        if pin(expected['config']['path'])['sha256'] != expected['config']['sha256']:
            raise ValueError('Why3 configuration differs')
        for name, digest in expected['wp_artifacts'].items():
            if pin(name)['sha256'] != digest:
                raise ValueError('typechecker artifact differs')
        for row in expected['portable_import_surfaces'].values():
            import_surface(row['path'], row['files'])
        kernel_meta = str(Path(expected['ocaml_packages']['frama-c.kernel']).parent / 'META')
        if (kernel_meta != KERNEL_META_PIN_V2['path'] or
                expected['runtime_files'].get(kernel_meta) != KERNEL_META_PIN_V2['sha256']):
            raise ValueError('Frama kernel package selection META lacks the exact root passive pin')
        closed._file_pin(KERNEL_META_PIN_V2)
        parser = expected['linux_parser_physical']
        if (expected['runtime_files'].get(parser['path']) != parser['sha256'] or
                expected['linux_clang_components']['parser']['sha256'] != parser['sha256']):
            raise ValueError('physical parser runtime/component binding differs')
        closed._file_pin(parser)
        headers = header_surface_check_v4(expected['linux_header_surfaces'], expected['linux_clang_components']['headers'], closed)
        return {'ocaml': ocaml_membership_v2(expected), 'headers': headers, 'parser': parser}

    runtime_before = runtime_check_v2()
    profile.mkdir()
    for name in ('tmp', 'cache'):
        (profile / name).mkdir()
    try:
        prefix = Path(expected['tools']['frama-c']['path']).parent.parent
        for name, wanted in expected['ocaml_packages'].items():
            result = subprocess.run([expected['tools']['ocamlfind']['path'], 'query', name], capture_output=True, text=True, env=environment, timeout=10)
            found = Path(result.stdout.strip()).resolve()
            if result.returncode or found != Path(wanted).resolve() or not found.is_dir() or not found.is_relative_to((prefix / 'lib').resolve()):
                raise ValueError('actual OCaml package binding differs: ' + name)
            if name == 'frama-c-wp.core' and found != Path(next(path for path in expected['wp_artifacts'] if path.endswith('/core/wp.cmxs'))).parent.resolve():
                raise ValueError('actual WP package and pinned plugin differ')
        result = subprocess.run([expected['tools']['cbmc']['path'], '--version'], env=environment, capture_output=True, text=True, timeout=30)
        version_receipt = cbmc.check_cbmc_version(expected, result.returncode, result.stdout, result.stderr)
        if {'stdout': result.stdout, 'stderr': result.stderr} != expected['cbmc_version_output']:
            raise ValueError('CBMC raw version output differs')
        result = subprocess.run([expected['tools']['frama-c']['path'], '-version'], env=environment, capture_output=True, text=True, timeout=30)
        if result.returncode or re.search(r'(?<![0-9.])33\.0(?![0-9.])', result.stdout + result.stderr) is None:
            raise ValueError('Frama33 actual version differs')
        environment.update(SWDB_CBMC=expected['tools']['cbmc']['path'], SWDB_FRAMA_C=expected['tools']['frama-c']['path'],
            SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'], WHY3CONFIG=expected['config']['path'],
            SWDB_WHY3_CONFIG=expected['config']['path'], SWDB_T28_TRACE_ACTUAL='1')
        actual_environment = {name: environment[name] for name in ('SWDB_CLANG', 'SWDB_CBMC', 'SWDB_FRAMA_C',
            'SWDB_OCAMLFIND', 'WHY3CONFIG', 'SWDB_WHY3_CONFIG', 'SWDB_VERIFIER_RSS_CAP_BYTES', 'SWDB_VERIFIER_LOCK')}
        environment['SWDB_T28_TRACE_ACTUAL_ENVIRONMENT'] = json.dumps(actual_environment, sort_keys=True)
        request = roles.role_request_v2(plan, role='pytest-child', environment=environment, cache=cache)
        child_source = 'import json, sys\n' + observer_function + '\n' + contents['trace_pytest_child_v2.py'].decode() + '\nraise SystemExit(trace_child_main_v2(json.loads(sys.argv[1])))\n'
        child_arguments = {'startup_request': request, 'project': str(project), 'profile': str(profile),
                           'policy': str(policy_path), 'policy_sha256': argv[4]}
        source_check_v2()
        (profile / 'launch-provenance.json').write_text(json.dumps({'compiler_selector_normalization': compiler_selector,
            'compiler_preflight': compiler, 'cbmc_version': version_receipt, 'plan': plan_receipt}, indent=2, sort_keys=True) + '\n')
        with (profile / 'child-stdout.txt').open('x') as stdout, (profile / 'child-stderr.txt').open('x') as stderr:
            result = subprocess.run([python, '-B', '-c', child_source, json.dumps(child_arguments)], env=environment,
                                    stdout=stdout, stderr=stderr)
        census = junit_census(profile / 'junit.xml', expected['selection'], expected['junit_classname'])
        (profile / 'junit-census.json').write_text(json.dumps(census, indent=2, sort_keys=True) + '\n')
        return result.returncode
    finally:
        after_source = source_check_v2()
        if runtime_check_v2() != runtime_before or closed.verify_python_metadata(physical) != physical_before:
            raise ValueError('closed runtime/Python bytes changed during suite')
        load_controls_v2(raw, expected)
        if check_staged_controllers_v2(raw, expected, entry_file=Path(__file__),
                policy_file=policy_path, policy_sha256=argv[4]) != staged_before:
            raise ValueError('staged controller identity/membership changed during suite')
        (raw / 'memory-trace-final-physical-check.json').write_text(json.dumps({'source_before': before_source,
            'source_after': after_source, 'python_physical': physical_before, 'unchanged': True}, indent=2, sort_keys=True) + '\n')
        if cache.exists() or cache.is_symlink():
            raise ValueError('unexpected bytecode cache output')


if __name__ == '__main__':
    raise SystemExit(main_v2(sys.argv))
