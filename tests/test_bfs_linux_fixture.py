"""Bounded fixture-runner orchestration contracts. Created 2026-09-26 ET."""
from datetime import datetime,timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import xml.etree.ElementTree as XML

import pytest
from scripts import bfs_linux_fixture as runner


def write_junit(path,names,fault=None):
    root=XML.Element('testsuite')
    for name in names:
        case=XML.SubElement(root,'testcase',name=name)
        if fault in ('failure','error','skipped'): XML.SubElement(case,fault)
    path.write_bytes(XML.tostring(root))


@pytest.mark.parametrize('kind',runner.SELECTIONS)
def test_exact_three_commands_preserve_venv_and_fixed_unskipped_selection(tmp_path,kind):
    argv=runner.command(kind,tmp_path)
    assert argv[:3]==[sys.executable,'-m','pytest']
    assert argv[3:3+len(runner.SELECTIONS[kind][1])]==runner.SELECTIONS[kind][1]
    assert '-p' in argv and 'no:cacheprovider' in argv
    assert '--junitxml='+str(tmp_path/'junit.xml') in argv
    assert len(runner.SELECTIONS[kind][2])==(4 if kind=='owned_cleanup' else 2)


@pytest.mark.parametrize('fault',[None,'failure','error','skipped','duplicate','missing','extra'])
def test_junit_requires_exact_successful_case_set(tmp_path,fault):
    names=sorted(runner.SELECTIONS['owned_cleanup'][2]);expected=set(names)
    if fault=='duplicate':names.append(names[0])
    elif fault=='missing':names.pop()
    elif fault=='extra':names.append('unrequested')
    p=tmp_path/'junit.xml';write_junit(p,names,fault)
    if fault:
        with pytest.raises(ValueError):runner.junit_cases(p,expected)
    else:assert set(runner.junit_cases(p,expected))==expected


def test_child_environment_removes_python_and_pytest_injection(tmp_path,monkeypatch):
    for key in runner.PYTHON_INPUTS:monkeypatch.setenv(key,'injected')
    result=runner.child_environment(tmp_path)
    for key,value in runner.PYTHON_INPUTS.items():assert result.get(key)==value
    assert result['TMPDIR']==str(tmp_path/'tmp')
    assert os.environ['PYTHONPATH']=='injected'  # Parent environment is not modified.


@pytest.mark.parametrize('key',['PYTEST_PLUGINS','PYTHONOPTIMIZE'])
def test_child_environment_removes_explicit_plugins_and_optimization(tmp_path,monkeypatch,key):
    monkeypatch.setenv(key,'injected')
    assert key not in runner.child_environment(tmp_path)


def test_optimized_fixture_supervisor_is_rejected_before_imports(tmp_path):
    result=subprocess.run([sys.executable,'-O',str(Path(runner.__file__).resolve()),'--help'],
        env=runner.child_environment(tmp_path),capture_output=True,text=True,timeout=10)
    assert result.returncode != 0
    assert 'assertions enabled' in result.stderr


@pytest.fixture
def execution(tmp_path,monkeypatch):
    """Real subprocess and shared ledger; explicit synthetic procfs/host seams."""
    children=[];owners=[];fault={'kind':None};kind='owned_cleanup'
    names=sorted(runner.SELECTIONS[kind][2])
    runtime={'files':{name:'0'*64 for name in (*runner.CLEANUP_RUNTIME,'swdb/dx100.py',
                    'tests/test_dx100_interruption.py','tests/test_bfs_owned_execution.py')}}
    pytest_runtime={'version':'fixture','module':{'path':'/fixture/pytest','sha256':'0'*64}}
    def identity(pid):return {'pid':pid,'parent_pid':os.getppid(),'start_ticks':1,'state':'S','rss_bytes':4096}
    class Owner:
        def __init__(self,budget):self.budget=budget;self.history={};owners.append(self)
        def remember(self,row):self.history[(row['pid'],row['start_ticks'])]=row
        def sample(self):
            row={**identity(os.getpid()),'rss_pages':1};self.remember(row)
            return {'sampled_at':runner.own.stamp(),'processes':[row],'rss_bytes':4096,
                    'rss_source':runner.own.RSS_SOURCE,'page_size_bytes':4096}
        def finish(self,child=None,direct=None):
            if child is not None:child.wait(timeout=1)
            if fault['kind']=='cleanup':raise PermissionError('fixture cleanup denied')
            return {'state':'all_owned_descendants_absent','errors':[], 'direct_reaped':True,'observed':[]}
    real_popen=subprocess.Popen
    def popen(*args,**kwargs):
        child=real_popen(*args,**kwargs)
        if args[0][0:2]==[sys.executable,'-c']:children.append(child)
        return child
    def argv(selected,folder):
        code='import pathlib,time,sys;time.sleep(.03);'
        if fault['kind']!='missing_junit':
            xml=XML.Element('testsuite')
            for name in names:XML.SubElement(xml,'testcase',name=name)
            code+='pathlib.Path('+repr(str(folder/'junit.xml'))+').write_bytes('+repr(XML.tostring(xml))+');'
        code+='print("explicit orchestration fixture");sys.exit('+str(3 if fault['kind']=='child' else 0)+')'
        return [sys.executable,'-c',code]
    monkeypatch.setattr(runner.own,'Owned',Owner)
    monkeypatch.setattr(runner.own,'identity',identity)
    monkeypatch.setattr(runner.own,'ancestry',lambda driver,pane:[driver,pane])
    monkeypatch.setattr(runner,'Store',lambda path:SimpleNamespace(get=lambda key:{}))
    monkeypatch.setattr(runner,'lease_observation',lambda *args:{'fixture_only':True})
    monkeypatch.setattr(runner.os,'statvfs',lambda path:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    monkeypatch.setattr(runner,'campaign_runtime',lambda code:runtime)
    monkeypatch.setattr(runner,'pytest_identity',lambda:pytest_runtime)
    monkeypatch.setattr(runner,'command',argv)
    monkeypatch.setattr(subprocess,'Popen',popen)
    def run():
        begin=datetime.now(runner.own.ET)
        return runner.execute(kind,tmp_path/'run',begin,begin+timedelta(seconds=90),
            time.monotonic()+90,'a'*40,runtime,{'pid':2,'start_ticks':1},0,pytest_runtime)
    return SimpleNamespace(run=run,children=children,owners=owners,fault=fault,folder=tmp_path/'run')


@pytest.mark.parametrize('fault',[None,'child','cleanup','missing_junit'])
def test_real_child_paths_reap_and_preserve_failure_receipts(execution,fault):
    execution.fault['kind']=fault
    if fault:
        with pytest.raises((ValueError,PermissionError)):execution.run()
    else:result=execution.run();assert result['state']=='complete'
    assert len(execution.children)==1 and execution.children[0].returncode is not None
    with pytest.raises(ChildProcessError):os.waitpid(execution.children[0].pid,os.WNOHANG)
    value=json.loads((execution.folder/'driver.json').read_text())
    assert value['state']==('failed' if fault else 'complete')
    assert value['cleanup_verified'] is False
    assert value['process_observations']['owned_processes']
    assert (execution.folder/'proof.pending.json').exists() is (fault is None)
    budget=json.loads((execution.folder/'cleanup-ledger.json').read_text())
    assert not budget['reservations'] and budget['spent_seconds']<=30


def test_original_child_failure_survives_later_finalization_error(execution,monkeypatch):
    execution.fault['kind']='child'
    original=runner.reference
    def broken(path):
        if Path(path).name=='resources.jsonl':raise OSError('injected final hashing failure')
        return original(path)
    monkeypatch.setattr(runner,'reference',broken)
    with pytest.raises(ValueError,match='public stage exited 3'):execution.run()
    value=json.loads((execution.folder/'driver.json').read_text())
    assert 'public stage exited 3' in value['reason']
    assert 'injected final hashing failure' in value['finalization_error']
    assert execution.children[0].returncode==3


def test_post_proof_storage_failure_leaves_pending_unaccepted(execution,monkeypatch):
    original=runner.allocated_bytes
    def used(paths):
        if (execution.folder/'proof.pending.json').exists():return runner.LIMIT_BYTES+1
        return original(paths)
    monkeypatch.setattr(runner,'allocated_bytes',used)
    with pytest.raises(ValueError,match='proof publication'):execution.run()
    value=json.loads((execution.folder/'driver.json').read_text())
    proof=json.loads((execution.folder/'proof.pending.json').read_text())
    assert value['state']=='failed' and proof['state']=='tests_passed_cleanup_unverified'
    assert not (execution.folder/'proof.json').exists()
    assert proof['independent_cleanup_verified'] is False


def test_original_clock_rejects_before_any_fixture_child(tmp_path,monkeypatch):
    begin=datetime.now(runner.own.ET)
    monkeypatch.setattr(sys,'argv',['runner','owned_cleanup','--expected-commit','a'*40,
        '--python-sha256','0'*64,'--pytest-version','fixture','--pytest-sha256','0'*64,
        '--outer-started',begin.isoformat(),'--outer-deadline',(begin+timedelta(seconds=91)).isoformat(),
        '--pane-pid','1','--pane-start-ticks','1','--lane','0'])
    with pytest.raises(ValueError,match='90-second'):runner.main()
    assert not (tmp_path/'run').exists()


def test_public_simulator_admission_rejects_pending_fixture_proof(monkeypatch):
    from scripts import bfs_simulator_batch as batch
    names=(*batch.CLEANUP_RUNTIME,'swdb/dx100.py','tests/test_dx100_interruption.py','tests/test_bfs_owned_execution.py')
    runtime={name:'0'*64 for name in names}
    admission={'linux_cleanup_tests':[{},{}],'code_commit':'a'*40,'runtime_sha256':runtime}
    pending={'format':'swdb.bfs.linux-fixture.v1','kind':'owned_cleanup','host':'mbit10',
        'platform':'linux','code_commit':'a'*40,'runtime_sha256':runtime,
        'evidence_kind':'contract_fixture','state':'tests_passed_cleanup_unverified','returncode':0}
    monkeypatch.setattr(batch,'read_reference',lambda ref:pending)
    with pytest.raises(ValueError,match='Linux fixture admission'):batch.validate_cleanup_tests(admission)


def test_public_native_admission_rejects_pending_fixture_proof(tmp_path):
    from test_bfs_native_execution import proof_fixture
    from scripts import bfs_native_campaign as campaign
    admission,value,_=proof_fixture(tmp_path)
    value['state']='tests_passed_cleanup_unverified'
    path=tmp_path/'proof.pending.json';path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='exact Linux'):campaign.validate_linux_proof(campaign.reference(path),admission)
