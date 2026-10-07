"""Public total-cell resource derivation, 2026-10-06 ET."""
import copy
import json
import subprocess
import sys

import pytest
import yaml

from conftest import run_swdb
from test_cpu_service_calibration import fixture_receipt, save_receipt
from testkit.analytic import digest


def derive(records, source='fixture.memory.residual', identifier='fixture.memory.resource', fixture=True):
    argv=[sys.executable,'-m','swdb.cpu_memory_resource','--records',str(records.path),
        '--source-calibration',source,'--id',identifier,'--format','json']
    if fixture:argv.append('--fixture')
    return subprocess.run(argv,capture_output=True,text=True)


def residual_fixture(records,tmp_path):
    raw=fixture_receipt();raw['settings']['group']='memory_v1'
    cell=raw['services'][0];cell.update(id='memory.write.8.8388608',unit='seconds/request',
        event_definition='One hand-proved logical ordinary8B write, not physical traffic.',
        scope={'operation':'write','update_kind':'write','element_bytes':8,'footprint_bytes':8388608,
            'memory_regime':'resident_serial_constructed_requests','worker_scope':'serial','transfer_basis':'inferred'})
    for trial,gross in zip(cell['trials'],[.9,1.2,1.]):trial['gross_seconds']=gross
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,
        '--receipt',save_receipt(tmp_path,raw),'--id','fixture.memory.residual','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    return json.loads(imported.stdout)


def test_total_cell_keeps_failed_subtraction_and_original_bytes(records,tmp_path):
    original=residual_fixture(records,tmp_path)
    path=records.path/'cpu_service_calibrations/fixture.memory.residual.yaml';before=path.read_bytes()
    assert original['services'][0]['parameter']['value'] is None
    result=derive(records)
    assert result.returncode==0,result.stderr+result.stdout
    resource=json.loads(result.stdout);cell=resource['services'][0]
    assert resource['kind']=='cpu_memory_resource_calibration'
    assert resource['recipe']['id']=='gross_constructed_resource_v1'
    assert resource['recipe']['composition']=='max_with_compute'
    assert resource['source_calibration_sha256']==digest(original)
    assert resource['calibration_sources']==[original['id']]
    assert cell['parameter']['value']==pytest.approx(.1)
    assert cell['parameter']['basis']=='reported'
    assert cell['gross_seconds_per_request']['spread']==pytest.approx(.03)
    assert cell['trials']==original['services'][0]['trials']
    assert cell['paired_residual']['parameter']['value'] is None
    assert cell['paired_residual']['seconds_per_event']['min']==pytest.approx(-.01)
    assert path.read_bytes()==before
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_recipe_rejects_tampered_source_and_output_with_resealed_identity(records,tmp_path):
    original=residual_fixture(records,tmp_path)
    refused=derive(records,identifier='fixture.unapproved',fixture=False)
    assert refused.returncode!=0 and 'fixture' in refused.stderr
    result=derive(records);assert result.returncode==0,result.stderr
    resource=json.loads(result.stdout);resource['services'][0]['parameter']['value']=.2
    resource.pop('identity_sha256');resource['identity_sha256']=digest(resource)
    records.write('cpu_memory_resource_calibrations/fixture.memory.resource.yaml',resource)
    rejected=records.validate()
    assert rejected.returncode!=0 and 'retained inputs differ' in rejected.stdout+rejected.stderr
    source=copy.deepcopy(original);source['services'][0]['parameter'].update(value=.001,basis='reported')
    source.pop('identity_sha256');source['identity_sha256']=digest(source)
    records.write('cpu_service_calibrations/fixture.memory.residual.yaml',source)
    refused=derive(records,identifier='fixture.tampered.source')
    assert refused.returncode!=0 and 'invalid source calibration' in refused.stderr


def test_resource_binding_pins_total_and_original_records_and_explicit_recipe(records,tmp_path):
    from test_cpu_service_binding import bind
    from testkit.analytic import target_description, fixture_characterization
    records.add_stub()
    base=yaml.safe_load(target_description(tmp_path).read_text());base.update(id='fixture.cpu.base',target='mbit10')
    records.write('target_descriptions/fixture.cpu.base.yaml',base)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    residual_fixture(records,tmp_path)
    result=derive(records);assert result.returncode==0,result.stderr
    binding=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.resource','--id','fixture.cpu.total',
        '--memory-footprint-bytes','8388608','--memory-cas-policy','max_constructed_success_failure_median','--fixture')
    assert binding.returncode==0,binding.stderr+binding.stdout
    target=json.loads(binding.stdout);model=target['mechanisms'][-1];cell=model['selector']['requests'][0]
    assert model['accounting']=='resource_bound'
    assert cell['construction']['cost_basis']=='gross_constructed_resource_v1'
    assert model['parameters'][cell['parameter']]['value']==pytest.approx(.1)
    assert target['calibration_sources']==['fixture.memory.resource','fixture.counts']
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr
    assert json.loads(result.stdout)['calibration_sources']==['fixture.memory.residual']
    from testkit.analytic import freeze_protocol
    protocol_id=freeze_protocol(records.path,tmp_path,'fixture.cpu.total',roi='fixture.stream.v1',input_id='tiny-sym')
    protocol=records.read('protocols/'+protocol_id+'.yaml')
    dependencies=protocol['settings']['dependency_identities']
    assert dependencies['fixture.memory.resource']==digest(json.loads(result.stdout))
    assert dependencies['fixture.memory.residual']==digest(records.read('cpu_service_calibrations/fixture.memory.residual.yaml'))


def test_native_total_cells_keep_all_original_trials_and_inferred_basis(records,tmp_path):
    from conftest import REPO
    identifier='mbit10.cpu.lanl20261006.service.memory.a1'
    path=REPO/'records/cpu_service_calibrations'/f'{identifier}.yaml'
    original=yaml.safe_load(path.read_text());before=path.read_bytes()
    records.write('cpu_service_calibrations/'+path.name,original)
    result=derive(records,identifier,'fixture.native.total',False)
    assert result.returncode==0,result.stderr+result.stdout
    resource=json.loads(result.stdout)
    assert resource['evidence_kind']=='native'
    assert len(resource['services'])==20
    unresolved=[s for s in resource['services'] if s['paired_residual']['parameter']['value'] is None]
    assert len(unresolved)==2 and all(s['scope']['operation']=='write' and s['scope']['element_bytes']==8 for s in unresolved)
    assert all(s['parameter']['basis']=='inferred' and s['parameter']['value']>0 for s in resource['services'])
    for derived,source in zip(resource['services'],original['services']):
        assert derived['trials']==source['trials'] and derived['denominator']==source['denominator']
    assert path.read_bytes()==before
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr
