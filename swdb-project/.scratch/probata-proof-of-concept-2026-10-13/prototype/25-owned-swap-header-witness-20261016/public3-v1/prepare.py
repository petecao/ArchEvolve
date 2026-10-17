"""2026-10-16 ET. Materialize inert witness3 entry and sparse source from a separately published Git source.

No project import, compiler, verifier, source checkout or remote operation occurs.
The exact prospective entry must freshly check all source/runtime/canonical data.
"""
import ast
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zlib

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
REPO = HERE.parents[5]
SOURCE = sys.argv[1] if len(sys.argv) == 2 else None
if SOURCE is None or len(SOURCE) != 40 or set(SOURCE) - set('0123456789abcdef'):
    raise ValueError('a separately published exact forty-hex source commit is required before materialization')
PREVIOUS = POC/'prototype/25-owned-swap-header-cases-20261016/public3-v1/inert-abb598a4-public3-v1'
OUTPUT = HERE/('inert-'+SOURCE[:8]+'-public3-v1')
REMOTE = '/data1/yanruj/probata-resume-20261016-'+SOURCE[:8]+'/swdb-project'
ROOT_KIND = 't25-owned-swap-header-witness3-public-v1'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def git(*args):
    return subprocess.check_output(['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                                   '-C', str(REPO), *args], timeout=60)


def blob(relative, source=SOURCE):
    return git('show', source+':swdb-project/'+relative)


def functions(raw):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(raw).body
            if isinstance(node, ast.FunctionDef)}


def main():
    assert git('rev-parse', SOURCE).decode().strip() == SOURCE
    predecessor = json.loads((PREVIOUS/'packet.json').read_bytes())
    for field, name in [('entry', 'entry.py'), ('expected', 'expected.json'), ('root_command', 'root-command.json')]:
        assert pin(PREVIOUS/name)['sha256'] == predecessor[field]['sha256']
    old_entry = (PREVIOUS/'entry.py').read_bytes()
    old_expected_raw = (PREVIOUS/'expected.json').read_bytes()
    old = json.loads(old_expected_raw)
    expected = copy.deepcopy(old)
    canonical = HERE.parent/'inert-all-types-v1'
    manifest = json.loads((canonical/'manifest.json').read_bytes())
    source_packet_path = HERE.parent/'source-packet-v1.json'
    source_packet = json.loads(source_packet_path.read_bytes())
    for row in source_packet['source_inputs']:
        assert digest(blob(row['path'])) == row['sha256']
    physical = [{'path': str(path.relative_to(canonical)), 'bytes': path.stat().st_size,
                 'sha256': digest(path.read_bytes())} for path in sorted(canonical.rglob('*')) if path.is_file()]
    assert len(physical) == 48 and len(manifest['obligations']) == 3
    assert manifest['logical_target'] == 'swap.owner_correspondence.header.ready'
    assert manifest['elements'] == ['int', 'float', 'double', 'int *']
    assert len(manifest['unchanged_dependencies']) == 12
    assert manifest['reconstruction']['added_premises'] == manifest['reconstruction']['axioms_added'] == []
    assert [(row['case'], row['condition']) for row in manifest['obligations']] == [
        ('left', 'observed == l'), ('right', 'observed == r'), ('other', 'observed != l && observed != r')]
    assert manifest['type_registry']['container_sha256'] == digest(blob('swdb/c_lowering.py'))
    for row in manifest['obligations']:
        assert row['kind'] == 'check_lemma' and row['dependencies'] == [] and row['status'] == 'pending'
        raw = (canonical/row['path']).read_bytes()
        assert digest(raw) == row['sha256'] and raw.count(b'check lemma ') == 1
    helper_path = POC/'prototype/25-prefix10-resume-20261016/author.py'
    spec = importlib.util.spec_from_file_location('header3_metadata_compiler_recipe', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.compiler_identity(old['source_commit'], old['linux_project_identity_derivation']['runtime'],
                                    old['linux_project_identity_derivation']['predicted_identity']) == old['linux_project_identity_derivation']['predicted_identity']
    runtime = copy.deepcopy(old['linux_project_identity_derivation']['runtime'])
    changes = 0
    for index, value in enumerate(runtime['frontend']):
        for flag in ('-fdebug-compilation-dir=', '-fcoverage-compilation-dir='):
            if value == flag+old['remote_project']:
                runtime['frontend'][index] = flag+REMOTE
                changes += 1
    assert changes == 2
    runtime['check']['sha256'] = digest(blob('swdb/stdlib_provenance.py'))
    expected['linux_project_identity_derivation'] = {
        'runtime': runtime,
        'predicted_identity': helper.compiler_identity(SOURCE, runtime, old['linux_project_identity_derivation']['predicted_identity']),
        'scope': 'Prospective exact Git/context digest reconstruction only; fresh actual Linux compiler equality required.'}
    expected['source_blobs'] = []
    for part in git('ls-tree', '-r', '-z', SOURCE, '--', 'swdb-project/swdb').split(b'\0'):
        if not part:
            continue
        meta, name = part.decode().split('\t')
        mode, kind, oid = meta.split()
        assert mode in ('100644', '100755') and kind == 'blob'
        relative = name.removeprefix('swdb-project/')
        expected['source_blobs'].append({'path': name, 'relative': relative, 'blob': oid, 'sha256': digest(blob(relative))})
    roots = ['swdb', 'schemas', 'vocab', 'library/methods/probata-draft-1.yaml',
             'tests/fixtures/proof/methods/contract-fixture-1.yaml']
    expected['source_consumer_trees'] = {name: {'oid': git('rev-parse', SOURCE+':swdb-project/'+name).decode().strip()} for name in roots}
    expected['test_helper_pins'] = [{'relative': name, 'sha256': digest(blob(name))} for name in roots[-2:]]
    expected.update(created='2026-10-16 ET', status='INERT / UNREVIEWED / NOT EXECUTED', source_commit=SOURCE,
                    remote_project=REMOTE, method_id='method.wp-owned-swap-header-witness3-v1',
                    canonical_manifest=manifest, canonical_files=physical,
                    target_ids=[row['id'] for row in manifest['obligations']],
                    scope='Three stronger explicit-witness owner cases sufficient for the unchanged universal ready-header duty under its complete original antecedent; all existential recovery and source binding remain separately pending. Fresh public prepare/check and ordinary complete WP portfolio. No sibling proof premise, source/body/Heap/Typed/caller/default/public-record admission.',
                    cost_estimate='Unmeasured allowance: three targets at unchanged30seconds per solver/180seconds leaf,2600profile/2800whole/2920outer,8GiB one worker/2GiB aggregate raw. No result guarantee.')
    expected['proof_policy'].update(complete_targets=3, check_lemmas=3, complete_canonical_files=48)
    assert expected['resource_policy'] == old['resource_policy']
    expected_raw = encoded(expected)
    template = (HERE/'entry_template.py').read_bytes()
    assert template.count(b'__EXPECTED_SHA256__') == 1
    entry = template.replace(b'__EXPECTED_SHA256__', digest(expected_raw).encode())
    ast.parse(entry)
    old_functions, new_functions = functions(old_entry), functions(entry)
    assert set(old_functions) == set(new_functions)
    identical = [name for name in old_functions if old_functions[name] == new_functions[name]]
    assert set(old_functions)-set(identical) == {'canonical_check', 'main'}
    command = json.loads((PREVIOUS/'root-command.json').read_bytes())
    bootstrap = command[6]
    replacements = [(digest(old_entry), digest(entry)), (digest(old_expected_raw), digest(expected_raw)),
                    (base64.b64encode(zlib.compress(old_entry, 9)).decode(), base64.b64encode(zlib.compress(entry, 9)).decode()),
                    (base64.b64encode(zlib.compress(old_expected_raw, 9)).decode(), base64.b64encode(zlib.compress(expected_raw, 9)).decode()),
                    ('owned-swap-header3-public-root-early-preflight.json', 'owned-swap-header-witness3-public-root-early-preflight.json'),
                    ('owned-swap-header3-public-v1', 'owned-swap-header-witness3-public-v1')]
    for before, after in replacements:
        assert before in bootstrap
        bootstrap = bootstrap.replace(before, after)
    inverse = bootstrap
    for before, after in reversed(replacements):
        inverse = inverse.replace(after, before)
    assert inverse == command[6]
    ast.parse(bootstrap)
    assert len(bootstrap.encode()) < 120000
    command[6] = bootstrap
    rows = []
    for part in git('ls-tree', '-rlz', SOURCE, '--', *['swdb-project/'+name for name in roots]).split(b'\0'):
        if not part:
            continue
        meta, name = part.split(b'\t', 1)
        mode, kind, oid, size = meta.decode().split()
        assert kind == 'blob' and mode in ('100644', '100755')
        rows.append({'path': name.decode(), 'mode': mode, 'oid': oid, 'bytes': int(size)})
    projection = {'date': '2026-10-16 ET', 'mode': 'isolated-shared-sparse-header-witness3-v1',
                  'source_commit': SOURCE, 'roots': roots, 'files': len(rows),
                  'bytes': sum(row['bytes'] for row in rows), 'package_files': len(expected['source_blobs']),
                  'inventory_sha256': digest(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()),
                  'metadata_headroom_bytes': 1024**3,
                  'consumer_oids': {name: row['oid'] for name, row in expected['source_consumer_trees'].items()}}
    old_launcher_path = POC/'prototype/resume-root-20261016/launch_reviewed_main_v10.py'
    old_launcher = old_launcher_path.read_text()
    node = next(node for node in ast.parse(old_launcher).body if isinstance(node, ast.Assign) and
                isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'SPARSE_SOURCE_SPEC')
    before = ast.get_source_segment(old_launcher, node)
    after = 'SPARSE_SOURCE_SPEC='+repr(projection)
    assert old_launcher.count(before) == 1
    launcher = old_launcher.replace(before, after, 1)
    assert launcher.replace(after, before, 1) == old_launcher
    ast.parse(launcher)
    remote = next(node.value.right.value for node in ast.parse(launcher).body if isinstance(node, ast.Assign) and
                  isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'script')
    compile('cfg={}\n'+remote, '<inert-header3-nested-remote>', 'exec')
    OUTPUT.mkdir(exist_ok=False)
    for name, raw in [('entry.py', entry), ('expected.json', expected_raw), ('root-command.json', encoded(command)),
                      ('source-projection-spec.json', encoded(projection)), ('selected-Git-metadata.json', encoded(rows)),
                      ('root-launcher-candidate.py', launcher.encode())]:
        (OUTPUT/name).write_bytes(raw)
    delta = {'date': '2026-10-16 ET', 'predecessor': pin(old_launcher_path),
             'changes': [{'before': before, 'after': after}], 'full_inverse_exact': True,
             'only_exact_source_projection_literal_changed': True}
    (OUTPUT/'launcher-delta-v1.json').write_bytes(encoded(delta))
    packet = {'date': '2026-10-16 ET', 'status': 'INERT / UNREVIEWED / NOT EXECUTED',
              'source_commit': SOURCE, 'remote_project': REMOTE, 'root_kind': ROOT_KIND,
              'entry': pin(OUTPUT/'entry.py'), 'expected': pin(OUTPUT/'expected.json'),
              'root_command': pin(OUTPUT/'root-command.json'), 'author': pin(Path(__file__)),
              'template': pin(HERE/'entry_template.py'), 'predecessor_packet': pin(PREVIOUS/'packet.json'),
              'source_packet': pin(source_packet_path), 'complete_targets': 3, 'check_lemmas': 3,
              'canonical_files': 48, 'C_layout_only_units': 0, 'canonical_manifest_sha256': digest((canonical/'manifest.json').read_bytes()),
              'identical_predecessor_function_asts': identical, 'changed_function_asts': ['canonical_check', 'main'],
              'bootstrap_inverse_exact': True, 'bootstrap_bytes': len(bootstrap.encode()),
              'source_package_count': len(expected['source_blobs']), 'sparse_projection': projection,
              'launcher_candidate': pin(OUTPUT/'root-launcher-candidate.py'),
              'launcher_delta': pin(OUTPUT/'launcher-delta-v1.json'), 'resource_policy': expected['resource_policy'],
              'runtime_files': len(expected['runtime_files']), 'runtime_aliases': len(expected['why3_elf_candidate_aliases']),
              'project_imports': 0, 'compiler_native_verifier_calls': 0, 'actual_generations': 0,
              'proof_acceptance': False, 'source_typed_bridge_established': False, 'body_acceptance': False,
              'caller_acceptance': False, 'ticket_closure': False, 'independent_review_pending': True,
              'root_once_admission_pending': True}
    (OUTPUT/'packet.json').write_bytes(encoded(packet))
    print(json.dumps({'packet': pin(OUTPUT/'packet.json'), 'entry': packet['entry'], 'expected': packet['expected'],
                      'command': packet['root_command'], 'bootstrap_bytes': packet['bootstrap_bytes'],
                      'sparse_projection': projection}, indent=2))


if __name__ == '__main__':
    main()
