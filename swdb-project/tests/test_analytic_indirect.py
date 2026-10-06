"""Independent shape/count fixtures through the public CLI. Updated: 2026-10-06 ET."""
import json
import shutil
from pathlib import Path

import pytest
from conftest import REPO,run_swdb

@pytest.mark.parametrize("function,shape,elements,unique_bytes",[
    ("gather","single_valued_indirect",4,12),
    ("ranged","ranged_indirect",5,20),
    ("chase","pointer_chase",3,24),
    ("merge","data_dependent_merge",4,16),
])
def test_independent_indirect_shapes_and_useful_counts(tmp_path,llvm22,function,shape,elements,unique_bytes):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/indirect.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function',function,
        '--run-arg',function,'--fixture','--id','fixture.'+function,'--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    accesses=[a for r in data['regions'] for a in r['access_patterns'] if a['address_shape']['value']==shape]
    assert accesses,'Missing shape '+shape
    if function=='chase': accesses=[a for a in accesses if a['element_bytes']==8]
    assert sum(a['element_count']['value'] for a in accesses)==elements
    assert sum(a['observed_unique_bytes']['value'] for a in accesses)==unique_bytes
    assert data['unmapped_loops']
    checked=run_swdb('validate','--records',records)
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_registered_gapbs_rejects_arbitrary_translation_unit(tmp_path):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--adapter','registered-gapbs',
        '--source',REPO/'tests/fixtures/analytic/indirect.cpp','--implementation','gapbs-bfs-do',
        '--input','kron-g16-k16','--id','invalid.registered')
    assert result.returncode==1
    assert 'registered translation unit' in result.stderr


@pytest.mark.parametrize("implementation,patterns",[("gapbs-bfs-do",13),("gapbs-bc-brandes",20)])
def test_registered_gapbs_counts_trial_lambda_and_workers(tmp_path,llvm22,implementation,patterns):
    import yaml
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    input_path=records/'inputs/kron-g16-k16.yaml'
    data=yaml.safe_load(input_path.read_text())
    data.update(id='fixture.kron.g4',name='Independent small generated graph')
    data['generator']['arguments']='-g 4 -k 2'
    data['properties']={}
    (records/'inputs/fixture.kron.g4.yaml').write_text(yaml.safe_dump(data,sort_keys=False))
    result=run_swdb('characterize','--records',records,'--adapter','registered-gapbs',
        '--implementation',implementation,'--input','fixture.kron.g4','--threads','2','--trials','3',
        '--id','fixture.registered','--llvm-bin',llvm22,'--run-library-path',llvm22.parent/'lib',
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    assert data['binding']['state']=='verified'
    assert data['binding']['roi']=='gapbs.trial_lambda.v1'
    assert data['coverage']['whole_timed_call'] is True
    assert len(data['trials'])==3
    assert all(len(t['sources'])==1 for t in data['trials'])
    for trial in data['trials']:
        observed_ids={r['id'] for r in trial['regions']}
        assert all(c['region'] in observed_ids for c in trial['unmodeled_calls'])
    assert data['counting']['summary']=='per_trial_then_median_time'
    assert any('.omp_outlined' in r['source_location']['llvm_function'] for r in data['regions'])
    if implementation=='gapbs-bfs-do':
        bindings={r['catalog_loop']:r['id'] for r in data['binding']['subject_source_identity']['region_bindings']}
        assert bindings['td-frontier']=='loop:bfs.cc:2257:ac1d48c6461c4614'
        assert bindings['td-edge']=='loop:bfs.cc:2357:401922b5b521a378'
        assert any(r['id']=='loop:bfs.cc:2357:401922b5b521a378' and '.omp_outlined' in r['source_location']['llvm_function'] for r in data['regions'])
    assert len(data['pattern_comparison'])==patterns
    assert all(row['matched'] or row['reason'] for row in data['pattern_comparison'])
    assert data['coverage']['missing_costs']
    checked=run_swdb('validate','--records',records)
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_atomic_rmw_retains_memory_operand_and_footprint(tmp_path,llvm22):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/indirect.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','atomic_update',
        '--run-arg','atomic','--fixture','--id','fixture.atomic','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    accesses=[a for r in data['regions'] for a in r['access_patterns'] if a['read_write']]
    assert len(accesses)==1
    assert accesses[0]['update_kind']=='add-update'
    assert accesses[0]['element_bytes']==4
    assert accesses[0]['element_count']['value']==3
    assert accesses[0]['bytes_accessed']['value']==12
    assert accesses[0]['observed_unique_bytes']['value']==4
    assert sum(r['operation_counts']['atomic']['value'] for r in data['regions'])==3


def test_worker_measurement_distinguishes_sparse_execution_from_team_size(tmp_path,llvm22):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/indirect.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','sparse_workers',
        '--run-arg','sparse','--fixture','--id','fixture.sparse','--llvm-bin',llvm22,'--threads','4',
        '--build-flag=-fopenmp','--run-library-path',llvm22.parent/'lib',
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    loop=next(r for r in data['regions'] if r['kind']=='loop' and any(a['element_count']['value'] for a in r['access_patterns']))
    assert loop['active_workers']['value']==1
    assert loop['worker_context']['team_sizes']==[4]
    assert sum(a['element_count']['value'] for a in loop['access_patterns'] if a['update_kind']=='write')==3


def test_fixture_v2_pipeline_preserves_independent_stream_counts(tmp_path,llvm22):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    fixture=REPO/'tests/fixtures/analytic'
    result=run_swdb('characterize','--records',records,'--source',fixture/'stream.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','stream',
        '--region-map',fixture/'regions.json','--run-arg','17','--fixture',
        '--counting-pipeline','source-normalized-v2','--id','fixture.stream.v2','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    assert data['counting']['pipeline_version']=='source-normalized-v2'
    assert data['counting']['passes']==['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']
    region=next(r for r in data['regions'] if r['id']=='fixture.stream')
    assert region['dynamic_counts']['loop_iterations']['value']==17
    assert region['operation_counts']['floating_point']['value']==34
    assert sorted(a['element_count']['value'] for a in region['access_patterns'])==[17,17]
    assert sorted(a['bytes_accessed']['value'] for a in region['access_patterns'])==[68,68]


def test_registered_adapter_refuses_v1_pipeline(tmp_path):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--adapter','registered-gapbs',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16',
        '--counting-pipeline','source-normalized-v1','--id','invalid.pipeline')
    assert result.returncode==1
    assert 'requires source-normalized-v2' in result.stderr


def test_intrinsic_semantics_cover_hints_and_checked_arithmetic_only(tmp_path,llvm22):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/intrinsics.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','intrinsic_math',
        '--counting-pipeline','source-normalized-v2','--fixture','--id','fixture.intrinsics','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    called=[c for c in data['unmodeled_calls'] if c['execution_count']['value']]
    hints=[c for c in called if c.get('event')=='compiler_annotation']
    assert any(c['name'].startswith('llvm.expect.') for c in hints)
    assert all(c['cost_accounting']=='no_runtime_operation' and c['operations_per_execution']==0 for c in hints)
    arithmetic=next(c for c in called if c['name']=='llvm.umul.with.overflow.i64')
    assert arithmetic['cost_accounting']=='source_normalized_operations'
    assert arithmetic['operation_class']=='integer' and arithmetic['operations_per_execution']==2
    assert arithmetic['execution_count']['value']==2
    assert sum(r['operation_counts']['integer']['value'] for r in data['regions'])==9
    assert all(c['name'] not in data['coverage']['missing_costs'] for c in hints+[arithmetic])
    assert next(c for c in called if c['name']=='puts')['execution_count']['value']==2
    assert 'puts' in data['coverage']['missing_costs']


def test_noalias_declaration_is_retained_as_a_cost_free_annotation(tmp_path,llvm22):
    records=tmp_path/'records'
    shutil.copytree(REPO/'records',records)
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/noalias.ll',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','metadata_hint',
        '--counting-pipeline','source-normalized-v2','--fixture','--id','fixture.noalias','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    called=next(c for c in data['unmodeled_calls'] if c['name']=='llvm.experimental.noalias.scope.decl')
    assert called['execution_count']['value']==1
    assert called['event']=='compiler_annotation' and called['cost_accounting']=='no_runtime_operation'
    assert called['operations_per_execution']==0
    assert sum(r['operation_counts']['integer']['value'] for r in data['regions'])==0
    assert data['coverage']['missing_costs']==[] and data['coverage']['missing_counts']==[]
