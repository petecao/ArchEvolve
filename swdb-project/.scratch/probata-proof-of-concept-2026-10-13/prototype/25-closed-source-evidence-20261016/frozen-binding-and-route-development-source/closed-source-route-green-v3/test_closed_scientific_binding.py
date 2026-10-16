"""2026-10-16 ET. Explicit source-rule route and public observation controls."""
import copy
from pathlib import Path
import types

import pytest

from testkit.vector_reallocation import CONTRACT


SCIENTIFIC = Path(__file__).parent/'fixtures/proof/vector_closed_scientific_bundle'


def test_closed_source_route_requires_all_current_method_pins_and_keeps_native_history(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_route as route
    source, lowering = lowered_no_growth
    method = types.SimpleNamespace(id='method.wp-vector-closed-source-v1', data={
        'id': 'method.wp-vector-closed-source-v1', 'evidence_kind': 'contract_fixture',
        'c_lowering': {'translators': route.required_translators()}})
    assert route.selected(method)
    result = route.prepare(method, lowering, source, CONTRACT, SCIENTIFIC, tmp_path/'route')
    assert route.check(method, lowering, source, CONTRACT, SCIENTIFIC, tmp_path/'route') == result
    assert result['proof_basis'] == 'checked closed source observation rule and exact conditional mathematical evidence'
    assert result['original_contract'] == CONTRACT
    assert result['caller_premises_added'] == []
    assert result['scientific_target_count'] == 82
    assert len(result['source_obligations']) == 24
    assert all(goal['source'] == 'source_rule' and goal['status'] == 'valid' for goal in result['source_obligations'])
    assert result['original_diagnostic']['normal_verdict'] == 'not_proven'
    assert result['original_diagnostic']['original_entry_refusal_preserved'] is True
    assert result['native_projected_diagnostic']['normal_verdict'] == 'not_proven'
    assert result['native_projected_diagnostic']['role'] == 'supplemental conditional observation'
    assert result['source_typed_bridge_established'] is False
    assert result['current_model_records_created'] == []
    assert result['framework_integration_admitted'] is False
    assert all(result['pins'][name] in route.required_translators() for name in (
        'vector_closed_source_rule', 'vector_closed_scientific_binding', 'vector_closed_scientific_bundle'))
    assert any('freshness' in row['sentence'] and 'release' in row['sentence'] for row in result['assumptions'])
    with pytest.raises(route.Refused):
        route.check_launch(method, lowering, source, CONTRACT, SCIENTIFIC, tmp_path/'route')


def test_closed_source_route_does_not_enable_default_stale_or_partial_methods(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_route as route
    source, lowering = lowered_no_growth
    assert route.selected(types.SimpleNamespace(id='method.other', data={'c_lowering': {'translators': []}})) is False
    required = route.required_translators()
    for index, mutation in enumerate(('missing', 'stale', 'execution', 'wrong_function', 'hint', 'define', 'candidate')):
        method = types.SimpleNamespace(id='method.wp-vector-closed-source-v1', data={
            'id': 'method.wp-vector-closed-source-v1', 'evidence_kind': 'contract_fixture',
            'c_lowering': {'translators': copy.deepcopy(required)}})
        options = {}
        selected = copy.deepcopy(lowering)
        if mutation == 'missing':
            method.data['c_lowering']['translators'].pop()
        elif mutation == 'stale':
            method.data['c_lowering']['translators'][0]['sha256'] = '0'*64
        elif mutation == 'execution':
            method.data['evidence_kind'] = 'execution'
        elif mutation == 'wrong_function':
            object.__setattr__(selected, 'function', 'vector_realloc_v3_stale')
        elif mutation == 'hint':
            options['hints'] = [{'text': r'assert \true;'}]
        elif mutation == 'define':
            options['defines'] = ['ASSUME=1']
        else:
            options['candidate'] = 'candidate.other'
        with pytest.raises(route.Refused):
            route.prepare(method, selected, source, CONTRACT, SCIENTIFIC, tmp_path/str(index), **options)
