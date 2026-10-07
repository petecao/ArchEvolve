"""Reported public fixtures for frozen empirical holdout scope (2026-10-06 ET)."""
import copy
import json
import time

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, freeze_protocol, target_description
from swdb.cpu_native_validation import PROCESS


def pair(records,tmp_path,*,tag='dev',input_id='tiny-sym',median=2.,source_policy='reported advancing fixture sources'):
    char=fixture_characterization(records.path,subject_id='stub-impl',input_id=input_id)
    char['id']='fixture.'+tag+'.counts'
    fact=lambda n:{'value':n,'basis':'reported','scope':'per_call'}
    region={'id':'fixture.compute','source_location':{'function':'fixture','line':1},'mapped':True,
        'kind':'serial_remainder','access_patterns':[],
        'operation_counts':{k:fact(2 if k=='integer' else 0) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':fact(1)},'footprint_bytes':{'value':0,'basis':'reported'},
        'address_stream_counts':{},'accelerator_calls':[]}
    char['regions']=[region];char['trials']=[{'position':i,'sources':[i+1],'regions':[copy.deepcopy(region)],'unmodeled_calls':[]} for i in range(5)]
    si=char['binding']['subject_source_identity'];si.update(source_root_sha256='1'*64,
        timed_wrapper_sha256='2'*64,source_policy=source_policy,trial_count=5)
    graph={'num_nodes':16,'reported_edges':32,'directed':True}
    char['binding']['execution_receipt']={'graph':graph}
    char.pop('identity_sha256');char['identity_sha256']=digest(char)
    records.write('workload_characterizations/'+char['id']+'.yaml',char)
    target=target_description(tmp_path);td=yaml.safe_load(target.read_text());td['mechanisms']=td['mechanisms'][:1]
    td['mechanisms'][0]['parameters']['integer_ops_per_s']['value']=1.
    target.write_text(yaml.safe_dump(td))
    request=tmp_path/(tag+'-freeze.yaml')
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.'+tag+'.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':str(target),
            'inputs':[input_id],'roi':'fixture.stream.v1','threads':1}}))
    frozen=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    protocol_id=json.loads(frozen.stdout)['id']
    estimate_id='fixture.'+tag+'.estimate'
    estimated=run_swdb('estimate','--records',records.path,'--characterization',char['id'],
        '--target-description',target,'--protocol',protocol_id,'--id',estimate_id,'--format','json')
    assert estimated.returncode==0,estimated.stderr+estimated.stdout
    estimate=json.loads(estimated.stdout);protocol=records.read('protocols/'+protocol_id+'.yaml')
    now=time.time_ns()
    validation={'kind':'cpu_native_validation','schema_version':'0.4','id':'fixture.'+tag+'.validation',
        'status':'draft','created':'2026-10-06','updated':'2026-10-06',
        'provenance':[{'id':'hand','kind':'source_code','description':'Reported rounding/scope fixture, no native measurement.'}],
        'format':'swdb.cpu-native-validation.v1','backend':'native','evidence_kind':'fixture',
        'characterization':char['id'],'characterization_sha256':digest(char),'implementation':'stub-impl',
        'input':input_id,'target':'mbit10','threads':1,'timing_arguments':[],'development_band':None,
        'estimate_protocol':{'id':protocol_id,'sha256':digest(protocol),
            'estimator_sha256':protocol['settings']['estimator_sha256'],
            'target_description_sha256':protocol['settings']['target_description']['sha256']},
        'scope':{'roi':'fixture.stream.v1','process_policy':PROCESS,'source_policy':si['source_policy'],
            'input_sha256':char['binding']['input_record_sha256'],'source_root_sha256':si['source_root_sha256'],
            'translation_unit_sha256':char['source']['sha256'],'timed_wrapper_sha256':si['timed_wrapper_sha256'],
            'observed_graph':graph,'observed_graph_metadata_sha256':digest(graph),'graph_content_digest':None},
        'context':{'instrumented_timer':False,'flags':[],'started_ns':now,'timing_started_ns':now,'finished_ns':now+1,
            'compiler_version':'reported fixture','compiler_sha256':'3'*64,'llvm_version':'22.fixture',
            'run_library_paths':[],'loaded_libraries':{},'native_runtime':{},'counted_native_runtime_sha256':None},
        'correctness':{'state':'passed','separate_process':True,'arguments':['-v'],'checks':['PASS']*5},
        'trials':[{'position':i,'source':i+1,'printed_duration_s':median,'printed_text':f'{median:.5f}',
            'interval_s':[max(0.,median-.000005),median+.000005],'basis':'reported'} for i in range(5)],
        'summary':{'median_whole_call_s':median,'rounding_half_width_s':.000005,'basis':'reported'},'raw_artifacts':[]}
    validation['identity_sha256']=digest(validation)
    records.write('cpu_native_validations/'+validation['id']+'.yaml',validation)
    return estimate,validation


@pytest.mark.parametrize('case',['outside','inside','source_policy','before_freeze','wrong_protocol','wrong_phase'])
def test_reported_holdout_keeps_frozen_width_and_refuses_scope_or_order_gaps(records,tmp_path,case):
    records.add_stub()
    estimate,validation=pair(records,tmp_path)
    frozen=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',estimate['id'],
        '--validation',validation['id'],'--id','fixture.dev.band','--fixture','--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    band=json.loads(frozen.stdout)
    assert band['state']=='fixture' and band['width_log']>0
    inp=records.read('inputs/tiny-sym.yaml');inp['id']='fixture.holdout.input';records.write('inputs/'+inp['id']+'.yaml',inp)
    held,observed=pair(records,tmp_path,tag='held',input_id=inp['id'],median=4. if case=='outside' else 2.,
        source_policy='different reported source policy' if case=='source_policy' else 'reported advancing fixture sources')
    observed['development_band']=None if case=='wrong_phase' else band['id']
    if case=='before_freeze':
        observed['context']['started_ns']=band['frozen_ns']-3;observed['context']['timing_started_ns']=band['frozen_ns']-2
    if case=='wrong_protocol':observed['estimate_protocol']['sha256']='f'*64
    observed.pop('identity_sha256');observed['identity_sha256']=digest(observed)
    records.write('cpu_native_validations/'+observed['id']+'.yaml',observed)
    result=run_swdb('validate-cpu-error-band','--records',records.path,'--development-band',band['id'],
        '--estimate',held['id'],'--validation',observed['id'],'--id','fixture.held.band','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    assert data['state']==('fixture' if case=='inside' else 'failed') and data['width_log']==band['width_log']
    assert data['admission']['validated'] is False and data['admission']['holdout_passed']==(case=='inside')
    expected={'outside':'empirical_holdout_outside_frozen_width','source_policy':'exact_development_source_runtime_scope',
        'before_freeze':'holdout_timing_after_frozen_development_width','wrong_protocol':'exact_prior_frozen_estimate_protocol','wrong_phase':'prior_development_band_binding'}
    if case in expected:assert expected[case] in data['admission']['missing']
    assert data['development_band']==band['id']
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_reported_holdout_never_grants_confidence_in_a_frozen_protocol(records,tmp_path):
    records.add_stub()
    estimate,validation=pair(records,tmp_path)
    frozen=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',estimate['id'],
        '--validation',validation['id'],'--id','fixture.dev.band','--fixture','--format','json')
    assert frozen.returncode==0,frozen.stderr
    inp=records.read('inputs/tiny-sym.yaml');inp['id']='fixture.holdout.input';records.write('inputs/'+inp['id']+'.yaml',inp)
    held,observed=pair(records,tmp_path,tag='held',input_id=inp['id'])
    observed['development_band']='fixture.dev.band';observed.pop('identity_sha256');observed['identity_sha256']=digest(observed)
    records.write('cpu_native_validations/'+observed['id']+'.yaml',observed)
    checked=run_swdb('validate-cpu-error-band','--records',records.path,'--development-band','fixture.dev.band',
        '--estimate',held['id'],'--validation',observed['id'],'--id','fixture.held.band','--fixture','--format','json')
    assert checked.returncode==0,checked.stderr
    request=tmp_path/'band-freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.band.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':str(tmp_path/'target.yaml'),
            'inputs':[inp['id']],'roi':'fixture.stream.v1','threads':1,'cpu_error_band':'fixture.held.band'}}))
    created=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert created.returncode==0,created.stderr+created.stdout
    result=run_swdb('estimate','--records',records.path,'--characterization',held['characterization'],
        '--target-description',tmp_path/'target.yaml','--protocol',json.loads(created.stdout)['id'],
        '--id','fixture.bound.held','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    assert data['seconds']==2. and data['verdict']=='within_error' and data['error_band']['validated'] is False
    assert data['error_band']['state']=='fixture'
