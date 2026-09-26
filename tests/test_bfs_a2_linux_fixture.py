"""A2-specific bounded fixture-runner orchestration contracts. Created 2026-09-26 ET."""
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
from scripts import bfs_a2_linux_fixture as runner


def write_junit(path,names,fault=None):
    root=XML.Element('testsuite')
    for name in names:
        case=XML.SubElement(root,'testcase',name=name)
        if fault in ('failure','error','skipped'): XML.SubElement(case,fault)
    path.write_bytes(XML.tostring(root))


@pytest.mark.parametrize('kind',runner.SELECTIONS)
def test_exact_two_commands_preserve_venv_and_fixed_unskipped_selection(tmp_path,kind):
    argv=runner.command(kind,tmp_path)
    assert argv[:3]==[sys.executable,'-m','pytest']
    assert argv[3:3+len(runner.SELECTIONS[kind][1])]==runner.SELECTIONS[kind][1]
    assert '-p' in argv and 'no:cacheprovider' in argv
    assert '--junitxml='+str(tmp_path/'junit.xml') in argv
    assert len(runner.SELECTIONS[kind][2])==2


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
    runtime={'files':{'supervisor':'0'*64}}
    tested_root=tmp_path/'tested';tested_root.mkdir()
    tested_runtime={'repository_commit':runner.TESTED_COMMIT,'root':str(tested_root),
        'files':{'historical':'1'*64},'python':runner.reference(Path(sys.executable).resolve()),
        'python_version':sys.version,'a2_plan':{},'project_config':{},'test_files':{}}
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
    metadata_calls=[]
    def metadata_argv():
        metadata_calls.append(True)
        value=dict(tested_runtime)
        if fault['kind']=='runtime_drift' and len(metadata_calls)==2:value['python_version']='changed'
        return [sys.executable,'-c','import json;print('+repr(json.dumps(value))+')']
    monkeypatch.setattr(runner,'runtime_command',metadata_argv)
    monkeypatch.setattr(runner,'tested_inventory',lambda root:{'fixture_tested':True})
    monkeypatch.setattr(subprocess,'Popen',popen)
    def run():
        begin=datetime.now(runner.own.ET)
        return runner.execute(kind,tmp_path/'run',begin,begin+timedelta(seconds=90),
            time.monotonic()+90,'a'*40,runtime,tested_root,{'pid':2,'start_ticks':1},0,pytest_runtime)
    return SimpleNamespace(run=run,children=children,owners=owners,fault=fault,folder=tmp_path/'run')


@pytest.mark.parametrize('fault',[None,'child','cleanup','missing_junit','runtime_drift'])
def test_real_child_paths_reap_and_preserve_failure_receipts(execution,fault):
    execution.fault['kind']=fault
    if fault:
        with pytest.raises((ValueError,PermissionError)):execution.run()
    else:result=execution.run();assert result['state']=='complete'
    assert len(execution.children)==(3 if fault in (None,'runtime_drift') else 1 if fault=='cleanup' else 2)
    for child in execution.children:
        assert child.returncode is not None
        with pytest.raises(ChildProcessError):os.waitpid(child.pid,os.WNOHANG)
    value=json.loads((execution.folder/'driver.json').read_text())
    assert value['state']==('failed' if fault else 'complete')
    assert value['cleanup_verified'] is False
    assert value['process_observations']['owned_processes']
    assert (execution.folder/'proof.pending.json').exists() is (fault is None)
    if fault is None:
        pending=json.loads((execution.folder/'proof.pending.json').read_text())
        assert pending['code_commit']==runner.TESTED_COMMIT and pending['supervisor_commit']=='a'*40
        assert pending['runtime']['files']=={'historical':'1'*64}
        assert pending['supervisor_runtime']=={'files':{'supervisor':'0'*64}}
        assert set(pending['tested_runtime_snapshots'])=={'before','after'}
        for phase, ref in pending['tested_runtime_snapshots'].items():
            assert ref['path']==str(execution.folder/('runtime-'+phase+'.json'))
            assert ref==runner.reference(ref['path'])
        assert len(value['stages'])==3 and all(s['returncode']==0 for s in value['stages'])
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
    assert execution.children[1].returncode==3


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
    monkeypatch.setattr(sys,'argv',['runner','owned_cleanup','--expected-supervisor-commit','a'*40,'--tested-checkout',str(tmp_path/'tested'),
        '--python-sha256','0'*64,'--pytest-version','fixture','--pytest-sha256','0'*64,
        '--outer-started',begin.isoformat(),'--outer-deadline',(begin+timedelta(seconds=91)).isoformat(),
        '--pane-pid','1','--pane-start-ticks','1','--lane','0'])
    with pytest.raises(ValueError,match='90-second'):runner.main()
    assert not (tmp_path/'run').exists()


def test_public_a2_admission_rejects_pending_fixture_proof(monkeypatch):
    from scripts import bfs_dx100_coverage_a2 as a2
    pending={'format':'swdb.bfs.linux-fixture.v1','kind':'owned_cleanup','host':'mbit10',
        'platform':'linux','code_commit':runner.TESTED_COMMIT,
        'evidence_kind':'contract_fixture','state':'tests_passed_cleanup_unverified','returncode':0}
    monkeypatch.setattr(a2,'read',lambda ref:pending)
    with pytest.raises(ValueError,match='Linux fixture identity'):
        a2.validate_linux_proof({},'owned_cleanup',runner.TESTED_COMMIT,datetime.now(runner.own.ET),{})


@pytest.mark.parametrize('fault',['same_root','outside','wrong_commit'])
def test_tested_checkout_is_separate_fixed_historical_identity(monkeypatch,fault):
    root = runner.ROOT if fault=='same_root' else Path('/tmp/outside') if fault=='outside' else Path('/data1/yanruj/tested')
    calls=[]
    def runtime(commit,root):
        calls.append((commit,root));raise ValueError('wrong actual commit')
    monkeypatch.setattr(runner,'campaign_runtime',runtime)
    monkeypatch.setattr(runner,'validate_root_entries',lambda *args:[])
    with pytest.raises(ValueError):runner.tested_inventory(root)
    assert calls == ([(runner.TESTED_COMMIT,root)] if fault=='wrong_commit' else [])


def test_runtime_output_is_bounded_and_exact(tmp_path):
    path=tmp_path/'runtime.json';root=tmp_path/'tested'
    value={'repository_commit':runner.TESTED_COMMIT,'root':str(root),'files':{},
        'python':runner.reference(Path(sys.executable).resolve()),'python_version':sys.version,
        'a2_plan':{},'project_config':{},'test_files':{}}
    path.write_text(json.dumps(value));assert runner.read_runtime(path,root)==value
    value['repository_commit']='a'*40;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='exact tested'):runner.read_runtime(path,root)
    path.write_bytes(b' '* (runner.RUNTIME_OUTPUT_BYTES+1))
    with pytest.raises(ValueError,match='exceeded4MiB'):runner.read_runtime(path,root)


@pytest.mark.parametrize('shadow', ['pytest.py', 'pytest', 'json.py'])
def test_real_git_root_inventory_rejects_ignored_import_shadows(tmp_path, shadow):
    root=tmp_path/'checkout';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="fixture"\nversion="0"\n')
    (root/'.gitignore').write_text('*.py\npytest/\n')
    subprocess.run(['git','init','-q',str(root)],check=True,timeout=5)
    subprocess.run(['git','add','pyproject.toml','.gitignore'],cwd=root,check=True,timeout=5)
    subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','-qm','explicit synthetic fixture'],cwd=root,check=True,timeout=5)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=5).strip()
    assert runner.validate_root_entries(root,commit)==['.git','.gitignore','pyproject.toml']
    if shadow=='pytest':
        (root/shadow).mkdir();(root/shadow/'__init__.py').write_text('raise RuntimeError("untrusted")\n')
    else:(root/shadow).write_text('raise RuntimeError("untrusted")\n')
    assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=root,text=True)
    with pytest.raises(ValueError,match='untracked import'):
        runner.validate_root_entries(root,commit)
