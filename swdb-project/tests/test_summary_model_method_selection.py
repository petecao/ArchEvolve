"""2026-10-16 ET. Requested/default methods through both public prove routes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from conftest import FIXTURES, REPO
from testkit.vector_closed_workflow import CONTRACT_ID, build_closed_source_fixture


@pytest.mark.parametrize('route, selection', [('summary', 'named'), ('summary', 'default'), ('summary', 'missing'),
                                             ('model', 'named'), ('model', 'default'), ('model', 'missing')])
def test_public_summary_and_model_preserve_explicit_method_selection(tmp_path, monkeypatch, route, selection):
    # The observer never consults installed tools. These are explicit fixture
    # method values only, supplied to the shared builder's no-discovery input.
    template = yaml.safe_load((FIXTURES/'proof/methods/contract-fixture-1.yaml').read_bytes())
    fixture_lineup = {row['tool']: row['version'] for row in template['lineup']
                      if row['tool'] in {'frama-c-wp', 'alt-ergo', 'cvc5', 'z3'}}
    monkeypatch.setenv('SWDB_DX100_SELECTOR_ACTUAL_LINEUP', json.dumps(fixture_lineup))
    records, named = build_closed_source_fixture(tmp_path)
    method = {'named': named, 'default': 'method.contract-fixture-1', 'missing': 'method.never-written'}[selection]
    argv = ['prove', '--records', records, '--adapter', 'wp', '--runs-dir', tmp_path/'runs', '--format', 'json']
    argv += ['--summary', CONTRACT_ID] if route == 'summary' else ['--model', 'std_vector_int_size']
    if selection != 'default':
        argv += ['--method-version', method]
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'SWDB_CLANG': 'none', 'SWDB_FRAMA_C': 'none',
                   'SWDB_CBMC': 'none', 'SWDB_CRUX_LLVM': 'none'}
    done = subprocess.run([sys.executable, '-B', str(FIXTURES/'proof/method_selection_observer.py'), *map(str, argv)],
        cwd=REPO, env=environment, capture_output=True, text=True, timeout=60)
    if selection == 'missing':
        assert done.returncode == 1 and 'no method-version file' in done.stderr and method in done.stderr, done.stdout+done.stderr
        assert not list((records/'proofs').glob('*.yaml'))
        assert not (tmp_path/'runs').exists()
        return
    assert done.returncode == 0, done.stdout+done.stderr
    record = yaml.safe_load((records/json.loads(done.stdout)['path']).read_bytes())
    source = tmp_path/'library/methods'/(method.removeprefix('method.')+'.yaml')
    assert record['pins']['method_version'] == {'id': method, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    assert record['proof_setup_check']['method_version'] == record['pins']['method_version']
    assert record['settings']['selected_method'] == method
    assert record['settings']['verifier_launched'] is False and record['settings']['scientific_result'] is False
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unknown'
    assert record['evidence_kind'] == 'contract_fixture'
    assert record['subject']['kind'] == ('library_summary' if route == 'summary' else 'c_model')
