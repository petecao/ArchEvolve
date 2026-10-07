"""Public bounded object/frame observer contract. Updated: 2026-10-06 ET."""
import json
import pytest
import copy
from testkit.analytic import digest
from conftest import REPO, run_swdb, make_records


def characterize_scopes(records,tmp_path,llvm22,*extra,function="scope_reads",fixture="object_scopes.cpp",scopes=True):
    records.add_stub()
    mapping=tmp_path/'regions.json'
    mapping.write_text(json.dumps({'regions':[{'id':'fixture.scopes','function':function,'line_start':1,'line_end':100}]}))
    result=run_swdb('characterize','--records',records.path,'--source',
        REPO/'tests/fixtures/analytic'/fixture,'--implementation','stub-impl',
        '--input','tiny-sym','--function',function,'--region-map',mapping,
        '--roi','fixture.scopes.v1','--id','fixture.scopes','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--fixture','--format','json',
        *(['--object-scopes'] if scopes else []),*extra)
    assert result.returncode==0,result.stderr+result.stdout
    return json.loads(result.stdout)


def test_fixed_source_objects_cover_parent_pre_roi_and_callee_frame(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22)
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    # Each of two distinct 129-byte objects has three one-byte reads at 0,64,128.
    assert memory['requests_by_update_kind']['read'][0]['requests']['value']==6
    assert memory['useful_bytes']['value']==6
    assert memory['unknown_object_requests']['value']==0
    assert memory['lifetime_line_union']['value']==6
    assert memory['pre_roi_allocation_pages']['value']==1
    assert memory['in_roi_allocation_pages']['value']==1
    assert data['observation_contract']['object_scope_contract']['format']=='swdb.object-scopes.v1'
    checked=records.validate()
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_dynamic_source_extent_is_checked_and_retired_at_stackrestore(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22,'--run-arg','dynamic','--run-arg','129',function='scope_dynamic')
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    # Three writes and three reads in one runtime-sized 129-byte alloca.
    assert memory['useful_bytes']['value']==6
    assert memory['unknown_object_requests']['value']==0
    assert memory['lifetime_line_union']['value']==3
    assert memory['in_roi_allocation_pages']['value']==1


def test_openmp_abi_referent_view_covers_logical_load_without_allocation_claim(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22,'--build-flag=-fopenmp',
        function='scope_worker',fixture='object_scopes_openmp.cpp')
    memory=[r['memory_service_counts'] for r in data['regions']]
    assert sum(m['unknown_object_requests']['value'] for m in memory)==0
    scoped=[m for m in memory if m['object_scope_counts']['bounded_view_requests']['value']]
    # One outlined worker reads the ABI global-thread-id referent once.
    assert sum(m['object_scope_counts']['bounded_view_requests']['value'] for m in scoped)==1
    assert sum(m['object_scope_counts']['bounded_view_line_union']['value'] for m in scoped)==1
    assert all(m['lifetime_line_union']['value'] is None for m in scoped)
    assert all(m['pre_roi_allocation_pages']['value'] is None for m in scoped)
    assert all('bounded_view_not_full_allocation' in m['missing'] for m in scoped)
    assert records.validate().returncode==0


def test_caught_exception_retires_child_frames_before_caller_lifetime_start(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22,'--run-arg','recover',function='scope_recover')
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    assert memory['useful_bytes']['value']==3
    assert memory['unknown_object_requests']['value']==0
    assert memory['lifetime_line_union']['value']==3
    assert memory['in_roi_allocation_pages']['value']==1


def test_defined_global_has_declared_extent_and_pre_roi_lifetime(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22,'--run-arg','global',function='scope_global')
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    assert memory['useful_bytes']['value']==3
    assert memory['unknown_object_requests']['value']==0
    assert memory['lifetime_line_union']['value']==3
    assert memory['pre_roi_allocation_pages']['value']==1
    assert memory['in_roi_allocation_pages']['value']==0


def test_optional_scope_observer_preserves_original_source_ids_and_counts_when_absent(tmp_path,llvm22,monkeypatch):
    plain=tmp_path/'plain';plain.mkdir();scoped=tmp_path/'scoped';scoped.mkdir()
    monkeypatch.setenv('SWDB_OBJECT_SCOPES','1')
    legacy=characterize_scopes(make_records(plain),plain,llvm22,scopes=False)
    current=characterize_scopes(make_records(scoped),scoped,llvm22)
    assert 'object_scope_contract' not in legacy['observation_contract']
    assert legacy['static_analysis']['source_ir_sha256']==current['static_analysis']['source_ir_sha256']
    assert json.loads((plain/'counted/source.json').read_text())==json.loads((scoped/'counted/source.json').read_text())
    for old,new in zip(legacy['regions'],current['regions']):
        assert old['id']==new['id']
        assert old['access_patterns']==new['access_patterns']
        assert old['operation_counts']==new['operation_counts']
        assert old['dynamic_counts']==new['dynamic_counts']
        assert 'object_scope_counts' not in old['memory_service_counts']


def test_all_optional_scope_facts_reject_negative_values_after_fixture_resigning(records,tmp_path,llvm22):
    original=characterize_scopes(records,tmp_path,llvm22)
    for name in ('full_allocation_requests','bounded_view_requests','unresolved_requests','bounded_view_line_union'):
        data=copy.deepcopy(original)
        region=next(r for r in data['regions'] if r['id']=='fixture.scopes')
        region['memory_service_counts']['object_scope_counts'][name]['value']=-1
        data.pop('identity_sha256');data['identity_sha256']=digest(data)
        records.write('workload_characterizations/fixture.scopes.yaml',data)
        checked=records.validate()
        assert checked.returncode==1
        assert 'nonnegative' in checked.stdout+checked.stderr


def test_scope_coverage_partition_must_match_executed_requests(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22)
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    memory['object_scope_counts']['full_allocation_requests']['value']=5
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.scopes.yaml',data)
    result=records.validate()
    assert result.returncode==1
    assert 'partition' in result.stdout+result.stderr


def test_source_nonlocal_exit_keeps_unproved_recovered_frame_unknown(records,tmp_path,llvm22):
    data=characterize_scopes(records,tmp_path,llvm22,'--run-arg','nonlocal',function='scope_nonlocal')
    memory=next(r for r in data['regions'] if r['id']=='fixture.scopes')['memory_service_counts']
    assert memory['useful_bytes']['value']==3
    assert memory['unknown_object_requests']['value']==3
    assert 'nonlocal_control_flow' in memory['missing']


@pytest.mark.parametrize('mode',['ordinary','throw'])
def test_object_scopes_preserve_functional_command_domains_and_request_partitions(records,tmp_path,llvm22,mode):
    from test_analytic_commands import characterize_command
    extra=('--object-scopes',)+(('--run-arg','throw') if mode=='throw' else ())
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=extra)
    assert data['observation_contract']['object_scope_contract']['format']=='swdb.object-scopes.v1'
    if mode=='ordinary':
        assert data['observation_contract']['semantic_commands']['complete'] is True
        observed=next(region['address_stream_counts'][target_hash] for region in data['regions']
            if region['address_stream_counts'][target_hash]['line_requests']['value'])
        assert observed['line_requests']['value']==6
        assert observed['row_groups']['value']==3 and observed['windows']['value']==2
    else:
        assert any('command_unwind' in region['address_stream_counts'][target_hash]['missing'] for region in data['regions'])
        host_stores=[access for region in data['regions'] for access in region['access_patterns']
            if access['source_location']['function']=='main' and access['update_kind']=='write' and access['element_count']['value']]
        assert host_stores
    for region in data['regions']:
        memory=region['memory_service_counts']
        requests=sum(item['requests']['value'] for rows in memory['requests_by_update_kind'].values() for item in rows)
        if 'object_scope_counts' in memory:
            facts=memory['object_scope_counts']
            assert sum(facts[name]['value'] for name in
                ('full_allocation_requests','bounded_view_requests','unresolved_requests'))==requests
        else:
            assert requests==0 # No executed host access; offload requests stay in their command domain.
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr
