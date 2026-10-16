"""2026-10-16 ET. Pure pending reserve application, without caller admission."""
import hashlib

from swdb import vector_reallocation_composition as composition
from swdb import vector_reallocation_model as model


def candidate(request='count+1', observation='current buffer'):
    # Worked metadata at the pure composition boundary. The public packet route
    # supplies its independently checked original/lowered physical source spans.
    return {
        'count': {'name': 'n', 'type': 'int'}, 'reserve_request': request,
        'observation': observation,
        'capacity_qualification': {'id': 'vector-cpp17-capacity-1',
                                   'model_postcondition_to_prove': 'capacity == count'},
        'call_obligations': [{'call': 'reserve', 'source': {
            'begin': 0, 'end': 25, 'sha256': 'source-reserve-span'}}],
        'lowered_lifetime': {'events': [{'event': 'reserve',
            'lowered_source': {'begin': 40, 'end': 81, 'sha256': 'lowered-reserve-span'},
            'reachable_on_normal_return': True}]},
    }


def test_growing_reserve_entry_derives_request_bound_and_branch_from_pending_constructor_capacity():
    source = candidate()
    row, receipt = composition.reserve_entry(source)
    assert row['id'] == 'apply.reserve.entry'
    assert row['statement'] == (
        r'\forall Heap::heap h; \forall integer r,o,b,bo,n; '
        r't25v3_eligible(h,r,o,b,bo,n,n) && 0 <= n <= 2147483647 ==> '
        r't25v3_eligible(h,r,o,b,bo,n,n) && 0 <= (n+1) <= 4611686018427387903 && (n+1) > n')
    assert row['dependencies'] == [] and row['status'] == 'pending'
    assert row['source'] == source['call_obligations'][0]['source']
    assert row['lowered_events'] == source['lowered_lifetime']['events']
    assert receipt['source_request'] == 'count+1' and receipt['request_term'] == '(n+1)'
    assert receipt['growth_branch'] is True and receipt['state_before'] == 'h'
    assert receipt['state_after'] == 'pending current qualified grow application'
    assert receipt['predecessor_discharge'].startswith('pending completed constructor')
    assert receipt['caller_premises_added'] == [] and receipt['current_proof_records_admitted'] == []
    for key, member in [('callee_precondition', 'reserve'),
                        ('branch_and_call', 'reserve'),
                        ('constructor_exact_capacity', 'ctor_count_value')]:
        raw = model.model_text('std_vector_int_realloc_v3_' + member).encode()
        span = receipt[key]
        assert hashlib.sha256(raw[span['begin']:span['end']]).hexdigest() == span['sha256']
        assert hashlib.sha256(raw).hexdigest() == span['source_sha256']
    assert receipt['buffer_element_loads'] == 0


def test_no_growth_reserve_application_preserves_the_same_source_state_without_importing_a_summary():
    row, receipt = composition.reserve_entry(candidate('count', 'captured alias'))
    assert row['statement'] == (
        r'\forall Heap::heap h; \forall integer r,o,b,bo,n; '
        r't25v3_eligible(h,r,o,b,bo,n,n) && 0 <= n <= 2147483647 ==> '
        r't25v3_eligible(h,r,o,b,bo,n,n) && 0 <= n <= 4611686018427387903 && n <= n')
    assert receipt['growth_branch'] is False and receipt['request_term'] == 'n'
    assert receipt['state_after'] == 'h' and receipt['source_effect'] == 'branch false; no body store or call'
    assert receipt['buffer_element_loads'] == 0 and row['dependencies'] == []
    assert receipt['proof_status'] == 'unexecuted source-local entry/branch duty; no reserve or caller theorem granted'


def test_reserve_entry_refuses_unknown_request_type_or_missing_capacity_predecessor():
    for change in ['request', 'type', 'capacity', 'witness']:
        source = candidate()
        if change == 'request':
            source['reserve_request'] = 'count+2'
        elif change == 'type':
            source['count']['type'] = 'unsigned int'
        elif change == 'capacity':
            source['capacity_qualification']['model_postcondition_to_prove'] = 'capacity >= count'
        else:
            source['capacity_qualification']['id'] = 'unreviewed-capacity-source'
        try:
            composition.reserve_entry(source)
        except ValueError:
            continue
        raise AssertionError('unsupported reserve predecessor or source arithmetic accepted')


def test_growing_current_and_stale_observation_receive_no_liveness_or_value_fact():
    safe, safe_receipt = composition.reserve_entry(candidate())
    stale, stale_receipt = composition.reserve_entry(candidate(observation='captured alias'))
    assert safe == stale and safe_receipt == stale_receipt
    assert 'Heap::load_int' not in stale['statement'] and 'Heap::can_read' not in stale['statement']
    assert 'n > 0' not in stale['statement']
    assert stale_receipt['remaining'] == [
        'completed constructor state/capacity/typed-image source-runtime discharge',
        'current reserve/grow body-record admission and branch application',
        'observation, stale-alias liveness, cleanup and final incoming frame',
    ]
