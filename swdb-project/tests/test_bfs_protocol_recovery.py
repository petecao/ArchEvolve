"""Prospective T16 protocol continuation contracts. Updated 2026-09-27 ET."""
import copy
import json
from datetime import timedelta

import pytest
from scripts import bfs_simulator_batch as batch, bfs_simulator_recovery as recovery
from swdb import artifacts, yamlio


HISTORICAL_RUNTIME = {  # the a1 continuation's reviewed verifier runtime (2026-09-27)
    'scripts/dx100_verify.py': '476874619644d1256dcc5ca1e853c47b7be2e1dc56f538aaa2dd783842e7ad10',
    'swdb/dx100_witness.py': 'c9d3e14b70a3689799314556fab2922b1723c00960902109af2922a958cd3498'}


@pytest.fixture(autouse=True)
def historical_runtime(monkeypatch):
    """The closed a1 plan pins its own runtime; later R12 helper edits must not
    turn these historical admission contracts into checks of the current files."""
    original = artifacts.file_hash
    pinned = {batch.ROOT/name: digest for name, digest in HISTORICAL_RUNTIME.items()}
    monkeypatch.setattr(artifacts, 'file_hash', lambda path: pinned.get(path, None) or original(path))


def plan():
    return json.loads((batch.PLAN_DIR/'bfs-t16-protocol-recovery-simulator-batch-20260927-a1.json').read_text())


def protocols(value):
    return {key: {'settings': yamlio.load(batch.ROOT/ref['path'])['settings']}
            for key,ref in value['protocol_requests'].items()}


def test_new_protocol_requests_preserve_science_and_admit_actual_runtime():
    value=plan();base=recovery.base_plan(value)
    batch.validate_plan(value,'t16-protocol-recovery')
    recovery.validate_protocol_runtime(value,protocols(value))
    for key in ('bounds','model_build','target','verifier','roi','threads','repetitions','warmups',
                'verification_ticks','profitability','record_sha256','clock_policy'):
        assert value[key]==base[key]
    assert [{k:v for k,v in row.items() if k!='id'} for row in value['series']]==[
        {k:v for k,v in row.items() if k!='id'} for row in base['series']]
    assert (recovery.hard_end(value)-timedelta(seconds=21630)).isoformat()=='2026-09-27T14:15:47.225985-04:00'
    for key,ref in value['protocol_requests'].items():
        assert artifacts.file_hash(batch.ROOT/ref['path'])==ref['sha256']
        assert artifacts.digest(protocols(value)[key]['settings'])==ref['settings_sha256']


@pytest.mark.parametrize('key',['artifact','control'])
@pytest.mark.parametrize('role',['baseline','candidate'])
@pytest.mark.parametrize('field',['driver_sha256','parser_sha256','observer_sha256'])
def test_every_protocol_role_rejects_stale_runtime(key,role,field):
    value=plan();items=protocols(value)
    items[key]['settings']['instrumentation'][role]['verifier_runtime'][field]='0'*64
    with pytest.raises(ValueError,match='scientific settings or has stale'):
        recovery.validate_protocol_runtime(value,items)


@pytest.mark.parametrize('fault',['target','sampling','missing-control','runtime-bytes'])
def test_admission_rejects_science_or_selected_runtime_changes(fault,monkeypatch):
    value=plan();items=protocols(value)
    if fault=='target':items['artifact']['settings']['targets']['baseline']['configuration']['mode']='MAA'
    elif fault=='sampling':items['control']['settings']['sampling']['repetitions']+=1
    elif fault=='missing-control':items.pop('control')
    else:monkeypatch.setattr(artifacts,'file_hash',lambda p:'0'*64)
    with pytest.raises(ValueError):recovery.validate_protocol_runtime(value,items)


@pytest.mark.parametrize('fault',[None,'prior-refund','new-time','old-alias','lost-cost'])
def test_new_proof_and_failed_attempt_charged_once(fault,monkeypatch):
    value=plan();base=recovery.base_plan(value);original=recovery.preparation_charges
    prior=[{'id':'retained-prior-costs','elapsed_seconds':13174,'raw_bytes':8232083456}]
    monkeypatch.setattr(recovery,'base_plan',lambda p:base)
    monkeypatch.setattr(recovery,'preparation_charges',lambda p:copy.deepcopy(prior) if p is base else original(p))
    monkeypatch.setattr(recovery,'failed_protocol_batch',lambda p,b:{'id':base['id'],'elapsed_seconds':1839,'raw_bytes':11907072})
    if fault=='prior-refund':value['accounting']['protocol_recovery']['prior_proof_reservation']['elapsed_seconds']=0
    elif fault=='new-time':value['accounting']['preparation_reservation']['elapsed_seconds']=601
    elif fault=='old-alias':value['linux_proof_provenance']=recovery.PROOF_PROVENANCE
    elif fault=='lost-cost':prior[0]['elapsed_seconds']-=1
    if fault:
        with pytest.raises(ValueError):original(value)
    else:
        rows=original(value)
        assert rows==prior+[{'id':base['id'],'elapsed_seconds':1839,'raw_bytes':11907072},
            {'id':recovery.PROTOCOL_GROUP_ID,'elapsed_seconds':600,'raw_bytes':2*batch.GIB}]
        assert sum(r['elapsed_seconds'] for r in rows)==15613
        assert sum(r['raw_bytes'] for r in rows)==10391474176


def test_prospective_proof_rejects_historical_runtime_alias_before_io():
    with pytest.raises(ValueError,match='exact current-runtime'):
        batch.validate_preparation_reservation(plan(),{'linux_proof_runtime':{}})


@pytest.mark.parametrize('fault',[None,'promoted','unsettled','changed-wall','storage-growth','live-child','lost-prior'])
def test_failed_attempt_reader_does_not_promote_or_refund_closed_failure(fault,monkeypatch):
    value=plan();base=recovery.base_plan(value);entry=value['accounting']['protocol_recovery']['failed_batch']
    audit=json.loads((batch.ROOT/entry['closure_observation']['repository_path']).read_text())
    pane=next(row for row in audit['identity_observations'][0] if row['state']=='Z')
    prior=[{'id':'prior','elapsed_seconds':13174,'raw_bytes':8232083456}]
    driver={'id':base['id'],'plan':base,'state':'failed','reason':'ValueError: public stage exited 1',
        'outer_deadline':recovery.ENDS['t16-seal-recovery'],'outer_started':audit['driver']['outer_started'],
        'process_observations':{'pane_identity':pane},'storage_paths':entry['storage_paths'],'preparation_charges':copy.deepcopy(prior)}
    evaluation={'outcome':{'state':'failed','stage':'execution_identity',
        'reason':'actual simulator instrumentation differs from frozen treatment'},
        'correctness':{'state':'unverified','checks':[]},'timing':[]}
    objects={str(batch.ROOT/entry['closure_observation']['repository_path']):audit,
        entry['driver']['path']:driver,entry['evaluation']['path']:evaluation}
    monkeypatch.setattr(batch,'read_reference',lambda ref,maximum:copy.deepcopy(objects[ref['path']]))
    monkeypatch.setattr(batch,'allocated_bytes',lambda paths:entry['retained_bytes']+(fault=='storage-growth'))
    monkeypatch.setattr(recovery,'preparation_charges',lambda p:prior)
    monkeypatch.setattr(recovery.owned,'identity',lambda pid:None)
    from scripts import bfs_simulator_batch_terminal as terminal
    def ledger(*args,**kwargs):
        if fault=='unsettled':raise ValueError('unsettled retained ledger')
    monkeypatch.setattr(terminal,'validate_cleanup_ledger',ledger)
    if fault=='promoted':evaluation['outcome']['state']='complete'
    elif fault=='changed-wall':entry['elapsed_seconds']-=1
    elif fault=='lost-prior':driver['preparation_charges']=[]
    elif fault=='live-child':
        live=next(row for row in audit['identity_observations'][0] if row['pid']!=pane['pid'])
        monkeypatch.setattr(recovery.owned,'identity',lambda pid:{**live,'state':'R','rss_bytes':1} if pid==live['pid'] else None)
    if fault:
        with pytest.raises(ValueError):recovery.failed_protocol_batch(value,base)
    else:
        assert recovery.failed_protocol_batch(value,base)=={'id':base['id'],'elapsed_seconds':1839,'raw_bytes':11907072}
