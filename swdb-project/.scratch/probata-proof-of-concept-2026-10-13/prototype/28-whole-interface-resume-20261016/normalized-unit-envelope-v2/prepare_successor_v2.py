"""Source-only exact envelope successor; every V1 file stays unchanged."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'normalized-unit-envelope-v1'
edits = []


def change(text, old, new):
    assert text.count(old) == 1, old[:100]
    edits.append({'old': old, 'new': new})
    return text.replace(old, new, 1)


def replace_function(text, name, new):
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    return change(text, ast.get_source_segment(text, node), new.strip())


READ = '''def read(row, *, limit=CONTROLS_BYTES):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
         and type(row['bytes']) is int and 0 <= row['bytes'] <= limit,
         'closed bounded physical envelope pin required')
    path = Path(row['path']); before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
         and before.st_size == row['bytes'], 'bounded canonical physical extent required before reading')
    with path.open('rb') as handle: data = handle.read(limit + 1)
    need(stable(path.lstat()) == stable(before) and len(data) == row['bytes']
         and hashlib.sha256(data).hexdigest() == row['sha256'], 'envelope bytes changed during bounded consumption')
    return data'''

PUBLISH = '''def publish_final_result(raw, status, started):
    """Success requires zero exit and a settled check after publication/flush."""
    result = dict(status)
    result['completion_requires_zero_exit_and_settled_finalization'] = True
    try:
        need(time.monotonic() - started <= ENTRY_SECONDS, 'prepublication deadline exceeded')
        check_outputs(raw)
        save(raw / 'envelope-result.json', result)
        print(json.dumps(result, sort_keys=True, allow_nan=False)); sys.stdout.flush()
        check_outputs(raw)
        need(time.monotonic() - started <= ENTRY_SECONDS, 'settled post-publication deadline exceeded')
        return bool(result['observation_complete'])
    except Exception as error:
        refusal = {'schema': 'linux-normalized-unit-envelope-finalization-refusal-1',
            'observation_complete': False, 'public_admission': False,
            'error': frames(error), 'wall_seconds': time.monotonic() - started,
            'earlier_result_alone_cannot_establish_completion': True}
        try: save(raw / 'envelope-finalization-refusal.json', refusal)
        except Exception: pass  # Nonzero exit still refuses if quota/IO prevents metadata publication.
        return False'''


source = (OLD / 'linux_observation_envelope_v1.py').read_text()
source = change(source, "RAW_NAME = 'probata-resume-20261016-t28-unit-observation-2baf722f-v1'",
    "RAW_NAME = 'probata-resume-20261016-t28-unit-observation-2baf722f-v2'")
source = source.replace('control/linux_observation_envelope_v1.py', 'control/linux_observation_envelope_v2.py')
source = source.replace('control/envelope-policy-v1.json', 'control/envelope-policy-v2.json')
source = change(source, "'envelope-source-before.json', 'envelope-source-after.json', 'envelope-result.json')",
    "'envelope-source-before.json', 'envelope-source-after.json', 'envelope-result.json', 'envelope-finalization-refusal.json')")
source = replace_function(source, 'read', READ)
source = change(source, "    need(shutil.disk_usage(raw).free >= policy['disk_floor_bytes'] + OUTPUT_BYTES, 'disk reserve plus quota required')",
    "    need(type(policy['disk_floor_bytes']) is int and policy['disk_floor_bytes'] >= 20 * 1024**3, 'governing twenty-GiB raw-mount floor required')\n"
    "    need(shutil.disk_usage(raw).free >= policy['disk_floor_bytes'] + OUTPUT_BYTES, 'disk reserve plus quota required')")
source = change(source, 'sum(row[\'bytes\'] for row in rows) <= OUTPUT_BYTES - 2 * FILE_BYTES',
    'sum(row[\'bytes\'] for row in rows) <= OUTPUT_BYTES - 8 * FILE_BYTES')
source = change(source, 'def main(argv=None):', PUBLISH + '\n\n\ndef main(argv=None):')
source = change(source, "        save(raw / 'envelope-result.json', status)\n        signal.setitimer(signal.ITIMER_REAL, 0)\n    print(json.dumps(status, sort_keys=True, allow_nan=False))\n    return 0 if status['observation_complete'] else 1",
    "        accepted = publish_final_result(raw, status, started)\n        signal.setitimer(signal.ITIMER_REAL, 0)\n    return 0 if accepted else 1")
ast.parse(source)
(HERE / 'linux_observation_envelope_v2.py').write_text(source)
restored = source
for row in reversed(edits):
    assert restored.count(row['new']) == 1
    restored = restored.replace(row['new'], row['old'], 1)
restored = restored.replace('control/linux_observation_envelope_v2.py', 'control/linux_observation_envelope_v1.py')
restored = restored.replace('control/envelope-policy-v2.json', 'control/envelope-policy-v1.json')
assert restored == (OLD / 'linux_observation_envelope_v1.py').read_text()
(HERE / 'entry-inverse-v2.json').write_text(json.dumps({'schema': 'exact-observer-envelope-v2-inverse-1',
    'replacements': edits, 'final_name_inverse': {'control/linux_observation_envelope_v2.py': 'control/linux_observation_envelope_v1.py',
    'control/envelope-policy-v2.json': 'control/envelope-policy-v1.json'}, 'exact_V1_restored': True}, sort_keys=True, indent=2) + '\n')
builder = (OLD / 'prepare_envelope_v1.py').read_text()
builder = builder.replace('t28-unit-observation-2baf722f-v1', 't28-unit-observation-2baf722f-v2')
builder = builder.replace('linux_observation_envelope_v1.py', 'linux_observation_envelope_v2.py')
builder = builder.replace("'disk_floor_bytes': 2147483648", "'disk_floor_bytes': 21474836480")
builder = builder.replace('envelope-policy-v1.json', 'envelope-policy-v2.json').replace('envelope-policy-template-v1.json', 'envelope-policy-template-v2.json')
builder = builder.replace('command-v1.json', 'command-v2.json').replace('command-template-v1.json', 'command-template-v2.json')
builder = builder.replace("'root_created_directories': [RAW + '/control', RAW + '/observer', RAW + '/observer/control',\n                                     RAW + '/library_fixture', RAW + '/library_fixture/proof_units'],",
    "'root_created_directories': [RAW + '/control'],\n        'envelope_created_directories': [RAW + '/observer', RAW + '/observer/control', RAW + '/library_fixture', RAW + '/library_fixture/proof_units'],")
(HERE / 'prepare_envelope_v2.py').write_text(builder); ast.parse(builder)
metadata = (OLD / 'root-metadata-selection-v1.json').read_text().replace('t28-unit-observation-2baf722f-v1', 't28-unit-observation-2baf722f-v2')
(HERE / 'root-metadata-selection-v2.json').write_text(metadata)
(HERE / 'root-metadata-provenance-v1.json').write_bytes((OLD / 'root-metadata-provenance-v1.json').read_bytes())
tests = (OLD / 'test_envelope_v1.py').read_text().replace('linux_observation_envelope_v1.py', 'linux_observation_envelope_v2.py')
tests = tests.replace('prepare_envelope_v1.py', 'prepare_envelope_v2.py').replace('control/envelope-policy-v1.json', 'control/envelope-policy-v2.json')
(HERE / 'test_envelope_v2.py').write_text(tests)
print(json.dumps({'entry_sha256': hashlib.sha256(source.encode()).hexdigest(), 'actual_executed': False}))
