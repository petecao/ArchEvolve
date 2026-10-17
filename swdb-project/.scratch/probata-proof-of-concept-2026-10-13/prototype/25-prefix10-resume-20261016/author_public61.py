"""2026-10-16 ET. Author a deferred public61 packet; no SWDB/native execution."""
import ast
import base64
import copy
import json
import zlib

from author import HERE, OUTPUT, SNAPSHOT, constants, digest, encoded, pin


def main():
    output = HERE / 'inert-public61-c978393b'
    prior = SNAPSHOT / 'historical-deferred-full52'
    stem = 'probata-t25-qualified-grow52-public-'
    suffix = '-v1-3a48da2f-20261016'
    old_paths = {name: prior / (stem + name + suffix + extension)
                 for name, extension in [('entry', '.py'), ('expected', '.json'),
                                          ('root-command', '.json'), ('packet', '.json')]}
    packet = json.loads(old_paths['packet'].read_bytes())
    for name in ['entry', 'expected', 'root-command']:
        assert digest(old_paths[name].read_bytes()) == packet[name.replace('-', '_')]['sha256']
    old_entry, old_expected = old_paths['entry'].read_bytes(), old_paths['expected'].read_bytes()
    base_packet = json.loads((OUTPUT / 'packet.json').read_bytes())
    expected = json.loads((OUTPUT / 'expected.json').read_bytes())
    assert digest(encoded(expected)) == base_packet['expected']['sha256']
    expected.pop('diagnostic_ids')
    references = [row for row in expected['canonical_files'] if row['path'].startswith('references/')]
    assert len(references) == 5 and len(expected['target_ids']) == 61
    expected.update(
        canonical_reference_files=references, method_id='method.wp-qualified-grow61-v1',
        status='INERT / UNREVIEWED / NOT EXECUTED: deferred until focused10 review and root admission',
        scope='One fresh complete qualified v3 grow public profile: all61 current targets (60 mathematical source duties plus numeric C), three top-level logical groups/five physical references. No old prefix or diagnostic result promoted, no sibling theorem assumed. Normal public adapter/report/schema/persistence and actual-derived complete RTE/init/smoke census; independent final cold review mandatory. Original-v2/caller/ticket acceptance false.',
        prior_results_not_reused=['all historical partial grow profiles', 'all focused copy-step/prefix diagnostics',
                                 'all scripted workflow controls', 'all prior public body records'],
        cost_estimate='Scheduling bound only:61 fresh targets at up to90 solver seconds each gives5490 seconds, with810 seconds setup/report margin in6300 public/6400profile/6600whole/6720outer. Actual timings remain unmeasured. Canonical per-goal30seconds, three-solver portfolio and all acceptance policies are unchanged. Root must choose launch timing after focused10; no success or runtime prediction is claimed.',
    )
    expected['resource_policy'].update(root_whole_seconds=6600, root_outer_seconds=6720,
                                       profile_seconds=6400, public_timeout_seconds=6300)
    expected['resource_policy'].pop('leaf_timeout_seconds', None)
    new_expected = encoded(expected)
    replacements = [(digest(old_expected), digest(new_expected)),
                    ('grow52', 'grow61'), ('complete52', 'complete61'), ('full52', 'full61'),
                    ("'fresh_targets':52", "'fresh_targets':61"), ('!=52', '!=61'),
                    ('targets=52', 'targets=61'),
                    ("len(expected['canonical_reference_files'])!=4", "len(expected['canonical_reference_files'])!=5"),
                    ('all four original whole-target reference C files required',
                     'all five original whole-target reference C files required')]
    text = old_entry.decode()
    for before, after in replacements:
        assert before in text
        text = text.replace(before, after)
    new_entry = text.encode()
    inverse = text
    for before, after in reversed(replacements):
        inverse = inverse.replace(after, before)
    assert inverse.encode() == old_entry
    ast.parse(new_entry)
    command = json.loads(old_paths['root-command'].read_bytes())
    bootstrap = command[6]
    substitutions = [
        (digest(old_entry), digest(new_entry)), (digest(old_expected), digest(new_expected)),
        (base64.b64encode(zlib.compress(old_entry, 9)).decode(),
         base64.b64encode(zlib.compress(new_entry, 9)).decode()),
        (base64.b64encode(zlib.compress(old_expected, 9)).decode(),
         base64.b64encode(zlib.compress(new_expected, 9)).decode()),
        ('grow52', 'grow61'),
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
        'source_commit': expected['source_commit'], 'remote_project': expected['remote_project'],
        'root_kind': 't25-qualified-grow61-public-v1',
        'entry': pin(output / 'entry.py'), 'expected': pin(output / 'expected.json'),
        'root_command': pin(output / 'root-command.json'), 'author': pin(HERE / 'author_public61.py'),
        'current_metadata_packet': pin(OUTPUT / 'packet.json'),
        'historical_public52_packet': pin(old_paths['packet']),
        'entry_inverse_predecessor_equal': True, 'bootstrap_inverse_predecessor_equal': True,
        'embedded_roundtrip_exact': True, 'normal_public_route': True,
        'full_fresh_targets': 61, 'check_lemmas': 60, 'numeric_C_kernels': 1,
        'canonical_files': 70, 'physical_reference_files': 5, 'old_results_imported': 0,
        'resource_policy': expected['resource_policy'],
        'project_imports': 0, 'native_or_compiler_calls': 0,
        'independent_static_review_pending': True, 'root_admission_pending': True,
        'proof_acceptance': False, 'original_v2_acceptance': False,
        'caller_acceptance': False, 'ticket_closure': False,
    }
    (output / 'packet.json').write_bytes(encoded(result))
    print(json.dumps({'packet': pin(output / 'packet.json'),
                      'bootstrap_bytes': len(bootstrap.encode())}, indent=2))


if __name__ == '__main__':
    main()
