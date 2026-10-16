"""Public CLI controls for native environment-inspection errors, 2026-10-15 ET."""
import json
from pathlib import Path
import subprocess
import sys

import psutil
import pytest


RUNNER = Path(__file__).with_name('counted_verifier.py')
NATIVE_ERROR = '<built-in function proc_environ> returned a result with an exception set'


@pytest.mark.parametrize('chain_kind', ['none', 'cause', 'context'])
def test_transient_native_environ_error_recovers_on_the_same_live_identity(tmp_path, chain_kind):
    """Inject the retained C-extension error at the actual public CLI seam."""
    lock = tmp_path / 'private.lock'
    output = tmp_path / 'inspection.log'
    identity_file = tmp_path / 'owned.json'
    wrapper = tmp_path / 'controlled_runner.py'
    if chain_kind == 'none':
        fault = f'   raise SystemError({NATIVE_ERROR!r})\n'
    else:
        suffix = ' from cause' if chain_kind == 'cause' else ''
        fault = ('   try: raise PermissionError(13,"private-cause-fixture-never-persist")\n'
                 + f'   except PermissionError as cause: raise SystemError({NATIVE_ERROR!r}){suffix}\n')
    wrapper.write_text(
        'import json,sys,time\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal=V.psutil.Process.environ\nfirst=[None]\n'
        + 'def environ(self):\n'
        + f' p=Path({str(identity_file)!r})\n'
        + ' if p.exists() and self.pid==json.loads(p.read_text())["pid"]:\n'
        + '  first[0]=time.monotonic() if first[0] is None else first[0]\n'
        + '  if time.monotonic()-first[0]<.15:\n'
        + fault
        + ' return original(self)\n'
        + 'V.psutil.Process.environ=environ\nraise SystemExit(V.main())\n'
    )
    child = (
        'import json,os,time,psutil;from pathlib import Path;'
        + f'Path({str(identity_file)!r}).write_text(json.dumps({{"pid":os.getpid(),"birth":psutil.Process().create_time()}}));'
        + 'time.sleep(.7)'
    )
    try:
        result = subprocess.run(
            [sys.executable, str(wrapper), '--lock', str(lock), '--log', str(output),
             '--cap-gb', '8', '--timeout', '2', '--', sys.executable, '-c', child],
            capture_output=True, text=True, timeout=8,
        )
        report_text = Path(str(output) + '.summary.json').read_text()
        report = json.loads(report_text)
        assert result.returncode == 0, report['error']
        assert report['error'] is None and report['unconfirmed_children'] == []
        assert not lock.exists()
        assert any(e['outcome'] == 'recovered' for e in report['inspection_events'])
        native = [e for e in report['inspection_events'] if e.get('exception', {}).get('type') == 'SystemError']
        assert native and all(e['operation'] == e['requested_operation'] == 'environ' for e in native)
        assert all(e['expected_birth'] == e['observed_birth'] and e['identity_state'] == 'live' for e in native)
        assert all(e['outcome'] == 'inspection-error' and e['stage'] == 'supervision' for e in native)
        assert any(e['retry_elapsed_s'] >= .12 for e in native)
        assert all(e['traceback'] for e in native)
        chain = native[0]['exception_chain']
        assert any(x['type'] == 'PermissionError' for x in chain) == (chain_kind != 'none')
        if chain_kind != 'none':
            assert chain[1]['relation'] == chain_kind and chain[1]['errno'] == 13
        assert not report['timed_out'] and not report['killed_by_watchdog']
        assert 'private-cause-fixture-never-persist' not in report_text + result.stdout + result.stderr
    finally:
        if identity_file.exists():
            identity = json.loads(identity_file.read_text())
            try:
                process = psutil.Process(identity['pid'])
                if process.create_time() == identity['birth']:
                    process.kill()
                    process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass


@pytest.mark.parametrize('mode', ['unknown-native', 'other-error', 'identity', 'status'])
def test_only_the_exact_requested_native_environ_error_can_retry(tmp_path, mode):
    lock = tmp_path / 'private.lock'
    output = tmp_path / 'inspection.log'
    identity_file = tmp_path / 'owned.json'
    wrapper = tmp_path / 'controlled_runner.py'
    secret = 'private-unexpected-exception-payload-never-persist'
    if mode in {'unknown-native', 'other-error'}:
        kind = 'SystemError' if mode == 'unknown-native' else 'RuntimeError'
        injection = (
            'def environ(self):\n'
            + f' if self.pid==target():raise {kind}({secret!r})\n'
            + ' return original_env(self)\n'
            + 'V.psutil.Process.environ=environ\n'
        )
        expected_operation, expected_requested = 'environ', 'environ'
    elif mode == 'identity':
        injection = (
            'def environ(self):\n'
            + ' if self.pid==target():changed[0]=True\n'
            + ' return original_env(self)\n'
            + 'def birth(self):\n'
            + f' if changed[0] and self.pid==target():raise SystemError({NATIVE_ERROR!r})\n'
            + ' return original_birth(self)\n'
            + 'V.psutil.Process.environ=environ\nV.psutil.Process.create_time=birth\n'
        )
        expected_operation, expected_requested = 'identity_after.create_time', 'environ'
    else:
        injection = (
            'def status(self):\n'
            + f' if self.pid==target():raise SystemError({NATIVE_ERROR!r})\n'
            + ' return original_status(self)\n'
            + 'V.psutil.Process.status=status\n'
        )
        expected_operation, expected_requested = 'status', 'status'
    wrapper.write_text(
        'import json,sys\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\nchanged=[False]\n'
        + 'original_env=V.psutil.Process.environ\noriginal_birth=V.psutil.Process.create_time\n'
        + 'original_status=V.psutil.Process.status\n'
        + 'def target():\n'
        + f' p=Path({str(identity_file)!r})\n'
        + ' return json.loads(p.read_text())["pid"] if p.exists() else None\n'
        + injection + 'raise SystemExit(V.main())\n'
    )
    child = (
        'import json,os,time,psutil;from pathlib import Path;'
        + f'Path({str(identity_file)!r}).write_text(json.dumps({{"pid":os.getpid(),"birth":psutil.Process().create_time()}}));'
        + 'time.sleep(2)'
    )
    try:
        result = subprocess.run(
            [sys.executable, str(wrapper), '--lock', str(lock), '--log', str(output),
             '--cap-gb', '8', '--timeout', '3', '--', sys.executable, '-c', child],
            capture_output=True, text=True, timeout=8,
        )
        text = Path(str(output) + '.summary.json').read_text()
        report = json.loads(text)
        failure = report['primary_inspection_failure']
        assert result.returncode != 0 and report['unconfirmed_children'] and lock.exists()
        assert failure['operation'] == expected_operation
        assert failure['requested_operation'] == expected_requested
        assert failure['outcome'] == 'inspection-failed' and failure['attempt'] == 1
        assert failure['identity_state'] == 'unknown' and failure['traceback']
        assert not any(e['outcome'] in {'inspection-error', 'recovered'} for e in report['inspection_events'])
        assert secret not in text + result.stdout + result.stderr
        assert report['cleanup_inspection_failure']['stage'] == 'cleanup'
        if mode == 'identity':
            # The snapshot birth cannot be independently revalidated, so the
            # guard must neither declare absence nor signal that numeric PID.
            identity = json.loads(identity_file.read_text())
            process = psutil.Process(identity['pid'])
            assert process.create_time() == identity['birth']
            assert process.status() not in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}
    finally:
        if identity_file.exists():
            identity = json.loads(identity_file.read_text())
            try:
                process = psutil.Process(identity['pid'])
                if process.create_time() == identity['birth']:
                    process.kill()
                    process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass


@pytest.mark.parametrize('original_kind', ['AccessDenied', 'SystemError'])
@pytest.mark.parametrize('secondary_kind', ['SystemError', 'RuntimeError'])
@pytest.mark.parametrize('validation_operation', ['create_time', 'status'])
def test_secondary_validation_error_fails_closed_without_message_leak(
        tmp_path, original_kind, secondary_kind, validation_operation):
    identity_file = tmp_path / 'owned.json'
    wrapper = tmp_path / 'controlled_runner.py'
    output = tmp_path / 'inspection.log'
    lock = tmp_path / 'private.lock'
    secret = 'private-secondary-identity-message-never-persist'
    initial = ('V.psutil.AccessDenied(self.pid)' if original_kind == 'AccessDenied'
               else f'SystemError({NATIVE_ERROR!r})')
    wrapper.write_text(
        'import json,sys\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal_env=V.psutil.Process.environ\n'
        + f'original_validation=V.psutil.Process.{validation_operation}\n'
        + 'failed=[False]\nvalidation_failed=[False]\n'
        + 'def target():\n'
        + f' p=Path({str(identity_file)!r})\n'
        + ' return json.loads(p.read_text())["pid"] if p.exists() else None\n'
        + 'def environ(self):\n'
        + ' if self.pid==target() and not failed[0]:\n  failed[0]=True\n'
        + f'  raise {initial}\n'
        + ' return original_env(self)\n'
        + 'def validate(self):\n'
        + ' if self.pid==target() and failed[0] and not validation_failed[0]:\n'
        + '  validation_failed[0]=True\n'
        + f'  raise {secondary_kind}({secret!r})\n'
        + ' return original_validation(self)\n'
        + 'V.psutil.Process.environ=environ\n'
        + f'V.psutil.Process.{validation_operation}=validate\n'
        + 'raise SystemExit(V.main())\n'
    )
    child = (
        'import json,os,time,psutil;from pathlib import Path;'
        + f'Path({str(identity_file)!r}).write_text(json.dumps({{"pid":os.getpid(),"birth":psutil.Process().create_time()}}));'
        + 'time.sleep(.7)'
    )
    try:
        result = subprocess.run(
            [sys.executable, str(wrapper), '--lock', str(lock), '--log', str(output),
             '--cap-gb', '8', '--timeout', '2', '--', sys.executable, '-c', child],
            capture_output=True, text=True, timeout=8,
        )
        text = Path(str(output) + '.summary.json').read_text()
        report = json.loads(text)
        failure = report['primary_inspection_failure']
        assert result.returncode != 0, 'secondary identity failure recovered into a successful run'
        assert failure is not None, 'secondary exception escaped without contextual annotation'
        assert failure['operation'] == f'identity_validation.{validation_operation}'
        assert failure['requested_operation'] == 'environ'
        assert failure['exception']['type'] == secondary_kind
        assert failure['environment_failure']['exception']['type'] == original_kind
        assert failure['identity_exception']['operation'] == failure['operation']
        assert failure['identity_state'] == 'unknown' and failure['outcome'] == 'inspection-failed'
        assert not any(e['outcome'] == 'recovered' for e in report['inspection_events'])
        assert secret not in text + result.stdout + result.stderr
    finally:
        if identity_file.exists():
            identity = json.loads(identity_file.read_text())
            try:
                process = psutil.Process(identity['pid'])
                if process.create_time() == identity['birth']:
                    process.kill()
                    process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass
