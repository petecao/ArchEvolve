"""2026-10-15 ET. Ticket28 complete header surface, through public validate.

Approved seams: validate for immutable declarations/contracts and prove/level for
later synthetic rule scenarios. Missing tools remain unchecked, never proof.
"""
import json
import shutil

import pytest
import yaml

from conftest import REPO, make_records, run_swdb

QUIET = {'SWDB_FRAMA_C': 'none', 'SWDB_CLANG': 'none'}
MANIFEST = REPO / 'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json'


def fixture_entry(tmp_path):
    """A validation fixture only; its added unreachable contracts prove nothing."""
    library = tmp_path / 'library'
    for folder in ('proof_semantics', 'dx100'):
        shutil.copytree(REPO / 'library' / folder, library / folder)
    entry = library / 'proof_semantics/dx100_bfs_0_1.yaml'
    data = yaml.safe_load(entry.read_text())
    manifest = json.loads(MANIFEST.read_text())
    data['declaration_inventory'] = {k: manifest[k] for k in ('sources', 'declarations')}
    return library, entry, data


def test_a_complete_interface_cannot_silently_keep_only_the_bfs_call_subset(tmp_path):
    library, entry, data = fixture_entry(tmp_path)
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    records = make_records(tmp_path)
    result = run_swdb('validate', '--records', records.path, '--library', library, env=QUIET)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'interface declaration' in result.stderr and 'get_noncacheable_tile_pointer' in result.stderr
    assert 'print_tile' in result.stderr and 'get_data_type' in result.stderr


def test_the_initialized_register_allocation_overload_needs_its_own_contract(tmp_path):
    library, entry, data = fixture_entry(tmp_path)
    covered = {row['call'] for row in data['calls']}
    for name in sorted({row['name'] for row in data['declaration_inventory']['declarations']} - covered):
        data['calls'].append({'call': name, 'prototype': f'void {name}(void)',
                              'contract': r'requires \false; assigns \nothing;', 'rules': ['allocation']})
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    records = make_records(tmp_path)
    result = run_swdb('validate', '--records', records.path, '--library', library, env=QUIET)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'get_new_reg' in result.stderr and 'overload' in result.stderr


def complete_fixture(tmp_path):
    library, entry, data = fixture_entry(tmp_path)
    covered = {row['call'] for row in data['calls']}
    declarations = data['declaration_inventory']['declarations']
    for name in sorted({row['name'] for row in declarations} - covered):
        data['calls'].append({'call': name, 'prototype': f'void {name}(void)',
                              'contract': r'requires \false; assigns \nothing;', 'rules': ['allocation']})
    allocation = next(row for row in data['calls'] if row['call'] == 'get_new_reg')
    allocation['overloads'] = [
        {'declaration': row['declaration'],
         'prototype': 'int get_new_reg__initialized(int data)' if 'T1 data' in row['declaration']
                      else 'int get_new_reg(void)',
         'contract': r'requires \false; assigns \nothing;'}
        for row in declarations if row['name'] == 'get_new_reg']
    return library, entry, data


def test_full_pinned_declarations_and_both_allocation_contracts_are_accepted_as_unchecked(tmp_path):
    library, entry, data = complete_fixture(tmp_path)
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'UNCHECKED' in result.stdout + result.stderr and '28 ACSL contracts' in result.stderr


@pytest.mark.parametrize('change, expected', [
    ('delete_declaration', 'complete pinned header declarations'),
    ('duplicate_declaration', 'complete pinned header declarations'),
    ('invent_declaration', 'complete pinned header declarations'),
    ('delete_contract', 'interface declaration maa_stream_store has no call contract'),
    ('delete_overload_contract', 'overload needs its own C prototype and contract'),
    ('duplicate_overload_symbol', 'overload C symbols must be distinct'),
    ('repoint_header', 'immutable upstream header'),
])
def test_complete_interface_manifest_controls_refuse_missing_or_invented_coverage(tmp_path, change, expected):
    library, entry, data = complete_fixture(tmp_path)
    inventory = data['declaration_inventory']
    allocation = next(row for row in data['calls'] if row['call'] == 'get_new_reg')
    if change == 'delete_declaration':
        inventory['declarations'].pop()
    elif change == 'duplicate_declaration':
        inventory['declarations'].append(inventory['declarations'][0])
    elif change == 'invent_declaration':
        inventory['declarations'][0] = {**inventory['declarations'][0], 'name': 'invented_api'}
    elif change == 'delete_contract':
        data['calls'] = [row for row in data['calls'] if row['call'] != 'maa_stream_store']
    elif change == 'delete_overload_contract':
        allocation['overloads'][0].pop('contract')
    elif change == 'duplicate_overload_symbol':
        allocation['overloads'][1]['prototype'] = allocation['overloads'][0]['prototype']
    elif change == 'repoint_header':
        inventory['sources'][1] = dict(inventory['sources'][0])
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 1, result.stdout + result.stderr
    assert expected in result.stderr


def test_malformed_overload_metadata_is_a_validation_problem_not_a_typechecker_crash(tmp_path):
    library, entry, data = complete_fixture(tmp_path)
    next(row for row in data['calls'] if row['call'] == 'get_new_reg')['overloads'] = 1
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('validate', '--records', make_records(tmp_path).path, '--library', library, env=QUIET)
    assert result.returncode == 1 and 'overloads' in result.stderr
    assert 'Traceback' not in result.stderr, result.stderr
