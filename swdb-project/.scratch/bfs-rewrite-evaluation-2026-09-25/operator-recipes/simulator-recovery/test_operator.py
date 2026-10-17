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


@pytest.mark.parametrize('seconds',[39603,74426])
def test_schedule_never_restores_consumed_wall_time(seconds):
    end=datetime.fromisoformat('2026-09-27T09:14:09.851819-04:00')
    charges=[{'id':'consumed','elapsed_seconds':86400-seconds,'raw_bytes':123}]
    plan={'bounds':{'series_seconds':21600,'cleanup_seconds':30}}
    b=SimpleNamespace(preparation_charges=lambda _:charges)
    recovery=SimpleNamespace(hard_end=lambda _:end)
    latest=end-timedelta(seconds=21630)
    saved,clock=m.schedule(b,recovery,plan,latest)
    assert saved==charges and clock['latest_start']==latest.isoformat() and clock['absolute_end']==end.isoformat()
    with pytest.raises(ValueError,match='latest start'):
        m.schedule(b,recovery,plan,latest+timedelta(microseconds=1))


def test_operation_keeps_two_pristine_record_roots_and_original_supervisor():
    assert len(set(m.ROOTS.values()))==2
    source=P.read_text();tree=ast.parse(source)
    assert 'scripts/bfs_simulator_batch.py' in source and 'linux_proof_runtime' in source
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
