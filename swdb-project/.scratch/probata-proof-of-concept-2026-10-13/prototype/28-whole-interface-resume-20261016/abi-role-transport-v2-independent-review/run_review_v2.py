"""2026-10-16 ET. Reproduce the passive ABI source review; no actual replay."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V1 = WHOLE / 'abi-role-transport-v1'
V2 = WHOLE / 'abi-role-transport-v2'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('source review forbids child/native/network')


sys.addaudithook(audit)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


paths = set()


def add_rows(item):
    if isinstance(item, dict):
        if {'path', 'bytes', 'sha256'} <= set(item):
            path = Path(item['path'])
            assert pin(path) == {key: item[key] for key in ('path', 'bytes', 'sha256')}
            paths.add(path)
        for value in item.values(): add_rows(value)
    elif isinstance(item, list):
        for value in item: add_rows(value)


for selected in (V2 / 'source-packet-v2.json', V1 / 'source-packet-v1.json', V2 / 'adapter-inverse-v1.json'):
    paths.add(selected)
    add_rows(json.loads(selected.read_bytes()))
paths.update((HERE / 'test_independent_abi_v2.py', Path(__file__).resolve(),
    WHOLE / 'compiler_abi_probe_v1.cpp', WHOLE / 'whole_interface_v4.py'))
before = [pin(path) for path in sorted(paths)]


def run_suite(namespaces, count, label):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for namespace in namespaces:
        for name, value in namespace.items():
            if isinstance(value, type) and issubclass(value, unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(value))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    (HERE / (label + '.log')).write_text(output.getvalue())
    assert result.testsRun == count and result.wasSuccessful() and not result.skipped
    return {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'log': pin(HERE / (label + '.log'))}


independent = run_suite([runpy.run_path(str(HERE / 'test_independent_abi_v2.py'), run_name='reviewer_controls')], 9, 'independent-controls-v2')
author = run_suite([runpy.run_path(str(V2 / 'test_abi_transport_v1.py'), run_name='independent_author_controls'),
    runpy.run_path(str(V2 / 'test_prehash_v2.py'), run_name='independent_author_resource_controls')], 10, 'author-controls-independent-rerun-v2')
after = [pin(path) for path in sorted(paths)]
assert before == after and EVENTS == []

receipt = {
    'schema': 'independent-ABI-role-transport-source-review-2', 'date': '2026-10-16 ET',
    'verdict': 'PASS: scoped source-only helper and adapter proposal',
    'source_packet': pin(V2 / 'source-packet-v2.json'),
    'selected_helper': pin(V2 / 'abi_role_transport_v1.py'),
    'selected_adapter': pin(V2 / 'normalized_compiler_adapter_v2.py'),
    'reviewer_components_authored': ['independent controls and this review receipt only'],
    'source_files_checked_before_and_after': before,
    'source_pin_rows': len(before),
    'source_unchanged_after_review': before == after,
    'independent_controls': independent, 'author_controls_independent_rerun': author,
    'checks': {
        'complete_exact_two_edit_helper_inverse_to_held_V1': True,
        'four_edit_adapter_inverse_to_original_normalized_wrapper': True,
        'adapter_is_byte_identical_to_V1_successor': True,
        'generic_strict_decoder_and_all_legacy_functions_unchanged': True,
        'root_spans_ASCII_order_and_nonrole_tokens_retained': True,
        'synthetic_wrapper_removed_without_reencoding_declarations': True,
        'complete_original_minified_token_inverse_rechecked_by_real_primitive': True,
        'only_closed_exact_original_artifact_selectors_publicly_available': True,
        'unknown_duplicate_kind_key_order_shape_collision_and_count_refuse': True,
        'explicit_original_versus_actual_derived_ABI_input_identities': True,
        'source_call_IDs_never_joined_from_ABI_roots': True,
        'first_adapter_refuses_memory_family_before_legacy_consumer': True,
        'actual_canonical_regular_primitive_source_pins_still_required': True,
        'prehash_type_nonempty_extent_and_single_digest': True,
        'two_real_exact_primitive_installations_V1_RED_V2_GREEN': True,
        'synthetic_29_root_4_role_fixture_reaches_unchanged_ABI_reader_and_real_validate_abi': True,
    },
    'two_installation_scope': 'Exact pinned source bytes were copied into two explicit temporary canonical installations. V1 receipts differed only in primitive paths; V2 semantic receipts were exactly equal. Actual locations remain separately checked, not arbitrary module equivalence.',
    'synthetic_ABI_scope': 'The independent 29-root fixture is authored test data, with deliberately repeated IDs and both documented Type node kinds. It is never claimed to equal either retained compiler artifact or to establish their eligibility.',
    'physical_path_requirement': 'Before actual use, the enclosing independently admitted fixed observer control set and normal producer manifest must retain exact physical helper/adapter/normalizer/token source paths and bytes before/after. Stable role identities do not replace that closure.',
    'actual_retained_ABI_replay_executed': False,
    'memory_four_role_eligibility_observed_by_review': False,
    'full_TU_or_source_call_or_public_proof_admission': False,
    'native_compiler_verifier_SSH_child_or_network_executed': False,
    'real_project_modules_imported': False,
    'denied_runtime_events': EVENTS,
    'held_predecessor_and_actual_observer_refusal_preserved': True,
    'remaining_gate': 'Root-owned reviewed passive replay of both exact retained ABI artifacts through this helper and unchanged literal-value validator, then fresh observer/producer source-runtime closure and actual complete-TU admission.',
}
destination = HERE / 'independent-abi-v2-source-review-20261016.json'
destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({'review': pin(destination), 'independent_tests': independent['tests'],
    'author_tests': author['tests'], 'source_pin_rows': len(before), 'verdict': receipt['verdict']}, sort_keys=True))
