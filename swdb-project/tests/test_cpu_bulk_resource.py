"""Distinct gross bulk-loop recipe; failed driver resolution is retained.2026-10-06 ET."""
import json
import pytest
import subprocess
import sys
from conftest import run_swdb
from testkit.cpu_bulk import native_bulk_receipt
from testkit.cpu_service import save_receipt


def test_gross_bulk_resource_retains_short_driver_and_never_promotes_paired_rate(records,tmp_path):
    records.add_stub();raw=native_bulk_receipt();raw.update(evidence_kind='fixture',machine='testhost')
    raw['settings']['group']='bulk_total_v2'
    for cell in raw['services']:
        cell['scope']['residual_policy']={'id':'both_windows_meet_declared_threshold','minimum_window_s':.05}
        for trial in cell['trials']:trial['driver_seconds']=.00001
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.bulk.total.source','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    source=json.loads(imported.stdout)
    assert all(c['parameter']['value'] is None and 'paired_driver_window_resolution' in c['missing'] for c in source['services'])
    path=records.path/'cpu_service_calibrations/fixture.bulk.total.source.yaml';before=path.read_bytes()
    result=subprocess.run([sys.executable,'-m','swdb.cpu_bulk_resource','--records',str(records.path),
        '--source-calibration',source['id'],'--id','fixture.bulk.resource','--fixture','--format','json'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    assert data['recipe']['id']=='gross_bulk_loop_resource_v1' and data['recipe']['includes_loop_control'] is True
    assert data['calibration_sources']==[source['id']]
    assert all(c['parameter']['basis']=='reported' and c['parameter']['value']==pytest.approx(.0000001) for c in data['services'])
    assert all(c['paired_residual']['parameter']['value'] is None for c in data['services'])
    assert path.read_bytes()==before and records.validate().returncode==0


def test_native_gross_recipe_admits_short_driver_but_retains_null_subtraction(records,tmp_path):
    import copy
    records.copy_repo('machines')
    raw=native_bulk_receipt();raw['settings']['group']='bulk_total_v2'
    raw['context']['collection_recipe']='gross_loop_window_with_retained_driver_v2'
    for cell in raw['services']:
        cell['scope']['residual_policy']={'id':'both_windows_meet_declared_threshold','minimum_window_s':.05}
        for t in cell['trials']:t['driver_seconds']=.00001
    def ingest(data,key):
        return run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,data),
            '--id',key,'--format','json')
    accepted=ingest(raw,'synthetic.bulk.total.native')
    assert accepted.returncode==0,accepted.stderr+accepted.stdout
    assert all(s['parameter']['value'] is None for s in json.loads(accepted.stdout)['services'])
    assert records.validate().returncode==0
    for i,mutation in enumerate(('short_gross','missing_policy','bad_copy')):
        bad=copy.deepcopy(raw)
        if mutation=='short_gross':bad['services'][0]['trials'][0]['gross_seconds']=.001
        elif mutation=='missing_policy':del bad['services'][0]['scope']['residual_policy']
        else:bad['services'][0]['trials'][0]['checked_one_copy']=False
        assert ingest(bad,'synthetic.bulk.total.invalid.'+str(i)).returncode!=0
    # The older recipe still requires both windows; changing the new classification is insufficient.
    legacy=copy.deepcopy(raw);legacy['settings']['group']='bulk_v1'
    assert ingest(legacy,'synthetic.bulk.total.legacy.refused').returncode!=0


def test_large_exact_bulk_gross_pilot_finishes_with_short_driver_retained(records,tmp_path):
    result=subprocess.run([sys.executable,'-m','swdb.cpu_bulk_total_calibration','--records',str(records.path),
        '--output',str(tmp_path/'gross'),'--fixture','--machine','testhost','--size','1048576',
        '--repetitions','3','--min-trial-s','.002','--max-wall-s','60'],capture_output=True,text=True,timeout=75)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((tmp_path/'gross/receipt.json').read_text())
    assert raw['settings']['group']=='bulk_total_v2' and len(raw['services'])==4
    moves=raw['services'][1:]
    assert all(min(t['gross_seconds'] for t in s['trials'])>=.002 for s in moves)
    assert any(t['driver_seconds']<.002 for s in moves for t in s['trials'])
    records.add_stub()
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',tmp_path/'gross/receipt.json',
        '--id','fixture.bulk.total.runner','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    assert all(s['parameter']['value'] is None and 'paired_driver_window_resolution' in s['missing']
        for s in json.loads(imported.stdout)['services'][1:])
