"""2026-10-16 ET. Closed source effects and all-incoming observation boundary."""
import copy
import json

import pytest

from testkit.vector_reallocation import CONTRACT


def test_closed_source_rule_derives_private_effects_before_observation(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_evidence as evidence
    source, lowering = lowered_no_growth
    directory = tmp_path/'source-rule'
    plan = evidence.prepare(lowering, source, CONTRACT, directory)
    assert evidence.check(lowering, source, CONTRACT, directory) == plan
    assert plan['original_contract'] == CONTRACT and plan['caller_premises_added'] == []
    assert plan['observation']['protected_objects'] == 'every incoming allocated program object, live or dead'
    assert plan['observation']['preserves'] == ['allocation identity', 'liveness', 'extent', 'address',
                                               'writability', 'contents of every byte', 'initialization of every byte']
    assert plan['observation']['incoming_type_restriction'] is None
    assert plan['observation']['total_Typed_to_Heap_encoding_claimed'] is False
    assert plan['native_projected_C']['role'] == 'supplemental conditional evidence only'
    assert plan['native_projected_C']['constructor_premise_discharged_by_native'] is False
    assert plan['native_projected_C']['smoke_timeout_implies_satisfiable'] is False
    assert len(plan['ordinary_source_discharge_ledger']) == 17
    assert len({row['goal'] for row in plan['ordinary_source_discharge_ledger']}) == 17
    assert all(row['uses_native_constructor_post_state'] is False and row['required_targets']
               for row in plan['ordinary_source_discharge_ledger'])
    assert plan['source_history']['receiver'] == 'not issued at caller entry'
    assert plan['source_history']['positive_buffer'] == 'not issued at caller entry and distinct from receiver'
    assert set(plan['branch_derivations']) == {'zero', 'positive'}
    for branch, derivation in plan['branch_derivations'].items():
        assert derivation['caller_visible_writes'] == []
        assert derivation['returned_pointer'] is False
        assert derivation['later_private_pointer_observation'] is False
        assert derivation['scalar_captured_before_release'] is True
        assert derivation['result'] == (0 if branch == 'zero' else 7)
        assert derivation['incoming_frame_induction']['all_steps_checked'] is True
        frame_steps = derivation['incoming_frame_induction']['steps']
        assert frame_steps[0]['operation'] == 'begin_automatic'
        assert any(row['operation'] == 'release' and row['target'] == ('null' if branch == 'zero' else 'buffer')
                   for row in frame_steps)
        assert derivation['terminal_cleanup']['receiver_scope_ended'] is True
        assert derivation['terminal_cleanup']['dynamic_buffer_released'] is (branch == 'positive')
    assert plan['source_safety']['null_plus_zero_used'] is False
    assert plan['source_safety']['positive_count_bound'] == 2147483647
    assert plan['source_safety']['model_maximum_count'] == 4611686018427387903
    assert plan['all_scientific_dependencies_admitted'] is False
    assert plan['source_admission'] is False and plan['caller_acceptance'] is False
    with pytest.raises(evidence.Refused):
        evidence.check_launch(lowering, source, CONTRACT, directory)


def test_closed_source_rule_refuses_removed_effect_observer_or_source_event(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_evidence as evidence
    source, lowering = lowered_no_growth
    for index, mutation in enumerate(['live_only', 'cleanup', 'pointer_escape', 'source_event', 'extra']):
        directory = tmp_path/str(index)
        plan = evidence.prepare(lowering, source, CONTRACT, directory)
        if mutation == 'extra':
            (directory/'unbound.json').write_text('{}')
        else:
            changed = copy.deepcopy(plan)
            if mutation == 'live_only':
                changed['observation']['protected_objects'] = 'incoming live integer objects'
            elif mutation == 'cleanup':
                changed['branch_derivations']['positive']['terminal_cleanup']['dynamic_buffer_released'] = False
            elif mutation == 'pointer_escape':
                changed['branch_derivations']['positive']['returned_pointer'] = True
            else:
                changed['source_events'] = changed['source_events'][:-1]
            (directory/'manifest.json').write_text(json.dumps(changed))
        with pytest.raises(evidence.Refused):
            evidence.check(lowering, source, CONTRACT, directory)
