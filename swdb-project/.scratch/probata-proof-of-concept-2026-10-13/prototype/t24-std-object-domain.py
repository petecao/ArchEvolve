#!/usr/bin/env python3
"""Distinct std safe-domain fixture, reusing normally eligible actual models, 2026-10-15 ET.

The input seed is read only. Only copied records/library and new proof outputs are
written. The original failed contract is retained as a named negative receipt.
No production checker, source fixture, model, method or original clause changes.
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
from swdb import artifacts, c_lowering, host_identity, proof_setup, standard_range_model  # noqa: E402
import yaml  # noqa: E402
from t24_std_object_domain import corrected_contract, original_contract, QUALIFIED_ID, GAP_LABEL  # noqa: E402
from test_wp_subset import MODELS, contract_id  # noqa: E402

spec = importlib.util.spec_from_file_location('t24_original_matrix', Path(__file__).with_name('t24-original-matrix.py'))
matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matrix)
FROZEN = '0e7f232762e4555aa9435a3a3622923fad8ee928'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--from-seed', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--public-timeout-seconds', type=int, default=1800)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if not 600 <= args.public_timeout_seconds <= 7200:
        parser.error('public timeout must be between 600 and 7200 seconds')
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip()
    assert head == args.expected_commit, 'unexpected runner source commit'
    assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no','--',':(top)swdb-project'],
                                       cwd=REPO, text=True).strip(), 'tracked source changes'
    source = args.from_seed.resolve()
    prior = json.loads((source.parent/'matrix.json').read_text())
    manifest = json.loads((source.parent/'source-manifest.json').read_text())
    assert prior['commit'] == manifest['commit'] == FROZEN, 'reuse source is not the diagnosed current freeze'
    runtime_sources = {p:digest for p,digest in manifest['sources'].items() if p.startswith('swdb/')}
    current_runtime = set(subprocess.check_output(['git','ls-files','swdb'], cwd=REPO, text=True).splitlines())
    assert set(runtime_sources) == current_runtime, 'runtime source file set differs from 0e7'
    assert runtime_sources and all(sha(REPO/p) == digest for p,digest in runtime_sources.items()), 'runtime differs from 0e7'
    os.environ['SWDB_VERIFIER_RSS_CAP_BYTES'] = '8589934592'
    os.environ[host_identity.FIXTURE_HOST_ENV] = 'swdb-fixture-host'
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    seed_path = output/'seed'
    seed_path.mkdir()
    for directory in ('records','library'):
        shutil.copytree(source/directory, seed_path/directory)
    candidates = json.loads((source.parent/'candidates.json').read_text())
    method_file = seed_path/'library/methods/wp-tracer-fixture.yaml'
    method = yaml.safe_load(method_file.read_text())
    assert c_lowering.identity()['c_lowering'] in method['c_lowering']['translators'], 'current translator differs'
    original_file = seed_path/'library/rewrite_contracts/fixture_wp24_std_models.yaml'
    original_bytes = original_file.read_bytes()
    original = yaml.safe_load(original_bytes)
    assert original == original_contract(), 'original contract differs from diagnosed fixture'
    corrected = corrected_contract(original)
    qualified_file = seed_path/'library/rewrite_contracts/fixture_wp24_std_models_object_domain.yaml'
    qualified_file.write_text(yaml.safe_dump(corrected, sort_keys=False))
    reused = []
    for name in MODELS['std_models']:
        row, = [r for r in prior['rows'] if r['label'] == 'model:'+name]
        physical = Path(row['record']['path'])
        assert sha(physical) == row['record']['sha256'], 'prior model record changed'
        record = yaml.safe_load(physical.read_text())
        checked = matrix.audit(record, 'proven')
        assert not checked['errors'], checked['errors']
        assert record['subject'] == {'kind':'c_model','id':name}, 'unexpected model subject'
        assert record['pins']['method_version'] == {'id':method['id'],'sha256':sha(method_file)}, 'method differs'
        assert record['proof_setup_check']['check'] == proof_setup.identity()['proof_setup_check'], 'setup checker differs'
        assert record['pins']['code'] == {'id':name,'sha256':hashlib.sha256(c_lowering.model_text(name).encode()).hexdigest()}
        assert record['pins']['contract'] == record['pins']['code'], 'model contract text differs'
        copied = seed_path/'records/proofs'/physical.name
        assert copied.read_bytes() == physical.read_bytes(), 'copied model record differs'
        if name == standard_range_model.NAME:
            view = standard_range_model.wp_view(name, c_lowering.model_text(name), output)
            assert record['settings']['standard_range_model'] == view.certificate, 'range qualification differs'
            assert all(record['pins'].get(k) == pin for k,pin in view.pins.items()), 'qualification pins differ'
        reused.append({'model':name,'id':record['id'],'record':row['record'],'copied_path':str(copied)})
    gap, = [r for r in prior['rows'] if r['label'] == 'std_models:safe']
    gap_file = Path(gap['record']['path'])
    assert sha(gap_file) == gap['record']['sha256']
    gap_record = yaml.safe_load(gap_file.read_text())
    assert gap_record['verdict'] == 'not_proven' and gap_record['pins']['contract'] == {
        'id':contract_id('std_models'),'sha256':artifacts.digest(original)}
    assert any(not g.get('smoke') and g['status'] != 'valid' and 'swdb_pointer_formation_1' in g['goal']
               for g in gap_record['goals']), 'missing original contract-gap obligation'
    result = {'created':'2026-10-15 ET','commit':head,'runtime_freeze':FROZEN,
              'runtime_sources':runtime_sources,'runtime_identity':c_lowering.identity(),
              'source_seed':str(source),'source_matrix_sha256':sha(source.parent/'matrix.json'),
              'method':{'id':method['id'],'sha256':sha(method_file)},'candidates':candidates,
              'qualified_contract':{'id':QUALIFIED_ID,'sha256':artifacts.digest(corrected),
                                    'file_sha256':sha(qualified_file)},
              'retained_original_gap':{'label':GAP_LABEL,'record':gap['record'],
                    'original_expected':'proven','original_acceptance_errors':gap.get('errors',[]),
                    'verdict':'not_proven','role':'retained original contract-gap negative; no unchanged-original success'},
              'reused_models':reused,'public_timeout_seconds':args.public_timeout_seconds,
              'ordinary_dependency_eligibility':'public swdb prove must resolve these records normally; no bypass',
              'zero_size_boundary':'live zero-size allocations are not represented by the readable-neighbor proxy; no UB claim',
              'rows':[],'complete':False,'check_only':args.check_only}
    dump(output/'profile.json', result)
    if args.check_only:
        print('PASS source/model/contract preflight; no proof launched', flush=True)
        return 0
    seed = matrix.MatrixSeed(seed_path, candidates, args.public_timeout_seconds)
    for candidate,label,expected in [('safe','safe','proven'),('bug','seeded','not_proven')]:
        started = time.monotonic()
        print('START std_models_object_domain:'+label, flush=True)
        record = seed.prove('--candidate',candidates[candidate],'--function','swdb_std_unit',
                            '--contract',QUALIFIED_ID)
        checked = matrix.audit(record, expected, ordinary_open=('ensures','swdb_pointer_formation','swdb_window_copy','rte_'))
        pins = record['pins']
        assert pins['contract'] == {'id':QUALIFIED_ID,'sha256':artifacts.digest(corrected)}
        actual = {p['id']:p for p in pins.get('models',[])}
        assert set(actual) == set(MODELS['std_models']), 'model closure differs'
        for reused_row in reused:
            assert actual[reused_row['model']]['proof_record'] == reused_row['id'], 'public dependency selection differs'
        proof_file = seed.records/'proofs'/(record['id']+'.yaml')
        checked.update(label='std_models_object_domain:'+label,
                       record={'path':str(proof_file),'sha256':sha(proof_file)},wall_seconds=time.monotonic()-started)
        result['rows'].append(checked)
        dump(output/'profile.json', result)
        assert not checked['errors'], checked['errors']
        assert original_file.read_bytes() == original_bytes, 'original contract changed'
        print('PASS '+checked['label'], flush=True)
    result['complete'] = True
    result['success'] = True
    dump(output/'profile.json', result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
