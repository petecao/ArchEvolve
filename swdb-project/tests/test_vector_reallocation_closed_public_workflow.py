"""2026-10-16 ET. Coordinator-admitted real public source-rule records.

Fresh Clang/source/runtime checks are real. No new WP solver invocation is
requested: the source rule binds accepted unchanged historical mathematics.
"""
import json
import os

import pytest
import yaml

from conftest import run_swdb
from testkit.vector_closed_workflow import CONTRACT_ID, build_closed_source_fixture


@pytest.mark.skipif(os.environ.get('SWDB_VECTOR_CLOSED_SOURCE_ACTUAL') != '1',
                    reason='requires coordinator source/compiler/runtime admission')
@pytest.mark.parametrize('control', ['safe', 'missing_bundle', 'stale_method', 'wrong_result', 'default_method'])
def test_public_closed_source_proof_and_exact_opt_in_controls(tmp_path, control):
    records, method = build_closed_source_fixture(tmp_path, control=control)
    done = run_swdb('prove', '--records', records, '--summary', CONTRACT_ID, '--adapter', 'wp',
        '--method-version', method, '--runs-dir', tmp_path/'runs', '--budget-minutes', '5', '--format', 'json',
        env={'SWDB_VERIFIER_RSS_CAP_BYTES': '8589934592'}, timeout=420)
    assert done.returncode == 0, done.stdout+done.stderr
    record_path = records/json.loads(done.stdout)['path']
    original_record = record_path.read_bytes()
    record = yaml.safe_load(original_record)
    (tmp_path/'retained-public-record.json').write_text(json.dumps(record, indent=2)+'\n')
    assert record['evidence_kind'] == 'contract_fixture'
    assert record['proof_setup_check']['verdict'] == 'passed'
    assert record['settings']['verifier_launched'] is False
    assert not any(row['name'] == 'wp_log' for row in record['evidence']['reports'])
    if control != 'safe':
        assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct', record
        return
    assert record['verdict'] == 'proven' and not record.get('unproven_properties'), record
    assert len(record['goals']) == 24
    assert all(goal['source'] == 'source_rule' and goal['status'] == 'valid' for goal in record['goals'])
    assert record['settings']['tool'] == 'checked-vector-source-rule'
    assert record['settings']['framework_source_rule_evaluated'] is True
    assert record['settings']['source_typed_bridge_established'] is False
    assert record['settings']['current_model_records_created'] == []
    assert record['settings']['original_diagnostic']['normal_verdict'] == 'not_proven'
    assert record['settings']['native_projected_diagnostic']['normal_verdict'] == 'not_proven'
    assert sum(row['targets'] for row in record['settings']['historical_scientific_components']) == 82
    assert any(row['invocation'] == 'checked-source-rule-evaluation' and row['native_verifier_launched'] is False
               for row in record['proof_setup_check']['runs'])
    assert record['verdict_reading']['verdict'] == 'proven'
    assert all(name in record['pins'] for name in ('vector_closed_source_rule', 'vector_closed_scientific_binding',
                                                  'vector_closed_scientific_bundle', 'vector_closed_source_route'))
    assert 'models' not in record['pins']
    from swdb import std_models
    standard = [row for row in record['assumptions'] if row['reference'] == record['pins']['std_models']]
    assert any(row['sentence'] == std_models.SENTENCE_ALLOCATION for row in standard)
    assert any(row['sentence'].startswith('The pinned standard library ') for row in standard)
    valid = run_swdb('validate', '--records', records, timeout=120)
    assert valid.returncode == 0, valid.stdout+valid.stderr
    try:
        for mutation in ('missing_source_pin', 'native_result_promoted', 'execution_scope'):
            changed = yaml.safe_load(original_record)
            if mutation == 'missing_source_pin':
                changed['pins'].pop('vector_closed_scientific_binding')
            elif mutation == 'native_result_promoted':
                changed['settings']['native_projected_diagnostic']['normal_verdict'] = 'proven'
            else:
                changed['evidence_kind'] = 'execution'
            record_path.write_text(yaml.safe_dump(changed, sort_keys=False))
            invalid = run_swdb('validate', '--records', records, timeout=120)
            assert invalid.returncode != 0, invalid.stdout+invalid.stderr
    finally:
        record_path.write_bytes(original_record)
