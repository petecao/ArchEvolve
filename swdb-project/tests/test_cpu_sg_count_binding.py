"""Exact SG counts use the protected native v3 call. 2026-10-09 ET.

These small host executions test graph/source/correctness bindings. Fixture
packaging and host timing never establish LANL numerical agreement.
"""
import copy
import json
from pathlib import Path

import pytest

from conftest import run_swdb
from swdb import artifacts
from swdb import analytic_cpu_binding as binding
from swdb import bfs_native_scalable as scalable
from swdb.cli import Failure
from swdb.store import Store
from testkit.bfs_native import build_evaluation_setup
from testkit.bfs_protocol import _command, _payload, _workload_request
from testkit.proposals import build_proposal_setup
from testkit.native_catalog import seed_native_contract_records


@pytest.fixture
def sg_setup(records,tmp_path):
    seed_native_contract_records(records)
    return build_evaluation_setup(build_proposal_setup(records,tmp_path,copy_all=False),tmp_path)


@pytest.mark.parametrize('width',[4,8])
def test_exact_sg_counts_reject_rebound_graphs_and_preserve_unknown_numeric_state(sg_setup,tmp_path,llvm22,width):
    records,runs,request,base=sg_setup
    graph={'num_vertices':6,'directed':True,'edges':[[0,1],[0,2],[1,3],[2,3],[4,5]]}
    registration=_workload_request(records,tmp_path,graph)
    registration['representations']=[rep for rep in registration['representations'] if rep['format']!='json_graph'
        and (width==8 or rep['format']=='gapbs_sg32le')]
    workload=_command(records,'register-workload',_payload(tmp_path,'register',registration))
    prospective=request(id='fixture.sg.prospective',workload={'id':workload['id']},
        evaluator=scalable.EVALUATOR_V3,sources=[0,4],repetitions=2,
        budget={'build_seconds':30,'run_seconds':10,'total_seconds':180},
        build={'compiler':str(llvm22/'clang++'),'flags':['-std=c++11','-O2']})
    result=run_swdb('characterize','--records',records.path,'--candidate',base['candidate'],
        '--adapter','registered-cpu','--evaluation-request',prospective,'--input',workload['id'],
        '--source-position','1','--repetition','1','--id','fixture.sg.counts','--llvm-bin',llvm22,
        '--output',runs/'sg-counts','--trials','1','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    counts=json.loads(result.stdout);identity=counts['binding']['subject_source_identity'];context=identity['evaluation_scope']
    assert identity['adapter']==binding.SG_ADAPTER
    assert identity['slot']=={'source_position':1,'repetition':1,'source':4}
    assert counts['trials'][0]['sources']==[4] and len(counts['trials'])==1
    assert context['evaluator']==scalable.EVALUATOR_V3
    assert context['process_policy']==binding.SG_PROCESS_POLICY
    assert context['graph_input']['offset_bytes']==width
    assert context['canonical_graph_sha256']==workload['definition']['canonical_sha256']
    assert context['driver_template_sha256']==artifacts.file_hash(scalable.DRIVER_V3)
    assert identity['counted_correctness']['passed'] is True
    assert identity['counted_correctness']['timer_outputs_used'] is False
    assert identity['counted_correctness']['parents_bytes']==24
    assert 'duration_s' not in counts['binding']['execution_receipt']
    assert counts['binding']['execution_receipt']['graph']['representation']==context['graph_input']
    assert counts['evidence_kind']=='contract_fixture'
    assert binding.verify(counts,Store(records.path),require_available=True)==[]
    assert records.validate().returncode==0

    # Recompute the self-digests: immutable registered content still rejects a
    # forged graph or representation, including a different valid-width input.
    for mutate in (
        lambda scope:scope.update(canonical_graph_sha256='0'*64),
        lambda scope:scope['canonical_graph'].update(num_vertices=7),
        lambda scope:scope['graph_input'].update(sha256='0'*64),
        lambda scope:scope['graph_input'].update(offset_bytes=12-width),
        lambda scope:scope.update(evaluator=scalable.EVALUATOR_V2),
    ):
        altered=copy.deepcopy(counts);source=altered['binding']['subject_source_identity'];mutate(source['evaluation_scope'])
        source['evaluation_scope_sha256']=artifacts.digest(source['evaluation_scope'])
        altered['binding']['execution_receipt']['graph']['representation']=copy.deepcopy(source['evaluation_scope']['graph_input'])
        assert binding.verify(altered,Store(records.path)), 'Self-consistent rebinding accepted an unregistered graph.'

    altered=copy.deepcopy(counts);source=altered['binding']['subject_source_identity']
    source['evaluation_scope']['verifier']['source_sha256']='0'*64
    source['counted_correctness']['verifier_source_sha256']='0'*64
    source['evaluation_scope_sha256']=artifacts.digest(source['evaluation_scope'])
    assert 'protected SG independent correctness binding differs' in binding.verify(altered,Store(records.path))
    altered=copy.deepcopy(counts);source=altered['binding']['subject_source_identity']
    source['evaluation_scope']['verifier']['flags']=['-std=c++11','-O0']
    source['evaluation_scope_sha256']=artifacts.digest(source['evaluation_scope'])
    assert 'protected SG independent correctness binding differs' in binding.verify(altered,Store(records.path))
    if width==8:
        altered=copy.deepcopy(counts);source=altered['binding']['subject_source_identity']
        source['application']='dx100-gapbs'
        alternate=scalable.registered_graph_input(workload,source['application'])
        assert alternate['offset_bytes']==4
        source['evaluation_scope']['graph_input']=alternate
        source['evaluation_scope_sha256']=artifacts.digest(source['evaluation_scope'])
        altered['binding']['execution_receipt']['graph']['representation']=alternate
        altered['source']['run_arguments'][:2]=[alternate['path'],str(alternate['offset_bytes'])]
        altered['binding']['run_arguments_sha256']=artifacts.digest(altered['source']['run_arguments'])
        altered['binding']['execution_receipt']['run_arguments_sha256']=altered['binding']['run_arguments_sha256']
        issues=binding.verify(altered,Store(records.path))
        assert 'protected CPU registered application differs' in issues
        assert 'protected SG representation binding differs' in issues

    # The same public semantic seam used by validation must fail closed on
    # malformed saved nested metadata rather than raising an uncaught exception.
    from swdb.analytic_binding import verify_binding
    for mutate in (
        lambda source:source['evaluation_scope'].update(graph_input=None),
        lambda source:source['evaluation_scope'].update(verifier=[]),
        lambda source:source.update(slot=None),
        lambda source:source.update(counted_correctness=[]),
    ):
        altered=copy.deepcopy(counts);mutate(altered['binding']['subject_source_identity'])
        assert verify_binding(altered,Store(records.path))

    path=Path(context['graph_input']['path']);saved_path=path.with_suffix('.offline')
    path.rename(saved_path)
    try:
        assert binding.verify(counts,Store(records.path),require_available=False)==[]
        assert 'protected SG input changed during counting' in binding.verify(counts,Store(records.path),require_available=True)
    finally:saved_path.rename(path)

    # Exercise the real independent checker on copied outputs. The count-only
    # proof ignores instrumented duration, but rejects wrong parents and bools.
    proof=tmp_path/'independent-proof';proof.mkdir()
    original_arguments=counts['source']['run_arguments']
    trial=proof/'trial.json';parents=proof/'parents.i32'
    observed=json.loads(Path(original_arguments[3]).read_text())
    observed['duration_s']='instrumented duration is not an estimator premise'
    trial.write_text(json.dumps(observed));parents.write_bytes(Path(original_arguments[4]).read_bytes())
    adapter={'identity':copy.deepcopy(identity),'roi':counts['binding']['roi'],'timeout_s':30,
        'run':[original_arguments[0],original_arguments[1],original_arguments[2],str(trial),str(parents)]}
    assert binding.finish_sg(adapter,counts)['passed'] is True
    parents.write_bytes(b'\0'*24)
    with pytest.raises(Failure,match='independent correctness failed'):
        binding.finish_sg(adapter,counts)
    observed['source']=True;trial.write_text(json.dumps(observed))
    with pytest.raises(Failure,match='source/ROI/thread/parent output differs'):
        binding.finish_sg(adapter,counts)

    # The uninstrumented evaluator retains its existing native outcome and an
    # explicitly unavailable forecast. Counts alone cannot produce seconds.
    evaluated=records.swdb('evaluate',request(id='fixture.sg.evaluation',
        workload={'id':workload['id']},evaluator=scalable.EVALUATOR_V3,
        build={'compiler':str(llvm22/'clang++'),'flags':['-std=c++11','-O2']},
        budget={'build_seconds':30,'run_seconds':10,'total_seconds':180}), '--runs-dir',runs,'--format','json')
    assert evaluated.returncode==0,evaluated.stdout+evaluated.stderr
    native=json.loads(evaluated.stdout)
    assert native['outcome']['state']=='complete' and native['correctness']['state']=='passed'
    assert native['context']['analytic_evaluator_scope']['graph_input']==context['graph_input']
    assert native['paired_estimate']['state']=='unavailable'
    assert native['paired_estimate']['seconds'] is None and native['gain_claim'] is False
    assert records.validate().returncode==0

    # A changed SG cannot be characterized again under the saved registration.
    original=path.read_bytes()
    path.write_bytes(original[:-1]+bytes([original[-1]^1]))
    refused=run_swdb('characterize','--records',records.path,'--candidate',base['candidate'],
        '--adapter','registered-cpu','--evaluation-request',prospective,'--input',workload['id'],
        '--id','fixture.sg.changed','--llvm-bin',llvm22,'--output',runs/'changed',
        '--trials','1','--fixture','--format','json')
    assert refused.returncode==1 and 'changed since registration' in refused.stdout+refused.stderr
    assert not (runs/'changed').exists()
    path.write_bytes(original)
