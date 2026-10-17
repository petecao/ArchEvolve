"""2026-10-16 ET. Inert six-duty closed source/lifetime normal-WP profile.

Fresh public prepare/check plus unchanged normal command, flag/lineup policies,
native reader and outcome reading. No admitted model/View, public proof record,
universal setup attestation, source correspondence or caller acceptance.
"""
import argparse
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

EXPECTED_SHA256 = 'a10f2ee5864b8c39c22e72b29f34e3195b59839e0fdc9a6ae9e5c6c5f7ecd4b2'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pin(p):return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}


def write(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def surface(root,rows):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('selected import root changed')
    found=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonregular import input')
        if p.is_file():found.append({'relative':str(p.relative_to(root)),'sha256':sha(p)})
    if found!=rows:raise ValueError('selected full import-tree membership/hash differs: '+str(root))


def linux_admission(expected,repo,out):
    raw_value=os.environ.get('PROBATA_OUTPUT')
    if not raw_value:raise ValueError('Linux coordinator PROBATA_OUTPUT marker required')
    root=Path(raw_value).resolve()
    if root!=out.parent.resolve():raise ValueError('Linux output marker differs from exact profile root')
    if os.environ.get('SWDB_VERIFIER_LOCK')!=str(root/'verifier.lock') or os.environ.get('SWDB_VERIFIER_RSS_CAP_BYTES')!='8589934592':
        raise ValueError('Linux lock/cap context differs from reviewed wrapper')
    launch_path=root/'launch.json';launch=json.loads(launch_path.read_bytes());policy=expected['resource_policy']
    if Path(launch['source']).resolve()!=repo.resolve() or launch.get('source_commit')!=expected['source_commit']:
        raise ValueError('Linux launch source differs from selected immutable source')
    if launch.get('rss_cap_bytes')!=policy['cap_bytes'] or launch.get('workers')!=1 or launch.get('timeout_seconds')!=policy['root_whole_seconds']:
        raise ValueError('Linux launch whole-worker budget differs')
    command=launch.get('command',[]);binding=expected['linux_launch_binding']
    prefix=[expected['tools']['opam']['path'],'exec','--switch=framac-33','--',binding['python'],'-c']
    if command[:6]!=prefix or len(command)!=9 or command[-2:]!=[str(repo/'swdb-project'),str(root)]:
        raise ValueError('Linux admitted entry command boundary differs')
    # Root's reviewed bootstrap embeds exact entry/expectation bytes and digest
    # literals; it stages them outside source then execs this immutable entry.
    code=command[6]
    if 'ENTRY_SHA256 = '+repr(sha(__file__)) not in code or 'EXPECTED_SHA256 = '+repr(EXPECTED_SHA256) not in code:
        raise ValueError('Linux launch does not bind exact entry/expected byte hashes')
    for name,wanted in binding['wrappers'].items():
        if launch.get('reviewed_wrapper_reuse',{}).get(name)!=wanted or sha(root/name)!=wanted:
            raise ValueError('Linux outer wrapper bytes differ')
    return {'marker_path':str(root),'launch':pin(launch_path),'command_sha256':hashlib.sha256(json.dumps(command,separators=(',',':')).encode()).hexdigest(),
            'source_commit':expected['source_commit'],'rss_cap_bytes':policy['cap_bytes'],'whole_seconds':policy['root_whole_seconds'],
            'lock_path':str(root/'verifier.lock'),'scope':binding['scope'],'Mac_counted_token_required':False}


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
    if found!={r['relative']for r in wanted}:raise ValueError('source consumer physical membership differs from selected exact source Git tree')
    # hash-object streams physical files and emits only40-byte object names.
    # It never captures the1.33GB catalog body or invokes a content filter.
    physical_oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n'for r in wanted).encode()).decode().splitlines()
    if physical_oids!=[r['git_blob']for r in wanted]:raise ValueError('source consumer physical bytes differ from selected immutable source Git blob')
    for row in wanted:
        p=Path(row['path']);h=hashlib.sha256()
        with p.open('rb')as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        row.update(sha256=h.hexdigest(),bytes=p.stat().st_size)
    return {'source_commit':commit,'trees':trees,'files':wanted,'count':len(wanted),
            'total_bytes':sum(r['bytes']for r in wanted),'physical_git_blob_equality':True,
            'scope':'Opaque source-byte identity only. Existing fixture helper selects/parses YAML header/reference closure; no unrelated scientific evidence or held-out source semantics inspected.'}


def initialize_workspace(out,builder):
    # The unchanged pytest seed expects its caller to supply an existing root.
    # Only this fresh parent is ours: make_records creates records; copytree
    # creates library, whose tracked methods directory already exists. The
    # ordinary public worker later creates runs-outside-repo with parents.
    root=out/'workspace';root.mkdir(exist_ok=False)
    seed=builder(root)
    if seed.root!=root or seed.records!=root/'records' or seed.runs!=root/'runs-outside-repo':
        raise ValueError('committed fixture builder returned unexpected workspace paths')
    for relative in ('records','library','library/methods'):
        path=root/relative
        if path.is_symlink() or not path.is_dir():raise ValueError('fixture directory missing/redirected: '+relative)
    for filename in ('wp-tracer-fixture.yaml','contract-fixture-1.yaml'):
        path=root/'library/methods'/filename
        if path.is_symlink() or not path.is_file():raise ValueError('fixture method missing/redirected: '+filename)
    if seed.runs.exists() or seed.runs.is_symlink():raise ValueError('fixture run output must remain fresh for the ordinary worker')
    return seed


def guarded_generation(command, directory, environment, policy, timeout, watchdog, output_root):
    """Generation guard whose every post-spawn path kills and reaps its session."""
    file_allowance = policy['output_budget_bytes']-raw_bytes(output_root)-policy['metadata_reserve_bytes']
    if file_allowance <= 0:
        raise ValueError('no raw-output allowance remains before generation')
    def setup():
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_allowance, file_allowance))

    started = time.monotonic()
    timed_out = output_limit = False
    watch = None
    descendants = {}
    primary_error = None
    with (directory/'frama-c.log').open('wb') as log:
        process = subprocess.Popen(command, cwd=directory, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=setup)
        try:
            # Snapshot before entering the watcher: __enter__ may itself fail.
            descendants = watchdog.tree(process.pid)
            watch = watchdog.TreeWatch(process.pid, policy['cap_bytes'])
            with watch:
                while process.poll() is None:
                    descendants = watchdog.tree(process.pid)
                    timed_out = time.monotonic()-started > timeout
                    output_limit = raw_bytes(output_root) > policy['output_budget_bytes']-policy['metadata_reserve_bytes']
                    if timed_out or output_limit:
                        break
                    time.sleep(0.1)
                if not timed_out and not output_limit:
                    process.wait()
            if watch.error:
                raise RuntimeError(watch.error)
        except BaseException as exc:
            primary_error = exc
            raise
        finally:
            # The child owns a new session. A callback/watch/poll/wait exception
            # must never leave it running after the outer worker returns.
            cleanup_errors = []
            try:
                descendants = {**descendants, **watchdog.tree(process.pid)}
            except BaseException as exc:
                cleanup_errors.append('final process-tree snapshot: '+type(exc).__name__+': '+str(exc))
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as exc:
                cleanup_errors.append('session kill: '+type(exc).__name__+': '+str(exc))
            for pid in descendants:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except BaseException as exc:
                    cleanup_errors.append('descendant kill: '+type(exc).__name__+': '+str(exc))
            try:
                process.wait(timeout=10)
            except BaseException as exc:
                cleanup_errors.append('reap: '+type(exc).__name__+': '+str(exc))
            if cleanup_errors:
                # Best-effort diagnostics must not replace the original error.
                try:
                    write(directory/'guard-cleanup-errors.json', {
                        'primary_error': None if primary_error is None else
                            type(primary_error).__name__+': '+str(primary_error),
                        'cleanup_errors': cleanup_errors,
                        'scope': 'Guard failure; no complete generation or resource claim'})
                except BaseException:
                    pass
                if primary_error is None:
                    raise RuntimeError('; '.join(cleanup_errors))
    return {'exit_code': process.returncode, 'peak_rss_bytes': watch.peak,
            'out_of_memory': watch.tripped, 'timed_out': timed_out,
            'output_limit': output_limit, 'wall_seconds': time.monotonic()-started}


def raw_bytes(root):
    """Count regular output files; tolerate only concurrent disappearance."""
    def scan_error(exc):
        if not isinstance(exc, FileNotFoundError):
            raise exc
    total = 0
    for directory, _subdirs, files in os.walk(root, onerror=scan_error, followlinks=False):
        for name in files:
            try:
                metadata = (Path(directory)/name).stat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(metadata.st_mode):
                total += metadata.st_size
    return total


def bounded_bytes(path, data, output_root, policy, *, reserve=True):
    """Refuse aggregate growth before writing a derived fragment or metadata."""
    try:
        previous = path.stat().st_size
    except FileNotFoundError:
        previous = 0
    reserved = policy['metadata_reserve_bytes'] if reserve else 0
    if raw_bytes(output_root)-previous+len(data)+reserved > policy['output_budget_bytes']:
        raise ValueError('projected aggregate raw-output allowance exceeded before writing '+path.name)
    path.write_bytes(data)


def bounded_json(path, value, output_root, policy, *, reserve=True):
    bounded_bytes(path, (json.dumps(value, indent=2, sort_keys=True)+'\n').encode(),
                  output_root, policy, reserve=reserve)


def lineage(anchors):
    """Host-independent source/anchor lineage; complete certificates stay retained."""
    direct = ('tool', 'function', 'c_lowering_sha256', 'anchors', 'models', 'std_models', 'allocation')
    candidate = anchors['vector_reallocation_candidate']
    keys = ('count', 'receiver', 'alias', 'reserve_request', 'observation', 'guard',
            'entry_obligations', 'call_obligations', 'scalar_read_obligation',
            'lowered_lifetime', 'source_sha256', 'lowered_sha256')
    return {**{key: anchors[key] for key in direct},
            'candidate_source_events': {key: candidate[key] for key in keys}}



def canonical_check(packets, expected, directory, original, source):
    manifest = packets.check(original, source, expected['contract_clauses'], directory)
    portable = json.loads(json.dumps(manifest))
    host_certificate = portable['source_view']['library_allocator_binding'].pop('certificate_sha256')
    if not re.fullmatch('[0-9a-f]{64}', host_certificate):
        raise ValueError('full fresh host provenance certificate digest missing')
    physical = [{'path': str(p.relative_to(directory)), 'bytes': p.stat().st_size,
                 'sha256': sha(p)} for p in sorted(directory.rglob('*')) if p.is_file() and p != directory/'manifest.json']
    if portable != expected['canonical_manifest_portable'] or physical != expected['canonical_files']:
        raise ValueError('fresh complete source-bound lifetime canonical packet differs')
    rows = manifest['obligations']
    if len(rows) != 6 or [r['id'] for r in rows] != expected['target_ids'] or any(
            r['kind'] != 'check_lemma' or r['status'] != 'pending' or r['dependencies'] for r in rows):
        raise ValueError('all six independent pending check lemmas are required')
    if manifest['source_typed_bridge_established'] is not False or \
            manifest['current_proof_records_admitted'] or manifest['caller_premises_added']:
        raise ValueError('source lifetime packet falsely broadens admission')
    return manifest


def normal_task_census(directory, target, inventory, output_root, policy):
    """Streaming metadata over retained tasks; independent term audit still required."""
    goals = inventory['goals']
    properties = inventory['properties']
    if inventory.get('complete') is not True or not goals or \
            len({g['goal'] for g in goals}) != len(goals) or \
            len({p['property'] for p in properties}) != len(properties):
        raise ValueError('native complete goal/property census missing or duplicated')
    by_property = {p['property']: p for p in properties}
    missing = sorted({d for p in properties for d in p['dependencies'] if d not in by_property})
    origins = sorted({p['origin'] for p in properties if p['origin'] is not None and p['origin'] not in by_property})
    lemmas = [p for p in properties if p.get('kind') == 'lemma']
    ordinary = [g for g in goals if not g['smoke']]
    if missing or origins or len(lemmas) != 1 or not ordinary or any(
            g['property'] != lemmas[0]['property'] for g in ordinary) or \
            not lemmas[0]['property'].endswith('_'+target['goal']) or \
            lemmas[0].get('dependencies') or lemmas[0].get('extern'):
        raise ValueError('sole source-owned independent check lemma or dependency closure differs')
    standard = json.loads((directory/'wp-goals.json').read_bytes())
    if len({g['goal'] for g in standard}) != len(standard) or \
            {g['goal'] for g in standard} != {g['goal'] for g in goals}:
        raise ValueError('complete native/standard goal census differs')
    peers = {g['goal']: g for g in standard}
    for g in goals:
        if any(g.get(k) != peers[g['goal']].get(k) for k in ('property','function','line','smoke','passed')):
            raise ValueError('native/standard goal binding differs: '+g['goal'])
    log_path = directory/'frama-c.log'
    exports = []
    current = None
    offset = line_number = 0
    marker = re.compile(rb'^\s*(?:\[wp(?::[^\]]+)?\]\s*)?EXPORT GOAL\s+(\S+)\s*$')
    declaration = re.compile(rb'^\s*(?:\[wp:print-generated\]\s*)?(use|clone|axiom|goal|constant|function|predicate|type|theory)\s+([^\s:(=]+)')
    with log_path.open('rb') as stream:
        for line in stream:
            line_number += 1
            match = marker.match(line)
            if match:
                if current is not None:
                    current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
                    exports.append(current)
                ident = match.group(1).decode()
                owners = [g['goal'] for g in goals if g['goal'].endswith('_'+ident)]
                if len(owners) != 1:
                    raise ValueError('actual common export has no unique native owner: '+ident)
                current = {'export_id': ident, 'goal': owners[0], 'begin_byte': offset,
                           'begin_line': line_number, '_hash': hashlib.sha256(),
                           'declarations': [], 'theory_seen': False, 'goal_seen': False, 'end_seen': False}
            if current is not None:
                current['_hash'].update(line)
                parsed = declaration.match(line)
                if parsed:
                    kind, name = (part.decode(errors='replace') for part in parsed.groups())
                    current['declarations'].append({'kind': kind, 'name': name, 'line': line_number,
                                                   'line_sha256': hashlib.sha256(line).hexdigest()})
                    current['theory_seen'] |= kind == 'theory'
                    current['goal_seen'] |= kind == 'goal'
                current['end_seen'] |= bool(re.match(rb'^\s*end\s*$', line))
            offset += len(line)
    if current is not None:
        current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
        exports.append(current)
    if any(not all(row[k] for k in ('theory_seen','goal_seen','end_seen')) for row in exports):
        raise ValueError('retained common task fragment is incomplete')
    exported = {row['goal'] for row in exports}
    inventory_only = [g for g in goals if g['goal'] not in exported]
    missing_tasks = [g['goal'] for g in inventory_only if not (
        g['results'] == ['valid'] and any(p['prover'] == 'qed' and p.get('success') == 1
                                       for p in peers[g['goal']].get('provers', [])))]
    census = {'target': target['id'], 'native_goal_count': len(goals),
              'native_property_count': len(properties), 'ordinary_count': len(ordinary),
              'smoke_count': sum(bool(g['smoke']) for g in goals), 'log': pin(log_path),
              'common_exports': exports, 'internal_qed_inventory_only': [g['goal'] for g in inventory_only],
              'missing_noninternal_tasks': missing_tasks,
              'extern_properties': [p['property'] for p in properties if p['extern']],
              'property_dependencies': [{'property': p['property'], 'variant': p['property_variant'],
                  'origin': p['origin'], 'dependencies': p['dependencies'], 'extern': p['extern']}
                  for p in properties],
              'scope': 'Complete actual census and declaration positions only. Original full log, prover files, native properties and CSV retained. Imported definitions/axioms/hypotheses require independent cold interpretation; no source/caller proof or automatic semantic acceptance.'}
    bounded_json(directory/'task-census.json', census, output_root, policy)
    if missing_tasks:
        raise ValueError('actual required common tasks missing; preserve partial census')
    return census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('reviewed six-duty expectation bytes differ')
    expected = json.loads(args.expected.read_bytes()); policy = expected['resource_policy']
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact immutable source and fresh external profile required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'created': '2026-10-16 ET', 'scope': expected['scope'],
              'source_commit': expected['source_commit'], 'producer_complete': False,
              'all_six_producer_proven': False, 'proof_acceptance': False,
              'source_typed_bridge_established': False, 'caller_acceptance': False,
              'body_acceptance': False, 'public_proof_record_created': False,
              'universal_proof_setup_attested': False, 'independent_task_hypothesis_review_pending': True,
              'linux_launch': launch, 'source_receipts': [], 'runs': [],
              'unexecuted': list(expected['target_ids'])}
    def remaining():
        value = deadline-time.monotonic()
        if value <= 0:
            raise TimeoutError('whole standalone profile budget spent')
        return value
    def source_check():
        command = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                   '-c', 'core.preloadIndex=false', '-c', 'core.fsmonitor=false',
                   '-c', 'index.threads=1', '-C', str(repo)]
        head = subprocess.check_output([*command, 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
        dirty = subprocess.check_output([*command, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=30)
        if head != expected['source_commit'] or dirty:
            raise ValueError('selected source is not exact and clean')
        for row in expected['source_blobs']+expected['test_helper_pins']:
            if sha(project/row['relative']) != row['sha256']:
                raise ValueError('selected source input changed: '+row['relative'])
        closure = consumer_closure(project, repo, expected)
        path = out/('source-consumers-'+str(len(result['source_receipts']))+'.json')
        bounded_json(path, closure, out, policy); result['source_receipts'].append(pin(path))
    def runtime_check():
        selected = {}
        for name, row in expected['tools'].items():
            path = shutil.which(name)
            if path is None or Path(path).resolve() != Path(row['path']).resolve() or sha(path) != row['sha256']:
                raise ValueError('selected physical tool changed: '+name)
            selected[name] = pin(Path(path).resolve())
        for row in expected['wp_artifacts']:
            if sha(row['path']) != row['sha256']:
                raise ValueError('selected WP artifact changed')
        prefix = Path(expected['linux_prefix'])
        for key, root in [('why3_stdlib', prefix/'share/why3/stdlib'),
                          ('wp_why3_support', prefix/'share/frama-c/share/wp/why3'),
                          ('why3_drivers', prefix/'share/why3/drivers')]:
            surface(root, expected['portable_import_surfaces'][key])
        for row in expected['runtime_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name']) != row['sha256']:
                raise ValueError('selected runtime source changed: '+row['name'])
        if sha(expected['why3_config']['path']) != expected['why3_config']['sha256']:
            raise ValueError('selected Why3 configuration changed')
        return selected
    try:
        source_check(); bounded_json(out/'runtime.json', runtime_check(), out, policy)
        ambient = sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_')) or k == 'SWDB_PROOF_REPORT_OUT')
        if ambient:
            raise ValueError('forbidden ambient WP selectors: '+','.join(ambient))
        shutil.copyfile(__file__, out/'entry.py'); shutil.copyfile(args.expected, out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'], SWDB_CBMC='none',
            SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'], WHY3CONFIG=expected['why3_config']['path'],
            SWDB_WHY3_CONFIG=expected['why3_config']['path'], PYTHONDONTWRITEBYTECODE='1',
            SWDB_FIXTURE_HOST='swdb-fixture-host', SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode = True; sys.path[:0] = [str(project), str(project/'tests')]
        from swdb import vector_reallocation_closed_lifetime as packets
        from swdb import heap_model_view as engine, proof_setup, wp_adapter, c_lowering, stdlib_provenance, framac, method_version, rss_watchdog
        from swdb.library import Library
        compiler = stdlib_provenance.runtime_identity(c_lowering.locate()); lowering = c_lowering.identity()
        if {k: compiler[k] for k in expected['linux_clang_components']} != expected['linux_clang_components'] or \
                compiler != expected['linux_project_identity_derivation']['runtime'] or \
                lowering != expected['linux_project_identity_derivation']['predicted_identity']:
            raise ValueError('fresh source/context compiler composite differs')
        bounded_json(out/'compiler-runtime.json', {'runtime': compiler, 'identity': lowering}, out, policy)
        source = project/expected['source_relative']
        if sha(source) != expected['source_sha256']:
            raise ValueError('original closed caller source differs')
        original = c_lowering.lower(source, expected['function'])
        if original.sha256 != expected['lowered_sha256'] or lineage(json.loads(original.anchors_json)) != expected['cached_anchor_lineage']:
            raise ValueError('fresh original caller lowering/source/event lineage differs')
        problem = stdlib_provenance.check(original.stdlib_provenance, c_lowering.locate(), source,
            models=tuple(sorted(set((*original.models,*original.std_models)))), substitutions=original.stdlib_substitutions)
        if problem:
            raise ValueError('fresh full original-TU provenance differs: '+problem)
        bounded_bytes(out/'anchors.fresh.json', original.anchors_json.encode(), out, policy)
        inputs = out/'canonical-inputs'
        manifest = packets.prepare(original, source, expected['contract_clauses'], inputs)
        if manifest != canonical_check(packets, expected, inputs, original, source):
            raise ValueError('fresh public source prepare/check results differ')
        bounded_json(out/'canonical-precheck.json', {'manifest': pin(inputs/'manifest.json'),
            'checker': packets.identity(), 'target_ids': expected['target_ids'],
            'canonical_nonmanifest_files': expected['canonical_files'], 'old_proofs_imported': 0,
            'host_certificate_policy': 'Full fresh source/stdlib certificate retained in manifest. Only its host-specific digest leaf is removed for portable comparison; all source predicates, events, formulas, dependencies and other metadata remain exact.'}, out, policy)
        from test_standard_member_contracts import _member_seed
        seed = initialize_workspace(out, _member_seed)
        import yaml
        inherited = seed.root/'library/methods/wp-tracer-fixture.yaml'
        method_data = yaml.safe_load(inherited.read_bytes())
        if method_data['c_lowering']['translators'] != [lowering['c_lowering']]:
            raise ValueError('unchanged seed compiler context differs')
        method_data.update(id=expected['method_id'], sequence=3,
            description='Standalone six source lifetime gluing duties. No body/caller/model admission. '+json.dumps(expected['explicit_method_binding'], sort_keys=True))
        method_path = seed.root/'library/methods/wp-closed-lifetime6-v1.yaml'
        method_path.write_text(yaml.safe_dump(method_data, sort_keys=False))
        method = method_version.select(seed.root/'library', expected['method_id'])
        adapter = wp_adapter.WpAdapter(Library(seed.root/'library'), 'standalone-closed-lifetime', method, records=seed.records)
        tools = adapter._tools(); flags = engine.flags(tools)
        if tools['seconds'] != 30 or tools['provers'] != ['alt-ergo','z3','cvc5'] or \
                any(x.startswith(('-wp-prop','-wp-fct')) or x in {'-wp-gen','-wp-no-why3-detect'} for x in flags):
            raise ValueError('complete unchanged normal proof portfolio required')
        proof_setup._wp_flags(flags, out); proof_setup._lineup(method, adapter, tools, flags)
        bounded_json(out/'method.json', {'pin': method_version.pin(method), 'method': method_data,
            'inherited': pin(inherited), 'flags': flags, 'tools': tools,
            'policy': 'Actual ordinary flag/lineup functions only; no universal setup certificate claimed.'}, out, policy)
        reader_dir = out/'reader'; reader_dir.mkdir()
        reader = proof_setup.compile_report_module(reader_dir, timeout=min(120, remaining()))
        foundation = engine.foundations(framac.locate().command, out/'foundation', deadline)
        bounded_json(out/'foundation.json', foundation, out, policy)
        for row in manifest['obligations']:
            remaining(); canonical_check(packets, expected, inputs, original, source); runtime_check()
            directory = out/('leaf-'+row['id']); directory.mkdir(); (directory/'tmp').mkdir()
            path = directory/'wp_input.c'; path.write_bytes((inputs/row['path']).read_bytes())
            invocation = engine.command(framac.locate().command, flags, inputs, reader)
            proof_setup._wp_flags(invocation, directory); proof_setup._lineup(method, adapter, tools, flags)
            if sha(path) != row['sha256'] or invocation != engine.command(framac.locate().command, engine.flags(tools), inputs, reader):
                raise ValueError('complete normal command or fresh input changed before launch')
            timeout = min(policy['leaf_timeout_seconds'], remaining())
            bounded_json(directory/'command.json', {'argv': invocation, 'cwd': str(directory),
                'timeout_seconds': timeout, 'input': pin(path), 'selected_id': row['id']}, out, policy)
            environment = {**os.environ, 'TMPDIR': str(directory/'tmp'),
                           'SWDB_PROOF_REPORT_OUT': str(directory/'wp-inventory.json')}
            resource_result = guarded_generation(invocation, directory, environment, policy, timeout, rss_watchdog, out)
            bounded_json(directory/'resources.json', resource_result, out, policy)
            if resource_result['out_of_memory'] or resource_result['timed_out'] or resource_result['output_limit']:
                raise ValueError('leaf resource boundary hit; preserve all partial artifacts')
            outcome = wp_adapter.read_outcome(SimpleNamespace(**resource_result),
                (directory/'frama-c.log').read_text(errors='replace'),
                directory/'wp-goals.json' if (directory/'wp-goals.json').exists() else None,
                directory/'wp-properties.csv' if (directory/'wp-properties.csv').exists() else None,
                inventory=directory/'wp-inventory.json' if (directory/'wp-inventory.json').exists() else None)
            bounded_json(directory/'outcome.json', outcome, out, policy)
            if not all((directory/name).is_file() for name in ('wp-goals.json','wp-properties.csv','wp-inventory.json','wp-normalized.c')):
                raise ValueError('actual complete native/ordinary/property/normalized reports absent')
            inventory = json.loads((directory/'wp-inventory.json').read_bytes())
            census = normal_task_census(directory, row, inventory, out, policy)
            result['runs'].append({'id': row['id'], 'cwd': str(directory), 'input': pin(path),
                'resources': resource_result, 'outcome': outcome, 'census': pin(directory/'task-census.json'),
                'ordinary_goals': census['ordinary_count'], 'smoke_goals': census['smoke_count']})
            result['unexecuted'].remove(row['id']); bounded_json(out/'result.json', result, out, policy)
        source_check(); runtime_check(); canonical_check(packets, expected, inputs, original, source)
        if list((seed.records/'proofs').glob('*.yaml')):
            raise ValueError('standalone profile unexpectedly created a public proof record')
        result.update(producer_complete=True, all_six_producer_proven=all(r['outcome']['verdict']=='proven' for r in result['runs']),
            source_after_clean=True, raw_bytes=raw_bytes(out),
            classification='Six fresh mathematical producer outcomes retained. Independent complete source/runtime/resource/task/hypothesis review required; no constructor/destructor dependency, source/Typed/body/caller/public-record acceptance.')
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['within_profile_budget'] = time.monotonic() <= deadline
        bounded_json(out/'result.json', result, out, policy, reserve=False)
        bounded_json(out/'artifact-manifest.json', [{'relative': str(p.relative_to(out)), **pin(p)}
            for p in sorted(out.rglob('*')) if p.is_file() and p != out/'artifact-manifest.json'], out, policy, reserve=False)
    return 0 if result['producer_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
