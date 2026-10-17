"""2026-10-16 ET. Closed initialized-u32 native-result health, no proof from pytest."""
import hashlib
import json
from pathlib import Path


def assert_initialized_native_outcome(record, expected):
    """Read every native goal before admitting this fixture's 711/1107 observation.

    A healthy wrong postcondition remains nonproof. This predicate does not check
    source correspondence, complete property/DAG/Extern closure, solver-task
    provenance or process settlement; the independent cold reader does those.
    """
    assert type(expected) is int and expected in (711, 1107)
    goals = record.get('goals')
    assert isinstance(goals, list) and goals and all(isinstance(g, dict) for g in goals)
    recorded = {g.get('goal'): g for g in goals}
    assert len(recorded) == len(goals) and all(isinstance(name, str) and name for name in recorded)
    assert all(type(g.get('smoke')) is bool for g in goals)
    ordinary = [g for g in goals if not g['smoke']]
    smoke = [g for g in goals if g['smoke']]
    assert ordinary and smoke
    assert all(g.get('status') == 'valid' for g in smoke)
    reports = [p for p in record.get('evidence', {}).get('reports', []) if p.get('name') == 'wp_inventory']
    assert len(reports) == 1, 'complete native inventory required for both fixture halves'
    data = Path(reports[0]['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == reports[0]['sha256']
    inventory = json.loads(data)
    assert inventory.get('version') == '1' and inventory.get('complete') is True
    rows = inventory.get('goals')
    assert isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows)
    native = {r.get('goal'): r for r in rows}
    assert len(native) == len(rows) and native.keys() == recorded.keys(), 'missing, duplicate or unread native goal'
    for name, row in native.items():
        assert type(row.get('passed')) is bool and type(row.get('smoke')) is bool
        assert row['smoke'] == recorded[name]['smoke']
        assert row['passed'] == (recorded[name].get('status') == 'valid')
        results = row.get('results')
        assert isinstance(results, list) and all(isinstance(r, str) for r in results)
        if row['smoke']:
            # A proved false smoke exposes inconsistent premises. Every native
            # result must remain healthy and nonvalid; no unattempted smoke.
            assert row['passed'] and results and all(r in {'unknown', 'timeout', 'stepout', 'invalid'} for r in results)
        else:
            assert all(r in {'valid', 'unknown', 'timeout', 'stepout', 'untried'} for r in results)
            if row['passed']:
                assert 'valid' in results, 'ordinary pass needs a direct Valid prover result'
            else:
                assert any(r in {'unknown', 'timeout', 'stepout'} for r in results), 'unattempted ordinary goal'
    failed = [g for g in ordinary if g.get('status') != 'valid']
    assert record.get('failure_class') != 'vacuous_pass'
    if expected == 711:
        assert record['verdict'] == 'proven' and not failed
        assert record.get('failure_class') is None
    else:
        assert record['verdict'] == 'not_proven' and record.get('failure_class') in {'unknown', 'timeout'}
        assert len(failed) == 1 and 'ensures' in failed[0]['goal'], 'only the deliberately wrong result may remain unproved'
    return {'ordinary': len(ordinary), 'smoke': len(smoke), 'failed_ordinary': len(failed)}
