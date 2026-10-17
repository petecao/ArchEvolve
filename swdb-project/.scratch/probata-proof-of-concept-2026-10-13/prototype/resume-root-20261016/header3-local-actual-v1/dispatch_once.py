"""2026-10-16 ET. Exact root-once-admitted Header3 dispatch, no automatic retry.

Run only after root reviews the retained scoped preflight adaptation. No source
deletion/cleanup occurs; only the exact admitted fresh clone/job can be created.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
EV = POC/'evidence'
PREFIX = 't25-owned-swap-header3-public-v1-'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, value):
    path = EV/(PREFIX+name+'-20261016.json')
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return pin(path)


def invoke(name, argv, *, data=None, timeout=60, cap=65536):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    try:
        result = subprocess.run(argv, input=data, capture_output=True, timeout=timeout)
        code, stdout, stderr, uncertain = result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr, uncertain = None, error.stdout or b'', error.stderr or b'', True
    output = EV/(PREFIX+name+'-stdout-20261016.json')
    errors = EV/(PREFIX+name+'-stderr-20261016.txt')
    for path, raw in ((output, stdout), (errors, stderr)):
        with path.open('xb') as stream:
            stream.write(raw)
    receipt = {'date': '2026-10-16 ET', 'started_utc': started,
               'elapsed_seconds': time.monotonic()-clock, 'argv': argv,
               'stdin_sha256': hashlib.sha256(data).hexdigest() if data is not None else None,
               'exit_code': code, 'uncertain_transport': uncertain,
               'stdout': pin(output), 'stderr': pin(errors),
               'within_caps': len(stdout) <= cap and len(stderr) <= 65536}
    receipt_pin = save(name+'-invocation', receipt)
    if not receipt['within_caps']:
        raise ValueError('finite dispatch output cap exceeded; preserve and do not retry')
    return receipt, receipt_pin, stdout


def main():
    admission_path = EV/'t25-owned-swap-header3-public-root-once-admission-v1-20261016.json'
    assert pin(admission_path)['sha256'] == 'f7ec9de7ea2436e42c197d020695e76c9d57abfa55cdc51b5ce9518242b19905'
    admission = json.loads(admission_path.read_bytes())
    for name in ('Spec', 'Standards', 'entry', 'expected', 'command', 'launcher', 'local_argv', 'source_review', 'preparation'):
        row = admission[name]
        assert pin(Path(row['path'])) == row
    argv = json.loads(Path(admission['local_argv']['path']).read_bytes())
    assert argv == admission['exact_local_argv']
    assert argv[4:8] == ['abb598a485cca67c77798e690382b44beb48c9e3',
                         't25-owned-swap-header3-public-v1', '2800', '1']
    preparation = json.loads(Path(admission['preparation']['path']).read_bytes())
    for row in preparation['files']:
        assert pin(Path(row['path'])) == row
    preflight = HERE/'scoped-preflight-v1.py'
    assert pin(preflight)['sha256'] == 'ddeb9d08496816889e7fa6604e9fa6550ca72b1f447429faa9c7dcde6113f54c'
    ssh = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'mbit10',
           '/usr/bin/env', '-i', 'HOME=/nonexistent', 'PATH=/usr/bin:/bin', 'LANG=C', 'LC_ALL=C',
           '/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '35s', '/usr/bin/python3', '-I', '-B', '-']
    observed, preflight_pin, raw = invoke('fresh-scoped-preflight', ssh, data=preflight.read_bytes(), timeout=45)
    if observed['exit_code'] != 0:
        save('preflight-refusal', {'root_admission': pin(admission_path), 'preflight': preflight_pin,
                                 'actual_dispatch_attempted': False, 'automatic_retry': False})
        return 1
    value = json.loads(raw)
    assert value['scoped_preflight_pass'] and value['fresh_source_and_raw_absent']
    # Exclusive attempt token is created after all fresh read-only gates pass.
    save('actual-attempt', {'root_admission': pin(admission_path), 'argv': admission['local_argv'],
                           'preflight': preflight_pin, 'once_only': True,
                           'protected_startup_coordinated': True, 'cleanup_or_deletion': False})
    result, result_pin, stdout = invoke('launcher-dispatch', argv, timeout=240, cap=2*1024**2)
    launch = json.loads(stdout) if result['exit_code'] == 0 and stdout else {}
    receipt = save('dispatch-execution', {
        'root_admission': pin(admission_path), 'classification':
        'DISPATCHED_PENDING_ACTUAL_SETTLEMENT' if result['exit_code'] == 0 else 'REFUSED_OR_UNCERTAIN_NO_AUTOMATIC_RETRY',
        'preflight': preflight_pin, 'dispatch': result_pin, 'source_commit': argv[4], 'node': 1,
        'reported_session': launch.get('session'), 'reported_raw_root': launch.get('output'),
        'actual_settlement': False, 'science_source_Heap_Typed_caller_or_ticket_admission': False,
        'cleanup_or_deletion_attempted': False})
    print(json.dumps(receipt))
    return 0 if result['exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
