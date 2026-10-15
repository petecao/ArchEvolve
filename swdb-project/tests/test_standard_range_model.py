"""Exact std::copy range-model relation; created 2026-10-15 ET.

These public preparation/replay API controls run Clang only, never a verifier.
The relation supplies explicit library domain metadata; it is not a body proof.
"""
import copy
from dataclasses import replace
import importlib
from pathlib import Path

import pytest

from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang 22.1.8 is required')


def api():
    return importlib.import_module('swdb.standard_range_model')


def test_exact_copy_relation_keeps_contract_body_initialization_and_explicit_typed_ranges(tmp_path):
    module = api()
    original = c_lowering.model_text('std_copy_int')
    view = module.wp_view('std_copy_int', original, tmp_path)
    module.check_view('std_copy_int', view, tmp_path)
    assert view.original == original
    assert view.certificate['original_contract_sha256'] == view.certificate['view_contract_sha256']
    assert view.certificate['acsl_input_premises_added'] == []
    assert view.certificate['domain_role'] == 'explicit standard-library valid-range domain; caller discharge required'
    assert view.certificate['standalone_scope'] == 'range-qualified body contract; not unrestricted opaque-pointer admission'
    domain = view.certificate['range_domain']
    assert domain['element_type'] == 'int'
    assert domain['source']['first'] == 'first' and domain['source']['last'] == 'last'
    assert domain['source']['same_array_required'] is True
    assert domain['destination']['first'] == 'd_first'
    assert domain['destination']['same_count_as_source'] is True
    assert domain['extent_acsl'].count('Pre') >= 2
    assert r'\initialized(first +' in view.text
    assert r'\initialized(d_first +' in view.text
    assert 'last - first' in view.text and 'd_first[i] = first[i]' in view.text
    assert 'std_copy_range_entry' in view.text and 'std_copy_range_access' in view.text
    assert 'std_copy_range_return' in view.text
    assert r'\valid' not in str(domain) and r'\base_addr' not in str(domain)


@pytest.mark.parametrize('replacement', [
    ('first[i]', 'first[i+1]'),
    ('d_first[i] = first[i]', 'd_first[i+1] = first[i]'),
    ('last - first;', 'last - first + 1;'),
    ('i < n;', 'i <= n;'),
    ('++i)', 'i += 2)'),
    ('d_first + n;', 'd_first + n + 1;'),
    (r'\initialized(first + (0 .. last - first - 1))', r'\true'),
    ('first <= last', 'first <= last + 1'),
])
def test_changed_copy_body_or_contract_has_no_audited_range_relation(tmp_path, replacement):
    module = api()
    original = c_lowering.model_text('std_copy_int')
    assert replacement[0] in original
    changed = original.replace(*replacement)
    with pytest.raises(module.Refused, match='exact audited'):
        module.wp_view('std_copy_int', changed, tmp_path)


@pytest.mark.parametrize('mutation', ['view', 'domain', 'premise', 'pin'])
def test_relation_replay_refuses_view_domain_and_policy_tampering(tmp_path, mutation):
    module = api()
    view = module.wp_view('std_copy_int', c_lowering.model_text('std_copy_int'), tmp_path)
    if mutation == 'view':
        changed = replace(view, text=view.text.replace('d_first[i] = first[i]', 'd_first[i] = 0'))
    elif mutation == 'pin':
        changed = replace(view, pins={})
    else:
        cert = copy.deepcopy(view.certificate)
        if mutation == 'domain':
            cert['range_domain']['source']['same_array_required'] = False
        else:
            cert['acsl_input_premises_added'] = ['requires n >= 0']
        changed = replace(view, certificate=cert)
    with pytest.raises(module.Refused, match='changed before launch'):
        module.check_view('std_copy_int', changed, tmp_path)


def test_scalar_models_and_arbitrary_opaque_model_text_do_not_gain_range_permission(tmp_path):
    module = api()
    for name in ('std_swap_int', 'std_min_int'):
        with pytest.raises(module.Refused, match='std_copy_int'):
            module.wp_view(name, c_lowering.model_text(name), tmp_path)


def test_generated_model_keeps_opaque_default_closed_and_accepts_only_exact_qualified_view(tmp_path):
    from swdb import wp_pointer_bounds
    module = api()
    view = module.wp_view('std_copy_int', c_lowering.model_text('std_copy_int'), tmp_path)
    source = '\n'.join([*c_lowering.HEADERS, view.text]) + '\n'
    with pytest.raises(wp_pointer_bounds.Refused, match='certified array-object origin'):
        wp_pointer_bounds.model_view(source, tmp_path)
    generated, report = wp_pointer_bounds.model_view(source, tmp_path, qualified=view)
    assert report['qualified_standard_range'] == view.certificate
    assert report['functions'] == ['std_copy_int']
    assert generated.count('std_copy_range_access') == 1
    assert 'std_copy_range_entry' in generated and 'std_copy_range_return' in generated
    assert r'\initialized(first +' in generated and r'\initialized(d_first +' in generated
    assert 'last - first' in generated and 'd_first + n' in generated
    assert len(report['sites']) == 2
    with pytest.raises(wp_pointer_bounds.Refused, match='qualified.*input'):
        wp_pointer_bounds.model_view(source + '\nint hidden(int*p){return p[4];}\n', tmp_path, qualified=view)


def _public_seed(tmp_path):
    import json
    import shutil
    import sys
    import yaml
    from conftest import FIXTURES, make_records, run_swdb
    from test_wp_adapter import method_version
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    methods = library / 'methods'; methods.mkdir(parents=True)
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    method = method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    marker = tmp_path/'wp-launched'
    frama = tmp_path/'frama.py'
    frama.write_text('import sys\nfrom pathlib import Path\n'
        'if "-version" in sys.argv: print("33.0");sys.exit(0)\n'
        'if "-wp" in sys.argv:\n'
        f' Path({str(marker)!r}).write_text("parser-error stand-in; no solver")\n'
        ' print("[kernel] wp_input.c:3: User Error: scripted fault\\nFrama-C aborted: invalid user input.");sys.exit(1)\n')
    why3 = tmp_path/'why3.conf'
    names = {'alt-ergo':'Alt-Ergo','z3':'Z3','cvc5':'CVC5'}
    why3.write_text(''.join(f'[prover]\nname = "{names[row["tool"]]}"\nversion = "{row["version"]}"\n'
                           'command = "/usr/bin/false"\n' for row in method['lineup'] if row['tool'] in names))
    def prove(*args, ok=True):
        done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
            '--runs-dir',tmp_path/'runs','--format','json',*args,env={
                'SWDB_FRAMA_C':f'{sys.executable} {frama}','WHY3CONFIG':str(why3),
                'SWDB_VERIFIER_LOCK':str(tmp_path/'standin-only.lock')})
        if not ok:
            return done
        assert done.returncode == 0, done.stdout + done.stderr
        return yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    return library, prove, marker


def test_public_copy_model_records_typed_qualification_and_preserves_checks_before_standin(tmp_path):
    from pathlib import Path
    library, prove, marker = _public_seed(tmp_path)
    record = prove('--model','std_copy_int')
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'parse_error',record
    assert marker.exists()  # version/parse-error stand-in only; never a proof result
    cert = record['settings']['standard_range_model']
    assert cert['domain_role'] == 'explicit standard-library valid-range domain; caller discharge required'
    assert cert['original_contract_sha256'] == cert['view_contract_sha256']
    assert 'standard_range_model_check' in record['pins']
    assert 'standard_range_model_certificate' in record['pins']
    flags = record['settings']['flags']
    assert '-wp-no-filter-init' in flags and '-rte-initialized' in flags and '-wp-smoke-tests' in flags
    assert '-wp-rte' in flags
    report = next(r for r in record['evidence']['reports'] if r['name']=='wp_input')
    text = Path(report['path']).read_text()
    assert 'std_copy_range_access' in text and r'\initialized(first +' in text
    assert 'swdb_model_pointer_formation_' in text
    assert record['proof_setup_check']['verdict'] == 'passed'
    assert record['proof_setup_check']['runs'][-1]['hashes']['standard_range_model']


def test_public_typed_caller_still_requires_a_current_qualified_model_proof(tmp_path):
    import hashlib
    import json
    from test_formal_frame import frame_contract, write_library
    library, prove, marker = _public_seed(tmp_path)
    source = ('#include <algorithm>\nint unit(int n) { int a[1]={7}; int b[1]={0}; '
              'std::copy(a,a+1,b); return b[0]; }\n')
    entry = frame_contract('contract.fixture_copy_domain', role='enabling', concurrency_frame=[], clauses=[
        {'id':'post','role':'postcondition','statement':'The safe scalar copy result is seven.',
         'discharge_mode':'runtime_guard','negative_control':{'id':'post-control','check':'fixture'},
         'acsl':{'text':r'assigns \nothing; ensures \result == 7;', 'uses':[]},
         'proof_placement':{'once':'self'}}])
    entry['proof_unit']={'function':'unit','source':{'root':'library','path':'proof_units/copy.cc',
        'sha256':hashlib.sha256(source.encode()).hexdigest()}}
    write_library(library,{'proof_units/copy.cc':source,'rewrite_contracts/copy.yaml':entry})
    done = prove('--summary',entry['id'],ok=False)
    assert done.returncode != 0
    assert 'std_copy_int' in done.stderr and 'no proven record at its current text' in done.stderr
    assert not marker.exists()


@pytest.mark.parametrize('mutation', ['none','qualification_omitted','guard_removed','canonical_changed'])
def test_prelaunch_rebuild_cannot_omit_domain_or_checked_numeric_obligations(tmp_path, monkeypatch, mutation):
    from types import SimpleNamespace
    from swdb import proof, proof_setup, wp_pointer_bounds
    module = api()
    scratch=tmp_path/'scratch';scratch.mkdir()
    original=c_lowering.model_text('std_copy_int')
    view=module.wp_view('std_copy_int',original,scratch)
    source='\n'.join([*c_lowering.HEADERS,view.text])+'\n'
    text,report=wp_pointer_bounds.model_view(source,scratch,qualified=view)
    unit=proof.ProofUnit(None,'std_copy_int',str(tmp_path),'0'*64,'c_model.std_copy_int','0'*64)
    job=proof.Job(unit,(),scratch,tmp_path/'adapter.log',bounds={},budget_seconds=30)
    adapter=SimpleNamespace(name='wp',library=None)
    proof_setup.begin(job,adapter,{'method_version':{'not_applicable':'Static prelaunch control.'}},None)
    context={'pointer_bounds_model_source':source,'wp_expected_text':text,'pointer_bounds_report':report,
             'standard_range_model':{'view':view}}
    if mutation=='qualification_omitted':
        del context['standard_range_model']
    elif mutation=='guard_removed':
        text=text.replace('assert std_copy_range_access:', 'assert removed_range_check:')
        context['wp_expected_text']=text
    elif mutation=='canonical_changed':
        monkeypatch.setattr(c_lowering,'model_text',lambda name:original.replace('i < n;', 'i <= n;'))
    path=scratch/'wp_input.c';path.write_text(text)
    flags=['-wp-cache','none','-machdep','x86_64','-wp-model','+real','-wp-no-filter-init']
    if mutation=='none':
        proof_setup.check_generated(job,adapter,context,[(path,text)],flags)
    else:
        with pytest.raises(proof.AdapterError,match='pointer_bounds'):
            proof_setup.check_generated(job,adapter,context,[(path,text)],flags)
