"""Public paper-scoped MAPLE target admission. Created: 2026-10-06 ET."""
import json
import yaml
from conftest import REPO,run_swdb

TARGET='maple-isca2022.fpga-reference.t2'


def test_reported_fpga_target_freezes_without_simulation_or_service_fabrication(records,tmp_path):
    records.add_stub()
    added=run_swdb('add',REPO/'records/target_descriptions'/f'{TARGET}.yaml',
        '--records',records.path,'--db',tmp_path/'index.sqlite')
    assert added.returncode==0,added.stdout+added.stderr
    request=tmp_path/'freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.maple.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':TARGET,
            'threads':2,'roi':'fixture.whole_call.v1','sources':['stub-impl'],'inputs':['tiny-sym']}}))
    frozen=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert frozen.returncode==0,frozen.stdout+frozen.stderr
    target=json.loads(frozen.stdout)['settings']['target_description']['snapshot']
    assert target['threads']==2 and target['calibration_sources']==[]
    reference=target['extensions']['reference_configuration']
    assert reference['evidence_scope']=='reported_fpga_reference_only'
    assert reference['core_frequency_hz']['value']==60000000
    assert reference['dram_latency_cycles']['value']==300
    assert reference['shared_l2_bytes']['value']==65536
    assert reference['dram_bandwidth_bytes_per_s']['value'] is None
    assert target['extensions']['accuracy_validation'] is False
    assert target['extensions']['estimate_only'] is True
    queue=next(m for m in target['mechanisms'] if m['model']=='fetch_queue')
    assert queue['parameters']['queue_entries']['value'] is None
    assert all(fact['basis']=='unknown' for fact in queue['parameters'].values())
    assert target['dram_address_layout'] is None and 'functional_observation' not in target
    assert all(fact['value'] is None for m in target['mechanisms'] if m['model']=='compute_throughput'
               for fact in m['parameters'].values())


def test_public_maple_estimate_exposes_missing_command_counts_and_effective_cost(records,tmp_path):
    from swdb import artifacts
    from testkit.analytic import fixture_characterization,freeze_protocol
    records.add_stub()
    data=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym',threads=2)
    # Independent four-integer-operation contract fixture; no target command stream.
    data['regions']=[{'id':'fixture.host','kind':'serial_remainder','mapped':True,
        'source_location':{'function':'fixture','line':1},
        'operation_counts':{k:{'value':4 if k=='integer' else 0,'basis':'reported','scope':'per_call'}
            for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':{'value':0,'basis':'reported','scope':'per_call'}},
        'footprint_bytes':{'value':0,'basis':'reported'},'access_patterns':[],
        'accelerator_calls':[],'address_stream_counts':{}}]
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',data)
    target=REPO/'records/target_descriptions'/f'{TARGET}.yaml'
    protocol=freeze_protocol(records.path,tmp_path,target,roi='fixture.stream.v1',threads=2,input_id='tiny-sym')
    estimated=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',target,'--protocol',protocol,'--id','fixture.maple.estimate','--format','json')
    assert estimated.returncode==0,estimated.stdout+estimated.stderr
    result=json.loads(estimated.stdout)
    assert result['evidence_kind']=='contract_fixture' and result['seconds'] is None and result['ratio'] is None
    queue=next(b for b in result['regions'][0]['bounds'] if b['model']=='fetch_queue')
    assert queue['seconds'] is None and 'address_stream_counts.requested_target_description' in queue['missing']
    compute=next(b for b in result['regions'][0]['bounds'] if b['model']=='compute_throughput')
    assert compute['seconds'] is None and 'integer_ops_per_s' in compute['missing']
    assert result['error_band'] is None
