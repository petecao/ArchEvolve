"""Source-only namespace successor. Never execute launcher or observer."""
import ast
import hashlib
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'normalized-unit-envelope-v2'
LAUNCHER = HERE.parent / 'root-launcher-loader-v11/launch_observer_loader_v11.py'
assert hashlib.sha256(LAUNCHER.read_bytes()).hexdigest() == 'b4a2664da950070e5e37ffb88eb260e90d8cdb2d5a591504a7e9723c4891272b'
source = (OLD / 'linux_observation_envelope_v2.py').read_text()
assert hashlib.sha256(source.encode()).hexdigest() == 'd137b636d72e00baadc7bb6705c796b99f80dc2218e12c1e9e02e35f8b9a7f01'
replacements = [
    ('t28-unit-observation-2baf722f-v2', 't28-unit-observation-2baf722f-v3'),
    ('control/linux_observation_envelope_v2.py', 'control/linux_observation_envelope_v3.py'),
    ('control/envelope-policy-v2.json', 'control/envelope-policy-v3.json')]
for index, (old, new) in enumerate(replacements):
    assert source.count(old) == (1 if index == 0 else 2)
    source = source.replace(old, new)
ast.parse(source)
(HERE / 'linux_observation_envelope_v3.py').write_text(source)
(HERE / 'entry-inverse-v3.json').write_text(json.dumps({'schema': 'exact-observer-envelope-v3-namespace-inverse-1',
    'replacements': [{'old': a, 'new': b} for a, b in replacements],
    'strict_environment_and_all_scientific_functions_unchanged': True}, sort_keys=True, indent=2) + '\n')
builder = (OLD / 'prepare_envelope_v2.py').read_text()
for old, new in (
    ('t28-unit-observation-2baf722f-v2', 't28-unit-observation-2baf722f-v3'),
    ('linux_observation_envelope_v2.py', 'linux_observation_envelope_v3.py'),
    ('envelope-policy-v2.json', 'envelope-policy-v3.json'),
    ('envelope-policy-template-v2.json', 'envelope-policy-template-v3.json'),
    ('command-v2.json', 'command-v3.json'), ('command-template-v2.json', 'command-template-v3.json'),
    ("pin(POC / 'prototype/resume-root-20261016/launch_reviewed_main_v9.py')", "pin(WHOLE / 'root-launcher-loader-v11/launch_observer_loader_v11.py')"),
    ("'run_environment_unset': ['LIBRARY_PATH']", "'run_environment_unset': ['LIBRARY_PATH', 'LD_LIBRARY_PATH']")):
    assert old in builder
    builder = builder.replace(old, new)
(HERE / 'prepare_envelope_v3.py').write_text(builder)
metadata = (OLD / 'root-metadata-selection-v2.json').read_text().replace('t28-unit-observation-2baf722f-v2', 't28-unit-observation-2baf722f-v3')
(HERE / 'root-metadata-selection-v3.json').write_text(metadata)
(HERE / 'root-metadata-provenance-v1.json').write_bytes((OLD / 'root-metadata-provenance-v1.json').read_bytes())
namespace = runpy.run_path(str(HERE / 'prepare_envelope_v3.py'), run_name='inert_source_only_builder')
print(json.dumps(namespace['build'](json.loads(metadata)), sort_keys=True))
test = (OLD / 'test_envelope_v2.py').read_text().replace('linux_observation_envelope_v2.py', 'linux_observation_envelope_v3.py').replace('prepare_envelope_v2.py', 'prepare_envelope_v3.py').replace('control/envelope-policy-v2.json', 'control/envelope-policy-v3.json')
test = test.replace("text = SOURCE.read_text(); inverse = json.loads((HERE / 'entry-inverse-v2.json').read_bytes())", "text = SOURCE.read_text()\n        for row in reversed(json.loads((HERE / 'entry-inverse-v3.json').read_bytes())['replacements']):\n            text = text.replace(row['new'], row['old'])\n        inverse = json.loads((HERE.parent / 'normalized-unit-envelope-v2/entry-inverse-v2.json').read_bytes())")
(HERE / 'test_envelope_v3.py').write_text(test)
