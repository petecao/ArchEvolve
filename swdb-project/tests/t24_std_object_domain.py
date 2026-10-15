"""Explicitly qualified fixture contract; production runtime stays unchanged, 2026-10-15 ET."""
import copy
from test_wp_subset import GROUPS, UNITS, _entry, contract_id

QUALIFIED_ID = 'contract.fixture_wp24_std_models_object_domain'
GAP_LABEL = 'std_models_original_contract_gap'


def original_contract():
    function, clauses, arrays, _hints = GROUPS['std_models']
    data = _entry(contract_id('std_models'), function, 'subset_units.cc', UNITS,
                  clauses, arrays, 'per_candidate')
    data['proof_unit']['array_domains'] = {name: {'extent': 'n'} for name in ('a', 'b')}
    return data


def corrected_contract(original):
    if original != original_contract():
        raise ValueError('qualification requires the exact original std fixture contract')
    data = copy.deepcopy(original)
    data['id'] = QUALIFIED_ID
    domains = [rf'({p} == \null || \valid_read({p}) || '
               rf'(\base_addr({p} - 1) == \base_addr({p}) && \valid_read({p} - 1)))'
               for p in ('a', 'b')]
    data['clauses'].insert(1, {
        'id': 'empty_object_domain', 'role': 'legality',
        'statement': 'For an empty range each endpoint is null, readable, or one past a readable same-base element. '
                     'This explicit conservative domain excludes the zero-size-allocation proxy gap.',
        'discharge_mode': 'runtime_guard',
        'negative_control': {'id': 'empty-object-domain-control', 'check': 'explicit_object_or_one_past'},
        'acsl': {'text': 'requires n == 0 ==> (' + ' && '.join(domains) + ');', 'uses': []},
        'proof_placement': 'per_candidate'})
    return data
