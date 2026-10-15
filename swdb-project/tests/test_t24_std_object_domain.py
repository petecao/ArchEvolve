"""Distinct explicit std fixture domain; no production policy change, 2026-10-15 ET."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
import yaml
from swdb import artifacts, c_lowering, framac
from t24_std_object_domain import corrected_contract, original_contract, QUALIFIED_ID
from conftest import FIXTURES

PROFILE = Path(__file__).resolve().parents[1]/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-std-object-domain.py'


def test_corrected_fixture_is_distinct_and_preserves_original_source_and_clauses():
    case = yaml.safe_load((Path(__file__).parent/'fixtures/proof/regression_corpus/wp-std-empty-contract-gap.yaml').read_text())
    original = original_contract()
    assert original['id'] == case['input']['original_contract']
    assert artifacts.digest(original) == case['input']['original_contract_sha256']
    before = copy.deepcopy(original)
    corrected = corrected_contract(original)
    assert original == before
    assert corrected['id'] == QUALIFIED_ID != original['id']
    assert QUALIFIED_ID == case['input']['qualified_contract']
    assert corrected['proof_unit'] == original['proof_unit']
    assert [c for c in corrected['clauses'] if c['id'] != 'empty_object_domain'] == original['clauses']
    domain = next(c for c in corrected['clauses'] if c['id'] == 'empty_object_domain')['acsl']['text']
    assert 'n == 0 ==>' in domain
    for pointer in ('a', 'b'):
        assert pointer + r' == \null' in domain
        assert r'\valid(' + pointer + ')' in domain
        assert r'\valid(' + pointer + ' - 1)' in domain


@pytest.mark.parametrize('mutation', ['post', 'source', 'domain'])
def test_qualified_fixture_cannot_silently_take_an_altered_original(mutation):
    original = original_contract()
    if mutation == 'post': original['clauses'][-1]['acsl']['text'] = r'ensures \true;'
    if mutation == 'source': original['proof_unit']['function'] = 'another_function'
    if mutation == 'domain': original['proof_unit']['array_domains']['a']['extent'] = 'n + 1'
    with pytest.raises(ValueError, match='exact original std fixture'):
        corrected_contract(original)


def test_corrected_domain_typechecks_over_original_names_and_rejects_a_wrong_field():
    if c_lowering.locate().missing or framac.locate().missing:
        pytest.skip('Clang22.1.8 and Frama-C33 typechecker required')
    lowered = c_lowering.lower(FIXTURES/'proof/lowering/std_models.cc','swdb_std_unit')
    contract = corrected_contract(original_contract())
    texts = '\n'.join(c['acsl']['text'] for c in contract['clauses'])
    head, declaration = lowered.declaration.rstrip('\n').rsplit('\n',1)
    assert framac.typecheck(framac.locate(),head+'\n/*@ '+texts+' */\n'+declaration+'\n') is None
    wrong = texts.replace(r'\valid(a)',r'\valid(a->missing)')
    assert framac.typecheck(framac.locate(),head+'\n/*@ '+wrong+' */\n'+declaration+'\n') is not None


def test_targeted_profile_documents_read_only_reuse_without_launching_a_proof():
    done = subprocess.run([sys.executable,str(PROFILE),'--help'],capture_output=True,text=True,
                          env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
    assert done.returncode == 0,done.stderr
    assert '--from-seed' in done.stdout and '--check-only' in done.stdout


@pytest.mark.parametrize('timeout', ['0','7201'])
def test_invalid_targeted_profile_budget_stops_before_touching_input_or_output(tmp_path,timeout):
    output = tmp_path/'unused'
    done = subprocess.run([sys.executable,str(PROFILE),'--expected-commit','unused',
        '--from-seed',str(tmp_path/'missing'),'--output',str(output),'--public-timeout-seconds',timeout],
        capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
    assert done.returncode == 2 and 'between 600 and 7200' in done.stderr
    assert not output.exists()


@pytest.mark.parametrize('location', ['seed', 'matrix', 'checkout'])
def test_targeted_profile_rejects_output_inside_historical_input_or_checkout_before_mutation(tmp_path,location):
    source = tmp_path/'historical'/'seed'
    source.mkdir(parents=True)
    output = {'seed':source/'new', 'matrix':source.parent/'new',
              'checkout':PROFILE.parent/'unused-review-control'}[location]
    done = subprocess.run([sys.executable,str(PROFILE),'--expected-commit','unused',
        '--from-seed',str(source),'--output',str(output)],capture_output=True,text=True,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
    assert done.returncode == 2 and 'disjoint from the historical input matrix' in done.stderr
    assert not output.exists()
    assert list(source.iterdir()) == []


def _public_contract_validation(tmp_path, contract):
    from conftest import run_swdb
    from test_wp_subset import UNITS
    records=tmp_path/'records';records.mkdir()
    library=tmp_path/'library'
    (library/'rewrite_contracts').mkdir(parents=True)
    (library/'proof_units').mkdir()
    (library/'proof_units/subset_units.cc').write_text(UNITS)
    (library/'rewrite_contracts/std.yaml').write_text(yaml.safe_dump(contract,sort_keys=False))
    done = run_swdb('validate','--records',records,'--library',library,timeout=90)
    (tmp_path/'public-validation.json').write_text(json.dumps({
        'command':list(map(str,done.args)),'returncode':done.returncode,
        'stdout':done.stdout,'stderr':done.stderr},indent=2)+'\n')
    return done


def test_qualified_fixture_passes_public_library_validation(tmp_path):
    done = _public_contract_validation(tmp_path, corrected_contract(original_contract()))
    assert done.returncode == 0, done.stdout + done.stderr


def test_previous_readable_domain_retains_its_actual_public_admission_failure(tmp_path):
    from t24_std_object_domain import rejected_readable_contract, REJECTED_ID
    rejected = rejected_readable_contract(original_contract())
    case = yaml.safe_load((Path(__file__).parent/'fixtures/proof/regression_corpus/wp-std-domain-public-vocabulary.yaml').read_text())['input']
    assert rejected['id'] == REJECTED_ID == case['rejected_contract'] != QUALIFIED_ID
    assert artifacts.digest(rejected) == case['rejected_contract_sha256']
    done = _public_contract_validation(tmp_path, rejected)
    assert done.returncode == 1
    assert f"FAILED: {case['errors']} error(s)" in done.stdout + done.stderr
    for builtin in case['forbidden_builtins']:
        assert 'memory built-in ' + builtin + ' is not allowed' in done.stdout + done.stderr
