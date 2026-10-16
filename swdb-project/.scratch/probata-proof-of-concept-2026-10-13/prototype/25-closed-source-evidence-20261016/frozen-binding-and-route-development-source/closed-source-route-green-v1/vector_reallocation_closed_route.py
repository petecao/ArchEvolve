"""2026-10-16 ET. Opt-in source observation result; framework gate still pending.

This is a separate checked source interpretation using retained conditional
WP mathematics. It neither promotes the native Typed caller result nor
creates constructor/destructor model records.
"""
import hashlib
import json
from pathlib import Path

from swdb import std_models
from swdb import vector_reallocation_closed_binding as binding
from swdb import vector_reallocation_closed_evidence as source_rule


class Refused(ValueError):
    pass


METHOD = 'method.wp-vector-closed-source-v1'
EVIDENCE_DIRECTORY = 'proof_evidence/vector_closed_scientific_bundle'


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def identity():
    return {'id': 'vector-closed-source-route-1',
            'sha256': hashlib.sha256(_json({'source': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                            'scientific_binding': binding.identity()})).hexdigest()}


def bundle_identity():
    return {'id': 'vector-closed-scientific-bundle-1', 'sha256': binding.REVIEWED_CATALOG_SHA256}


def required_translators():
    return [source_rule.identity(), binding.identity(), bundle_identity(), identity()]


def selected(method):
    required = required_translators()
    translators = (method.data.get('c_lowering') or {}).get('translators') or []
    names = {row['id'] for row in required}
    requested = [row for row in translators if isinstance(row, dict) and row.get('id') in names]
    if not requested and method.id != METHOD:
        return False
    if method.id != METHOD or method.data.get('id') != METHOD or \
            method.data.get('evidence_kind') != 'contract_fixture' or \
            len(requested) != len(required) or any(row not in requested for row in required):
        raise Refused('closed source route requires its explicit fixture method and all exact current checker/bundle pins')
    return True


def declaration(method, lowering, source, formal_texts, scientific_directory, *, hints=(), defines=(), candidate=None):
    if not selected(method):
        raise Refused('closed source route is not selected by this method')
    if hints or defines or candidate is not None or lowering.function != 'vector_realloc_v3_no_growth':
        raise Refused('only the unchanged original closed no-growth summary without hints or build overrides is admitted')
    try:
        bound, files = binding.declaration(lowering, source, formal_texts, scientific_directory)
    except (binding.Refused, KeyError, OSError) as error:
        raise Refused(str(error)) from None
    rule = bound['source_rule']
    ledger = rule['original_source_obligation_ledger']
    if ledger['ordinary_count'] != 24 or ledger['smoke_count'] != 9 or ledger['frame_partitions'] != 13 or \
            len({row['goal'] for row in ledger['ordinary']}) != 24 or \
            rule['caller_premises_added'] or rule['observation']['total_Typed_to_Heap_encoding_claimed']:
        raise Refused('the complete original source observation derivation changed')
    source_goals = [{'goal': row['goal'], 'property': row['goal'], 'function': lowering.function,
        'status': 'valid', 'solver': source_rule.identity()['id'], 'seconds': None,
        'source': 'source_rule', 'smoke': False} for row in ledger['ordinary']]
    pins = {'vector_closed_source_rule': source_rule.identity(),
            'vector_closed_scientific_binding': binding.identity(),
            'vector_closed_scientific_bundle': bundle_identity(),
            'vector_closed_source_route': identity()}
    assumptions = [
        {'kind': 'trusted_tool', 'reference': source_rule.identity(),
         'sentence': 'The pinned checked source observation rule soundly interprets this exact source, its private automatic/dynamic allocation identities and hidden administrative storage; it preserves every incoming live byte observation and retained dead-identity history, with scalar capture before actual cleanup.'},
        {'kind': 'trusted_tool', 'reference': bundle_identity(),
         'sentence': 'The exact historical source-to-VC, WP/Qed, foundation, arithmetic/map/datatype and solver TCB recorded in the complete accepted scientific bundle is sound for its 82 unchanged conditional mathematical targets; historical compiler/method/checker identities are retained and are not relabeled current.'},
        {'kind': 'trusted_tool', 'reference': std_models.identity(),
         'sentence': 'The pinned allocator/library model supplies successful normal allocation with freshness, validity and freeability, incoming-memory framing and the specified null/dynamic release; separately linked allocator replacements or interposition obey these same modeled effects, and the standard-library bodies/contracts match the complete source interpretation.'},
    ]
    result = {'created': '2026-10-16 ET', 'checker': identity(), 'method': METHOD,
        'proof_basis': binding.PROOF_BASIS, 'original_contract': list(formal_texts),
        'caller_premises_added': [], 'scientific_target_count': 82,
        'source_obligations': source_goals, 'pins': pins, 'assumptions': assumptions,
        'source_rule': rule, 'scientific_binding': bound,
        'original_diagnostic': {'normal_verdict': 'not_proven',
            'original_entry_refusal_preserved': True,
            'ordinary': 24, 'smokes': 9, 'frame_partitions': 13,
            'native_false_or_ignored_initialization_and_freeable_facts_preserved': True},
        'native_projected_diagnostic': {'normal_verdict': 'not_proven',
            'role': 'supplemental conditional observation', 'ordinary': 17, 'smokes': 4,
            'modular_constructor_post_state_admitted': False, 'native_satisfiability_claimed': False},
        'correctness_scope': 'return scalar, initializedness/access and incoming observation/frame under the explicit modeled normal-return allocator/library/source TCB; no allocator or hardware termination theorem',
        'source_typed_bridge_established': False, 'current_model_records_created': [],
        'historical_records_rewritten': False, 'framework_integration_admitted': False,
        'public_proof_record_created': False, 'ticket25_acceptance': False}
    result_files = {'scientific-binding/'+name: raw for name, raw in files.items()}
    result_files['manifest.json'] = _json(result)
    return result, result_files


def prepare(method, lowering, source, formal_texts, scientific_directory, directory, **options):
    result, files = declaration(method, lowering, source, formal_texts, scientific_directory, **options)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return result


def check(method, lowering, source, formal_texts, scientific_directory, directory, **options):
    result, files = declaration(method, lowering, source, formal_texts, scientific_directory, **options)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise Refused('closed source result canonical membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise Refused('closed source result or complete bound evidence differs: '+name)
    return result


def check_launch(method, lowering, source, formal_texts, scientific_directory, directory, **options):
    check(method, lowering, source, formal_texts, scientific_directory, directory, **options)
    raise Refused('public framework setup/schema/adapter integration must be independently reviewed')
