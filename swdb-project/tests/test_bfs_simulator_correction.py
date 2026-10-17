"""Retained failed-attempt costs; synthetic local files only. Dated 2026-09-26 ET."""
import copy
from datetime import datetime
import json
from pathlib import Path

import pytest

from scripts import bfs_simulator_batch as batch
from swdb import artifacts
from test_bfs_simulator_batch import plan, admission
from test_bfs_simulator_batch_admission import terminal_files


@pytest.fixture
def failed(tmp_path, monkeypatch, terminal_files):
    fixture = terminal_files
    policy = plan()
    runs = tmp_path/policy['id']; runs.mkdir()
    dispatch = Path(str(runs)+'.dispatch'); dispatch.mkdir()
    folder = runs/(runs.name+'.driver'); folder.mkdir()
    ledger_path = folder/'cleanup-ledger.json'
    driver = fixture.driver
    driver.update(id=policy['id'], state='failed', plan=policy, plan_sha256=artifacts.digest(policy),
                  preparation_charges=[], storage_paths=list(map(str,(runs,dispatch))),
                  final_ledger={'raw_bytes':0,'charged_raw_bytes':0})
    driver['cleanup_budget']['path'] = driver['cleanup']['shared_budget'] = str(ledger_path)
    monkeypatch.setattr(batch, 'RAW_ROOTS', (tmp_path,))
    monkeypatch.setattr(batch, 'now', lambda: datetime(2026,9,26,10,2,tzinfo=batch.ET))
    lane = {'socket_lane':{'exit_code':1,'job':policy['id'],'host':'mbit10','lease_generation':411,'started_utc':'2026-09-26T14:00:00Z',
                           'ended_utc':'2026-09-26T14:00:10Z'}}
    audit = {'id':policy['id'],'state':'failed','lease_released':True,
             'cleanup_state':'terminal_and_reaped','lease_generation':411,'observed_at':'2026-09-26T10:01:00-04:00'}
    def ref(path,value):
        path.write_text(json.dumps(value))
        return {'path':str(path),'sha256':artifacts.file_hash(path)}
    def seal():
        driver_ref = ref(folder/'driver.json',driver)
        audit['driver']=driver_ref
        lane_ref=ref(dispatch/'lane.json',lane)
        audit['lane']=lane_ref
        entry = {'id':policy['id'],'driver':driver_ref,
                 'cleanup_ledger':ref(ledger_path,fixture.ledger),
                 'terminal':ref(dispatch/'terminal-validation.json',audit),
                 'lane':lane_ref,'closed_at':'2026-09-26T10:01:00.5-04:00','storage_paths':list(map(str,(runs,dispatch)))}
        entry['retained_bytes']=batch.allocated_bytes([runs,dispatch])
        return entry
    return driver, fixture.ledger, lane, audit, runs, dispatch, seal


def test_correction_charges_all_failed_output_and_original_outer_clock(failed):
    driver, ledger, lane, audit, runs, dispatch, seal = failed
    (runs/'failed-debug.log').write_bytes(b'x'*32000)
    entry = seal()
    value = plan(); value['accounting']['retained_failed_batches']=[entry]
    rows = batch.preparation_charges(value)
    assert rows == [{'id':entry['id'],'elapsed_seconds':61,'raw_bytes':batch.allocated_bytes([runs,dispatch])}]
    begin=batch.now(); approved=admission(value,started=begin,charges=rows)
    account=batch.Ledger(value,approved,batch.time.monotonic(),begin)
    assert account.charged_seconds==61 and account.charged_bytes>=32000
    assert account.next_allowance(0)==(21600,39)
    assert driver['state']=='failed'


@pytest.mark.parametrize('fault',['success','zero-exit','bool-exit','wrong-id','live-audit',
    'wrong-audit','unsettled','changed-driver','changed-lane','grew','omitted-root',
    'bad-clock','nested-correction','duplicate-charge','other-lane','early-closure'])
def test_correction_cannot_hide_failed_cost_or_incomplete_closure(failed,fault):
    driver, ledger, lane, audit, runs, dispatch, seal=failed
    if fault=='success': driver['state']='complete'
    elif fault=='zero-exit': lane['socket_lane']['exit_code']=0
    elif fault=='bool-exit': lane['socket_lane']['exit_code']=True
    elif fault=='live-audit': audit['lease_released']=False
    elif fault=='wrong-audit': audit['id']='other'
    elif fault=='unsettled': ledger['reservations']={'unsettled':{}}
    elif fault=='bad-clock': lane['socket_lane']['ended_utc']='2026-09-26T14:00:01Z'
    elif fault=='nested-correction': driver['plan']['accounting']['retained_failed_batches']=[{}]
    entry=seal()
    if fault=='wrong-id': entry['id']='other'
    elif fault=='changed-driver': Path(entry['driver']['path']).write_text('{}')
    elif fault=='changed-lane': Path(entry['lane']['path']).write_text('{}')
    elif fault=='grew': (dispatch/'late.log').write_bytes(b'x'*32000)
    elif fault=='omitted-root': entry['storage_paths']=[str(runs)]
    elif fault=='early-closure': entry['closed_at']=driver['finished']
    elif fault=='other-lane':
        path=dispatch/'unrelated-lane.json';path.write_text(json.dumps(lane))
        entry['lane']={'path':str(path),'sha256':artifacts.file_hash(path)}
    value=plan();value['accounting']['retained_failed_batches']=[entry]
    if fault=='duplicate-charge': value['accounting']['retained_failed_batches'].append(copy.deepcopy(entry))
    with pytest.raises(ValueError): batch.preparation_charges(value)


def test_transport_is_opt_in_for_both_public_series_requests(tmp_path):
    value=plan(); row=value['series'][0]; approved=admission(value)
    args=(value,row,approved,tmp_path/'config',tmp_path/'raw',tmp_path/'records',1,21600,39)
    assert '--trace-transport' not in batch.series_command(*args)
    value['trace_transport']='gem5-gzip.v1'
    command=batch.series_command(*args)
    assert command[command.index('--trace-transport')+1]=='gem5-gzip.v1'
    assert '--accelerated' in command and '--protocol' not in command
    value['trace_transport']='drop-events'
    with pytest.raises(ValueError,match='unsupported'):batch.series_command(*args)


@pytest.fixture
def closed_preparation(tmp_path):
    runs=tmp_path/'smoke'; runs.mkdir()
    dispatch=Path(str(runs)+'.dispatch'); dispatch.mkdir()
    def ref(path,value):
        path.write_text(json.dumps(value))
        return {'path':str(path),'sha256':artifacts.file_hash(path)}
    entry={'id':'smoke','driver':ref(runs/'driver.json',{'id':'smoke','state':'complete',
        'started':'2026-09-26T10:00:01-04:00','finished':'2026-09-26T10:00:04-04:00',
        'stages':[{'host_wall_s':2.5}]}),
        'lane':ref(dispatch/'lane.json',{'socket_lane':{'exit_code':0,
            'started_utc':'2026-09-26T14:00:01Z','ended_utc':'2026-09-26T14:00:04Z'}}),
        'storage_paths':[str(runs),str(dispatch)]}
    preflight=ref(dispatch/'preflight.json',{'observed_at':'2026-09-26T10:00:00.4-04:00'})
    audit={'id':'smoke','state':'complete','driver':entry['driver'],'lane':entry['lane'],
        'lease_released':True,'cleanup_state':'terminal_and_reaped','observed_at':'2026-09-26T10:01:00-04:00'}
    def seal():
        entry['closed_envelope']={'preflight':preflight,'terminal':ref(dispatch/'terminal-validation.json',audit),
            'started':'2026-09-26T10:00:00.4-04:00','finished':'2026-09-26T10:01:10.5-04:00',
            'retained_bytes':batch.allocated_bytes([runs,dispatch])}
        return {'accounting':{'preparation':[entry]}}
    return entry,audit,dispatch,seal


def test_preparation_charges_full_preflight_to_final_readback_including_idle(closed_preparation):
    entry,audit,dispatch,seal=closed_preparation
    rows=batch.preparation_charges(seal())
    assert rows==[{'id':'smoke','elapsed_seconds':71,'raw_bytes':entry['closed_envelope']['retained_bytes']}]


@pytest.mark.parametrize('fault',['wrong-driver','wrong-lane','live','wrong-start','early-end','changed-output'])
def test_preparation_envelope_reopens_and_binds_actual_artifacts(closed_preparation,fault):
    entry,audit,dispatch,seal=closed_preparation
    if fault=='wrong-driver': audit['driver']={'path':'/wrong','sha256':'f'*64}
    elif fault=='wrong-lane': audit['lane']={'path':'/wrong','sha256':'f'*64}
    elif fault=='live': audit['lease_released']=False
    value=seal()
    if fault=='wrong-start': entry['closed_envelope']['started']='2026-09-26T10:00:00.5-04:00'
    elif fault=='early-end': entry['closed_envelope']['finished']='2026-09-26T10:00:30-04:00'
    elif fault=='changed-output': (dispatch/'late-write').write_bytes(b'x'*32000)
    with pytest.raises(ValueError): batch.preparation_charges(value)


@pytest.fixture
def reserved(tmp_path):
    value=plan();group=tmp_path/'proof-preparation.dispatch';group.mkdir()
    fixed={'id':'proof-preparation','elapsed_seconds':600,'raw_bytes':2*batch.GIB,
           'selections':{'owned_cleanup':'owned','dx100_interruption':'interruption'},'storage_paths':[]}
    approved=admission(value);approved['code_commit']='f'*40;approved['linux_cleanup_tests']=[];audits={};readbacks={}
    def ref(path,value):
        path.write_text(json.dumps(value));return {'path':str(path),'sha256':artifacts.file_hash(path)}
    for kind,rid in fixed['selections'].items():
        raw=tmp_path/rid;raw.mkdir();dispatch=tmp_path/(rid+'.dispatch');dispatch.mkdir()
        fixed['storage_paths'].extend(map(str,(raw,dispatch)))
        driver={'path':str(raw/'driver.json'),'sha256':'a'*64}
        audit=ref(raw/'terminal-audit.json',{'id':rid,'state':'passed','code_commit':'f'*40,
            'driver':driver,'lease_released':True,'cleanup_state':'terminal_and_reaped',
            'observed_at':'2026-09-26T10:00:30-04:00'})
        proof={'kind':kind,'terminal_audit':audit,'driver':driver,'independent_cleanup_verified':True,
               'started':'2026-09-26T10:00:01-04:00','finished':'2026-09-26T10:00:10-04:00'}
        proof_ref=ref(raw/'proof.json',proof)
        approved['linux_cleanup_tests'].append(proof_ref)
        audits[kind]=ref(dispatch/'audit-receipt.json',{'state':'complete','returncode':0,
            'outer_seconds':60,'host_wall_s':20,'audit_started':'2026-09-26T10:00:11-04:00',
            'audit_finished':'2026-09-26T10:00:31-04:00','proof':proof_ref,'terminal_audit':audit})
        readbacks[kind]=ref(group/(kind+'.readback.json'),{'id':rid,'audit_receipt':audits[kind],
            'proof':proof_ref,'terminal_audit':audit,'wrapper_returncode':0,
            'wrapper_exit':ref(group/(kind+'.audit-wrapper.exit'),0),'finished':'2026-09-26T10:00:32-04:00'})
    fixed['storage_paths'].append(str(group))
    preflight=ref(group/'preflight.json',{'id':fixed['id'],'code_commit':'f'*40,
        'observed_at':'2026-09-26T10:00:00-04:00'})
    approved['preparation_reservation']={'preflight':preflight,'audits':audits,'auditor_readbacks':readbacks,'finished':'2026-09-26T10:01:00-04:00',
                                        'raw_bytes':batch.allocated_bytes(fixed['storage_paths'])}
    value['accounting']['preparation_reservation']=fixed
    return value,approved


def test_future_proof_reservation_is_charged_in_full_without_refund(reserved):
    value,approved=reserved
    batch.validate_preparation_reservation(value,approved)
    assert batch.preparation_charges(value)==[{'id':'proof-preparation','elapsed_seconds':600,'raw_bytes':2*batch.GIB}]
    assert approved['preparation_reservation']['raw_bytes']<2*batch.GIB


@pytest.mark.parametrize('fault',['elapsed','changed-output','understated','early-end','wrong-commit',
    'missing-proof','duplicate-proof','extra-root','symlink-root','unplanned'])
def test_proof_reservation_cannot_admit_missing_excess_or_substituted_work(reserved,fault,tmp_path):
    value,approved=reserved;fixed=value['accounting']['preparation_reservation'];actual=approved['preparation_reservation']
    if fault=='elapsed':actual['finished']='2026-09-26T10:10:01-04:00'
    elif fault=='changed-output':Path(fixed['storage_paths'][0],'late').write_bytes(b'x'*32000)
    elif fault=='understated':actual['raw_bytes']-=1
    elif fault=='early-end':actual['finished']='2026-09-26T10:00:20-04:00'
    elif fault=='wrong-commit':approved['code_commit']='e'*40
    elif fault=='missing-proof':approved['linux_cleanup_tests'].pop()
    elif fault=='duplicate-proof':approved['linux_cleanup_tests'][1]=approved['linux_cleanup_tests'][0]
    elif fault=='extra-root':fixed['storage_paths'].append(str(tmp_path))
    elif fault=='symlink-root':
        path=tmp_path/'alias';path.symlink_to(fixed['storage_paths'][0]);fixed['storage_paths'][0]=str(path)
    else:value['accounting'].pop('preparation_reservation')
    with pytest.raises(ValueError):batch.validate_preparation_reservation(value,approved)


@pytest.mark.parametrize('fault',['nonzero','late','wrong-proof','bool-exit','overspent'])
def test_reservation_includes_actual_auditor_postpublication_exit(reserved,fault):
    value,approved=reserved
    ref=approved['preparation_reservation']['audits']['owned_cleanup']
    path=Path(ref['path']); completion=json.loads(path.read_text())
    if fault=='nonzero':completion['returncode']=1
    elif fault=='late':completion['audit_finished']='2026-09-26T10:11:00-04:00'
    elif fault=='wrong-proof':completion['proof']['sha256']='0'*64
    elif fault=='bool-exit':completion['returncode']=False
    else:completion['host_wall_s']=61
    path.write_text(json.dumps(completion));ref['sha256']=artifacts.file_hash(path)
    with pytest.raises(ValueError,match='external audit'):batch.validate_preparation_reservation(value,approved)


@pytest.mark.parametrize('fault',['wrapper-exit','post-hash-late','wrong-audit','actual-exit'])
def test_reservation_checks_wrapper_exit_and_post_hash_readback(reserved,fault):
    value,approved=reserved
    ref=approved['preparation_reservation']['auditor_readbacks']['owned_cleanup']
    path=Path(ref['path']); record=json.loads(path.read_text())
    if fault=='wrapper-exit':record['wrapper_returncode']=1
    elif fault=='post-hash-late':record['finished']='2026-09-26T10:11:00-04:00'
    elif fault=='actual-exit':
        exit_path=Path(record['wrapper_exit']['path']);exit_path.write_text('1\n')
        record['wrapper_exit']['sha256']=artifacts.file_hash(exit_path)
    else:record['audit_receipt']['sha256']='0'*64
    path.write_text(json.dumps(record));ref['sha256']=artifacts.file_hash(path)
    with pytest.raises(ValueError,match='wrapper or final hash'):batch.validate_preparation_reservation(value,approved)


def test_corrective_plan_retains_original_science_and_budgets():
    previous=plan('t15');corrected=plan('t15-correction')
    batch.validate_plan(previous,'t15');batch.validate_plan(corrected,'t15-correction')
    for key in ('model_build','target','verifier','roi','threads','repetitions','warmups',
                'verification_ticks','profitability','bounds','record_sha256','protocol_requests'):
        assert corrected[key]==previous[key]
    for old,new in zip(previous['series'],corrected['series'],strict=True):
        assert old['id']!=new['id']
        assert {k:v for k,v in old.items() if k!='id'}=={k:v for k,v in new.items() if k!='id'}
    assert corrected['automatic_retry_allowed'] is False
    corrected['bounds']['batch_seconds']+=1
    with pytest.raises(ValueError,match='fixed scope'):batch.validate_plan(corrected,'t15-correction')


@pytest.mark.parametrize('fault',['receipt','primary','diagnostic'])
def test_planned_transport_must_reach_each_actual_execution(monkeypatch,fault):
    from test_bfs_simulator_batch import complete_child,fixture_package
    value=plan();value['trace_transport']='gem5-gzip.v1';row=value['series'][0];approved=admission(value)
    child=complete_child(value,row,approved,39);child['trace_transport']='gem5-gzip.v1'
    class Store:
        def get(self,rid,kind):
            transport=None if (fault=='primary' and '.primary.' in rid) or (fault=='diagnostic' and '.diagnostic.' in rid) else 'gem5-gzip.v1'
            return {'context':{'trace_transport':transport},'request':{'verification':{'trace_transport':transport}}}
    def package(store,pid,requested,*args):
        pos=int(requested[len(row['id'])+2:].split('.')[0]);return fixture_package(value,row,row['sources'][pos])
    monkeypatch.setattr(batch,'package_binding',package)
    if fault=='receipt':child.pop('trace_transport')
    with pytest.raises(ValueError,match='trace transport'):batch.validate_series_result(value,row,approved,child,21600,39,Store())
