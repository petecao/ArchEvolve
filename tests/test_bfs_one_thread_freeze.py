"""One-thread publication contracts; artificial fixtures, never measurements.

Created: 2026-09-26 ET. Raw collection admission is tested by the pinned client;
these tests exercise history/gate routing, terminal closure, and reader launch.
"""
import copy
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from scripts import bfs_freeze_pilot as publisher
from scripts import bfs_one_thread_calibration as one
from scripts import bfs_paired_calibration as paired
from swdb import artifacts, bfs_native
from swdb.cli import Failure
from swdb.store import Store
from test_bfs_freeze_pilot import aa_control
from test_bfs_paired_freeze import paired_review, SAMPLING


PLAN = json.loads(one.driver.PLAN.read_text())


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')
    return {'path': str(path), 'sha256': artifacts.file_hash(path)}


def selected(checkout, packages):
    return {'run_id': one.RUN_ID, 'code_commit': one.COLLECTOR_COMMIT,
            'collector_checkout': str(checkout), 'driver_receipt': {}, 'terminal_receipt': {},
            'packages': packages, 'historical_paired_calibration': {}}


@pytest.fixture
def fresh_review(paired_review, monkeypatch):
    """Real serial raw fixture; explicit new/old paired admission seams."""
    case = paired_review
    fresh = []
    for old in case.packets:
        item = copy.deepcopy(old); row = item['evaluation']
        row['id'] += '.one-thread'
        row['context'].update(threads=1, repetitions=10)
        row['build'].update(native_runtime=copy.deepcopy(PLAN['native_runtime']),
                            execution_environment=bfs_native.controlled_environment(1))
        template = row['timing'][0]
        row['timing'] = [{**template, 'source': vertex, 'source_position': position,
            'repetition': repeat, 'duration_s': 1+.001*repeat,
            'output': f'synthetic-{row["id"]}-{position}-{repeat}'}
            for repeat in range(10) for position, vertex in enumerate(PLAN['sources'])]
        item['package']['id'] += '.one-thread'; item['diagnostic']['id'] += '.one-thread'
        item['record_identities'] = {value['id']: artifacts.digest(value)
                                    for value in (row, item['package'], item['diagnostic'])}
        fresh.append(item)
    packets = {item['package']['id']: item for item in case.packets+fresh}
    monkeypatch.setattr(publisher, 'packet', lambda _store, rid: packets[rid])
    historical = case.spec.pop('paired_calibration')
    case.spec['one_thread_calibration'] = selected(Path('/synthetic/collector'), list(packets)[4:])
    case.spec['one_thread_calibration']['historical_paired_calibration'] = historical
    case.spec['packages'] = [fresh[i]['package']['id'] for i in (1, 3)]
    old_paired = {'control': {'state': 'unqualified', 'pairs': [{'id':i} for i in range(4)]},
        'unmet_gates': ['original four-thread variability failure'], 'admitted_for_new_sampling': False}
    monkeypatch.setattr(one, 'historical_paired_control', lambda *_: copy.deepcopy(old_paired))

    def qualify(_spec, items, _store, identities, gates):
        pairs = []
        for item, samples in zip(fresh, case.samples):
            checked = paired.negative_control(samples, PLAN['profitability'], SAMPLING)
            gates.extend(checked['unmet_gates'])
            pairs.append({**checked, 'evaluations': {role: copy.deepcopy(item['evaluation'])
                           for role in ('baseline', 'candidate')}})
            identities.update(item['record_identities'])
        return {'pairs': pairs, 'sampling': copy.deepcopy(SAMPLING), 'native_runtime': PLAN['native_runtime'],
            'driver_receipt': {'path':'synthetic'}, 'terminal_closure': {'audit': {'path':'synthetic'}},
            'fresh_diagnostics': [item['package']['id'] for item in fresh],
            'selected_primary_evaluations': [item['evaluation']['id'] for item in items]}, [item['evaluation'] for item in items]
    monkeypatch.setattr(one, 'qualify', qualify)
    case.fresh = fresh
    return case


def test_new_configuration_can_qualify_while_retaining_both_old_failures(fresh_review):
    case = fresh_review
    case.trials(case.seconds[0], .5); case.save()
    result = publisher.prepare(case.spec, case.store)
    settings = result['freeze_request']['settings']; calibration = settings['calibration']
    assert result['publishable'] and result['unmet_gates'] == [] and not result['gain_claim']
    assert settings['threads'] == 1 and settings['sampling']['repetitions'] == 10
    assert settings['native_runtime'] == PLAN['native_runtime']
    assert calibration['historical_serial_control']['control']['state'] == 'numerical_gain_detected'
    assert calibration['historical_serial_control']['unmet_gates']
    assert calibration['historical_four_thread_paired_control']['control']['state'] == 'unqualified'
    assert calibration['historical_four_thread_paired_control']['unmet_gates']
    assert calibration['historical_four_thread_paired_control']['admitted_for_new_sampling'] is False
    assert len(calibration['repeatability_control']['fresh_diagnostics']) == 4
    assert case.accelerator_calls and not case.qualified_calls
    assert all(row['context']['threads'] == 4 for row in case.seconds)


def test_unselected_new_cell_still_vetoes_publication(fresh_review):
    fresh_review.samples[0]['candidate'][0] = publisher.summary(0, [1]*9+[2])
    result = publisher.prepare(fresh_review.spec, fresh_review.store)
    assert not result['publishable']
    assert any('spread' in gate for gate in result['unmet_gates'])


def test_new_route_keeps_shared_accelerator_gate(fresh_review, monkeypatch):
    def blocked(_store, _ids, _packets, _identities, gates, _ceiling):
        gates.append('actual shared accelerator calibration missing'); return {}
    monkeypatch.setattr(publisher, 'accelerator_gate', blocked)
    result = publisher.prepare(fresh_review.spec, fresh_review.store)
    assert not result['publishable'] and 'actual shared accelerator calibration missing' in result['unmet_gates']


@pytest.mark.parametrize('fault', ['old-package', 'missing-old', 'changed-old', 'ambiguous'])
def test_new_route_cannot_omit_history_or_reuse_old_context(fresh_review, fault):
    case = fresh_review
    if fault == 'old-package': case.spec['packages'][0] = case.packets[1]['package']['id']
    elif fault == 'missing-old': case.spec['one_thread_calibration']['historical_paired_calibration']['historical_packages'].pop()
    elif fault == 'changed-old': case.seconds[0]['timing'][0]['duration_s'] = 99
    else: case.spec['paired_calibration'] = {}
    with pytest.raises(ValueError): publisher.prepare(case.spec, case.store)


@pytest.fixture
def terminal_case(tmp_path):
    ancestor = [{'pid':101,'start_ticks':1,'parent_pid':102},
                {'pid':102,'start_ticks':2,'parent_pid':103},
                {'pid':103,'start_ticks':3,'parent_pid':999}]
    child = {'pid':104,'start_ticks':4,'parent_pid':101}
    samples = write(tmp_path/'samples.jsonl', {'processes': [ancestor[0],child]})
    receipt = {'started':'2026-09-26T14:00:01-04:00', 'finished':'2026-09-26T14:00:10.5-04:00',
        'outer_start':'2026-09-26T14:00:00-04:00','outer_end':'2026-09-26T19:04:00-04:00',
        'driver_pid':101, 'lane':{'verified_lane':f'{one.driver.LANE} (verified: affinity, bind:1, lease held, generation 500)'},
        'process_observations':{'driver_identity':ancestor[0],'pane_identity':ancestor[-1],
                                'ancestry':ancestor,'owned_processes':[ancestor[0],child]},
        'rss':{'samples':samples},'stages':[{'identity':child}]}
    driver_ref = write(tmp_path/'driver.json', receipt)
    lane = {'socket_lane':{'host':'mbit10','node':1,'lease_name':one.driver.LANE,'lease_generation':500,
        'exit_code':0,'started_utc':'2026-09-26T18:00:00Z','ended_utc':'2026-09-26T18:00:10Z'}}
    exit_path = tmp_path/'exit'; exit_path.write_text('0\n')
    lease = {'state':'released','lease':{'generation':500,'lease_name':one.driver.LANE},
             'released_at':'2026-09-26T14:00:11-04:00'}
    audit = {'id':one.RUN_ID,'state':'complete','repository_commit':one.COLLECTOR_COMMIT,
        'driver':driver_ref,'lane':write(tmp_path/'lane.json',lane),
        'outer_exit':{'path':str(exit_path),'sha256':artifacts.file_hash(exit_path)},
        'lease_snapshot':write(tmp_path/'lease.json',lease),'observed_at':'2026-09-26T14:00:12-04:00',
        'lease_released':True,'cleanup_state':'terminal_and_reaped','owned_processes_absent':True,
        'owned_processes':[dict(row,state='absent') for row in ancestor+[child]]}
    def check():
        return one.terminal_closure(write(tmp_path/'audit.json',audit),driver_ref,receipt,
            datetime.fromisoformat('2026-09-26T14:00:13-04:00'), tmp_path/'proc')
    return SimpleNamespace(receipt=receipt,audit=audit,lane=lane,lease=lease,check=check,root=tmp_path)


def test_whole_terminal_audit_accepts_fractional_finish(terminal_case):
    assert terminal_case.check()['cleanup_state'] == 'terminal_and_reaped'


def test_outer_clock_can_precede_helper_across_a_second_boundary(terminal_case):
    c = terminal_case
    c.receipt['outer_start'] = '2026-09-26T13:59:59.8-04:00'
    c.receipt['outer_end'] = '2026-09-26T19:03:59.8-04:00'
    assert c.check()['cleanup_state'] == 'terminal_and_reaped'


@pytest.mark.parametrize('where',['stage','final'])
def test_terminal_union_includes_cleanup_only_observations(terminal_case,where):
    c = terminal_case
    target = c.receipt['stages'][0] if where == 'stage' else c.receipt
    target['cleanup'] = {'observed':[{'pid':105,'start_ticks':5}]}
    with pytest.raises(ValueError, match='omits or adds'): c.check()
    c.audit['owned_processes'].append({'pid':105,'start_ticks':5,'state':'absent'})
    assert c.check()['cleanup_state'] == 'terminal_and_reaped'


@pytest.mark.parametrize('fault', ['omit-child','omit-helper','add-identity','duplicate','changed-start',
                                  'wrong-pane-zombie','nonzero-zombie','driver-ref','lane','held','live'])
def test_whole_terminal_audit_rejects_unbound_cleanup(terminal_case, fault):
    c = terminal_case; rows = c.audit['owned_processes']
    if fault == 'omit-child': rows.pop()
    elif fault == 'omit-helper': rows.pop(1)
    elif fault == 'add-identity': rows.append({'pid':105,'start_ticks':5,'state':'absent'})
    elif fault == 'duplicate': rows.append(copy.deepcopy(rows[-1]))
    elif fault == 'changed-start': rows[-1]['start_ticks'] += 1
    elif fault in {'wrong-pane-zombie','nonzero-zombie'}:
        c.audit.update(cleanup_state='terminal_no_live_owned_processes',owned_processes_absent=False,owned_processes_nonrunning=True)
        rows[3 if fault == 'wrong-pane-zombie' else 2].update(state='Z',rss_bytes=1 if fault == 'nonzero-zombie' else 0,role='tmux_launcher')
    elif fault == 'driver-ref': c.audit['driver'] = {'path':'changed','sha256':'0'*64}
    elif fault == 'lane':
        c.lane['socket_lane']['node'] = 0; c.audit['lane'] = write(c.root/'lane.json',c.lane)
    elif fault == 'held':
        c.lease['state'] = 'held'; c.audit['lease_snapshot'] = write(c.root/'lease.json',c.lease)
    else:
        path = c.root/'proc'/'104'; path.mkdir(parents=True)
        fields = ['S','101']+['0']*17+['4','0','1']
        (path/'stat').write_text('104 (fixture) '+' '.join(fields))
    with pytest.raises(ValueError): c.check()


def test_only_exact_terminal_pane_zero_rss_zombie_is_allowed(terminal_case):
    c = terminal_case
    c.audit.update(cleanup_state='terminal_no_live_owned_processes',owned_processes_absent=False,owned_processes_nonrunning=True)
    c.audit['owned_processes'][2].update(state='Z',rss_bytes=0,role='tmux_launcher')
    assert c.check()['cleanup_state'] == 'terminal_no_live_owned_processes'


@pytest.fixture
def readback_case(tmp_path, monkeypatch):
    """Real child process; explicit synthetic runtime-validation seam."""
    checkout = tmp_path/'collector'; checkout.mkdir()
    (checkout/one.PLAN_RELATIVE).parent.mkdir(parents=True)
    (checkout/one.PLAN_RELATIVE).write_text(json.dumps(PLAN))
    for folder in ('scripts','swdb'):
        (checkout/folder).mkdir(); (checkout/folder/'__init__.py').write_text('')
    (checkout/'swdb/store.py').write_text('class Store:\n def __init__(self,path): self.path=path\n')
    (checkout/'swdb/yamlio.py').write_text('import json\ndef load(path): return json.load(open(path))\n')
    source = checkout/'scripts/bfs_native_one_thread_pilot.py'
    source.write_text('import os,json\nPLAN='+repr(one.PLAN_RELATIVE)+'\n'
        'def validate_driver_receipt(ref,plan,store,commit):\n'
        ' assert commit=='+repr(one.COLLECTOR_COMMIT)+'\n'
        ' assert os.path.isabs(store.path)\n'
        ' return dict(state="complete",qualified=True,gain_claim=False,driver=ref)\n')
    runtime = {'python':{'path':sys.executable},'synthetic_fixture':True}
    monkeypatch.setattr(one.driver,'runtime_identity',lambda expected,root: copy.deepcopy(runtime))
    value = selected(checkout,['a','b','c','d']); value['driver_receipt']={'path':'fixture','sha256':'0'*64}
    return SimpleNamespace(selected=value,receipt={'runtime':runtime},store=SimpleNamespace(dir=tmp_path/'records'),source=source)


def test_pinned_reader_uses_its_checkout_and_returns_stable_result(readback_case):
    c = readback_case
    first = one.pinned_readback(c.selected,c.receipt,c.store)
    second = one.pinned_readback(c.selected,c.receipt,c.store)
    assert first == second and first[1]['result']['qualified'] is True


def test_pinned_reader_timeout_reaps_its_actual_child(readback_case, monkeypatch):
    c = readback_case
    c.source.write_text(c.source.read_text()+'\nimport time\ntime.sleep(5)\n')
    monkeypatch.setattr(one,'READBACK_SECONDS',.1)
    original = subprocess.Popen; children=[]
    def spawn(*args,**kwargs):
        child=original(*args,**kwargs); children.append(child); return child
    monkeypatch.setattr(one.subprocess,'Popen',spawn)
    with pytest.raises(subprocess.TimeoutExpired): one.pinned_readback(c.selected,c.receipt,c.store)
    assert len(children)==1 and children[0].returncode is not None


def test_pinned_reader_denied_shutdown_reaps_and_preserves_original_timeout(readback_case, monkeypatch):
    c=readback_case
    c.source.write_text(c.source.read_text()+'\nimport time\ntime.sleep(.2)\n')
    monkeypatch.setattr(one,'READBACK_SECONDS',.03)
    original=subprocess.Popen; children=[]
    def spawn(*args,**kwargs):
        child=original(*args,**kwargs);children.append(child);return child
    monkeypatch.setattr(one.subprocess,'Popen',spawn)
    def denied(*_):raise PermissionError('synthetic signal denial')
    monkeypatch.setattr(one.os,'killpg',denied)
    try:
        with pytest.raises(subprocess.TimeoutExpired) as failure:
            one.pinned_readback(c.selected,c.receipt,c.store)
        assert isinstance(failure.value.__cause__,PermissionError)
        assert len(children)==1 and children[0].returncode==0
        with pytest.raises(ChildProcessError):one.os.waitpid(children[0].pid,one.os.WNOHANG)
    finally:
        for child in children:child.wait(timeout=2)


def test_successful_reader_never_signals_a_reaped_numeric_group(readback_case,monkeypatch):
    c=readback_case
    def forbidden(*_):pytest.fail('communicate already reaped this group leader')
    monkeypatch.setattr(one.os,'killpg',forbidden)
    assert one.pinned_readback(c.selected,c.receipt,c.store)[1]['result']['qualified'] is True


def test_reader_final_output_hash_cannot_escape_shared_deadline(readback_case,monkeypatch):
    c=readback_case; actual_hash=one.hashlib.sha256; actual_clock=time.monotonic; elapsed=[0]
    def digest(value=b''):
        result=actual_hash(value)
        if value.startswith(b'{"driver":') and b'"qualified": true' in value:
            elapsed[0]=one.READBACK_SECONDS+one.READBACK_CLEANUP_SECONDS+1
        return result
    monkeypatch.setattr(one.hashlib,'sha256',digest)
    monkeypatch.setattr(one.time,'monotonic',lambda:actual_clock()+elapsed[0])
    with pytest.raises(ValueError,match='finalization exceeded'):
        one.pinned_readback(c.selected,c.receipt,c.store)


def test_reader_shutdown_waits_clip_to_less_than_five_seconds(monkeypatch):
    waits=[]
    child=SimpleNamespace(pid=999,poll=lambda:None)
    def wait(timeout):
        waits.append(timeout);raise subprocess.TimeoutExpired('synthetic reader',timeout)
    child.wait=wait
    monkeypatch.setattr(one.os,'getpgid',lambda pid:pid)
    monkeypatch.setattr(one.os,'killpg',lambda *_:None)
    one.stop_reader(child,time.monotonic()+.2)
    assert len(waits)==2 and all(0 <= value <= .2 for value in waits)


@pytest.mark.parametrize('fault',['runtime','checkout','result'])
def test_pinned_reader_rejects_changed_runtime_or_unqualified_result(readback_case,fault):
    c=readback_case
    if fault=='runtime': c.receipt['runtime']={'changed':True}
    elif fault=='checkout': c.selected['collector_checkout'] += '/absent'
    else: c.source.write_text(c.source.read_text().replace('qualified=True','qualified=False'))
    with pytest.raises(ValueError): one.pinned_readback(c.selected,c.receipt,c.store)


@pytest.mark.parametrize('version',[True,1.0,None])
def test_unselected_member_cannot_supply_inexact_runtime_version(version):
    evaluations=[{'id':str(i),'build':{'native_runtime':copy.deepcopy(PLAN['native_runtime']),
                                    'execution_environment':bfs_native.controlled_environment(1)}} for i in range(8)]
    evaluations[-1]['build']['native_runtime']['version']=version
    control={'native_runtime':PLAN['native_runtime'],'pairs':[{'evaluations':dict(zip(('baseline','candidate'),evaluations[i:i+2]))}
                                                           for i in range(0,8,2)]}
    with pytest.raises(Failure,match='runtime'): one.calibrated_runtime(control)


@pytest.fixture
def qualification_case(tmp_path, monkeypatch):
    """Synthetic records; collection and terminal admission have explicit seams."""
    records, packets, cells = {}, {}, []
    for index, cell in enumerate(PLAN['cells']):
        pair = {'id':cell['id']}; records[pair['id']] = pair
        members = {}
        for role in ('baseline','candidate'):
            row = {'id':cell[role+'_evaluation'], 'build':{'native_runtime':copy.deepcopy(PLAN['native_runtime']),
                      'execution_environment':bfs_native.controlled_environment(1)}}
            records[row['id']] = row; members[role] = {'sha256':artifacts.digest(row)}
        samples = {role:[publisher.summary(vertex,[1+.001*r for r in range(10)]) for vertex in PLAN['sources']]
                   for role in members}
        entry = {'id':cell['id'],'pair_sha256':artifacts.digest(pair),'members':members,'samples':samples,
                 'control':paired.negative_control(samples,PLAN['profitability'],SAMPLING)}
        cells.append(entry)
        package_id = f'fresh-{index}'
        packets[package_id] = {'package':{'id':package_id},'diagnostic':{'id':cell['profile']},
            'evaluation':records[cell['baseline_evaluation']], 'record_identities':{package_id:'a'*64}}
    receipt = {'id':one.RUN_ID,'repository_commit':one.COLLECTOR_COMMIT,'state':'complete',
        'primary_qualified':True,'gain_claim':False,'protocol_freeze':False,'provider_calls':False,
        'cells':cells,'diagnostics':[{'id':rid} for rid in packets]}
    spec = {'maximum_relative_spread':.10,'one_thread_calibration':selected(tmp_path,list(packets))}
    def save(): spec['one_thread_calibration']['driver_receipt'] = write(tmp_path/'driver.json',receipt)
    save()
    calls=[]
    def readback(*_): calls.append(True); return copy.deepcopy(PLAN), {'synthetic_admission_seam':True}
    monkeypatch.setattr(one,'pinned_readback',readback)
    monkeypatch.setattr(one,'terminal_closure',lambda *_: {'audit':{'synthetic_terminal_seam':True}})
    monkeypatch.setattr(one,'packet',lambda _store,rid: packets[rid])
    return SimpleNamespace(spec=spec,receipt=receipt,records=records,packets=packets,save=save,calls=calls,
                           store=SimpleNamespace(get=lambda rid,kind=None: records.get(rid)))


def test_qualifier_requires_four_fresh_diagnostics_and_all_eight_runtime_maps(qualification_case):
    c=qualification_case; identities={}; gates=[]
    control,primary=one.qualify(c.spec,[c.packets['fresh-1'],c.packets['fresh-3']],c.store,identities,gates)
    policy,evidence=one.calibrated_runtime(control)
    assert len(c.calls)==1 and control['state']=='qualified' and not gates
    assert len(control['pairs'])==len(control['fresh_diagnostics'])==4 and len(evidence['evaluations'])==8
    assert policy==PLAN['native_runtime'] and [row['id'] for row in primary]==control['selected_primary_evaluations']
    assert all(cell['id'] in identities for cell in PLAN['cells'])


@pytest.mark.parametrize('fault',['missing-package','reordered-packages','missing-cell','changed-member',
                                'changed-control','unqualified','different-pin','old-package'])
def test_qualifier_rejects_incomplete_or_incompatible_new_evidence(qualification_case,fault):
    c=qualification_case; selected=c.spec['one_thread_calibration']; packets=[c.packets['fresh-1'],c.packets['fresh-3']]
    if fault=='missing-package': selected['packages'].pop()
    elif fault=='reordered-packages': selected['packages'].reverse()
    elif fault=='missing-cell': c.receipt['cells'].pop()
    elif fault=='changed-member': c.records[PLAN['cells'][0]['candidate_evaluation']]['changed']=True
    elif fault=='changed-control': c.receipt['cells'][0]['control']['gain_claim']=True
    elif fault=='unqualified': c.receipt['primary_qualified']=False
    elif fault=='different-pin': c.receipt['repository_commit']='0'*40
    else: packets=[{'package':{'id':'old-four-thread'},'evaluation':{'id':'old'}}]
    c.save()
    with pytest.raises(ValueError): one.qualify(c.spec,packets,c.store,{},[])


def test_resealed_unselected_control_failure_still_blocks_new_qualification(qualification_case):
    c=qualification_case; entry=c.receipt['cells'][0]
    entry['samples']['candidate'][0]=publisher.summary(0,[1]*9+[2])
    entry['control']=paired.negative_control(entry['samples'],PLAN['profitability'],SAMPLING); c.save()
    gates=[]
    result,_=one.qualify(c.spec,[c.packets['fresh-1'],c.packets['fresh-3']],c.store,{},gates)
    assert result['state']=='unqualified' and any('spread' in value for value in gates)


@pytest.fixture
def historical_metadata(monkeypatch):
    """Actual imported metadata only; remote driver/terminal bytes are stubbed."""
    store=Store(one.driver.ROOT/'records')
    old_plan=json.loads((one.driver.ROOT/PLAN['historical_plan']['path']).read_text())
    driver_ref={'path':'synthetic-old-driver','sha256':'a'*64}
    receipt={'state':'complete','cells':[{'id':cell['id'],'pair_sha256':artifacts.digest(store.get(cell['id']))}
                                       for cell in old_plan['cells']]}
    spec={'maximum_relative_spread':.10,'one_thread_calibration':selected(Path('/synthetic'),['a','b','c','d'])}
    spec['one_thread_calibration']['historical_paired_calibration']={
        'pairs':[cell['id'] for cell in old_plan['cells']],'driver_receipt':driver_ref,'historical_packages':['a','b','c','d']}
    monkeypatch.setattr(one,'read',lambda ref,*_: {'driver':driver_ref} if ref==PLAN['fixed_prerequisites']['paired'] else receipt)
    return SimpleNamespace(spec=spec,store=store,receipt=receipt)


def test_exact_imported_historical_failures_remain_unqualified_metadata(historical_metadata):
    c=historical_metadata; identities={}
    value=one.historical_paired_control(c.spec,c.store,identities)
    assert value['control']['state']=='unqualified' and value['admitted_for_new_sampling'] is False
    assert len(value['control']['pairs'])==4 and len(identities)==12
    failed=[row for pair in value['control']['pairs'] for samples in pair['samples'].values() for row in samples
            if row['relative_spread']>.10]
    assert len(failed)==7
    assert all(not direction['numerical_gain_leg'] for pair in value['control']['pairs'] for direction in pair['directions'])


@pytest.mark.parametrize('fault',['missing','mutated','driver'])
def test_historical_metadata_cannot_be_dropped_or_consistently_rehashed(historical_metadata,fault):
    c=historical_metadata
    rid=next(iter(PLAN['historical_records']))
    if fault=='driver': c.receipt['cells'][0]['pair_sha256']='0'*64
    else:
        original=c.store.get
        def get(name,kind=None):
            row=original(name,kind)
            if name==rid:
                if fault=='missing': return None
                row=copy.deepcopy(row); row['changed']=True
            return row
        c.store.get=get
    with pytest.raises(ValueError): one.historical_paired_control(c.spec,c.store,{})
