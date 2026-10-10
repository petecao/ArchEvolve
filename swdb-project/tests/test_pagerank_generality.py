"""Public actual Jacobi source counting. Created: 2026-10-06 ET.
Updated: 2026-10-09 ET (code review 14-F2: catalog loops bind to regions; closure-copied store)."""
import json
from conftest import REPO,run_swdb
from swdb import artifacts

IMPLEMENTATION='gapbs-pr-jacobi-analytic-v1'


def test_registered_jacobi_counts_original_source_free_roi(records,tmp_path,llvm22):
    records.copy_closure(IMPLEMENTATION,'gapbs-pr-jacobi','kron-g16-k16')
    (records.path/'implementations'/f'{IMPLEMENTATION}.yaml').unlink(missing_ok=True)
    added=run_swdb('add',REPO/'records/implementations'/f'{IMPLEMENTATION}.yaml',
        '--records',records.path,'--db',tmp_path/'index.sqlite')
    assert added.returncode==0,added.stdout+added.stderr
    original=(REPO/'apps/gapbs/src/pr_spmv.cc').read_bytes()
    legacy=(REPO/'records/implementations/gapbs-pr-jacobi.yaml').read_bytes()
    snapshot=run_swdb('source-snapshot',IMPLEMENTATION,'--records',records.path,
        '--runs-dir',tmp_path/'snapshots','--id','fixture.jacobi.source','--format','json')
    assert snapshot.returncode==0,snapshot.stdout+snapshot.stderr
    source=json.loads(snapshot.stdout)
    assert source['context']['verification']['status']=='unchecked'
    assert any(p['path']=='src/pr_spmv.cc' for p in source['protections'])
    data=records.read('inputs/kron-g16-k16.yaml');data['id']='fixture.jacobi.kron-g8-k4'
    data['generator'].update(application='gapbs',arguments='-g 8 -k 4')
    data['properties']={k:{'value':v,'basis':'code_reading','evidence_refs':['fixture-generator']}
        for k,v in [('scale',8),('requested_degree',4),('directed',False),('weighted',False)]}
    data['provenance']=[{'id':'fixture-generator','kind':'source_code','description':'Registered generator arguments; no realized size or timing.'}]
    data['notes']=[];records.write('inputs/'+data['id']+'.yaml',data)
    counted=run_swdb('characterize','--records',records.path,'--implementation',IMPLEMENTATION,
        '--source-snapshot','fixture.jacobi.source','--input',data['id'],
        '--adapter','registered-functional','--threads','1','--trials','1','--object-scopes',
        '--counting-pipeline','source-normalized-v2','--llvm-bin',llvm22,
        '--run-library-path',llvm22.parent/'lib','--id','fixture.jacobi.count',
        '--output',tmp_path/'counted','--timeout-s','60','--format','json',timeout=180)
    assert counted.returncode==0,counted.stdout+counted.stderr
    result=json.loads(counted.stdout)
    assert result['binding']['state']=='verified'
    assert result['coverage']['whole_timed_call'] is True
    assert result['binding']['subject_source_identity']['source_selection']=='none'
    assert result['binding']['roi']=='gapbs.functional_trial_lambda.v1'
    assert result['source']['run_arguments']==['-g','8','-k','4','-n','1']
    assert len(result['trials'])==1 and result['trials'][0]['sources']==[]
    assert result['binding']['execution_receipt']['graph']['num_nodes']==256
    assert result['regions'] and result['binding']['execution_receipt']['counted_payload_sha256']
    assert (REPO/'apps/gapbs/src/pr_spmv.cc').read_bytes()==original
    assert (REPO/'records/implementations/gapbs-pr-jacobi.yaml').read_bytes()==legacy
    assert records.read('implementations/'+IMPLEMENTATION+'.yaml')['verification']['status']=='unchecked'
    # Code review 14-F2: the registered-functional route binds the declared catalog loops to
    # region IDs and compares every handwritten access pattern step by step.
    implementation=records.read('implementations/'+IMPLEMENTATION+'.yaml')
    bindings={r['catalog_loop']:r['id'] for r in result['binding']['subject_source_identity']['region_bindings']}
    assert set(bindings)=={loop['id'] for loop in implementation['loops']}
    mapped={r['id'] for r in result['regions'] if r['mapped']}
    assert set(bindings.values())<=mapped
    assert not set(bindings.values())&set(result['unmapped_loops'])
    rows=result['pattern_comparison']
    assert [row['pattern'] for row in rows]==[p['id'] for p in implementation['access_patterns']]
    assert all(row['region'] and len(row['steps'])==len(row['expected_shapes']) for row in rows)
