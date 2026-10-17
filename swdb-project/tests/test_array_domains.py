"""Explicit array-window input domains; created 2026-10-15 ET (tickets24/36).

Public validation binds a declaration to actual lowered parameters. A declaration
alone cannot bypass proof admission or replace a checked source-origin certificate.
"""
import hashlib
import shutil

import pytest
import yaml

from conftest import FIXTURES, make_records, run_swdb
from test_formal_frame import UNIT_CC, frame_contract, write_library
from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason="clang 22.1.8 is required for actual parameter bindings")


@pytest.fixture
def domain_library(tmp_path):
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    entry = frame_contract('contract.fixture_array_domain', role='enabling')
    write_library(library, {'proof_units/fixture_unit.cc': UNIT_CC,
                           'rewrite_contracts/array_domain.yaml': entry})
    return records, library, entry


def _validate(fixture, domains):
    records, library, entry = fixture
    entry['proof_unit']['array_domains'] = domains
    (library / 'rewrite_contracts/array_domain.yaml').write_text(yaml.safe_dump(entry, sort_keys=False))
    return run_swdb('validate', '--records', records.path, '--library', library)


@pytest.mark.parametrize('extent', ['n', '2 * n + 1', '(n - 1) + 1', '0'])
def test_explicit_integer_array_window_declaration_validates_against_real_parameters(domain_library, extent):
    result = _validate(domain_library, {'parent': {'extent': extent}})
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('domains,reason', [
    ([], 'mapping'),
    ({'parent': 'n'}, 'exactly extent'),
    ({'parent': {'extent': 'n', 'initialized': True}}, 'exactly extent'),
    ({'missing': {'extent': 'n'}}, 'pointer parameter'),
    ({'n': {'extent': 'n'}}, 'pointer parameter'),
    ({'parent': {'extent': 'parent'}}, 'integer parameter'),
    ({'parent': {'extent': 'missing'}}, 'integer parameter'),
    ({'parent': {'extent': 'n()'}}, 'integer arithmetic'),
    ({'parent': {'extent': 'n / 2'}}, 'integer arithmetic'),
    ({'parent': {'extent': True}}, 'expression string'),
    ({'parent': {'extent': '-1'}}, 'nonnegative'),
])
def test_invalid_or_implicitly_strengthened_domains_are_refused(domain_library, domains, reason):
    result = _validate(domain_library, domains)
    assert result.returncode == 1, result.stdout
    assert 'array_domains' in result.stderr and reason in result.stderr, result.stderr


def test_a_declaration_cannot_make_a_scripted_proof_run_without_origin_admission(domain_library, tmp_path):
    result = _validate(domain_library, {'parent': {'extent': 'n'}})
    assert result.returncode == 0, result.stderr
    records, library, _ = domain_library
    methods = library / 'methods'
    methods.mkdir()
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    marker = tmp_path / 'must-not-run'
    script = tmp_path / 'script.yaml'
    script.write_text(yaml.safe_dump({'verdict': 'proven', 'run': ['touch', str(marker)]}))
    result = run_swdb('prove', '--records', records.path, '--summary', 'contract.fixture_array_domain',
                      '--adapter', 'scripted', '--script', script, '--runs-dir', tmp_path / 'runs')
    assert result.returncode == 2, result.stdout
    assert 'array_domains' in result.stderr and 'origin certificate' in result.stderr, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize('name', ['lambda', 'async', 'True'])
def test_extent_names_keep_cpp_identifier_meaning(domain_library, name):
    _, library, entry = domain_library
    source = UNIT_CC.replace('int n)', f'int n, int {name})')
    (library / 'proof_units/fixture_unit.cc').write_text(source)
    entry['proof_unit']['source'] = dict(entry['proof_unit']['source'],
                                       sha256=hashlib.sha256(source.encode()).hexdigest())
    result = _validate(domain_library, {'parent': {'extent': name}})
    assert result.returncode == 0, result.stdout + result.stderr
