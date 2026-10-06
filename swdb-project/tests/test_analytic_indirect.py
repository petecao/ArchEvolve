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
