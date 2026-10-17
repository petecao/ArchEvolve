"""Explicit frozen bulk profile choice through the public binder,2026-10-06 ET."""
import json
import yaml
from conftest import run_swdb
from testkit.analytic import fixture_characterization, target_description
from testkit.cpu_bulk import native_bulk_receipt
from testkit.cpu_service import bind


def setup(records,tmp_path, *, second_copy_only=False, gross=False):
    from swdb.cpu_service_calibration import identity
    records.add_stub()
    base=yaml.safe_load(target_description(tmp_path).read_text());base.update(id='fixture.cpu.base',target='testhost')
    records.write('target_descriptions/fixture.cpu.base.yaml',base)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    for identifier in ('fixture.bulk.a1','fixture.bulk.a2'):
        raw=native_bulk_receipt();raw.update(evidence_kind='fixture',machine='testhost')
        if identifier=='fixture.bulk.a2' and second_copy_only:raw['services']=raw['services'][:1]
        for service in raw['services']:
            service['denominator']['basis']='reported'
            op=int(service['id'].split('.')[1])
            for trial in service['trials']:trial['gross_seconds']=trial['driver_seconds']+(.01+.01*op)
        if gross:
            raw['settings']['group']='bulk_total_v2'
            for service in raw['services']:
                service['scope']['residual_policy']={'id':'both_windows_meet_declared_threshold','minimum_window_s':.05}
                for trial in service['trials']:trial['driver_seconds']=.00001
        raw['identity_sha256']=identity(raw);receipt=tmp_path/(identifier+'.json');receipt.write_text(json.dumps(raw))
        result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',receipt,'--id',identifier,'--fixture')
        assert result.returncode==0,result.stderr+result.stdout
    return ['--target-description','fixture.cpu.base','--characterization','fixture.counts','--calibration','fixture.bulk.a1','--fixture']


def test_binder_requires_explicit_policy_and_keeps_independent_profile_parameters(records,tmp_path):
    common=setup(records,tmp_path)
    data=bind(records,*common,'--bulk-profile-policy','max_constructed_profiles_median','--id','fixture.bulk.bound')
    assert data.returncode==0,data.stderr+data.stdout
    target=json.loads(data.stdout);model=target['mechanisms'][-1]
    selection=next(c for c in model['selector']['calls'] if c['name']=='llvm.memmove.p0.p0.i64')
    assert [c['bytes'] for c in selection['bins']]==[8,292]
    for cell in selection['bins']:
        assert len(cell['source_profiles'])==3
        param=model['parameters'][cell['parameter']]
        assert param['basis']=='inferred' and param['value']==max(model['parameters'][s['parameter']]['value'] for s in cell['source_profiles'])
    assert selection['scope_assumption']['source_overlap']=='unverified'
    assert selection['scope_assumption']['physical_upper_bound'] is False
    assert records.validate().returncode==0
    refused=bind(records,*common,'--id','fixture.bulk.no.policy')
    assert refused.returncode!=0 and not (records.path/'target_descriptions/fixture.bulk.no.policy.yaml').exists()


def test_duplicate_copy_receipts_require_explicit_selection_and_duplicate_move_bins_still_refuse(records,tmp_path):
    common=setup(records,tmp_path)
    # Both fixture receipts intentionally duplicate every move bin too; selecting
    # the copy alone cannot silently pool or discard conflicting move profiles.
    data=bind(records,*common,'--calibration','fixture.bulk.a2','--bulk-profile-policy','max_constructed_profiles_median',
        '--bulk-copy-calibration','fixture.bulk.a1','--id','fixture.bulk.ambiguous')
    assert data.returncode!=0 and not (records.path/'target_descriptions/fixture.bulk.ambiguous.yaml').exists()


def test_duplicate_copy_choice_retains_one_exact_receipt_and_never_pools(records,tmp_path):
    common=setup(records,tmp_path,second_copy_only=True)
    options=['--calibration','fixture.bulk.a2','--bulk-profile-policy','max_constructed_profiles_median']
    refused=bind(records,*common,*options,'--id','fixture.bulk.copy.unselected')
    assert refused.returncode!=0 and 'duplicate bulk copy receipts' in refused.stderr
    selected=bind(records,*common,*options,'--bulk-copy-calibration','fixture.bulk.a2','--id','fixture.bulk.copy.selected')
    assert selected.returncode==0,selected.stderr+selected.stdout
    target=json.loads(selected.stdout);model=target['mechanisms'][-1]
    copy=next(c for c in model['selector']['calls'] if c['name']=='memcpy')
    source=copy['bins'][0]['source_profiles'][0]
    assert source['calibration']=='fixture.bulk.a2' and len(copy['bins'])==1
    rows=target['extensions']['cpu_services_binding']['compatibility']
    assert len([r for r in rows if r['service']=='bulk.0.8'])==1
    assert target['calibration_sources'][:2]==['fixture.bulk.a1','fixture.bulk.a2']
    assert records.validate().returncode==0


def test_gross_bulk_binding_pins_distinct_recipe_and_retains_unknown_residual_source(records,tmp_path):
    import subprocess,sys
    setup(records,tmp_path,gross=True)
    derived=subprocess.run([sys.executable,'-m','swdb.cpu_bulk_resource','--records',str(records.path),
        '--source-calibration','fixture.bulk.a1','--id','fixture.bulk.gross.resource','--fixture'],capture_output=True,text=True)
    assert derived.returncode==0,derived.stderr+derived.stdout
    result=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration','fixture.bulk.gross.resource','--fixture','--bulk-profile-policy','max_constructed_profiles_median',
        '--id','fixture.bulk.gross.bound')
    assert result.returncode==0,result.stderr+result.stdout
    target=json.loads(result.stdout);model=target['mechanisms'][-1]
    assert all(c['scope_assumption']['cost_basis']=='gross_bulk_loop_resource_v1' and c['scope_assumption']['includes_loop_control'] is True
        for c in model['selector']['calls'])
    assert all(p['value']>0 for p in model['parameters'].values())
    assert target['calibration_sources'][0]=='fixture.bulk.gross.resource'
    assert records.validate().returncode==0
