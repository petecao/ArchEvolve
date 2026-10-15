"""A summary must describe the actual called definition; created 2026-10-15 ET.

Public prove seam: proving a library implementation does not prove a changed,
same-named definition in the candidate artifact.
"""
import hashlib
import copy
import json
import shutil

import pytest
import yaml

import test_cbmc_adapter as cbmc
from test_cbmc_adapter import cbmc_seed, seed
from test_wp_adapter import needs_wp
from conftest import FIXTURES, make_records, run_swdb


@pytest.fixture(scope='module')
def divergent_summary_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp('divergent-summary')
    original = cbmc.UNITS
    case = yaml.safe_load((FIXTURES / 'proof/regression_corpus/summary-same-name-different-body.yaml').read_text())
    old = case['input']['original_return']
    assert original.count(old) == 1
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cbmc, 'UNITS', original.replace(old, case['input']['changed_return']))
        candidates = cbmc.build_cbmc_seed(root)
    correct = root / 'library/proof_units/cbmc_fixture_units.cc'
    correct.write_text(original)
    for path in (root / 'library/rewrite_contracts').glob('fixture_cbmc_*.yaml'):
        contract = yaml.safe_load(path.read_text())
        contract['proof_unit']['source']['sha256'] = hashlib.sha256(original.encode()).hexdigest()
        path.write_text(yaml.safe_dump(contract, sort_keys=False))
    return cbmc.Seed(root, candidates)


@cbmc.needs_cbmc
@pytest.mark.parametrize('adapter', ['cbmc', 'crux-llvm-c', 'crux-llvm-cxx'])
def test_changed_candidate_callee_cannot_borrow_library_implementation_summary(divergent_summary_seed, adapter):
    seed = divergent_summary_seed
    summary = seed.read(seed.prove_summary())
    assert summary['verdict'] == 'proven', summary
    if adapter == 'cbmc':
        record = seed.read(seed.prove('swdb_fixture_clamp_all', cbmc.CLAMP_ALL,
                                      {'threads': 1, 'n': 2}))
    else:
        from swdb import crux_adapter
        if crux_adapter.locate()[3]:
            pytest.skip('Crux tool lookup is needed; the source refusal launches no Crux solver')
        done = seed.swdb('prove', '--candidate', seed.candidates['safe'], '--function', 'swdb_fixture_clamp_all',
            '--contract', cbmc.CLAMP_ALL, '--adapter', adapter, '--bounds', '{"threads":1,"n":2}',
            '--runs-dir', seed.runs, '--format', 'json')
        assert done.returncode == 0, done.stdout + done.stderr
        record = seed.read(json.loads(done.stdout))
    assert record['verdict'] != 'proven', record
    assert record['failure_class'] == 'unsupported_construct', record
    assert record['settings']['verifier_launched'] is False, record


@cbmc.needs_cbmc
def test_a_narrower_array_summary_cannot_cover_a_larger_caller(seed):
    summary = seed.read(seed.prove_summary(cbmc.ADD_ONE, bounds={'threads': 1, 'n': 2}))
    assert summary['verdict'] == 'proven', summary
    record = seed.read(seed.prove('swdb_fixture_call_outside', cbmc.CALL_OUTSIDE,
                                  {'threads': 1, 'n': 3}))
    assert record['verdict'] == 'not_proven', record
    assert record['failure_class'] == 'unsupported_construct', record
    assert record['settings']['verifier_launched'] is False, record


@cbmc.needs_cbmc
@pytest.mark.parametrize('changed', ['method', 'lowering', 'evidence', 'adapter', 'code'])
def test_a_summary_proof_must_match_its_method_implementation_and_retained_evidence(seed, changed):
    summary_out = seed.prove_summary()
    summary = seed.read(summary_out)
    assert summary['verdict'] == 'proven', summary
    if changed == 'method':
        old = seed.root / 'library/methods/contract-fixture-1.yaml'
        summary['pins']['method_version'] = {'id': yaml.safe_load(old.read_text())['id'],
                                            'sha256': hashlib.sha256(old.read_bytes()).hexdigest()}
    elif changed == 'lowering':
        summary['pins']['c_lowering']['sha256'] = '0' * 64
    elif changed == 'adapter':
        summary['job']['adapter'] = 'scripted'
    elif changed == 'code':
        summary['pins']['code']['sha256'] = '0' * 64
    else:
        summary['evidence']['reports'][0]['sha256'] = '0' * 64
    (seed.records / summary_out['path']).write_text(yaml.safe_dump(summary, sort_keys=False))
    record = seed.read(seed.prove('swdb_fixture_clamp_all', cbmc.CLAMP_ALL, {'threads': 1, 'n': 2}))
    assert record['verdict'] == 'not_proven', record
    assert record['failure_class'] == 'unsupported_construct', record
    assert record['settings']['verifier_launched'] is False, record


@cbmc.needs_cbmc
def test_a_newer_ineligible_summary_does_not_mask_an_eligible_proof(seed):
    summary = seed.read(seed.prove_summary())
    assert summary['verdict'] == 'proven', summary
    later = copy.deepcopy(summary)
    later['id'] += '.later'
    later['job']['batch'] = 'zzzz-later-ineligible'
    old = seed.root / 'library/methods/contract-fixture-1.yaml'
    later['pins']['method_version'] = {'id': yaml.safe_load(old.read_text())['id'],
                                      'sha256': hashlib.sha256(old.read_bytes()).hexdigest()}
    (seed.records / 'proofs' / f"{later['id']}.yaml").write_text(yaml.safe_dump(later, sort_keys=False))
    record = seed.read(seed.prove('swdb_fixture_clamp_all', cbmc.CLAMP_ALL, {'threads': 1, 'n': 2}))
    assert record['verdict'] == 'proven', record
    assert record['pins']['summaries'][0]['proof_record'] == summary['id'], record


@needs_wp
def test_wp_keeps_the_checked_generic_binding_through_its_final_settings_and_launch(tmp_path):
    from swdb import c_lowering
    from test_formal_frame import write_library
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    source = 'int leaf(int n) { return n; }\nint unit(int n) { return leaf(n) - n; }\n'
    contracts = {}
    for name, post in [('leaf', r'assigns \nothing; ensures \result == n;'),
                       ('unit', r'assigns \nothing; ensures \result == 0;')]:
        contract = cbmc._contract(f'contract.binding_{name}', name,
            [('post', 'postcondition', post, {'once': 'self'})], [])
        contract['proof_unit']['source'] = {'root': 'library', 'path': 'proof_units/unit.cc',
            'sha256': hashlib.sha256(source.encode()).hexdigest()}
        contracts[f'rewrite_contracts/{name}.yaml'] = contract
    write_library(library, {'proof_units/unit.cc': source, **contracts})
    methods = library / 'methods'
    methods.mkdir()
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    (methods / 'cbmc-fixture.yaml').write_text(yaml.safe_dump(cbmc.method_version(c_lowering.identity()), sort_keys=False))
    results = []
    for name in ('leaf', 'unit'):
        done = run_swdb('prove', '--records', records.path, '--summary', f'contract.binding_{name}',
            '--adapter', 'wp', '--runs-dir', tmp_path / 'runs', '--format', 'json', env={'SWDB_FRAMA_C': ''})
        assert done.returncode == 0, done.stdout + done.stderr
        result = json.loads(done.stdout)
        results.append(yaml.safe_load((records.path / result['path']).read_text()))
        assert results[-1]['verdict'] == 'proven', results[-1]
    unit = results[-1]
    assert unit['settings']['summary_bindings'][0]['proof_record'] == results[0]['id']
    assert unit['proof_setup_check']['runs'][-1]['hashes']['summary_bindings']
