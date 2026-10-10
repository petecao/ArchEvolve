"""One finite, source-pinned SYNTHETIC batch. No actual guard execution."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

PYTHON = Path('/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12')
HARNESS = Path('/private/tmp/lanl_consumed_source_guard_binding_journal_isolated_test_source_20261007_r2.py')
OUT = Path('/private/tmp/lanl-consumed-source-guard-binding-journal-isolated-tests-20261007-r2')
RECEIPT = Path('/private/tmp/lanl-consumed-source-guard-binding-journal-isolated-tests-actual-20261007-r2.json')
PINS = [
    (HARNESS, 14456, '9376fd62312916d67fddd6f84b7398480c5efa9922e53ea907fa3aa996b768bf'),
    (Path('/private/tmp/lanl_consumed_detached_source_guard_r1_20261007.py'), 64859, '66944bb04d05a690dc1c81ced7c203c0494cc028c6c9c1531e1fcb9cecd110e1'),
    (Path('/private/tmp/lanl_consumed_detached_source_guard_r2_20261007.py'), 65830, '3ff7bde67947adf524d0c4f556047fcf1377bc6ddb1e64c9ac58409c3e0acfeb'),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


os.umask(0o077)
assert not OUT.exists() and not RECEIPT.exists()
before = [pin(p) for p, size, expected in PINS]
for facts, (_, size, expected) in zip(before, PINS):
    assert facts['bytes'] == size and facts['sha256'] == expected
native = pin(PYTHON)
assert native['bytes'] == 33816
assert native['sha256'] == '08fa4dbadc420090dfee2acf433b827ae05541f728d1478d96879122f53b4328'
OUT.mkdir(mode=0o700)
stdout = OUT / 'stdout.txt'
stderr = OUT / 'stderr.txt'
argv = [str(PYTHON), '-B', str(HARNESS)]
started, clock = stamp(), time.monotonic()
timed_out = False
with stdout.open('xb') as out, stderr.open('xb') as err:
    try:
        completed = subprocess.run(argv, cwd=str(OUT), stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err, timeout=60,
                                   env={'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'})
        status = completed.returncode
    except subprocess.TimeoutExpired:
        status, timed_out = None, True
    out.flush(); os.fsync(out.fileno())
    err.flush(); os.fsync(err.fileno())
finished, elapsed = stamp(), time.monotonic() - clock
after = [pin(p) for p, _, _ in PINS]
assert before == after
assert native == pin(PYTHON)
streams = [pin(stdout), pin(stderr)]
assert all(p['bytes'] <= 1024 * 1024 for p in streams)
original_stderr = stderr.read_bytes()
passed = status == 0 and not timed_out and b'Ran 6 tests' in original_stderr and original_stderr.rstrip().endswith(b'OK')
doc = {'format': 'swdb.consumed-source-guard-isolated-synthetic-tests.v1',
       'canonical_ensure_ascii': True, 'started_at': started, 'finished_at': finished,
       'elapsed_seconds': elapsed, 'argv': argv, 'cwd': str(OUT),
       'native_interpreter': native, 'runner': pin(Path(__file__)),
       'source_pins_before_and_after_equal': True, 'source_pins': before,
       'original_streams': streams, 'returncode': status, 'timed_out': timed_out,
       'timeout_seconds': 60, 'test_method_count': 6, 'passed': passed,
       'scope': 'SYNTHETIC exact isolated AST binding and interruption-custody blocks only',
       'actual_guard_main_plan_filesystem_removal_host_visibility_capacity_scientific_admission': False}
doc['identity_sha256'] = sha(json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode())
with RECEIPT.open('x') as out:
    out.write(json.dumps(doc, indent=2, ensure_ascii=True, allow_nan=False) + '\n')
    out.flush(); os.fsync(out.fileno())
print(json.dumps({'receipt': str(RECEIPT), 'identity_sha256': doc['identity_sha256'],
                  'returncode': status, 'timed_out': timed_out, 'passed': passed}))
raise SystemExit(0 if passed else 1)
