"""Fixed pre-guest recovery accounting; synthetic records only. 2026-09-26 ET."""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import bfs_simulator_batch as batch
from scripts import bfs_simulator_batch_terminal as terminal
from scripts import bfs_linux_fixture as runner
from swdb import artifacts, yamlio
from test_bfs_simulator_batch import plan
from test_bfs_simulator_correction import reserved

CASE = 'test_linux_storage_observation_handles_sqlite_journal_unlink'


def recovery():
    return plan('t15-setup-recovery')


def charges():
    value = recovery(); entry = value['accounting']['retained_setup_failure']
    return entry['prior_charges'] + [
        {k: entry[k] for k in ('id','elapsed_seconds')} | {'raw_bytes':entry['retained_bytes']},
        {k:value['accounting']['preparation_reservation'][k] for k in ('id','elapsed_seconds','raw_bytes')}]


def test_fixed_recovery_preserves_science_and_only_flat_costs():
    old, value = plan('t15-correction'), recovery()
    batch.validate_plan(old,'t15-correction'); batch.validate_plan(value,'t15-setup-recovery')
    excluded = {'id','series','accounting','budget_authority','clock','clock_policy','supervision'}
    assert {k:v for k,v in old.items() if k not in excluded} == {k:v for k,v in value.items() if k not in excluded}
    assert [{k:v for k,v in row.items() if k!='id'} for row in old['series']] == [
        {k:v for k,v in row.items() if k!='id'} for row in value['series']]
    assert value['supervision'] == old['supervision'] | {
        'required_linux_cases':old['supervision']['required_linux_cases']+['sqlite_journal_unlink']}
    rows=charges()
    assert sum(row['elapsed_seconds'] for row in rows)==2997
    assert sum(row['raw_bytes'] for row in rows)==15322025984
    assert 43200-2997==40203 and 40*batch.GIB-15322025984==27627646976
    assert len({row['id'] for row in rows})==5
    assert runner.SELECTIONS['owned_cleanup'][0].endswith('-a4') and CASE in runner.SELECTIONS['owned_cleanup'][2]
    assert runner.SELECTIONS['dx100_interruption'][0].endswith('-a4')
    assert runner.SELECTIONS['native_campaign_owned_cleanup'][0].endswith('-a1')


@pytest.fixture
def setup(tmp_path,monkeypatch):
    """Real hash-bound new-reader inputs; previously tested old readers are seams."""
    value=recovery(); old=plan('t15-correction'); entry=value['accounting']['retained_setup_failure']
    runs=tmp_path/old['id'];runs.mkdir();dispatch=Path(str(runs)+'.dispatch');dispatch.mkdir()
    folder=runs/(old['id']+'.driver');folder.mkdir()
    records=tmp_path/'records/evaluations';records.mkdir(parents=True)
    row=old['series'][0];rid=row['id']+'.s0.r0.primary.evaluation';leaf=runs/row['id']/rid;leaf.mkdir(parents=True)
    def ref(path,record):
        path.write_text(json.dumps(record));return {'path':str(path),'sha256':artifacts.file_hash(path)}
    host=ref(leaf/'host-observation.json',{'explicit':'contract fixture, no actual host execution'})
    evaluation={'id':rid,'evidence_kind':'execution','outcome':{'state':'interrupted','stage':'execution_identity','reason':'interrupted by SIGTERM'},
        'timing':[],'correctness':{'state':'unverified','checks':[]},
        'stages':[{'stage':'execution_identity','state':'interrupted'}],
        'request':{'id':rid,'candidate':row['candidate'],'build_evaluation':old['model_build'],
            'configuration':copy.deepcopy(row['configuration']),'workload':{'id':row['workload'],'source':0},
            'protocol_trial':{'source_position':0,'repetition':0},'verification':{'checker':old['verifier'],
                'max_ticks':old['verification_ticks'],'coverage':True,'post_roi_trace':'SyscallBase','trace_transport':old['trace_transport']}},
        'context':{'host_observation':host},'raw_artifacts':[{'kind':'dx100_execute','path':str(leaf)},
            {'kind':'host_observation',**host}]}
    approval={'plan_sha256':artifacts.digest(old),'code_commit':entry['code_commit'],
              'preparation_charges':copy.deepcopy(entry['prior_charges'])}
    driver={'id':old['id'],'state':'failed','code_commit':entry['code_commit'],'plan':old,
        'outer_started':'2026-09-26T21:50:45.851819-04:00','started':'2026-09-26T21:50:46.419651-04:00',
        'finished':'2026-09-26T21:52:07.874658-04:00','outer_deadline':batch.SETUP_HARD_END,
        'preparation_charges':copy.deepcopy(entry['prior_charges']),
        'series':[{'id':row['id'],'state':'failed'}]}
    lane={'socket_lane':{'job':old['id'],'host':'mbit10','lease_generation':416,'exit_code':1,
        'started_utc':'2026-09-27T01:50:46Z','ended_utc':'2026-09-27T01:52:08Z'}}
    audit={'id':old['id'],'state':'failed','lease_released':True,'lease_generation':416,
        'observed_at':'2026-09-26T21:54:05.889090-04:00'}
    entry['storage_paths']=list(map(str,(runs,dispatch)));calls=[]
    original=batch.preparation_charges
    def old_charges(policy):
        if policy['id']==old['id']:
            calls.append('old_charges');return copy.deepcopy(recovery()['accounting']['retained_setup_failure']['prior_charges'])
        return original(policy)
    monkeypatch.setattr(batch,'preparation_charges',old_charges)
    monkeypatch.setattr(batch,'validate_cleanup_tests',lambda v:calls.append(('oldproof',copy.deepcopy(v))))
    monkeypatch.setattr(batch,'validate_preparation_reservation',lambda p,a:calls.append(('oldreservation',artifacts.digest(p))))
    monkeypatch.setattr(terminal,'validate_cleanup_ledger',lambda *a,**k:calls.append(('cleanup',k)))
    monkeypatch.setattr(terminal,'validate_storage_accounting',lambda *a,**k:{'storage_paths':entry['storage_paths'],
        'raw_bytes':batch.allocated_bytes([runs,dispatch])})
    monkeypatch.setattr(batch,'now',lambda:datetime(2026,9,26,22,20,tzinfo=batch.ET))
    def seal():
        entry['admission']=ref(dispatch/'admission.json',approval);driver['admission']=entry['admission']
        entry['driver']=ref(folder/'driver.json',driver);audit['driver']=entry['driver']
        audit['lane']=ref(dispatch/'lane.json',lane)
        entry['terminal']=ref(dispatch/'terminal-validation.json',audit)
        entry['cleanup_ledger']=ref(folder/'cleanup-ledger.json',{'explicit':'old settled reader seam'})
        file=records/(rid+'.yaml');file.write_text(yamlio.dumps(evaluation))
        entry['evaluation']={'path':str(file),'sha256':artifacts.file_hash(file)}
        entry['retained_bytes']=batch.allocated_bytes([runs,dispatch])
        return value
    return SimpleNamespace(value=value,old=old,entry=entry,approval=approval,driver=driver,lane=lane,audit=audit,
        evaluation=evaluation,leaf=leaf,runs=runs,dispatch=dispatch,records=records,seal=seal,calls=calls)


def test_recovery_reopens_exact_failed_record_leaf_and_old_charges(setup):
    rows=batch.setup_failure_charges(setup.seal())
    assert rows == [setup.entry['prior_proof_charge'],{'id':batch.SETUP_FAILURE_ID,'elapsed_seconds':201,
                                                    'raw_bytes':setup.entry['retained_bytes']}]
    assert any(call[0]=='oldproof' for call in setup.calls)
    assert ('oldreservation',batch.PLAN_HASHES['t15-correction']) in setup.calls
    assert any(call[0]=='cleanup' and call[1]['expected_deadline']==batch.SETUP_HARD_END for call in setup.calls)


@pytest.mark.parametrize('fault',['complete','later-end','wrong-code','other-lineage','revised-old-plan',
    'prior-refund','driver-refund','proof-refund','omitted-proof','clock-extension','later-stage','timing',
    'correctness','fixture','wrong-source','wrong-position','wrong-checker','no-gzip','wrong-candidate',
    'checkpoint-request','simulation-dir','checkpoint-dir','extra-leaf','other-evaluation','other-series',
    'unreleased','zero-exit','wrong-audit','wrong-host-observation','host-hash','changed-evaluation','undercharge','grew'])
def test_recovery_refuses_rehashed_later_work_or_lineage_changes(setup,fault):
    f=setup
    if fault=='complete':f.driver['state']='complete'
    elif fault=='later-end':f.driver['outer_deadline']='2026-09-27T09:43:24-04:00'
    elif fault=='wrong-code':f.driver['code_commit']='e'*40
    elif fault=='other-lineage':f.entry['id']='arbitrary-retry'
    elif fault=='revised-old-plan':f.old['bounds']['batch_seconds']+=1
    elif fault=='prior-refund':f.approval['preparation_charges'][0]['elapsed_seconds']-=1
    elif fault=='driver-refund':f.driver['preparation_charges'][1]['raw_bytes']-=1024
    elif fault=='proof-refund':f.entry['prior_proof_charge']['raw_bytes']-=1024
    elif fault=='omitted-proof':f.entry['prior_charges'].pop()
    elif fault=='clock-extension':f.value['clock_policy']['absolute_end']='2026-09-28T09:14:09.851819-04:00'
    elif fault=='later-stage':f.evaluation['stages'].append({'stage':'checkpoint','state':'failed'})
    elif fault=='timing':f.evaluation['timing']=[{'value':1}]
    elif fault=='correctness':f.evaluation['correctness']['checks']=[{'state':'passed'}]
    elif fault=='fixture':f.evaluation['request']['fixture']=True
    elif fault=='wrong-source':f.evaluation['request']['workload']['source']=1234
    elif fault=='wrong-position':f.evaluation['request']['protocol_trial']['repetition']=1
    elif fault=='wrong-checker':f.evaluation['request']['verification']['checker']='v1'
    elif fault=='no-gzip':f.evaluation['request']['verification'].pop('trace_transport')
    elif fault=='wrong-candidate':f.evaluation['request']['candidate']='other'
    elif fault=='checkpoint-request':f.evaluation['request']['checkpoint_evaluation']='previous'
    elif fault=='simulation-dir':(f.runs/'simulation').mkdir()
    elif fault=='checkpoint-dir':(f.leaf/'checkpoint').mkdir()
    elif fault=='extra-leaf':(f.leaf/'guest.log').write_text('ran')
    elif fault=='other-evaluation':(f.records/(batch.SETUP_FAILURE_ID+'.extra.yaml')).write_text('{}')
    elif fault=='other-series':f.driver['series'].append({'id':'second','state':'failed'})
    elif fault=='unreleased':f.audit['lease_released']=False
    elif fault=='zero-exit':f.lane['socket_lane']['exit_code']=0
    elif fault=='wrong-host-observation':f.evaluation['context']['host_observation']['path']=str(f.leaf/'other')
    elif fault=='host-hash':(f.leaf/'host-observation.json').write_text('{}')
    value=f.seal()
    if fault=='wrong-audit':
        path=Path(f.entry['terminal']['path']);v=json.loads(path.read_text());v['driver']['sha256']='f'*64
        path.write_text(json.dumps(v));f.entry['terminal']['sha256']=artifacts.file_hash(path)
    elif fault=='changed-evaluation':Path(f.entry['evaluation']['path']).write_text('{}')
    elif fault=='undercharge':f.entry['elapsed_seconds']-=1
    elif fault=='grew':(f.dispatch/'late.log').write_bytes(b'x'*32768)
    with pytest.raises(ValueError):batch.setup_failure_charges(value)


def make_clock(monkeypatch,begin):
    value=recovery();rows=charges();clock=SimpleNamespace(wall=begin,mono=100.)
    monkeypatch.setattr(batch,'preparation_charges',lambda p:rows)
    monkeypatch.setattr(batch,'now',lambda:clock.wall)
    monkeypatch.setattr(batch.time,'monotonic',lambda:clock.mono)
    end=batch.stamp(batch.SETUP_HARD_END)
    approved={'prepared_at':(begin-timedelta(minutes=1)).isoformat(),'preparation_charges':rows,
        'clock':{'not_before':begin.isoformat(),'latest_start':(end-timedelta(seconds=21630)).isoformat(),
                 'absolute_end':end.isoformat()}}
    return value,approved,clock


def test_new_only_clock_clamps_late_start_and_second_series_cannot_borrow_time(monkeypatch):
    begin=datetime(2026,9,26,23,tzinfo=batch.ET);value,approved,c=make_clock(monkeypatch,begin)
    ledger=batch.Ledger(value,approved,c.mono,begin)
    remaining=(batch.stamp(batch.SETUP_HARD_END)-begin).total_seconds()
    assert ledger.monotonic_end==100+remaining and remaining<40203
    assert ledger.next_allowance(0)==(21600,25)
    c.mono+=remaining-21630+.001;c.wall+=timedelta(seconds=remaining-21630+.001)
    with pytest.raises(ValueError,match='next full series'):ledger.next_allowance(0)
    assert ledger.observation(0)['charged_elapsed_seconds']==pytest.approx(2997+c.mono-100)


def test_recovery_supports_narrower_prospective_latest_and_preserves_startup_cost(monkeypatch):
    begin=datetime(2026,9,26,23,tzinfo=batch.ET);value,approved,c=make_clock(monkeypatch,begin)
    approved['clock']['latest_start']=(begin+timedelta(minutes=2)).isoformat()
    ledger=batch.Ledger(value,approved,100,begin+timedelta(seconds=2),outer_started=begin)
    assert ledger.monotonic_end==100+(batch.stamp(batch.SETUP_HARD_END)-begin).total_seconds()-2
    assert ledger.observation(0)['charged_elapsed_seconds']==2999


@pytest.mark.parametrize('fault',['after-last-full','extend-end','latest-too-late','future-prep','other-id','missing-policy'])
def test_recovery_clock_cannot_extend_or_relabel_old_policy(monkeypatch,fault):
    begin=datetime(2026,9,26,23,tzinfo=batch.ET);value,approved,c=make_clock(monkeypatch,begin)
    if fault=='after-last-full':begin=batch.stamp(batch.SETUP_HARD_END)-timedelta(seconds=21629)
    elif fault=='extend-end':approved['clock']['absolute_end']='2026-09-27T09:43:24-04:00'
    elif fault=='latest-too-late':approved['clock']['latest_start']=batch.SETUP_HARD_END
    elif fault=='future-prep':approved['prepared_at']=(begin+timedelta(seconds=1)).isoformat()
    elif fault=='other-id':value['id']='bfs-t15-correction-simulator-batch-20260926-a1'
    else:value.pop('clock_policy')
    with pytest.raises(ValueError):batch.Ledger(value,approved,100,begin)


@pytest.mark.parametrize('fault',[None,'missing','skip','failure','duplicate','changed-hash'])
def test_recovery_requires_fifth_actual_linux_case_without_changing_old_reader(reserved,fault):
    value,approved=reserved
    batch.validate_preparation_reservation(value,approved) # old proof shape still readable
    value['id']=batch.SETUP_RECOVERY_ID
    proof_ref=approved['linux_cleanup_tests'][0];proof=json.loads(Path(proof_ref['path']).read_text())
    path=Path(proof_ref['path']).parent/'junit.xml'
    case='' if fault=='missing' else '<testcase name="'+CASE+'">'+(
        '<skipped/>' if fault=='skip' else '<failure/>' if fault=='failure' else '')+'</testcase>'
    if fault=='duplicate':case+=case
    path.write_text('<testsuites><testsuite>'+case+'</testsuite></testsuites>')
    proof['junit']={'path':str(path),'sha256':artifacts.file_hash(path)}
    if fault=='changed-hash':proof['junit']['sha256']='0'*64
    Path(proof_ref['path']).write_text(json.dumps(proof));proof_ref['sha256']=artifacts.file_hash(proof_ref['path'])
    # Update all content references as a real freshly sealed admission would.
    kind='owned_cleanup';ref=approved['preparation_reservation']['audits'][kind]
    completion=json.loads(Path(ref['path']).read_text());completion['proof']=proof_ref
    Path(ref['path']).write_text(json.dumps(completion));ref['sha256']=artifacts.file_hash(ref['path'])
    readback_ref=approved['preparation_reservation']['auditor_readbacks'][kind]
    readback=json.loads(Path(readback_ref['path']).read_text());readback.update(proof=proof_ref,audit_receipt=ref)
    Path(readback_ref['path']).write_text(json.dumps(readback));readback_ref['sha256']=artifacts.file_hash(readback_ref['path'])
    approved['preparation_reservation']['raw_bytes']=batch.allocated_bytes(value['accounting']['preparation_reservation']['storage_paths'])
    if fault:
        with pytest.raises(ValueError,match='SQLite'):batch.validate_preparation_reservation(value,approved)
    else:batch.validate_preparation_reservation(value,approved)
