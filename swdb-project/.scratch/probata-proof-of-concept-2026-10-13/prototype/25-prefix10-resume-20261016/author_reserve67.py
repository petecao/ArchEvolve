"""2026-10-16 ET. Deferred reserve67 metadata packet; no SWDB/native execution."""
import ast
import base64
import copy
import json
import zlib
from pathlib import Path

from author import HERE, SOURCE, constants, digest, encoded, pin


def main():
    base = HERE / 'inert-public61-c978393b'
    output = HERE / 'inert-reserve67-c978393b'
    pure = Path('/private/tmp/probata-resume-20261016-t25-pure-reserve67-c978393b')
    packet = json.loads((base / 'packet.json').read_bytes())
    for key, filename in [('entry', 'entry.py'), ('expected', 'expected.json'),
                          ('root_command', 'root-command.json')]:
        assert digest((base / filename).read_bytes()) == packet[key]['sha256']
    receipt = json.loads((pure / 'preparer-receipt.json').read_bytes())
    manifest = json.loads((pure / 'canonical/manifest.json').read_bytes())
    assert receipt['source_commit'] == SOURCE and receipt['target_count'] == 67
    assert receipt['external_native_attempts'] == []
    assert digest((pure / 'canonical/manifest.json').read_bytes()) == receipt['manifest_sha256']
    physical = [{'path': str(path.relative_to(pure / 'canonical')), 'bytes': path.stat().st_size,
                 'sha256': digest(path.read_bytes())}
                for path in sorted((pure / 'canonical').rglob('*')) if path.is_file()]
    assert physical == receipt['canonical_files'] and len(physical) == 76
    expected = json.loads((base / 'expected.json').read_bytes())
    expected.update(
        member='std_vector_int_realloc_v3_reserve', method_id='method.wp-qualified-reserve67-v1',
        canonical_manifest_sha256=receipt['manifest_sha256'], canonical_files=physical,
        canonical_reference_files=[row for row in physical if row['path'].startswith('references/')],
        model=manifest['model'], logical_obligations=manifest['logical_obligations'],
        target_ids=[row['id'] for row in manifest['obligations']],
        typed_source_image=manifest['typed_source_image'],
        status='INERT / UNREVIEWED / DEFERRED / NOT EXECUTED: fresh reserve67 requires independent review and root admission',
        scope='One complete qualified v3 reserve public profile, all67 current targets fresh including its61-target grow helper and numeric C. Both reserve branches and all five physical reference files remain required. No sibling/model/diagnostic theorem is imported. Normal public CLI, current method/source/runtime, ordinary/native/CSV/Counter/schema/persistence and numeric smoke checks; independent cold task/hypothesis audit mandatory. Original-v2/caller/ticket acceptance false.',
        cost_estimate='Scheduling allowance only:67fresh targets at up to90 solver seconds each gives6030seconds plus770seconds setup/report margin in6800public/6900profile/7100whole/7220outer. Actual runtime unmeasured; unchanged30seconds per solver and canonical full portfolio. Root schedules after focused10/current public gates; no result guarantee.',
    )
    expected['explicit_method_binding']['qualified_model'] = manifest['model']
    expected['resource_policy'].update(root_whole_seconds=7100, root_outer_seconds=7220,
                                       profile_seconds=6900, public_timeout_seconds=6800)
    new_expected = encoded(expected)
    old_expected = (base / 'expected.json').read_bytes()
    old_entry = (base / 'entry.py').read_bytes()
    replacements = [(digest(old_expected), digest(new_expected)), ('grow61', 'reserve67'),
                    ('complete61', 'complete67'), ('full61', 'full67'),
                    ("'fresh_targets':61", "'fresh_targets':67"), ('!=61', '!=67'),
                    ('targets=61', 'targets=67'),
                    ('Qualified v3 full grow contract-fixture method.',
                     'Qualified v3 full reserve contract-fixture method.')]
    text = old_entry.decode()
    for before, after in replacements:
        assert before in text
        text = text.replace(before, after)
    inverse = text
    for before, after in reversed(replacements):
        inverse = inverse.replace(after, before)
    assert inverse.encode() == old_entry
    new_entry = text.encode()
    ast.parse(new_entry)
    command = json.loads((base / 'root-command.json').read_bytes())
    bootstrap = command[6]
    substitutions = [
        (digest(old_entry), digest(new_entry)), (digest(old_expected), digest(new_expected)),
        (base64.b64encode(zlib.compress(old_entry, 9)).decode(),
         base64.b64encode(zlib.compress(new_entry, 9)).decode()),
        (base64.b64encode(zlib.compress(old_expected, 9)).decode(),
         base64.b64encode(zlib.compress(new_expected, 9)).decode()),
        ('grow61', 'reserve67'),
    ]
    for before, after in substitutions:
        assert before in bootstrap
        bootstrap = bootstrap.replace(before, after)
    inverse = bootstrap
    for before, after in reversed(substitutions):
        inverse = inverse.replace(after, before)
    assert inverse == command[6]
    ast.parse(bootstrap)
    assert len(bootstrap.encode()) < 120000
    embedded = constants(bootstrap, {'ENTRY_COMPRESSED_BASE64', 'EXPECTED_COMPRESSED_BASE64'})
    assert zlib.decompress(base64.b64decode(embedded['ENTRY_COMPRESSED_BASE64'], validate=True)) == new_entry
    assert zlib.decompress(base64.b64decode(embedded['EXPECTED_COMPRESSED_BASE64'], validate=True)) == new_expected
    command[6] = bootstrap
    output.mkdir(exist_ok=False)
    for name, data in [('entry.py', new_entry), ('expected.json', new_expected),
                       ('root-command.json', encoded(command))]:
        (output / name).write_bytes(data)
    result = {
        'created': '2026-10-16 ET', 'status': 'INERT / UNREVIEWED / DEFERRED / NOT EXECUTED',
        'source_commit': SOURCE, 'remote_project': expected['remote_project'],
        'root_kind': 't25-qualified-reserve67-public-v1',
        'entry': pin(output / 'entry.py'), 'expected': pin(output / 'expected.json'),
        'root_command': pin(output / 'root-command.json'), 'author': pin(Path(__file__)),
        'predecessor_public61_packet': pin(base / 'packet.json'),
        'pure_preparer_receipt': pin(pure / 'preparer-receipt.json'),
        'normal_public_route': True, 'full_fresh_targets': 67, 'check_lemmas': 66,
        'numeric_C_kernels': 1, 'canonical_files': 76, 'physical_reference_files': 5,
        'resource_policy': expected['resource_policy'], 'old_results_imported': 0,
        'entry_inverse_predecessor_equal': True, 'bootstrap_inverse_predecessor_equal': True,
        'embedded_roundtrip_exact': True, 'project_imports': 0, 'native_or_compiler_calls': 0,
        'independent_static_review_pending': True, 'root_admission_pending': True,
        'proof_acceptance': False, 'original_v2_acceptance': False,
        'caller_acceptance': False, 'ticket_closure': False,
    }
    (output / 'packet.json').write_bytes(encoded(result))
    print(json.dumps({'packet': pin(output / 'packet.json'),
                      'bootstrap_bytes': len(bootstrap.encode())}, indent=2))


if __name__ == '__main__':
    main()
