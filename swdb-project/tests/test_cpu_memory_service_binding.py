"""Typed conditional memory costs bound through the public module CLI (2026-10-06)."""
import json
import subprocess
import sys

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import target_description,fixture_characterization


def run_bind(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_service_binding','--records',str(records.path),
        *map(str,args),'--format','json'],capture_output=True,text=True)


def setup(records,tmp_path):
    records.add_stub();base=yaml.safe_load(target_description(tmp_path).read_text())
    base.update(id='fixture.memory.base',target='testhost')
    records.write('target_descriptions/fixture.memory.base.yaml',base)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    operations=('read','write','add-update','cas-success','cas-failure')
    kinds=('read','write','add-update','compare-and-swap','compare-and-swap')
    services=[]
    for op,kind in zip(operations,kinds):
        for width in (4,8):
            for footprint in (32768,8388608):
                services.append({'id':f'memory.{op}.{width}.{footprint}','unit':'seconds/request',
                    'event_definition':'Hand fixture only; not native evidence.',
                    'scope':{'operation':op,'update_kind':kind,'element_bytes':width,'footprint_bytes':footprint,
                        'memory_regime':'resident_serial_constructed_requests','transfer_basis':'inferred','worker_scope':'serial'},
                    'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand fixture, not native proof.'},
                    'trials':[{'events':10,'gross_seconds':3 if op=='cas-failure' else 2,'driver_seconds':1,
                        'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]})
    services.append({'id':'memory.read.1.256','unit':'seconds/request','event_definition':'Hand byte-read fixture.',
        'scope':{'operation':'read','update_kind':'read','element_bytes':1,'footprint_bytes':256,
            'memory_regime':'fixed_small_byte_read_constructed_requests','transfer_basis':'inferred','worker_scope':'serial'},
        'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand fixture only.'},
        'trials':[{'events':10,'gross_seconds':2,'driver_seconds':1,'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]})
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture','machine':'testhost','threads':1,
        'context':{'compiler_version':'hand fixture'},'settings':{'repetitions':3},'services':services}
    from swdb.cpu_service_calibration import identity
    raw['identity_sha256']=identity(raw);path=tmp_path/'memory-fixture.json';path.write_text(json.dumps(raw))
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id','fixture.memory.costs','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return (records.path/'target_descriptions/fixture.memory.base.yaml').read_bytes()


def import_narrow_stores(records,tmp_path,identifier='fixture.memory.narrow'):
    """Hand memory_v2 receipt: 1-byte writes 0.3 s/request, 2-byte writes 0.5 s/request (fixture only)."""
    services=[]
    for width,gross in ((1,4),(2,6)):
        services.append({'id':f'memory.write.{width}.8388608','unit':'seconds/request','event_definition':'Hand narrow-store fixture.',
            'scope':{'operation':'write','update_kind':'write','element_bytes':width,'footprint_bytes':8388608,
                'memory_regime':'resident_serial_constructed_requests','transfer_basis':'inferred','worker_scope':'serial'},
            'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand fixture only.'},
            'trials':[{'events':10,'gross_seconds':gross,'driver_seconds':1,'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]})
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture','machine':'testhost','threads':1,
        'context':{'compiler_version':'hand fixture'},'settings':{'group':'memory_v2','repetitions':3},'services':services}
    from swdb.cpu_service_calibration import identity
    raw['identity_sha256']=identity(raw);path=tmp_path/(identifier+'.json');path.write_text(json.dumps(raw))
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id',identifier,'--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout


def narrow_store_counts(records):
    """Add one region with 8-byte reads x3, 1-byte stores x4 and volatile 2-byte stores x2 (t75 shape)."""
    from testkit.analytic import digest
    char=records.read('workload_characterizations/fixture.counts.yaml')
    fact=lambda n:{'value':n,'basis':'reported' if n is not None else 'unknown','scope':'per_run'}
    rows=((1,'read',8,3,'load',False),(2,'write',1,4,'store',False),(3,'write',2,2,'store',True))
    counts={k:[] for k in ('read','write','add-update','compare-and-swap','min-max-update','arbitrary')}
    accesses=[]
    for site,kind,width,n,opcode,volatile in rows:
        counts[kind].append({'element_bytes':width,'requests':fact(n)})
        accesses.append({'id':'access.'+str(site),'source_location':{'function':'fixture','line':site},
            'address_shape':{'value':'constant','basis':'reported'},'stride_bytes':{'value':0,'basis':'reported'},
            'element_bytes':width,'update_kind':kind,'read_write':False,'element_count':fact(n),
            'bytes_accessed':fact(width*n),'observed_address_span_bytes':{'value':width,'basis':'reported'},
            'observed_unique_bytes':{'value':width,'basis':'reported'},'ir_lanes':1,'address_expression':'hand fixture',
            'primitive_semantics':{'format':'swdb.source-memory-primitive.v1','opcode':opcode,'value_kind':'integer',
                'element_bits':8*width,'vector':False,'atomic_ordering':'not_atomic','failure_ordering':None,
                'volatile':volatile,'weak':None,'update_opcode':None}})
    unscoped=lambda n:{'value':n,'basis':'reported' if n is not None else 'unknown'}
    memory={'format':'swdb.memory-service-counts.v1','scope':'per_run','observation_method':'source_normalized_ir_allocation_relative',
        'state':'partial','requests_by_update_kind':counts,'useful_bytes':unscoped(3*8+4*1+2*2),
        **{k:unscoped(None) for k in ('lifetime_line_union','logical_first_read_pages','logical_first_write_pages','pre_roi_allocation_pages','in_roi_allocation_pages')},
        'unknown_object_requests':unscoped(0),'missing':[],'assumption_sha256':'0'*64}
    char['regions']=[{'id':'fixture.region','source_location':{'function':'fixture','line':1},'mapped':True,'kind':'serial_remainder',
        'access_patterns':accesses,'operation_counts':{k:{'value':0,'basis':'reported','scope':'per_call'} for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':{'value':0,'basis':'reported','scope':'per_call'}},'footprint_bytes':{'value':0,'basis':'reported'},
        'active_workers':{'value':1,'basis':'reported'},'worker_context':{'team_sizes':[1],'measurement':'Hand fixture.'},
        'accelerator_calls':[],'address_stream_counts':{},'memory_service_counts':memory}]
    char.pop('identity_sha256');char['identity_sha256']=digest(char)
    records.write('workload_characterizations/fixture.counts.yaml',char)


def test_narrow_store_cells_bind_beside_v1_and_price_one_and_two_byte_stores(records,tmp_path):
    # 2026-10-12 ET (cpud ticket 02, seam 1): bind v1 + memory_v2 receipts, then estimate.
    setup(records,tmp_path);narrow_store_counts(records);import_narrow_stores(records,tmp_path)
    outcome=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--calibration','fixture.memory.narrow','--memory-footprint-bytes','8388608',
        '--memory-cas-policy','max_constructed_success_failure_median','--id','fixture.memory.narrow.bound','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    rows=json.loads(outcome.stdout)['mechanisms'][-1]['selector']['requests']
    narrow={r['element_bytes']:r['construction'] for r in rows if r['update_kind']=='write' and r['element_bytes'] in (1,2)}
    assert set(narrow)=={1,2}
    assert all(c['regime']=='resident_serial_constructed_requests' and c['footprint_bytes']==8388608 and c['primitive']=='ordinary_write' for c in narrow.values())
    from testkit.analytic import freeze_protocol
    target=records.path/'target_descriptions/fixture.memory.narrow.bound.yaml'
    protocol=freeze_protocol(records.path,tmp_path,target,roi='fixture.stream.v1',input_id='tiny-sym')
    estimated=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts','--target-description',target,
        '--protocol',protocol,'--id','fixture.memory.narrow.estimate','--format','json')
    assert estimated.returncode==0,estimated.stderr+estimated.stdout
    region=json.loads(estimated.stdout)['regions'][0]
    model=next(b for b in region['bounds'] if b['model']=='memory_service_scenario')
    assert not any(m.startswith('memory_scenario.cell.write') for m in model['missing']),model['missing']
    # 3 x 0.1 (v1 read 8) + 4 x 0.3 (v2 write 1) + 2 x 0.5 (v2 write 2), from the hand gross-minus-driver rates.
    assert model['seconds']==pytest.approx(2.5) and model['missing']==[]
    assert records.validate().returncode==0


def test_narrow_store_receipt_bound_twice_is_an_ambiguous_duplicate(records,tmp_path):
    setup(records,tmp_path);import_narrow_stores(records,tmp_path);import_narrow_stores(records,tmp_path,'fixture.memory.narrow.again')
    refused=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--calibration','fixture.memory.narrow','--calibration','fixture.memory.narrow.again',
        '--memory-footprint-bytes','8388608','--memory-cas-policy','max_constructed_success_failure_median','--id','fixture.dup','--fixture')
    assert refused.returncode!=0 and 'ambiguous duplicate constructed memory cell' in refused.stderr
    assert not (records.path/'target_descriptions/fixture.dup.yaml').exists()


def test_binding_selects_preregistered_footprint_retains_cas_inputs_and_does_not_reuse_stream_costs(records,tmp_path):
    before=setup(records,tmp_path)
    outcome=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--memory-footprint-bytes','8388608',
        '--memory-cas-policy','max_constructed_success_failure_median','--id','fixture.memory.bound','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    target=json.loads(outcome.stdout);model=target['mechanisms'][-1]
    assert model['model']=='memory_service_scenario'
    assert all(m['model']!='streaming_bandwidth' for m in target['mechanisms'])
    assert target['extensions']['cpu_services_binding']['memory_selection']['superseded_memory_models']==['streaming_bandwidth']
    rows=model['selector']['requests']
    assert {(r['update_kind'],r['element_bytes']) for r in rows}=={
        ('read',1),('read',4),('read',8),('write',4),('write',8),('add-update',4),('add-update',8),('compare-and-swap',4),('compare-and-swap',8)}
    for row in rows:
        scope=row['construction']
        assert scope['footprint_bytes']==(256 if row['element_bytes']==1 else 8388608)
        parameter=model['parameters'][row['parameter']]
        if row['update_kind']=='compare-and-swap':
            assert parameter['value']==.2 and parameter['basis']=='inferred'
            assert len(scope['source_services'])==2 and scope['outcome_policy']=='max_constructed_success_failure_median'
        else:assert parameter['basis']=='reported'
    assert 'fixture.memory.costs' in target['calibration_sources'] and 'fixture.counts' in target['calibration_sources']
    assert (records.path/'target_descriptions/fixture.memory.base.yaml').read_bytes()==before
    assert records.validate().returncode==0


def test_binding_requires_explicit_memory_footprint_and_cas_policy_before_writing(records,tmp_path):
    setup(records,tmp_path)
    rejected=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--id','fixture.implicit.memory','--fixture')
    assert rejected.returncode!=0 and 'explicit memory footprint' in rejected.stderr
    assert not (records.path/'target_descriptions/fixture.implicit.memory.yaml').exists()


def test_binding_keeps_distinct_integer_and_floating_add_cells_in_one_coarse_bucket(records,tmp_path):
    setup(records,tmp_path)
    from swdb.cpu_service_calibration import identity
    from swdb.cpu_float_memory_calibration import PRIMITIVE
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture','machine':'testhost','threads':1,
        'context':{'compiler_version':'hand fixture'},'settings':{'group':'memory_float_v1','repetitions':3},
        'services':[{'id':'memory.floating-add-update.8.8388608','unit':'seconds/request','event_definition':'Separate hand floating monotonic fixture, never native evidence.',
            'scope':{'operation':'floating-add-update','update_kind':'add-update','element_bytes':8,'footprint_bytes':8388608,
                'memory_regime':'resident_serial_constructed_requests','transfer_basis':'inferred','worker_scope':'serial','source_primitive':PRIMITIVE},
            'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand floating event coefficient only.'},
            'trials':[{'events':10,'gross_seconds':2.,'driver_seconds':1.,'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]}]}
    raw['identity_sha256']=identity(raw);path=tmp_path/'float-binding.json';path.write_text(json.dumps(raw))
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id','fixture.float.cost','--fixture')
    assert imported.returncode==0,imported.stderr+imported.stdout
    result=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--calibration','fixture.float.cost','--memory-footprint-bytes','8388608',
        '--memory-cas-policy','max_constructed_success_failure_median','--id','fixture.mixed.memory.bound','--fixture')
    assert result.returncode==0,result.stderr+result.stdout
    rows=json.loads(result.stdout)['mechanisms'][-1]['selector']['requests']
    adds=[row for row in rows if row['update_kind']=='add-update' and row['element_bytes']==8]
    assert len(adds)==2 and len({row['parameter'] for row in adds})==2
    assert {row['construction']['primitive'] for row in adds}=={'integer_seq_cst_add','floating_monotonic_add'}
    assert records.validate().returncode==0
