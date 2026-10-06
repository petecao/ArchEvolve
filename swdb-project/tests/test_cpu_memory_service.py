"""Public conditional logical-request scenarios (2026-10-06 ET)."""
import json

import yaml

from conftest import run_swdb
from test_analytic_cpu_service import clock_case
from testkit.analytic import digest, freeze_protocol


def memory_case(records,tmp_path,*,missing_write=False):
    clock_case(records,tmp_path,events=0)
    char=records.read('workload_characterizations/fixture.counts.yaml');char['id']='fixture.memory.counts'
    fact=lambda n:{'value':n,'basis':'reported' if n is not None else 'unknown','scope':'per_run'}
    counts={k:[] for k in ('read','write','add-update','compare-and-swap','min-max-update','arbitrary')}
    counts['read']=[{'element_bytes':8,'requests':fact(3)}]
    counts['write']=[{'element_bytes':4,'requests':fact(2)}]
    char['regions'][0]['memory_service_counts']={'format':'swdb.memory-service-counts.v1','scope':'per_run',
        'observation_method':'source_normalized_ir_allocation_relative','state':'partial',
        'requests_by_update_kind':counts,'useful_bytes':fact(32),'lifetime_line_union':fact(None),
        'logical_first_read_pages':fact(None),'logical_first_write_pages':fact(None),
        'pre_roi_allocation_pages':fact(None),'in_roi_allocation_pages':fact(None),
        'unknown_object_requests':fact(1),'missing':['unresolved_object_requests'],'assumption_sha256':'0'*64}
    for field in ('useful_bytes','lifetime_line_union','logical_first_read_pages','logical_first_write_pages','pre_roi_allocation_pages','in_roi_allocation_pages','unknown_object_requests'):
        char['regions'][0]['memory_service_counts'][field].pop('scope')
    char.pop('identity_sha256');char['identity_sha256']=digest(char)
    records.write('workload_characterizations/fixture.memory.counts.yaml',char)
    target=yaml.safe_load((tmp_path/'target.yaml').read_text());target['mechanisms']=target['mechanisms'][:1]
    target['mechanisms'].append({'model':'memory_service_scenario','selector':{
        'domain':'host','worker_scope':'serial_T1','scenario':'resident_serial_constructed_requests',
        'transfer_basis':'inferred','object_scope':'logical_requests_and_bounded_referent_views',
        'characterization_sha256':digest(char),
        'requests':[{'update_kind':'read','element_bytes':8,'parameter':'read8_s'},
                    {'update_kind':'write','element_bytes':4,'parameter':'write4_s'}]},
        'parameters':{'read8_s':{'value':.5,'basis':'reported','unit':'seconds/request','source':'Hand dependent-read cell.'},
            'write4_s':{'value':None if missing_write else .5,'basis':'unknown' if missing_write else 'reported',
                'unit':'seconds/request','source':'Hand store cell.'}}})
    path=tmp_path/'memory-target.yaml';path.write_text(yaml.safe_dump(target,sort_keys=False))
    frozen=tmp_path/'memory-freeze.yaml'
    frozen.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.memory.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':str(path),
            'inputs':['tiny-sym'],'roi':'fixture.stream.v1','threads':1}}))
    created=run_swdb('freeze-protocol',frozen,'--records',records.path,'--format','json')
    assert created.returncode==0,created.stderr+created.stdout
    protocol=json.loads(created.stdout)['id']
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.memory.counts',
        '--target-description',path,'--protocol',protocol,'--id','fixture.memory.estimate','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return json.loads(result.stdout)


def test_exact_logical_requests_use_conditional_service_without_inventing_residency(records,tmp_path):
    data=memory_case(records,tmp_path)
    model=next(b for b in data['regions'][0]['bounds'] if b['model']=='memory_service_scenario')
    assert model['seconds']==2.5 and data['seconds']==2.5
    assert model['inputs']['unknown_object_requests']['value']==1
    assert model['inputs']['physical_residency_known'] is False
    assert 'inferred' in ' '.join(model['notes'])
    assert records.validate().returncode==0


def test_missing_executed_memory_cell_keeps_compute_bound_and_null_total(records,tmp_path):
    data=memory_case(records,tmp_path,missing_write=True)
    bounds=data['regions'][0]['bounds']
    model=next(b for b in bounds if b['model']=='memory_service_scenario')
    assert model['seconds'] is None and data['seconds'] is None
    assert 'memory_scenario.cell.write.4' in model['missing']
    assert next(b for b in bounds if b['model']=='compute_throughput')['seconds']==2
