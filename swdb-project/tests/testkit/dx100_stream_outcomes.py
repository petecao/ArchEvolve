"""2026-10-16 ET. Strict actual stream goal-health predicate; no theorem from pytest.

Derived from the reviewed size-negative health boundary: all native prover
results must be read, and solver/resource failures never qualify as negatives.
"""
import hashlib,json
from pathlib import Path

def assert_stream_outcome(record,expected):
    assert type(expected) is int and expected in (0,1)
    ordinary=[g for g in record['goals'] if not g.get('smoke')]
    smoke=[g for g in record['goals'] if g.get('smoke')]
    assert ordinary and smoke
    assert all(g.get('status')=='valid' for g in smoke),smoke
    assert record.get('failure_class')!='vacuous_pass'
    if expected==1:
        assert record['verdict']=='proven'
        assert all(g.get('status')=='valid' for g in ordinary),ordinary
    else:
        # A healthy ordinary nonproof is distinct from a tool/resource failure.
        # The record's best status alone can hide another prover's Failed result.
        assert record['verdict']=='not_proven' and record.get('failure_class') in ('unknown','timeout')
        failed=[g for g in ordinary if g.get('status')!='valid']
        assert failed and all('ensures' in str(g.get('goal','')) for g in failed),failed
        reports=[p for p in record.get('evidence',{}).get('reports',[]) if p.get('name')=='wp_inventory']
        assert len(reports)==1,'negative acceptance needs the complete pinned native inventory'
        data=Path(reports[0]['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==reports[0]['sha256']
        inventory=json.loads(data)
        assert inventory.get('version')=='1' and inventory.get('complete') is True
        rows=inventory.get('goals')
        assert isinstance(rows,list) and rows and all(isinstance(r,dict) for r in rows)
        generated={r.get('goal'):r for r in rows}
        recorded={g.get('goal'):g for g in record['goals']}
        assert None not in generated and len(generated)==len(rows)
        assert None not in recorded and len(recorded)==len(record['goals'])
        assert set(generated)==set(recorded),'unread or missing native goals'
        healthy={'valid','unknown','timeout','stepout','untried'}
        for name,row in generated.items():
            results=row.get('results')
            assert isinstance(results,list) and all(isinstance(r,str) and r in healthy for r in results),row
            assert type(row.get('passed')) is bool and type(row.get('smoke')) is bool
            assert row['smoke']==bool(recorded[name].get('smoke'))
            assert row['passed']==(recorded[name].get('status')=='valid')
            if not row['passed']:
                assert any(r in ('unknown','timeout','stepout') for r in results),'unattempted ordinary goal'
