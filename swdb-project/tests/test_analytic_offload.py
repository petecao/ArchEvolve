"""Public composition contracts. Artificial event counts are fixtures only.
Updated: 2026-10-06 ET.
"""
import json
import yaml
import pytest
from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description, freeze_protocol


def fact(value):
    return {'value': value, 'basis': 'reported', 'scope': 'per_call'}


def setup_fixture(records, tmp_path, *, events=1, setup_cost=.25):
    records.add_stub()
    data=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    data['regions']=[{'id':'fixture.region','source_location':{'function':'fixture','line':1},
        'mapped':True,'kind':'serial_remainder','access_patterns':[],
        'operation_counts':{k:fact(0 if k!='floating_point' else 32) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':fact(0)}, 'footprint_bytes':{'value':0,'basis':'reported'},
        'accelerator_calls':[] if events is None else [{'event':'fixture.command','execution_count':fact(events)}],
        'address_stream_counts':{}}]
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.counts.yaml',data)
    path=target_description(tmp_path)
    target=yaml.safe_load(path.read_text());target['target']='testhost';target['mechanisms']=target['mechanisms'][:1]
    target['mechanisms'].append({'model':'offload_setup','accounting':'additive_overhead',
        'selector':{'event_ids':['fixture.command']},
        'parameters':{'seconds_per_event':{'value':setup_cost,'basis':'unknown' if setup_cost is None else 'reported',
            'source':'Hand-computed contract fixture only.','unit':'seconds/event'}}})
    path.write_text(yaml.safe_dump(target,sort_keys=False))
    protocol=freeze_protocol(records.path,tmp_path,path,roi='fixture.stream.v1',input_id='tiny-sym')
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',path,'--protocol',protocol,'--id','fixture.estimate','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return json.loads(result.stdout)


def test_resource_bound_plus_setup_is_added_once(records,tmp_path):
    result=setup_fixture(records,tmp_path)
    region=result['regions'][0]
    assert region['bounds'][0]['seconds']==2
    assert region['overheads'][0]['seconds']==.25
    assert region['seconds']==2.25 and result['seconds']==2.25
    assert result['evidence_kind']=='contract_fixture'
    checked=records.validate()
    assert checked.returncode==0,checked.stdout+checked.stderr


@pytest.mark.parametrize('events, cost, expected', [(1,None,None),(0,None,2.)])
def test_setup_unknown_and_proven_zero_propagate(records,tmp_path,events,cost,expected):
    result=setup_fixture(records,tmp_path,events=events,setup_cost=cost)
    assert result['seconds']==expected
    if events:
        assert result['regions'][0]['overheads'][0]['missing']==['seconds_per_event']


def test_unobserved_setup_is_unknown_instead_of_zero(records,tmp_path):
    result=setup_fixture(records,tmp_path,events=None)
    assert result['seconds'] is None
    assert 'accelerator_calls.event_coverage' in result['regions'][0]['overheads'][0]['missing']
