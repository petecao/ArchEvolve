"""2026-10-16 ET. Pure canonical preparation; no external tools or project jobs."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
ATTEMPTS = []


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise RuntimeError('pure typed preparation rejects '+event)


sys.addaudithook(audit)
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True
from swdb import vector_allocating_payload as payload

directory = HERE/'inert-v1'
plan = payload.prepare(directory)
assert payload.check(directory) == plan
paths = sorted(path for path in directory.rglob('*') if path.is_file())
rows = [pin(path) for path in paths]
manifest = {'date': '2026-10-16 ET', 'root': str(directory), 'files': rows,
            'file_count': len(rows), 'bytes': sum(row['bytes'] for row in rows),
            'directory_count': sum(path.is_dir() for path in directory.rglob('*'))}
(HERE/'canonical-manifest-v1.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n')
controls = []
for path in sorted((HERE/'history').glob('*/result.json')):
    result = json.loads(path.read_bytes())
    controls.append({'artifact': pin(path), 'stage': result['stage'], 'passed': result['passed'],
                     'failed': result['failed'], 'external_attempts_after_audit': result['external_attempts_after_audit']})
source_names = ('swdb/vector_allocating_payload.py', 'swdb/vector_typed_payload.mlw',
                'tests/test_vector_allocating_payload.py')
input_names = ('swdb/std_models.py', 'swdb/c_lowering.py', 'swdb/heap_reallocation.mlw',
               '.scratch/probata-proof-of-concept-2026-10-13/issues/22-saw-adapter-and-translator.md',
               '.scratch/probata-proof-of-concept-2026-10-13/issues/25-vector-and-pair-models.md',
               '.scratch/probata-proof-of-concept-2026-10-13/prototype/25-owned-closed-move-20261016/floating-semantics-research-v1/primary-source-observation-v1.json')
primary = Path('/Users/yanrujhou/.opam/framac-33/share/why3/stdlib/ieee_float.mlw')
cfloat = Path('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/Cfloat.ml')
preparation = {'date': '2026-10-16 ET', 'classification': 'ISOLATED_TYPED_SOURCE_TRANSPORT_PREPARATION_PENDING_REVIEW',
    'source_and_tests': [pin(PROJECT/name) for name in source_names],
    'observed_context_inputs': [pin(PROJECT/name) for name in input_names],
    'primary_semantic_references': [
        {'artifact': pin(primary), 'range': [117, 118], 'role': 'C-style float eq differs from logical equality'},
        {'artifact': pin(cfloat), 'ranges': [[52, 59], [242, 254], [436, 459]], 'role': 'selected model distinction and Real-mode erasure'}],
    'readme': pin(HERE/'README.md'), 'harness': pin(HERE/'run_pure.py'), 'materializer': pin(Path(__file__)),
    'canonical': pin(HERE/'canonical-manifest-v1.json'), 'file_count': len(rows),
    'canonical_bytes': sum(row['bytes'] for row in rows), 'original_source_units': len(plan['source_members']),
    'mathematical_targets': [{'id': row['id'], 'goal': row['goal'], 'sha256': row['sha256']}
                             for row in plan['mathematical_obligations']],
    'controls': controls, 'external_attempts_after_audit': ATTEMPTS,
    'source_or_theory_parsed_by_compiler_or_prover': False,
    'actual_native_or_formal_or_remote_execution': False,
    'source_Heap_Typed_or_model_or_caller_admission': False,
    'source_semantics_correction': {
        'early_ACSL_equality_conflation_preserved_as_history_but_withdrawn': True,
        'original_ACSL_NaN_counterexample_established': False,
        'plain_ACSL_equality_is_C_IEEE_comparison': False,
        'nonfinite_source_logical_promotion_and_mode_coverage_established': False,
        'original_sources_or_historical_evidence_modified': False,
        'reviewed_new_explicit_nonfinite_model_identity_and_rebind_requested_by_root': True,
        'permanent_non_NaN_caller_carveout': False,
        'candidate_value_class_relation_includes_NaNs_without_bit_identity': True},
    'mechanical_authoring_history': 'An earlier documentation apply_patch tool script had a JavaScript syntax error before execution; no files were written by that refused call.',
    'scope': 'pure complete source/inverse/typed product/effect/affine induction implementation; actual theorem and source admission stay separate'}
assert not ATTEMPTS
(HERE/'preparation-v1.json').write_text(json.dumps(preparation, sort_keys=True, indent=2)+'\n')
packet = {'date': '2026-10-16 ET', 'kind': 'typed-allocating-payload-source-v1',
          'preparation': pin(HERE/'preparation-v1.json'),
          'canonical': pin(HERE/'canonical-manifest-v1.json'),
          'source_and_tests': preparation['source_and_tests'], 'actual_execution_admitted': False,
          'source_or_caller_admission': False}
(HERE/'source-packet-v1.json').write_text(json.dumps(packet, sort_keys=True, indent=2)+'\n')
print(json.dumps({'packet': pin(HERE/'source-packet-v1.json'), 'preparation': pin(HERE/'preparation-v1.json'),
                  'files': len(rows), 'bytes': manifest['bytes'], 'targets': len(plan['mathematical_obligations']),
                  'source_and_tests': preparation['source_and_tests']}, sort_keys=True, indent=2))
