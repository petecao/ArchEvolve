#!/usr/bin/env python3
"""Continue stopped original t24 matrix without replaying accepted atomic proofs.

Fixture-only no-op summary policy v1; ordinary public dependency eligibility is
unchanged. An exact no-op summary stays provisional until the unchanged actual
MAA safe caller supplies per-call reachability/nonvacuity smoke. All new raw
outputs are disjoint from the retained stopped input; no production edits.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO/'tests')]
import yaml
from swdb import artifacts, c_lowering, host_identity, proof_setup
from test_wp_subset import (MODELS, SUMMARIES, TERMINAL_CONTROLS, summary_id, contract_id,
                            GROUPS as FIXTURE_GROUPS, BUG_UNITS, UNITS, IMPLS, _entry)
from t24_noop_summary import audit_noop, caller_witness
spec = importlib.util.spec_from_file_location('original_t24', Path(__file__).with_name('t24-original-matrix.py'))
matrix = importlib.util.module_from_spec(spec);spec.loader.exec_module(matrix)
FROZEN = '0e7f232762e4555aa9435a3a3622923fad8ee928'
STOPPED_MATRIX = '946176dcb5fcf7caa4e0e2e4bed8fe5ada363eaa7d5bb2514e339de914a22c49'
GROUPS = ('maa_summary','dxc_summary','templates','classes','omp','new_array')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit',required=True)
    parser.add_argument('--from-seed',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--public-timeout-seconds',type=int,default=1800)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    if not 600<=args.public_timeout_seconds<=7200:parser.error('public timeout outside600..7200')
    source=args.from_seed.resolve();output=args.output.resolve()
    if output.is_relative_to(REPO) or output.is_relative_to(source.parent) or source.parent.is_relative_to(output):
        parser.error('output must be outside checkout and disjoint from historical matrix')
    assert matrix.git('rev-parse','HEAD')==args.expected_commit
    assert not matrix.git('status','--porcelain','--untracked-files=no','--',':(top)swdb-project')
    assert sha(source.parent/'matrix.json')==STOPPED_MATRIX, 'not the retained exact stopped matrix'
    prior=json.loads((source.parent/'matrix.json').read_text())
    manifest=json.loads((source.parent/'source-manifest.json').read_text())
    assert prior['commit']==manifest['commit']==FROZEN
    runtime={p:d for p,d in manifest['sources'].items() if p.startswith('swdb/')}
    assert set(runtime)==set(matrix.git('ls-files','swdb').splitlines())
    assert all(sha(REPO/p)==digest for p,digest in runtime.items())
    # Bind all original C++/contract/hint/candidate builders, not only production.
    original={p:d for p,d in manifest['sources'].items() if p=='tests/test_wp_subset.py' or p.startswith('tests/fixtures/proof/lowering/')}
    assert original and all(sha(REPO/p)==digest for p,digest in original.items())
    os.environ['SWDB_VERIFIER_RSS_CAP_BYTES']='8589934592'
    os.environ[host_identity.FIXTURE_HOST_ENV]='swdb-fixture-host'
    output.mkdir(parents=True,exist_ok=False);seed_path=output/'seed';seed_path.mkdir()
    for folder in ('records','library'):shutil.copytree(source/folder,seed_path/folder)
    candidates=json.loads((source.parent/'candidates.json').read_text())
    assert (seed_path/'library/proof_units/subset_units.cc').read_text()==UNITS
    assert (seed_path/'library/proof_units/summaries/summary_impls.cc').read_text()==IMPLS
    original_contracts={}
    for group,(function,clauses,arrays,_hints) in {**FIXTURE_GROUPS,**BUG_UNITS}.items():
        expected=_entry(contract_id(group),function,'subset_units.cc',UNITS,clauses,arrays,'per_candidate')
        if group=='std_models':expected['proof_unit']['array_domains']={n:{'extent':'n'} for n in ('a','b')}
        elif group in {'classes','omp','floats'}:expected['proof_unit']['array_domains']={'a':{'extent':'n'}}
        path=seed_path/'library/rewrite_contracts'/('fixture_wp24_'+group+'.yaml')
        assert yaml.safe_load(path.read_text())==expected, 'original caller contract changed: '+group
        original_contracts[contract_id(group)]=artifacts.digest(expected)
    for name,(function,clauses,arrays) in SUMMARIES.items():
        expected=_entry(summary_id(name),function,'summaries/summary_impls.cc',IMPLS,clauses,arrays,{'once':'self'})
        path=seed_path/'library/rewrite_contracts'/('fixture_wp24_summary_'+name+'.yaml')
        assert yaml.safe_load(path.read_text())==expected, 'original summary contract changed: '+name
        original_contracts[summary_id(name)]=artifacts.digest(expected)
    method_file=seed_path/'library/methods/wp-tracer-fixture.yaml'
    method=yaml.safe_load(method_file.read_text())
    assert c_lowering.identity()['c_lowering'] in method['c_lowering']['translators']
    by_label={r['label']:r for r in prior['rows']}
    result=dict(commit=args.expected_commit,runtime_freeze=FROZEN,runtime_sources=runtime,
        original_sources=original,source_seed=str(source),source_matrix_sha256=sha(source.parent/'matrix.json'),
        runtime_identity=c_lowering.identity(),candidates=candidates,policy_version=1,
        method=dict(id=method['id'],sha256=sha(method_file)),workers=1,rss_cap_bytes=8589934592,
        public_timeout_seconds=args.public_timeout_seconds,reused=[],rows=[],complete=False,success=False,
        ordinary_dependency_eligibility='unchanged public swdb prove; no trusted IDs or bypass',
        historical_rejection=by_label['summary:maa_const'].get('errors',[]))
    seed=matrix.MatrixSeed(seed_path,candidates,args.public_timeout_seconds)
    summaries={}
    def saved(record):
        path=seed.records/'proofs'/(record['id']+'.yaml')
        return dict(path=str(path),sha256=sha(path))
    def reuse(label,expected,**kwargs):
        row=by_label[label];physical=Path(row['record']['path'])
        assert sha(physical)==row['record']['sha256']
        record=yaml.safe_load(physical.read_text())
        assert (seed.records/'proofs'/physical.name).read_bytes()==physical.read_bytes()
        assert record['pins']['method_version']==dict(id=method['id'],sha256=sha(method_file))
        assert record['proof_setup_check']['check']==proof_setup.identity()['proof_setup_check']
        assert record['verdict_reading']['check']==proof_setup.identity()['verdict_reading']
        if label=='summary:maa_const':
            contract=yaml.safe_load((seed_path/'library/rewrite_contracts/fixture_wp24_summary_maa_const.yaml').read_text())
            source_text=(seed_path/'library/proof_units/summaries/summary_impls.cc').read_text()
            checked=audit_noop(record,contract,source_text,matrix.audit)
        else:checked=matrix.audit(record,expected,**kwargs)
        assert not checked['errors'],checked['errors']
        result['reused'].append(dict(label=label,record=saved(record),**checked))
        return record
    models={name:reuse('model:'+name,'proven') for name in MODELS['atomics']}
    for name,record in models.items():
        assert record['subject']==dict(kind='c_model',id=name)
        expected=dict(id=name,sha256=hashlib.sha256(c_lowering.model_text(name).encode()).hexdigest())
        assert record['pins']['code']==record['pins']['contract']==expected
    def closure(record,models,summary_records):
        for kind,deps in [('models',models),('summaries',summary_records)]:
            pins={p['id']:p for p in record['pins'].get(kind,[])}
            assert set(pins)==set(deps),(kind,pins)
            for cid,dependency in deps.items():
                assert pins[cid]['proof_record']==dependency['id'] and pins[cid]['sha256']==dependency['pins']['code']['sha256']
    safe_atomic=reuse('atomics:safe','proven')
    assert safe_atomic['subject']==dict(kind='candidate_proof_unit',candidate=candidates['safe'],function='swdb_atomics_unit')
    closure(safe_atomic,models,{})
    closure(reuse('atomics:seeded','not_proven',ordinary_open='ensures'),models,{})
    summaries[summary_id('maa_const')]=reuse('summary:maa_const','proven')
    dump(output/'profile.json',result)
    if args.check_only:
        print('PASS source/reused-proof preflight; no proof launched',flush=True);return 0
    def run(label,action,expected,*,actual=True,ordinary_open=None,dependencies=None):
        started=time.monotonic();print('START '+label,flush=True)
        record=action()
        contract_pin=record['pins']['contract']
        assert contract_pin['sha256']==original_contracts[contract_pin['id']], 'selected original contract differs'
        checked=matrix.audit(record,expected,actual=actual,ordinary_open=ordinary_open)
        if dependencies is not None:closure(record,{},dependencies)
        row=dict(label=label,record=saved(record),wall_seconds=time.monotonic()-started,**checked)
        result['rows'].append(row);dump(output/'profile.json',result)
        assert not checked['errors'],checked['errors']
        print('PASS '+label,flush=True);return record
    for group in GROUPS:
        entries={'maa_summary':['maa_indirect_load'],'dxc_summary':['dxc_tile_size']}.get(group,[])
        for name in entries:
            record=run('summary:'+name,lambda n=name:seed.prove('--summary',summary_id(n)),'proven')
            summaries[summary_id(name)]=record
        deps={summary_id(n):summaries[summary_id(n)] for n in
              {'maa_summary':['maa_const','maa_indirect_load'],'dxc_summary':['dxc_tile_size']}.get(group,[])}
        safe=run(group+':safe',lambda g=group:seed.unit(g),'proven',dependencies=deps)
        if group=='maa_summary':
            witness=caller_witness(safe,deps,matrix.audit,expected_candidate=candidates['safe'],expected_code=safe_atomic['pins']['code']);result['noop_caller_witness']=witness
            dump(output/'profile.json',result);assert not witness['errors'],witness['errors']
            for row in result['reused']:
                if row['label']=='summary:maa_const':row['acceptance']='accepted_with_unchanged_caller_witness';row['witness_record']=safe['id']
        goal={'maa_summary':'ensures','dxc_summary':'ensures','templates':'ensures','classes':'loop_invariant',
              'omp':('loop_invariant','ensures'),'new_array':'rte_mem_access'}[group]
        run(group+':seeded',lambda g=group:seed.unit(g,candidate='bug'),'not_proven',ordinary_open=goal,dependencies=deps)
        if group=='new_array':
            for label in ['new_out_of_range','new_after_delete',*('new_'+n for n in TERMINAL_CONTROLS)]:
                run(label,lambda n=label:seed.unit(n),'not_proven',actual=label=='new_out_of_range',
                    ordinary_open='rte_mem_access' if label=='new_out_of_range' else None)
    assert sha(source.parent/'matrix.json')==STOPPED_MATRIX, 'historical input matrix changed'
    result.update(complete=True,success=True);dump(output/'profile.json',result);return 0


if __name__=='__main__':raise SystemExit(main())
