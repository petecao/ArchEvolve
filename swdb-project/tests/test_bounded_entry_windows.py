"""Primitive declared windows through public bounded prove; created 2026-10-15 ET.

The same numerical checks must execute in the C lowering and C++ replay.
Physical buffer capacity is deliberately larger than the declared window.
"""
import json

import pytest
import yaml

import test_cbmc_adapter as cbmc
from test_entry_array_domains import window_seed  # noqa: F401
from conftest import run_swdb


def prove(seed, unit, define=None):
    extra = ['--define', define] if define else []
    result = run_swdb('prove', '--records', seed.records,
        '--candidate', seed.candidates['safe'], '--function', unit,
        '--contract', 'contract.fixture_dx_' + unit, '--adapter', 'cbmc',
        '--bounds', '{"threads":1,"n":4}', '--runs-dir', seed.runs,
        '--format', 'json', *extra, timeout=900)
    assert result.returncode == 0, result.stdout + result.stderr
    return seed.read(json.loads(result.stdout))


@cbmc.needs_cbmc
def test_bounded_primitive_window_proves_legal_one_past(window_seed):
    record = prove(window_seed, 'window_form')
    assert record['verdict'] == 'proven', record
    assert record['settings']['array_domains']['source_operations_checked'] is True
    assert any('swdb_window_formation' in g['property'] for g in record['goals'])
    assert record['settings']['agreement']['verdict'] == 'agree'


@cbmc.needs_cbmc
@pytest.mark.parametrize('unit,define,property_name', [
    ('window_read', 'WINDOW_OUTSIDE', 'swdb_window_access'),
    ('window_form', 'WINDOW_MUTATE_EXTENT', 'swdb_window_formation'),
])
def test_bounded_logical_window_failures_replay_on_source_cpp(window_seed, unit, define, property_name):
    record = prove(window_seed, unit, define)
    assert record['verdict'] == 'refuted', record
    assert record['settings']['array_domains']['source_operations_checked'] is True
    assert record['settings']['agreement']['verdict'] == 'agree'
    assert property_name in record['counterexample']['property'], record
    assert record['counterexample']['replay']['replayed'] is True
    assert record['counterexample']['replay']['form'] == 'cxx'


@cbmc.needs_cbmc
def test_bounded_math_cancellation_cannot_hide_an_overflowing_intermediate(window_seed):
    path = window_seed.root / 'library/rewrite_contracts/fixture_dx_window_form.yaml'
    original = path.read_text()
    data = yaml.safe_load(original)
    factor = '18446744073709551615 * 18446744073709551615'
    data['proof_unit']['array_domains']['p']['extent'] = factor + ' - ' + factor
    try:
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        record = prove(window_seed, 'window_form')
        assert record['verdict'] == 'not_proven', record
        assert record['failure_class'] == 'unsupported_construct'
        assert record['settings']['verifier_launched'] is False
        assert not record['goals']
        assert '128-bit' in record['settings']['array_domains']['refusal'], record
    finally:
        path.write_text(original)
