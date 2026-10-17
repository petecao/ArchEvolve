"""2026-10-16 ET. Real retained scientific evidence and closed source binding."""
import json
from pathlib import Path
import shutil

import pytest

from testkit.vector_reallocation import CONTRACT


SCIENTIFIC = Path(__file__).parent/'fixtures/proof/vector_closed_scientific_bundle'


def test_closed_binding_matches_all_scientific_targets_without_relabeling_history(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_binding as binding
    source, lowering = lowered_no_growth
    directory = tmp_path/'bound'
    result = binding.prepare(lowering, source, CONTRACT, SCIENTIFIC, directory)
    assert binding.check(lowering, source, CONTRACT, SCIENTIFIC, directory) == result
    assert result['scientific_dependencies_bound'] is True
    assert result['source_rule']['original_contract'] == CONTRACT
    assert result['source_rule']['caller_premises_added'] == []
    components = {row['id']: row for row in result['components']}
    assert {name: len(row['targets']) for name, row in components.items()} == {
        'constructor': 35, 'destructor': 11, 'private_frame': 9, 'gluing': 4, 'positive': 23}
    assert result['complete_source_target_count'] == 82
    assert all(row['historical_identity_preserved'] for row in components.values())
    assert len({row['historical_source_commit'] for row in components.values()}) == 5
    assert result['current_model_records_created'] == []
    assert result['historical_records_rewritten'] is False
    assert result['original_two_timeout_results_preserved'] is True
    assert result['original_native_reader_not_proven_preserved'] is True
    assert result['source_typed_bridge_established'] is False
    assert result['proof_basis'] == 'checked closed source observation rule and exact conditional mathematical evidence'
    assert result['source_admission'] is False and result['public_proof_record_created'] is False
    with pytest.raises(binding.Refused):
        binding.check_launch(lowering, source, CONTRACT, SCIENTIFIC, directory)
    manifest = directory/'manifest.json'
    changed = json.loads(manifest.read_bytes())
    changed['historical_records_rewritten'] = True
    manifest.write_text(json.dumps(changed))
    with pytest.raises(binding.Refused):
        binding.check(lowering, source, CONTRACT, SCIENTIFIC, directory)


def test_closed_binding_refuses_changed_targets_context_or_historical_scope(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_binding as binding
    source, lowering = lowered_no_growth
    for index, mutation in enumerate(['missing', 'goal', 'statement', 'input', 'history', 'timeout', 'cold', 'object', 'extra']):
        bundle = tmp_path/(str(index)+'-bundle')
        shutil.copytree(SCIENTIFIC, bundle)
        catalog = json.loads((bundle/'catalog.json').read_bytes())
        components = {row['id']: row for row in catalog['components']}
        row = components['constructor']['targets'][0]
        if mutation == 'missing':
            components['constructor']['targets'].pop()
        elif mutation == 'goal':
            row['goal'] = str(row['goal'])+'_unbound'
        elif mutation == 'statement':
            row['statement'] = str(row['statement'])+r' && \false'
        elif mutation == 'input':
            row['input_sha256'] = '0'*64
        elif mutation == 'history':
            components['constructor']['historical_identity']['source_commit'] = 'current-relabel'
        elif mutation == 'timeout':
            replacement = dict(components['gluing']['targets'][0])
            replacement['id'] = 'positive.cleanup'
            components['gluing']['targets'].append(replacement)
        elif mutation == 'cold':
            components['constructor']['cold_evidence'] = []
        elif mutation == 'object':
            context = components['constructor']['context']['canonical_manifest']['document']
            path = bundle/context['path']
            value = json.loads(path.read_bytes())
            value['obligations'][0]['statement'] = r'\true'
            path.write_text(json.dumps(value))
        else:
            (bundle/'unbound.c').write_text('/* raw/foreign material is not an evidence object */')
        if mutation not in {'object', 'extra'}:
            (bundle/'catalog.json').write_text(json.dumps(catalog))
        with pytest.raises(binding.Refused):
            binding.prepare(lowering, source, CONTRACT, bundle, tmp_path/(str(index)+'-bound'))


def test_closed_binding_rechecks_source_and_contract_before_reusing_science(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_binding as binding
    source, lowering = lowered_no_growth
    changed = tmp_path/'changed.cc'
    changed.write_text(source.read_text().replace('return n > 0 ? *saved : 0;', 'return n > 0 ? *saved : 1;'))
    assert changed.read_bytes() != source.read_bytes()
    with pytest.raises(binding.Refused):
        binding.prepare(lowering, changed, CONTRACT, SCIENTIFIC, tmp_path/'source-bound')
    with pytest.raises(binding.Refused):
        binding.prepare(lowering, source, [r'requires count >= 0; ensures \result == 123;'],
                        SCIENTIFIC, tmp_path/'contract-bound')
