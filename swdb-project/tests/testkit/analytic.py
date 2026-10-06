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
