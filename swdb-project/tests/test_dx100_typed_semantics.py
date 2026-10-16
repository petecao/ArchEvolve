"""2026-10-15 ET. Public validation of typed DX100 instance contracts.

Structural contract fixtures only; no hardware behavior or actual formal tool.
"""
import json

import pytest
import yaml

from conftest import make_records, run_swdb
from test_dx100_interface_inventory import QUIET, complete_fixture
from test_dx100_trust_entries import run_semantics_fixture
from test_proof_records import proof_seed, seed  # noqa: F401 (public scripted candidate fixture)


def typed_entry(tmp_path):
    library, entry, data = complete_fixture(tmp_path)
    row = next(row for row in data['calls'] if row['call'] == 'get_data_type')
    row['instances'] = [
        {'arguments': ['int'], 'arity': 0, 'prototype': 'int get_data_type_int(void)',
         'contract': r'assigns \nothing; ensures \result == 1;'},
        {'arguments': ['double'], 'arity': 0, 'prototype': 'int get_data_type_double(void)',
         'contract': r'assigns \nothing; ensures \result == 5;'}]
    return library, entry, data, row


@pytest.mark.parametrize('change, reason', [
    ('missing_contract', 'instance needs its own C prototype and contract'),
    ('duplicate_selector', 'duplicate template arguments and arity'),
    ('duplicate_symbol', 'instance C symbols must be distinct'),
    ('bad_arguments', 'instance arguments must be a nonempty list'),
    ('bad_arity', 'instance arity must be a nonnegative integer'),
    ('bad_list', 'instances must be a nonempty list'),
])
def test_incomplete_or_ambiguous_typed_instances_are_refused(tmp_path, change, reason):
    library, entry, data, row = typed_entry(tmp_path)
    if change == 'missing_contract':
        row['instances'][0].pop('contract')
    elif change == 'duplicate_selector':
        row['instances'][1]['arguments'] = ['int']
    elif change == 'duplicate_symbol':
        row['instances'][1]['prototype'] = row['instances'][0]['prototype']
    elif change == 'bad_arguments':
        row['instances'][0]['arguments'] = 'int'
    elif change == 'bad_arity':
        row['instances'][0]['arity'] = True
    else:
        row['instances'] = 3
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 1 and reason in result.stderr, result.stdout + result.stderr


def test_each_typed_contract_replaces_the_generic_family_contract_in_typechecking(tmp_path):
    library, entry, data, row = typed_entry(tmp_path)
    row.pop('prototype')
    row.pop('contract')
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '29 ACSL contracts' in result.stderr


@pytest.mark.parametrize('missing', [False, True])
def test_typed_allocation_instances_cover_both_literal_header_declarations(tmp_path, missing):
    library, entry, data, _row = typed_entry(tmp_path)
    allocation = next(row for row in data['calls'] if row['call'] == 'get_new_reg')
    allocation.pop('overloads')
    allocation['instances'] = [
        {'arguments': ['int'], 'arity': 1 if 'T1 data' in row['declaration'] else 0,
         'declaration': row['declaration'],
         'prototype': 'int get_new_reg_int_args1(int data)' if 'T1 data' in row['declaration']
                      else 'int get_new_reg_int_args0(void)',
         'contract': r'requires \false; assigns \nothing;'}
        for row in data['declaration_inventory']['declarations'] if row['name'] == 'get_new_reg']
    if missing:
        allocation['instances'].pop()
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    if missing:
        assert result.returncode == 1 and 'instances must cover its exact declarations' in result.stderr
    else:
        assert result.returncode == 0, result.stdout + result.stderr


def test_instance_and_generic_overload_selectors_cannot_silently_ignore_each_other(tmp_path):
    library, entry, data, row = typed_entry(tmp_path)
    row['overloads'] = [{'prototype': 'int ignored(void)', 'contract': r'assigns \nothing;'}]
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 1 and 'instances and overloads cannot both select' in result.stderr


@pytest.mark.parametrize('adapter', ['cbmc', 'wp'])
@pytest.mark.parametrize('case', ['missing', 'bad_abi', 'definition', 'good'])
def test_public_prove_binds_a_template_instance_before_accepting_a_family_contract(tmp_path, adapter, case):
    call = {'call': 'get_data_type', 'prototype': 'int get_data_type(void)',
            'contract': r'assigns \nothing;', 'rules': ['allocation'],
            'instances': [{'arguments': ['double'] if case == 'missing' else ['int'], 'arity': 0,
                           'prototype': ('double' if case == 'bad_abi' else 'int') + ' get_data_type_int(void)',
                           'contract': r'assigns \nothing; ensures \result == 1;'}]}
    source = ('template<class T> int get_data_type();\n'
              'int trust_fixture(int *p) { int x = get_data_type<int>(); p[0] = x; return x; }\n')
    if case == 'definition':
        source = source.replace('get_data_type();', 'get_data_type() { return 42; }')
    result, records, _entry, marker = run_semantics_fixture(tmp_path, adapter, source=source, extra_calls=[call])
    if case != 'good':
        reason = {'missing': 'no proof-semantics template instance',
                  'bad_abi': 'template instance C signature differs',
                  'definition': 'template instance needs a pinned interface definition'}[case]
        assert result.returncode == 1 and reason in result.stderr, result.stdout + result.stderr
        assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))
        return
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load((records.path / json.loads(result.stdout)['path']).read_text())
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct'
    assert record['settings']['verifier_launched'] is False and not marker.exists()
    assert record['settings']['proof_semantics']['instances'] == [
        {'name': 'get_data_type', 'c_name': 'get_data_type_int', 'arguments': ['int'], 'arity': 0}]


def test_a_fresh_execution_method_accepts_the_current_typed_contract_checker(seed):
    from swdb import proof_setup
    methods = seed.root / 'library/methods'
    method = yaml.safe_load((methods / 'contract-fixture-1.yaml').read_text())
    method.update(id='method.current-typed-contracts', sequence=3, evidence_kind='execution')
    method['checks'].update(proof_setup.identity())
    (methods / 'current-typed-contracts.yaml').write_text(yaml.safe_dump(method, sort_keys=False))
    marker = seed.root / 'scripted-command-started'
    record = seed.prove(seed.script(run=['/usr/bin/touch', str(marker)]),
                        '--method-version', method['id'])['record']
    assert marker.exists() and record['evidence_kind'] == 'contract_fixture'
    assert record['proof_setup_check']['check'] == method['checks']['proof_setup_check']


@pytest.mark.parametrize('adapter', ['cbmc', 'wp'])
def test_a_pointer_typedef_retains_the_actual_primitive_array_parameter_domain(tmp_path, adapter):
    source = ('typedef int *Pointer;\nvoid maa_const(int value, int reg);\n'
              'int trust_fixture(Pointer p) { maa_const(7, 0); p[0] = 7; return 7; }\n')
    result, records, _entry, marker = run_semantics_fixture(tmp_path, adapter, source=source)
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load((records.path / json.loads(result.stdout)['path']).read_text())
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct'
    assert record['settings']['verifier_launched'] is False and not marker.exists()
