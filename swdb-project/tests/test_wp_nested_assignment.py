"""Nested local assignment through the public WP path; 2026-10-15 ET."""
import pytest
import yaml

from test_wp_adapter import needs_wp
from test_wp_nested_local import assert_initializer_obligations, prove, seed


SOURCE = 'int nested_local(int *q,int *base,int n) { int value=0; value=base[q[0]]; return value; }\n'


@needs_wp
def test_nested_assignment_reaches_the_ordinary_pointer_and_initializedness_checks(tmp_path):
    fixture = seed(tmp_path, source=SOURCE)
    record = prove(fixture)
    assert record['failure_class'] == 'unknown', record
    assert len(record['settings']['nested_entry_reads']['certificate']['captures']) == 1
    assert record['settings']['nested_entry_reads']['input_premises_added'] == []


@needs_wp
@pytest.mark.parametrize('case', ['safe', 'uninitialized_inner'])
def test_actual_local_assignment_preserves_the_original_read_obligations(tmp_path, case):
    fixture = seed(tmp_path, source=SOURCE)
    path = tmp_path / 'library/rewrite_contracts/fixture_nested_local.yaml'
    entry = yaml.safe_load(path.read_text())
    if case == 'uninitialized_inner':
        for clause in entry['clauses']:
            clause['acsl']['text'] = clause['acsl']['text'].replace(r'\initialized(q) && ', '')
    path.write_text(yaml.safe_dump(entry, sort_keys=False))
    record = prove(fixture, standin=False)
    assert_initializer_obligations(record, case)
