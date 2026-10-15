"""Entry-scope proof hints across checked source views; 2026-10-15 ET."""
import json

import pytest
import yaml

from conftest import run_swdb
from test_proof_semantics import dx, dx_seed
from test_wp_adapter import needs_wp
from test_wp_helper_windows import _contract, _run
from test_wp_nested_local import CONTRACT, seed
from test_wp_adapter import fake


@needs_wp
def test_checked_helpers_keep_a_pure_assertion_at_the_original_unit_entry(dx):
    _contract(dx)
    record = _run(dx, hints=[{'anchor': 'dxf_size.entry', 'kind': 'assert',
        'text': 'assert n >= 0;', 'provenance': {'source': 'agent'}}])
    assert record['failure_class'] == 'unknown', record
    assert record['hint_check']['verdict'] == 'accepted'
    assert record['settings']['helper_windows']['certificate']['context_count'] == 1


@needs_wp
@pytest.mark.parametrize('kind,text,accepted', [
    ('assert', 'assert n == 1;', True),
    ('ghost', 'ghost int saved_count = n;', True),
    ('ghost', 'ghost q[0] = 7;', False),
])
def test_nested_entry_hints_keep_the_normal_noninterference_check(tmp_path, kind, text, accepted):
    fixture = seed(tmp_path)
    path = tmp_path / 'entry-hints.yaml'
    path.write_text(yaml.safe_dump({'hints': [{'anchor': 'nested_local.entry', 'kind': kind,
        'text': text, 'provenance': {'source': 'agent'}}]}, sort_keys=False))
    result = run_swdb('prove', '--records', fixture.records, '--summary', CONTRACT, '--adapter', 'wp',
        '--runs-dir', fixture.runs, '--format', 'json', '--hint-file', path, timeout=600,
        env=fake('unknown'))
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((fixture.records / json.loads(result.stdout)['path']).read_text())
    assert record['hint_check']['verdict'] == ('accepted' if accepted else 'rejected'), record
    assert record['hint_check']['reached_wp'] is accepted
    assert record['settings']['source_view_hints']['anchor'] == 'nested_local.entry'
    if not accepted:
        assert any(row['rule'] == 'interfering_ghost_code' for row in record['hint_check']['rejections'])


@needs_wp
@pytest.mark.parametrize('case', ['safe', 'short_frame', 'early_cpu_read'])
def test_actual_store_source_keeps_entry_witness_and_original_safety_obligations(dx, case):
    from test_proof_semantics import prove_wp
    path = dx.root / 'library/rewrite_contracts/fixture_dx_store_source_wait.yaml'
    entry = yaml.safe_load(path.read_text())
    entry['proof_unit']['array_domains'] = {name: {'extent': 'n'} for name in ('q', 'p')}
    path.write_text(yaml.safe_dump(entry, sort_keys=False))
    bound = 'n - 1' if case == 'short_frame' else 'n'
    hints = [{'anchor': 'dxf_store_source_wait.entry', 'kind': 'ghost',
              'text': f'ghost dx_store_bound = {bound};', 'provenance': {'source': 'agent'}}]
    record = prove_wp(dx, 'store_source_wait',
                      *(['SWDB_CPU_READ_AFTER_STORE'] if case == 'early_cpu_read' else []), hints=hints)
    assert record['hint_check']['verdict'] == 'accepted', record
    assert record['settings']['source_view_hints']['anchor'] == 'dxf_store_source_wait.entry'
    if case == 'safe':
        assert record['verdict'] == 'proven', (record['failure_class'], record.get('unproven_properties'))
    else:
        assert record['verdict'] == 'not_proven', record
        assert any(row['status'] != 'valid' for row in record['goals']), record

