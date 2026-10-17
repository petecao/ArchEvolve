#!/usr/bin/env python3
"""Validate prospective T17 planning consistency only. 2026-09-27 ET."""
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path
import jsonschema

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def validate(value):
    jsonschema.Draft202012Validator(json.loads((HERE/'manifest.schema.json').read_text())).validate(value)
    assert {(r['family'],r['role']) for r in value['series']}=={(f,r) for f in ('uniform_random','kronecker') for r in ('baseline','candidate')}
    assert len({r['id'] for r in value['series']})==4
    assert all(r['accelerated']==(r['role']=='candidate') for r in value['series'])
    old=value['historical_diagnostic']
    assert datetime.fromisoformat(old['original_deadline'])-datetime.fromisoformat(old['original_started'])==timedelta(seconds=600)
    planned=value['remaining_diagnostic_prerequisite'];request_path=HERE/planned['request_file']
    assert request_path.resolve()==HERE/'diagnostic-request-prospective.json'
    assert hashlib.sha256(request_path.read_bytes()).hexdigest()==planned['request_sha256']
    request=json.loads(request_path.read_text())
    primary=json.loads((ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/requests/t17-build-only-20260926-a1.json').read_text())
    assert request=={**primary,'id':'bfs-t17-diagnostic-build-only-20260927-a2','diagnostic_regions':True}
    assert all(r['diagnostic_build']['id']==request['id'] for r in value['series'] if r['role']=='candidate')
    count=len(value['series'])*value['scientific_scope']['sources_per_family']*value['scientific_scope']['repetitions']
    assert count==value['expected_outputs']['primary_executions']==value['expected_outputs']['diagnostic_executions']==24
    return {'state':'valid_prospective_template','dispatch_allowed':False,'empirical_acceptance':False,
            'expected_primary_executions':count,'expected_diagnostic_executions':count,
            'unresolved':value['remaining_bindings']}


if __name__=='__main__':
    print(json.dumps(validate(json.loads((HERE/'manifest-template.json').read_text())),indent=2))
