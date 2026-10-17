"""Freeze the inherited source route plus narrow nonadmitting profile repair."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import stat
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'production-route-v4'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


old_packet_path = OLD / 'source-packet-v4.json'
assert pin(old_packet_path)['sha256'] == '7e36fbf2dc634a62e1c9eb4350005d308f8ab3c32a44fc522e2abdafa9eb1565'
old_packet = json.loads(old_packet_path.read_bytes())
for row in old_packet['files']:
    assert pin(Path(row['path'])) == row
namespace = runpy.run_path(str(HERE / 'test_profile_streams_v5.py'), run_name='pure_v5_control_support')
suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['PRIOR']['CompositionControls']))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['StreamControls']))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
(HERE / 'pure-controls-v5.log').write_text(stream.getvalue())
assert result.testsRun == 29 and result.wasSuccessful() and not result.skipped
(HERE / 'pure-controls-v5.json').write_text(json.dumps({'tests':29, 'unchanged_V4_controls':21,
    'new_streaming_actual_shape_and_inverse_controls':8, 'errors':0, 'failures':0, 'skipped':0,
    'no_child_project_import_compiler_native_solver_SSH_Git_or_actual_preparation':True,
    'log':pin(HERE / 'pure-controls-v5.log')}, sort_keys=True, indent=2) + '\n')
files = []
for path in sorted(HERE.rglob('*')):
    if path.is_dir(): continue
    assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    if path.name == 'source-packet-v5.json': continue
    files.append(pin(path))
packet = {'schema':'coherent-checked-source-production-profile-proposal-5', 'date':'2026-10-16 ET',
    'predecessor':pin(old_packet_path), 'files':files,
    'production_patch':old_packet['patch'], 'production_paths_and_exact_bases':old_packet['production_paths_and_exact_bases'],
    'production_source_model_native_Plan_contracts_and_all_50_paths_unchanged':True,
    'source_base_commit':old_packet['source_base_commit'], 'proposed_production_paths':50,
    'profile_builder':pin(HERE / 'profile/profile_builder_v4.py'),
    'profile_prepare':pin(HERE / 'profile/profile_prepare_v4.py'),
    'normal_producer_basis':pin(HERE / 'profile/normal-producer-basis-v4.json'),
    'descriptor_source':pin(WHOLE / 'compiler-descriptor-v1/passive-read-stdout-v1.json'),
    'prospective_descriptor':pin(WHOLE / 'compiler-descriptor-v1/expected-absolute-compiler-descriptor-v1.json'),
    'descriptor_provenance':pin(WHOLE / 'compiler-descriptor-v1/descriptor-provenance-v1.json'),
    'input_map':pin(HERE / 'first-profile-input-map-v5.json'),
    'tests':29, 'shared_production_written':False, 'Git_mutated':False, 'scientific_execution':False,
    'actual_root_descriptor_selection':'pending external root receipt',
    'actual_source_preparation_ownership_public_proofs_and_persisted_audits':'pending root admission',
    'public_admission':False, 'whole_ticket28_acceptance':False}
(HERE / 'source-packet-v5.json').write_text(json.dumps(packet, sort_keys=True, indent=2) + '\n')
print(json.dumps({name:pin(HERE / path) for name,path in {'packet':'source-packet-v5.json',
    'builder':'profile/profile_builder_v4.py', 'preparer':'profile/profile_prepare_v4.py',
    'input_map':'first-profile-input-map-v5.json'}.items()}, sort_keys=True))
