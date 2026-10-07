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
