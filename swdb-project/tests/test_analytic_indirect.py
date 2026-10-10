"""Independent shape/count fixtures through the public CLI. Updated: 2026-10-09 ET
(code review: stream negatives, per-step pattern comparison, closure-copied stores)."""
import json
from pathlib import Path

import pytest
from conftest import REPO,run_swdb


def fixture_store(records):
    """Placeholder subject/input closure; fixtures never need the whole ~1 GB catalog."""
    return records.copy_closure('gapbs-bfs-do','kron-g16-k16').path


def registered_store(records,implementation):
    """Registered subject plus the profile packages whose region IDs it reuses (D33)."""
    import re
    packages=[re.search(r'^id: (.+)$',p.read_text(),re.M).group(1) for p in (REPO/'records/profile_packages').glob('*.yaml')
        if re.search(r'^implementation: '+re.escape(implementation)+r'$',p.read_text(),re.M)]
    return records.copy_closure(implementation,'kron-g16-k16',*packages).path


@pytest.mark.parametrize("function,shape,elements,unique_bytes",[
    ("gather","single_valued_indirect",4,12),
    ("ranged","ranged_indirect",5,20),
    ("chase","pointer_chase",3,24),
    ("merge","data_dependent_merge",4,16),
])
def test_independent_indirect_shapes_and_useful_counts(records,tmp_path,llvm22,function,shape,elements,unique_bytes):
    store=fixture_store(records)
    result=run_swdb('characterize','--records',store,'--source',REPO/'tests/fixtures/analytic/indirect.cpp',
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
    # Negative check (code review F1): the index, offset and selector reads are plain streams.
    executed=[a for r in data['regions'] if r['kind']=='loop' for a in r['access_patterns'] if a['element_count']['value']]
    assert {a['address_shape']['value'] for a in executed}<={shape,'stream'}
    assert data['unmapped_loops']
    checked=run_swdb('validate','--records',store)
    assert checked.returncode==0,checked.stdout+checked.stderr


@pytest.mark.parametrize("function,argument,unit_elements,reused_elements",[
    ("omp_stream","omp",16,None),       # x[i] reads and y[i] writes, 8 each across the team
    ("member_stream","member",8,None),  # v->data[i]; v->data and v->n are reloaded each iteration
    ("field_bounds","bounds",6,None),   # a[1..6]; the bounds are scalar fields, not an index array
    ("accumulate","accumulate",8,16),   # a[i], plus 8 reads and 8 writes of the same *out
])
def test_streams_through_reloaded_bases_are_never_indirect(records,tmp_path,llvm22,function,argument,unit_elements,reused_elements):
    store=fixture_store(records)
    extra=('--build-flag=-fopenmp','--threads','2','--run-library-path',llvm22.parent/'lib') if function=='omp_stream' else ()
    result=run_swdb('characterize','--records',store,'--source',REPO/'tests/fixtures/analytic/streams.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function',function,'--run-arg',argument,
        '--fixture','--id','fixture.'+function,'--llvm-bin',llvm22,*extra,'--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    executed=[a for r in data['regions'] if r['kind']=='loop' for a in r['access_patterns'] if a['element_count']['value']]
    assert executed and {a['address_shape']['value'] for a in executed}=={'stream'}
    assert sum(a['element_count']['value'] for a in executed if a['stride_bytes']['value']==4)==unit_elements
    if reused_elements:
        reused=[a for a in executed if a['stride_bytes']['value']==0 and a['element_bytes']==8]
        assert sum(a['element_count']['value'] for a in reused)==reused_elements
        assert all(a['observed_unique_bytes']['value']==8 for a in reused)


def test_registered_gapbs_rejects_arbitrary_translation_unit(records,tmp_path):
    records=fixture_store(records)
    result=run_swdb('characterize','--records',records,'--adapter','registered-gapbs',
        '--source',REPO/'tests/fixtures/analytic/indirect.cpp','--implementation','gapbs-bfs-do',
        '--input','kron-g16-k16','--id','invalid.registered')
    assert result.returncode==1
    assert 'registered translation unit' in result.stderr


@pytest.mark.parametrize("implementation,patterns",[("gapbs-bfs-do",13),("gapbs-bc-brandes",20)])
def test_registered_gapbs_counts_trial_lambda_and_workers(records,tmp_path,llvm22,implementation,patterns):
    import yaml
    records=registered_store(records,implementation)
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
    # Per-step comparison (code review F3): every step is judged, and a mismatch names the failed steps.
    for row in data['pattern_comparison']:
        assert len(row['steps'])==len(row['expected_shapes'])
        assert row['matched']==(row['region'] is not None and all(step['matched'] for step in row['steps']))
        if row['region'] and not row['matched']:
            assert all(f"step {s['position']} " in row['reason'] for s in row['steps'] if not s['matched'])
    if implementation=='gapbs-bfs-do':
        # pvector writes/reads through a reloaded member base are plain streams (code review F1).
        matched={row['pattern'] for row in data['pattern_comparison'] if row['matched']}
        assert {'init-parent-write','init-degree-read'}<=matched
    # A gated run's top-level counts repeat trial 0, so they are labeled per_trial (code review F4).
    assert data['counting']['top_level_counts']=={'scope':'per_trial','trial_position':0,
        'note':'Top-level regions and calls repeat the first registered trial window; trials holds every window.'}
    assert {c['scope'] for r in data['regions'] for c in r['operation_counts'].values()}=={'per_trial'}
    assert data['binding']['subject_source_identity']['adapter']=='registered-gapbs.v2'
    assert data['coverage']['missing_costs']
    checked=run_swdb('validate','--records',records)
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_atomic_rmw_retains_memory_operand_and_footprint(records,tmp_path,llvm22):
    records=fixture_store(records)
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


def test_worker_measurement_distinguishes_sparse_execution_from_team_size(records,tmp_path,llvm22):
    records=fixture_store(records)
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


def test_fixture_v2_pipeline_preserves_independent_stream_counts(records,tmp_path,llvm22):
    records=fixture_store(records)
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


def test_registered_adapter_refuses_v1_pipeline(records,tmp_path):
    records=fixture_store(records)
    result=run_swdb('characterize','--records',records,'--adapter','registered-gapbs',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16',
        '--counting-pipeline','source-normalized-v1','--id','invalid.pipeline')
    assert result.returncode==1
    assert 'requires source-normalized-v2' in result.stderr


def test_intrinsic_semantics_cover_hints_and_checked_arithmetic_only(records,tmp_path,llvm22):
    records=fixture_store(records)
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


def test_noalias_declaration_is_retained_as_a_cost_free_annotation(records,tmp_path,llvm22):
    records=fixture_store(records)
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


def test_pure_arithmetic_intrinsics_are_counted_operations_not_calls(records,tmp_path,llvm22):
    """Code review 14-F3 (2026-10-09 ET): fabs/maxnum/abs/ctpop are operations, not opaque calls."""
    store=fixture_store(records)
    result=run_swdb('characterize','--records',store,'--source',REPO/'tests/fixtures/analytic/pure_intrinsics.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','pure_math',
        '--counting-pipeline','source-normalized-v2','--fixture','--id','fixture.pure','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    totals={k:sum(r['operation_counts'][k]['value'] for r in data['regions']) for k in ('integer','floating_point','branch')}
    # One call: fabs + maxnum + the final fadd; icmp (std::max) + sub + abs + ctpop + two adds;
    # std::max's two-way branch and the taken arm's jump to the merge.
    assert totals=={'integer':6,'floating_point':3,'branch':2}
    assert data['unmodeled_calls']==[] and data['coverage']['missing_costs']==[]
