"""2026-10-16 ET. Explicit 35-case real public profile; no default collection.

Invoke this exact file only after independent fixture/runtime/guard admission.
Missing inputs or tools fail. There are no skips, AST controls, protocol tools,
manufactured records, or implied original-C++ equivalence for finite summaries.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from swdb import proof_semantics,yamlio
from swdb.library import Library
from swdb._dx100_finite import context_rule_scope_v1 as scope,finite_checks_v1 as finite_checks
from swdb import cbmc_translator as translator
from testkit.dx100_whole_interface_checked import CASES,CASE_IDS,actual_selection,physical,strict,verify_reports,successful_native_outputs

def expected_argv(row,case,profile,plan):
    common=[plan['python'],'-B','-P','-m','swdb','prove','--records',profile['records']]
    assert row['candidate'] is None
    common+=['--summary',case['contract_id']]
    if case['kind']=='TraceUnit':
        method='method.dx100-finite-whole-trace-v1';defines=[]
    else:
        method='method.dx100-whole-checked-source-v1';defines=['--define','NUM_CORES=4','--define','TILE_SIZE=16384']
    return common+['--method-version',method,*defines,'--adapter','cbmc','--bounds','{"threads":1}','--runs-dir',profile['runs'],'--format','json']

@pytest.mark.parametrize('case_id',CASE_IDS)
def test_actual_checked_whole_public_case(case_id,real_host):
    pin,selection,profile,plan=actual_selection()
    assert profile['schema']=='checked-whole-actual-profile-1' and len(profile['cases'])==35
    assert {row['case_id'] for row in profile['cases']}==set(CASE_IDS)
    assert plan['required_count']==35 and plan['required_skips']==0 and plan['sequential_workers']==1
    assert {job['case_id'] for job in plan['jobs']}==set(CASE_IDS) and len(plan['jobs'])==35
    assert Path(profile['records']).parent/'library'==Path(profile['library'])
    case=next(row for row in CASES if row['case_id']==case_id)
    row=next(row for row in profile['cases'] if row['case_id']==case_id)
    job=next(row for row in plan['jobs'] if row['case_id']==case_id)
    assert all(row[key]==value for key,value in case.items())
    assert job['argv']==expected_argv(row,case,profile,plan) and job['cwd']==plan['producer_project']
    assert 1<=plan['per_case_timeout_seconds']<=1800
    # Root binds this normal CLI command to its actual role/resource/lane guard.
    # An admission receipt is retained provenance, never a replacement for it.
    done=subprocess.run(job['argv'],cwd=job['cwd'],env={**os.environ,**plan['environment']},capture_output=True,text=True,timeout=plan['per_case_timeout_seconds'])
    assert done.returncode==0,done.stdout[-2000:]+done.stderr[-2000:]
    output=strict(done.stdout);assert type(output) is dict and set(output)=={'record','path'}
    record=output['record'];target=Path(output['path'])
    if not target.is_absolute():target=Path(profile['records'])/target
    assert target.resolve(strict=True)==target and target.is_relative_to(Path(profile['records']))
    assert yamlio.load(target)==record
    assert record['kind']=='proof' and record['evidence_kind']=='execution' and not record.get('skip_reason')
    assert record['verdict']==case['expected_verdict'] and record['bounds']=={'threads':1}
    assert record['proof_setup_check']['verdict']=='passed' and record['proof_setup_check']['runs']
    assert record['settings']['verifier_launched'] is True
    assert record['pins']['contract']==row['contract']
    library=Library(Path(profile['library']));assert not library.validate()
    entry=library.get(profile['entry']['id']);entry_sha=hashlib.sha256(library.files[entry['id']].read_bytes()).hexdigest()
    assert entry_sha==profile['entry']['sha256'] and record['pins']['proof_semantics']==profile['entry']
    normal=proof_semantics.record_assumptions(library,entry['id'],entry_sha)
    method=scope.source if case['kind']=='SourceUnit' else scope.finite
    applicable,receipt=method(entry,normal,entry['id'],entry_sha)
    assert [item for item in record['assumptions'] if item['kind']=='proof_semantics']==applicable
    cert=record['settings']['whole_source' if case['kind']=='SourceUnit' else 'finite_trace']
    assert cert==strict(physical(row['prepared_unit']))
    assert cert['rule_scope']==receipt
    goals=record['goals'];assert goals and len({g['goal'] for g in goals})==len(goals)
    assert all(g['status'] in ('success','failure') for g in goals)
    assert not any('.unwind.' in g['goal'] and g['status']=='failure' for g in goals)
    reports=verify_reports(record)
    flags=record['settings']['flags'];assert '--unwinding-assertions' in flags and '--no-assertions' not in flags
    if case['kind']=='TraceUnit':
        assert record['subject']=={'kind':'library_summary','id':case['contract_id']}
        finite_checks.public_record(record,dict(case_id=case_id.removeprefix('finite-'),contract=row['contract'],conditional_predicted_verdict=case['expected_verdict']),
            dict(entry=profile['entry'],record_assumptions=applicable))
        assert cert['native_scope'].startswith('exact generated abstract model')
    else:
        assert record['subject']=={'kind':'library_summary','id':case['contract_id']}
        assert record['settings']['agreement']['verdict']=='agree'
        assert record['settings']['agreement'].get('undefined_behavior_runs',0)==0
        assert {'differential_c','differential_cxx','differential_c_output','differential_cxx_output','cbmc_input','cbmc_output'}<=set(reports)
        if record['verdict']=='proven':
            successful_native_outputs(reports)
            reaches=[g for g in goals if g['property']==translator.REACH_END or g['property'].startswith(translator.REACH_SUMMARY)]
            assert reaches and all(g['status']=='failure' for g in reaches)
            assert all(g['status']=='success' for g in goals if g not in reaches)
        else:
            replay=record['counterexample']['replay'];assert replay['form']=='cxx' and replay['replayed'] is True and replay['end']=='check'
            assert record['counterexample']['property'] in replay['failed']
    # Settled control identity is mandatory; no output Boolean grants authority.
    assert strict(physical(selection['profile']))==profile and strict(physical(selection['command_plan']))==plan
    assert strict(physical(pin))==selection
    for name in ('root_admission','runtime'):physical(selection[name])
