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
