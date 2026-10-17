"""2026-10-16 ET. Root admission for reviewed Mac private preparation controls."""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / '28-interface-memory-resume-20261016/command_v2.json'
assert not sys.flags.optimize
plan = json.loads(COMMAND.read_bytes())
assert hashlib.sha256(COMMAND.read_bytes()).hexdigest() == '0f36871d8360311145e11e848c15ff4ccd595b2392cb79e8b1bfcb4dc3e66220'
for row in [plan['entry'], plan['source_policy'], plan['runtime_policy'], *plan['guard_required']['guard_source_pins']]:
    path = Path(row['path'])
    assert path.stat().st_size == row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], str(path)
assert psutil.virtual_memory().available >= 5 * 1024**3
with open('/private/tmp/probata-mac-compiler-worker-b.lock', 'a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(lock, fcntl.LOCK_UN)
raw = Path(plan['raw_root'])
assert raw == Path('/private/tmp/probata-resume-20261016-t28-memory53-native-v2') and not raw.is_symlink()
raw.mkdir(exist_ok=False)
python = '/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12'
guard = plan['guard_required']['guard_source_pins'][1]['path']
wrapper = plan['guard_required']['guard_source_pins'][0]['path']
argv = [python, '-I', '-B', '-X', 'pycache_prefix=' + str(raw / 'wrapper-cache'), wrapper, '--',
        python, '-B', '-X', 'pycache_prefix=' + str(raw / 'guard-cache'), guard,
        '--log', str(raw / 'guard.log'), '--cap-gb', '4', '--timeout', '180', '--queue-timeout', '30',
        '--owner', 't28-memory53-v2', '--lock', '/tmp/claude/swdb-verifier.lock', '--', *plan['entry_argv']]
environment = {'HOME': '/Users/yanrujhou', 'USER': 'yanrujhou', 'LOGNAME': 'yanrujhou',
               'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C', 'LC_ALL': 'C',
               'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
               'SWDB_VERIFIER_RSS_CAP_BYTES': '4294967296'}
admission = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'command_sha256': hashlib.sha256(COMMAND.read_bytes()).hexdigest(), 'argv': argv,
             'environment': environment, 'available_bytes': psutil.virtual_memory().available,
             'scope': plan['scope'], 'guards_physically_rechecked': True,
             'slot_policy': 'c6 compatible shared slot scheduler; never modify external ticket7 ownership'}
(raw / 'root-admission.json').write_text(json.dumps(admission, indent=2) + '\n')
started = time.monotonic()
with (raw / 'root.stdout').open('wb') as stdout, (raw / 'root.stderr').open('wb') as stderr:
    child = subprocess.Popen(argv, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
    outer_timeout = False
    try:
        status = child.wait(timeout=260)
    except subprocess.TimeoutExpired:
        outer_timeout = True
        os.killpg(child.pid, signal.SIGTERM)
        try:
            status = child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            status = child.wait(timeout=10)
result = {'exit_code': status, 'outer_timeout': outer_timeout, 'wall_s': time.monotonic() - started,
          'raw': str(raw), 'scope': plan['scope']}
(raw / 'root-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
raise SystemExit(status if status >= 0 else 128 - status)
