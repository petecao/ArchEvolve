"""2026-10-16 ET. Author inert d7f685c6 ten-duty profile using Git/stdlib only.

Does not import SWDB or execute any compiler, native helper, verifier or solver.
Exact source/runtime/prepare equality is mandatory in the prospective entry.
"""
import ast
import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
SOURCE = 'd7f685c6fdbd7ff776eb1eaccc40099a2c48dc08'
REMOTE = '/data1/yanruj/probata-resume-20261016-d7f685c6/swdb-project'
OUTPUT = HERE/'inert-d7f685c6-public10-v1'
PREDECESSOR = HERE.parent.with_name('25-prefix10-resume-20261016')/'inert-c978393b'
GUARD = HERE.parent.with_name('25-original-no-growth-generation-20261016')/'inert-c978393b-v3'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def git(*arguments):
    return subprocess.check_output(['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
        '-C', str(REPO), *arguments], timeout=60)


def blob(relative):
    return git('show', SOURCE+':swdb-project/'+relative)


def definitions(raw, names):
    lines = raw.decode().splitlines(keepends=True)
    found = {n.name: ''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body
             if isinstance(n, ast.FunctionDef) and n.name in names}
    assert set(found) == set(names)
    return found


def constants(raw, names):
    return {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(raw).body
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and
            isinstance(n.targets[0], ast.Name) and n.targets[0].id in names}


def main():
    assert git('rev-parse', SOURCE).decode().strip() == SOURCE
    predecessors = []
    for directory in (PREDECESSOR, GUARD):
        packet = json.loads((directory/'packet.json').read_bytes())
        for key, name in [('entry','entry.py'), ('expected','expected.json'), ('root_command','root-command.json')]:
            assert pin(directory/name)['sha256'] == packet[key]['sha256']
        predecessors.append(pin(directory/'packet.json'))
    old = json.loads((PREDECESSOR/'expected.json').read_bytes())
    normal_entry = (PREDECESSOR/'entry.py').read_bytes()
    guard_entry = (GUARD/'entry.py').read_bytes()
    guard_expected = json.loads((GUARD/'expected.json').read_bytes())
    keep = ('linux_clang_component_origin','linux_clang_components','linux_launch_binding',
            'linux_prefix','linux_project_identity_derivation','metadata_origin','portable_import_surfaces',
            'portable_surface_origin','source_consumer_trees','tools','why3_config','wp_artifacts')
    expected = {key: copy.deepcopy(old[key]) for key in keep}
    # Reconstruct the compiler digest from exact Git blobs without importing it.
    author_path = PREDECESSOR.parent/'author.py'
    spec = importlib.util.spec_from_file_location('inert_prefix_metadata_author', author_path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    assert helper.compiler_identity(old['source_commit'], old['linux_project_identity_derivation']['runtime'],
           old['linux_project_identity_derivation']['predicted_identity']) == old['linux_project_identity_derivation']['predicted_identity']
    runtime = copy.deepcopy(old['linux_project_identity_derivation']['runtime'])
    changed = 0
    for i, value in enumerate(runtime['frontend']):
        for flag in ('-fdebug-compilation-dir=', '-fcoverage-compilation-dir='):
            if value == flag+old['remote_project']:
                runtime['frontend'][i] = flag+REMOTE; changed += 1
    assert changed == 2
    runtime['check']['sha256'] = digest(blob('swdb/stdlib_provenance.py'))
    expected['linux_project_identity_derivation'] = {
        'runtime': runtime,
        'predicted_identity': helper.compiler_identity(SOURCE, runtime, old['linux_project_identity_derivation']['predicted_identity']),
        'scope': 'Prospective Git/context digest reconstruction only; fresh actual Linux compiler equality required.'}
    expected['source_blobs'] = []
    for raw in git('ls-tree','-r','-z', SOURCE, '--', 'swdb-project/swdb').split(b'\0'):
        if not raw:
            continue
        meta, path = raw.decode().split('\t'); mode, kind, oid = meta.split()
        assert mode in {'100644','100755'} and kind == 'blob'
        relative = path.removeprefix('swdb-project/')
        expected['source_blobs'].append({'path': path, 'relative': relative, 'blob': oid,
                                         'sha256': digest(blob(relative))})
    roots = ['swdb', 'schemas', 'vocab', 'library/methods/probata-draft-1.yaml',
             'tests/fixtures/proof/methods/contract-fixture-1.yaml']
    expected['source_consumer_trees'] = {relative: {'oid': git('rev-parse', SOURCE+':swdb-project/'+relative).decode().strip()} for relative in roots}
    expected['test_helper_pins'] = [{'relative': name, 'sha256': digest(blob(name))} for name in roots[-2:]]
    canonical = HERE.parent/'inert-v2'
    manifest = json.loads((canonical/'manifest.json').read_bytes())
    physical = [{'path': str(p.relative_to(canonical)), 'bytes': p.stat().st_size,
                 'sha256': digest(p.read_bytes())} for p in sorted(canonical.rglob('*')) if p.is_file()]
    receipt_path = HERE.parents[2]/'evidence/t25-owned-transfer-preparation-v2-20261016.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert len(physical) == 21 and len(manifest['obligations']) == 10
    assert digest(blob('swdb/vector_owned_transfer.py')) == '6fa50d3b0ff6610c541bfa787179b37c6c8b50e4155fb2b0605d00e1eaffd085'
    assert digest((canonical/'theory/vector_owned_state.mlw').read_bytes()) == digest(blob('swdb/vector_owned_state.mlw'))
    assert digest(blob('swdb/vector_owned_state.mlw')) == 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'
    assert manifest['type_registry']['container_sha256'] == digest(blob('swdb/c_lowering.py'))
    assert manifest['elements'] == ['int','float','double','int *']
    runtime_snapshot = json.loads((HERE/'why3-runtime-snapshot.json').read_bytes())
    expected.update({key: runtime_snapshot[key] for key in ('why3_runtime_extension','runtime_files','ocaml_packages','why3_elf_candidate_files','why3_elf_candidate_aliases')})
    for row in manifest['obligations']:
        assert row['kind'] == 'check_lemma' and row['dependencies'] == [] and row['status'] == 'pending'
        raw = (canonical/row['path']).read_bytes()
        assert digest(raw) == row['sha256'] and raw.count(b'check lemma ') == 1
    policy = copy.deepcopy(old['resource_policy'])
    policy.update(metadata_reserve_bytes=4*1024**2, per_file_bytes=128*1024**2, profile_seconds=1900, root_whole_seconds=2100, root_outer_seconds=2220)
    expected.update(created='2026-10-16 ET', status='INERT / UNREVIEWED / NOT EXECUTED',
        source_commit=SOURCE, remote_project=REMOTE, method_id='method.wp-owned-transfer10-v1', elements=manifest['elements'],
        canonical_manifest=manifest, canonical_files=physical,
        target_ids=[row['id'] for row in manifest['obligations']], resource_policy=policy,
        runtime_sources=copy.deepcopy(guard_expected['runtime_sources']),
        scope='Standalone ten conditional ownership-registry mathematical duties, actual public prepare/check followed by normal complete WP flags/portfolio/native reports. No admitted model/View, universal proof-setup attestation, original source/Typed bridge, body/caller proof or public record.',
        explicit_method_binding={'wp_model_flags':['+real'], 'wp_memory_model':'Typed/Fits with Var wrapper',
            'wp_integer_model':'Machine', 'selected_runtime_sources':copy.deepcopy(guard_expected['runtime_sources']),
            'scope':'Pinned current mathematical ownership-registry duties and unchanged Owners definitions only; source and allocator ownership/effect assumptions remain pending.'},
        cost_estimate='Unmeasured allowance: ten targets, unchanged three solvers at30seconds each;180seconds leaf,1900seconds profile,2100whole,2220outer;8GiB one worker and2GiB aggregate raw limit. No result guarantee.',
        proof_policy={'actual_public_prepare_check':True, 'complete_targets':10, 'check_lemmas':10,
            'complete_canonical_files':21, 'numeric_C_kernels':0, 'solver_seconds':30,
            'solver_portfolio':['alt-ergo','z3','cvc5'], 'old_proofs_imported':0,
            'normal_command_and_flags':True, 'normal_native_and_outcome_readers':True,
            'universal_proof_setup_attested':False, 'public_proof_record_created':False,
            'independent_complete_task_hypothesis_cold_review_required':True})
    expected_bytes = encoded(expected)
    names = ('sha','pin','write','surface','linux_admission','consumer_closure')
    helpers = definitions(normal_entry, names)
    guard_names = ('guarded_generation',)
    guards = definitions(guard_entry, guard_names)
    guards['guarded_generation'] = guards['guarded_generation'].replace('resource.RLIMIT_FSIZE, (file_allowance, file_allowance)', 'resource.RLIMIT_FSIZE, (min(file_allowance, policy[\'per_file_bytes\']), min(file_allowance, policy[\'per_file_bytes\']))')
    template = (HERE/'entry_template.py').read_text()
    entry = template.replace('# __REVIEWED_HELPERS__', '\n\n'.join([*helpers.values(), *guards.values()]))
    runtime_helpers = (HERE/'runtime_quota.py').read_text()+'\n\n'+(HERE/'reviewed_why3_package_check.py').read_text()
    entry = entry.replace('# __OWNED10_RUNTIME_AND_QUOTA__', runtime_helpers)
    entry = entry.replace('__EXPECTED_SHA256__', digest(expected_bytes)).encode()
    ast.parse(entry)
    assert definitions(entry, names) == helpers and definitions(entry, guard_names) == guards
    command = json.loads((PREDECESSOR/'root-command.json').read_bytes())
    bootstrap = command[6]
    replacements = [(digest(normal_entry),digest(entry)),
        (digest((PREDECESSOR/'expected.json').read_bytes()),digest(expected_bytes)),
        (base64.b64encode(zlib.compress(normal_entry,9)).decode(),base64.b64encode(zlib.compress(entry,9)).decode()),
        (base64.b64encode(zlib.compress((PREDECESSOR/'expected.json').read_bytes(),9)).decode(),
         base64.b64encode(zlib.compress(expected_bytes,9)).decode()),
        ('copy-prefix10-root-early-preflight.json','owned-transfer10-public-root-early-preflight.json'),
        ('copy-prefix10-diagnostic','owned-transfer10-public-v1')]
    for before, after in replacements:
        assert before in bootstrap
        bootstrap = bootstrap.replace(before,after)
    inverse = bootstrap
    for before, after in reversed(replacements):
        inverse = inverse.replace(after,before)
    assert inverse == command[6]
    ast.parse(bootstrap); assert len(bootstrap.encode()) < 120000
    embeds = constants(bootstrap, {'ENTRY_SHA256','EXPECTED_SHA256','ENTRY_COMPRESSED_BASE64','EXPECTED_COMPRESSED_BASE64'})
    assert embeds['ENTRY_SHA256'] == digest(entry) and embeds['EXPECTED_SHA256'] == digest(expected_bytes)
    assert zlib.decompress(base64.b64decode(embeds['ENTRY_COMPRESSED_BASE64'],validate=True)) == entry
    assert zlib.decompress(base64.b64decode(embeds['EXPECTED_COMPRESSED_BASE64'],validate=True)) == expected_bytes
    command[6] = bootstrap
    OUTPUT.mkdir(exist_ok=False)
    for name, raw in [('entry.py',entry),('expected.json',expected_bytes),('root-command.json',encoded(command))]:
        (OUTPUT/name).write_bytes(raw)
    packet = {'created':'2026-10-16 ET','status':'INERT / UNREVIEWED / NOT EXECUTED',
        'source_commit':SOURCE,'remote_project':REMOTE,'root_kind':'t25-owned-transfer10-public-v1',
        'entry':pin(OUTPUT/'entry.py'),'expected':pin(OUTPUT/'expected.json'),
        'root_command':pin(OUTPUT/'root-command.json'),'author':pin(Path(__file__)),
        'template':pin(HERE/'entry_template.py'),'predecessor_packets':predecessors,
        'pure_preparation_receipt':pin(receipt_path),'compiler_recipe_predecessor_equal':True,
        'complete_targets':10,'check_lemmas':10,'canonical_files':21,
        'canonical_manifest_sha256':digest((canonical/'manifest.json').read_bytes()),
        'reviewed_helpers_exact':list(names),'reviewed_guard_helpers_exact':[], 'guard_delta':'Only RLIMIT_FSIZE is the minimum of projected aggregate allowance and128MiB per-file cap', 'why3_runtime_snapshot':pin(HERE/'why3-runtime-snapshot.json'), 'runtime_quota':pin(HERE/'runtime_quota.py'), 'why3_package_checker':pin(HERE/'reviewed_why3_package_check.py'),
        'bootstrap_inverse_predecessor_equal':True,'embedded_roundtrip_exact':True,
        'bootstrap_bytes':len(bootstrap.encode()),'resource_policy':policy,
        'source_package_count':len(expected['source_blobs']),'project_runtime_imports':0,
        'compiler_or_native_or_verifier_calls':0,'actual_generations':0,'actual_proofs':0,
        'public_proof_records_created':0,'universal_proof_setup_attested':False,
        'proof_acceptance':False,'source_typed_bridge_established':False,'body_acceptance':False,
        'caller_acceptance':False,'ticket_closure':False,
        'runtime_extension_independent_review_pending':True, 'independent_entry_review_pending':True,'root_admission_pending':True}
    (OUTPUT/'packet.json').write_bytes(encoded(packet))
    print(json.dumps({'packet':pin(OUTPUT/'packet.json'),'entry':packet['entry'],
        'expected':packet['expected'],'root_command':packet['root_command'],
        'bootstrap_bytes':packet['bootstrap_bytes'],'source_package_count':packet['source_package_count']},indent=2))


if __name__ == '__main__':
    main()
