"""Shared LLVM and hand-target fixtures. Updated: 2026-10-06 ET."""
from pathlib import Path
import pytest
import yaml

@pytest.fixture
def llvm22():
    import os
    import subprocess
    candidate = Path(os.environ.get('SWDB_LLVM_BIN', '/opt/homebrew/opt/llvm/bin'))
    if not all((candidate / tool).is_file() for tool in ('llvm-config', 'clang++', 'opt')):
        pytest.skip('LLVM 22 llvm-config/clang++/opt required')
    version = subprocess.run([candidate / 'llvm-config', '--version'], capture_output=True, text=True)
    if version.returncode or not version.stdout.startswith('22.'):
        pytest.skip('LLVM 22 required')
    return candidate

def target_description(tmp_path, bandwidth=32.0):
    params = {name + '_ops_per_s': {'value': (16.0 if name == 'floating_point' else 1e9),
        'basis': 'reported', 'source': 'Hand-computed test fixture; not mbit10 measurement.', 'unit': 'operations/s'}
        for name in ('integer', 'floating_point', 'branch', 'atomic')}
    target = {'kind': 'target_description', 'schema_version': '0.4', 'id': 'fixture.target',
        'status': 'draft', 'created': '2026-10-06', 'updated': '2026-10-06',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Hand-computed test fixture.', 'uri': None}],
        'format': 'swdb.target-description.v1', 'version': '1', 'target': 'mbit10', 'threads': 1,
        'estimator_variant': 'team', 'calibration_sources': [], 'dram_address_layout': None,
        'mechanisms': [{'model': 'compute_throughput', 'parameters': params},
            {'model': 'streaming_bandwidth', 'parameters': {'bytes_per_s': {'value': bandwidth,
                'basis': 'unknown' if bandwidth is None else 'reported',
                'source': 'Hand-computed test fixture; not mbit10 measurement.', 'unit': 'bytes/s'}}}]}
    path = tmp_path / 'target.yaml'
    path.write_text(yaml.safe_dump(target, sort_keys=False))
    return path


def freeze_protocol(records, tmp_path, target, *, roi, threads=1, input_id='kron-g16-k16', arguments=None):
    """Freeze through the public command; fixture protocols are isolated copied-store data."""
    import json
    from conftest import run_swdb
    settings={'mode':'estimated','estimator_version':'swdb.analytic.v1',
        'target_description':str(target),'inputs':[input_id],'roi':roi,'threads':threads}
    if arguments is not None:settings['input_run_arguments']={input_id:arguments}
    file=tmp_path/'freeze.yaml'
    file.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.estimate.protocol',
        'version':1,'settings':settings},sort_keys=False))
    result=run_swdb('freeze-protocol',file,'--records',records,'--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return json.loads(result.stdout)['id']


import json

def digest(data):
    import hashlib
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False, default=lambda value: value.isoformat()).encode()).hexdigest()

def fixture_characterization(team, subject_id='gapbs-bfs-do', input_id='kron-g16-k16', **binding_changes):
    # Zero-work contract fixture tests binding only; these placeholders never
    # stand in for LLVM characterization or application execution evidence.
    data = {'kind': 'workload_characterization', 'schema_version': '0.4', 'id': 'fixture.counts',
        'status': 'draft', 'created': '2026-10-06', 'updated': '2026-10-06',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Zero-work binding contract fixture.'}],
        'format': 'swdb.workload-characterization.v1', 'subject': {'kind': 'implementation', 'id': subject_id},
        'input': input_id, 'source': {'path': 'fixture.cpp', 'sha256': '0' * 64,
            'build_flags': [], 'run_arguments': [], 'protected_driver': 'fixture'},
        'host': {'machine': 'fixture', 'architecture': 'fixture', 'system': 'fixture'},
        'toolchain': {'llvm_version': '22.fixture', 'llvm_bin': 'fixture', 'compiler_flags': [],
                      'plugin_linkage': 'host_symbols', 'run_library_paths': []},
        'counting': {'level': 'source_normalized_ir', 'passes': [], 'native_runs': 1, 'basis': 'measured',
            'vector_multiplicity': 'fixture', 'operation_definition': 'fixture', 'loop_definition': 'fixture',
            'binary_sha256': '0' * 64, 'counts_sha256': '0' * 64, 'output_directory': 'fixture'},
        'static_analysis': {'basis': 'code_reading', 'source_ir_sha256': '0' * 64,
            'optimized_ir_sha256': '0' * 64, 'loops': [], 'optimized_facts': {}, 'mapping_note': 'fixture'},
        'coverage': {'scope': 'contract fixture'}, 'regions': [], 'unmapped_loops': [], 'unmodeled_calls': [],
        'evidence_kind': 'contract_fixture', 'binding': {'state': 'fixture',
            'subject_source_identity': {'subject_record_sha256': digest(yaml.safe_load((team / 'implementations' / (subject_id + '.yaml')).read_text()))},
            'input_record_sha256': digest(yaml.safe_load((team / 'inputs' / (input_id + '.yaml')).read_text())),
            'roi': 'fixture.stream.v1', 'threads': 1, 'run_arguments_sha256': digest([]),
            'note': 'Binding contract fixture only.', **binding_changes}}
    data['identity_sha256'] = digest(data)
    path = team / 'workload_characterizations/fixture.counts.yaml'
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return data
