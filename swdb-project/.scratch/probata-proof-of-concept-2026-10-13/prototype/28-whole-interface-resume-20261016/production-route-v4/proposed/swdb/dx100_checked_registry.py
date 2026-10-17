"""Closed unit registry consumption through the normal physical read set.

2026-10-16 ET. Structural baseline lookup grants no source/contract admission.
The actual proof gate repeats the complete source/function/contract-hash lookup.
This module performs no compiler, native, verifier or child execution.
"""
import json
from pathlib import Path

from swdb._dx100_whole import unit_policy_registry_v2 as registry


def load(library, reads, reference):
    """Read all four policies and five canonical contract files before lookup."""
    from swdb import dx100_checked_source as source
    from swdb.library import Library
    source.need(type(reads) is source.Inputs and type(library) is Library,
                'normal selected library and producer read set required')
    raw = reads.portable(reference)
    value = registry.document(raw)
    registry.exact(value, {'kind', 'schema', 'choice_budget', 'units'}, 'unit registry')
    source.need(type(value['units']) is list and len(value['units']) == len(registry.FUNCTIONS),
                'complete closed unit registry required before document reads')
    policies, contracts = {}, {}
    for unit, definition in zip(value['units'], registry.FUNCTIONS):
        function, source_sha, expected = definition
        registry.exact(unit, {'source', 'function', 'contracts', 'policy'}, 'registry unit')
        registry.portable(unit['source']); registry.portable(unit['policy'])
        registry.contract_rows(unit['contracts'], expected)
        source.need(unit['function'] == function and unit['source']['sha256'] == source_sha,
                    'exact source/function registry order required before document reads')
        selected = unit['policy']['sha256']
        source.need(selected not in policies, 'distinct selected policy bytes required')
        policies[selected] = reads.portable(unit['policy'])
        for row in unit['contracts']:
            ident = row['id']
            data = library.get(ident)
            source.need(ident not in contracts and type(data) is dict and ident in library.files,
                        'complete distinct actual library contracts required')
            path = Path(library.files[ident])
            source.need(path.is_relative_to(library.root / 'rewrite_contracts'),
                        'registered contracts must be physical rewrite-contract files')
            pin = {'root': 'library', 'path': path.relative_to(library.root).as_posix(), 'sha256': row['sha256']}
            actual = reads.portable(pin)
            source.need(actual == registry.canonical(data) and library.content_sha256(ident) == row['sha256'],
                        'registered physical canonical contract differs from selected library data')
            contracts[ident] = actual
    checked = registry.validate(raw, policies, contracts)
    reads.recheck()
    return checked


def baseline(library, reads, reference, proof_unit):
    checked = load(library, reads, reference)
    selected = registry.baseline_policy(checked, proof_unit)
    raw = reads.portable(selected['policy'])
    reads.recheck()
    return selected['policy'], registry.document(raw)


def contract(unit, contract_id, contract_sha256, rows):
    """Actual selected contract gate; no inferred result or baseline fallback."""
    from swdb import dx100_checked_source as source
    source.need(type(unit) is source.SourceUnit, 'producer-created source unit required')
    reads = source.Inputs(unit.selection.library)
    _entry, normalized, policy = source.source_policy(unit.selection, reads)
    source.need(registry.canonical(policy) == unit.policy_json and 'unit_registry' in normalized,
                'fresh selected registered policy required')
    from swdb.library import Library
    physical = Library(unit.selection.library.root)
    checked = load(physical, reads, normalized['unit_registry'])
    selected = registry.lookup(checked, source=policy['proof_source'], function=unit.function,
        contract_id=contract_id, contract_sha256=contract_sha256)
    source.need(selected['policy'] == normalized['source_policy'],
                'actual contract selected a different per-unit source policy')
    expected = selected['contract']['expected_result']
    source.need(len(rows) == 2 and sorted((row.kind, ' '.join(row.text.split())) for row in rows) ==
                [('assigns', r'\everything'), ('ensures', r'\result == ' + str(expected))],
                'registered source unit has an extra premise/frame/property or wrong result')
    reads.recheck()


def harness_clauses(unit, rows):
    """The selected property changes no source/model/receiver/draw behavior."""
    from swdb import dx100_checked_source as source
    policy = json.loads(unit.policy_json)
    definition = [row for row in registry.FUNCTIONS if row[0] == unit.function]
    source.need(len(definition) == 1 and policy['function'] == unit.function
                and policy['proof_source']['sha256'] == definition[0][1],
                'exact registered harness source/function required')
    registry.contract_rows(policy['unit_contracts'], definition[0][2])
    expected = [[('assigns', r'\everything'), ('ensures', r'\result == ' + str(row['expected_result']))]
                for row in policy['unit_contracts']]
    source.need(len(rows) == 2 and sorted((row.kind, ' '.join(row.text.split())) for row in rows) in expected,
                'exact selected source-policy scalar property and whole-state frame required')
