"""Reported public fixtures for frozen empirical holdout scope (2026-10-06 ET).

Updated 2026-10-09 23:10 ET (code review of tickets 07/11): unobserved held-out inputs
(F1), the reported D25 token (F2), large-error explanations (F6) and the ArchEvolve-only
refusals (F7).
"""
import copy
import json
import math
import time

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, freeze_protocol, target_description
from swdb.cpu_native_validation import PROCESS


def pair(records,tmp_path,*,tag='dev',input_id='tiny-sym',median=2.,source_policy='reported advancing fixture sources',
         subject_id='stub-impl',operations=2):
    char=fixture_characterization(records.path,subject_id=subject_id,input_id=input_id)
    char['id']='fixture.'+tag+'.counts'
    fact=lambda n:{'value':n,'basis':'reported','scope':'per_call'}
    region={'id':'fixture.compute','source_location':{'function':'fixture','line':1},'mapped':True,
        'kind':'serial_remainder','access_patterns':[],
        'operation_counts':{k:fact(operations if k=='integer' else 0) for k in ('integer','floating_point','branch','atomic')},
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
        'characterization':char['id'],'characterization_sha256':digest(char),'implementation':subject_id,
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


def rehash(records,data,folder='cpu_native_validations'):
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write(folder+'/'+data['id']+'.yaml',data)


@pytest.mark.parametrize('case',['outside','inside','source_policy','before_freeze','wrong_protocol','wrong_phase',
                                 'reobserved','remeasured'])
def test_reported_holdout_keeps_frozen_width_and_refuses_scope_or_order_gaps(records,tmp_path,case):
    records.add_stub()
    estimate,validation=pair(records,tmp_path)
    frozen=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',estimate['id'],
        '--validation',validation['id'],'--id','fixture.dev.band','--fixture','--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    band=json.loads(frozen.stdout)
    assert band['state']=='fixture' and band['width_log']>0
    assert band['format']=='swdb.cpu-error-band.v2' and band['large_errors']==[]
    inp=records.read('inputs/tiny-sym.yaml');inp['id']='fixture.holdout.input';records.write('inputs/'+inp['id']+'.yaml',inp)
    if case in ('reobserved','remeasured'):
        # F1: an earlier timing of the held-out input (development phase, or a prior
        # held-out attempt against this band) means its outcome is no longer unseen.
        _,seen=pair(records,tmp_path,tag='seen',input_id=inp['id'])
        if case=='remeasured':
            seen['development_band']=band['id'];rehash(records,seen)
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
        'before_freeze':'holdout_timing_after_frozen_development_width','wrong_protocol':'exact_prior_frozen_estimate_protocol','wrong_phase':'prior_development_band_binding',
        'reobserved':'unobserved_heldout_input','remeasured':'unobserved_heldout_input'}
    if case in expected:assert expected[case] in data['admission']['missing']
    if case=='inside':assert 'unobserved_heldout_input' not in data['admission']['missing']
    assert data['development_band']==band['id']
    # F6: a large error carries its forecast-only ranked region explanation.
    if case=='outside':
        [row]=data['large_errors']
        assert row['estimate']==held['id'] and row['direction']=='under_prediction'
        assert row['rounding_aware_absolute_log_error']>data['admission']['large_error_threshold_log']
        assert [(r['region'],r['limiting_bound'],r['share_of_predicted_seconds']) for r in row['dominant_regions']]==[
            ('fixture.compute','compute_throughput',1.0)]
    else:
        assert data['large_errors']==[]
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr
    if case=='outside':
        tampered=copy.deepcopy(data);tampered['large_errors']=[]
        rehash(records,tampered,'cpu_error_bands')
        rejected=records.validate()
        assert rejected.returncode!=0 and 'large-error' in rejected.stdout+rejected.stderr


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
    assert 'fixture_verdict' not in data['error_band']


def test_reported_holdout_shows_the_d25_token_on_both_sides_without_changing_the_verdict(records,tmp_path):
    """F2 (code review 2026-10-09 ET): the three-state arithmetic runs through the public
    estimate seam on a reported held-out fixture band; the public verdict stays within_error."""
    records.add_stub()
    impl=records.read('implementations/stub-impl.yaml');impl['id']='stub-impl-fast'
    records.write('implementations/stub-impl-fast.yaml',impl)
    slow,slow_seen=pair(records,tmp_path,tag='dev',operations=4,median=4.)
    fast,fast_seen=pair(records,tmp_path,tag='devfast',subject_id='stub-impl-fast',operations=2,median=2.)
    frozen=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',slow['id'],'--estimate',fast['id'],
        '--validation',slow_seen['id'],'--validation',fast_seen['id'],'--id','fixture.dev.band','--fixture','--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    inp=records.read('inputs/tiny-sym.yaml');inp['id']='fixture.holdout.input';records.write('inputs/'+inp['id']+'.yaml',inp)
    held_slow,observed_slow=pair(records,tmp_path,tag='held',input_id=inp['id'],operations=4,median=4.)
    held_fast,observed_fast=pair(records,tmp_path,tag='heldfast',input_id=inp['id'],subject_id='stub-impl-fast',operations=2,median=2.)
    for observed in (observed_slow,observed_fast):
        observed['development_band']='fixture.dev.band';rehash(records,observed)
    checked=run_swdb('validate-cpu-error-band','--records',records.path,'--development-band','fixture.dev.band',
        '--estimate',held_slow['id'],'--estimate',held_fast['id'],'--validation',observed_slow['id'],
        '--validation',observed_fast['id'],'--id','fixture.held.band','--fixture','--format','json')
    assert checked.returncode==0,checked.stderr
    held_band=json.loads(checked.stdout)
    assert held_band['state']=='fixture' and held_band['admission']['holdout_passed'] is True
    request=tmp_path/'band-freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.band.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':str(tmp_path/'target.yaml'),
            'inputs':[inp['id']],'roi':'fixture.stream.v1','threads':1,'cpu_error_band':'fixture.held.band'}}))
    created=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert created.returncode==0,created.stderr+created.stdout
    protocol=json.loads(created.stdout)['id']
    def estimate(rid,characterization,baseline=None):
        extra=['--baseline',baseline] if baseline else []
        result=run_swdb('estimate','--records',records.path,'--characterization',characterization,
            '--target-description',tmp_path/'target.yaml','--protocol',protocol,'--id',rid,*extra,'--format','json')
        assert result.returncode==0,result.stderr+result.stdout
        return json.loads(result.stdout)
    assert estimate('fixture.bound.slow',held_slow['characterization'])['seconds']==4.
    assert estimate('fixture.bound.fast',held_fast['characterization'])['seconds']==2.
    for rid,characterization,baseline,ratio,token in (
            ('fixture.bound.gain',held_fast['characterization'],'fixture.bound.slow',2.,'estimated_gain'),
            ('fixture.bound.loss',held_slow['characterization'],'fixture.bound.fast',.5,'estimated_no_gain'),
            # Equal speed: the narrow fixture band lies wholly below 1.05.
            ('fixture.bound.same',held_slow['characterization'],'fixture.bound.slow',1.,'estimated_no_gain')):
        data=estimate(rid,characterization,baseline)
        assert data['ratio']==ratio and data['verdict']=='within_error'
        band=data['error_band']
        assert band['validated'] is False and band['fixture_verdict']==token and band['gain_threshold']==1.05
        low,high=band['ratio_log_interval']
        assert low<high and abs((low+high)/2-math.log(ratio))<1e-12 and abs((high-low)-4*band['width_log'])<1e-12
    assert records.validate().returncode==0


def test_three_state_boundaries():
    from swdb.cpu_error_band import three_state
    width=math.log(1.1)
    assert three_state(1.05*1.1**2*1.001,width)[0]=='estimated_gain'
    assert three_state(1.05/1.1**2/1.001,width)[0]=='estimated_no_gain'
    assert three_state(1.05*1.001,width)[0]=='within_error'
    # A band that only touches 1.05 still covers it.
    assert three_state(1.05,0.)==('within_error',[math.log(1.05)]*2)
    assert three_state(None,width)==('within_error',None) and three_state(2.,None)==('within_error',None)


EXTENSA_CAMPAIGN='extensa-native-bfs-20261006-a1'


def test_cpu_error_check_admits_archevolve_mode_timings_only(records,tmp_path):
    """F7 (code review 2026-10-09 ET): story 57 / D28 through the public commands."""
    records.add_stub()
    estimate,validation=pair(records,tmp_path)
    tagged=copy.deepcopy(validation);tagged.update(id='fixture.dev.extensa.validation',mode='extensa',campaign=EXTENSA_CAMPAIGN)
    rehash(records,tagged)
    refused=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',estimate['id'],
        '--validation',tagged['id'],'--id','fixture.extensa.band','--fixture','--format','json')
    assert refused.returncode!=0 and 'ADR 0013' in refused.stderr and 'Extensa' in refused.stderr,refused.stderr+refused.stdout
    assert tagged['id'] in refused.stderr
    env={'SWDB_EXTENSA_CAMPAIGN':EXTENSA_CAMPAIGN}
    refused=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate',estimate['id'],
        '--validation',validation['id'],'--id','fixture.extensa.band','--fixture','--format','json',env=env)
    assert refused.returncode!=0 and 'CPU error bands require ArchEvolve mode' in refused.stderr,refused.stderr
    refused=run_swdb('validate-cpu-error-band','--records',records.path,'--development-band','fixture.dev.band',
        '--estimate',estimate['id'],'--validation',validation['id'],'--id','fixture.extensa.band','--fixture',env=env)
    assert refused.returncode!=0 and 'CPU error validation requires ArchEvolve mode' in refused.stderr,refused.stderr
    refused=run_swdb('collect-cpu-native-validation','--records',records.path,'--characterization',estimate['characterization'],
        '--id','fixture.extensa.validation','--output',tmp_path/'extensa-validation','--llvm-bin',tmp_path,'--fixture',env=env)
    assert refused.returncode!=0 and 'ArchEvolve-mode evidence only' in refused.stderr,refused.stderr
    assert not (tmp_path/'extensa-validation').exists()
    assert not list(records.path.rglob('fixture.extensa.band*'))
