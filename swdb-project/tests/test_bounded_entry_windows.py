"""Primitive declared windows through public bounded prove; created 2026-10-15 ET.

The same numerical checks must execute in the C lowering and C++ replay.
Physical buffer capacity is deliberately larger than the declared window.
"""
import json

import test_cbmc_adapter as cbmc
from test_entry_array_domains import window_seed  # noqa: F401
from conftest import run_swdb


@cbmc.needs_cbmc
def test_bounded_primitive_window_proves_legal_one_past(window_seed):
    seed = window_seed
    result = run_swdb('prove', '--records', seed.records,
        '--candidate', seed.candidates['safe'], '--function', 'window_form',
        '--contract', 'contract.fixture_dx_window_form', '--adapter', 'cbmc',
        '--bounds', '{"threads":1,"n":4}', '--runs-dir', seed.runs,
        '--format', 'json', timeout=900)
    assert result.returncode == 0, result.stdout + result.stderr
    record = seed.read(json.loads(result.stdout))
    assert record['verdict'] == 'proven', record
    assert record['settings']['array_domains']['source_operations_checked'] is True
    assert any('swdb_window_formation' in g['property'] for g in record['goals'])
    assert record['settings']['agreement']['verdict'] == 'agree'
