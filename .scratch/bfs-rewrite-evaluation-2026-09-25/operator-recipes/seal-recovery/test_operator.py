"""Bounded operator controls, created 2026-09-27 ET; no host dispatch."""
import importlib.util
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('supervision_operator',HERE/'operator.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)


def test_clock_uses_original_deadline_and_cleanup_reserve():
    start=datetime.fromisoformat('2026-09-27T00:00:00-04:00');end=(start+timedelta(seconds=90)).isoformat()
    assert op.remaining(end,30,start+timedelta(seconds=17))==43
    with pytest.raises(RuntimeError,match='exhausted'):op.remaining(end,30,start+timedelta(seconds=61))


def test_unresolved_config_rejects_before_any_host_action():
    with pytest.raises(RuntimeError,match='commit'):op.load_config(HERE/'config-template.json')


def test_fixed_paths_no_third_standard_proof():
    assert len(op.ROOTS)==5 and len(set(op.ROOTS))==5
    assert op.KINDS==('supplement','owned_cleanup','dx100_interruption')
    assert all('a7' in str(p) for p in op.ROOTS[:-1])


def test_environment_removes_injection_inputs(monkeypatch):
    for key in op.ENV_REMOVE:monkeypatch.setenv(key,'unexpected')
    env=op.environment()
    assert not set(op.ENV_REMOVE)&set(env)
    assert env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']=='1' and env['PYTHONNOUSERSITE']=='1'


def test_invocation_retains_isolation_and_literal_arguments():
    command=op.invocation({'python':'/exact/python'},Path('/exact/config'), 'scripts/bfs_linux_fixture.py',['owned_cleanup','--outer-started','timestamp'])
    assert command[:3]==['/exact/python','-I','-B']
    assert command[-3:]==['owned_cleanup','--outer-started','timestamp']
    assert command[4:7]==['invoke','/exact/config','scripts/bfs_linux_fixture.py']


def test_guard_rejects_untracked_import_file_before_git(monkeypatch,tmp_path):
    root=tmp_path/'runtime';root.mkdir();(root/'scripts').mkdir();(root/'scripts/__init__.py').write_text('raise RuntimeError()')
    m=tmp_path/'manifest.json';m.write_text(json.dumps({'commit':'a'*40,'files':{'tracked.py':{'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()}}}))
    monkeypatch.setattr(op.subprocess,'check_output',lambda *a,**kw:pytest.fail('git called before inventory rejection'))
    with pytest.raises(RuntimeError,match='runtime file changed'):op.guard({'runtime':str(root),'manifest':str(m),'manifest_sha256':op.sha(m),'commit':'a'*40})


def test_guard_rejects_symlink_before_import(tmp_path):
    root=tmp_path/'runtime';root.mkdir();(root/'evil').symlink_to('/tmp')
    m=tmp_path/'manifest.json';m.write_text(json.dumps({'commit':'a'*40,'files':{'tracked':{'bytes':0,'sha256':'0'*64}}}))
    with pytest.raises(RuntimeError,match='symlink'):op.guard({'runtime':str(root),'manifest':str(m),'manifest_sha256':op.sha(m),'commit':'a'*40})


def test_shell_unresolved_inputs_reject_before_clock_or_host_access():
    result=subprocess.run(['bash',str(HERE/'launch.sh')],env={'PATH':'/usr/bin:/bin'},capture_output=True)
    assert result.returncode!=0 and b'OPERATOR' in result.stderr


def test_free_lane_uses_real_lease_flock_and_rejects_live_lock(monkeypatch,tmp_path):
    helper=tmp_path/'helper';helper.write_text('helper')
    lock_script=tmp_path/'hostlock';lock_script.write_text('hostlock')
    c={'helper':str(helper),'helper_sha256':op.sha(helper),'hostlock':str(lock_script),
       'hostlock_sha256':op.sha(lock_script),'node':1,
       'helper_upstream_comparison':{'reviewed':True,'host_subtree_equal':True}}
    monkeypatch.setattr(op,'LEASE_ROOT',tmp_path)
    names=('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1')
    for name in names:
        (tmp_path/(name+'.lease')).touch()
        (tmp_path/(name+'.meta.json')).write_text(json.dumps({'state':'released'}))
    assert len(op.free_lane(c))==3
    with (tmp_path/'mbit10-evaluation-node1.lease').open('r') as stream:
        op.fcntl.flock(stream,op.fcntl.LOCK_EX|op.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError,match='disagree'):op.free_lane(c)
        (tmp_path/'mbit10-evaluation-node1.meta.json').write_text(json.dumps({'state':'held'}))
        with pytest.raises(RuntimeError,match='unavailable'):op.free_lane(c)
    (tmp_path/'mbit10-evaluation-node1.meta.json').write_text(json.dumps({'state':'released'}))
    assert not op.free_lane(c)['mbit10-evaluation-node1']['kernel_held']


def test_launch_passes_the_same_original_clock_to_outer_and_group():
    text=(HERE/'launch.sh').read_text()
    assert 'start+timedelta(seconds=600)' in text
    assert '"$CONFIG" "${CLOCK[0]}" "${CLOCK[1]}"' in text
    assert 'end-datetime.now(end.tzinfo)' in text
    assert '599s' not in text


@pytest.mark.parametrize('created',[False,True])
def test_failure_receipt_only_for_exclusively_created_group(monkeypatch,tmp_path,created):
    monkeypatch.setattr(op,'GROUP',tmp_path)
    monkeypatch.setattr(op,'load_config',lambda path:{'commit':'a'*40})
    monkeypatch.setattr(op.sys,'argv',['operator.py','run','config.json','begin','end'])
    def fail(c,config,start,end,ownership):
        ownership['created']=created
        raise ValueError('original failure')
    monkeypatch.setattr(op,'run',fail)
    with pytest.raises(ValueError,match='original failure'):op.main()
    assert (tmp_path/'operator-failure.json').exists()==created


def test_failed_receipt_persistence_preserves_original_error(monkeypatch,tmp_path):
    monkeypatch.setattr(op,'GROUP',tmp_path)
    monkeypatch.setattr(op,'load_config',lambda path:{'commit':'a'*40})
    monkeypatch.setattr(op.sys,'argv',['operator.py','run','config.json','begin','end'])
    def fail(c,config,start,end,ownership):
        ownership['created']=True
        raise ValueError('original failure')
    def denied(*args):raise OSError('disk full')
    monkeypatch.setattr(op,'run',fail);monkeypatch.setattr(op,'write',denied)
    with pytest.raises(ValueError,match='original failure'):op.main()
