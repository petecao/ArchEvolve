"""Fixed failed-supervision accounting and fresh supplement contracts. Updated 2026-09-27 ET."""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as XML

import pytest
from scripts import bfs_simulator_batch as batch, bfs_simulator_recovery as mod
from scripts import bfs_simulator_batch_terminal as terminal
from scripts import bfs_owned_execution as owned
from swdb import artifacts, yamlio, bfs_protocol
from test_bfs_simulator_batch import plan
from test_bfs_simulator_batch_admission import completed
from test_bfs_linux_fixture_audit import fixture as audit_fixture, write


def policy(key):
    return plan(key+'-supervision-recovery')


@pytest.mark.parametrize('key', ['t15','t16'])
def test_fixed_plans_preserve_science_and_hard_ends(key):
    value=policy(key);base=mod.base_plan(value)
    batch.validate_plan(value,key+'-supervision-recovery')
    assert value['bounds']==base['bounds']
    assert [{k:v for k,v in r.items() if k!='id'} for r in value['series']]==[
        {k:v for k,v in r.items() if k!='id'} for r in base['series']]
    for name in ('model_build','target','verifier','roi','threads','repetitions','warmups','verification_ticks','record_sha256'):
        assert value[name]==base[name]
    assert value['trace_transport']=='gem5-gzip.v1'
    assert mod.hard_end(value).isoformat()==mod.ENDS[key+'-supervision-recovery']
    assert len(value['accounting']['preparation_reservation']['supplement_testcases'])==42
    value['clock_policy']['absolute_end']='2026-09-28T12:00:00-04:00'
    with pytest.raises(ValueError,match='hard end'):mod.hard_end(value)


def test_flat_costs_retain_failed_a4_and_never_double_charge_t16_five_seconds(monkeypatch):
    prior=[{'id':'old','elapsed_seconds':2997,'raw_bytes':15322025984}]
    monkeypatch.setattr(mod,'failed_group',lambda *_:None)
    monkeypatch.setattr(batch,'preparation_charges',lambda _:copy.deepcopy(prior))
    a=mod.preparation_charges(policy('t15'))
    assert 43200-sum(r['elapsed_seconds'] for r in a)==39603
    assert 40*batch.GIB-sum(r['raw_bytes'] for r in a)==25480163328
    monkeypatch.setattr(mod,'failed_t16',lambda *_:[{'id':'prior','elapsed_seconds':253,'raw_bytes':1130987520},
        {'id':mod.OLD_T16,'elapsed_seconds':11121,'raw_bytes':658644992}])
    a=mod.preparation_charges(policy('t16'))
    assert 86400-sum(r['elapsed_seconds'] for r in a)==74426
    assert 60*batch.GIB-sum(r['raw_bytes'] for r in a)==60487393280


@pytest.fixture
def failed(tmp_path,monkeypatch):
    value=policy('t16');base=mod.base_plan(value);entry=value['accounting']['supervision_recovery']['failed_batch']
    runs=tmp_path/mod.OLD_T16;dispatch=Path(str(runs)+'.dispatch');folder=runs/(mod.OLD_T16+'.driver')
    folder.mkdir(parents=True);dispatch.mkdir()
    entry['storage_paths']=list(map(str,(runs,dispatch)))
    pane={'pid':1,'start_ticks':101};driver_id={'pid':2,'start_ticks':102}
    union=[{'pid':10000+i,'start_ticks':100+i} for i in range(941)]+[pane,driver_id,{'pid':3089858,'start_ticks':497039930}]
    outer='2026-09-26T20:20:30.225985-04:00';finish='2026-09-26T23:20:51.817090-04:00'
    ledger={'format':owned.FORMAT,'budget_seconds':30,'absolute_end':entry.get('absolute_end',mod.ENDS['t16-supervision-recovery']),
        'monotonic_end':10000,'created':outer,'creator':driver_id,'spent_seconds':20.94487111307685,
        'reservations':{'b3aac8d5d3bc45ca83bf59b152ce8b3b':{'pid':3089858,'seconds':5,'started':'2026-09-26T23:20:50.936598-04:00','purpose':'cleanup_or_finalization'}},
        'events':[{'pid':2,'purpose':'cleanup_or_finalization','seconds':1,'elapsed_seconds':20.94487111307685/117,
                   'started':outer,'finished':finish,'exceeded_grant':False} for _ in range(117)]}
    ledger_path=folder/'cleanup-ledger.json'
    driver={'id':mod.OLD_T16,'state':'failed','code_commit':entry['code_commit'],'plan':base,
        'reason':'ProcessLookupError: [Errno 3] No such process','outer_started':outer,'started':outer,
        'finished':finish,'outer_deadline':mod.ENDS['t16-supervision-recovery'],
        'process_observations':{'pane_identity':pane,'driver_identity':driver_id},
        'cleanup':{'state':'all_owned_descendants_absent','errors':[],'subreaper':True,'direct_reaped':True,
                   'checked_at':finish,'shared_budget':str(ledger_path)},
        'cleanup_budget':{'path':str(ledger_path),'binding':owned.SharedCleanup.binding_of(ledger),'budget_seconds':30},
        'preparation_charges':[{'id':'prior','elapsed_seconds':253,'raw_bytes':1130987520}]}
    audit={'id':mod.OLD_T16,'state':'failed','repository_commit':entry['code_commit'],'owned_processes':union,
        'lease_released':True,'complete_retained_identity_union':True,'cleanup_state':'terminal_no_live_owned_processes',
        'cleanup_budget_admissible':False,'lease_generation':332,'observed_at':'2026-09-26T23:24:46.556915-04:00','completed_samples':0}
    account={'admitted_cleanup_budget':False,'admitted_storage':False,'observed_at':'2026-09-26T23:25:50.293633-04:00'}
    lane={'socket_lane':{'host':'mbit10','job':mod.OLD_T16,'node':0,'lease_generation':332,'exit_code':1,
        'started_utc':'2026-09-27T00:20:30Z','ended_utc':'2026-09-27T03:20:52Z'}}
    evaluation={'outcome':{'state':'running','stage':'simulation','reason':None},'correctness':{'state':'unverified','checks':[]},'timing':[]}
    calls=[]
    monkeypatch.setattr(owned,'identity',lambda pid:calls.append(pid))
    monkeypatch.setattr(batch,'allocated_bytes',lambda _:658644992)
    monkeypatch.setattr(batch,'preparation_charges',lambda _:copy.deepcopy(driver['preparation_charges']))
    monkeypatch.setattr(batch,'now',lambda:datetime(2026,9,27,0,0,tzinfo=batch.ET))
    def seal():
        entry['ledger']=write(ledger_path,ledger)
        entry['driver']=write(folder/'driver.json',driver)
        audit['driver']=entry['driver'];audit['cleanup_ledger']=entry['ledger']
        audit['lane']=write(dispatch/'lane.json',lane);audit['outer_exit']=write(dispatch/'outer.exit',1)
        entry['evaluation']=write(tmp_path/'evaluation.yaml',evaluation);audit['evaluation']=entry['evaluation']
        entry['terminal']=write(dispatch/'terminal-validation.json',audit)
        account['driver']=entry['driver'];account['terminal']=entry['terminal']
        entry['accounting']=write(dispatch/'terminal-accounting.json',account)
        return value
    return SimpleNamespace(**locals())


def test_t16_cost_reader_keeps_original_strict_ledger_failure(failed):
    f=failed;rows=mod.failed_t16(f.seal(),f.base)
    assert rows[-1]=={'id':mod.OLD_T16,'elapsed_seconds':11121,'raw_bytes':658644992}
    assert len(f.calls)>=2*944
    with pytest.raises(ValueError,match='outstanding reservations'):
        terminal.validate_cleanup_ledger(f.entry['driver'],f.entry['ledger'],expected_run_id=mod.OLD_T16,
            expected_outer_start=f.outer,expected_deadline=f.driver['outer_deadline'],current=batch.now())


@pytest.mark.parametrize('fault',['settled','reservation-refund','wrong-owner','union-short','duplicate','live',
    'cleanup-promoted','storage-promoted','later-hardend','wall-refund','record-promoted','changed-record','grew',
    'new-error','other-plan','event-nan','event-exceeded','charge-refund','wrong-audit','wrong-lane'])
def test_failed_t16_exception_is_narrow_and_never_promotes(failed,monkeypatch,fault):
    f=failed
    if fault=='settled':f.ledger['reservations']={}
    elif fault=='reservation-refund':next(iter(f.ledger['reservations'].values()))['seconds']=4
    elif fault=='wrong-owner':f.audit['owned_processes'][-1]['pid']=3089859
    elif fault=='union-short':f.audit['owned_processes'].pop(0)
    elif fault=='duplicate':f.audit['owned_processes'][0]=f.audit['owned_processes'][1]
    elif fault=='live':monkeypatch.setattr(owned,'identity',lambda pid:{'start_ticks':497039930,'state':'S','rss_bytes':0} if pid==3089858 else None)
    elif fault=='cleanup-promoted':f.audit['cleanup_budget_admissible']=True
    elif fault=='storage-promoted':f.account['admitted_storage']=True
    elif fault=='later-hardend':f.driver['outer_deadline']='2026-09-28T20:16:17.225985-04:00'
    elif fault=='wall-refund':f.entry['elapsed_seconds']-=5
    elif fault=='record-promoted':f.evaluation['outcome']['state']='complete'
    elif fault=='grew':monkeypatch.setattr(batch,'allocated_bytes',lambda _:658644993)
    elif fault=='new-error':f.driver['cleanup']['errors']=['permission']
    elif fault=='other-plan':f.driver['plan']=copy.deepcopy(f.base);f.driver['plan']['threads']=1
    elif fault=='event-nan':f.ledger['events'][0]['elapsed_seconds']=float('nan')
    elif fault=='event-exceeded':f.ledger['events'][0]['exceeded_grant']=True
    elif fault=='charge-refund':f.entry['conservative_cleanup_seconds']-=5
    elif fault=='wrong-lane':f.lane['socket_lane']['lease_generation']=333
    value=f.seal()
    if fault=='changed-record':Path(f.entry['evaluation']['path']).write_text('{}')
    elif fault=='wrong-audit':f.entry['driver']['sha256']='f'*64
    with pytest.raises(ValueError):mod.failed_t16(value,f.base)


def test_gzip_transport_keeps_frozen_configuration_and_instrumentation(completed,monkeypatch):
    f=completed;p=f.primaries[0];candidate=f.store.get(p['candidate']);workload=f.store.get(f.row['workload'])
    workload['definition']['family']='fixture'
    monkeypatch.setattr(bfs_protocol,'_simulation_build',lambda *a,**k:None)
    monkeypatch.setattr(bfs_protocol,'verify_immutable',lambda v:v['identity_sha256'])
    monkeypatch.setattr(f.store,'application_of',lambda _:{'id':'app'},raising=False)
    monkeypatch.setattr(bfs_protocol,'workload_representation',lambda *_:{'representation':{'path':'/graph','sha256':'e'*64}})
    request=copy.deepcopy(p['request']);request['workload']={'id':workload['id'],'source':workload['definition']['sources'][request['protocol_trial']['source_position']],'representation':{'path':'/graph','sha256':'e'*64}}
    args=dict(actual_target=f.policy['target'],actual_configuration=f.row['configuration'],actual_build=p['build'],
        actual_instrumentation={},actual_threads=f.policy['threads'],actual_roi=f.policy['roi'],actual_verifier='synthetic.verifier')
    first=bfs_protocol.validate_protocol_for_simulation(f.store,request,candidate,**args)
    request['verification']={'trace_transport':'gem5-gzip.v1'}
    second=bfs_protocol.validate_protocol_for_simulation(f.store,request,candidate,**args)
    assert first['context']['backend_configuration']==second['context']['backend_configuration']==f.row['configuration']
    assert first['context']['instrumentation']==second['context']['instrumentation']=={}
    args['actual_configuration']={**f.row['configuration'],'threads':999}
    with pytest.raises(Exception,match='target/configuration'):bfs_protocol.validate_protocol_for_simulation(f.store,request,candidate,**args)


@pytest.fixture
def failed_group(tmp_path,monkeypatch):
    value=policy('t15');base=mod.base_plan(value);entry=value['accounting']['supervision_recovery']['failed_proof_group']
    old=base['accounting']['preparation_reservation'];roots=[tmp_path/str(i) for i in range(5)]
    for p in roots:p.mkdir()
    old['storage_paths']=list(map(str,roots))
    pre={'id':mod.OLD_GROUP,'code_commit':entry['code_commit'],'storage_paths':old['storage_paths'],
         'observed_at':'2026-09-26T23:17:12.749940-04:00'}
    observation={'id':mod.OLD_GROUP,'state':'failed','proof_group_admissible':False,'code_commit':entry['code_commit'],
        'reservation_seconds':600,'reservation_bytes':2*batch.GIB,'original_started':pre['observed_at'],
        'original_deadline':'2026-09-26T23:27:12.749940-04:00','observed_at':'2026-09-26T23:22:10.661627-04:00','fixtures':{}}
    for index,name in enumerate(('owned_cleanup','dx100_interruption')):
        pane={'pid':10+index,'start_ticks':100+index};rid=old['selections'][name]
        d={'id':rid,'state':'complete','process_observations':{'pane_identity':pane}}
        refs={'driver':write(roots[index]/'driver.json',d),'audit':write(roots[index]/'audit.json',{'returncode':index}),
              'proof':None,'terminal_audit':None}
        observation['fixtures'][name]={'id':rid,'refs':refs,'owned_union':[pane],'audit_returncode':index,'current_owned_processes_closed':True}
    calls=[];monkeypatch.setattr(owned,'identity',lambda pid:calls.append(pid))
    monkeypatch.setattr(batch,'allocated_bytes',lambda _:1548288)
    monkeypatch.setattr(batch,'now',lambda:datetime(2026,9,27,tzinfo=batch.ET))
    def seal():
        observation['group_preflight']=write(roots[4]/'preflight.json',pre)
        entry['observation']=write(roots[4]/'failed.json',observation)
        return value
    return SimpleNamespace(**locals())


def test_failed_a4_reads_both_closure_passes_without_promoting_pending(failed_group):
    f=failed_group;mod.failed_group(f.seal(),f.base)
    assert f.calls==[10,10,11,11]
    assert f.observation['fixtures']['dx100_interruption']['refs']['proof'] is None


@pytest.mark.parametrize('fault',['passed','refunded','changed-root','late','promoted','extra-selection','live','grew','modified-artifact'])
def test_failed_a4_cannot_be_refunded_or_rewritten(failed_group,monkeypatch,fault):
    f=failed_group
    if fault=='passed':f.observation['proof_group_admissible']=True
    elif fault=='refunded':f.old['elapsed_seconds']=599
    elif fault=='changed-root':f.pre['storage_paths']=[]
    elif fault=='late':f.entry['closed_at']='2026-09-26T23:28:00-04:00'
    elif fault=='promoted':write(f.roots[1]/'proof.json',{'state':'passed'})
    elif fault=='extra-selection':f.observation['fixtures']['extra']={}
    elif fault=='live':monkeypatch.setattr(owned,'identity',lambda pid:{'start_ticks':100,'state':'S','rss_bytes':0} if pid==10 else None)
    elif fault=='grew':monkeypatch.setattr(batch,'allocated_bytes',lambda _:1548289)
    value=f.seal()
    if fault=='modified-artifact':(f.roots[0]/'driver.json').write_text('{}')
    with pytest.raises(ValueError):mod.failed_group(value,f.base)


@pytest.fixture
def supplement(tmp_path,monkeypatch):
    from scripts import bfs_linux_fixture_audit as auditmod
    f=audit_fixture(tmp_path);old=f['folder'];folder=old.with_name('supplement');old.rename(folder)
    def relocate(v):
        if isinstance(v,str):return v.replace(str(old),str(folder))
        if isinstance(v,list):return [relocate(x) for x in v]
        if isinstance(v,dict):return {k:relocate(x) for k,x in v.items()}
        return v
    d=relocate(f['data']);ledger=relocate(f['ledger']);lane=f['lane'];group=tmp_path
    value=policy('t15');reservation=value['accounting']['preparation_reservation'];reservation['storage_paths'][-1]=str(group)
    approved={'code_commit':'a'*40,'runtime_sha256':{'actual':'fixture-pinned-runtime'},'python':f['py'],
              'preparation_reservation':{'finished':f['at'](30)}}
    actual=approved['preparation_reservation'];actual['preflight']=write(group/'preflight.json',{'observed_at':f['at'](-5)})
    command=[f['py']['path'],'-m','pytest',*mod.SUPPLEMENT_SELECTORS,'-q','-p','no:cacheprovider',
             '--junitxml='+str(folder/'junit.xml'),'--basetemp='+str(folder/'pytest')]
    xml=XML.Element('testsuite')
    for name in reservation['supplement_testcases']:XML.SubElement(xml,'testcase',name=name)
    (folder/'junit.xml').write_bytes(XML.tostring(xml))
    d.update(id=mod.GROUP_ID+'.supplement',runtime_sha256=approved['runtime_sha256'],command=command,work_deadline=f['at'](60))
    d['stages'][0]['command']=command;lane['socket_lane']['job']=d['id']
    v={'format':'swdb.bfs.supervision-supplement.v1','state':'passed','code_commit':'a'*40,'runtime_sha256':approved['runtime_sha256'],
       'returncode':0,'started':d['started'],'finished':d['finished'],'audited_at':f['at'](24),'command':command,'selectors':mod.SUPPLEMENT_SELECTORS}
    a={'id':d['id'],'state':'complete','code_commit':'a'*40,'lease_released':True,'complete_retained_identity_union':True,
       'cleanup_state':'terminal_and_reaped','lease_generation':10,'observed_at':f['at'](22),
       'owned_processes':[f[n] for n in ('driver','pane','helper','child','adopted')]}
    a['process_observations']=[[{'pid':r['pid'],'start_ticks':r['start_ticks'],'state':'absent','current_identity':None} for r in a['owned_processes']] for _ in range(2)]
    snapshot={name:{'kernel_held':False,'metadata':{'state':'released'}} for name in
              ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1')}
    snapshot['mbit10-evaluation-node0']['metadata'].update(lease={'generation':10,'host':'mbit10','lease_name':'mbit10-evaluation-node0','acquired_at':f['at'](0)},released_at=f['at'](19))
    a['lease_observations']=[copy.deepcopy(snapshot),copy.deepcopy(snapshot)];a['observation_times']=[f['at'](20),f['at'](21)]
    monkeypatch.setattr(owned,'identity',lambda _:None)
    def seal():
        ledger_ref=write(folder/'cleanup-ledger.json',ledger)
        d['cleanup_budget']['binding']=owned.SharedCleanup.binding_of(ledger)
        d['resource_samples']=auditmod.reference(folder/'resources.jsonl')
        v['stdout']=auditmod.reference(Path(d['stages'][0]['output']));v['stderr']=auditmod.reference(Path(d['stages'][0]['stderr']))
        v['junit']=auditmod.reference(folder/'junit.xml')
        d['stages'][0]['stdout_sha256']=v['stdout']['sha256'];d['stages'][0]['stderr_sha256']=v['stderr']['sha256']
        a['driver']=write(folder/'driver.json',d);a['lane']=write(folder/'lane.json',lane);a['outer_exit']=write(folder/'outer.exit',0)
        a['cleanup_ledger']={'ledger':ledger_ref,'binding':owned.SharedCleanup.binding_of(ledger),'spent_seconds':ledger['spent_seconds'],'events':len(ledger['events'])}
        v['terminal_audit']=write(folder/'terminal-validation.json',a)
        actual['supplement']=write(group/'supplement.readback.json',v)
        return value,approved
    return SimpleNamespace(**locals())


def test_supplement_reopens_full_ledger_resources_and_union(supplement):
    mod.validate_supplement(*supplement.seal())


@pytest.mark.parametrize('fault',['reservation','over-grant','sum','wrong-creator','wrong-binding','missing-adopted',
    'missing-middle','no-snapshots','held','observation-omits','wrong-command','work-late','finish-late','lane-late','nonzero','wrong-runtime','skipped','omitted','duplicate',
    'rss','output','final-output','gap','missing-driver','unbound-output','wrong-ledger-path','live'])
def test_supplement_rejects_each_real_contract_boundary(supplement,monkeypatch,fault):
    f=supplement
    if fault=='reservation':f.ledger['reservations']={'pending':{'seconds':5}}
    elif fault=='over-grant':f.ledger['events'][0]['elapsed_seconds']=6
    elif fault=='sum':f.ledger['spent_seconds']=2
    elif fault=='wrong-creator':f.ledger['creator']['start_ticks']=9999
    elif fault=='missing-adopted':f.a['owned_processes'].pop()
    elif fault=='missing-middle':f.d['process_observations']['ancestry'].pop(1);f.a['owned_processes'].pop(2)
    elif fault=='no-snapshots':f.a.pop('lease_observations')
    elif fault=='held':f.a['lease_observations'][0]['mbit10-evaluation-node0']['kernel_held']=True
    elif fault=='observation-omits':f.a['process_observations'][1].pop()
    elif fault=='wrong-command':f.v['command']=['true']
    elif fault=='work-late':f.d['stages'][0]['timeout_s']=61
    elif fault=='finish-late':f.v['finished']=f.f['at'](91)
    elif fault=='lane-late':f.lane['socket_lane']['ended_utc']=f.f['at'](91)
    elif fault=='nonzero':f.d['stages'][0]['returncode']=1
    elif fault=='wrong-runtime':f.d['runtime_sha256']={'other':'runtime'}
    elif fault in ('skipped','omitted','duplicate'):
        path=f.folder/'junit.xml';xml=XML.fromstring(path.read_bytes())
        if fault=='skipped':XML.SubElement(xml[0],'skipped')
        elif fault=='omitted':xml.remove(xml[0])
        else:xml.append(copy.deepcopy(xml[0]))
        path.write_bytes(XML.tostring(xml))
    elif fault in ('rss','output','gap','missing-driver'):
        path=f.folder/'resources.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
        if fault=='rss':rows[0]['rss_bytes']=513*1024**2
        elif fault=='output':rows[0]['output_bytes']=513*1024**2
        elif fault=='gap':rows[0]['sampled_at']=f.f['at'](40)
        else:rows[0]['processes']=rows[0]['processes'][1:];rows[0]['rss_bytes']=4096
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    elif fault=='final-output':monkeypatch.setattr(batch,'allocated_bytes',lambda _:513*1024**2)
    elif fault=='live':monkeypatch.setattr(owned,'identity',lambda pid:{'start_ticks':1004,'state':'S','rss_bytes':0} if pid==104 else None)
    value,approved=f.seal()
    if fault=='wrong-binding':f.a['cleanup_ledger']['binding']='bad';f.v['terminal_audit']=write(f.folder/'terminal-validation.json',f.a);approved['preparation_reservation']['supplement']=write(f.group/'supplement.readback.json',f.v)
    elif fault=='unbound-output':(f.folder/'pytest.stdout').write_text('changed')
    elif fault=='wrong-ledger-path':f.a['cleanup_ledger']['ledger']['path']=str(f.folder/'other.json');f.v['terminal_audit']=write(f.folder/'terminal-validation.json',f.a);approved['preparation_reservation']['supplement']=write(f.group/'supplement.readback.json',f.v)
    reason={'rss':'arithmetic|bound','output':'sampled output','gap':'sample gap','missing-driver':'omits driver','missing-middle':'ancestry'}.get(fault)
    with pytest.raises(ValueError,match=reason):mod.validate_supplement(value,approved)


def test_supplement_cleanup_in_original_reserve_does_not_shorten_work_allowance(supplement):
    f=supplement
    # Public run_stage includes cleanup in finished; its separate work-return
    # deadline check is source-bound; finalization may spend the30 reserve.
    f.d['stages'][0]['finished']=f.f['at'](65);f.d['stages'][0]['timeout_s']=58
    f.d['finished']=f.v['finished']=f.f['at'](70);f.a['observed_at']=f.f['at'](72);f.v['audited_at']=f.f['at'](74)
    f.a['observation_times']=[f.f['at'](71),f.f['at'](72)]
    for snapshot in f.a['lease_observations']:snapshot['mbit10-evaluation-node0']['metadata']['released_at']=f.f['at'](71)
    f.actual['finished']=f.f['at'](75);f.lane['socket_lane']['ended_utc']=f.f['at'](71)
    path=f.folder/'resources.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
    for tick in (35,55,69):rows.append({**copy.deepcopy(rows[-1]),'sampled_at':f.f['at'](tick)})
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    mod.validate_supplement(*f.seal())


@pytest.mark.parametrize('held',[False,True])
def test_supplement_historical_release_accepts_independent_successor(supplement,held):
    f=supplement
    for snapshot in f.a['lease_observations']:
        row=snapshot['mbit10-evaluation-node0'];row['kernel_held']=held
        row['metadata'].update(state='held' if held else 'released',released_at=None if held else f.f['at'](20))
        row['metadata']['lease'].update(generation=11,acquired_at=f.f['at'](19))
    mod.validate_supplement(*f.seal())


@pytest.mark.parametrize('fault',['stale-generation','same-held','before-end','wrong-kernel','missing-legacy','live-observed','early-observation'])
def test_supplement_requires_both_real_release_and_process_passes(supplement,fault):
    f=supplement;row=f.a['lease_observations'][1]['mbit10-evaluation-node0']
    if fault=='stale-generation':row['metadata']['lease']['generation']=9
    elif fault=='same-held':row['kernel_held']=True;row['metadata']['state']='held'
    elif fault=='before-end':row['metadata']['released_at']=f.f['at'](18)
    elif fault=='wrong-kernel':row['kernel_held']=True
    elif fault=='missing-legacy':f.a['lease_observations'][0].pop('mbit10-evaluation')
    elif fault=='live-observed':f.a['process_observations'][1][0]['state']='S'
    elif fault=='early-observation':f.a['observation_times'][0]=f.f['at'](18)
    with pytest.raises(ValueError):mod.validate_supplement(*f.seal())


# 2026-09-27: exercise the real producer against retained contract fixtures.
@pytest.mark.parametrize('fault',[None,'live','ledger','junit','runtime','repeat'])
def test_supplement_producer_seals_only_independently_closed_exact_evidence(supplement,monkeypatch,fault):
    from scripts import bfs_supervision_supplement as producer
    from scripts import bfs_linux_fixture_audit as auditmod
    f=supplement
    f.d.update(kind='supervision_supplement',standard_proof_kind=False)
    module=f.folder/'pytest-module.py';module.write_text('# fixed test fixture\n')
    f.d['pytest']['module']=auditmod.reference(module)
    stderr=f.folder/'pytest.stderr';stderr.write_bytes(Path(f.d['stages'][0]['stderr']).read_bytes())
    f.d['stages'][0]['stderr']=str(stderr)
    value,approved=f.seal()
    # The fixture initially materializes consumer inputs; remove only these
    # test-owned output paths so the producer must independently recreate them.
    (f.folder/'terminal-validation.json').unlink();(f.group/'supplement.readback.json').unlink()
    (f.folder/'proof.pending.json').unlink()
    monkeypatch.setattr(producer,'GROUP',f.group);monkeypatch.setattr(producer,'FOLDER',f.folder)
    monkeypatch.setattr(producer.runner,'campaign_runtime',lambda code:f.d['runtime'])
    monkeypatch.setattr(producer.runner,'pytest_identity',lambda:f.d['pytest'])
    monkeypatch.setattr(batch,'runtime_identity',lambda:approved['runtime_sha256'])
    monkeypatch.setattr(owned,'stamp',lambda:f.f['at'](25))
    if fault=='runtime':monkeypatch.setattr(batch,'runtime_identity',lambda:{'wrong':'runtime'})
    if fault=='ledger':
        f.ledger['reservations']={'open':{'pid':123,'seconds':5}}
        write(f.folder/'cleanup-ledger.json',f.ledger)
    if fault=='junit':(f.folder/'junit.xml').write_text('<testsuite/>')
    if fault=='repeat':write(f.folder/'audit-attempt.json',{'state':'prior_failed_attempt'})
    inspect=(lambda pid: {'pid':pid,'start_ticks':1,'state':'S','rss_bytes':1024}) if fault=='live' else lambda pid:None
    # Match retained identity start ticks so live work cannot masquerade as PID reuse.
    if fault=='live':
        lookup={r['pid']:r for r in f.a['owned_processes']}
        inspect=lambda pid:{**lookup[pid],'state':'S','rss_bytes':1024}
    invoke=lambda:producer.close(value,'a'*40,approved['preparation_reservation']['preflight'],f.a['lane'],f.a['outer_exit'],
        reader=auditmod.Reader(__import__('time').monotonic()+60),inspect=inspect,
        leases=lambda *args:copy.deepcopy(f.a['lease_observations'][0]))
    if fault:
        with pytest.raises((ValueError,FileExistsError)):invoke()
        assert not (f.group/'supplement.readback.json').exists()
    else:
        result=invoke();approved['preparation_reservation']['supplement']=result
        mod.validate_supplement(value,approved)
        produced=json.loads((f.folder/'terminal-validation.json').read_text())
        assert len(produced['process_observations'])==len(produced['lease_observations'])==2
        assert produced['complete_retained_identity_union'] is True
        assert not (f.folder/'proof.pending.json').exists()
        with pytest.raises(ValueError,match='already attempted'):invoke()


# 2026-09-27: preserve actual 8cb proof provenance through consumer-only repairs.
@pytest.mark.parametrize('different_binary',[False,True])
def test_supplement_canonical_python_alias_preserves_actual_argv(supplement,different_binary):
    f=supplement
    alias=f.group/'venv-python3'
    if different_binary:alias.write_bytes(b'not the pinned executable')
    else:alias.symlink_to(Path(f.approved['python']['path']))
    f.d['command'][0]=str(alias);f.d['stages'][0]['command'][0]=str(alias);f.v['command'][0]=str(alias)
    if different_binary:
        with pytest.raises(ValueError,match='exact lease-reader cases'):mod.validate_supplement(*f.seal())
    else:
        mod.validate_supplement(*f.seal())
        assert f.v['command'][0]==str(alias)  # No rewriting of retained evidence.


def declared_proof_admission():
    frozen=json.loads((Path(__file__).parent/'fixtures/bfs_proof_runtime_8cbfee6.json').read_text())
    original=frozen['runtime_sha256']
    assert frozen['code_commit']==mod.PROOF_COMMIT and len(original)==157
    assert frozen['runtime_sha256_digest']==artifacts.digest(original)==mod.PROOF_MAP_DIGEST
    # Construct an admissible synthetic current map from the frozen evidence;
    # unrelated main-branch changes must not relabel that historical proof.
    actual=batch.runtime_identity()
    current={**original,**{name:actual[name] for name in mod.PROOF_CONSUMERS}}
    return {'code_commit':'b'*40,'runtime_sha256':current,
            'linux_proof_runtime':{'code_commit':mod.PROOF_COMMIT,'runtime_sha256':original}}


def test_fixed_proof_runtime_is_explicit_and_does_not_relabel_current_execution():
    admission=declared_proof_admission();before=copy.deepcopy(admission)
    actual=mod.proof_admission(admission)
    assert actual['code_commit']==mod.PROOF_COMMIT
    assert artifacts.digest(actual['runtime_sha256'])==mod.PROOF_MAP_DIGEST
    assert admission==before and admission['code_commit']=='b'*40
    assert mod.proof_admission({'code_commit':'a'*40})=={'code_commit':'a'*40}


@pytest.mark.parametrize('fault',['old-map','old-commit','missing-entry','new-entry',
    'scripts/bfs_owned_execution.py','scripts/bfs_owned_rss.py','scripts/bfs_storage.py',
    'scripts/bfs_linux_fixture.py','scripts/bfs_linux_fixture_audit.py','scripts/bfs_supervision_supplement.py',
    'tests/test_bfs_owned_execution.py','tests/test_bfs_owned_rss.py','tests/test_bfs_linux_fixture_audit.py'])
def test_proof_runtime_never_waives_tested_primitive_or_inventory_changes(fault):
    admission=declared_proof_admission()
    if fault=='old-map':admission['linux_proof_runtime']['runtime_sha256']['scripts/bfs_owned_execution.py']='0'*64
    elif fault=='old-commit':admission['linux_proof_runtime']['code_commit']='c'*40
    elif fault=='missing-entry':del admission['runtime_sha256']['scripts/bfs_owned_execution.py']
    elif fault=='new-entry':admission['runtime_sha256']['scripts/unreviewed.py']='0'*64
    else:admission['runtime_sha256'][fault]='0'*64
    with pytest.raises(ValueError):mod.proof_admission(admission)


def test_new_plans_cannot_omit_explicit_proof_provenance():
    with pytest.raises(ValueError,match='explicit fixed Linux proof provenance'):
        batch.validate_preparation_reservation(policy('t15'),{})
    for key in ('t15','t16'):
        assert policy(key)['linux_proof_provenance']==mod.PROOF_PROVENANCE


def test_actual_changed_t17_dependency_cannot_reuse_the_old_proof():
    admission=declared_proof_admission()
    name='scripts/bfs_t17_diagnostic_build.py'
    actual=batch.runtime_identity()[name]
    assert actual != admission['linux_proof_runtime']['runtime_sha256'][name]
    admission['runtime_sha256'][name]=actual
    with pytest.raises(ValueError,match='tested primitive or proof dependency'):
        mod.proof_admission(admission)
