"""2026-10-16 ET. Read-only stdlib/Git focused10 cold audit; no project/tool probes."""
import ast
import csv
import hashlib
import io
import json
import re
import signal
import subprocess
import time
from collections import Counter
from pathlib import Path

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-c978393b-t25-copy-prefix10-v1')
PROFILE = RAW / 'copy-prefix10-diagnostic-profile'
SOURCE = Path('/data1/yanruj/probata-resume-20261016-c978393b')
COMMIT = 'c978393b119a3614229a37f0f2c8ca2a097c750b'
ENTRY_SHA = '6cdf4ca34c5c6b11d30fab45d078742fea18de4dc84afb3d8e01b52c2b7c3549'
EXPECTED_SHA = '7066731f62e2e1273b001f599728d5127611252982702d89dfa6204c2af1adfd'
CHECKS = []


def require(value, label):
    if not value:
        raise ValueError(label)
    CHECKS.append(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def pin(path):
    path = Path(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino), 'stable read ' + str(path))
    return {'path': str(path), 'bytes': before.st_size, 'sha256': h.hexdigest()}


def read(path):
    return json.loads(Path(path).read_bytes())


def git(*args, input=None):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(SOURCE), *args],
                                   input=input, timeout=30)


def snapshot(root):
    result = []
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), 'regular raw input ' + str(path))
        if path.is_file():
            result.append({'relative': str(path.relative_to(root)), **pin(path)})
    return result


def forms(text):
    lex = re.compile(r'\s+|;[^\n]*|"(?:[^"]|"")*"|\|[^|]*\||[()]|[^\s()]+')
    stack = [[]]
    position = 0
    for match in lex.finditer(text):
        require(match.start() == position, 'SMT token coverage')
        position = match.end()
        token = match[0]
        if token.isspace() or token.startswith(';'):
            continue
        if token == '(':
            item = []
            stack[-1].append(item)
            stack.append(item)
        elif token == ')':
            require(len(stack) > 1, 'balanced SMT close')
            stack.pop()
        else:
            stack[-1].append(token)
    require(position == len(text) and len(stack) == 1, 'complete SMT parse')
    return stack[0]


def expand(value, env=None):
    env = {} if env is None else env
    if isinstance(value, str):
        return env.get(value, value)
    if value and value[0] == 'let':
        additions = {name: expand(body, env) for name, body in value[1]}
        return expand(value[2], {**env, **additions})
    return [expand(x, env) for x in value]


def norm(value, env=None):
    value = expand(value, env)
    if isinstance(value, str):
        return value
    head = value[0]
    if head in {'forall', 'exists'}:
        names = {row[0]: 'bound' + str(i) for i, row in enumerate(value[1])}
        return [head, [row[1] for row in value[1]], norm(value[2], names)]
    args = [norm(x) for x in value[1:]]
    if head in {'and', 'or', '+', '*'}:
        flat = []
        for item in args:
            flat.extend(item[1:] if isinstance(item, list) and item and item[0] == head else [item])
        return [head, *sorted(flat, key=lambda x: json.dumps(x, sort_keys=True))]
    if head == '=':
        args.sort(key=lambda x: json.dumps(x, sort_keys=True))
    if head == '=>' and len(args) == 2 and isinstance(args[1], list) and args[1][0] == '=>':
        return norm(['=>', ['and', args[0], args[1][1]], args[1][2]])
    return [head, *args]


def strip_comments(text):
    output = []
    i = depth = 0
    while i < len(text):
        if text.startswith('(*', i) and not text.startswith('(*)', i):
            depth += 1
            i += 2
        elif depth and text.startswith('*)', i):
            depth -= 1
            require(depth >= 0, 'Why3 balanced comment')
            i += 2
        else:
            if not depth:
                output.append(text[i])
            i += 1
    require(depth == 0, 'Why3 complete comments')
    return ''.join(output)


def check_goal(tree, ident):
    require(tree[0] == 'not' and len(tree) == 2, 'final negated goal ' + ident)
    goal = tree[1]
    require(goal[0] == 'forall', 'unbounded quantified source goal ' + ident)
    body = expand(goal[2])
    antecedents = []
    while isinstance(body, list) and body[0] == '=>':
        antecedents.append(body[1])
        body = body[2]
    inv = [x for x in antecedents if x[0] == 'P_t25v3_copy_inv']
    require(len(inv) == 1 and len(inv[0]) == 12, 'one full original invariant ' + ident)
    names = dict(zip(inv[0][1:], ['entry', 'h', 'r', 'o', 'b', 'bo', 's', 'c', 'f', 'cap', 'k']))
    require(len(names) == 11, 'distinct original source binders ' + ident)
    if '.prior.' in ident:
        candidates = [a[2] for a in antecedents if len(a) == 3 and a[:2] == ['<=', '0']]
        require(len(candidates) == 1 and candidates[0] not in names, 'fresh prior index ' + ident)
        names[candidates[0]] = 'j'
        wanted = [['<', 'k', 's'], ['<=', '0', 'j'], ['<', 'j', 'k']]
        j = 'j'
    else:
        wanted = [['<=', '0', 'k'], ['<', 'k', 's']]
        j = 'k'
    expected_inv = ['P_t25v3_copy_inv', 'entry', 'h', 'r', 'o', 'b', 'bo', 's', 'c', 'f', 'cap', 'k']
    require(Counter(digest(norm(a, names)) for a in antecedents) ==
            Counter(digest(norm(a)) for a in [*wanted, expected_inv]), 'exact source-equivalent antecedents ' + ident)
    updated = ['copy_int', 'h', 'b', ['+', 'bo', ['*', '4', 'k']], 'f', ['*', '4', 'k']]
    offset = ['*', '4', j]
    loaded = ['load_int', updated, 'f', offset]
    conclusion = {
        'access': ['typed_reads', updated, 'f', offset, '4', '4'],
        'initialization': ['initialized_at', updated, 'f', offset],
        'integer': ['integer_at', updated, 'f', offset, loaded],
        'bounds': ['and', ['<=', ['-', '2147483648'], loaded], ['<=', loaded, '2147483647']],
        'value': ['=', loaded, ['load_int', 'entry', 'b', ['+', 'bo', offset]]],
    }[ident.rsplit('.', 1)[1]]
    require(norm(body, names) == norm(conclusion), 'exact source-derived conclusion ' + ident)
    return {'antecedents': [norm(x, names) for x in antecedents], 'conclusion': norm(body, names),
            'tree_sha256': digest(tree), 'full_A_range_case_equivalent': True}


def main():
    signal.alarm(60)
    started = time.monotonic()
    initial = snapshot(RAW)
    expected = read(PROFILE / 'expected.json')
    require(pin(PROFILE / 'expected.json')['sha256'] == EXPECTED_SHA, 'reviewed expected bytes')
    for path in [RAW / 'copy-prefix10-diagnostic-entry.py', PROFILE / 'entry.py']:
        require(pin(path)['sha256'] == ENTRY_SHA, 'reviewed entry bytes ' + str(path))
    require(expected['source_commit'] == COMMIT and expected['remote_project'] == str(SOURCE / 'swdb-project'), 'exact producer source/context')
    require(git('rev-parse', 'HEAD').decode().strip() == COMMIT and not git('status', '--porcelain', '--untracked-files=all'), 'live exact source clean')
    for row in expected['source_blobs'] + expected['test_helper_pins']:
        require(pin(SOURCE / 'swdb-project' / row['relative'])['sha256'] == row['sha256'], 'current source/helper ' + row['relative'])
    consumers = []
    for path in sorted(PROFILE.glob('source-consumers-*.json')):
        closure = read(path)
        for relative, row in closure['trees'].items():
            require(git('rev-parse', COMMIT + ':swdb-project/' + relative).decode().strip() == row['oid'], 'consumer selected Git root ' + relative)
        for row in closure['files']:
            got = pin(row['path'])
            require(got['sha256'] == row['sha256'] and got['bytes'] == row['bytes'], 'consumer current bytes ' + row['relative'])
        actual_oids = git('hash-object', '--no-filters', '--stdin-paths', input=''.join(r['path'] + '\n' for r in closure['files']).encode()).decode().splitlines()
        require(actual_oids == [r['git_blob'] for r in closure['files']], 'consumer current physical Git blobs')
        consumers.append({'receipt': pin(path), 'count': closure['count'], 'total_bytes': closure['total_bytes']})
    require(len(consumers) == 2 and read(PROFILE / 'source-consumers-0.json') == read(PROFILE / 'source-consumers-1.json'), 'before/after complete source consumers equal')
    runtime_pins = []
    for row in [*expected['tools'].values(), *expected['wp_artifacts'], expected['why3_config']]:
        got = pin(row['path'])
        require(got['sha256'] == row['sha256'], 'current installed tool/support/config ' + row['path'])
        runtime_pins.append(got)
    prefix = Path(expected['linux_prefix'])
    for key, root in [('why3_stdlib', prefix / 'share/why3/stdlib'), ('wp_why3_support', prefix / 'share/frama-c/share/wp/why3'), ('why3_drivers', prefix / 'share/why3/drivers')]:
        actual = []
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink(), 'physical import root ' + str(path))
            if path.is_file():
                got = pin(path)
                runtime_pins.append(got)
                actual.append({'relative': str(path.relative_to(root)), 'sha256': got['sha256']})
        require(actual == expected['portable_import_surfaces'][key], 'full installed import surface ' + key)
    foundation = read(PROFILE / 'foundation.json')
    for row in [*foundation['sources'], *read(PROFILE / 'typed-runtime.json')['sources']]:
        require(pin(row['path'])['sha256'] == row['sha256'], 'current foundation/Typed source ' + row['path'])
    require(pin(foundation['metadata_executable'])['sha256'] == foundation['metadata_executable_sha256'], 'retained metadata executable posthash')
    require(read(PROFILE / 'compiler-runtime.json') == {'runtime': expected['linux_project_identity_derivation']['runtime'], 'identity': expected['linux_project_identity_derivation']['predicted_identity']}, 'actual project compiler context equals current prospective reconstruction')
    for row in [expected['linux_clang_components']['command_executable'], expected['linux_clang_components']['driver']]:
        require(pin(row['path'])['sha256'] == row['sha256'], 'current Clang physical bytes ' + row['path'])
    compiler_root = Path(expected['linux_clang_components']['driver']['path']).parent.parent
    resource_root = compiler_root / 'lib/clang/22'
    require(pin((compiler_root / 'lib/libclang.so').resolve())['sha256'] == expected['linux_clang_components']['parser']['sha256'], 'current matching libclang bytes')
    header_digest = hashlib.sha256()
    header_count = 0
    for label, root in [('libc++', compiler_root / 'include/c++/v1'), ('clang-resource', resource_root / 'include')]:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                got = pin(path)
                header_digest.update(label.encode() + b'\0' + str(path.relative_to(root)).encode() + b'\0')
                header_digest.update(bytes.fromhex(got['sha256']))
                header_count += 1
    require({'id': 'llvm-standard-resource-headers', 'sha256': header_digest.hexdigest(), 'files': header_count} == expected['linux_clang_components']['headers'], 'complete current compiler resource/header identity')
    launch = read(RAW / 'launch.json')
    command = launch['command']
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(command[6]).body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {'ENTRY_SHA256', 'EXPECTED_SHA256'}}
    require(constants == {'ENTRY_SHA256': ENTRY_SHA, 'EXPECTED_SHA256': EXPECTED_SHA}, 'actual launch exact recipe constants')
    require(launch['source_commit'] == COMMIT and Path(launch['source']) == SOURCE, 'launch exact source')
    for name, want in expected['linux_launch_binding']['wrappers'].items():
        require(pin(RAW / name)['sha256'] == want == launch['reviewed_wrapper_reuse'][name], 'reviewed outer guard ' + name)
    guards = {name: read(RAW / name) for name in ['resources.json', 'outer-resources.json']}
    for name, guard in guards.items():
        require(guard['exit_code'] == 0 and not guard['out_of_memory'] and not guard['timed_out'] and guard['peak_rss_bytes'] <= 8589934592, 'healthy resource guard ' + name)
    lane = read(RAW / 'lane.json')['socket_lane']
    require(lane['node'] == 0 and lane['lease_generation'] == 603 and lane['exit_code'] == 0 and lane['numa_memory_policy'] == 'bind:0', 'settled node0 G603 lane binding')
    require(read(RAW / 'source-after.json') == {'commit': COMMIT, 'source_unchanged': True, 'tracked_changes': ''}, 'producer sourceafter clean')
    require('PYTHONPATH' not in read(RAW / 'dispatch-environment.json'), 'actual lane environment removes outer PYTHONPATH')
    manifest = read(PROFILE / 'canonical-inputs/manifest.json')
    for row in expected['canonical_files']:
        got = pin(PROFILE / 'canonical-inputs' / row['path'])
        require(got['sha256'] == row['sha256'] and got['bytes'] == row['bytes'], 'complete canonical input ' + row['path'])
    require(len(manifest['obligations']) == 61 and manifest['logical_obligations'] == expected['logical_obligations'], 'complete61 original logical receipt')
    result = read(PROFILE / 'result.json')
    require(result['selected_ids'] == expected['diagnostic_ids'] and result['diagnostic_complete'] and result['all_ten_producer_proven'] and not result['unexecuted'], 'ten complete fresh producer outcomes')
    require(not any(result[key] for key in ['model_acceptance', 'caller_acceptance', 'original_v2_acceptance', 'ticket_closure', 'public_proof_record_created']), 'all larger acceptance flags remain false')
    setup = read(PROFILE / 'setup.json')
    require(setup['verdict'] == 'passed' and len(setup['runs']) == 10, 'all ten ordinary setup checks passed')
    check_names = []
    for node in ast.parse((SOURCE / 'swdb-project/swdb/proof_setup.py').read_bytes()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CHECK_SOURCES' for t in node.targets):
            check_names.extend(ast.literal_eval(node.value))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == 'CHECK_SOURCES':
            check_names.extend(ast.literal_eval(node.value))
    identity_rows = [{'path': 'swdb/' + name, 'sha256': pin(SOURCE / 'swdb-project/swdb' / name)['sha256']} for name in check_names]
    identity_rows.extend({'path': 'vocab/' + name, 'sha256': pin(SOURCE / 'swdb-project/vocab' / name)['sha256']} for name in ['proof_failure_classes.yaml', 'proof_subject_kinds.yaml'])
    require(setup['check'] == {'version': '1', 'sha256': digest(identity_rows)}, 'independent current ordinary setup/reader source identity')
    method = read(PROFILE / 'method.json')
    require(method['tools']['seconds'] == 30 and method['tools']['provers'] == ['alt-ergo', 'z3', 'cvc5'], 'unchanged canonical portfolio')
    tasks = []
    leaves = []
    direct_roots = set()
    for run in result['runs']:
        ident = run['id']
        target = next(row for row in manifest['obligations'] if row['id'] == ident)
        directory = PROFILE / ('leaf-' + ident)
        require(str(directory) == run['cwd'] and pin(directory / 'wp_input.c')['sha256'] == target['sha256'], 'leaf full source identity ' + ident)
        require(read(directory / 'outcome.json') == run['outcome'], 'retained outcome equality ' + ident)
        require(run['outcome']['verdict'] == 'proven' and not run['outcome']['assumptions'] and not run['outcome']['unproven'], 'ordinary outcome no assumptions ' + ident)
        require(run['outcome']['reading'] == {'check': setup['check'], 'verdict': 'proven'}, 'current per-leaf normal reader attestation ' + ident)
        require(run['resources']['exit_code'] == 0 and not run['resources']['out_of_memory'] and not run['resources']['timed_out'], 'leaf healthy process ' + ident)
        native = read(directory / 'wp-inventory.json')
        ordinary = read(directory / 'wp-goals.json')
        require(native['version'] == '1' and native['complete'] is True and len(native['goals']) == len(ordinary) == len(run['outcome']['goals']) == 1, 'complete one native goal ' + ident)
        goal = native['goals'][0]
        prop = 'check_lemma_' + target['goal']
        require(goal['property'] == prop and goal['passed'] is True and goal['smoke'] is False and goal['targets'] == [] and 'valid' in goal['results'], 'sole ordinary native directValid owner ' + ident)
        require(ordinary[0]['property'] == prop and ordinary[0]['goal'] == goal['goal'] and ordinary[0]['passed'] is True and any(p['success'] for p in ordinary[0]['provers']), 'native/ordinary direct result equality ' + ident)
        require(all(p.get('dependencies') == [] and p.get('origin') is None and p.get('extern') is False and not p.get('generated_smoke_failure') for p in native['properties']), 'closed property/DAG/Extern census ' + ident)
        require(len(native['properties']) == 2 and [p['property'] for p in native['properties'] if p['kind'] == 'lemma'] == [prop], 'one source lemma plus module only ' + ident)
        require(list(csv.DictReader(io.StringIO((directory / 'wp-properties.csv').read_text()), delimiter='\t')) == [], 'legitimate global-lemma header-only CSV ' + ident)
        closure = native['property_closure']
        require(closure['initial_registered_snapshot_count'] == closure['registered_snapshot_count'] == closure['exported_count'] == 2 and not closure['unregistered_status_lookup_performed'] and not closure['unregistered_wp_smoke_properties'] and not closure['unregistered_wp_call_instances'], 'refreshed complete native property ownership ' + ident)
        log = (directory / 'frama-c.log').read_text()
        direct_roots.update(re.findall(r'\(\* use ([\w.]+) \*\)', log))
        direct_roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)', log))
        printed = re.search(r'(?m)^  theory WP\s*\n(.*?)^  end\s*$', log, re.S)
        require(printed is not None, 'complete emitted Why3 theory ' + ident)
        theory = strip_comments(printed[1])
        require(re.findall(r'^\s*(predicate|goal)\s+(\w+)', theory, re.M) == [('predicate', x) for x in ['P_t25v3_copy_frame', 'P_t25_fields', 'P_t25_repr', 'P_t25v3_repr', 'P_t25v3_eligible', 'P_t25v3_copy_inv']] + [('goal', 'wp_goal')], 'six source predicate definitions plus sole goal ' + ident)
        require(not re.search(r'^\s*(?:axiom|lemma|constant|val)\b', theory, re.M), 'no desired theorem premise in printed task ' + ident)
        leaf_tasks = sorted(directory.rglob('*.psmt2')) + sorted(directory.rglob('*.smt2'))
        require(len(leaf_tasks) >= 1, 'materialized task retained ' + ident)
        for task in leaf_tasks:
            text = task.read_text()
            tree = forms(text)
            assertions = [x[1] for x in tree if x[0] == 'assert']
            checks = [i for i, x in enumerate(tree) if x[0] == 'check-sat']
            require(len(checks) == 1 and all(x == ['get-info', ':reason-unknown'] for x in tree[checks[0] + 1:]), 'one check-sat with query-only standard epilogue ' + str(task))
            source_goal = check_goal(assertions[-1], ident)
            definitions = [x for x in tree if x[0] == 'define-fun']
            predicates = {x[1]: {'form_sha256': digest(x), 'body_sha256': digest(x[-1]), 'normalized_body_sha256': digest(norm(x[-1]))} for x in definitions if x[1].startswith('P_t25')}
            require(set(predicates) == {'P_t25v3_copy_frame', 'P_t25_fields', 'P_t25_repr', 'P_t25v3_repr', 'P_t25v3_eligible', 'P_t25v3_copy_inv'}, 'exact six materialized source predicates ' + str(task))
            expected_bodies = {
                'P_t25_fields': '(and (typed_writes h r o 24 8) (initialized_at h r o) (pointer_at h r o b bo) (initialized_at h r (+ o 8)) (integer_at h r (+ o 8) s) (initialized_at h r (+ o 16)) (integer_at h r (+ o 16) c))',
                'P_t25_repr': '(and (P_t25_fields h r o b bo s c) (<= 0 s) (<= s c) (<= c 4611686018427387903) (ite (= c 0) (and (= b 0) (= bo 0)) (typed_writes h b bo (* 4 c) 4)) (forall ((j Int)) (=> (<= 0 j) (=> (< j s) (initialized_at h b (+ bo (* 4 j)))))))',
                'P_t25v3_repr': '(and (P_t25_repr h r o b bo s c) (int32_region h b bo s))',
                'P_t25v3_eligible': '(and (P_t25v3_repr h r o b bo s c) (or (= c 0) (and (freeable h b bo) (not (= r b)))))',
                'P_t25v3_copy_frame': '(and (= (next h) (+ (next entry) 1)) (forall ((x Int)) (=> (not (= x fresh)) (same_object entry h x))) (forall ((x Int) (p Int)) (=> (not (= x fresh)) (and (= (contents entry x p) (contents h x p)) (= (initialized_at entry x p) (initialized_at h x p))))))',
                'P_t25v3_copy_inv': '(and (well_formed entry) (well_formed h) (P_t25v3_eligible entry r o b bo s c) (P_t25v3_eligible h r o b bo s c) (<= 0 k) (<= k s) (<= s c) (< c cap) (<= cap 4611686018427387903) (= f (next entry)) (not (issued entry f)) (not (= f r)) (not (= f b)) (typed_writes h f 0 (* 4 cap) 4) (freeable h f 0) (= (bytes h f) (* 4 cap)) (P_t25v3_copy_frame entry h f) (copied_prefix entry h b bo f k) (forall ((j Int)) (=> (<= k j) (=> (< j cap) (not (initialized_at h f (* 4 j)))))))',
            }
            for definition in definitions:
                if definition[1] in expected_bodies:
                    wanted = forms(expected_bodies[definition[1]])[0]
                    require(norm(definition[-1]) == norm(wanted), 'exact source-derived predicate body ' + definition[1] + ' ' + str(task))
            require(not any('check_lemma_' in json.dumps(a) or 'prior_' in json.dumps(a) or 'written_' in json.dumps(a) for a in assertions[:-1]), 'no sibling/desired assertion support ' + str(task))
            tasks.append({'id': ident, **pin(task), 'assertions': len(assertions), 'support_body_sha256': [digest(x) for x in assertions[:-1]], 'source_predicates': predicates, 'source_goal': source_goal,
                          'definition_names': [x[1] for x in definitions], 'actual_submission_attested': False})
        leaves.append({'id': ident, 'property': prop, 'goal': goal['goal'], 'native_results': goal['results'], 'solver': run['outcome']['goals'][0]['solver'], 'solver_seconds': run['outcome']['goals'][0]['seconds'], 'ordinary': 1, 'smoke': 0, 'properties': 2, 'CSV_rows': 0, 'source_input': pin(directory / 'wp_input.c')})
    require(len(leaves) == 10 and len({r['property'] for r in leaves}) == 10, 'ten distinct source owners preserved despite short-goal collision')
    normalized_predicates = lambda task: {name: row['normalized_body_sha256'] for name, row in task['source_predicates'].items()}
    require(all(normalized_predicates(t) == normalized_predicates(tasks[0]) for t in tasks), 'all materialized tasks share identical normalized original six predicate definitions')
    roots = {'stdlib': prefix / 'share/why3/stdlib', 'wp': prefix / 'share/frama-c/share/wp/why3'}
    graph = {}
    visiting = set()
    def visit(name):
        if name in graph:
            return
        require(name not in visiting, 'acyclic imported module ' + name)
        visiting.add(name)
        if name == 'why3.BuiltIn.BuiltIn':
            graph[name] = {'classification': 'selected Why3 intrinsic core'}
        else:
            filename = name.rsplit('.', 1)[0].replace('.', '/') + '.mlw'
            candidates = [PROFILE / 'canonical-inputs/theory/heap_reallocation.mlw'] if name == 'heap_reallocation.Heap' else [root / filename for root in roots.values()]
            found = [path for path in candidates if path.is_file()]
            require(len(found) == 1, 'unambiguous selected import ' + name)
            text = strip_comments(found[0].read_text())
            module = name.rsplit('.', 1)[1]
            bodies = list(re.finditer(r'^(?:module|theory) ' + re.escape(module) + r'\b[^\n]*\n(.*?)^end\s*$', text, re.M | re.S))
            require(len(bodies) == 1, 'complete selected module body ' + name)
            body = bodies[0][1]
            edges = []
            for edge in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b', body, re.M):
                kind, target = edge.groups()
                full = target if '.' in target else name.rsplit('.', 1)[0] + '.' + target
                edges.append({'kind': kind, 'target': full})
                visit(full)
            declarations = re.findall(r'^\s*(axiom|lemma|goal)\s+(\w+)', body, re.M)
            if name == 'heap_reallocation.Heap':
                require(not declarations, 'project Heap has definitions only and no desired assertions')
            graph[name] = {'source': pin(found[0]), 'module_body_sha256': hashlib.sha256(body.encode()).hexdigest(), 'dependencies': edges,
                           'proposition_declarations': declarations, 'classification': 'project definitions only' if name == 'heap_reallocation.Heap' else 'selected standard arithmetic/maps/Qed TCB'}
        visiting.remove(name)
    for name in sorted(direct_roots):
        visit(name)
    artifact_rows = read(PROFILE / 'artifact-manifest.json')
    for row in artifact_rows:
        require(pin(row['path'])['sha256'] == row['sha256'], 'producer artifact manifest current bytes ' + row['relative'])
    require(snapshot(RAW) == initial, 'complete remote raw pre/post hash identity')
    output = {'created': '2026-10-16 ET', 'classification': 'PASSIVE_COLD_CAPTURE_RECONCILED_SOURCE_NATIVE_TASKS; primary support hash reconciliation remains local',
              'source_commit': COMMIT, 'raw_root': str(RAW), 'checks': len(CHECKS), 'elapsed_seconds': time.monotonic() - started,
              'raw_files': len(initial), 'raw_bytes': sum(p['bytes'] for p in initial), 'raw_manifest': initial, 'raw_manifest_sha256': digest(initial),
              'source_consumers': consumers, 'runtime_pins': runtime_pins, 'guard': guards, 'lane': lane, 'leaves': leaves, 'materialized_tasks': tasks,
              'source_predicate_definitions': tasks[0]['source_predicates'], 'direct_import_roots': sorted(direct_roots), 'import_source_closure': graph,
              'result_pin': pin(PROFILE / 'result.json'), 'setup_pin': pin(PROFILE / 'setup.json'), 'launch_pin': pin(RAW / 'launch.json'),
              'entry_sha256': ENTRY_SHA, 'expected_sha256': EXPECTED_SHA, 'raw_pre_post_equal': True, 'sourceafter_clean': True,
              'actual_submission_count': None, 'submitted_byte_attestation': False, 'proof_or_fullmodel_or_caller_acceptance': False,
              'scope': 'Ten conditional mathematical source duties only. Zero C smoke/RTE reachability; numeric and other51 targets unexecuted. Native outcomes are source-mapped; materialized tasks are not submission attestations. Standard arithmetic/map/datatype/import transformations remain explicit TCB.'}
    print(json.dumps(output, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'classification': 'REFUSED_PASSIVE_AUDIT', 'error_type': type(error).__name__, 'error': str(error), 'checks_before_refusal': len(CHECKS), 'acceptance': False}))
        raise SystemExit(1)
