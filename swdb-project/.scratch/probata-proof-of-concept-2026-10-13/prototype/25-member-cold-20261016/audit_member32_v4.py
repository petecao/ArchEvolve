"""2026-10-16 ET. Independent read-only cold census of root's actual32 bodies.

No compiler/verifier/native/query invocation, project import or raw mutation.
The normal WP generation, standard theories and solver soundness remain TCB.
"""
import ast
import collections
import csv
import hashlib
import io
import json
import re
import shlex
import signal
import stat
import sys
import time
import types
from pathlib import Path

import yaml

PROJECT = Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project')
POC = PROJECT/'.scratch/probata-proof-of-concept-2026-10-13'
RAW = Path('/private/tmp/probata-vector-member-all32-public-20261016-v3')
OUT = POC/'evidence/t25-member-all32-independent-cold-v4-20261016.json'
ATTEMPTS = []
CHECKS = 0


def need(value, label):
    global CHECKS
    CHECKS += 1
    if not value:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def read(path):
    return json.loads(path.read_bytes())


def census():
    rows = []
    for path in sorted(RAW.rglob('*')):
        s = path.lstat()
        need(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode), 'raw links/specials forbidden')
        row = {'relative': str(path.relative_to(RAW)), 'kind': 'directory' if path.is_dir() else 'regular'}
        if path.is_file():
            raw = path.read_bytes()
            need(len(raw) == s.st_size, 'raw file stable while reading')
            row.update(bytes=len(raw), sha256=sha(raw))
        rows.append(row)
    need(sum(row.get('bytes', 0) for row in rows) <= 128*1024**2, 'entire raw <=128MiB')
    return rows


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen', 'socket.connect'}:
        ATTEMPTS.append(event)
        raise RuntimeError('cold audit forbids child/native/network')
    if event == 'open':
        path, mode, flags = args
        writing = isinstance(mode, str) and any(char in mode for char in 'wax+') or flags & 0o1101
        if writing:
            need(isinstance(path, str) and Path(path) == OUT, 'only the independent compact decision may be written')


def load_pure():
    # Explicitly load two reviewed pure sources, with no package initializer.
    package = types.ModuleType('swdb')
    package.__path__ = []
    sys.modules['swdb'] = package
    registry = types.ModuleType('swdb.c_lowering')
    for key in ('INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'):
        setattr(registry, key, literal(key, PROJECT/'swdb/c_lowering.py'))
    sys.modules[registry.__name__] = registry
    package.c_lowering = registry
    for name in ('std_models', 'standard_vector_member_view'):
        path = PROJECT/'swdb'/(name+'.py')
        module = types.ModuleType('swdb.'+name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        setattr(package, name, module)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    parser_path = POC/'prototype/25-owned-source-view-20261016/source9-cold/semantic_terms.py'
    need(pin(parser_path)['sha256'] == 'eb0265a44d147f062292bd32c299edd58dd3045cec252cfbe0369eb4726948fa', 'reviewed pure SMT parser')
    parser = {'__name__': '_member_cold_smt'}
    exec(compile(parser_path.read_bytes(), str(parser_path), 'exec'), parser)
    return package.std_models, package.standard_vector_member_view, parser['forms']


def literal(name, path):
    matches = [node.value for node in ast.parse(path.read_bytes()).body
               if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    need(len(matches) == 1, 'one literal '+name)
    return ast.literal_eval(matches[0])


def main():
    started = time.monotonic()
    signal.alarm(90)
    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    before = census()
    models, views, forms = load_pure()
    plan = read(RAW/'plan.json')
    progress = read(RAW/'incremental.json')
    need(plan['source_commit'] == '1c45737f6cff9b43731d8da530be869a7e5d745e', 'exact selected source')
    need(plan['members'] == list(views.NAMES) == [row['member'] for row in progress['results']], 'all32 exact four-type/eight-member census')
    source_pins = []
    for row in plan['source_pins']:
        current = pin(PROJECT/row['relative'])
        need(current['sha256'] == row['sha256'], 'current selected production/source bytes')
        source_pins.append(current)
    method_path = RAW/'library/methods/wp-vector-member-source-v1.yaml'
    need(pin(method_path)['sha256'] == plan['method_sha256'], 'immutable public method bytes')
    method = yaml.safe_load(method_path.read_bytes())
    need(method['id'] == views.METHOD and method['evidence_kind'] == 'contract_fixture', 'opt-in qualified fixture method')
    need(method['c_lowering']['translators'][-1] == views.identity(), 'exact source translator')
    wp = next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')
    need(wp['flags'] == ['-wp', '-wp-rte', '-wp-cache', 'none', '-wp-model', '+real', '-wp-par', '1',
         '-machdep', 'x86_64', '-rte-initialized', '@all', '-wp-no-filter-init', '-wp-out',
         str(RAW/'native-working'), '-wp-print', '-wp-proof-trace'], 'full normal prospective WP flags')
    headers = literal('HEADERS', PROJECT/'swdb/c_lowering.py')
    check_source = ast.parse((PROJECT/'swdb/proof_setup.py').read_bytes())
    names = []
    for node in check_source.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'CHECK_SOURCES' for target in node.targets):
            names += ast.literal_eval(node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == 'CHECK_SOURCES':
            names += ast.literal_eval(node.value)
    current_check = {'version': '1', 'sha256': digest([
        {'path': 'swdb/'+name, 'sha256': pin(PROJECT/'swdb'/name)['sha256']} for name in names]+[
        {'path': 'vocab/'+name, 'sha256': pin(PROJECT/'vocab'/name)['sha256']}
        for name in ('proof_failure_classes.yaml', 'proof_subject_kinds.yaml')])}
    totals = collections.Counter()
    all_support, all_defs, all_decls = {}, {}, {}
    rows = []
    for item in progress['results']:
        name = item['member']
        leaf = RAW/name
        resource = read(leaf/'resources.json')
        need(resource == item['resources'] and resource['exit_code'] == 0 and not resource['out_of_memory'] and not resource['timed_out']
             and resource['peak_rss_bytes'] <= 8*1024**3 and resource['wall_seconds'] < 240, 'healthy actual public leaf resources')
        public = read(leaf/'public.log')
        record = public['record']
        need(public['path'] == 'proofs/'+record['id']+'.yaml', 'exact public records-relative output path')
        ypath = RAW/'records'/public['path']
        need(ypath == RAW/'records/proofs'/(record['id']+'.yaml') and yaml.safe_load(ypath.read_bytes()) == record,
             'authoritative physical YAML equals complete public JSON')
        need(record['id'] == item['record_id'] and record['verdict'] == item['verdict'] == 'proven', 'actual fresh public record')
        view = views.wp_view(name, models.model_text(name))
        need(views.check_record(name, record) == view.certificate, 'current public source/type/domain qualification')
        need(record['evidence_kind'] == 'contract_fixture' and record['pins']['summaries'] == [], 'no caller, opaque callee or production-evidence promotion')
        need(record['proof_setup_check']['verdict'] == 'passed' and record['proof_setup_check']['check'] == current_check
             and record['verdict_reading'] == {'check': current_check, 'verdict': 'proven'}, 'current complete setup/reader source identity')
        need(record['bounds'] == {'threads': 1, 'input_size': 'unbounded'}, 'normal unbounded member proof')
        settings = record['settings']
        flags = wp['flags']+['-machdep', 'x86_64', '-wp-prover', 'alt-ergo,z3,cvc5', '-wp-timeout', '30', '-wp-par', '1', '-wp-smoke-tests', '-wp-fct='+name]
        need(settings['flags'] == flags and settings['session'] == 'fresh' and settings['environment_removed'] == []
             and settings['rss_cap_bytes'] == 8*1024**3 and settings['verifier_launched'] is True, 'complete actual flags/environment/lane settings')
        need(record['pins']['method_version'] == {'id': views.METHOD, 'sha256': plan['method_sha256']}, 'selected method pin')
        run = RAW/'runs'/record['id']
        evidence = [record['evidence']['adapter_log'], *record['evidence']['reports']]
        for report in evidence:
            path = Path(report['path'])
            need(path.is_relative_to(run) and pin(path)['sha256'] == report['sha256'], 'every retained report physical hash')
        reports = {report['name']: Path(report['path']) for report in record['evidence']['reports']}
        need(set(reports) == {'standard_vector_member_original', 'standard_vector_member_view_certificate',
             'wp_input', 'wp_log', 'wp_goals', 'wp_properties', 'wp_inventory', 'wp_normalized'}, 'complete original/generated/native report census')
        original = '\n'.join([*headers, view.original])+'\n'
        need(reports['standard_vector_member_original'].read_text() == original
             and read(reports['standard_vector_member_view_certificate']) == view.certificate, 'whole original source and exact contract/type view')
        base = ('\n'.join([*headers, view.text])+'\n').encode()
        pointer = settings['pointer_bounds']
        need(pointer['qualified_standard_vector_member'] == view.certificate and pointer['source_sha256'] == sha(base), 'actual pointer-origin source/domain binding')
        edits = {}
        for index, site in enumerate(pointer['sites'], 1):
            need(site['function'] == name and 0 <= site['offset'] < len(base), 'pointer check actual body owner/offset')
            edits.setdefault(site['offset'], []).append(f"/*@ assert swdb_model_pointer_formation_{index}: {site['predicate']}; */\n")
        generated = base
        for offset in sorted(edits, reverse=True):
            generated = generated[:offset]+''.join(edits[offset]).encode()+generated[offset:]
        need(reports['wp_input'].read_bytes() == generated, 'complete original view plus only recorded pointer assertions')
        need(view.certificate['original_contract_sha256'] == view.certificate['view_contract_sha256']
             and view.certificate['acsl_input_premises_added'] == [], 'original contracts unchanged; no added ACSL antecedent')
        if view.member == 'at':
            need(generated.count(b'assert at_guard_false:') == 1 and b'SWDB_MODEL_FAIL' not in generated, 'defensive at guard remains a separate ordinary obligation')
        log = reports['wp_log'].read_text()
        native = read(reports['wp_inventory'])
        ordinary = read(reports['wp_goals'])
        native_goals = {goal['goal']: goal for goal in native['goals']}
        ordinary_goals = {goal['goal']: goal for goal in ordinary}
        record_goals = {goal['goal']: goal for goal in record['goals']}
        need(len(native_goals) == len(native['goals']) and set(native_goals) == set(record_goals)
             and set(ordinary_goals) <= set(native_goals), 'complete unique native/JSON/record goal census')
        closure = native['property_closure']
        properties = {row['property']: row for row in native['properties']}
        need(native['complete'] is True and len(properties) == len(native['properties']) == closure['initial_registered_snapshot_count']
             == closure['registered_snapshot_count'] == closure['exported_count']
             and closure['unregistered_status_lookup_performed'] is False and closure['unregistered_wp_smoke_properties'] == []
             and closure['unregistered_wp_call_instances'] == [], 'complete actual registered property context')
        need(all(row['origin'] is None and row['extern'] is False and row['generated_smoke_failure'] is False
             and set(row['dependencies']) <= set(properties) for row in properties.values()), 'no Extern/origin/opaque dependency; full local property graph')
        for goal in native_goals.values():
            need(goal['function'] == name and goal['property'] in properties and goal['passed'] is True,
                 'every native body/smoke goal healthy')
            peer = record_goals[goal['goal']]
            need(peer['property'] == goal['property'] and peer['function'] == name and peer['status'] == 'valid'
                 and peer['smoke'] == goal['smoke'], 'actual record/native identity')
            if goal['smoke']:
                need('valid' not in goal['results'] and 'failed' not in goal['results'] and goal['targets']
                     and set(goal['targets']) <= set(properties), 'healthy nonproof smoke not a Valid ordinary theorem')
            else:
                need(goal['results'] == ['valid'], 'every ordinary native goal directly Valid')
            if goal['goal'] not in ordinary_goals:
                need(not goal['smoke'] and goal['property'] in {name+'_terminates', name+'_exits'}
                     and peer['source'] == 'wp_inventory', 'only CFG termination/exit inventory-only goals')
        printed = re.findall(r'(?m)^Goal (.*?)\n(.*?)(?=^Goal |\Z)', log, re.S)
        need(len(printed) == len(ordinary), 'all ordinary/smoke contexts printed and retained')
        csv_rows = list(csv.reader(io.StringIO(reports['wp_properties'].read_text()), delimiter='\t'))
        need(csv_rows[0] == ['directory', 'file', 'line', 'function', 'property kind', 'status', 'property']
             and all(row[3] == name and row[5] in {'Valid', 'Ignored'} for row in csv_rows[1:])
             and sum(row[5] == 'Ignored' for row in csv_rows[1:]) == 1, 'complete CSV; sole original requires is a premise, not an ordinary proof')
        relocation = read(leaf/'native-relocation.json')
        archive = leaf/'retained-native'
        need(relocation['actual_original_WP_output'] == str(RAW/'native-working')
             and relocation['retained_archive'] == str(archive) and relocation['exact_bytes_before_after_move'] is True, 'exact per-generation relocation record')
        actual_files = [path for path in sorted(archive.rglob('*')) if path.is_file()]
        need([str(path.relative_to(archive)) for path in actual_files] == [row['relative'] for row in relocation['files']]
             and len(actual_files) == item['native_files_preserved'], 'all per-generation native files retained exactly once')
        task_rows, by_goal = [], collections.Counter()
        for path, wanted in zip(actual_files, relocation['files']):
            raw = path.read_bytes()
            need(len(raw) == wanted['bytes'] and sha(raw) == wanted['sha256'], 'actual native relocation bytes/digest')
            need(path.suffix in {'.smt2', '.psmt2'}, 'every archived file is an actual SMT task')
            stem = path.name.split('_Why3_')[0]
            ident = 'typed_real_'+stem
            need(ident in native_goals, 'task filename actual complete native owner')
            by_goal[ident] += 1
            commands = forms(raw.decode())
            need(commands and all(isinstance(command, list) and command for command in commands), 'complete parsed SMT command stream')
            assertions = [command[1] for command in commands if command[0] == 'assert' and len(command) == 2]
            need(assertions and sum(command[0] == 'assert' for command in commands) == len(assertions)
                 and sum(command == ['check-sat'] for command in commands) == 1, 'all assertions and sole actual query captured')
            supports = [digest(value) for value in assertions[:-1]]
            for value, key in zip(assertions[:-1], supports):
                all_support.setdefault(key, {'occurrences': 0, 'symbols': sorted(set(re.findall(r'[A-Za-z_][\w.]*', json.dumps(value))))})['occurrences'] += 1
            definitions = [command for command in commands if command[0] == 'define-fun']
            declarations = [command for command in commands if str(command[0]).startswith('declare-')]
            for command in definitions:
                all_defs.setdefault(digest(command), {'name': command[1], 'occurrences': 0})['occurrences'] += 1
            for command in declarations:
                all_decls.setdefault(digest(command), {'kind': command[0], 'name': command[1] if isinstance(command[1], str) else None, 'occurrences': 0})['occurrences'] += 1
            task_rows.append({'relative': str(path.relative_to(RAW)), 'sha256': sha(raw), 'native_goal': ident,
                              'smoke': native_goals[ident]['smoke'], 'command_count': len(commands),
                              'commands': [{'kind': command[0], 'sha256': digest(command)} for command in commands],
                              'support_assertions': supports, 'final_goal_assertion_sha256': digest(assertions[-1]),
                              'source_driver_formula_equivalence_independently_established': False})
        for goal in ordinary:
            external = [row for row in goal['provers'] if row['prover'] != 'qed']
            need(by_goal[goal['goal']] == (3 if goal['smoke'] else 1 if external else 0), 'no missing noninternal solver task, all smoke solver tasks retained')
        setup = record['proof_setup_check']
        need(setup['hashes']['run_plan'] == digest({'bounds': None, 'budget_seconds': 180.0,
             'defines': [], 'function': name, 'contract': 'c_model.'+name,
             'contract_sha256': view.certificate['original_text_sha256']}), 'complete public job-plan hash and float budget source type')
        adapter_log = (run/'adapter.log').read_text()
        invocation = shlex.split(next(line[9:] for line in adapter_log.splitlines() if line.startswith('command: ')))
        expected_command = ['opam', 'exec', '--switch=framac-33', '--', 'frama-c', '-machdep', 'x86_64',
            'wp_input.c', '-print', '-ocode', 'wp-normalized.c', '-then', *flags,
            '-wp-report-json', 'wp-goals.json', '-then', '-load-module', str(run/'scratch/proof_report.cmxs'),
            '-report', '-report-untried', '-report-csv', 'wp-properties.csv']
        need(invocation == expected_command and len(setup['runs']) == 1, 'entire actual prelaunch command reconstructed')
        srun = setup['runs'][0]
        need(srun['verdict'] == 'passed' and srun['tool'] == 'wp' and srun['run_plan_sha256'] == digest({
             'command': invocation, 'flags': flags, 'inputs': srun['hashes'], 'bounds': None,
             'method_version': record['pins']['method_version']}), 'entire generated prelaunch plan hash')
        for filename, report_name in [('wp_input.c', 'wp_input'), ('standard_vector_member_original.c', 'standard_vector_member_original'),
                                      ('standard_vector_member_view.json', 'standard_vector_member_view_certificate')]:
            need(setup['hashes'][filename] == srun['hashes'][filename] == pin(reports[report_name])['sha256'], 'all prelaunch original/view/input physical hashes')
        need(srun['hashes']['standard_vector_member_view'] == record['pins']['standard_vector_member_view_certificate']['sha256']
             and srun['hashes']['compiler_runtime'] == digest(settings['compiler_runtime']), 'prelaunch certificate/runtime binds full current record')
        totals.update(records=1, ordinary=sum(not goal['smoke'] for goal in native_goals.values()),
                      smokes=sum(goal['smoke'] for goal in native_goals.values()), properties=len(properties),
                      printed_contexts=len(printed), CSV_rows=len(csv_rows)-1, tasks=len(task_rows),
                      inventory_only=len(native_goals)-len(ordinary))
        rows.append({'member': name, 'element': view.element, 'record_id': record['id'], 'record_yaml': pin(ypath),
                     'ordinary': sum(not goal['smoke'] for goal in native_goals.values()),
                     'healthy_nonproof_smokes': sum(goal['smoke'] for goal in native_goals.values()),
                     'native_properties': native['properties'], 'native_goals': native['goals'],
                     'printed_contexts': [{'heading': heading, 'body_sha256': sha(body.encode())} for heading, body in printed],
                     'CSV_statuses': [row[5] for row in csv_rows[1:]], 'native_tasks': task_rows,
                     'source_and_type_qualification': view.certificate, 'actual_resources': resource,
                     'assumptions': record['assumptions'], 'compiler_runtime': settings['compiler_runtime']})
    need(totals['records'] == 32 and totals['tasks'] == 212, 'complete exact actual32/task212 census')
    after = census()
    need(before == after and not ATTEMPTS, 'raw complete physical content pre/post unchanged, zero external attempts')
    result = {'date': '2026-10-16 ET', 'classification': 'PASS_32_QUALIFIED_PUBLIC_BODY_RECORD_SOURCE_TASK_CENSUS',
              'scope': 'Thirty-two nonallocating original C member bodies under explicit typed contiguous storage and normal Frama-C/WP standard theory/driver/solver TCB. This is no source C++ caller/domain discharge or independent theorem reconstruction.',
              'source_commit': plan['source_commit'], 'raw_root': str(RAW), 'raw_manifest': before,
              'raw_manifest_sha256': digest(before), 'raw_pre_post_equal': True,
              'source_pins': source_pins, 'method': pin(method_path), 'totals': dict(totals), 'members': rows,
              'complete_task_support_assertions': all_support, 'complete_task_definitions': all_defs,
              'complete_task_declarations': all_decls, 'checks': CHECKS,
              'external_native_network_attempts': ATTEMPTS, 'elapsed_seconds': time.monotonic()-started,
              'qualified_public_body_record_census_accepted': True,
              'boundaries': ['Original model version2 remains immutable; only the32 named nonallocating members are covered.',
                  'All ordinary native goals are Valid; healthy smoke timeout/unknown never proves consistency, source-state satisfiability or an ordinary theorem.',
                  'All212 original archived task bytes and every support/definition/declaration are retained and indexed. Source-to-driver formula equivalence and primary-source attribution of every standard theory assertion were not independently reconstructed in this audit; they remain explicit normal WP/compiler/driver/foundation TCB.',
                  'Method uses normal installed Frama-C/WP33 and solver binaries through opam. Full historical package/Python/native dependency/loader closure, source-to-binary correctness, actual solver-consumed bytes and continuous before/after runtime immutability are not established by record pins or this passive audit.',
                  'The compiler-runtime header aggregate is recorded at use. This audit does not reproduce all1982 header bytes, libclang binding, SDK closure, preprocessing/machdep correspondence or historical parse behavior.',
                  'Printed internal-Qed contexts and termination/exit inventory-only CFG results remain normal trusted WP/Qed/CFG results, not standalone independently checked SMT proofs.',
                  'Qualified typed input domain is not admitted for an arbitrary incoming C/C++ pointer. Generic source caller, default-model integration, construction/reallocation/move/swap/destruction, element payload computation and full ticket25 acceptance remain open.'],
              'source_cpp_caller_admission': False, 'general_member_dependency_admission': False,
              'full_support_primary_source_interpretation_complete': False, 'full_runtime_closure_attested': False,
              'full_ticket25_acceptance': False}
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'decision': pin(OUT), 'totals': dict(totals), 'checks': CHECKS}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        result = {'date': '2026-10-16 ET', 'classification': 'REFUSED_MEMBER32_COLD_AUDIT',
                  'error': type(error).__name__+': '+str(error), 'checks': CHECKS,
                  'external_attempts': ATTEMPTS, 'no_scientific_adoption': True}
        OUT.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
        print(json.dumps(result))
        raise SystemExit(1)
