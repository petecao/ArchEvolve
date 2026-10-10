"""Local schedule and launch safety contracts; no host execution. 2026-09-27 ET."""
import importlib.util
from datetime import datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
import ast
import pytest

P=Path(__file__).with_name('operator.py')
spec=importlib.util.spec_from_file_location('simulator_recovery_operator',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


@pytest.mark.parametrize('seconds',[73226])
def test_schedule_never_restores_consumed_wall_time(seconds):
    end=datetime.fromisoformat('2026-09-27T20:16:17.225985-04:00')
    charges=[{'id':'consumed','elapsed_seconds':86400-seconds,'raw_bytes':123}]
    plan={'bounds':{'series_seconds':21600,'cleanup_seconds':30}}
    b=SimpleNamespace(preparation_charges=lambda _:charges)
    recovery=SimpleNamespace(hard_end=lambda _:end)
    latest=end-timedelta(seconds=21630)
    saved,clock=m.schedule(b,recovery,plan,latest)
    assert saved==charges and clock['latest_start']==latest.isoformat() and clock['absolute_end']==end.isoformat()
    with pytest.raises(ValueError,match='latest start'):
        m.schedule(b,recovery,plan,latest+timedelta(microseconds=1))


def test_operation_keeps_one_pristine_record_root_and_original_supervisor():
    assert set(m.ROOTS)=={'t16'}
    source=P.read_text();tree=ast.parse(source)
    assert 'scripts/bfs_simulator_batch.py' in source and "'linux_proof_runtime' not in fragment" in source
    assert not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in
                   {'Popen','kill','killpg','pidfd_send_signal'} for x in ast.walk(tree))
    assert 'os.execvpe(argv[0],argv' in source and "'--kill-after=30s'" in source
    assert "(current-start).total_seconds()<25" in source


def test_launch_captures_parent_before_subprocess_and_requires_exact_pins():
    shell=P.with_name('launch.sh').read_text()
    assert shell.index('PANE_PID=$BASHPID')<shell.index('TICKS=$(')
    for pin in ('OPERATOR_SHA','CONFIG_SHA','ADMISSION_SHA'):
        assert '${'+pin+':?' in shell
    assert '--pane-pid "$PANE_PID"' in shell and 'outer.exit' in shell


def test_only_fresh_exact_runtime_proof_is_accepted():
    source=P.read_text()
    assert "fragment['code_commit']==PIN" in source
    assert "fragment['runtime_sha256']==b.runtime_identity()" in source
    assert "c.get('proofgroup') == ref(GROUP_FINAL)" in source
    assert "'linux_proof_runtime':" not in source
    assert "kind+'-seal-recovery'" in source
    assert m.PIN=='923cf33b955104fdf96705b648933e7d486a3810'


def test_wrapper_dispatch_matches_new_plan_date():
    shell=P.with_name('launch.sh').read_text()
    assert 'bfs-${KIND}-seal-recovery-simulator-batch-20260927-a1.dispatch' in shell
    assert 'seal-recovery-simulator-batch-20260926' not in shell


def test_unpinned_runtime_and_t15_cannot_enter_setup(monkeypatch):
    with pytest.raises(ValueError,match='T16-only'):m.setup('t15',Path('/nonexistent'))
    monkeypatch.setattr(m,'PIN',None)
    with pytest.raises(ValueError,match='not pinned'):m.setup('t16',Path('/nonexistent'))


def test_template_cannot_admit_or_reuse_old_proof():
    import json
    c=json.loads(P.with_name('t16-config-template.json').read_text())
    assert c['commit']==m.PIN and c['manifest_sha256']==m.sha(P.with_name('runtime-manifest.json'))
    assert c['proofgroup'] is None
    assert c['node']==0 and 't16_seal_recovery' in c['runtime']
    shell=P.with_name('launch.sh').read_text()
    assert '[[ "$KIND" == t16 ]] || exit 64' in shell
    assert '"$KIND" == t15' not in shell
