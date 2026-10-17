"""2026-10-16 ET. Versioned move/swap ownership packet controls."""
import json

import pytest


def test_owned_transfer_packet_binds_original_bodies_and_retains_source_duties(tmp_path):
    from swdb import vector_owned_transfer as transfer
    directory = tmp_path/'owned-transfer'
    plan = transfer.prepare(directory, elements=('int', 'float', 'double', 'int *'))
    assert transfer.check(directory, elements=('int', 'float', 'double', 'int *')) == plan
    assert plan['parent_model']['id'] == 'swdb-std-models-2'
    assert plan['source_admission'].startswith('unsupported:')
    assert plan['current_model_records_admitted'] == []
    assert plan['caller_premises_added'] == []
    assert plan['source_typed_bridge_established'] is False
    assert plan['domain']['exclusive_backing'] is True
    assert plan['domain']['raw_aliases_are_owners'] is False
    assert plan['domain']['identities'] == 'unbounded mathematical allocation identities; zero is no backing'
    assert {row['id'] for row in plan['obligations']} == {
        'empty.valid', 'receiver.fresh', 'buffer.fresh', 'move.transfer', 'move.frame',
        'swap.exchange', 'swap.frame', 'swap.self', 'retire.frame', 'shared_backing.rejected'}
    assert len(plan['source_members']) == 8
    for row in plan['source_members']:
        source = (directory/row['path']).read_text()
        assert row['original_body'] in source
        assert row['body_changed'] is False
        assert row['element_memory_accessed'] is False
        assert row['old_contract_proved'] is False
        if row['member'] == 'move_ctor':
            assert row['source_relation_requires'] == ['distinct source/destination receiver identities',
                'source established active owners', 'fresh empty destination ownership binding']
        else:
            assert row['self_swap_registry_identity'] is True
    assert 'actual original field reads/writes, layout and initializedness' in plan['pending_source_duties']
    assert 'source-derived ownership registration and complete existing owner set' in plan['pending_source_duties']
    for row in plan['obligations']:
        text = (directory/row['path']).read_text()
        assert 'check lemma '+row['goal'] in text
        assert 'axiom ' not in text and 'assume ' not in text
        assert row['dependencies'] == []
    with pytest.raises(ValueError, match='ownership protocol'):
        transfer.check_launch(directory, elements=('int', 'float', 'double', 'int *'))


def test_owned_transfer_packet_refuses_source_domain_and_claim_tampering(tmp_path):
    from swdb import vector_owned_transfer as transfer
    for change in ('move_body', 'ownership', 'source_claim', 'extra', 'redirect'):
        directory = tmp_path/change
        plan = transfer.prepare(directory)
        if change == 'move_body':
            row = next(row for row in plan['source_members'] if row['member'] == 'move_ctor')
            path = directory/row['path']
            path.write_text(path.read_text().replace('other->data = NULL;', 'other->data = this->data;'))
        elif change == 'ownership':
            path = directory/'theory/vector_owned_state.mlw'
            path.write_text(path.read_text().replace('predicate exclusive', 'predicate unreviewed_exclusive', 1))
        elif change == 'source_claim':
            path = directory/'manifest.json'
            changed = json.loads(path.read_text());changed['source_typed_bridge_established'] = True
            path.write_text(json.dumps(changed))
        elif change == 'extra':
            (directory/'accepted-proof.json').write_text('{}')
        else:
            target = directory/'prelude.acsl';target.unlink();target.symlink_to(directory/'manifest.json')
        with pytest.raises(ValueError):
            transfer.check(directory)


def test_owned_transfer_rejects_bool_class_and_noncanonical_or_repeated_types(tmp_path):
    from swdb import vector_owned_transfer as transfer
    for elements in (('bool',), ('Widget',), ('std::string',), ('int&',), ('const int',), ('int', 'int'), ()):
        directory = tmp_path/('case'+str(len(list(tmp_path.iterdir()))))
        with pytest.raises(ValueError):
            transfer.prepare(directory, elements=elements)
        assert not directory.exists()
