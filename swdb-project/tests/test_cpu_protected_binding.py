"""Prospective protected-driver CPU count/estimate pairing. 2026-10-09 ET.

Tiny fixture rates never establish native application accuracy.
"""
import json
import shutil

import pytest

from conftest import REPO, run_swdb, load_fixture
from swdb import artifacts


@pytest.fixture
def protected_setup(records, tmp_path):
    # Small exact proposal closure avoids validating unrelated large experiment records.
    for name in ('applications/gapbs.yaml','kernels/gapbs-bfs.yaml','implementations/gapbs-bfs-do.yaml','machines/mbit10.yaml'):
        path=records.path/name;path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/'records'/name,path)
    impl=records.read('implementations/gapbs-bfs-do.yaml')
    impl['verification']={'status':'unchecked','evidence':[],'scope':'Isolated contract fixture.'}
    records.write('implementations/gapbs-bfs-do.yaml',impl)
    from testkit.proposals import build_proposal_setup
    from testkit.bfs_native import build_evaluation_setup
    return build_evaluation_setup(build_proposal_setup(records,tmp_path,copy_all=False),tmp_path)


def test_protected_driver_counts_bind_exact_fresh_source_slot_before_evaluation(protected_setup, tmp_path, llvm22, monkeypatch):
    records, runs, request, base = protected_setup
    records.write('inputs/tiny-sym.yaml', load_fixture('profile/tiny-input.yaml'))
    prospective = request(id='fixture.prospective.cpu', analytic_input='tiny-sym', budget={'build_seconds':10,'run_seconds':5,'total_seconds':180}, build={'compiler': str(llvm22/'clang++'), 'flags': ['-std=c++11','-O2']})
    result = run_swdb('characterize','--records',records.path,'--candidate',base['candidate'],
        '--adapter','registered-cpu','--evaluation-request',prospective,'--input','tiny-sym',
        '--id','fixture.protected.counts','--llvm-bin',llvm22,'--output',runs/'protected-counts',
        '--trials','1','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    char=json.loads(result.stdout)
    identity=char['binding']['subject_source_identity']
    assert identity['adapter']=='registered-cpu.v1'
    assert identity['process_policy']=='one fresh process per source and repetition; graph construction before ROI'
    assert identity['slot']=={'source_position':0,'repetition':0,'source':0}
    assert identity['driver_template_sha256']==artifacts.file_hash(REPO/'tools/bfs_native/driver.cc.in')
    assert identity['source_selection']=='fixed_protected_source_slot'
    assert identity['counted_correctness']['passed'] is True
    assert char['binding']['roi']=='bfs.complete_call.v1'
    assert char['trials'][0]['sources']==[0] and len(char['trials'])==1
    assert identity['timer_outputs_used_for_counts'] is False
    assert 'duration_s' not in char['binding']['execution_receipt']
    assert records.validate().returncode==0
    # Persist the estimate before opening the native process. Hand rates remain fixture evidence.
    import yaml
    from testkit.analytic import target_description, freeze_protocol
    target_path=target_description(tmp_path)
    target=yaml.safe_load(target_path.read_text());target['target']='native-testhost'
    target['mechanisms']=target['mechanisms'][:1]
    # Independent hypothetical request/call costs. No observed timing enters these facts.
    cells=[];rates={}
    for kind,width in (('read',1),('read',4),('read',8),('write',4),('write',8)):
        name=kind+str(width)+'_s'
        rates[name]={'value':1e-7,'basis':'reported','unit':'seconds/request','source':'Hypothetical public contract fixture; no hardware latency claim.'}
        cells.append({'update_kind':kind,'element_bytes':width,'parameter':name,'construction':{
            'primitive':'ordinary_'+kind,'regime':'fixed_small_byte_read_constructed_requests' if width==1 else 'resident_serial_constructed_requests',
            'footprint_bytes':256 if width==1 else 8388608,'transfer_basis':'inferred','physical_cache_level':'unverified',
            'source_services':[{'calibration':'hand.protected.memory','service':name,'parameter':name}]}})
    target['mechanisms'].append({'model':'memory_service_scenario','selector':{'domain':'host','worker_scope':'serial_T1',
        'scenario':'resident_serial_constructed_requests','transfer_basis':'inferred',
        'object_scope':'logical_requests_and_bounded_referent_views','characterization_sha256':artifacts.digest(char),'requests':cells},'parameters':rates})
    from swdb.analytic import _uncovered_call
    names=sorted({row['name'] for row in char['unmodeled_calls'] if row['execution_count']['value'] and _uncovered_call(row)})
    target['mechanisms'].append({'model':'native_service_costs','accounting':'additive_overhead',
        'selector':{'domain':'host','worker_scope':'serial_T1','characterization_sha256':artifacts.digest(char),
            'calls':[{'name':name,'parameter':'call_'+str(i),'unit':'seconds/call'} for i,name in enumerate(names)]},
        'parameters':{'call_'+str(i):{'value':1e-6,'basis':'reported','unit':'seconds/call',
            'source':'Hypothetical exact-count public contract fixture, no measured allocator/clock/bulk claim.'} for i in range(len(names))}})
    target_path.write_text(yaml.safe_dump(target,sort_keys=False))
    protocol=freeze_protocol(records.path,tmp_path,target_path,roi=char['binding']['roi'],
        input_id='tiny-sym',arguments=char['source']['run_arguments'])
    estimated=records.swdb('estimate','--characterization',char['id'],'--target-description',target_path,
        '--protocol',protocol,'--id','fixture.protected.estimate','--format','json')
    assert estimated.returncode==0,estimated.stderr
    prediction=json.loads(estimated.stdout)
    assert prediction['seconds'] is not None and prediction['seconds']>0,[(r['id'],r['bounds']) for r in prediction['regions'] if r['seconds'] is None]
    evaluation_request=json.loads(json.dumps(__import__('yaml').safe_load(prospective.read_text())))
    evaluation_request.update(id='fixture.protected.evaluation',analytic_estimate='fixture.protected.estimate')
    # A coherent saved-number forgery must refuse before even runtime preflight.
    import copy
    from swdb import cpu_pairing
    from swdb.store import Store
    forged=copy.deepcopy(prediction);forged['seconds']*=2
    for row in forged['parameter_report']['sensitivities']:
        row['whole_call_seconds']['base']=forged['seconds']
    from swdb.analytic import _payload_problems
    assert not list(_payload_problems(forged))
    records.write('estimates/fixture.protected.estimate.yaml',forged)
    def no_runtime_query(*args,**kwargs):
        pytest.fail('Numerically forged estimate reached runtime preflight.')
    with monkeypatch.context() as patched:
        patched.setattr(cpu_pairing,'runtime_admission',no_runtime_query)
        refusal=cpu_pairing.prepare(Store(records.path),{'evidence_kind':char['evidence_kind']},
            evaluation_request,identity['evaluation_scope'],tmp_path/'must-not-execute')
    assert refusal['state']=='excluded' and refusal['seconds'] is None
    assert 'count-to-model composition differs: seconds' in refusal['reason']
    records.write('estimates/fixture.protected.estimate.yaml',prediction)
    file=tmp_path/'evaluation.json';file.write_text(json.dumps(evaluation_request))
    evaluated=records.swdb('evaluate',file,'--runs-dir',runs,'--format','json')
    assert evaluated.returncode==0,evaluated.stderr
    native=json.loads(evaluated.stdout)
    assert native['outcome']['state']=='complete' and native['correctness']['state']=='passed'
    pair=native['paired_estimate']
    assert pair['state']=='paired',pair
    assert pair['prepared_before_native_timing'] is True
    assert pair['slots'][0]['characterization']['sha256']==artifacts.digest(char)
    assert pair['kernel_seconds']==prediction['seconds']
    assert pair['slots'][0]['kernel_seconds']==prediction['seconds']
    assert pair['seconds'] is None and pair['error_band'] is None
    assert pair['missing']==['uncalibrated_steady_clock_measurement_boundary']
    assert pair['native_timing_decides'] is True and pair['agreement_claim'] is False
    stages=[row['stage'] for row in native['stages']]
    assert stages.index('analytic_pairing')<stages.index('execution')
    # Archived annotations must retain the immutable prediction and actual native scope.
    import copy
    for mutate in (
        lambda row: row['paired_estimate'].update(evaluation_scope_sha256='0'*64),
        lambda row: row['paired_estimate']['slots'][0]['estimate'].update(sha256='0'*64),
        lambda row: row['paired_estimate']['slots'][0].update(kernel_seconds=prediction['seconds']*2),
        lambda row: row['build'].update(wrapper_sha256='0'*64),
    ):
        altered=copy.deepcopy(native);mutate(altered)
        records.write('evaluations/fixture.protected.evaluation.yaml',altered)
        rejected=records.validate()
        assert rejected.returncode!=0,'A tampered archived CPU pairing was accepted.'
        assert 'paired' in rejected.stdout+rejected.stderr
        records.write('evaluations/fixture.protected.evaluation.yaml',native)
    assert records.validate().returncode==0
    # A persisted advancing/different source prediction cannot bind by its name.
    mismatch=copy.deepcopy(evaluation_request)
    mismatch.update(id='fixture.protected.source-mismatch',sources=[1])
    mismatch['budget']['total_seconds']=300
    mismatch_file=tmp_path/'source-mismatch.json';mismatch_file.write_text(json.dumps(mismatch))
    checked=records.swdb('evaluate',mismatch_file,'--runs-dir',runs,'--format','json')
    assert checked.returncode==0,checked.stderr
    rejected=json.loads(checked.stdout)
    assert rejected['outcome']['state']=='complete' and rejected['correctness']['state']=='passed'
    assert rejected['paired_estimate']['state']=='excluded'
    assert rejected['paired_estimate']['seconds'] is None
    assert 'scope differs' in rejected['paired_estimate']['reason']
    # Withheld costs remain null even with a correctly matched persisted scope.
    unknown=copy.deepcopy(target);unknown['id']='fixture.protected.unknown-target'
    unknown['mechanisms'][1]['parameters']['read8_s'].update(value=None,basis='unknown')
    unknown_dir=tmp_path/'unknown';unknown_dir.mkdir()
    unknown_path=unknown_dir/'target.yaml';unknown_path.write_text(yaml.safe_dump(unknown,sort_keys=False))
    unknown_freeze=unknown_dir/'freeze.json'
    unknown_freeze.write_text(json.dumps({'message_version':'1.0','id':'fixture.protected.unknown-protocol',
        'version':1,'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1',
            'target_description':str(unknown_path),'inputs':['tiny-sym'],'roi':char['binding']['roi'],
            'threads':1,'input_run_arguments':{'tiny-sym':char['source']['run_arguments']}}}))
    frozen=records.swdb('freeze-protocol',unknown_freeze,'--format','json')
    assert frozen.returncode==0,frozen.stderr
    unknown_protocol=json.loads(frozen.stdout)['id']
    withheld=records.swdb('estimate','--characterization',char['id'],'--target-description',unknown_path,
        '--protocol',unknown_protocol,'--id','fixture.protected.unknown-estimate','--format','json')
    assert withheld.returncode==0,withheld.stderr
    assert json.loads(withheld.stdout)['seconds'] is None
    missing_request=copy.deepcopy(evaluation_request)
    missing_request.update(id='fixture.protected.unknown-cost',analytic_estimate='fixture.protected.unknown-estimate')
    missing_request['budget']['total_seconds']=300
    missing_file=tmp_path/'unknown-cost.json';missing_file.write_text(json.dumps(missing_request))
    checked=records.swdb('evaluate',missing_file,'--runs-dir',runs,'--format','json')
    assert checked.returncode==0,checked.stderr
    missing_pair=json.loads(checked.stdout)['paired_estimate']
    assert missing_pair['state']=='paired' and missing_pair['kernel_seconds'] is None
    assert missing_pair['seconds'] is None and missing_pair['error_band'] is None
    assert 'required_model_costs' in missing_pair['missing']
    # Automatic admission requires a unique persisted choice for every exact slot.
    ambiguous=copy.deepcopy(evaluation_request);ambiguous.pop('analytic_estimate')
    ambiguous.update(id='fixture.protected.ambiguous');ambiguous['budget']['total_seconds']=300
    ambiguous_file=tmp_path/'ambiguous.json';ambiguous_file.write_text(json.dumps(ambiguous))
    checked=records.swdb('evaluate',ambiguous_file,'--runs-dir',runs,'--format','json')
    assert checked.returncode==0,checked.stderr
    ambiguous_pair=json.loads(checked.stdout)['paired_estimate']
    assert ambiguous_pair['state']=='unavailable' and ambiguous_pair['seconds'] is None
    assert 'multiple persisted matched estimates' in ambiguous_pair['reason']
