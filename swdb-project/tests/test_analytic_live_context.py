"""Public live-object characterization seam. Updated: 2026-10-06 ET.
Logical source observations never establish physical cache/DRAM requests.
"""
import json
import yaml
import pytest
from testkit.analytic import digest
from conftest import REPO, run_swdb


def characterize_lifetimes(records,tmp_path,llvm22,*extra):
    records.add_stub()
    mapping=tmp_path/'regions.json'
    mapping.write_text(json.dumps({'regions':[{'id':'fixture.loads','function':'observe','line_start':1,'line_end':100}]}))
    result=run_swdb('characterize','--records',records.path,
        '--source',REPO/'tests/fixtures/analytic/lifetimes.cpp','--implementation','stub-impl',
        '--input','tiny-sym','--function','observe','--region-map',mapping,
        '--roi','fixture.lifetimes.v1','--id','fixture.lifetimes','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--fixture','--format','json',*extra)
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    return data


def test_pre_roi_arrays_and_interior_aliases_keep_lifetime_namespaces(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22)
    region=next(r for r in data['regions'] if r['id']=='fixture.loads')
    memory=region['memory_service_counts']
    assert memory['requests_by_update_kind']['read']==[{'element_bytes':4,'requests':{'value':6,'basis':'measured','scope':'per_run'}}]
    assert memory['lifetime_line_union']['value']==5
    assert memory['logical_first_read_pages']['value']==2
    assert memory['pre_roi_allocation_pages']['value']==2
    assert memory['in_roi_allocation_pages']['value']==0
    assert memory['unknown_object_requests']['value']==0
    assert data['observation_contract']['level']=='source_normalized_ir'
    assert data['counting']['observation_format']=='swdb.live-count-context.v1'
    raw=json.loads((tmp_path/'counted/counts.json').read_text())
    assert all(key not in json.dumps(raw) for key in ('allocation_base','address_sequence','decoded_rows'))
    checked=records.validate()
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_bounded_state_keeps_requests_but_marks_union_incomplete(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--state-budget','2')
    region=next(r for r in data['regions'] if r['id']=='fixture.loads')
    memory=region['memory_service_counts']
    assert memory['requests_by_update_kind']['read'][0]['requests']['value']==6
    assert memory['useful_bytes']['value']==24
    assert memory['lifetime_line_union']['value'] is None
    assert 'state_budget.lifetime_line_union' in memory['missing']
    assert data['observation_contract']['state_budget']==2


def test_roi_reset_keeps_live_objects_and_prior_logical_touches(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--run-arg','reuse','--run-arg','second-trial')
    assert len(data['trials'])==2
    first=next(r for r in data['trials'][0]['regions'] if r['id']=='fixture.loads')['memory_service_counts']
    second=next(r for r in data['trials'][1]['regions'] if r['id']=='fixture.loads')['memory_service_counts']
    assert first['lifetime_line_union']['value']==7
    assert first['in_roi_allocation_pages']['value']==1
    assert second['lifetime_line_union']['value']==2
    assert second['pre_roi_allocation_pages']['value']==1
    assert second['logical_first_read_pages']['value']==0
    assert second['unknown_object_requests']['value']==0
    assert second['requests_by_update_kind']['read'][0]['requests']['scope']=='per_trial'


def test_trial_observation_payload_is_validated_as_strictly_as_aggregate(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--run-arg','reuse','--run-arg','second-trial')
    region=next(r for r in data['trials'][1]['regions'] if r['id']=='fixture.loads')
    del region['memory_service_counts']['requests_by_update_kind']
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.lifetimes.yaml',data)
    result=records.validate()
    assert result.returncode==1
    assert 'requests_by_update_kind' in result.stdout+result.stderr


def test_placement_new_alias_does_not_replace_backing_allocation(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--run-arg','placement')
    memory=next(r for r in data['regions'] if r['id']=='fixture.loads')['memory_service_counts']
    assert memory['lifetime_line_union']['value']==5
    assert memory['unknown_object_requests']['value']==0


@pytest.mark.parametrize('trial',[False,True])
def test_negative_observer_work_is_refused_even_with_a_resigned_fixture_identity(records,tmp_path,llvm22,trial):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--run-arg','reuse','--run-arg','second-trial')
    rows=data['trials'][1]['regions'] if trial else data['regions']
    region=next(r for r in rows if r['id']=='fixture.loads')
    region['memory_service_counts']['useful_bytes']['value']=-1
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.lifetimes.yaml',data)
    result=records.validate()
    assert result.returncode==1
    assert 'nonnegative' in result.stdout+result.stderr


def characterize_services(records,tmp_path,llvm22,*extra):
    records.add_stub()
    result=run_swdb('characterize','--records',records.path,
        '--source',REPO/'tests/fixtures/analytic/services.cpp','--implementation','stub-impl',
        '--input','tiny-sym','--function','services','--roi','fixture.services.v1',
        '--id','fixture.services','--llvm-bin',llvm22,'--output',tmp_path/'counted',
        '--fixture','--format','json',*extra)
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    return data


def test_executed_call_lengths_and_free_lifetimes_are_counted_without_addresses(records,tmp_path,llvm22):
    data=characterize_services(records,tmp_path,llvm22)
    calls=[call for region in data['regions'] for call in region['call_shape_counts']['calls']]
    allocated=next(c for c in calls if c['name']=='malloc')
    freed=next(c for c in calls if c['name']=='free')
    assert allocated['execution_count']['value']==freed['execution_count']['value']==3
    assert [(b['bytes'],b['execution_count']['value']) for b in allocated['known_length_bins']]==[(64,2),(128,1)]
    assert [(b['bytes'],b['execution_count']['value']) for b in freed['allocation_lifetime_size_bins']]==[(64,2),(128,1)]
    assert freed['unknown_free_lifetimes']['value']==0
    assert data['observation_contract']['call_abi']=='swdb.call.v2'
    checked=records.validate()
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_call_histogram_budget_preserves_execution_totals_and_unknown_bins(records,tmp_path,llvm22):
    data=characterize_services(records,tmp_path,llvm22,'--state-budget','1')
    calls=[call for region in data['regions'] for call in region['call_shape_counts']['calls']]
    allocated=next(c for c in calls if c['name']=='malloc')
    freed=next(c for c in calls if c['name']=='free')
    assert allocated['execution_count']['value']==3
    # The actual pre-loop memcpy consumes the sole global histogram bin.
    assert allocated['unknown_lengths']['value']==3
    assert sum(b['execution_count']['value'] for b in allocated['known_length_bins'])+allocated['unknown_lengths']['value']==3
    assert freed['unknown_free_lifetimes']['value']==3


def test_registered_cxx11_build_contract_keeps_live_objects(records,tmp_path,llvm22):
    data=characterize_lifetimes(records,tmp_path,llvm22,'--build-flag=-std=c++11')
    memory=next(r for r in data['regions'] if r['id']=='fixture.loads')['memory_service_counts']
    assert memory['lifetime_line_union']['value']==5
    assert memory['unknown_object_requests']['value']==0
