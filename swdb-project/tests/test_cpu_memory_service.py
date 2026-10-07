"""Public conditional logical-request scenarios (2026-10-06 ET)."""
import json
import pytest

import yaml

from conftest import run_swdb
from testkit.cpu_service import clock_case
from testkit.analytic import digest, freeze_protocol


def memory_case(records,tmp_path,*,missing_write=False,primitive_case=None,extra_selector=None):
    clock_case(records,tmp_path,events=0)
    char=records.read('workload_characterizations/fixture.counts.yaml');char['id']='fixture.memory.counts'
    fact=lambda n:{'value':n,'basis':'reported' if n is not None else 'unknown','scope':'per_run'}
    counts={k:[] for k in ('read','write','add-update','compare-and-swap','min-max-update','arbitrary')}
    read_kind='add-update' if primitive_case in ('floating_add','integer_add') else 'read'
    counts[read_kind]=[{'element_bytes':8,'requests':fact(3)}]
    counts['write']=[{'element_bytes':4,'requests':fact(2)}]
    char['regions'][0]['memory_service_counts']={'format':'swdb.memory-service-counts.v1','scope':'per_run',
        'observation_method':'source_normalized_ir_allocation_relative','state':'partial',
        'requests_by_update_kind':counts,'useful_bytes':fact(32),'lifetime_line_union':fact(None),
        'logical_first_read_pages':fact(None),'logical_first_write_pages':fact(None),
        'pre_roi_allocation_pages':fact(None),'in_roi_allocation_pages':fact(None),
        'unknown_object_requests':fact(1),'missing':['unresolved_object_requests'],'assumption_sha256':'0'*64}
    for field in ('useful_bytes','lifetime_line_union','logical_first_read_pages','logical_first_write_pages','pre_roi_allocation_pages','in_roi_allocation_pages','unknown_object_requests'):
        char['regions'][0]['memory_service_counts'][field].pop('scope')
    primitive=lambda opcode,bits:{'format':'swdb.source-memory-primitive.v1','opcode':opcode,
        'value_kind':'integer','element_bits':bits,'vector':False,'atomic_ordering':'not_atomic',
        'failure_ordering':None,'volatile':False,'weak':None,'update_opcode':None}
    accesses=[]
    for site,kind,width,n,opcode in ((1,read_kind,8,3,'load'),(2,'write',4,2,'store')):
        accesses.append({'id':'access.'+str(site),'source_location':{'function':'fixture','line':site},
            'address_shape':{'value':'constant','basis':'reported'},'stride_bytes':{'value':0,'basis':'reported'},
            'element_bytes':width,'update_kind':kind,'read_write':False,'element_count':fact(n),
            'bytes_accessed':fact(width*n),'observed_address_span_bytes':{'value':width,'basis':'reported'},
            'observed_unique_bytes':{'value':width,'basis':'reported'},'ir_lanes':1,'address_expression':'hand fixture',
            'primitive_semantics':primitive(opcode,width*8)})
    if primitive_case=='absent':
        for access in accesses:access.pop('primitive_semantics')
    elif primitive_case in ('floating_add','integer_add'):
        accesses[0]['read_write']=True
        accesses[0]['primitive_semantics'].update(opcode='atomicrmw',value_kind='floating' if primitive_case=='floating_add' else 'integer',
            update_opcode='fadd' if primitive_case=='floating_add' else 'add',atomic_ordering='seq_cst')
    elif primitive_case=='exchange':accesses[1]['primitive_semantics'].update(opcode='atomicrmw',update_opcode='xchg',atomic_ordering='seq_cst')
    elif primitive_case=='vector':accesses[0]['primitive_semantics']['vector']=True;accesses[0]['ir_lanes']=4
    elif primitive_case=='count_gap':accesses[0]['element_count']['value']=2
    char['regions'][0]['access_patterns']=accesses
    char.pop('identity_sha256');char['identity_sha256']=digest(char)
    records.write('workload_characterizations/fixture.memory.counts.yaml',char)
    target=yaml.safe_load((tmp_path/'target.yaml').read_text());target['mechanisms']=target['mechanisms'][:1]
    target['mechanisms'].append({'model':'memory_service_scenario','selector':{
        'domain':'host','worker_scope':'serial_T1','scenario':'resident_serial_constructed_requests',
        'transfer_basis':'inferred','object_scope':'logical_requests_and_bounded_referent_views',
        'characterization_sha256':digest(char),
        'requests':[{'update_kind':read_kind,'element_bytes':8,'parameter':'read8_s','construction':{
                        'primitive':'integer_seq_cst_add' if read_kind=='add-update' else 'ordinary_read',
                        'regime':'resident_serial_constructed_requests','footprint_bytes':8388608,'transfer_basis':'inferred',
                        'physical_cache_level':'unverified','source_services':[{'calibration':'hand.memory','service':'hand.read8','parameter':'read8_s'}]}},
                    {'update_kind':'write','element_bytes':4,'parameter':'write4_s','construction':{
                        'primitive':'ordinary_write','regime':'resident_serial_constructed_requests','footprint_bytes':8388608,'transfer_basis':'inferred',
                        'physical_cache_level':'unverified','source_services':[{'calibration':'hand.memory','service':'hand.write4','parameter':'write4_s'}]}}]},
        'parameters':{'read8_s':{'value':.5,'basis':'reported','unit':'seconds/request','source':'Hand dependent-read cell.'},
            'write4_s':{'value':None if missing_write else .5,'basis':'unknown' if missing_write else 'reported',
                'unit':'seconds/request','source':'Hand store cell.'}}})
    target['mechanisms'][-1]['selector'].update(extra_selector or {})
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


@pytest.mark.parametrize('primitive_case',['absent','floating_add','exchange','vector','count_gap'])
def test_unproved_or_different_primitive_never_consumes_integer_constructed_cost(records,tmp_path,primitive_case):
    data=memory_case(records,tmp_path,primitive_case=primitive_case)
    model=next(b for b in data['regions'][0]['bounds'] if b['model']=='memory_service_scenario')
    assert model['seconds'] is None and data['seconds'] is None
    assert any(m.startswith('memory_scenario.primitive') or m.startswith('memory_scenario.exact_source') for m in model['missing'])


def test_exact_integer_seq_cst_add_is_separately_admitted(records,tmp_path):
    data=memory_case(records,tmp_path,primitive_case='integer_add')
    model=next(b for b in data['regions'][0]['bounds'] if b['model']=='memory_service_scenario')
    assert model['seconds']==2.5


@pytest.mark.parametrize('blocked,expected',[(False,2.5),(True,None)])
def test_memory_context_admission_is_independent_of_numeric_cost(records,tmp_path,blocked,expected):
    reasons={'read8_s':['service_compiler_identity']} if blocked else {}
    data=memory_case(records,tmp_path,extra_selector={'calibration_admission':reasons})
    model=next(b for b in data['regions'][0]['bounds'] if b['model']=='memory_service_scenario')
    assert data['seconds']==expected and model['seconds']==expected
    assert not any(m=='selector.calibration_admission' for m in model['missing'])
    assert model['inputs']['calibration_admission']==reasons
