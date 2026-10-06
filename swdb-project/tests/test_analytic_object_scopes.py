"""Public bounded object/frame observer contract. Updated: 2026-10-06 ET."""
import json
from conftest import REPO, run_swdb


def characterize_scopes(records,tmp_path,llvm22,*extra):
    records.add_stub()
    mapping=tmp_path/'regions.json'
    mapping.write_text(json.dumps({'regions':[{'id':'fixture.scopes','function':'scope_reads','line_start':1,'line_end':100}]}))
    result=run_swdb('characterize','--records',records.path,'--source',
        REPO/'tests/fixtures/analytic/object_scopes.cpp','--implementation','stub-impl',
        '--input','tiny-sym','--function','scope_reads','--region-map',mapping,
        '--roi','fixture.scopes.v1','--id','fixture.scopes','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--fixture','--object-scopes','--format','json',*extra)
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
