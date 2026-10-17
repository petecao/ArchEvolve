"""Native storage contracts, dated 2026-09-26 ET; no empirical campaign."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts import bfs_native_campaign as native

def test_native_guard_counts_wrapper_sibling(tmp_path,monkeypatch):
    raw=tmp_path/'raw'; source=tmp_path/'source'; build=tmp_path/'build'; records=tmp_path/'records'
    for p in (raw,source,build,records):p.mkdir()
    dispatch=Path(str(raw)+'.dispatch');dispatch.mkdir()
    guard=native.NativeSupervision.__new__(native.NativeSupervision)
    guard.args=SimpleNamespace(runs_dir=raw,source_runs_dir=source,build_root=build,records=records,id='candidate-run')
    guard.check_clock=lambda:None
    monkeypatch.setattr(native.os,'statvfs',lambda _:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    initial=guard.account()['artifact_bytes']
    monkeypatch.setitem(native.NATIVE_BOUNDS,'artifact_bytes',initial+32768)
    (dispatch/'outer.stdout').write_bytes(b'x'*65536)
    with pytest.raises(ValueError,match='artifact/build'):
        guard.account()


import copy
import json
from datetime import timedelta
from test_bfs_native_execution import supervised
from scripts.bfs_dx100_coverage_execution import artifact_bytes


def inputs_at(tmp_path):
    paths = [tmp_path/name for name in ('raw','source','build','records')]
    for path in paths: path.mkdir()
    dispatch=Path(str(paths[0])+'.dispatch');dispatch.mkdir()
    return {'id':'candidate-run','runs_dir':str(paths[0]),'source_runs_dir':str(paths[1]),
            'build_root':str(paths[2]),'records':str(paths[3])},dispatch


@pytest.mark.parametrize('fault',['missing','file','symlink','parent-symlink','relative','nested','duplicate'])
def test_exact_native_storage_roots_reject_redirects_and_overlap(tmp_path,fault):
    inputs,dispatch=inputs_at(tmp_path)
    if fault in ('missing','file','symlink'):
        dispatch.rmdir()
        if fault=='file':dispatch.write_text('not a directory')
        elif fault=='symlink':dispatch.symlink_to(Path(inputs['runs_dir']),target_is_directory=True)
    elif fault=='parent-symlink':
        alias=tmp_path/'alias';alias.symlink_to(tmp_path,target_is_directory=True)
        inputs['runs_dir']=str(alias/'raw')
    elif fault=='relative':inputs['runs_dir']='raw'
    elif fault=='duplicate':inputs['source_runs_dir']=inputs['build_root']
    else:
        nested=dispatch/'source';nested.mkdir();inputs['source_runs_dir']=str(nested)
    with pytest.raises(ValueError,match='storage'):
        native.native_storage_accounting(inputs)


def test_record_view_below_dispatch_is_counted_once_and_external_records_are_retained(tmp_path):
    inputs,dispatch=inputs_at(tmp_path)
    external=Path(inputs['records'])/'candidate-run.evaluation.yaml';external.write_bytes(b'x'*177)
    a=native.native_storage_accounting(inputs)
    assert a['artifact_bytes']==artifact_bytes([Path(p) for p in a['storage_paths']])+177
    view=dispatch/'records';view.mkdir();moved=view/external.name;external.rename(moved)
    inputs['records']=str(view)
    b=native.native_storage_accounting(inputs)
    assert b['new_record_paths']==[str(moved)] and b['separately_charged_record_paths']==[]
    assert b['artifact_bytes']==artifact_bytes([Path(p) for p in b['storage_paths']])


def test_actual_monitor_and_failed_finalization_charge_dispatch(supervised,monkeypatch):
    c=supervised
    prior=c.account()['artifact_bytes'];monkeypatch.setitem(native.NATIVE_BOUNDS,'artifact_bytes',prior+32768)
    dispatch=Path(str(c.args.runs_dir)+'.dispatch')
    (dispatch/'outer.stdout').write_bytes(b'x'*65536)
    with pytest.raises(ValueError,match='artifact/build'):c.guard.observe()
    c.driver.receipt['state']='evaluated'
    with pytest.raises(ValueError,match='artifact/build'):c.finalize()
    saved=json.loads((c.driver.folder/'driver.json').read_text())
    assert saved['state']=='failed'
    assert saved['storage_paths'][1]==str(dispatch)


@pytest.fixture
def closed(tmp_path):
    inputs,dispatch=inputs_at(tmp_path);begin=native.now()-timedelta(minutes=2)
    folder=Path(inputs['runs_dir'])/(inputs['id']+'.driver');folder.mkdir()
    approval={'format':'swdb.bfs.native-campaign-admission.v1','id':inputs['id'],
        'prepared_at':(begin-timedelta(seconds=1)).isoformat(),'inputs':inputs,
        'code_commit':'a'*40,'runtime':{'explicit_contract_fixture':True},'bounds':copy.deepcopy(native.NATIVE_BOUNDS)}
    admission=dispatch/'admission.json';admission.write_text(json.dumps(approval))
    driver={'format':'swdb.bfs.native-campaign-driver.v2','id':inputs['id'],'state':'evaluated',
        'runtime':approval['runtime'],'supervision_bounds':copy.deepcopy(native.NATIVE_BOUNDS),
        'supervision_admission':native.reference(admission),'outer_started':begin.isoformat(),
        'outer_deadline':(begin+timedelta(seconds=14400)).isoformat(),'started':begin.isoformat(),
        'finished':(begin+timedelta(seconds=20)).isoformat(),
        'storage_paths':native.native_storage_accounting(inputs)['storage_paths'],
        'final_accounting':native.native_storage_accounting(inputs)}
    audit={'id':inputs['id'],'state':'evaluated','repository_commit':'a'*40,'lease_released':True,
        'cleanup_state':'terminal_and_reaped','observed_at':(begin+timedelta(seconds=30)).isoformat()}
    def seal():
        admission.write_text(json.dumps(approval));driver['supervision_admission']=native.reference(admission)
        path=folder/'driver.json';path.write_text(json.dumps(driver));audit['driver']=native.reference(path)
        terminal=dispatch/'terminal-validation.json';terminal.write_text(json.dumps(audit))
        return native.reference(path),native.reference(terminal),native.reference(admission)
    return inputs,dispatch,approval,driver,audit,seal


def test_terminal_recounts_post_helper_and_post_audit_writes_under_same_cap(closed,monkeypatch):
    inputs,dispatch,approval,driver,audit,seal=closed
    monkeypatch.setitem(native.NATIVE_BOUNDS,'artifact_bytes',1024*1024)
    approval['bounds']=copy.deepcopy(native.NATIVE_BOUNDS);driver['supervision_bounds']=copy.deepcopy(native.NATIVE_BOUNDS)
    refs=seal()
    def read():return native.validate_storage_accounting(*refs[:2],admission_ref=refs[2],current=native.now().isoformat())
    result=read()
    assert result['artifact_bytes']>driver['final_accounting']['artifact_bytes']
    assert result['process_absence_verified'] is False and result['empirical_qualification'] is False
    (dispatch/'storage-readback.json').write_text(json.dumps(result))
    assert read()['artifact_bytes']>=result['artifact_bytes']
    (dispatch/'outer.stdout').write_bytes(b'x'*(1024*1024))
    with pytest.raises(ValueError,match='artifact/build'):read()


@pytest.mark.parametrize('fault',['root','bounds','driver-ref','admission-ref','audit-path','released','future','snapshot'])
def test_terminal_rejects_resealed_storage_and_reference_substitutions(closed,fault):
    inputs,dispatch,approval,driver,audit,seal=closed
    if fault=='root':driver['storage_paths'][1]=str(dispatch.parent)
    elif fault=='bounds':approval['bounds']['artifact_bytes']+=1
    elif fault=='released':audit['lease_released']=False
    elif fault=='future':audit['observed_at']=(native.now()+timedelta(minutes=1)).isoformat()
    elif fault=='snapshot':driver['final_accounting']['artifact_bytes']=16*1024**3
    refs=seal()
    if fault=='driver-ref':
        p=Path(refs[1]['path']);value=json.loads(p.read_text());value['driver']['sha256']='f'*64
        p.write_text(json.dumps(value));refs=(refs[0],native.reference(p),refs[2])
    elif fault in ('admission-ref','audit-path'):
        index=2 if fault=='admission-ref' else 1
        path=dispatch/'elsewhere.json';path.write_bytes(Path(refs[index]['path']).read_bytes())
        refs=tuple(native.reference(path) if i==index else ref for i,ref in enumerate(refs))
    with pytest.raises(ValueError):
        native.validate_storage_accounting(*refs[:2],admission_ref=refs[2],current=native.now().isoformat())


@pytest.mark.parametrize('fault',['outside','symlink'])
def test_unaccounted_admission_rejected_before_runtime_and_public_stages(supervised,monkeypatch,fault):
    c=supervised;dispatch=Path(str(c.args.runs_dir)+'.dispatch')
    outside=c.args.records/'admission.json';outside.write_text('{}')
    c.args.supervision_admission=outside
    if fault=='symlink':
        link=dispatch/'admission.json';link.symlink_to(outside);c.args.supervision_admission=link
    c.args.supervision_sha256=native.artifacts.file_hash(outside)
    monkeypatch.setattr(native,'campaign_runtime',lambda *_:pytest.fail('must reject before runtime or public calls'))
    try:
        with pytest.raises(ValueError,match='unexpected symlink' if fault=='symlink' else 'exact accounted dispatch'):c.admit()
        assert c.driver.receipt['stages']==[]
    finally:c.guard.stop(native.time.monotonic()+1)



def test_terminal_accepts_extra_reference_metadata_without_rebinding_identity(closed):
    inputs,dispatch,approval,driver,audit,seal=closed
    refs=seal();admission={**refs[2],'bytes':Path(refs[2]['path']).stat().st_size}
    result=native.validate_storage_accounting(*refs[:2],admission_ref=admission,current=native.now().isoformat())
    assert result['admission']==admission and result['process_absence_verified'] is False


def test_failed_driver_without_final_persistence_is_counted_without_success_promotion(closed):
    inputs,dispatch,approval,driver,audit,seal=closed
    driver.update(state='failed');audit['state']='failed'
    driver.pop('finished');driver.pop('final_accounting')
    refs=seal()
    result=native.validate_storage_accounting(*refs[:2],admission_ref=refs[2],current=native.now().isoformat())
    assert result['state']=='within_existing_storage_budget' and result['empirical_qualification'] is False
    assert result['driver_outcome']=='failed'
    assert json.loads(Path(refs[0]['path']).read_text())['state']=='failed'
