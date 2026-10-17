"""2026-10-16 ET. Offline deterministic envelope selection; never executes it.

The optional ROOT_METADATA JSON supplies five freshly rehashed retained-file
pins, the root normal-guard hashes, a source-review/admission provenance pin and
one selected node. Missing inputs stay null in the visibly inert templates.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent
OBSERVER = HERE / 'observer'
TRACE = WHOLE.parent / '28-public-memory-trace-resume-20261016'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v5'
ORIGINAL = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10'
TRANSFORM = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2'
PROJECT = '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project'
MISSING = ('component/compiler-observation.json', 'capture-runtime-before.json', 'capture-runtime-after.json',
           'capture-zlib-before.json', 'capture-zlib-after.json')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pin(path, remote=None):
    raw = path.read_bytes()
    return {'path': str(path) if remote is None else remote, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def data(path): return json.loads(path.read_bytes())


def checked_metadata(value):
    if type(value) is not dict or set(value) != {'retained_pins', 'guard_files', 'root_admission_receipt', 'node'}:
        raise ValueError('closed root metadata selection required')
    if type(value['retained_pins']) is not dict or set(value['retained_pins']) != set(MISSING):
        raise ValueError('exact five retained original metadata pins required')
    for name, row in value['retained_pins'].items():
        if type(row) is not dict or set(row) != {'path', 'bytes', 'sha256'} or row['path'] != ORIGINAL + '/' + name:
            raise ValueError('literal original retained-file role differs')
        if type(row['bytes']) is not int or not 0 <= row['bytes'] <= 4194304 or type(row['sha256']) is not str or len(row['sha256']) != 64:
            raise ValueError('bounded retained metadata pin required')
        int(row['sha256'], 16)
    guards = value['guard_files']
    if type(guards) is not dict or set(guards) != {'execute.py', 'watch.py'} or not all(type(v) is str and len(v) == 64 for v in guards.values()):
        raise ValueError('root normal-guard hashes required')
    if type(value['node']) is not int or value['node'] not in (0, 1): raise ValueError('one explicit root-selected node required')
    receipt = value['root_admission_receipt']
    if type(receipt) is not dict or set(receipt) != {'path', 'bytes', 'sha256'} or not Path(receipt['path']).is_absolute():
        raise ValueError('external root receipt pin required')
    if receipt['path'].startswith(RAW + '/observer/control/'):
        raise ValueError('root receipt must remain outside observer/control')
    return value


def build(metadata=None):
    metadata = checked_metadata(metadata) if metadata is not None else None
    staged = {}; origins = {}
    def stage(path, basename=None):
        name = path.name if basename is None else basename
        if name in staged: raise ValueError('duplicate flat root control basename')
        staged[name] = pin(path, RAW + '/control/' + name); origins[name] = pin(path)
        return staged[name]
    template = data(OBSERVER / 'observation-policy-template-v3.json')
    for name in template['controls']:
        stage(OBSERVER / name if (OBSERVER / name).exists() else OBSERVER / 'modules' / name)
    stage(HERE / 'linux_observation_envelope_v5.py')
    for name in ('python_startup_roles_v2.py', 'python_role_observer_v2.py'): stage(TRACE / name)
    stage(WHOLE / 'linux_native86_entry_v4.py')
    stage(POC / 'evidence/resume-20261016-lane-coordination/t28-linux-runtime-observer-v2-actual-20261016.json')
    review = stage(POC / 'evidence/t28-normalized-unit-observer-v1-root-standards-review-20261016.json', 'root-source-review.json')
    if metadata is not None and metadata['root_admission_receipt'] != review:
        raise ValueError('root receipt is the fixed staged source-review provenance, never execution authority')
    mirrors = {
        'transform-command.json': WHOLE / 'role-normalization-controller-v2/command_v2.json',
        'transform-bootstrap.py': WHOLE / 'role-normalization-controller-v2/bootstrap_v2.py',
        'transform-execution.json': WHOLE / 'role-normalization-controller-v2-actual/root-observed-execution-v2.json',
        'transform-stdout.json': WHOLE / 'role-normalization-controller-v2-actual/actual-transform-stdout-v2.json',
        'transform-stderr.log': WHOLE / 'role-normalization-controller-v2-actual/actual-transform-stderr-v2.log'}
    for name, path in mirrors.items(): stage(path, name)
    runtime_path = WHOLE / 'compiler-capture-v10/linux_compiler_capture_policy_v10.json'
    runtime = data(runtime_path)
    # This describes the already-observed exact builtin decoder and its physical
    # origins; it does not claim a new runtime probe or grant decoder admission.
    zlib = runtime['zlib_binding']
    descriptor = {'schema': 'selected-stdlib-zlib-runtime-1', 'origin': zlib['spec_origin'],
        'version': zlib['ZLIB_RUNTIME_VERSION'],
        'physical_inputs': [zlib['physical_interpreter'], *zlib['mapped_compression_objects']]}
    (HERE / 'selected-zlib-runtime.json').write_bytes(canonical(descriptor))
    stage(HERE / 'selected-zlib-runtime.json')
    source = stage(WHOLE / 'source_call_fixture_v2.cpp')
    known = data(WHOLE / 'role-normalization-controller-v2/source_policy_v2.json')['physical_inputs']
    after = data(WHOLE / 'role-normalization-controller-v2-actual/actual-postflight-v2-stdout.json')
    output = after['output_pins']
    def old(name): return {'path': ORIGINAL + '/' + name, **known[ORIGINAL + '/' + name]}
    def derived(name): return {'path': TRANSFORM + '/' + name, **output[TRANSFORM + '/' + name]}
    original_roles = {'policy': old('control/linux_compiler_capture_policy_v10.json'), 'result': old('component/result.json'),
        'gzip_receipt': old('component/caller.ast.gzip.json'), 'compressed_tu': old('component/caller.ast.json.gz'),
        'abi': old('component/abi.ast.json'), 'probe': old('control/compiler_abi_probe_v1.cpp'),
        'source': old('control/source_call_fixture_v2.cpp'), 'source_after': old('source-after.json'),
        'zlib_runtime': staged['selected-zlib-runtime.json']}
    role_names = {'observation': MISSING[0], 'runtime_before': MISSING[1], 'runtime_after': MISSING[2],
                  'zlib_before': MISSING[3], 'zlib_after': MISSING[4]}
    original_roles.update({role: metadata['retained_pins'][name] if metadata is not None else None for role, name in role_names.items()})
    capture = {'kind': template['capture']['kind'], 'original': original_roles, 'prepared': None,
        'transform': {'controller': derived('control/controller.py'), 'command': staged['transform-command.json'],
            'bootstrap': staged['transform-bootstrap.py'], 'policy': derived('control/policy.json'),
            'result': derived('result.json'), 'transport': derived('component/transport.json'),
            'inverse': derived('component/inverse.json'), 'manifest': derived('component/rename-manifest.jsonl'),
            'normalized_gzip': derived('component/caller.normalized.json.gz'), 'complete_census': derived('control/census.json'),
            'execution': staged['transform-execution.json'], 'stdout': staged['transform-stdout.json'], 'stderr': staged['transform-stderr.log']}}
    selected = {**template, 'original_project': PROJECT, 'library_root': RAW + '/library_fixture', 'output_root': RAW + '/observer',
        'capture': capture, 'controls': {name: {**staged[name], 'path': RAW + '/observer/control/' + name} for name in template['controls']},
        'root_admission_receipt': metadata['root_admission_receipt'] if metadata is not None else None}
    observer_path = HERE / ('observation-policy-v1.json' if metadata is not None else 'observation-policy-template-v3.json')
    observer_path.write_bytes(canonical(selected))
    observer_pin = stage(observer_path, 'observation-policy-v1.json')
    envelope = {'schema': 'linux-normalized-unit-observation-envelope-1', 'raw_name': RAW.rsplit('/', 1)[1],
        'source_commit': runtime['source_commit'], 'source_project': PROJECT, 'python': runtime['python'],
        'node': metadata['node'] if metadata is not None else None,
        'budgets': {'whole_seconds': 1200, 'entry_seconds': 1180, 'rss_bytes': 4294967296, 'total_bytes': 268435456,
                    'file_bytes': 4194304, 'control_bytes': 1048576},
        'guard_files': metadata['guard_files'] if metadata is not None else None, 'disk_floor_bytes': 21474836480,
        'runtime_policy': pin(runtime_path, ORIGINAL + '/control/linux_compiler_capture_policy_v10.json'),
        'controls': staged, 'observer_policy': {**observer_pin, 'path': RAW + '/observer/control/observation-policy-v1.json'},
        'library_source': {**source, 'path': RAW + '/library_fixture/proof_units/source.cpp'},
        'root_admission_receipt': selected['root_admission_receipt']}
    envelope_path = HERE / ('envelope-policy-v5.json' if metadata is not None else 'envelope-policy-template-v5.json')
    envelope_path.write_bytes(canonical(envelope))
    total = sum(row['bytes'] for row in staged.values()) + envelope_path.stat().st_size
    if total > 1048576: raise ValueError('complete root control packet exceeds one MiB')
    command = {'schema': 'root-reviewed-normalized-unit-envelope-command-1', 'actual_executed': False,
        'root_admission_required': True, 'raw': RAW, 'source_commit': runtime['source_commit'], 'source_project': PROJECT,
        'argv': [runtime['python'], '-I', '-B', '-X', 'pycache_prefix=' + RAW + '/entry-source-cache',
            RAW + '/control/linux_observation_envelope_v5.py', RAW, RAW + '/control/envelope-policy-v5.json', pin(envelope_path)['sha256']],
        'policy': pin(envelope_path), 'stage_sources': origins, 'root_controls_bytes_including_policy': total,
        'copies': [{'from': RAW + '/control/' + name, 'to': row['path']} for name, row in selected['controls'].items()] +
            [{'from': observer_pin['path'], 'to': envelope['observer_policy']['path']},
             {'from': source['path'], 'to': envelope['library_source']['path']}],
        'root_created_directories': [RAW + '/control'],
        'envelope_created_directories': [RAW + '/observer', RAW + '/observer/control', RAW + '/library_fixture', RAW + '/library_fixture/proof_units'],
        'closed_environment': {'PATH': runtime['path'], 'HOME': runtime['home'], 'LANG': 'C', 'LC_ALL': 'C',
            'PROBATA_OUTPUT': RAW, 'SWDB_VERIFIER_LOCK': RAW + '/verifier.lock', 'SWDB_VERIFIER_RSS_CAP_BYTES': '4294967296',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': RAW + '/entry-source-cache',
            'PYTHONNOUSERSITE': '1', 'PYTHONSAFEPATH': '1', 'SETUPTOOLS_USE_DISTUTILS': 'local', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'},
        'root_injected_lane_environment': ['LACT_SOCKET_LANE_PID', 'LACT_SOCKET_LANE_GENERATION'],
        'guard': {'whole_seconds': 1200, 'rss_bytes': 4294967296, 'workers': 1, 'retained_bytes': 268435456},
        'root_metadata_complete': metadata is not None,
        'root_launcher': pin(WHOLE / 'root-launcher-loader-v11/launch_observer_loader_v11.py'),
        'root_launch_requirements': {'rss_cap_bytes': 4294967296, 'run_environment_unset': ['LIBRARY_PATH', 'LD_LIBRARY_PATH'],
            'finite_postflight_required': ['source unchanged', 'leases released', 'selected processes absent with zero read failures',
                                           'outer and inner resources settled', 'closed raw size/hash census']},
        'scope': 'Data-only actual complete-TU/ABI/call observation; no model/native/solver/ownership/public admission'}
    (HERE / ('command-v5.json' if metadata is not None else 'command-template-v5.json')).write_bytes(canonical(command))
    (HERE / 'missing-root-metadata-template-v1.json').write_text(json.dumps({'retained_pins': {name: None for name in MISSING},
        'guard_files': {'execute.py': None, 'watch.py': None}, 'root_admission_receipt': None, 'node': None}, sort_keys=True, indent=2) + '\n')
    return {'staged_controls': len(staged), 'staged_total_bytes_including_policy': total, 'root_metadata_complete': metadata is not None,
            'observer_code_selected': pin(OBSERVER / 'observe_entry_v3.py')['sha256'], 'actual_executed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root-metadata', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(None if args.root_metadata is None else data(args.root_metadata)), sort_keys=True))
