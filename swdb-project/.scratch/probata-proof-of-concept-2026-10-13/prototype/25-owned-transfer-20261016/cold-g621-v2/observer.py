"""2026-10-16 ET. INERT G621 ownership10 passive cold observation.

Root must review and admit this exact source before execution. No project import,
compiler, native metadata helper, verifier, solver, version query or socket call.
Raw proof content stays on mbit10. The stdout object contains only compact pins,
symbol/declaration attribution and semantic decisions. Unknown lowering refuses
scientific acceptance; a successful metadata census alone is never a proof.
"""
import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-d7f685c6-owned-transfer10-public-v2')
PROFILE = RAW / 'owned-transfer10-public-v2-profile'
SOURCE = Path('/data1/yanruj/probata-resume-20261016-d7f685c6')
COMMIT = 'd7f685c6fdbd7ff776eb1eaccc40099a2c48dc08'
ENTRY_SHA = '663fcd74640b4d04f7d3ae38b5587924fc10501cd82831a014f18e05eaf31c94'
EXPECTED_SHA = 'ff336dc468cb526061000c41125dabb1a285b5399f58ac27a3ca72f7a6ca46cf'
COMMAND_SHA = '12bcda644bfb6fde4877b6d5d82a2648c77e1b7b021ab154a4a198cae27bb0c1'
MAX_FILE = 128 * 1024**2
MAX_JSON = 2 * 1024**2
MAX_OUTPUT = 2 * 1024**2
CHECKS = 0
GIT_ACTIVE = False
STATE = {'classification': 'REFUSED_OWNERSHIP10_PASSIVE_COLD', 'scientific_acceptance': False}


def need(value, label):
    global CHECKS
    if not value:
        raise ValueError(label)
    CHECKS += 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return sha(compact(value))


def identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def physical(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute canonical input path')
    for parent in reversed(path.parents):
        need(stat.S_ISDIR(parent.lstat().st_mode), 'physical input ancestor ' + str(parent))
    return path


def read_bytes(path, cap=MAX_JSON):
    path = physical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'bounded regular input ' + str(path))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(descriptor)) == identity(before), 'opened original physical input')
        chunks = []
        remaining = cap + 1
        while remaining:
            block = os.read(descriptor, min(1048576, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        value = b''.join(chunks)
        need(len(value) == before.st_size and len(value) <= cap, 'bounded complete input read')
        need(identity(before) == identity(os.fstat(descriptor)) == identity(path.lstat()), 'stable input bytes')
        return value
    finally:
        os.close(descriptor)


def pin(path, cap=None):
    path = physical(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and (cap is None or before.st_size <= cap), 'physical bounded hash input')
    h = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(descriptor)) == identity(before), 'physical hash descriptor')
        count = 0
        while True:
            block = os.read(descriptor, 1048576)
            if not block:
                break
            h.update(block)
            count += len(block)
        need(count == before.st_size and identity(before) == identity(os.fstat(descriptor)) == identity(path.lstat()),
             'stable complete hash input')
        return {'path': str(path), 'bytes': count, 'sha256': h.hexdigest()}
    finally:
        os.close(descriptor)


def read(path):
    def pairs(items):
        result = {}
        for name, value in items:
            need(name not in result, 'unique JSON field')
            result[name] = value
        return result
    return json.loads(read_bytes(path), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('finite JSON required')))


def walk(root, *, hash_files=True, byte_cap=2 * 1024**3, entry_cap=10000):
    root = physical(root)
    need(stat.S_ISDIR(root.lstat().st_mode), 'physical walk root')
    rows = []
    pending = [root]
    total = 0
    while pending:
        directory = pending.pop()
        before = directory.lstat()
        need(stat.S_ISDIR(before.st_mode), 'physical traversed directory')
        with os.scandir(directory) as stream:
            children = sorted(stream, key=lambda entry: entry.name)
        need(len(rows) + len(children) <= entry_cap, 'finite directory census')
        for entry in children:
            path = directory / entry.name
            st = path.lstat()
            relative = str(path.relative_to(root))
            if stat.S_ISDIR(st.st_mode):
                pending.append(path)
                rows.append({'relative': relative, 'kind': 'directory'})
            else:
                need(stat.S_ISREG(st.st_mode), 'no raw symlink/socket/FIFO/device')
                total += st.st_size
                need(total <= byte_cap, 'bounded aggregate physical bytes')
                row = {'relative': relative, 'kind': 'regular', 'bytes': st.st_size}
                if hash_files:
                    row['sha256'] = pin(path)['sha256']
                rows.append(row)
        need(identity(before) == identity(directory.lstat()), 'stable directory traversal')
    return sorted(rows, key=lambda row: Path(row['relative']).parts)


def git(*arguments):
    global GIT_ACTIVE
    need(arguments in [('rev-parse', 'HEAD'), ('status', '--porcelain', '--untracked-files=all')]
         or len(arguments) == 2 and arguments[0] == 'rev-parse' and arguments[1].startswith(COMMIT + ':swdb-project/'),
         'closed read-only Git operation')
    GIT_ACTIVE = True
    try:
        return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '--no-optional-locks',
                                       '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false',
                                       '-c', 'index.threads=1', '-C', str(SOURCE), *arguments], timeout=20,
                                       env={'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent',
                                            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                                            'GIT_OPTIONAL_LOCKS': '0', 'LC_ALL': 'C'})
    finally:
        GIT_ACTIVE = False


def audit(event, args):
    if event == 'subprocess.Popen':
        need(GIT_ACTIVE and args[0] == '/usr/bin/git', 'only closed read-only Git child')
    elif event.startswith('socket.') or event in {'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'}:
        raise RuntimeError('native/network/project/tool execution forbidden')
    elif event == 'open':
        filename, mode, flags = args
        writable = isinstance(mode, str) and any(char in mode for char in 'wax+')
        writable = writable or flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writable:
            need(isinstance(filename, int) and GIT_ACTIVE and stat.S_ISFIFO(os.fstat(filename).st_mode),
                 'read-only observer forbids filesystem writes')


def runtime(expected):
    rows = []
    selected = [*expected['tools'].values(), *expected['wp_artifacts'], expected['why3_config']]
    selected += [{'path': name, 'sha256': value} for name, value in expected['runtime_files'].items()]
    for wanted in selected:
        got = pin(wanted['path'])
        need(got['sha256'] == wanted['sha256'], 'selected physical runtime bytes')
        rows.append(got)
    prefix = Path(expected['linux_prefix'])
    for key, root in [('why3_stdlib', prefix / 'share/why3/stdlib'),
                      ('wp_why3_support', prefix / 'share/frama-c/share/wp/why3'),
                      ('why3_drivers', prefix / 'share/why3/drivers')]:
        inventory = walk(root, byte_cap=256 * 1024**2)
        actual = [{'relative': r['relative'], 'sha256': r['sha256']} for r in inventory if r['kind'] == 'regular']
        need(actual == expected['portable_import_surfaces'][key], 'complete current import/support membership ' + key)
        rows += [dict(r, path=str(root / r['relative'])) for r in actual]
    for root_text, wanted in expected['why3_runtime_extension']['inventories'].items():
        root = Path(root_text)
        inventory = walk(root, byte_cap=256 * 1024**2)
        files = [{'relative': r['relative'], 'bytes': r['bytes'], 'sha256': r['sha256'],
                  'mode': stat.S_IMODE((root / r['relative']).lstat().st_mode)}
                 for r in inventory if r['kind'] == 'regular']
        directories = [r['relative'] for r in inventory if r['kind'] == 'directory']
        need(files == wanted['files'] and directories == wanted['directories'], 'Why3 package full membership')
    for wanted in expected['why3_elf_candidate_aliases']:
        path = Path(wanted['path'])
        physical(path.parent)
        need(stat.S_ISLNK(path.lstat().st_mode) and os.readlink(path) == wanted['target'] and
             str(path.resolve(strict=True)) == wanted['resolved'], 'exact prospective runtime alias')
        need(wanted['resolved'] in expected['runtime_files'], 'alias target physical pin')
    for row in expected['runtime_sources']:
        need(pin(prefix / 'lib/frama-c-wp/core' / row['name'])['sha256'] == row['sha256'], 'WP runtime source pin')
    for row in [expected['linux_clang_components']['command_executable'], expected['linux_clang_components']['driver']]:
        need(pin(row['path'])['sha256'] == row['sha256'], 'Clang wrapper/driver passive pin')
    compiler = Path(expected['linux_clang_components']['driver']['path']).parent.parent
    parser = compiler / 'lib/libclang.so'
    # A physical-target hash is reported separately from the old admission's
    # source-to-binary/loader boundary; no new generic symlink allowance is made.
    need(parser.resolve(strict=True).parent == compiler / 'lib', 'libclang target stays in selected lib directory')
    need(pin(parser.resolve(strict=True))['sha256'] == expected['linux_clang_components']['parser']['sha256'], 'libclang target bytes')
    headers = hashlib.sha256()
    count = 0
    for label, root in [('libc++', compiler / 'include/c++/v1'), ('clang-resource', compiler / 'lib/clang/22/include')]:
        for row in walk(root, byte_cap=128 * 1024**2):
            if row['kind'] == 'regular':
                headers.update(label.encode() + b'\0' + row['relative'].encode() + b'\0')
                headers.update(bytes.fromhex(row['sha256']))
                count += 1
    need({'id': 'llvm-standard-resource-headers', 'sha256': headers.hexdigest(), 'files': count}
         == expected['linux_clang_components']['headers'], 'complete resource and libc++ header identity')
    return {'physical_pins': rows, 'headers_count': count, 'headers_sha256': headers.hexdigest(),
            'TCB': 'Selected physical files/import roots/Why3 package only; no complete Python, OS loader, dlopen, continuous or source-to-binary closure. No retroactive historical Why3server identity.'}


def source_closure(expected):
    need(git('rev-parse', 'HEAD').decode().strip() == COMMIT and
         not git('status', '--porcelain', '--untracked-files=all'), 'current detached evaluated source clean')
    for row in expected['source_blobs'] + expected['test_helper_pins']:
        need(pin(SOURCE / 'swdb-project' / row['relative'])['sha256'] == row['sha256'], 'current selected source bytes')
    closures = [read(PROFILE / ('source-consumers-%d.json' % index)) for index in (0, 1)]
    need(closures[0] == closures[1], 'actual before/after source-consumer receipt equality')
    closure = closures[0]
    for relative, row in closure['trees'].items():
        need(git('rev-parse', COMMIT + ':swdb-project/' + relative).decode().strip() == row['oid'], 'consumer Git object')
    for row in closure['files']:
        path = SOURCE / 'swdb-project' / row['relative']
        need(str(path) == row['path'], 'consumer path bound to source')
        value = read_bytes(path, MAX_FILE)
        need(len(value) == row['bytes'] and sha(value) == row['sha256'] and
             hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest() == row['git_blob'],
             'consumer physical SHA256 and Git blob')
    for relative in closure['trees']:
        root = SOURCE / 'swdb-project' / relative
        actual = [str(root / r['relative']) for r in walk(root, byte_cap=128 * 1024**2, hash_files=False)
                  if r['kind'] == 'regular'] if root.is_dir() else [str(root)]
        wanted = [r['path'] for r in closure['files'] if r['path'] == str(root) or r['path'].startswith(str(root) + '/')]
        need(set(actual) == set(wanted), 'closed physical selected source membership')
    return {'count': closure['count'], 'bytes': closure['total_bytes'], 'trees': closure['trees'],
            'before_after_receipts_equal': True, 'physical_current_match': True}


def strip_comments(text):
    result = []
    depth = pos = 0
    while pos < len(text):
        if text.startswith('(*', pos) and not text.startswith('(*)', pos):
            depth += 1
            pos += 2
        elif depth and text.startswith('*)', pos):
            depth -= 1
            pos += 2
        else:
            if not depth:
                result.append(text[pos])
            pos += 1
    need(depth == 0, 'complete nested Why3 comments')
    return ''.join(result)


def import_closure(roots, prefix):
    graph, visiting = {}, set()
    def visit(name):
        if name in graph:
            return
        need(name not in visiting and len(graph) < 100, 'finite acyclic selected import closure')
        visiting.add(name)
        if name == 'why3.BuiltIn.BuiltIn':
            graph[name] = {'classification': 'Why3 intrinsic core TCB'}
        else:
            filename = name.rsplit('.', 1)[0].replace('.', '/') + '.mlw'
            candidates = [PROFILE / 'canonical-inputs/theory/vector_owned_state.mlw'] if name == 'vector_owned_state.Owners' else [prefix / 'share/why3/stdlib' / filename, prefix / 'share/frama-c/share/wp/why3' / filename]
            found = [path for path in candidates if path.exists()]
            need(len(found) == 1, 'unambiguous selected import ' + name)
            text = strip_comments(read_bytes(found[0]).decode())
            module = name.rsplit('.', 1)[1]
            bodies = list(re.finditer(r'^(?:module|theory) ' + re.escape(module) + r'\b[^\n]*\n(.*?)^end\s*$', text, re.M | re.S))
            need(len(bodies) == 1, 'whole selected module ' + name)
            body = bodies[0][1]
            propositions = re.findall(r'^\s*(axiom|lemma|goal)\s+(\w+)', body, re.M)
            if name == 'vector_owned_state.Owners':
                need(not propositions, 'Owners is definition-only, no desired axiom/lemma premise')
            edges = []
            for kind, target in re.findall(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b', body, re.M):
                full = target if '.' in target else name.rsplit('.', 1)[0] + '.' + target
                edges.append({'kind': kind, 'target': full})
                visit(full)
            graph[name] = {'file': pin(found[0]), 'module_body_sha256': sha(body.encode()),
                           'proposition_declarations': propositions, 'dependencies': edges,
                           'classification': 'project total definitions only' if name == 'vector_owned_state.Owners' else 'selected standard arithmetic/maps/Qed support TCB'}
        visiting.remove(name)
    for name in sorted(roots):
        visit(name)
    return graph


def normal_flags(flags):
    required = ['-wp', '-wp-rte', '-wp-cache', 'none', '-wp-model', '+real', '-wp-par', '1',
                '-machdep', 'x86_64', '-rte-initialized', '@all', '-wp-no-filter-init']
    need(flags[:len(required)] == required and '-wp-smoke-tests' in flags and '-wp-status-all' in flags and
         '-wp-print' in flags and not any(f.startswith(('-wp-prop', '-wp-fct')) or
         f in {'-wp-gen', '-wp-no-why3-detect'} for f in flags), 'normal complete ordinary method flags')


def guards(expected, context):
    launch = read(RAW / 'launch.json')
    need(digest(launch['command']) == COMMAND_SHA and launch['source_commit'] == COMMIT and
         launch['source'] == str(SOURCE) and launch['timeout_seconds'] == 2100 and
         launch['rss_cap_bytes'] == 8589934592 and launch['workers'] == 1, 'actual reviewed command/source/whole guard')
    for name, wanted in expected['linux_launch_binding']['wrappers'].items():
        need(pin(RAW / name)['sha256'] == wanted == launch['reviewed_wrapper_reuse'][name], 'actual reviewed wrapper')
    lane = read(RAW / 'lane.json')['socket_lane']
    need(lane['node'] == 0 and lane['lease_generation'] == 621 and lane['exit_code'] == 0 and
         lane['numa_memory_policy'] == 'bind:0' and lane['started_utc'] == '2026-10-16T21:51:35Z' and
         lane['ended_utc'] == '2026-10-16T21:52:07Z', 'exact settled G621 lane')
    resources = {name: read(RAW / name) for name in ('resources.json', 'outer-resources.json')}
    for name, value in resources.items():
        need(value['exit_code'] == 0 and not value['out_of_memory'] and not value['timed_out'] and
             value['peak_rss_bytes'] <= 8589934592 and value['wall_seconds'] < (2220 if name.startswith('outer') else 2100),
             'healthy settled whole guard')
    need(read(RAW / 'source-after.json') == {'commit': COMMIT, 'source_unchanged': True, 'tracked_changes': ''}, 'source-after exact clean')
    need('PYTHONPATH' not in read(RAW / 'dispatch-environment.json'), 'closed root dispatch environment')
    for relative, wanted in context['known_metadata_pins'].items():
        need(pin(RAW / relative)['sha256'] == wanted['sha256'], 'retained root/producer metadata identity')
    return {'lane': lane, 'resources': resources}


def main(context, semantic):
    started = time.monotonic()
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    sys.addaudithook(audit)
    initial = walk(RAW)
    membership = [{k: row[k] for k in ('relative', 'kind', 'bytes') if k in row} for row in initial]
    need(membership == context['raw_membership'], 'exact settled184-file/54-directory raw membership')
    need(len([r for r in initial if r['kind'] == 'regular']) == 184 and
         sum(r.get('bytes', 0) for r in initial) == 21000828, 'whole final raw extent')
    expected = read(PROFILE / 'expected.json')
    need(pin(PROFILE / 'expected.json')['sha256'] == EXPECTED_SHA, 'exact frozen expected context')
    need(expected['source_commit'] == COMMIT and expected['remote_project'] == str(SOURCE / 'swdb-project'), 'exact evaluated source')
    need(expected['resource_policy'] == context['resource_policy'], 'closed original producer resource policy')
    for path in (RAW / 'owned-transfer10-public-v2-entry.py', PROFILE / 'entry.py'):
        need(pin(path)['sha256'] == ENTRY_SHA, 'exact original producer entry')
    guard = guards(expected, context)
    consumers = source_closure(expected)
    runtime_before = runtime(expected)
    retained_runtime = read(PROFILE / 'runtime.json')
    need(set(retained_runtime) == set(expected['tools']) | {'why3_packages', 'why3_elf_candidates'},
         'complete retained initial selected runtime snapshot')
    for name, wanted in expected['tools'].items():
        need(retained_runtime[name]['sha256'] == wanted['sha256'], 'retained selected tool bytes')
    for name, wanted in expected['why3_runtime_extension']['inventories'].items():
        need(retained_runtime['why3_packages'][name] == {'count': len(wanted['files']),
             'inventory_sha256': digest(wanted['files'])}, 'retained initial Why3 package membership')
    manifest = read(PROFILE / 'canonical-inputs/manifest.json')
    need(manifest == expected['canonical_manifest'] == context['canonical_manifest'], 'complete canonical ownership/source manifest')
    canonical = [dict(path=r['relative'], bytes=r['bytes'], sha256=r['sha256'])
                 for r in walk(PROFILE / 'canonical-inputs') if r['kind'] == 'regular']
    need(canonical == expected['canonical_files'] and len(canonical) == 21, 'complete21 canonical bytes')
    need(all(not row['dependencies'] for row in manifest['obligations']) and
         manifest['current_model_records_admitted'] == manifest['caller_premises_added'] == [] and
         manifest['source_typed_bridge_established'] is False, 'no sibling/source/caller premise grant')
    foundation = read(PROFILE / 'foundation.json')
    for row in foundation['sources']:
        need(pin(row['path'])['sha256'] == row['sha256'], 'current standard/Typed foundation source')
    need(pin(foundation['metadata_executable'])['sha256'] == foundation['metadata_executable_sha256'], 'retained foundation helper bytes; not rerun')
    need(read(PROFILE / 'compiler-runtime.json') == {'runtime': expected['linux_project_identity_derivation']['runtime'],
         'identity': expected['linux_project_identity_derivation']['predicted_identity']}, 'producer compiler/source identity')
    method = read(PROFILE / 'method.json')
    need(method['tools']['seconds'] == 30 and method['tools']['provers'] == ['alt-ergo', 'z3', 'cvc5'], 'normal three-solver portfolio')
    normal_flags(method['flags'])
    need(method['flags'] == context['method_flags'], 'exact retained normal flag sequence/duplicates')
    result = read(PROFILE / 'result.json')
    need(result['producer_complete'] is True and result['all_ten_producer_proven'] is True and
         result['within_profile_budget'] is True and result['source_after_clean'] is True and
         result['unexecuted'] == [] and not result.get('error'), 'settled ten producer results')
    need([r['id'] for r in result['runs']] == expected['target_ids'] == list(semantic.GOALS), 'all ten distinct source duties in order')
    for key in ('proof_acceptance', 'source_typed_bridge_established', 'body_acceptance', 'caller_acceptance',
                'public_proof_record_created', 'universal_proof_setup_attested'):
        need(result[key] is False, 'source/body/caller/public/universal admission stays false')
    reader_source = read_bytes(SOURCE / 'swdb-project/swdb/proof_setup.py')
    check_names = []
    for node in ast.parse(reader_source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CHECK_SOURCES' for t in node.targets):
            check_names += ast.literal_eval(node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == 'CHECK_SOURCES':
            check_names += ast.literal_eval(node.value)
    identity_rows = [{'path': 'swdb/' + n, 'sha256': pin(SOURCE / 'swdb-project/swdb' / n)['sha256']} for n in check_names]
    identity_rows += [{'path': 'vocab/' + n, 'sha256': pin(SOURCE / 'swdb-project/vocab' / n)['sha256']}
                      for n in ('proof_failure_classes.yaml', 'proof_subject_kinds.yaml')]
    reading = {'version': '1', 'sha256': digest(identity_rows)}
    need(pin(PROFILE / 'reader/proof_report.ml')['sha256'] == pin(SOURCE / 'swdb-project/swdb/proof_report.ml')['sha256'], 'current retained native reader source')
    leaves, tasks, roots, unresolved = [], [], set(), []
    for run, target in zip(result['runs'], manifest['obligations']):
        ident = run['id']
        directory = PROFILE / ('leaf-' + ident)
        need(run['cwd'] == str(directory) and pin(directory / 'wp_input.c')['sha256'] == target['sha256'], 'leaf full canonical source')
        outcome = read(directory / 'outcome.json')
        need(outcome == run['outcome'] and outcome['verdict'] == 'proven' and not outcome['assumptions'] and
             not outcome['unproven'] and outcome['reading'] == {'check': reading, 'verdict': 'proven'}, 'current normal outcome with no opaque premise')
        resource_row = read(directory / 'resources.json')
        need(resource_row == run['resources'] and resource_row['exit_code'] == 0 and not any(resource_row[k] for k in
             ('timed_out', 'out_of_memory', 'output_limit')) and resource_row['peak_rss_bytes'] <= 8589934592 and
             resource_row['wall_seconds'] < 180, 'healthy exact leaf guard')
        invocation = read(directory / 'command.json')['argv']
        modules = [r['relative'] for r in initial if r['kind'] == 'regular' and
                   r['relative'].startswith(PROFILE.name + '/reader/') and r['relative'].endswith('.cmxs')]
        need(len(modules) == 1, 'sole retained native report module')
        diagnostics = 'print-generated,why3:compile,why3:import,prover:pp_task'
        exact_invocation = [expected['tools']['frama-c']['path'], '-machdep', 'x86_64', '-wp-library',
            str(PROFILE / 'canonical-inputs/theory'), '-wp-msg-key', diagnostics, 'wp_input.c', '-print',
            '-ocode', 'wp-normalized.c', '-then', *method['flags'], '-wp-library',
            str(PROFILE / 'canonical-inputs/theory'), '-wp-report-json', 'wp-goals.json', '-then',
            '-load-module', str(RAW / modules[0]), '-report', '-report-untried', '-report-csv', 'wp-properties.csv']
        need(invocation == exact_invocation, 'exact independently reconstructed ordinary complete command')
        need(not any(x.startswith(('-wp-prop', '-wp-fct')) or x == '-wp-gen' for x in invocation), 'no selective properties')
        native = read(directory / 'wp-inventory.json')
        ordinary = read(directory / 'wp-goals.json')
        prop = 'check_lemma_' + target['goal']
        need(native['version'] == '1' and native['complete'] is True and
             len(native['goals']) == len(ordinary) == len(outcome['goals']) == 1, 'one complete native ordinary owner')
        goal, peer = native['goals'][0], ordinary[0]
        need(goal['property'] == prop and goal['passed'] is True and goal['smoke'] is False and
             goal['targets'] == [] and 'valid' in goal['results'] and goal['function'] is None, 'direct global native Valid')
        need(all(goal.get(k) == peer.get(k) for k in ('goal', 'property', 'function', 'line', 'smoke', 'passed')) and
             any(p.get('success') for p in peer['provers']), 'ordinary/native/prover peer')
        properties = native['properties']
        need(len(properties) == 2 and [p['property'] for p in properties if p['kind'] == 'lemma'] == [prop] and
             all(not p['dependencies'] and p['origin'] is None and not p['extern'] and
                 not p.get('generated_smoke_failure') for p in properties), 'complete dependencies/origin/Extern property census')
        closure = native['property_closure']
        need(closure['initial_registered_snapshot_count'] == closure['registered_snapshot_count'] == closure['exported_count'] == 2 and
             not any(closure[k] for k in ('unregistered_status_lookup_performed', 'unregistered_wp_smoke_properties',
                                         'unregistered_wp_call_instances')), 'closed native registered property inventory')
        rows = list(csv.reader(io.StringIO(read_bytes(directory / 'wp-properties.csv').decode()), delimiter='\t'))
        need(rows == [['directory', 'file', 'line', 'function', 'property kind', 'status', 'property']], 'legitimate header-only global check-lemma CSV')
        log_bytes = read_bytes(directory / 'frama-c.log')
        log = log_bytes.decode()
        roots.update(re.findall(r'\(\* use ([\w.]+) \*\)', log))
        roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)', log))
        printed = re.findall(r'(?m)^  theory WP[0-9]*\s*\n(.*?)^  end\s*$', log, re.S)
        need(bool(printed), 'printed complete common Why3 theory')
        common = []
        for body in printed:
            clean = strip_comments(body)
            declarations = re.findall(r'^\s*(predicate|function|goal|axiom|lemma|constant|val|type)\s+(\w+)', clean, re.M)
            need([d for d in declarations if d[0] in ('goal', 'axiom', 'lemma')] == [('goal', 'wp_goal')],
                 'no common desired/sibling axiom or lemma premise')
            common.append({'body_sha256': sha(body.encode()), 'declarations': declarations})
        census = read(directory / 'task-census.json')
        need(not census['missing_noninternal_tasks'] and len(census['common_exports']) == len(printed), 'complete common export census')
        for export in census['common_exports']:
            segment = log_bytes[export['begin_byte']:export['end_byte']]
            need(sha(segment) == export['sha256'] and export['goal'] == goal['goal'], 'exact common byte-range/native owner')
        selected = [r for r in initial if r['kind'] == 'regular' and r['relative'].startswith(str(directory.relative_to(RAW)) + '/')
                    and Path(r['relative']).suffix in ('.psmt2', '.smt2')]
        need(len(selected) == 2 and all(Path(r['relative']).suffix == '.psmt2' for r in selected), 'all two retained Alt-Ergo task artifacts')
        for row in selected:
            path = RAW / row['relative']
            observed = semantic.task_semantics(read_bytes(path, 1024**2).decode(), ident, context['primary_standard_support'])
            tasks.append({'id': ident, 'artifact': row, **observed})
            unresolved += [dict(issue, id=ident, artifact=row['relative']) for issue in observed['unresolved']]
        leaves.append({'id': ident, 'goal': goal['goal'], 'property': prop, 'native_results': goal['results'],
                       'ordinary': 1, 'smokes': 0, 'properties': properties, 'CSV_data_rows': 0,
                       'native_provers': peer['provers'], 'common_theories': common, 'task_census': census})
    need(len(tasks) == 20 and len(leaves) == 10, 'complete ten-owner/twenty-task census')
    graph = import_closure(roots, Path(expected['linux_prefix']))
    need('vector_owned_state.Owners' in graph, 'actual Owners import present')
    manifest_rows = read(PROFILE / 'artifact-manifest.json')
    advertised = []
    for row in manifest_rows:
        path = Path(row['path'])
        need(path == PROFILE / row['relative'], 'retention row stays in profile')
        actual = pin(path)
        need(actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes'], 'retention physical hash')
        advertised.append(row['relative'])
    profile_files = [r['relative'][len(PROFILE.name) + 1:] for r in initial if r['kind'] == 'regular' and
                     r['relative'].startswith(PROFILE.name + '/')]
    need(len(advertised) == len(set(advertised)) == 164 and
         set(advertised) | {'artifact-manifest.json'} == set(profile_files), 'retention complete exact profile membership')
    runtime_after = runtime(expected)
    need(runtime_before == runtime_after, 'passive current runtime pre/post identity')
    need(source_closure(expected) == consumers, 'passive current source pre/post identity')
    final = walk(RAW)
    need(final == initial, 'entire raw stable full-content pre/post hash identity')
    STATE.update({'classification': 'COMPLETE_COLD_CAPTURE_PENDING_ENCODING_REVIEW' if unresolved else 'PASS_CONDITIONAL_OWNERSHIP10_MATH_COLD',
                  'date': '2026-10-16 ET', 'source_commit': COMMIT, 'raw_root': str(RAW),
                  'raw_manifest': initial, 'raw_manifest_sha256': digest(initial), 'raw_files': 184,
                  'raw_bytes': 21000828, 'raw_pre_post_equal': True, 'source_consumers': consumers,
                  'runtime': runtime_before, 'guards': guard, 'reader_check': reading,
                  'historical_runtime_snapshot_boundary': 'One retained initial runtime.json. Producer source calls runtime_check before each target and after all targets, but these later return values are not separately retained. Current passive pre/post file identity is not retroactive continuous runtime identity.',
                  'leaves': leaves, 'materialized_tasks': tasks, 'direct_import_roots': sorted(roots),
                  'import_source_closure': graph, 'unresolved_semantic_encodings': unresolved,
                  'all_ten_conditional_math_semantically_reconciled': not unresolved,
                  'consistency': context['constructive_consistency'], 'checks': CHECKS,
                  'elapsed_seconds': time.monotonic() - started,
                  'actual_submission_count': None, 'submitted_bytes_attested': False,
                  'proof_acceptance': False, 'body_acceptance': False, 'caller_acceptance': False,
                  'source_typed_bridge_established': False, 'public_proof_record_created': False,
                  'universal_proof_setup_attested': False,
                  'scope': 'Ten conditional unbounded mathematical registry duties only. Original8 move/swap bodies remain unproved context; no source field/ownership/lifetime/Heap/allocator/Typed/body/caller/default/public admission. Zero global check-lemma smokes are not empirical consistency evidence.'})
    encoded = compact(STATE) + b'\n'
    need(len(encoded) <= MAX_OUTPUT, 'compact result output cap')
    signal.alarm(0)
    sys.stdout.buffer.write(encoded)
    return 0 if not unresolved else 2


if __name__ == '__main__':
    # Filled by freeze.py as one self-contained stdin observer. Definitions above
    # are source reviewed before the context/helper bytes are loaded. No imports
    # from the project or neighboring controller directories are permitted.
    try:
        context = json.loads(CONTEXT_JSON)
        need(sha(SEMANTIC_SOURCE.encode()) == context['semantic_source_sha256'], 'exact pure semantic helper')
        module = type(sys)('ownership10_semantics')
        exec(compile(SEMANTIC_SOURCE, '<pinned-ownership10-pure-terms>', 'exec'), module.__dict__)
        raise SystemExit(main(context, module))
    except Exception as error:
        STATE.update({'classification': 'REFUSED_OWNERSHIP10_PASSIVE_COLD', 'error_type': type(error).__name__,
                      'error': str(error)[:2048], 'checks_before_refusal': CHECKS, 'scientific_acceptance': False})
        encoded = compact(STATE)
        sys.stdout.buffer.write((encoded if len(encoded) <= MAX_OUTPUT else compact({
            'classification': 'REFUSED_OWNERSHIP10_PASSIVE_COLD', 'error': 'bounded diagnostic overflow',
            'scientific_acceptance': False})) + b'\n')
        raise SystemExit(1)
