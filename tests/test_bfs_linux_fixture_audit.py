"""Exact-byte fixture admission and independent process closure. Dated 2026-09-26 ET."""
from datetime import datetime,timedelta
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as XML

import pytest
from scripts import bfs_linux_fixture_audit as mod


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value)+'\n')
    return mod.reference(path)


def fixture(tmp_path,route='standard',kind='owned_cleanup'):
    runner=mod.a2 if route=='a2' else mod.standard
    begin=datetime.fromisoformat('2026-09-26T12:00:00-04:00');end=begin+timedelta(seconds=90)
    at=lambda seconds:(begin+timedelta(seconds=seconds)).isoformat()
    folder=tmp_path/'run';folder.mkdir()
    driver={'pid':101,'parent_pid':102,'start_ticks':1001,'state':'S','rss_bytes':4096}
    pane={'pid':103,'parent_pid':1,'start_ticks':1003,'state':'S','rss_bytes':4096}
    helper={'pid':102,'parent_pid':103,'start_ticks':1002,'state':'S','rss_bytes':4096}
    child={'pid':104,'parent_pid':101,'start_ticks':1004,'state':'R','rss_bytes':4096}
    adopted={'pid':105,'parent_pid':101,'start_ticks':1005,'state':'R','rss_bytes':4096}
    source=tmp_path/'runtime';source.mkdir();py=mod.reference(Path(sys.executable).resolve())
    runtime={'root':str(source),'commit':'a'*40,'files':{},'python':py,'python_version':sys.version}
    ledger_path=folder/'cleanup-ledger.json'
    ledger={'format':mod.own.FORMAT,'budget_seconds':30,'absolute_end':at(90),'monotonic_end':10000,
        'created':at(1),'creator':driver,'spent_seconds':1.0,'reservations':{},
        'events':[{'pid':101,'purpose':'cleanup_or_finalization','seconds':5,'elapsed_seconds':1.0,
                   'started':at(15),'finished':at(16),'exceeded_grant':False}]}
    ledger_ref=write(ledger_path,ledger)
    cleanup={'state':'all_owned_descendants_absent','errors':[],'subreaper':True,'direct_reaped':True,
             'shared_budget':str(ledger_path),'checked_at':at(15),'observed':[adopted]}
    command=runner.command(kind,folder)
    stages=[]
    for index in range(3 if route=='a2' else 1):
        argv=command if route=='standard' or index==1 else runner.runtime_command()
        output=folder/('pytest.stdout' if argv==command else ('runtime-before.json' if index==0 else 'runtime-after.json'))
        output.write_text('{}\n');err=folder/(str(index)+'.stderr');err.write_text('')
        stages.append({'command':argv,'started':at(2+index*4),'finished':at(5+index*4),'state':'complete',
            'returncode':0,'timeout_s':3,'identity':{**child,'pid':104+index*2,'start_ticks':1004+index*2},
            'cleanup':cleanup,'output':str(output),'stdout_sha256':mod.reference(output)['sha256'],
            'stderr':str(err),'stderr_sha256':mod.reference(err)['sha256']})
    xml=XML.Element('testsuite')
    for name in sorted(runner.SELECTIONS[kind][2]):XML.SubElement(xml,'testcase',name=name)
    (folder/'junit.xml').write_bytes(XML.tostring(xml))
    samples=[]
    for tick in (1,8,17):
        rows=[{**row,'rss_pages':1} for row in (driver,child)]
        samples.append({'sampled_at':at(tick),'rss_bytes':8192,'processes':rows,'page_size_bytes':4096,
                        'rss_source':mod.own.RSS_SOURCE,'output_bytes':4096,
                        'lane':{'leases':{'mbit10-evaluation-node0':{'metadata':{'state':'held',
                          'lease':{'generation':10,'host':'mbit10','lease_name':'mbit10-evaluation-node0'}}}}}})
    (folder/'resources.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in samples))
    data={'id':runner.SELECTIONS[kind][0],'kind':kind,'state':'complete','returncode':0,
        'code_commit':mod.a2.TESTED_COMMIT if route=='a2' else 'a'*40,
        'started':at(0),'outer_deadline':at(90),'finished':at(18),'command':command,'stages':stages,
        'evidence_kind':'contract_fixture','cleanup_verified':False,'automatic_retry_allowed':False,
        'bounds':{'outer_seconds':90,'work_seconds':60,'cleanup_seconds':30,'sampled_rss_bytes':mod.LIMIT,'output_bytes':mod.LIMIT},
        'python_environment':runner.PYTHON_INPUTS,'runtime':runtime,'pytest':{'version':'fixture'},
        'testcases':sorted(runner.SELECTIONS[kind][2]),'process_observations':{'driver_identity':driver,
            'pane_identity':pane,'ancestry':[driver,helper,pane],'owned_processes':[driver,child]},
        'cleanup':cleanup,'cleanup_budget':{'path':str(ledger_path),'binding':mod.own.SharedCleanup.binding_of(ledger),'budget_seconds':30},
        'resource_samples':mod.reference(folder/'resources.jsonl')}
    pending={'format':'swdb.bfs.linux-fixture.v1','kind':kind,'host':'mbit10','platform':'linux',
        'state':'tests_passed_cleanup_unverified','returncode':0,'code_commit':data['code_commit'],
        'started':at(0),'finished':at(18),'evidence_kind':'contract_fixture','independent_cleanup_verified':False,
        'command':command,'stdout':mod.reference(folder/'pytest.stdout'),'junit':mod.reference(folder/'junit.xml'),
        'python_environment':runner.PYTHON_INPUTS,'pytest':data['pytest']}
    if route=='a2':
        data['supervisor_commit']='a'*40;data['supervisor_runtime']=runtime
        data['tested_runtime_snapshots']={key:mod.reference(folder/('runtime-'+key+'.json')) for key in ('before','after')}
    lane={'socket_lane':{'host':'mbit10','node':0,'lease_name':'mbit10-evaluation-node0',
        'lease_generation':10,'started_utc':at(0),'ended_utc':at(19),'exit_code':0}}
    exit_path=tmp_path/'outer.exit';exit_path.write_text('0\n')
    refs={'lane':write(tmp_path/'lane.json',lane),'exit':mod.reference(exit_path),'ledger':ledger_ref}
    def seal_pending():
        pending['driver']=write(folder/'driver.json',data)
        refs['pending']=write(folder/'proof.pending.json',pending)
    seal_pending()
    def run(inspect=lambda pid:None,leases=None,check_runtime=lambda *args:runtime):
        return mod.audit(route,kind,refs['pending'],refs['lane'],refs['exit'],refs['ledger'],'a'*40,0,10,
            reader=mod.Reader(time.monotonic()+60),inspect=inspect,
            leases=leases or (lambda *args:{'mbit10-evaluation-node0':{'state':'released','generation':10}}),
            check_runtime=check_runtime)
    return locals()


@pytest.mark.parametrize('route,kind',[('standard',key) for key in mod.standard.SELECTIONS]+[('a2',key) for key in mod.a2.SELECTIONS])
def test_all_five_fixed_routes_reopen_and_seal_pending_immutably(tmp_path,route,kind):
    f=fixture(tmp_path,route,kind);before=(f['folder']/'proof.pending.json').read_bytes()
    result,pending=f['run']();assert result['state']=='passed'
    identities={mod.identity(row) for row in result['owned_processes']}
    assert (105,1005) in identities and all(mod.identity(row['identity']) in identities for row in f['data']['stages'])
    ref=mod.seal(result,pending,f['folder'],mod.Reader(time.monotonic()+60))
    proof=json.loads(Path(ref['path']).read_text())
    assert proof['state']=='passed' and proof['pending']==f['refs']['pending']
    assert proof['terminal_audit']==mod.reference(f['folder']/'terminal-audit.json')
    assert proof['started']==pending['started'] and proof['finished']==pending['finished']
    assert (f['folder']/'proof.pending.json').read_bytes()==before
    with pytest.raises(ValueError,match='overwrite'):mod.seal(result,pending,f['folder'],mod.Reader(time.monotonic()+60))


@pytest.mark.parametrize('fault',['driver_failed','pending_passed','outer_nonzero','lane_nonzero','wrong_generation',
    'late_driver','late_helper','wrong_testset','stage_nonzero','stage_missing','stage_cleanup_error',
    'unsettled_ledger','ledger_exceeded','ledger_sum','changed_stdout','changed_driver','missing_ancestor',
    'output_exceeded','rss_exceeded','resource_gap','missing_driver_sample'])
def test_exact_failure_paths_never_seal_a_proof(tmp_path,fault):
    f=fixture(tmp_path);d,p,l=f['data'],f['pending'],f['lane']
    if fault=='driver_failed':d['state']='failed'
    elif fault=='pending_passed':p['state']='passed'
    elif fault=='outer_nonzero':f['exit_path'].write_text('1\n');f['refs']['exit']=mod.reference(f['exit_path'])
    elif fault=='lane_nonzero':l['socket_lane']['exit_code']=1
    elif fault=='wrong_generation':l['socket_lane']['lease_generation']=11
    elif fault=='late_driver':d['finished']=f['at'](91);p['finished']=d['finished']
    elif fault=='late_helper':l['socket_lane']['ended_utc']=f['at'](92)
    elif fault=='wrong_testset':(f['folder']/'junit.xml').write_text('<testsuite><testcase name="wrong"/></testsuite>');p['junit']=mod.reference(f['folder']/'junit.xml')
    elif fault=='stage_nonzero':d['stages'][0]['returncode']=1
    elif fault=='stage_missing':d['stages']=[]
    elif fault=='stage_cleanup_error':d['stages'][0]['cleanup']['errors']=['denied']
    elif fault.startswith('ledger_') or fault=='unsettled_ledger':
        value=f['ledger']
        if fault=='unsettled_ledger':value['reservations']={'pending':{'seconds':1}}
        elif fault=='ledger_exceeded':value['events'][0]['exceeded_grant']=True
        else:value['spent_seconds']=2
        f['refs']['ledger']=write(f['ledger_path'],value)
    elif fault=='missing_ancestor':d['process_observations']['ancestry'].pop()
    elif fault in ('output_exceeded','rss_exceeded','resource_gap','missing_driver_sample'):
        rows=f['samples']
        if fault=='output_exceeded':rows[0]['output_bytes']=mod.LIMIT+1
        elif fault=='rss_exceeded':rows[0]['processes'][0].update(rss_pages=200000,rss_bytes=819200000);rows[0]['rss_bytes']=819204096
        elif fault=='resource_gap':rows[-1]['sampled_at']=f['at'](60)
        else:rows[0]['processes']=rows[0]['processes'][1:];rows[0]['rss_bytes']=4096
        (f['folder']/'resources.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
        d['resource_samples']=mod.reference(f['folder']/'resources.jsonl')
    f['refs']['lane']=write(tmp_path/'lane.json',l);f['seal_pending']()
    if fault=='changed_stdout':(f['folder']/'pytest.stdout').write_text('changed')
    elif fault=='changed_driver':(f['folder']/'driver.json').write_text('{}')
    with pytest.raises((ValueError,KeyError)):f['run']()
    assert not (f['folder']/'proof.json').exists()


@pytest.mark.parametrize('mode',['live_driver','live_adopted','zombie_child','unknown','pid_reused','pane_zombie'])
def test_exact_process_identity_and_only_captured_zero_rss_pane_exception(tmp_path,mode):
    f=fixture(tmp_path)
    def inspect(pid):
        target=101 if mode=='live_driver' else 103 if mode=='pane_zombie' else 105
        if pid!=target:return None
        if mode=='unknown':raise PermissionError('procfs unavailable')
        return {'pid':pid,'start_ticks':1000+pid-100+(1 if mode=='pid_reused' else 0),
                'state':'Z' if mode in ('zombie_child','pane_zombie') else 'R','rss_bytes':0}
    if mode in ('pid_reused','pane_zombie'):
        result,_=f['run'](inspect=inspect)
        assert result['cleanup_state']==('terminal_no_live_owned_processes' if mode=='pane_zombie' else 'terminal_and_reaped')
    else:
        with pytest.raises((ValueError,PermissionError)):f['run'](inspect=inspect)


def test_second_observation_rejects_changed_lease_and_artifacts(tmp_path):
    f=fixture(tmp_path);calls=[]
    def leases(*args):calls.append(1);return {'mbit10-evaluation-node0':{'generation':10+len(calls)}}
    with pytest.raises(ValueError,match='lease changed'):f['run'](leases=leases)


def test_real_live_child_cannot_be_mistaken_for_absent(tmp_path):
    if sys.platform!='linux':pytest.skip('actual procfs identity requires Linux')
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(5)'])
    try:
        row=mod.own.identity(child.pid)
        with pytest.raises(ValueError,match='process remains'):mod.process_snapshot({mod.identity(row):row},(1,1))
    finally:child.terminate();child.wait(timeout=3)


def test_real_file_lock_and_exact_generation(tmp_path):
    f=fixture(tmp_path);lease_root=tmp_path/'leases';lease_root.mkdir()
    for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
        write(lease_root/(name+'.meta.json'),{'state':'released','released_at':f['at'](19),
            'lease':{'generation':10,'host':'mbit10','lease_name':name,'acquired_at':f['at'](0)}})
        (lease_root/(name+'.lease')).write_text('')
    result=mod.lease_snapshot(0,10,f['lane']['socket_lane'],f['begin'],f['end'],root=lease_root)
    assert all(not row['kernel_held'] for row in result.values())
    with pytest.raises(ValueError,match='generation'):mod.lease_snapshot(0,11,f['lane']['socket_lane'],f['begin'],f['end'],root=lease_root)
    with (lease_root/'mbit10-evaluation-node0.lease').open() as stream:
        mod.fcntl.flock(stream,mod.fcntl.LOCK_EX|mod.fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='kernel lock'):mod.lease_snapshot(0,10,f['lane']['socket_lane'],f['begin'],f['end'],root=lease_root)


def test_post_exit_deadline_is_separate_and_pending_survives_expiry(tmp_path):
    f=fixture(tmp_path);result,pending=f['run']()
    with pytest.raises(ValueError,match='audit deadline'):mod.seal(result,pending,f['folder'],mod.Reader(time.monotonic()-1))
    assert (f['folder']/'proof.pending.json').exists() and not (f['folder']/'proof.json').exists()


def test_publication_overrun_withdraws_only_new_link(tmp_path,monkeypatch):
    f=fixture(tmp_path);result,pending=f['run']();reader=mod.Reader(time.monotonic()+60)
    original=reader.check
    def check():
        if (f['folder']/'proof.json').exists():raise ValueError('post-exit audit deadline exceeded')
        original()
    monkeypatch.setattr(reader,'check',check)
    with pytest.raises(ValueError,match='deadline'):mod.seal(result,pending,f['folder'],reader)
    assert not (f['folder']/'proof.json').exists()
    assert (f['folder']/'proof.pending.json').exists() and (f['folder']/'terminal-audit.json').exists()


@pytest.mark.parametrize('fault',['expired','raises'])
def test_final_proof_reference_is_inside_withdrawal_and_deadline_guard(tmp_path,monkeypatch,fault):
    f=fixture(tmp_path);result,pending=f['run']();reader=mod.Reader(time.monotonic()+60)
    original=mod.reference
    def reference(path):
        if Path(path).name=='proof.json':
            if fault=='raises':raise OSError('injected final proof hash failure')
            reader.deadline=time.monotonic()-1
        return original(path)
    monkeypatch.setattr(mod,'reference',reference)
    with pytest.raises((ValueError,OSError)):mod.seal(result,pending,f['folder'],reader)
    assert not (f['folder']/'proof.json').exists()
    assert (f['folder']/'proof.pending.json').exists() and (f['folder']/'proof.sealed-staging.json').exists()


@pytest.mark.parametrize('fault',['runtime','pytest','subset','supervisor_pin','a2_snapshot','a2_file','python'])
def test_actual_runtime_validator_rejects_changed_identity(tmp_path,monkeypatch,fault):
    route='a2' if fault in ('supervisor_pin','a2_snapshot','a2_file','python') else 'standard'
    f=fixture(tmp_path,route);data,pending=f['data'],f['pending'];runtime=f['runtime']
    monkeypatch.setattr(mod,'ROOT',f['source'])
    module=f['source']/'pytest.py';module.write_text('# explicit fixture\n')
    data['pytest']=pending['pytest']={'version':'fixture','module':mod.reference(module)}
    monkeypatch.setattr(mod.standard,'pytest_identity',lambda:data['pytest'])
    current=copy.deepcopy(runtime)
    pending['runtime_sha256']={}
    monkeypatch.setattr(mod.standard,'CLEANUP_RUNTIME',())
    for name in ('swdb/dx100.py','tests/test_dx100_interruption.py','tests/test_bfs_owned_execution.py'):
        runtime['files'][name]='0'*64;current['files'][name]='0'*64;pending['runtime_sha256'][name]='0'*64
    tested=f['source']/'tested';tested.mkdir()
    if route=='a2':
        path=tested/'actual.py';path.write_text('# tested fixture\n')
        plan=tested/'plan.json';plan.write_text('{}')
        configuration=tested/'pyproject.toml';configuration.write_text('')
        before={'repository_commit':mod.a2.TESTED_COMMIT,'root':str(tested),
            'files':{'actual.py':mod.reference(path)},'test_files':{},'python':runtime['python'],
            'python_version':sys.version,'a2_plan':mod.reference(plan),'project_config':mod.reference(configuration)}
        refs={key:write(f['folder']/('runtime-'+key+'.json'),before) for key in ('before','after')}
        data.update(tested_root=str(tested),runtime=before,tested_runtime_snapshots=refs)
        pending.update(runtime=before,supervisor_commit='a'*40,supervisor_runtime=runtime,tested_runtime_snapshots=refs)
        tested_current={'files':{'actual.py':mod.reference(path)['sha256'],'pyproject.toml':mod.reference(configuration)['sha256']}}
    def inventory(code,root):return current if root==f['source'] else tested_current
    monkeypatch.setattr(mod,'campaign_runtime',inventory)
    if fault=='runtime':current['python_version']='changed'
    elif fault=='pytest':monkeypatch.setattr(mod.standard,'pytest_identity',lambda:{'version':'different'})
    elif fault=='subset':pending['runtime_sha256']={}
    elif fault=='supervisor_pin':pending['supervisor_commit']='b'*40
    elif fault=='a2_snapshot':refs['after']=write(f['folder']/'runtime-after.json',{})
    elif fault=='a2_file':tested_current['files']['actual.py']='f'*64
    elif fault=='python':before['python_version']='changed';refs.update({key:write(f['folder']/('runtime-'+key+'.json'),before) for key in ('before','after')})
    with pytest.raises(ValueError):mod.runtime_check(mod.Reader(time.monotonic()+60),data,pending,route,'a'*40)
