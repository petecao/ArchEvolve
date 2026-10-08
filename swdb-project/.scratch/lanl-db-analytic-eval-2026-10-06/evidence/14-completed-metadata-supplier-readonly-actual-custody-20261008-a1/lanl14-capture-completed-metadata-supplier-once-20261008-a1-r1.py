"""One future readonly supplier invocation; originals retained without retry."""
import argparse, datetime, hashlib, json, os, re, shlex, subprocess
from pathlib import Path

BOOT = Path('/private/tmp/lanl14-invoke-completed-metadata-supplier-r1-20261008-a1.py')
CAPTURE = Path('/private/tmp/lanl14-completed-metadata-supplier-r1-actual-20261008-a1')

def digest(value):
    return hashlib.sha256(value).hexdigest()

def save(name, body):
    fd = os.open(CAPTURE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    return {'path': str(CAPTURE / name), 'bytes': len(body), 'sha256': digest(body)}

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expected-primary', required=True)
args = parser.parse_args()
assert re.fullmatch('[0-9a-f]{40}', args.expected_primary)
body = BOOT.read_bytes()
assert len(body) == 3215 and digest(body) == '8ed2b16a14882a01ae26641e626ecd05c026ea11b4a054bb35406d2ff077b581'
assert not os.path.lexists(CAPTURE)
remote = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=60s', '840s', '/usr/bin/python3.12', '-B', '-', args.expected_primary]
argv = ['ssh', '-oBatchMode=yes', '-oConnectTimeout=20', 'mbit10', shlex.join(remote)]
os.mkdir(CAPTURE, 0o700)
start = {'format': 'swdb.lanl14-completed-readonly-supplier-parent-start.v1', 'sealed': False,
         'started_utc': now(), 'bootstrap': {'path': str(BOOT), 'bytes': len(body), 'sha256': digest(body)},
         'actual_transport_argv': argv, 'actual_remote_outer_argv': remote,
         'selected_supplier_sys_argv': ['/data1/yanruj/lanl14-completed-source-controls-20261008-a1/completed_metadata_supplier_r1.py', '--deadline-s', '600', '--expected-primary', args.expected_primary],
         'supplier_execution_route': 'Returned hash-verified bytes compiled in the same native Python-B bootstrap process; no separate target OS exec.',
         'local_wait_s': 1020, 'requested_readonly': True, 'scientific_admission': False}
save('start.json', (json.dumps(start, sort_keys=True) + '\n').encode())
code, out, err, failure = None, b'', b'', None
try:
    child = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1020, check=False)
    code, out, err = child.returncode, child.stdout, child.stderr
except subprocess.TimeoutExpired as exc:
    out, err, failure = exc.stdout or b'', exc.stderr or b'', 'TimeoutExpired'
except Exception as exc:
    failure = type(exc).__name__
stdout = save('stdout.json', out); stderr = save('stderr.txt', err)
result = {'format': 'swdb.lanl14-completed-readonly-supplier-parent-exit.v1', 'sealed': False,
          'ended_utc': now(), 'returncode': code, 'failure_type': failure, 'stdout': stdout, 'stderr': stderr,
          'science_or_permission_admission': False, 'no_retry_or_remote_cleanup': True}
save('exit.json', (json.dumps(result, sort_keys=True) + '\n').encode())
print(json.dumps(result, sort_keys=True))
raise SystemExit(code if code is not None else 2)
