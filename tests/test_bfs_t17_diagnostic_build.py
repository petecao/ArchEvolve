"""One diagnostic compile contracts; no empirical build evidence. 2026-09-26 ET."""
import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace

import pytest
from scripts import bfs_t17_diagnostic_build as build
from swdb import artifacts, yamlio
from test_bfs_scalar_v2_builds import FixtureOwned, proof
from test_bfs_t17_build_only import execution_fixture


def test_exact_request_only_adds_diagnostic_treatment_and_fresh_id():
    request=build.load_request(); previous=json.loads(build.primary.REQUEST.read_text())
    assert request == {**previous,'id':build.RUN_ID,'diagnostic_regions':True}
    assert request['budget'] == {'total_seconds':240,'build_seconds':180,'memory_gib':16,'storage_gib':1}
    assert build.BOUNDS['outer_seconds']==600 and build.BOUNDS['work_seconds']==570
    assert build.BOUNDS['artifact_bytes']==2*1024**3 and build.BOUNDS['build_bytes']==1024**3


@pytest.mark.parametrize('duration,startup',[(601,0),(600,-1),(600,31)])
def test_original_outer_clock_rejects_extension_or_late_entry(duration,startup):
    start=build.now()-timedelta(seconds=startup)
    with pytest.raises(ValueError,match='original 600'):
        build.Clock(start.isoformat(),(start+timedelta(seconds=duration)).isoformat())


@pytest.fixture
def worker(tmp_path,monkeypatch):
    raw=tmp_path/'raw'; dispatch=Path(str(raw)+'.dispatch'); dispatch.mkdir()
    records=dispatch/'record-view/records'; records.mkdir(parents=True)
    builds=tmp_path/'builds'; builds.mkdir()
    for key,value in [('RAW',raw),('DISPATCH',dispatch),('RECORDS',records),('BUILDS',builds)]:
        monkeypatch.setattr(build,key,value)
    monkeypatch.setattr(build.os,'statvfs',lambda _:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    monkeypatch.setattr(build.own,'identity',lambda pid:{'pid':pid,'start_ticks':1,'parent_pid':os.getpid()})
    monkeypatch.setattr(build.own,'ancestry',lambda ident,pane:[ident,pane])
    monkeypatch.setattr(build.own,'Owned',FixtureOwned)
    begin=build.now(); clock=build.Clock(begin.isoformat(),(begin+timedelta(seconds=600)).isoformat())
    args=SimpleNamespace(pane_pid=999,pane_start_ticks=1,lane=1,expected_commit='a'*40)
    result=build.Driver(args,clock)
    result.guard=build.own.Monitor(result.observe,interrupt=False); result.guard.start()
    yield result
    if result.guard.thread.is_alive():result.guard.stop(time.monotonic()+1)


def test_actual_public_get_uses_counted_db_and_record_view(worker):
    source=build.ROOT/'records/machines/mbit10.yaml'
    dest=build.RECORDS/'machines/mbit10.yaml'; dest.parent.mkdir(); shutil.copyfile(source,dest)
    before=worker.account()['artifact_bytes']
    result=worker.call(['get','mbit10'])
    assert result['id']=='mbit10' and (build.RAW/'swdb.sqlite').is_file()
    row=worker.receipt['stages'][0]
    assert row['command'][-6:]==['--records',str(build.RECORDS),'--db',str(build.RAW/'swdb.sqlite'),'--format','json']
    assert row['returncode']==0 and row['cleanup']['direct_reaped']
    assert worker.account()['artifact_bytes']>before


@pytest.mark.parametrize('mode',['fail','slow'])
def test_real_public_failure_stops_and_reaps_once(worker,tmp_path,monkeypatch,mode):
    # Only disposable public-child behavior is replaced. Real Popen, shared ledger,
    # run_stage, receipt persistence, and direct-child reaping are exercised.
    root=tmp_path/'public'; root.mkdir(); package=root/'swdb'; package.mkdir()
    (package/'__init__.py').write_text('')
    (package/'__main__.py').write_text('import time;time.sleep(.2);raise SystemExit(7)' if mode=='slow' else 'raise SystemExit(7)')
    monkeypatch.setattr(build,'ROOT',root)
    if mode=='slow':worker.clock.work=time.monotonic()+.02
    with pytest.raises((ValueError,subprocess.TimeoutExpired)):
        worker.call(['get','fixture'])
    row=worker.receipt['stages'][0]
    assert len(worker.receipt['stages'])==1 and row['returncode'] is not None
    assert row['cleanup']['direct_reaped'] and not worker.budget.snapshot()['reservations']


@pytest.mark.parametrize('location',['raw','dispatch','build','view','db-sidecar'])
def test_all_new_retained_locations_share_the_cap(worker,monkeypatch,location):
    monkeypatch.setitem(build.BOUNDS,'artifact_bytes',worker.account()['artifact_bytes']+16384)
    path={'raw':build.RAW/'log','dispatch':build.DISPATCH/'outer.stdout',
          'build':worker.temporary/'object','view':build.RECORDS/'extra.yaml',
          'db-sidecar':build.RAW/'swdb.sqlite-wal'}[location]
    path.write_bytes(b'x'*32768)
    with pytest.raises(ValueError,match='artifact/build'):worker.account()


def test_build_subset_and_original_work_boundary_are_independent(worker,monkeypatch):
    monkeypatch.setitem(build.BOUNDS,'build_bytes',16384)
    (worker.temporary/'object').write_bytes(b'x'*32768)
    with pytest.raises(ValueError,match='artifact/build'):worker.account()
    worker.clock.work=time.monotonic()-1
    with pytest.raises(ValueError,match='deadline'):worker.call(['get','never-spawn'])
    assert worker.receipt['stages']==[]


@pytest.mark.parametrize('failed',[False,True])
def test_reused_finalizer_retains_original_failure_and_one_cleanup_budget(worker,failed):
    original=ValueError('original diagnostic compile failed') if failed else None
    if not failed:worker.receipt['state']='complete'
    if failed:
        with pytest.raises(ValueError) as caught:worker.finalize(original)
        assert caught.value is original
    else:worker.finalize(None)
    value=json.loads((worker.folder/'driver.json').read_text())
    assert value['state']==('failed' if failed else 'complete')
    assert value['resource_validation']['samples']>=2 and value['cleanup_verified'] is False
    assert not worker.guard.thread.is_alive() and worker.budget.snapshot()['spent_seconds']<=30
    assert not worker.budget.snapshot()['reservations']


def test_record_view_reopens_full_manifest_and_allows_only_empty_writer_lock(worker):
    (build.RECORDS/'fixture.yaml').write_text('kind: machine\nid: fixture\n')
    value={'format':'swdb.bfs.record-view.v1','records':str(build.RECORDS),
           'git_provenance':[{'commit':'a'*40}], 'files':build.record_inventory()}
    path=build.DISPATCH/'record-view-manifest.json'; path.write_text(json.dumps(value))
    ref=build.reference(path)
    assert build.validate_record_view(ref)==value
    (build.RECORDS/'.swdb.lock').touch()
    assert build.validate_record_view(ref)==value
    (build.RECORDS/'fixture.yaml').write_text('kind: machine\nid: changed\n')
    with pytest.raises(ValueError,match='materialization'):build.validate_record_view(ref)


@pytest.fixture
def bound_results(execution_fixture,worker,monkeypatch):
    _,pins,values,old,_,records=execution_fixture
    pins['candidate']['artifact_sha256']=values['candidate']['artifact']['sha256']
    previous=copy.deepcopy(old)
    previous['context']={'candidate_sha256':pins['candidate']['artifact_sha256'],
                         'graph_verification':{'contract':'swdb.bfs.original-adjacency.v1'}}
    previous['build']['m5ops']=previous['build']['driver']
    records[build.PRIMARY_ID]=previous
    p=build.RECORDS/build.canonical_path('evaluation',build.PRIMARY_ID);p.parent.mkdir()
    p.write_text(json.dumps(previous))
    monkeypatch.setattr(build,'PRIMARY_RECORD_SHA',artifacts.file_hash(p))
    monkeypatch.setattr(build,'PRIMARY_BINARY_SHA',previous['build']['binary_sha256'])
    out=build.BUILDS/build.RUN_ID;out.mkdir(); binary=out/'bfs';binary.write_bytes(b'fixture diagnostic binary')
    result=copy.deepcopy(previous);result.update(id=build.RUN_ID,request=build.load_request())
    result['build'].update(binary=str(binary),binary_sha256=artifacts.file_hash(binary),
        compiler=pins['compiler']['path'],flags=['-DMAA'],source_artifact=values['candidate']['artifact'])
    result['context'].update(function='DOBFS',roi='bfs.complete_call.v1',accelerated_requested=True,
        diagnostic={'roi':'bfs.complete_call.v1'},verifier_source={'symbol':'swdb_original::Graph::verify'})
    records[build.RUN_ID]=result
    store=SimpleNamespace(get=lambda rid,kind=None:records.get(rid))
    monkeypatch.setattr(build,'Store',lambda _:store)
    calls=[]
    def call(command,compile=False):
        calls.append((command,compile))
        if command[0]=='dx100-compile':return copy.deepcopy(result)
        if '--chain' in command:return {'root':build.RUN_ID,'records':copy.deepcopy(records)}
        return copy.deepcopy(records[command[1]])
    monkeypatch.setattr(worker,'call',call)
    return worker,pins,values,previous,result,store,calls


def test_one_compile_with_real_origin_primary_and_diagnostic_validators(bound_results):
    worker,pins,values,previous,result,store,calls=bound_results
    worker.collect(pins,build.load_request())
    assert sum(command[0]=='dx100-compile' for command,_ in calls)==1
    assert len(calls)==10 and all(command[0] in ('get','dx100-compile') for command,_ in calls)
    assert worker.receipt['provider_budget_unchanged']
    assert values['proposal']['repair_budget']['used_seconds']==233.21830715797842
    assert worker.receipt['build']['binary_sha256'] != worker.receipt['primary_binary_sha256']


@pytest.mark.parametrize('admission_fault',[None,'outside','file-symlink','parent-symlink'])
def test_full_admitted_collection_reopens_view_proof_and_primary(bound_results,proof,tmp_path,monkeypatch,admission_fault):
    """Fixture host admission, actual proof/view readers and complete driver flow."""
    worker,pins,values,previous,result,store,calls=bound_results
    worker.guard.stop(time.monotonic()+1)
    _,_,runtime,seal=proof
    monkeypatch.setattr(build,'campaign_runtime',lambda _:copy.deepcopy(runtime))
    driver=tmp_path/'prior-driver.json';driver.write_text('{}')
    audit=tmp_path/'prior-terminal.json';audit.write_text(json.dumps({
        'driver':build.reference(driver),'owned_processes':[{'pid':99999999,'start_ticks':1,'state':'absent'}]}))
    observation=tmp_path/'prior-observation.json';observation.write_text(json.dumps({
        'terminal':build.reference(audit),'driver':build.reference(driver),
        'evaluation':{'sha256':build.PRIMARY_RECORD_SHA}}))
    monkeypatch.setattr(build,'PRIMARY_TERMINAL_SHA',artifacts.file_hash(audit))
    monkeypatch.setattr(build,'PRIMARY_OBSERVATION',observation)
    monkeypatch.setattr(build,'PRIMARY_OBSERVATION_SHA',artifacts.file_hash(observation))
    origin=tmp_path/'origin-pins.json';origin.write_text(json.dumps(pins))
    monkeypatch.setattr(build.primary,'OBSERVATION',origin)
    monkeypatch.setattr(build.primary,'OBSERVATION_SHA',artifacts.file_hash(origin))
    catalog={row['id']:row for row in values.values()};catalog[build.PRIMARY_ID]=previous
    monkeypatch.setattr(build,'Store',lambda _:SimpleNamespace(get=lambda rid,kind=None:catalog.get(rid)))
    prior_call=worker.call
    def call(command,compile=False):
        if compile:
            catalog[build.RUN_ID]=result
            (build.RECORDS/build.canonical_path('evaluation',build.RUN_ID)).write_text(json.dumps(result))
        return prior_call(command,compile=compile)
    monkeypatch.setattr(worker,'call',call)
    manifest=build.DISPATCH/'record-view-manifest.json'
    manifest.write_text(json.dumps({'format':'swdb.bfs.record-view.v1','records':str(build.RECORDS),
        'files':build.record_inventory(),'git_provenance':[{'commit':'a'*40}]}))
    admission=build.DISPATCH/'admission.json'
    admission.write_text(json.dumps({'format':'swdb.bfs.t17-diagnostic-build-admission.v1','id':build.RUN_ID,
        'request_sha256':build.REQUEST_SHA,'code_commit':'a'*40,'node':1,
        'prepared_at':worker.clock.begin.isoformat(),'runtime':runtime,
        'record_view':build.reference(manifest),'linux_proof':seal()}))
    worker.args.admission=admission;worker.args.admission_sha256=artifacts.file_hash(admission)
    monkeypatch.setattr(build,'lease_observation',lambda *args:{'fixture_only':True})
    monkeypatch.setattr(build,'capacity',lambda *args:{'estimated_available_kib':100*1024**2,'global_available_kib':100*1024**2})
    read=Path.read_text
    def kernel(path,*args,**kwargs):
        if str(path) in ('/sys/devices/system/node/node1/meminfo','/proc/zoneinfo','/proc/meminfo'):
            return 'explicit kernel contract fixture'
        return read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',kernel)
    if admission_fault:
        outside=tmp_path/'outside-admission.json';outside.write_bytes(admission.read_bytes())
        if admission_fault=='outside':worker.args.admission=outside
        elif admission_fault=='file-symlink':
            admission.unlink();admission.symlink_to(outside)
        else:
            alias=tmp_path/'dispatch-alias';alias.symlink_to(build.DISPATCH,target_is_directory=True)
            worker.args.admission=alias/'admission.json'
        with pytest.raises(ValueError,match='exact canonical accounted dispatch'):
            worker.execute()
        assert calls==[] and 'admission' not in worker.receipt
        return
    worker.execute();worker.finalize(None)
    saved=json.loads((worker.folder/'driver.json').read_text())
    assert saved['state']=='complete' and saved['provider_budget_unchanged']
    assert saved['linux_ownership_proof']['actual_proof_commit']=='b'*40
    assert saved['linux_ownership_proof']['driver_commit']=='a'*40
    assert len(calls)==10 and saved['final_accounting']['artifact_bytes']>0


@pytest.mark.parametrize('fault',['primary-bytes','provider-budget','diagnostic-missing','oracle','candidate','timing'])
def test_actual_binding_failures_cannot_be_relabelled_as_diagnostic_success(bound_results,fault):
    worker,pins,values,previous,result,store,calls=bound_results
    if fault=='primary-bytes':Path(previous['build']['binary']).write_bytes(b'changed primary')
    elif fault=='provider-budget':values['proposal']['repair_budget']['used_seconds']=0
    elif fault=='diagnostic-missing':result['context'].pop('diagnostic')
    elif fault=='oracle':result['context']['graph_verification']['contract']='old oracle'
    elif fault=='candidate':result['context']['candidate_sha256']='0'*64
    else:result['timing']=[{'duration_s':1}]
    with pytest.raises(ValueError):worker.collect(pins,build.load_request())
    assert 'evaluation_sha256' not in worker.receipt
    if fault in ('primary-bytes','provider-budget'):
        assert not any(command[0]=='dx100-compile' for command,_ in calls)
