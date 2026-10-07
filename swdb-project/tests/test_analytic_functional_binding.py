"""Public registered-source counting preserves fixture packaging provenance. 2026-10-06 ET."""
import json
import shutil
from conftest import REPO,run_swdb
from swdb import artifacts,certification
from swdb.store import Store

SOURCE='bfs-functional-read-offload-20261006-a1.source'
CANDIDATE='bfs-functional-read-offload-20261006-a1.proposal.candidate-1'


def registered_tree(records,tmp_path):
    records.copy_repo()
    store=Store(records.path)
    root,_=certification.materialize_snapshot(store,SOURCE,tmp_path/'materialized')
    primary=root/'benchmarks/gapbs/src/bfs.cc'
    primary.write_text(certification.peter_source(primary.read_text()))
    shutil.copy2(REPO/'library/dx100/dxc_lowering.hpp',primary.parent/'swdb_dxc_lowering.hpp')
    assert artifacts.identify(root)['sha256']==store.get(CANDIDATE,'candidate')['artifact']['sha256']
    data=records.read('inputs/kron-g16-k16.yaml');data['id']='fixture.functional.kron.g8-k4'
    data['generator'].update(application='dx100-gapbs',arguments='-g 8 -k 4')
    data['name']='Registered built-in scale8 degree4 graph for a public count-binding test.'
    data['provenance']=[{'id':'fixture-generator','kind':'source_code','description':'Pinned registered source generator arguments; no performance or measured size input.'}]
    data['properties']={name:{'value':value,'basis':'code_reading','evidence_refs':['fixture-generator']}
        for name,value in [('scale',8),('requested_degree',4),('directed',False),('weighted',False)]}
    data['notes']=['Test fixture input identity; observed graph sizes stay in the new execution receipt.']
    records.write('inputs/'+data['id']+'.yaml',data)
    return primary,data['id']


def test_registered_candidate_count_binds_actual_tree_trials_and_preserves_packaging_fixture(records,tmp_path,llvm22):
    source,input_id=registered_tree(records,tmp_path)
    result=run_swdb('characterize','--records',records.path,'--source',source,'--candidate',CANDIDATE,
        '--input',input_id,'--adapter','registered-functional','--threads','1','--trials','1',
        '--id','fixture.functional.count','--llvm-bin',llvm22,'--run-library-path',llvm22.parent/'lib',
        '--output',tmp_path/'counted','--timeout-s','45','--format','json',timeout=120)
    assert result.returncode==0,result.stdout+result.stderr
    data=json.loads(result.stdout)
    assert data['binding']['state']=='verified'
    assert data['binding']['subject_source_identity']['adapter']=='registered-functional.v1'
    assert data['binding']['subject_source_identity']['source_root_sha256']==artifacts.identify(source.parents[3])['sha256']
    assert len(data['trials'])==1 and len(data['trials'][0]['sources'])==1
    assert data['source']['run_arguments']==['-g','8','-k','4','-n','1']
    assert records.read('source_snapshots/'+SOURCE+'.yaml')['context']['verification']['status']=='unchecked'
    assert records.read('candidates/'+CANDIDATE+'.yaml')['state']=='unverified'
    profile=Store(records.path).get('bfs-functional-read-offload-20261006-a1.fixture-profile','profile_package')
    assert profile['evidence']['classification']=='contract_fixture'
    assert data['binding']['execution_receipt']['counted_payload_sha256']


def test_registered_candidate_refuses_modified_artifact_before_build(records,tmp_path,llvm22):
    source,input_id=registered_tree(records,tmp_path);source.write_text(source.read_text()+'\n')
    result=run_swdb('characterize','--records',records.path,'--source',source,'--candidate',CANDIDATE,
        '--input',input_id,'--adapter','registered-functional','--llvm-bin',llvm22,
        '--id','fixture.refused','--output',tmp_path/'counted')
    assert result.returncode==1 and 'differs from immutable registered identity' in result.stdout+result.stderr
    assert not (tmp_path/'counted').exists()


def test_registered_candidate_refuses_generator_parameter_mismatch(records,tmp_path,llvm22):
    source,input_id=registered_tree(records,tmp_path)
    data=records.read('inputs/'+input_id+'.yaml');data['properties']['scale']['value']=9
    records.write('inputs/'+input_id+'.yaml',data)
    result=run_swdb('characterize','--records',records.path,'--source',source,'--candidate',CANDIDATE,
        '--input',input_id,'--adapter','registered-functional','--llvm-bin',llvm22,
        '--id','fixture.refused','--output',tmp_path/'counted')
    assert result.returncode==1 and 'scale differs from generator arguments' in result.stdout+result.stderr
    assert not (tmp_path/'counted').exists()


def test_registered_canonical_candidate_observes_guarded_read_commands_without_emulator_double_count(records,tmp_path,llvm22):
    source,input_id=registered_tree(records,tmp_path)
    result=run_swdb('characterize','--records',records.path,'--source',source,'--candidate',CANDIDATE,
        '--input',input_id,'--adapter','registered-functional','--threads','1','--trials','1',
        '--id','fixture.functional.guarded','--llvm-bin',llvm22,'--run-library-path',llvm22.parent/'lib',
        '--target-description','dx100-e4fc4af-functional-analytic-v1.t1','--object-scopes',
        '--output',tmp_path/'counted','--timeout-s','45','--format','json',timeout=150)
    assert result.returncode==0,result.stdout+result.stderr
    data=json.loads(result.stdout)
    assert data['observation_contract']['semantic_commands']['complete'] is True
    assert data['observation_contract']['object_scope_contract']['format']=='swdb.object-scopes.v1'
    assert all('primitive_semantics' in a for r in data['trials'][0]['regions'] for a in r['access_patterns'])
    calls=[c for r in data['trials'][0]['regions'] for c in r['accelerator_calls']]
    reads=[c for c in calls if c['event'] in ('dx100.functional.gather','dx100.functional.stream_load') and c['execution_count']['value']]
    assert {c['event'] for c in reads}=={'dx100.functional.gather','dx100.functional.stream_load'}
    assert all(c['active_elements']['value']==c['useful_accesses']['value'] and c['active_elements']['value']>0 for c in reads)
    logical=[v for r in data['trials'][0]['regions'] for v in r.get('address_stream_counts',{}).values()]
    known=[v for v in logical if v['line_requests']['value'] is not None and v['line_requests']['value']>0]
    assert known and all(v['row_groups']['value'] is not None and v['row_groups']['value']<=v['line_requests']['value'] for v in known)
    assert sum(c['functional_bookkeeping']['accesses']['value'] for c in calls)>0
    assert data['observation_contract']['host_counting_policy']=='exclusive_host_outside_guarded_functional_commands'
    assert data['binding']['state']=='verified'
    assert data['observation_contract']['counted_target_description_snapshot']['id']=='dx100-e4fc4af-functional-analytic-v1.t1'
    assert data['observation_contract']['target_observation_policy_format']=='swdb.observation-policy.v1'
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr
    target_path='hardware_targets/dx100-e4fc4af-functional-analytic-v1.yaml'
    target=records.read(target_path);original=json.loads(json.dumps(target))
    target['configuration']['tile_elements']+=1;records.write(target_path,target)
    refused=records.validate()
    assert refused.returncode==1 and 'functional normative record changed: dx100-e4fc4af-functional-analytic-v1' in refused.stdout+refused.stderr
    records.write(target_path,original)
    # Re-signing a top-level JSON label cannot change the sealed execution policy.
    data['observation_contract']['state_budget']+=1
    data.pop('identity_sha256');data['identity_sha256']=artifacts.digest(data)
    records.write('workload_characterizations/fixture.functional.guarded.yaml',data)
    refused=records.validate()
    assert refused.returncode==1 and 'counted_payload_sha256' in refused.stdout+refused.stderr
