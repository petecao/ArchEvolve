"""One bounded synthetic index regression batch; no actual writer/main input."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode())


interpreter = Path('/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3')
test = Path('/private/tmp/lanl17_parent_full_record_index_isolated_test_source_20261007.py')
writer = Path('/private/tmp/lanl17_write_parent_full_record_index_20261007.py')
preparation = Path('/private/tmp/lanl17-parent-full-record-index-source-preparation-20261007.json')
handoff = Path('/private/tmp/lanl17-parent-full-record-index-writer-source-handoff-20261007.md')
pins = [(test, '02395edfab3000e8ffac2dba895bbd1d3d78eb6fefa4cb15585dc88c5b77fa40', 10704),
        (writer, '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b', 33445),
        (preparation, '54d916f5933da0af661e1245856f8e93b30bdc6147a569626aad066a60b7eb88', None),
        (handoff, '1ad58ed923ea8c6b20f6d57b6f07a8fc89d266ccf0f88c83bd871dcf07c8118c', 10048)]
for path, identity, size in pins:
    assert path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == identity
    assert size is None or path.stat().st_size == size
prepared = json.loads(preparation.read_bytes())
assert prepared['identity_sha256'] == digest({k: v for k, v in prepared.items() if k != 'identity_sha256'})
assert prepared['identity_sha256'] == '9be4d961e49fedf415c9f068318c8480a47e1331737399d4405fb113fa33519c'
assert prepared['isolated_fixture_cases_executed'] == 0
assert prepared['new_writer_and_test_source_imported_or_executed'] is False
tree = ast.parse(test.read_bytes())
cases = [n.name for c in tree.body if isinstance(c, ast.ClassDef)
         for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert cases == prepared['isolated_fixture_case_source_names'] and len(cases) == 8
assert interpreter.is_file()
paths = {suffix: Path('/private/tmp/lanl17-parent-full-record-index-tests-actual-20261007.' + suffix)
         for suffix in ('start.json', 'stdout', 'stderr', 'json')}
assert all(not path.exists() and not path.is_symlink() for path in paths.values())
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
begin = time.monotonic()
start = {'format': 'swdb.lanl17-parent-index-isolated-test-start.v1', 'started_utc': started,
         'test_source_sha256': pins[0][1], 'writer_source_sha256': pins[1][1],
         'state': 'original_unsealed_start_before_one_synthetic_subprocess',
         'scientific_admission': False, 'actual_inputs_constructed': False}
with paths['start.json'].open('x') as stream:
    stream.write(json.dumps(start, indent=2) + '\n')
timed_out = False
returncode = None
with paths['stdout'].open('xb') as out, paths['stderr'].open('xb') as err:
    try:
        result = subprocess.run([str(interpreter), '-B', str(test)], stdout=out, stderr=err,
                                timeout=60, check=False)
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
preserved = all(sha(path.read_bytes()) == identity for path, identity, _ in pins)
stderr = paths['stderr'].read_text()
counts = re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$', stderr, re.M)
reported_count = int(counts[0][0]) if len(counts) == 1 else None
reported_ok = bool(re.search(r'^OK$', stderr, re.M))
successful_methods = re.findall(r'^(test_[A-Za-z0-9_]+) \(.+\) \.\.\. ok$', stderr, re.M)
receipt = {'format': 'swdb.lanl17-parent-index-isolated-tests-actual.v1',
           'started_utc': started, 'ended_utc': ended, 'canonical_ensure_ascii': True,
           'actual_subprocess_returncode': returncode, 'actual_timed_out': timed_out,
           'actual_reported_test_count': reported_count, 'actual_reported_OK': reported_ok,
           'actual_successful_test_method_names': successful_methods,
           'elapsed_parent_seconds': time.monotonic() - begin,
           'original_preparation_identity': prepared['identity_sha256'],
           'source_pins': {str(path): {'sha256': identity, 'bytes': path.stat().st_size}
                           for path, identity, _ in pins},
           'outputs': {suffix: {'path': str(path), 'bytes': path.stat().st_size,
                                'sha256': sha(path.read_bytes()), 'original_sealed': False}
                       for suffix, path in paths.items() if suffix != 'json'},
           'batch_invocations': 1, 'source_and_preparation_preserved': preserved,
           'scientific_admission': False, 'actual_inputs_constructed': False,
           'writer_main_or_Store_validate_provider_native_campaign_actions': 0,
           'scope': 'One local eight-case synthetic batch, lifting closed exact original helper AST only. '
                    'No actual writer main, request, catalogue, index, SWDB, Store, validator, selected '
                    'collector/auditor, SSH, native or provider execution. Original preparation stays NOTRUN history.'}
receipt['identity_sha256'] = digest(receipt)
with paths['json'].open('x') as stream:
    stream.write(json.dumps(receipt, indent=2, ensure_ascii=True, allow_nan=False) + '\n')
print(json.dumps({'path': str(paths['json']), 'bytes': paths['json'].stat().st_size,
                  'sha256': sha(paths['json'].read_bytes()), 'identity_sha256': receipt['identity_sha256'],
                  'returncode': returncode, 'tests': reported_count, 'OK': reported_ok,
                  'scientific_admission': False}))
assert not timed_out and returncode == 0 and reported_count == 8 and reported_ok and preserved
assert set(successful_methods) == set(cases) and len(successful_methods) == 8
