"""2026-10-16 ET. Rebind an inert diagnostic using Git and stdlib metadata only.

This author never imports SWDB, executes a compiler, or runs the emitted entry.
It refuses source drift: a changed production/consumer tree requires new review.
"""
import ast
import base64
import copy
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SNAPSHOT = HERE.with_name('25-prefix10-stop-checkpoint-20261016')
SOURCE = 'c978393b119a3614229a37f0f2c8ca2a097c750b'
OLD_SOURCE = 'e99d09b1699b32525cd4c44cead21ed2fc6f4917'
REMOTE_PROJECT = '/data1/yanruj/probata-resume-20261016-c978393b/swdb-project'
OUTPUT = HERE / 'inert-c978393b'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def git(*arguments):
    return subprocess.check_output(
        ['/usr/bin/git', '--no-replace-objects', '-C', str(REPO), *arguments],
        timeout=60,
    )


def blob(relative, source=SOURCE):
    return git('show', source + ':swdb-project/' + relative)


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': digest(data)}


def compiler_identity(source, runtime, template):
    """Independent digest recipe, checked against the retained actual046 image."""
    def module(name):
        return blob('swdb/' + name, source)

    tree = ast.parse(module('c_lowering.py'))
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'identity')
    assignment = next(node for node in function.body
                      if isinstance(node, ast.Assign) and any(
                          isinstance(target, ast.Name) and target.id == 'digest'
                          for target in node.targets))
    calls = sorted((node for node in ast.walk(assignment)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'with_name'),
                   key=lambda node: (node.lineno, node.col_offset))
    tail = [ast.literal_eval(node.args[0]) for node in calls]
    bounded = digest(module('bounded_initialization.py') + module('proof_semantics.py')
                     + module('bounded_std_initialization.py'))
    pointer = digest(module('wp_pointer_bounds.py'))
    raw = (module('c_lowering.py') + module('terminal_release.py') + module('cpu_effects.py')
           + module('cpu_memory_admission.py') + bounded.encode() + pointer.encode()
           + b''.join(module(name) for name in tail)
           + json.dumps(runtime, sort_keys=True).encode())
    result = copy.deepcopy(template)
    result['c_lowering']['sha256'] = digest(raw)
    return result


def constants(source, names):
    return {node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names}


def main():
    draft = SNAPSHOT / 'focused10-draft'
    old_entry_path = draft / 'probata-t25-copy-prefix10-entry-v1-e99d09b1-20261016.py'
    old_expected_path = draft / 'probata-t25-copy-prefix10-expected-v1-e99d09b1-20261016.json'
    old_command_path = draft / 'probata-t25-copy-prefix10-root-command-v1-e99d09b1-20261016.json'
    old_packet_path = draft / 'probata-t25-copy-prefix10-packet-v1-e99d09b1-20261016.json'
    old_entry, old_expected = old_entry_path.read_bytes(), old_expected_path.read_bytes()
    old_packet = json.loads(old_packet_path.read_bytes())
    for key, path in [('entry', old_entry_path), ('expected', old_expected_path),
                      ('root_command', old_command_path)]:
        assert digest(path.read_bytes()) == old_packet[key]['sha256']
    expected = json.loads(old_expected)
    assert expected['source_commit'] == OLD_SOURCE
    assert git('rev-parse', SOURCE).decode().strip() == SOURCE
    assert git('diff', '--name-only', OLD_SOURCE, SOURCE, '--',
               *['swdb-project/' + relative for relative in
                 ['swdb', *expected['source_consumer_trees']]]) == b''
    for row in expected['source_blobs'] + expected['test_helper_pins']:
        assert digest(blob(row['relative'])) == row['sha256']
    for relative, row in expected['source_consumer_trees'].items():
        assert git('rev-parse', SOURCE + ':swdb-project/' + relative).decode().strip() == row['oid']

    canonical = SNAPSHOT / 'pure-preparer-snapshot' / 'canonical'
    physical = [{'path': str(path.relative_to(canonical)), 'bytes': path.stat().st_size,
                 'sha256': digest(path.read_bytes())}
                for path in sorted(canonical.rglob('*')) if path.is_file()]
    assert physical == expected['canonical_files'] and len(physical) == 70
    assert digest((canonical / 'manifest.json').read_bytes()) == expected['canonical_manifest_sha256']
    manifest = json.loads((canonical / 'manifest.json').read_bytes())
    assert len(manifest['obligations']) == 61 and len(expected['diagnostic_ids']) == 10
    assert expected['logical_obligations'] == manifest['logical_obligations']
    assert [row['id'] for row in manifest['obligations']] == expected['target_ids']
    for row in json.loads((SNAPSHOT / 'pure-preparer-snapshot' / 'preparer-receipt.json').read_bytes())['files']:
        assert digest(blob(row['relative'])) == row['sha256']

    observation_path = SNAPSHOT / 'historical-authoring-inputs' / 'probata-t25-cell4-setup-only-metadata-v1-20261016.json'
    observation = json.loads(observation_path.read_bytes())['metadata']['cell4-setup-only-profile/compiler-runtime.json']['content']
    assert compiler_identity('046f6b9e64d45777a8032951ced04f942fc9c3c2',
                             observation['runtime'], observation['identity']) == observation['identity']
    old_runtime = expected['linux_project_identity_derivation']['runtime']
    old_prediction = expected['linux_project_identity_derivation']['predicted_identity']
    assert compiler_identity(OLD_SOURCE, old_runtime, observation['identity']) == old_prediction
    runtime = copy.deepcopy(old_runtime)
    replacements = 0
    for index, value in enumerate(runtime['frontend']):
        for flag in ['-fdebug-compilation-dir=', '-fcoverage-compilation-dir=']:
            if value == flag + expected['remote_project']:
                runtime['frontend'][index] = flag + REMOTE_PROJECT
                replacements += 1
    assert replacements == 2
    runtime['check']['sha256'] = digest(blob('swdb/stdlib_provenance.py'))
    prediction = compiler_identity(SOURCE, runtime, observation['identity'])
    expected.update(source_commit=SOURCE, remote_project=REMOTE_PROJECT,
                    status='INERT: resumed current-source packet; independent review and root admission required')
    expected['linux_project_identity_derivation'] = {
        'runtime': runtime, 'predicted_identity': prediction,
        'scope': 'Prospective exact-source/context reconstruction only; fresh actual runtime equality mandatory.',
    }
    new_expected = encoded(expected)
    new_entry = old_entry.replace(digest(old_expected).encode(), digest(new_expected).encode())
    assert new_entry != old_entry
    assert new_entry.replace(digest(new_expected).encode(), digest(old_expected).encode()) == old_entry
    ast.parse(new_entry)

    command = json.loads(old_command_path.read_bytes())
    bootstrap = command[6]
    substitutions = [
        (digest(old_entry), digest(new_entry)), (digest(old_expected), digest(new_expected)),
        (base64.b64encode(zlib.compress(old_entry, 9)).decode(),
         base64.b64encode(zlib.compress(new_entry, 9)).decode()),
        (base64.b64encode(zlib.compress(old_expected, 9)).decode(),
         base64.b64encode(zlib.compress(new_expected, 9)).decode()),
    ]
    for before, after in substitutions:
        assert bootstrap.count(before) == 1
        bootstrap = bootstrap.replace(before, after)
    inverse = bootstrap
    for before, after in substitutions:
        inverse = inverse.replace(after, before)
    assert inverse == command[6]
    ast.parse(bootstrap)
    assert len(bootstrap.encode()) < 120000
    command[6] = bootstrap
    embedded = constants(bootstrap, {'ENTRY_SHA256', 'EXPECTED_SHA256',
                                    'ENTRY_COMPRESSED_BASE64', 'EXPECTED_COMPRESSED_BASE64'})
    assert zlib.decompress(base64.b64decode(embedded['ENTRY_COMPRESSED_BASE64'], validate=True)) == new_entry
    assert zlib.decompress(base64.b64decode(embedded['EXPECTED_COMPRESSED_BASE64'], validate=True)) == new_expected

    OUTPUT.mkdir(exist_ok=False)
    for name, data in [('entry.py', new_entry), ('expected.json', new_expected),
                       ('root-command.json', encoded(command))]:
        (OUTPUT / name).write_bytes(data)
    packet = {
        'created': '2026-10-16 ET', 'status': 'INERT / UNREVIEWED / NOT EXECUTED',
        'source_commit': SOURCE, 'remote_project': REMOTE_PROJECT,
        'root_kind': 't25-copy-prefix10-diagnostic-v1',
        'entry': pin(OUTPUT / 'entry.py'), 'expected': pin(OUTPUT / 'expected.json'),
        'root_command': pin(OUTPUT / 'root-command.json'), 'author': pin(Path(__file__)),
        'predecessor_packet': pin(old_packet_path), 'actual046_metadata': pin(observation_path),
        'production_and_consumer_diff_empty': True,
        'source_package_count': len(expected['source_blobs']),
        'helper_count': len(expected['test_helper_pins']),
        'canonical_manifest_sha256': expected['canonical_manifest_sha256'],
        'canonical_files': len(physical), 'complete_model_targets': 61,
        'fresh_diagnostic_targets': 10, 'unexecuted_model_targets': 51,
        'resource_policy': expected['resource_policy'], 'old_results_imported': 0,
        'entry_inverse_predecessor_equal': True, 'bootstrap_inverse_predecessor_equal': True,
        'compiler_recipe_actual046_equal': True, 'compiler_recipe_old_prediction_equal': True,
        'embedded_roundtrip_exact': True, 'project_imports': 0, 'native_or_compiler_calls': 0,
        'root_admission_pending': True, 'independent_static_review_pending': True,
        'model_acceptance': False, 'original_v2_acceptance': False,
        'caller_acceptance': False, 'ticket_closure': False,
    }
    (OUTPUT / 'packet.json').write_bytes(encoded(packet))
    print(json.dumps({'packet': pin(OUTPUT / 'packet.json'), 'source_commit': SOURCE,
                      'bootstrap_bytes': len(bootstrap.encode()),
                      'compiler_identity': prediction['c_lowering']}, indent=2))


if __name__ == '__main__':
    main()
