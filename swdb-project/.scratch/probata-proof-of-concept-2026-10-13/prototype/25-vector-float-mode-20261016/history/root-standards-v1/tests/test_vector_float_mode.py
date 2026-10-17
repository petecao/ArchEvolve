"""2026-10-16 ET. Explicit symbolic floating copy-mode boundary controls."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace

import pytest

from swdb import std_models


def _method(mode):
    return SimpleNamespace(id=mode.METHOD, data={'id': mode.METHOD,
        'evidence_kind': 'contract_fixture', 'models': {'std_vector': std_models.identity()},
        'c_lowering': {'translators': [mode.identity()]},
        'lineup': [{'tool': 'frama-c-wp', 'version': '33.0',
                    'flags': ['-wp-cache', 'none', '-wp-model', '+float']}]})


def test_old_methods_keep_the_existing_real_model_selection():
    from swdb import vector_float_mode as mode

    for method in (None, SimpleNamespace(id='method.fixture', data={}),
                   SimpleNamespace(id='method.wp-vector-member-source-v1', data={})):
        assert mode.selected(method) is False
        assert mode.model_option(method) == '+real'


def test_symbolic_mode_preserves_all_six_original_copy_only_units_and_contracts():
    from swdb import vector_float_mode as mode

    method = _method(mode)
    assert mode.selected(method) is True and mode.model_option(method) == '+float'
    assert len(mode.NAMES) == 6
    for name in mode.NAMES:
        original = std_models.model_text(name)
        certificate = mode.check_source(method, name, original,
            method.data['lineup'][0]['flags'])
        assert certificate['function'] == name
        assert certificate['element_type'] in {'float', 'double'}
        assert certificate['original_source_sha256'] == hashlib.sha256(original.encode()).hexdigest()
        assert certificate['model_option'] == '+float'
        assert certificate['source_modified'] is False
        assert certificate['original_acsl_clauses_modified'] is False
        assert certificate['finite_or_non_NaN_requires_added'] is False
        assert certificate['actual_driver_and_goal_evidence_required'] is True
        assert certificate['source_or_lifetime_or_caller_admitted'] is False
        assert certificate['IEEE_bit_payload_preservation_proved'] is False
        mode.check_certificate(method, name, original, method.data['lineup'][0]['flags'], certificate)


def test_explicit_method_and_current_checker_model_and_version_pins_are_mandatory():
    from swdb import vector_float_mode as mode

    original = _method(mode)
    mutations = []
    for key, value in (('id', 'method.other'), ('evidence_kind', 'execution'),
                       ('models', {}), ('lineup', [])):
        data = deepcopy(original.data)
        data[key] = value
        mutations.append(SimpleNamespace(id=original.id, data=data))
    for translators in ([], [dict(mode.identity(), sha256='0' * 64)],
                        [mode.identity(), mode.identity()], 'malformed'):
        data = deepcopy(original.data)
        data['c_lowering']['translators'] = translators
        mutations.append(SimpleNamespace(id=original.id, data=data))
    for lineup in ([{'tool': 'frama-c-wp', 'version': '32.0'}],
                   original.data['lineup'] * 2):
        data = deepcopy(original.data)
        data['lineup'] = lineup
        mutations.append(SimpleNamespace(id=original.id, data=data))
    mutations.append(SimpleNamespace(id='method.other', data=deepcopy(original.data)))
    for method in mutations:
        with pytest.raises(mode.Refused):
            mode.selected(method)


def test_model_flags_refuse_erasure_duplicates_mixed_overrides_and_pseudo_values():
    from swdb import vector_float_mode as mode

    method = _method(mode)
    name = 'std_vector_float_ctor_count_value'
    source = std_models.model_text(name)
    for flags in ([], ['-wp-model', '+real'], ['-wp-model=+float'],
                  ['-wp-model', '+float', '-wp-model', '+float'],
                  ['-wp-model', '+float', '-wp-model=+real'],
                  ['-wp-model', '+float,+real'], ['-wp-model', '+cfloat'],
                  ['-wp-model', '+FLOAT'], ['-wp-model'], ['-wp-model', 1]):
        with pytest.raises(mode.Refused):
            mode.check_source(method, name, source, flags)


def test_source_certificate_cannot_expand_to_arithmetic_other_types_or_changed_clauses():
    from swdb import vector_float_mode as mode

    method = _method(mode)
    flags = method.data['lineup'][0]['flags']
    name = 'std_vector_double_copy_ctor'
    original = std_models.model_text(name)
    for source in (original + '\n', original.replace('other->data[k]', 'other->data[k] + 0.0'),
                   original.replace('other->data[j]', '0'),
                   original.replace('requires ', 'requires 1 && ', 1)):
        with pytest.raises(mode.Refused):
            mode.check_source(method, name, source, flags)
    for other in ('std_vector_int_copy_ctor', 'std_vector_float_move_ctor',
                  'std_vector_double_reserve', 'std_vector_int_ptr_ctor_count'):
        with pytest.raises(mode.Refused):
            mode.check_source(method, other, std_models.model_text(other), flags)
    certificate = mode.check_source(method, name, original, flags)
    for key, value in (('source_or_lifetime_or_caller_admitted', True),
                       ('IEEE_bit_payload_preservation_proved', True),
                       ('function', 'std_vector_float_copy_ctor'),
                       ('original_source_sha256', '0' * 64)):
        changed = deepcopy(certificate)
        changed[key] = value
        with pytest.raises(mode.Refused):
            mode.check_certificate(method, name, original, flags, changed)
