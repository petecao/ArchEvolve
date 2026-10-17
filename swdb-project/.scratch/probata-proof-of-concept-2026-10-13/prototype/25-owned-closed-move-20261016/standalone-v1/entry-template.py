"""2026-10-16 ET. Inert complete original-C move WP observation.

This deliberately calls the normal engine/report reader without creating a
framework proof record. It never changes the ordinary public lifetime gate.
The source commit and physical consumer pins must be frozen after root publishes
the shared checkpoint. Do not run this unmaterialized template.
"""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time


COMMIT = '__ROOT_PUBLISHED_SOURCE_COMMIT__'
SOURCE_PINS = ()  # materializer fills the complete selected physical consumers
OUTPUT = '__FRESH_ABSOLUTE_MAC_OUTPUT__'
FUNCTION = 'vector_owned_move_capture'
METHOD = 'method.wp-vector-owned-move-original-c-diagnostic-v1'
SOURCE = 'tests/fixtures/proof/lowering/vector_owned_transfer.cc'
SOURCE_SHA = 'a0dc043284f96a5b7c052963b51188318ae4abc6a85ee347fea78b6ab392d3a2'
LOWERED_SHA = '5c33a1a1843045d0b9d2ba43eb8d590c9e6106c794982286b28505c64e896e34'
CLAUSES = (r'requires 0 <= n;', r'assigns \nothing;', r'ensures \result == (n > 0 ? 7 : 0);')
CAP = 8*1024**3
WHOLE = 600
NATIVE_SECONDS = 420
BUDGET = 128*1024**2
FINAL_HEADROOM = 256*1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def normal_flags(tools):
    # Exact WpAdapter._wp settings construction, with its sole source root.
    # Heap check-lemma flags would append another relative -wp-out and are
    # deliberately not used for this original C caller observation.
    selected = any(flag == '-wp-prover' or flag.startswith('-wp-prover=') for flag in tools['flags'])
    return [*tools['flags'], '-machdep', 'x86_64',
            *([] if selected else ['-wp-prover', ','.join(tools['provers'])]),
            '-wp-timeout', str(tools['seconds']), '-wp-par', '1', '-wp-smoke-tests',
            '-wp-fct='+FUNCTION]


def need(value, reason):
    if not value:
        raise ValueError(reason)


def extent(root, *, active=False):
    """Only this fresh private TMPDIR admits transient sockets/disappearance.

    All final settled paths must be regular files or physical directories.
    Links, unknown specials and races outside that exact scratch root refuse.
    """
    root = Path(root)
    scratch = root/'wp/tmp'
    total = 0
    todo = [root]
    while todo:
        directory = todo.pop()
        try:
            entries = list(os.scandir(directory))
        except FileNotFoundError:
            if active and directory.is_relative_to(scratch):
                continue
            raise
        for entry in entries:
            path = Path(entry.path)
            try:
                mode = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                if active and path.is_relative_to(scratch):
                    continue
                raise
            if stat.S_ISDIR(mode.st_mode):
                todo.append(path)
            elif stat.S_ISREG(mode.st_mode):
                total += mode.st_size
            elif not (active and path.is_relative_to(scratch) and stat.S_ISSOCK(mode.st_mode)):
                raise ValueError('unexpected linked/special observation artifact: '+str(path))
    return total


def write(root, path, raw, *, reserve=True):
    need(type(raw) is bytes and len(raw) <= 8*1024**2, 'bounded metadata/source write required')
    need(extent(root) + len(raw) <= BUDGET-(FINAL_HEADROOM if reserve else 0),
         'whole observation output budget exceeded')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


class OutputWatch:
    def __init__(self, root, kill_children):
        self.root, self.kill_children = root, kill_children
        self.stop = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def loop(self):
        while not self.stop.is_set():
            try:
                need(extent(self.root, active=True) <= BUDGET-FINAL_HEADROOM,
                     'active aggregate observation extent exceeded')
            except Exception as error:
                self.error = type(error).__name__+': '+str(error)
                self.kill_children()
                return
            self.stop.wait(.1)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *unused):
        self.stop.set()
        self.thread.join()


def complete_census(inventory, standard):
    """Inventory every row; interpretation/owner discrepancies remain visible.

    No row is filtered or relabeled, and no normal-reader verdict is changed.
    Exact source/call-site and full term/support interpretation follows cold.
    """
    need(inventory.get('complete') is True and inventory.get('version') == '1',
         'complete fresh native inventory required')
    native, properties = inventory['goals'], inventory['properties']
    need(type(native) is list and type(properties) is list and type(standard) is list,
         'complete native/property/standard lists required')
    by_native = {row['goal']: row for row in native}
    by_standard = {row['goal']: row for row in standard}
    by_property = {row['property']: row for row in properties}
    need(len(by_native) == len(native) and len(by_standard) == len(standard)
         and len(by_property) == len(properties) and native and standard
         and set(by_standard) <= set(by_native), 'unique complete report goal/property identities required')
    need(all(row['property'] in by_property for row in native),
         'native goal has no physical property')
    missing = sorted({dep for row in properties for dep in row['dependencies'] if dep not in by_property})
    origins = sorted({row['origin'] for row in properties
                      if row['origin'] is not None and row['origin'] not in by_property})
    need(not missing and not origins, 'complete property origin/dependency closure required')
    return {'native_goals': len(native), 'ordinary': sum(not row['smoke'] for row in native),
            'smokes': sum(bool(row['smoke']) for row in native), 'properties': len(properties),
            'standard_goals': len(standard),
            'inventory_only_goal_ids': sorted(set(by_native)-set(by_standard)),
            'native_standard_pairs': [{'goal': name, 'native': by_native[name], 'standard': by_standard[name]}
                                      for name in sorted(by_standard)],
            'all_properties': properties, 'all_native_goals': native,
            'missing_dependencies': missing, 'missing_origins': origins,
            'source_call_site_term_hypothesis_and_import_interpretation': 'pending independent complete cold review',
            'source_or_caller_admission': False}


def main():
    need(len(COMMIT) == 40 and SOURCE_PINS and OUTPUT.startswith('/private/tmp/'),
         'unmaterialized diagnostic template must never execute')
    started = time.monotonic()
    deadline = started+WHOLE
    project = Path(__file__).resolve().parents[5]
    out = Path(OUTPUT)
    need(not os.path.lexists(out) and out.parent.resolve() == out.parent
         and shutil.disk_usage(out.parent).free >= 20*1024**3,
         'fresh canonical external output with full headroom required')
    def git(*args):
        return subprocess.check_output(['git', '--no-optional-locks', '--no-replace-objects',
            '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false', '-c', 'index.threads=1',
            '-C', str(project), *args], timeout=30)
    def source_check():
        need(git('rev-parse', 'HEAD').decode().strip() == COMMIT, 'selected source commit changed')
        for row in SOURCE_PINS:
            path = project/row['relative']
            need(not path.is_symlink() and path.is_file(), 'physical source consumer required')
            raw = path.read_bytes()
            need(len(raw) == row['bytes'] and sha(raw) == row['sha256']
                 and raw == git('show', COMMIT+':swdb-project/'+row['relative']),
                 'selected physical source consumer differs: '+row['relative'])
    def remaining(maximum):
        left = deadline-time.monotonic()
        need(left > 0, 'whole original-C diagnostic budget spent')
        return min(maximum, left)
    source_check()
    need(not any(name.startswith(('FRAMAC_WP', 'WP_')) or name in
        {'SWDB_FRAMA_C', 'SWDB_OCAMLFIND', 'SWDB_VERIFIER_LOCK', 'SWDB_PROOF_REPORT_OUT'}
        for name in os.environ), 'ambient verifier/lock selector refused')
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(project), str(project/'tests')]
    import yaml
    from swdb import c_lowering, framac, heap_model_view as engine, hint_check, method_version
    from swdb import proof_setup, rss_watchdog, std_models, stdlib_provenance, verifier_lock, wp_adapter
    from swdb import vector_owned_move_source as rule
    from swdb.library import Library
    from testkit.standard_library import method_version as standard_method
    out.mkdir(mode=0o700)
    signal.alarm(WHOLE)
    result = {'created': '2026-10-16 ET', 'source_commit': COMMIT, 'producer_complete': False,
        'diagnostic_only': True, 'public_gate_refusal_unchanged': True, 'public_proof_record_created': False,
        'source_Heap_Typed_lifetime_body_caller_or_default_admission': False}
    def kill_children():
        for pid in rss_watchdog.tree(os.getpid()):
            if pid != os.getpid():
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    watch = OutputWatch(out, kill_children)
    try:
        with verifier_lock.hold('standalone original closed int move diagnostic') as held, watch:
            write(out, out/'lock.json', encoded(held))
            source = project/SOURCE
            need(sha(source.read_bytes()) == SOURCE_SHA, 'complete original source changed')
            compiler = stdlib_provenance.runtime_identity(c_lowering.locate())
            lowering_identity = c_lowering.identity()
            original = c_lowering.lower(source, FUNCTION)
            need(original.sha256 == LOWERED_SHA, 'exact original full C differs')
            problem = stdlib_provenance.check(original.stdlib_provenance, c_lowering.locate(), source,
                models=tuple(sorted(set((*original.models, *original.std_models)))),
                substitutions=original.stdlib_substitutions)
            need(not problem, 'fresh original-TU library certificate refused: '+str(problem))
            source_plan, canonical = rule.declaration(original, source, CLAUSES)
            need(source_plan['source_grammar']['lowering_sha256'] == LOWERED_SHA,
                 'public original source-rule inverse changed')
            for name, raw in canonical.items():
                write(out, out/'source-rule'/name, raw)
            write(out, out/'original-anchors.json', original.anchors_json.encode())
            write(out, out/'compiler-use-time.json', encoded({'runtime': compiler,
                'lowering_identity': lowering_identity, 'scope': 'fresh original lowering use-time certificate; no continuous loader/interposition guarantee'}))
            block = '/*@ '+'\n    '.join(CLAUSES)+' */'
            merged = hint_check.wp_base(original.text, original.anchors, {FUNCTION+'.contract': [block]})
            write(out, out/'original-contract.json', encoded({'clauses': CLAUSES,
                'caller_requires_added': [], 'full_original_lowering_sha256': LOWERED_SHA,
                'wp_input_sha256': sha(merged.encode()), 'view_or_inline_edits': []}))
            methods = out/'library/methods'
            methods.mkdir(parents=True)
            data = standard_method(lowering_identity)
            data.update(id=METHOD, sequence=5, status='draft', created='2026-10-16',
                description='Complete original-C move normal WP observation; no source or framework admission.')
            data['models']['std_vector'] = std_models.identity()
            entry = next(row for row in data['lineup'] if row['tool'] == 'frama-c-wp')
            entry['flags'] += ['-wp-out', str(out/'retained-native'), '-wp-print', '-wp-proof-trace',
                '-wp-msg-key', 'print-generated,why3:compile,why3:import,prover:pp_task']
            write(out, methods/'wp-vector-owned-move-original-c-diagnostic-v1.yaml', yaml.safe_dump(data, sort_keys=False).encode())
            method = method_version.select(out/'library', METHOD)
            adapter = wp_adapter.WpAdapter(Library(out/'library'), 'standalone-original-closed-move', method)
            tools = adapter._tools()
            flags = normal_flags(tools)
            need(tools['seconds'] == 30 and tools['provers'] == ['alt-ergo', 'z3', 'cvc5']
                 and not any(flag.startswith(('-wp-prop', '-wp-fct')) or flag == '-wp-gen' for flag in tools['flags']),
                 'unchanged normal portfolio and all ordinary/RTE/init/smoke flags required')
            proof_setup._lineup(method, adapter, tools, flags)
            write(out, out/'method.json', encoded({'pin': method_version.pin(method),
                'method': data, 'tools': tools, 'flags': flags}))
            reader_dir = out/'reader'
            reader_dir.mkdir()
            reader = proof_setup.compile_report_module(reader_dir, timeout=remaining(120))
            write(out, out/'foundation.json', encoded(engine.foundations(framac.locate().command,
                out/'foundation', deadline)))
            directory = out/'wp'
            (directory/'tmp').mkdir(parents=True)
            write(out, directory/'wp_input.c', merged.encode())
            command = [*framac.locate().command, '-machdep', 'x86_64', 'wp_input.c', '-print',
                '-ocode', 'wp-normalized.c', '-then', *flags,
                '-wp-report-json', 'wp-goals.json', '-then', '-load-module', str(reader),
                '-report', '-report-untried', '-report-csv', 'wp-properties.csv']
            proof_setup._wp_flags(command, directory)
            proof_setup._lineup(method, adapter, tools, flags)
            write(out, directory/'command.json', encoded({'argv': command, 'cwd': str(directory),
                'timeout_seconds': remaining(NATIVE_SECONDS), 'input': pin(directory/'wp_input.c')}))
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                TMPDIR=str(directory/'tmp'), SWDB_PROOF_REPORT_OUT=str(directory/'wp-inventory.json'),
                SWDB_VERIFIER_RSS_CAP_BYTES=str(CAP))
            observed = rss_watchdog.run(command, log=directory/'frama-c.log', cwd=directory,
                env=environment, cap_bytes=CAP, timeout=remaining(NATIVE_SECONDS))
            resources = dataclasses.asdict(observed)
            write(out, directory/'resources.json', encoded(resources))
            result['native_resources'] = resources
            need(watch.error is None and not observed.timed_out and not observed.out_of_memory,
                 'native output/RSS/whole-wall guard refused')
            for name in ('wp-goals.json', 'wp-properties.csv', 'wp-inventory.json', 'wp-normalized.c'):
                need((directory/name).is_file(), 'complete original native reports absent: '+name)
            census = complete_census(json.loads((directory/'wp-inventory.json').read_bytes()),
                                     json.loads((directory/'wp-goals.json').read_bytes()))
            need(census['ordinary'] > 0, 'complete original ordinary census required')
            write(out, directory/'complete-census.json', encoded(census))
            allocator = {name: {'id': name, 'sha256': sha(text.encode())}
                         for name, text in std_models.allocator('int')}
            write(out, out/'modular-hypothesis-boundary.json', encoded({
                'allocator_only_normal_reader_TCB': allocator,
                'all_original_models': [{'name': name, 'sha256': sha(std_models.model_text(name).encode())}
                                        for name in original.models],
                'no_new_extern_or_constructor_whitelist': True,
                'conditional_model_poststates_not_source_ownership_or_nonvacuity': True}))
            try:
                outcome = wp_adapter.read_outcome(observed, (directory/'frama-c.log').read_text(errors='replace'),
                    directory/'wp-goals.json', directory/'wp-properties.csv',
                    inventory=directory/'wp-inventory.json', extern_contracts=allocator)
                write(out, directory/'normal-outcome.json', encoded(outcome))
                result['normal_outcome'] = {key: outcome[key] for key in ('verdict', 'failure_class', 'why')}
            except wp_adapter.AdapterError as error:
                result['normal_reader_refusal'] = str(error)
                write(out, directory/'normal-reader-refusal.json', encoded({'type': type(error).__name__, 'message': str(error)}))
            need(observed.exit_code == 0, 'native compiler/solver session failed; partial evidence preserved')
            source_check()
            rule.declaration(original, source, CLAUSES)
            need(sha((directory/'wp_input.c').read_bytes()) == sha(merged.encode()),
                 'complete original contract input changed')
            result.update(producer_complete=True, ordinary=census['ordinary'], smokes=census['smokes'],
                native_goals=census['native_goals'], properties=census['properties'],
                native_tasks=sorted(str(p.relative_to(out)) for p in (out/'retained-native').rglob('*')
                    if p.is_file() and p.suffix in {'.smt2', '.psmt2'}),
                interpretation='Complete original normal engine observation; ordinary reader refusal or not_proven is preserved. Source/task/hypothesis/import and exact source-rule discharge remain separately pending.')
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    finally:
        result.update(elapsed_seconds=time.monotonic()-started, output_guard_error=watch.error)
        result['within_whole_budget'] = result['elapsed_seconds'] <= WHOLE
        write(out, out/'result.json', encoded(result), reserve=False)
        manifest = [{'relative': str(p.relative_to(out)), **pin(p)} for p in sorted(out.rglob('*')) if p.is_file()]
        write(out, out/'artifact-manifest.json', encoded(manifest), reserve=False)
        need(extent(out) <= BUDGET, 'complete settled output exceeds aggregate cap')
        signal.alarm(0)
    print(json.dumps({'output': str(out), 'producer_complete': result['producer_complete'],
        'normal_outcome': result.get('normal_outcome'), 'normal_reader_refusal': result.get('normal_reader_refusal'),
        'error': result.get('error'), 'ordinary': result.get('ordinary'), 'smokes': result.get('smokes'),
        'source_or_caller_admission': False}, sort_keys=True), flush=True)
    return 0 if result['producer_complete'] and result['within_whole_budget'] and watch.error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
