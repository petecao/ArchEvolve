"""Nonallocating vector body/domain boundaries; created 2026-10-16 ET."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from swdb import std_models


def test_all_registered_member_views_preserve_complete_contracts_and_payload_types():
    from swdb import standard_vector_member_view as view

    assert len(view.NAMES) == 32
    for name in view.NAMES:
        original = std_models.model_text(name)
        checked = view.wp_view(name, original)
        assert checked.original == original
        assert checked.certificate['original_contract_sha256'] == checked.certificate['view_contract_sha256']
        assert checked.certificate['acsl_input_premises_added'] == []
        assert checked.certificate['caller_domain_discharge_required'] is True
        if checked.member == 'at':
            assert 'at_guard_false' in checked.text
            assert checked.certificate['guard_elision_obligation'] == 'at_guard_false'
            assert checked.certificate['body_operations_removed'] == ['defensive abort branch under proven negated guard']
        else:
            assert checked.certificate['body_operations_removed'] == []
            assert checked.text == original
        view.check_view(name, checked)


def test_bounds_and_type_mutations_cannot_reuse_the_member_qualification():
    from swdb import standard_vector_member_view as view

    name = 'std_vector_float_at'
    original = std_models.model_text(name)
    for text in (original.replace('&& n < this->size', ''),
                 original.replace('return this->data + n;', 'return this->data + n + 1;'),
                 original.replace('float', 'double')):
        with pytest.raises(view.Refused):
            view.wp_view(name, text)
    checked = view.wp_view(name, original)
    with pytest.raises(view.Refused):
        view.check_view(name, replace(checked, text=checked.text.replace('n < this->size;', '1;')))
    with pytest.raises(view.Refused):
        view.wp_view('std_vector_bool_at', original)
    with pytest.raises(view.Refused):
        view.wp_view('std_vector_int_reserve', std_models.model_text('std_vector_int_reserve'))


def test_member_method_is_explicit_and_stale_or_partial_pins_refuse():
    from swdb import standard_vector_member_view as view

    method = SimpleNamespace(id='method.fixture', data={})
    assert view.selected(method) is False
    method = SimpleNamespace(id=view.METHOD, data={'id': view.METHOD,
        'evidence_kind': 'contract_fixture', 'c_lowering': {'translators': [view.identity()]}})
    assert view.selected(method) is True
    for translators in ([], [{**view.identity(), 'sha256': '0' * 64}], [view.identity()] * 2):
        stale = SimpleNamespace(id=view.METHOD, data={**method.data,
            'c_lowering': {'translators': translators}})
        with pytest.raises(view.Refused):
            view.selected(stale)
    for lowering in ('malformed', {'translators': 'malformed'}):
        with pytest.raises(view.Refused):
            view.selected(SimpleNamespace(id=view.METHOD, data={**method.data, 'c_lowering': lowering}))


def test_array_origin_binds_actual_this_declaration_and_data_field_only():
    from swdb import standard_vector_member_view as view

    name = 'std_vector_int_ptr_end'
    checked = view.wp_view(name, std_models.model_text(name))
    parameter = {'kind': 'ParmVarDecl', 'id': 'owner-1', 'name': 'this',
        'type': {'qualType': 'const std_vector_int_ptr *'}}
    definition = {'kind': 'FunctionDecl', 'name': name, 'inner': [parameter,
        {'kind': 'CompoundStmt'}]}
    node = {'kind': 'MemberExpr', 'name': 'data', 'isArrow': True,
        'type': {'qualType': 'int **'}, 'inner': [{'kind': 'DeclRefExpr',
            'referencedDecl': {'id': 'owner-1', 'kind': 'ParmVarDecl', 'name': 'this'}}]}
    origin = view.qualified_origin(checked, name, node, {name: definition})
    assert origin['element_type'] == 'int *'
    assert origin['elements'] == r'\at(this->capacity,Pre)'
    assert origin['caller_domain_discharge_required'] is True
    assert view.qualified_origin(checked, name, {**node, 'type': {'qualType': 'int **const'}},
        {name: definition}) == origin
    for bad in ({**node, 'name': 'other'}, {**node, 'isArrow': False},
                {**node, 'type': {'qualType': 'double **'}},
                {**node, 'inner': [{'kind': 'DeclRefExpr', 'referencedDecl': {'id': 'shadow'}}]}):
        assert view.qualified_origin(checked, name, bad, {name: definition}) is None
    assert view.qualified_origin(checked, name + '_other', node, {name: definition}) is None


def test_qualified_body_record_cannot_become_an_unqualified_caller_dependency():
    from swdb import standard_vector_member_view as view

    name = 'std_vector_double_operator_index'
    checked = view.wp_view(name, std_models.model_text(name))
    record = {'verdict': 'proven', 'subject': {'kind': 'c_model', 'id': name},
        'pins': {'code': {'id': name, 'sha256': checked.certificate['original_text_sha256']},
            'contract': {'id': name, 'sha256': checked.certificate['original_text_sha256']},
            'std_models': std_models.identity(), **checked.pins},
        'settings': {'standard_vector_member_view': checked.certificate}}
    assert view.check_record(name, record) == checked.certificate
    with pytest.raises(view.Refused, match='caller'):
        view.require_caller_discharge(name, record)
    bad = {**record, 'settings': {'standard_vector_member_view': {
        **checked.certificate, 'caller_domain_discharge_required': False}}}
    with pytest.raises(view.Refused):
        view.check_record(name, bad)
    for key in ('pins', 'settings'):
        with pytest.raises(view.Refused):
            view.check_record(name, {**record, key: 'malformed'})


@pytest.mark.parametrize('name', ['std_vector_int_end', 'std_vector_float_at',
    'std_vector_double_operator_index', 'std_vector_int_ptr_clear'])
def test_public_model_seam_records_qualified_domain_before_parser_standin(tmp_path, name):
    from pathlib import Path
    import yaml
    from swdb import c_lowering, standard_vector_member_view as view, std_models
    from testkit.standard_library import public_parser_standin_seed

    if c_lowering.locate().missing:
        pytest.skip('Clang 22.1.8 is required for the actual generated-C inventory')
    library, prove, marker = public_parser_standin_seed(tmp_path)
    original_method = library / 'methods/wp-tracer-fixture.yaml'
    method = yaml.safe_load(original_method.read_bytes())
    method['id'] = view.METHOD
    method['sequence'] = 3
    method['models']['std_vector'] = std_models.identity()
    method['c_lowering']['translators'].append(view.identity())
    (library / 'methods/wp-vector-member-source-v1.yaml').write_text(yaml.safe_dump(method, sort_keys=False))
    record = prove('--model', name, '--method-version', view.METHOD)
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'parse_error', record
    assert marker.exists()  # The selected parser-error stand-in ran; no solver or proof success.
    certificate = record['settings']['standard_vector_member_view']
    assert certificate == view.wp_view(name, std_models.model_text(name)).certificate
    assert record['pins']['standard_vector_member_view_check'] == view.identity()
    assert record['proof_setup_check']['runs'][-1]['hashes']['standard_vector_member_view']
    source = next(row for row in record['evidence']['reports'] if row['name'] == 'wp_input')
    text = Path(source['path']).read_text()
    assert '-wp-no-filter-init' in record['settings']['flags']
    assert '-rte-initialized' in record['settings']['flags']
    assert '-wp-smoke-tests' in record['settings']['flags']
    if name.endswith(('_end', '_at', '_operator_index')):
        assert 'swdb_model_pointer_formation_' in text
    if name.endswith('_at'):
        assert 'at_guard_false' in text


@pytest.mark.parametrize('mutation', ['none', 'qualification_omitted', 'formation_removed', 'domain_changed'])
def test_actual_prelaunch_rebuild_requires_domain_and_every_formation_obligation(tmp_path, mutation):
    from swdb import c_lowering, proof, proof_setup, standard_vector_member_view as view, wp_pointer_bounds

    if c_lowering.locate().missing:
        pytest.skip('Clang 22.1.8 is required for the actual generated-C inventory')
    name = 'std_vector_int_end'
    checked = view.wp_view(name, c_lowering.model_text(name))
    original = '\n'.join([*c_lowering.HEADERS, checked.text]) + '\n'
    with pytest.raises(wp_pointer_bounds.Refused, match='certified array-object origin'):
        wp_pointer_bounds.model_view(original, tmp_path)
    text, report = wp_pointer_bounds.model_view(original, tmp_path, vector_qualified=checked)
    with pytest.raises(wp_pointer_bounds.Refused, match='complete checked source'):
        wp_pointer_bounds.model_view(original + '\nint hidden(int*p){return p[1];}\n',
            tmp_path, vector_qualified=checked)
    method = SimpleNamespace(id=view.METHOD, data={'id': view.METHOD,
        'evidence_kind': 'contract_fixture', 'c_lowering': {
            'translators': [c_lowering.identity()['c_lowering'], view.identity()]}})
    adapter = SimpleNamespace(name='wp', library=None, method=method)
    unit = proof.ProofUnit(None, name, str(tmp_path), '0' * 64, 'c_model.' + name, '0' * 64)
    job = proof.Job(unit, (), tmp_path, tmp_path / 'adapter.log', bounds={}, budget_seconds=30)
    proof_setup.begin(job, adapter, {'method_version': {'not_applicable': 'Static prelaunch control.'}}, None)
    context = {'pointer_bounds_model_source': original, 'wp_expected_text': text,
        'pointer_bounds_report': report, 'standard_vector_member_view': {'view': checked}}
    if mutation == 'qualification_omitted':
        del context['standard_vector_member_view']
    elif mutation == 'formation_removed':
        text = text.replace('assert swdb_model_pointer_formation_', 'assert removed_formation_')
        context['wp_expected_text'] = text
    elif mutation == 'domain_changed':
        context['standard_vector_member_view']['view'] = replace(checked, certificate={})
    path = tmp_path / 'wp_input.c'
    path.write_text(text)
    flags = ['-wp-cache', 'none', '-machdep', 'x86_64', '-wp-model', '+real', '-wp-rte', '-wp-no-filter-init']
    if mutation == 'none':
        proof_setup.check_generated(job, adapter, context, [(path, text)], flags)
    else:
        with pytest.raises(proof.AdapterError, match='pointer_bounds'):
            proof_setup.check_generated(job, adapter, context, [(path, text)], flags)
