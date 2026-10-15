"""Public proof-admission refusal matrix; created 2026-10-15 ET.

No declaration-only plan may launch a bounded verifier through the factory.
"""
import shutil

import pytest
import yaml

from conftest import FIXTURES, make_records, run_swdb
from test_formal_frame import UNIT_CC, frame_contract, write_library
from swdb import c_lowering


@pytest.mark.skipif(bool(c_lowering.locate().missing), reason='clang 22.1.8 binds real proof parameters')
@pytest.mark.parametrize('adapter', ['cbmc', 'crux-llvm-c', 'crux-llvm-cxx', 'bounded', 'scripted'])
def test_all_public_bounded_routes_stay_closed_without_source_operation_admission(tmp_path, adapter):
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    entry = frame_contract('contract.fixture_array_domain', role='enabling')
    entry['proof_unit']['array_domains'] = {'parent': {'extent': 'n'}}
    write_library(library, {'proof_units/fixture_unit.cc': UNIT_CC,
                           'rewrite_contracts/array_domain.yaml': entry})
    methods = library / 'methods'
    methods.mkdir()
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    marker = tmp_path / 'must-not-run'
    script = tmp_path / 'script.yaml'
    script.write_text(yaml.safe_dump({'verdict': 'proven', 'run': ['touch', str(marker)]}))
    runs = tmp_path / 'runs'
    result = run_swdb('prove', '--records', records.path, '--summary', 'contract.fixture_array_domain',
                      '--adapter', adapter, '--script', script, '--bounds', '{"threads":1,"n":3}',
                      '--runs-dir', runs)
    assert result.returncode == 2, result.stdout + result.stderr
    assert 'array_domains' in result.stderr and 'origin certificate' in result.stderr
    assert not marker.exists() and not runs.exists()
