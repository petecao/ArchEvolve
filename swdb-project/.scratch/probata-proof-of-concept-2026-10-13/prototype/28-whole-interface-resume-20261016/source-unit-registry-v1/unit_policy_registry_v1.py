"""2026-10-16 ET. Closed original-source unit-policy registry, data only.

One new0.2 entry may pin this registry, while each unit retains its exact source,
contract, receiver, atlas and compiler certificate. Validation consumes bytes;
the normal producer must obtain/recheck them through its fixed physical read
set. No caller callback, Library substitute, process or source admission occurs
here. The old first-source policy is referenced without rewriting its bytes.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re

KIND = 'dx100-whole-interface-source-v1'
SCHEMA = 'dx100-whole-closed-unit-policy-registry-1'
FIRST_SHA = '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
MEMORY_SHA = '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
FUNCTIONS = (
    ('whole_interface_source_fixture', FIRST_SHA, ((79, 'contract.dx100_whole_source_79'), (80, 'contract.dx100_whole_source_80'))),
    ('whole_same_thread_read_during_store', MEMORY_SHA, ((7, 'contract.dx100_whole_same_thread_read_during_store'),)),
    ('whole_same_thread_write_during_gather', MEMORY_SHA, ((9, 'contract.dx100_whole_same_thread_write_during_gather'),)),
    ('whole_same_thread_read_during_gather', MEMORY_SHA, ((7, 'contract.dx100_whole_same_thread_read_during_gather'),)),
)
POLICY_KEYS = {'kind', 'schema', 'function', 'caller_mangled', 'defines', 'choice_budget', 'thread',
    'buffer_projection', 'proof_source', 'capture', 'receiver_selection', 'expected', 'producer_manifest',
    'native_projection', 'frame', 'unit_contracts', 'source_loop_bound', 'helper_loop_bound'}


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def exact(value, fields, label):
    need(type(value) is dict and set(value) == set(fields), label + ' exact fields required')


def document(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 4 * 1024 * 1024, 'bounded explicit document bytes required')
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate registry/policy/contract key refused')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(Refused('nonfinite registry document refused')))


def portable(row):
    exact(row, {'root', 'path', 'sha256'}, 'source/policy reference')
    need(row['root'] in ('library', 'project') and type(row['path']) is str and row['path']
         and not PurePosixPath(row['path']).is_absolute() and '\\' not in row['path']
         and row['path'] == PurePosixPath(row['path']).as_posix()
         and not any(part in ('', '.', '..', '.git', '__pycache__') for part in row['path'].split('/')),
         'canonical portable source/policy reference required')
    need(type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'exact lowercase reference digest required')
    return row


def contract_rows(rows, expected):
    need(type(rows) is list and len(rows) == len(expected), 'complete exact per-unit contract census required')
    for row, (value, name) in zip(rows, expected):
        exact(row, {'id', 'sha256', 'expected_result'}, 'unit contract selection')
        need(row['id'] == name and type(row['expected_result']) is int and row['expected_result'] == value
             and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']),
             'closed source-specific contract identity/result required')


def check_policy(policy, unit, definition, budget):
    function, source_sha, expected = definition
    exact(policy, POLICY_KEYS, 'source policy')
    need(policy['kind'] == KIND and policy['function'] == function and policy['proof_source'] == unit['source']
         and policy['caller_mangled'] == '_Z' + str(len(function)) + function + 'v'
         and policy['defines'] == ['NUM_CORES=4', 'TILE_SIZE=16384']
         and type(policy['thread']) is int and policy['thread'] == 0
         and type(policy['choice_budget']) is int and policy['choice_budget'] == budget
         and type(policy['source_loop_bound']) is int and policy['source_loop_bound'] == 1
         and type(policy['helper_loop_bound']) is int and policy['helper_loop_bound'] == 513
         and policy['frame'] == r'assigns \everything;',
         'exact function/configuration/source/whole-frame/budget required')
    if source_sha == FIRST_SHA:
        need(policy['schema'] == 'dx100-whole-fixed-source-policy-1'
             and policy['buffer_projection'] == 'fixed-fixture-identical-buffer-with-captured-diagnostic-origin-v1',
             'original79/80 policy schema/projection must remain unchanged')
    else:
        need(policy['schema'] == 'dx100-whole-exact-memory-source-policy-1'
             and policy['buffer_projection'] == 'exact-three-root-cxx-view-with-captured-origin-v1',
             'separate exact memory-source policy required')
    contract_rows(policy['unit_contracts'], expected)
    need(policy['unit_contracts'] == unit['contracts'], 'registry and selected policy contract hashes differ')
    # These subdocuments remain owned by the real complete source consumer.
    # Checking their content/physical closure is never replaced by this lookup.
    for name in ('capture', 'expected', 'native_projection'):
        need(type(policy[name]) is dict and policy[name], 'complete downstream source binding required: ' + name)
    portable(policy['receiver_selection']); portable(policy['producer_manifest'])


def check_contract(raw, row, unit):
    value = document(raw)
    need(type(value) is dict and value.get('id') == row['id'] and value.get('kind') == 'rewrite_contract'
         and digest(value) == row['sha256'], 'actual unit contract content differs from registry')
    need(value.get('proof_unit') == {'source': unit['source'], 'function': unit['function']}
         and value.get('concurrency_frame') == [], 'exact no-parameter source unit/empty interface frame required')
    clauses = value.get('clauses')
    need(type(clauses) is list and len(clauses) == 2, 'separate exact frame/result clause rows required')
    texts = []
    for clause in clauses:
        need(type(clause) is dict and type(clause.get('acsl')) is dict,
             'exact formal unit clause required')
        acsl = clause['acsl']
        need(set(acsl) <= {'text', 'uses'} and acsl.get('uses', []) == [] and type(acsl.get('text')) is str,
             'unit registry has no extra logic imports')
        texts.append(' '.join(acsl['text'].split()))
    need(sorted(texts) == sorted([r'assigns \everything;', r'ensures \result == ' + str(row['expected_result']) + ';']),
         'registered contract has extra premise/frame/property or wrong result')
    return value


@dataclass(frozen=True)
class Registry:
    input_bytes: bytes
    policy_byte_identities: tuple
    contract_content_identities: tuple


def validate(registry_raw, policy_documents, contract_documents):
    """Validate complete bytes, never fill receipts or construct a source unit.

    `policy_documents` is keyed by each referenced physical byte SHA; contract
    documents are keyed by actual library ID. Root/normal producer must read all
    documents through its closed physical read set before and after each use.
    """
    registry = document(registry_raw)
    exact(registry, {'kind', 'schema', 'choice_budget', 'units'}, 'unit registry')
    need(registry['kind'] == KIND and registry['schema'] == SCHEMA
         and type(registry['choice_budget']) is int and registry['choice_budget'] == 256,
         'closed registry/schema/common draw budget required')
    units = registry['units']
    need(type(units) is list and len(units) == len(FUNCTIONS), 'all four closed source units are mandatory')
    needed_policies, needed_contracts, memory_sources, memory_captures = set(), set(), [], []
    identities, content = [], []
    for unit, definition in zip(units, FUNCTIONS):
        exact(unit, {'source', 'function', 'contracts', 'policy'}, 'registry unit')
        function, source_sha, expected = definition
        portable(unit['source']); portable(unit['policy'])
        need(unit['function'] == function and unit['source']['sha256'] == source_sha,
             'exact source hash/function registry order required')
        contract_rows(unit['contracts'], expected)
        reference = unit['policy']['sha256']
        need(reference not in needed_policies and type(policy_documents) is dict
             and reference in policy_documents, 'distinct complete selected policy documents required')
        raw = policy_documents[reference]
        need(type(raw) is bytes and sha(raw) == reference, 'selected source policy byte identity differs')
        policy = document(raw)
        check_policy(policy, unit, definition, registry['choice_budget'])
        identities.append((reference, len(raw))); needed_policies.add(reference)
        if source_sha == MEMORY_SHA:
            memory_sources.append(unit['source'])
            memory_captures.append(policy['capture'])
        for row in unit['contracts']:
            need(row['id'] not in needed_contracts and type(contract_documents) is dict and row['id'] in contract_documents,
                 'distinct complete actual contract documents required')
            check_contract(contract_documents[row['id']], row, unit)
            content.append((row['id'], row['sha256'])); needed_contracts.add(row['id'])
    need(memory_sources == [memory_sources[0]] * 3, 'three memory callers must share one complete original source/TU buffer')
    need(memory_captures == [memory_captures[0]] * 3, 'three memory callers must share one exact complete-TU capture/ABI transport')
    need(set(policy_documents) == needed_policies and set(contract_documents) == needed_contracts,
         'unselected extra/missing registry documents refused')
    return Registry(registry_raw, tuple(identities), tuple(content))


def lookup(registry, *, source, function, contract_id, contract_sha256):
    """Exact runtime source/function/contract selection; never a name fallback."""
    need(type(registry) is Registry, 'freshly validated registry required')
    portable(source)
    value = document(registry.input_bytes)
    matches = [(unit, row) for unit in value['units'] if unit['source'] == source and unit['function'] == function
        for row in unit['contracts'] if row['id'] == contract_id and row['sha256'] == contract_sha256]
    need(len(matches) == 1, 'source hash/function/contract ID/hash tuple is not registered')
    unit, contract = matches[0]
    return {'source': unit['source'], 'function': unit['function'], 'policy': unit['policy'],
        'contract': contract, 'registry_sha256': sha(registry.input_bytes),
        'source_or_runtime_admission_granted': False}


def baseline_policy(registry, proof_unit):
    """Structural validation view only; actual proof lookup still needs a hash.

    A no-parameter baseline is shared by79/80. Both rows must point to its same
    exact policy, so this view cannot change source/model/receiver by result.
    """
    need(type(registry) is Registry and type(proof_unit) is dict
         and set(proof_unit) == {'source', 'function'}, 'exact registered structural proof unit required')
    portable(proof_unit['source'])
    value = document(registry.input_bytes)
    matches = [unit for unit in value['units']
        if unit['source'] == proof_unit['source'] and unit['function'] == proof_unit['function']]
    need(len(matches) == 1, 'unregistered baseline source/function refuses')
    return {'policy': matches[0]['policy'], 'registry_sha256': sha(registry.input_bytes),
        'structural_view_only': True, 'contract_or_source_admission_granted': False}


def assemble(policy_references, policy_documents, contract_documents):
    """Build only the registry bytes around four unchanged prepared policies.

    Contracts -> individual policy -> registry -> shared semantics entry is the
    dependency order. This function creates none of those prior documents and
    cannot mint context, mapping, compiler or runtime ownership receipts.
    """
    need(type(policy_references) is list and len(policy_references) == 4,
         'four exact externally prepared policy references required')
    units, budgets = [], []
    for reference, (function, _source_sha, _expected) in zip(policy_references, FUNCTIONS):
        portable(reference)
        need(type(policy_documents) is dict and reference['sha256'] in policy_documents,
             'complete exact prepared policy bytes required')
        policy = document(policy_documents[reference['sha256']])
        need(type(policy) is dict and policy.get('function') == function, 'prepared policy registry order differs')
        units.append({'source': policy['proof_source'], 'function': function,
            'contracts': policy['unit_contracts'], 'policy': reference})
        budgets.append(policy['choice_budget'])
    need(all(type(budget) is int and budget == budgets[0] for budget in budgets),
         'all unit policies must use the same explicit independently drawn budget')
    raw = canonical({'kind': KIND, 'schema': SCHEMA, 'choice_budget': budgets[0], 'units': units})
    checked = validate(raw, policy_documents, contract_documents)
    return {'registry_bytes': raw, 'registry_sha256': sha(raw),
        'unchanged_policy_byte_identities': checked.policy_byte_identities,
        'contract_content_identities': checked.contract_content_identities,
        'owned_receipts_emitted': False, 'scientific_acceptance': False}
