"""Nested reads in automatic initializers preserve their scope; 2026-10-15 ET."""
import json
import os
import subprocess
import sys

import pytest
import yaml

from conftest import REPO, run_swdb
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp
from test_wp_subset import _entry


SOURCE = 'int nested_local(int *q,int *base,int n) { int value=base[q[0]]; return value; }\n'
CONTRACT = 'contract.fixture_nested_local'


def seed(root, source=SOURCE):
    fixture = _ownership_seed(root, source=source, cases=[])
    entry = _entry(CONTRACT, 'nested_local', 'vector_ownership.cc', source,
        [('pre', 'legality', r'requires n == 1 && \valid(q) && \valid(base); '
          r'requires \initialized(q) && \initialized(base); requires q[0] == 0 && base[0] == 7;'),
         ('post', 'postcondition', r'assigns \nothing; ensures \result == 7;')],
        ['q', 'base'], {'once': 'self'})
    entry['proof_unit']['array_domains'] = {name: {'extent': 'n'} for name in ('q', 'base')}
    (root / 'library/rewrite_contracts/fixture_nested_local.yaml').write_text(yaml.safe_dump(entry, sort_keys=False))
    return fixture


def prove(fixture, *, standin=True):
    result = run_swdb('prove', '--records', fixture.records, '--summary', CONTRACT,
        '--adapter', 'wp', '--runs-dir', fixture.runs, '--format', 'json', timeout=600,
        env=fake('unknown', SWDB_VERIFIER_LOCK=str(fixture.root / 'standin.lock')) if standin else None)
    assert result.returncode == 0, result.stderr + result.stdout
    return yaml.safe_load((fixture.records / json.loads(result.stdout)['path']).read_text())


@needs_wp
def test_a_nested_initializer_keeps_its_declared_value_visible_after_the_read(tmp_path):
    fixture = seed(tmp_path)
    record = prove(fixture)
    assert record['failure_class'] == 'unknown', record
    certificate = record['settings']['nested_entry_reads']['certificate']
    assert len(certificate['captures']) == 1
    assert record['settings']['nested_entry_reads']['input_premises_added'] == []
    report = next(row for row in record['evidence']['reports'] if row['name'] == 'wp_input')
    text = (fixture.records / report['path']).read_text()
    assert 'return value;' in text


@needs_wp
@pytest.mark.parametrize('fault', ['static', 'tls', 'type', 'root', 'later_use'])
def test_a_rehashed_initializer_renderer_cannot_change_scope_storage_or_bindings(tmp_path, fault):
    fixture = seed(tmp_path)
    before, after = {
        'static': ('int value=', 'static int value='),
        'tls': ('int value=', 'thread_local int value='),
        'type': ('int value=', 'const int value='),
        'root': ('value=base[', 'value=q['),
        'later_use': ('return value;', 'return swdb_nested_read_1;'),
    }[fault]
    script = '''from swdb import proof, wp_adapter, nested_entry_reads
from swdb.cli import main
original = nested_entry_reads._render
def faulty(raw, edits):
    text = original(raw, edits)
    if edits:
        assert text.count(BEFORE) == 1
        return text.replace(BEFORE, AFTER, 1)
    return text
nested_entry_reads._render = faulty
raise SystemExit(main())
'''.replace('BEFORE', repr(before)).replace('AFTER', repr(after))
    result = subprocess.run([sys.executable, '-c', script, 'prove', '--records', str(fixture.records),
        '--summary', CONTRACT, '--adapter', 'wp', '--runs-dir', str(fixture.runs), '--format', 'json'],
        cwd=REPO, text=True, capture_output=True, timeout=600,
        env={**os.environ, **fake('unknown', SWDB_VERIFIER_LOCK=str(tmp_path / 'standin.lock'))})
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((fixture.records / json.loads(result.stdout)['path']).read_text())
    assert record['failure_class'] == 'unsupported_construct', record
    assert record['settings']['verifier_launched'] is False
    assert not any(row['name'] == 'wp_log' for row in record['evidence']['reports'])


@needs_wp
@pytest.mark.parametrize('case', ['safe', 'inner_window', 'outer_window', 'uninitialized_inner'])
def test_actual_initializer_scope_and_independent_read_obligations(tmp_path, case):
    fixture = seed(tmp_path)
    path = tmp_path / 'library/rewrite_contracts/fixture_nested_local.yaml'
    entry = yaml.safe_load(path.read_text())
    if case in {'inner_window', 'outer_window'}:
        entry['proof_unit']['array_domains']['q' if case == 'inner_window' else 'base']['extent'] = '0'
    if case == 'uninitialized_inner':
        for clause in entry['clauses']:
            clause['acsl']['text'] = clause['acsl']['text'].replace(r'\initialized(q) && ', '')
    path.write_text(yaml.safe_dump(entry, sort_keys=False))
    record = prove(fixture, standin=False)
    assert_initializer_obligations(record, case)


def assert_initializer_obligations(record, case):
    """Check public property meaning without depending on a prover's goal spelling."""
    assert len(record['settings']['nested_entry_reads']['certificate']['captures']) == 1
    if case == 'safe':
        assert record['verdict'] == 'proven', record.get('unproven_properties')
    else:
        assert record['verdict'] == 'not_proven', record
        open_goals = {row['goal'] for row in record['goals'] if row['status'] != 'valid'}
        if case == 'uninitialized_inner':
            assert any(row.get('kind') == 'initialization' and row.get('goal') in open_goals
                       for row in record['unproven_properties']), record
        else:
            assert any('swdb_window_access' in goal for goal in open_goals), record

