"""One finite completed21 mode action, retaining original argv and all streams."""
import datetime, hashlib, json, os, shlex, subprocess
from pathlib import Path

BOOT = Path('/private/tmp/lanl14-invoke-completed21-mode-20261008-a1.py')
SUP = Path('/private/tmp/lanl14-completed-metadata-supplier-r1-actual-20261008-a1')
CAPTURE = Path('/private/tmp/lanl14-completed21-mode-actual-20261008-a1')
REMOTE_CUSTODY = '/data/yanruj/EvolveSWDB_runs/lanl14-report-transfer-mode-administration-20261008-a1'
SOURCE_SHA = 'ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7'
def digest(value): return hashlib.sha256(value).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name, body):
    fd = os.open(CAPTURE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        assert stream.write(body) == len(body)
        stream.flush(); os.fsync(stream.fileno())
    return {'path': str(CAPTURE / name), 'bytes': len(body), 'sha256': digest(body)}
raw = (SUP / 'stdout.json').read_bytes()
assert len(raw) == 29107 and digest(raw) == '62d3f72960c96084840c03382b9057d06d9d43d90d249d0c6d1390ebc9a15ada'
d = json.loads(raw); exited = json.loads((SUP / 'exit.json').read_bytes())
assert exited['returncode'] == 0 and exited['failure_type'] is None and exited['stdout']['sha256'] == digest(raw)
assert (SUP / 'stderr.txt').read_bytes() == b'' and exited['stderr']['bytes'] == 0
assert d['sealed'] is False and d['scientific_admission'] is False and d['guard_or_permission_actions'] == 0
assert d['read_only_actual_metadata'] is True and d['source_only_preparation'] is False
assert d['R14'] == 'c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
assert d['C'] == 'f893fed400347ed23d92e917d8bde21b75e5375d'
assert d['F6'] == 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
copy = json.loads(Path('/private/tmp/lanl14-completed-source-controls-copy-producer-actual-stdout-20261008-a1.json').read_bytes())
assert d['own_source'] == copy['copied_source_before_after_pins'][1]
assert d['native'] == copy['native_before_after']
assert d['literal_private_roots_before'] == d['literal_private_roots_after']
rows = d['original21_current_modes_and_stats']
assert len(rows) == len({r['path'] for r in rows}) == 21
assert all(r['mode_octal'] == '0o664' and r['stat']['st_mode'] == 33204
           and r['stat']['st_uid'] == 114316761 and r['stat']['st_nlink'] == 1
           and r['bytes'] == r['stat']['st_size'] and len(r['declared_original_file_sha256']) == 64 for r in rows)
assert [r['kind'] for r in rows[:18]] == ['protocol', 'estimate'] * 9
a = d['exact_derived_args']
assert set(a) == {'manifest_file_sha256', 'manifest_identity_sha256', 'acceptance_file_sha256', 'acceptance_identity_sha256',
                  'request_file_sha256', 'request_identity_sha256', 'protected_file_sha256', 'final_validation_file_sha256',
                  'report_file_sha256', 'report_identity_sha256', 'markdown_file_sha256', 'report_bytes', 'markdown_bytes'}
for key, obj in [('manifest', 'manifest'), ('acceptance', 'acceptance'), ('request', 'request')]:
    assert a[key + '_file_sha256'] == d[obj]['file']['sha256']
    assert a[key + '_identity_sha256'] == d[obj]['original_identity_sha256']
assert a['protected_file_sha256'] == d['protected']['file']['sha256']
assert a['final_validation_file_sha256'] == d['validation']['sha256']
assert a['report_file_sha256'] == d['report']['file']['sha256'] == rows[18]['declared_original_file_sha256']
assert a['report_identity_sha256'] == d['report']['semantic_identity_sha256']
assert a['markdown_file_sha256'] == d['Markdown']['file']['sha256'] == rows[19]['declared_original_file_sha256']
assert a['request_file_sha256'] == rows[20]['declared_original_file_sha256']
assert a['report_bytes'] == d['report']['file']['bytes'] == rows[18]['bytes'] == 68324111
assert a['markdown_bytes'] == d['Markdown']['file']['bytes'] == rows[19]['bytes'] == 1475
assert d['wrapper_upstream_commit'] == '76cca359136794afa5ede975cfac8293cfa2ab9a'
assert d['completed_raw_canonical_count'] == 704 and d['prior_canonical_count'] == 686 and d['new_canonical_count'] == 18
target = [d['imported_original_helper']['path'], '--source-sha256', SOURCE_SHA]
for key, value in a.items(): target.extend(['--' + key.replace('_', '-'), str(value)])
target.extend(['--deadline-s', '600', '--output-directory', REMOTE_CUSTODY])
remote = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=60s', '840s', '/usr/bin/python3.12', '-B', '-', *target[1:]]
argv = ['ssh', '-oBatchMode=yes', '-oConnectTimeout=20', 'mbit10', shlex.join(remote)]
body = BOOT.read_bytes()
assert digest(body) == '69583a87a632d4933d9aba628799429e0c4f9594c31657d50523026e9c54103e'
compile(body, str(BOOT), 'exec')
assert not os.path.lexists(CAPTURE)
os.mkdir(CAPTURE, 0o700)
save('start.json', (json.dumps({'format': 'swdb.lanl14-completed21-mode-parent-start.v1', 'sealed': False,
    'started_utc': now(), 'actual_transport_argv': argv, 'actual_remote_outer_argv': remote,
    'selected_target_sys_argv': target, 'same_process_hash_verified_execution': True,
    'bootstrap': {'path': str(BOOT), 'bytes': len(body), 'sha256': digest(body)},
    'actual_supplier_stdout_sha256': digest(raw), 'local_wait_s': 1020, 'scientific_admission': False}, sort_keys=True) + '\n').encode())
code, out, err, failure = None, b'', b'', None
try:
    child = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1020, check=False)
    code, out, err = child.returncode, child.stdout, child.stderr
except subprocess.TimeoutExpired as exc: out, err, failure = exc.stdout or b'', exc.stderr or b'', 'TimeoutExpired'
except Exception as exc: failure = type(exc).__name__
stdout = save('stdout.json', out); stderr = save('stderr.txt', err)
result = {'format': 'swdb.lanl14-completed21-mode-parent-exit.v1', 'sealed': False, 'ended_utc': now(),
          'returncode': code, 'failure_type': failure, 'stdout': stdout, 'stderr': stderr,
          'scientific_admission': False, 'no_retry_rollback_or_remote_cleanup': True}
save('exit.json', (json.dumps(result, sort_keys=True) + '\n').encode())
print(json.dumps(result, sort_keys=True))
raise SystemExit(code if code is not None else 2)
