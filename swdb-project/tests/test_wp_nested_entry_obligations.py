"""Nested source reads keep independent inner and outer obligations; 2026-10-15 ET."""
import json

import pytest
import yaml

from conftest import run_swdb
import test_cbmc_adapter as cbmc
import test_proof_semantics as dx
import test_wp_adapter as wp

UNIT = '\nint nested_read(int *q,int *base,int n) { return base[q[0]]; }\n'


@pytest.fixture(scope='module')
def nested_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp('nested-obligations')
    requires = ('requires n == 1 && \\valid(q) && \\valid(base);\n'
                'requires q[0] == 0 && base[0] == 1;')
    fixtures = {**dx.FIXTURES, 'nested_read': ('nested_read', ['q', 'base'], requires, '\\nothing', 1)}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dx, 'UNITS', dx.UNITS + UNIT)
        patch.setattr(dx, 'FIXTURES', fixtures)
        candidate = dx.build_dx_seed(root)
    path = root / 'library/rewrite_contracts/fixture_dx_nested_read.yaml'
    data = yaml.safe_load(path.read_text())
    data['proof_unit']['array_domains'] = {p: {'extent': 'n'} for p in ('q', 'base')}
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return cbmc.Seed(root, {'safe': candidate})


@pytest.fixture
def nested_case(nested_seed, tmp_path):
    import shutil
    for name in ('records', 'library'):
        shutil.copytree(nested_seed.root / name, tmp_path / name)
    return cbmc.Seed(tmp_path, nested_seed.candidates)


def prove(seed, *, fake=False):
    result = run_swdb('prove', '--records', seed.records, '--candidate', seed.candidates['safe'],
        '--function', 'nested_read', '--contract', 'contract.fixture_dx_nested_read', '--adapter', 'wp',
        '--runs-dir', seed.runs, '--format', 'json', timeout=3600, env=wp.fake('unknown') if fake else None)
    assert result.returncode == 0, result.stderr + result.stdout
    return seed.read(json.loads(result.stdout))


@wp.needs_wp
@pytest.mark.parametrize('case,goal', [('safe', None), ('inner_window', 'swdb_window_access'),
    ('outer_window', 'swdb_window_access'), ('uninitialized_inner', 'initialization'),
    ('null_inner', 'swdb_window_access')])
def test_actual_ordered_nested_read_obligations(nested_case, case, goal):
    path = nested_case.root / 'library/rewrite_contracts/fixture_dx_nested_read.yaml'
    data = yaml.safe_load(path.read_text())
    if case in {'inner_window', 'null_inner'}:
        data['proof_unit']['array_domains']['q']['extent'] = '0'
    elif case == 'outer_window':
        data['proof_unit']['array_domains']['base']['extent'] = '0'
    if case in {'uninitialized_inner', 'null_inner'}:
        for clause in data['clauses']:
            if clause.get('acsl'):
                text = clause['acsl']['text'].replace('requires \\initialized(q + (0 .. n - 1));', '')
                if case == 'null_inner':
                    text = text.replace('\\valid(q)', 'q == \\null').replace('q[0] == 0 && ', '')
                clause['acsl']['text'] = text
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    record = prove(nested_case)
    assert len(record['settings']['nested_entry_reads']['certificate']['captures']) == 1
    if case == 'safe':
        assert record['verdict'] == 'proven', record.get('unproven_properties')
    else:
        assert record['verdict'] == 'not_proven', record
        assert any(goal in g['goal'] and g['status'] != 'valid' for g in record['goals']), record
