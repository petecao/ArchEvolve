"""Ticket24 fixture-only no-op policy; never a production proof rule.

Only unchanged precondition-free maa_const has no generated smoke. Its three
real obligations remain mandatory; acceptance awaits an actual original caller.
"""
import hashlib
import json
from pathlib import Path
import re
from swdb import artifacts

CONST_ID = 'contract.fixture_wp24_summary_maa_const'
CONST_DIGEST = '4c3e3b76b033cee9def533ee7e5994441e56ac005c41e6c348e52ca2c2b7d4a0'
SOURCE_DIGEST = '7954719a7ab3bd93f8da1eea7a028de9d1dfa524761f2ff5f56c92dd70712e25'
EXCEPTION_ERRORS = {'actual ordinary/smoke goal inventory is empty', 'safe proof lacks all-goal/smoke Valid acceptance'}


def audit_noop(record, contract, source, strict_audit):
    checked = strict_audit(record, 'proven')
    errors = [e for e in checked['errors'] if e not in EXCEPTION_ERRORS]
    function = 'maa_const_i32'
    properties = {function+'_'+kind for kind in ('terminates','exits','assigns')}
    pin = dict(id=CONST_ID, sha256=CONST_DIGEST)
    try:
        assert record['subject'] == dict(kind='library_summary',id=CONST_ID)
        assert artifacts.digest(contract) == CONST_DIGEST
        assert hashlib.sha256(source.encode()).hexdigest() == SOURCE_DIGEST
        assert record['pins']['code'] == record['pins']['contract'] == pin
        assert [f for f in record['settings']['flags'] if f.startswith('-wp-fct=')] == ['-wp-fct='+function]
        goals = record['goals']
        assert len(goals) == 3 and {g['property'] for g in goals} == properties
        assert all(g['function']==function and not g.get('smoke') and g['status']=='valid' for g in goals)
        reports = {r['name']:Path(r['path']) for r in record['evidence']['reports']}
        inventory = json.loads(reports['wp_inventory'].read_text())
        assert inventory['complete'] is True and len(inventory['goals']) == 3
        assert {g['property'] for g in inventory['goals']} == properties
        assert all(g['function']==function and not g['smoke'] and g['passed'] is True for g in inventory['goals'])
        descriptions = {p['property']:p['description'] for p in inventory['properties']}
        assert descriptions[function+'_assigns'] == 'assigns \\nothing;'
        assert descriptions[function+'_exits'] == 'exits\n\\false'
        assert descriptions[function+'_terminates'] == 'terminates\n\\true'
        assert set(descriptions) <= properties | {function}
        bodies = re.findall(r'void maa_const_i32\(int value, int reg\)\s*\{([^{}]*)\}', reports['wp_normalized'].read_text())
        assert bodies and all(re.sub(r'\s+', '', body)=='return;' for body in bodies)
    except (AssertionError, KeyError, ValueError, OSError):
        errors.append('outside exact precondition-free original maa_const no-op policy')
    checked.update(errors=errors,generated_smoke='not_applicable_exact_noop' if not errors else 'exception_refused',
                   acceptance='pending_unchanged_caller_witness' if not errors else 'rejected',
                   historical_strict_errors=strict_audit(record,'proven')['errors'])
    return checked


def caller_witness(record, summary_records, strict_audit, *, expected_candidate, expected_code):
    """Actual smoke must show original caller preconditions and each call reachable."""
    checked = strict_audit(record, 'proven')
    errors = list(checked['errors'])
    try:
        assert record['pins']['contract'] == dict(id='contract.fixture_wp24_maa_summary',
            sha256='59bc854bb0ad4c12b13eaf84dbb3c99dfc3a9aa7f923ce59fdbdf754812c6c22')
        assert record['subject'] == dict(kind='candidate_proof_unit',candidate=expected_candidate,function='swdb_maa_unit')
        assert record['pins']['code'] == expected_code
        pins = {p['id']:p for p in record['pins']['summaries']}
        assert set(pins) == set(summary_records)
        for cid,summary in summary_records.items():
            assert pins[cid]['proof_record'] == summary['id']
            assert pins[cid]['sha256'] == summary['pins']['code']['sha256']
        smoke = [g for g in record['goals'] if g.get('smoke')]
        assert all(g['status']=='valid' for g in smoke)
        for callee in ('maa_const_i32','maa_indirect_load_i32'):
            assert len([g for g in smoke if re.fullmatch('typed_real_'+callee+r'_wp_smoke_dead_call_s\d+',g['goal'])])==1
        assert any(g['goal']=='typed_real_swdb_maa_unit_wp_smoke_default_requires' for g in smoke)
        report, = [r for r in record['evidence']['reports'] if r['name']=='wp_inventory']
        inventory = json.loads(Path(report['path']).read_text())
        assert inventory['complete'] is True
        by_goal = {g['goal']:g for g in inventory['goals']}
        assert all(by_goal[g['goal']]['passed'] is True and by_goal[g['goal']]['smoke'] is True for g in smoke)
    except (AssertionError, KeyError, ValueError, OSError):
        errors.append('missing unchanged MAA caller per-call reachability/nonvacuity witness')
    return dict(errors=errors,acceptance='accepted' if not errors else 'rejected',witness_record=record['id'],
                generated_smoke='actual_unchanged_caller_per_call')
