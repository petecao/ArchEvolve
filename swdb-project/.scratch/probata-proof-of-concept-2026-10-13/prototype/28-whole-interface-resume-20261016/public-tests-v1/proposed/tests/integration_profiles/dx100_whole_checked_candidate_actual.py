"""2026-10-16 ET. One separately admitted positive source-candidate proof.

This file is explicitly selected after a genuine per-candidate source profile,
certification, method/runtime and physical SourceUnit are prepared. It has no
skip path or fabricated candidate/certification/proof. Do not run it yet.
"""
import hashlib
import os
from pathlib import Path
import subprocess

from conftest import run_swdb
from swdb import cbmc_translator as translator,handoff_level,proof_semantics,yamlio
from swdb.library import Library
from swdb.store import Store
from swdb.wp_adapter import _unit_source
from swdb._dx100_finite import context_rule_scope_v1 as scope
from testkit.dx100_whole_interface_checked import physical,strict,verify_reports,successful_native_outputs

def test_actual_positive_source_candidate_level_and_handoff(real_host):
    assert os.environ.get('SWDB_DX100_WHOLE_CHECKED_CANDIDATE_ACTUAL')=='1'
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    pin=strict(os.environ['SWDB_DX100_WHOLE_CHECKED_CANDIDATE_SELECTION']);selection=strict(physical(pin))
    assert set(selection)=={'schema','profile','command_plan','root_admission','runtime'} and selection['schema']=='checked-whole-candidate-selection-1'
    for name in ('root_admission','runtime'):physical(selection[name])
    profile=strict(physical(selection['profile']));plan=strict(physical(selection['command_plan']))
    assert profile['schema']=='checked-whole-positive-candidate-profile-1'
    assert plan['required_count']==1 and plan['required_skips']==0 and plan['sequential_workers']==1
    assert Path(profile['records']).parent/'library'==Path(profile['library'])
    library=Library(Path(profile['library']));assert not library.validate()
    contract=library.get(profile['contract']['id']);assert library.content_sha256(contract['id'])==profile['contract']['sha256']
    assert contract['proof_unit']['function']=='whole_interface_source_fixture'
    assert contract['proof_unit']['source']['sha256']=='3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
    assert all(row['proof_placement']=='per_candidate' for row in contract['clauses'])
    store=Store(Path(profile['records']));candidate=store.get(profile['candidate'],'candidate');assert candidate is not None
    actual_source=_unit_source(Path(candidate['artifact']['path']),'whole_interface_source_fixture')
    assert actual_source.resolve(strict=True)==library.resolve(contract['proof_unit']['source'])
    expected=[plan['python'],'-B','-P','-m','swdb','prove','--records',profile['records'],'--candidate',profile['candidate'],
        '--function','whole_interface_source_fixture','--contract',contract['id'],'--method-version','method.dx100-whole-checked-source-v1',
        '--define','NUM_CORES=4','--define','TILE_SIZE=16384','--adapter','cbmc','--bounds','{"threads":1}','--runs-dir',profile['runs'],'--format','json']
    assert plan['argv']==expected and plan['cwd']==plan['producer_project'] and 1<=plan['timeout_seconds']<=1800
    done=subprocess.run(expected,cwd=plan['cwd'],env={**os.environ,**plan['environment']},capture_output=True,text=True,timeout=plan['timeout_seconds'])
    assert done.returncode==0,done.stdout[-2000:]+done.stderr[-2000:]
    output=strict(done.stdout);assert set(output)=={'record','path'};record=output['record']
    target=Path(output['path']);target=target if target.is_absolute() else Path(profile['records'])/target
    assert target.resolve(strict=True)==target and target.is_relative_to(Path(profile['records'])) and yamlio.load(target)==record
    assert record['subject']=={'kind':'candidate_proof_unit','candidate':profile['candidate'],'function':'whole_interface_source_fixture'}
    assert record['verdict']=='proven' and record['evidence_kind']=='execution' and not record.get('skip_reason')
    assert record['bounds']=={'threads':1} and record['proof_setup_check']['verdict']=='passed' and record['proof_setup_check']['runs']
    assert record['settings']['verifier_launched'] is True and record['settings']['agreement']['verdict']=='agree'
    assert record['settings']['agreement'].get('undefined_behavior_runs',0)==0
    reports=verify_reports(record)
    assert {'differential_c','differential_cxx','differential_c_output','differential_cxx_output','cbmc_input','cbmc_output'}<=set(reports)
    successful_native_outputs(reports)
    goals=record['goals'];assert goals and len({g['goal'] for g in goals})==len(goals)
    assert all(g['status'] in ('success','failure') for g in goals)
    reach=[g for g in goals if g['property']==translator.REACH_END or g['property'].startswith(translator.REACH_SUMMARY)]
    assert reach and all(g['status']=='failure' for g in reach) and all(g['status']=='success' for g in goals if g not in reach)
    assert '--unwinding-assertions' in record['settings']['flags'] and '--no-assertions' not in record['settings']['flags']
    assert record['pins']['code']=={'id':profile['candidate'],'sha256':candidate['artifact']['sha256']}
    assert record['pins']['contract']==profile['contract']
    cert=record['settings']['whole_source'];assert cert==strict(physical(profile['prepared_unit']))
    entry=library.get(profile['entry']['id']);digest=hashlib.sha256(library.files[entry['id']].read_bytes()).hexdigest()
    assert record['pins']['proof_semantics']==profile['entry']=={'id':entry['id'],'sha256':digest}
    applicable,receipt=scope.source(entry,proof_semantics.record_assumptions(library,entry['id'],digest),entry['id'],digest)
    assert cert['rule_scope']==receipt and [x for x in record['assumptions'] if x['kind']=='proof_semantics']==applicable
    result=run_swdb('candidate-level',profile['candidate'],'--records',profile['records'],'--format','json',env=plan['environment'])
    assert result.returncode==0,result.stderr
    level=strict(result.stdout);assert level['level']=='proven_within_bounds_threads_1' and record['id'] in level['proven']['records']
    block=handoff_level.render(Store(Path(profile['records'])),profile['candidate'])
    assert block['level']==level['level'] and record['id'] in block['proof_records'] and block['text'].endswith('Says nothing about speed.')
    refs={x['reference']['id'] for x in block['assumptions'] if x['kind']=='proof_semantics'}
    assert {x['reference']['id'] for x in applicable}<=refs
    assert not refs&{entry['id']+'#'+name for name in scope.FINITE_IDS}
    assert strict(physical(selection['profile']))==profile and strict(physical(selection['command_plan']))==plan and strict(physical(pin))==selection
    for name in ('root_admission','runtime'):physical(selection[name])
