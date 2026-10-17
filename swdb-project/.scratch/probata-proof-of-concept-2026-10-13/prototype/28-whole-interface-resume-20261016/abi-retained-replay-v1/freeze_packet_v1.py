"""2026-10-16 Eastern. Freeze local source/pins only; never execute replay main."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(path, value):
    path.write_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n')

def freeze():
    own = sorted(path for path in HERE.rglob('*') if path.is_file() and path.name != 'source-packet-v1.json')
    assert all(not path.is_symlink() for path in own)
    assert not list(HERE.rglob('__pycache__'))
    for path in own:
        if path.suffix == '.py':
            ast.parse(path.read_bytes())
    basis = [
        WHOLE / 'abi-role-diagnostic-v1/read_abi_census_v1.py',
        WHOLE / 'abi-role-transport-v2/source-packet-v2.json',
        WHOLE / 'abi-role-transport-v2/abi_role_transport_v1.py',
        WHOLE / 'abi-role-transport-v2-independent-review/independent-abi-v2-source-review-20261016.json',
        WHOLE / 'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py',
        WHOLE / 'normalized-unit-observation-v1/modules/closed_python_surface.py',
        WHOLE / 'whole_interface_v4.py',
        WHOLE / 'compiler_abi_probe_v1.cpp',
        WHOLE / 'role-normalized-gzip-v2/role_normalized_gzip_v2.py',
        WHOLE / 'streaming-minify-v1/strict_minify_v2.py',
        WHOLE / 'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json',
        WHOLE / 'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json',
        WHOLE / 'compiler-memory-capture-v1-actual/closure-stdout-v1.json',
        WHOLE / 'normalized-unit-envelope-v3-actual/status-stdout-v3.json',
    ]
    policy = json.loads((HERE / 'controls/policy.json').read_bytes())
    inverse = json.loads((HERE / 'scanner-inverse-v1.json').read_bytes())
    command = json.loads((HERE / 'command-v1.json').read_bytes())
    assert pin(HERE / 'replay_entry_v1.py') == command['stdin']
    assert len(policy['known']) == 116 and len(policy['runtime_hashes']) == 2569
    for row in inverse['complete_module_bytes_unchanged'].values():
        assert Path(row['basis']['path']).read_bytes() == Path(row['staged']['path']).read_bytes()
    result = {
        'schema': 'retained-ABI-replay-source-packet-1', 'date': '2026-10-16 Eastern',
        'owned': [pin(path) for path in own], 'basis': [pin(path) for path in basis],
        'controls': {'pure_test_cases': 8, 'no_child_native_network_project_import': True,
                     'synthetic_29_roots_only': True, 'actual_original_ABI_payload_used': False},
        'original_artifacts': policy['artifacts'],
        'historical_boundaries': {'G639': 'original full-TU duplicate-key refusal',
                                 'G625': 'original private ABI-observer Refused',
                                 'G642': 'four-zero-exit compiler observation only'},
        'no_actual_execution': True, 'root_once_admission_required': True,
        'source_call_ABI_theorem_native_public_acceptance': False,
        'physical_module_paths_separate_from_stable_semantic_receipt': True,
        'resource': policy['resource'], 'fresh_outer_Git_and_settled_output_required': True,
    }
    save(HERE / 'source-packet-v1.json', result)
    return pin(HERE / 'source-packet-v1.json')

if __name__ == '__main__':
    print(json.dumps(freeze(), sort_keys=True))
