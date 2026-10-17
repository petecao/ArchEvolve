"""2026-10-16 ET. Freeze an inert, self-contained stdin observer from local metadata.

No SSH, project imports, catalog reads, compilers, native helpers or solvers.
The first capture cannot grant semantic acceptance: its record/empty-map encoding
attribution is deliberately pending. Root owns review and any passive execution.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
EVIDENCE = POC / 'evidence/resume-20261016-lane-coordination'


def raw_sha(value):
    return hashlib.sha256(value).hexdigest()


def pin(path):
    value = path.read_bytes()
    return {'path': str(path), 'bytes': len(value), 'sha256': raw_sha(value)}


def write(path, value):
    if path.exists():
        raise ValueError('fresh frozen output required: ' + str(path))
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def main():
    packet_dir = HERE.parent / 'public10-v2/inert-d7f685c6-public10-v2'
    expected = json.loads((packet_dir / 'expected.json').read_bytes())
    observed_path = EVIDENCE / 't25-owned-transfer10-v2-actual-passive-failure-census-20261016.json'
    metadata_path = EVIDENCE / 't25-owned-transfer10-v2-actual-passive-metadata-pins-20261016.json'
    observed = json.loads(observed_path.read_bytes())
    metadata = json.loads(metadata_path.read_bytes())
    prior_path = POC / 'evidence/t25-private-frame9-independent-cold-decision-20261016.json'
    prior = json.loads(prior_path.read_bytes())
    assert raw_sha(prior_path.read_bytes()) == '8c8764bcdc2d6939251cc3966eb9032220b69040f24560c2fb03d7b3eb4e201f'
    context = {
        'schema': 'ownership10-g621-passive-context-1', 'date': '2026-10-16 ET',
        'semantic_source_sha256': raw_sha((HERE / 'semantic_terms.py').read_bytes()),
        'frozen_root_command': json.loads((packet_dir / 'root-command.json').read_bytes()),
        'frozen_root_command_file_sha256': raw_sha((packet_dir / 'root-command.json').read_bytes()),
        'resolved_root_command_sha256': raw_sha(json.dumps([value.replace('{SOURCE}', '/data1/yanruj/probata-resume-20261016-d7f685c6').replace('{OUTPUT}', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-d7f685c6-owned-transfer10-public-v2') for value in json.loads((packet_dir / 'root-command.json').read_bytes())], sort_keys=True, separators=(',', ':')).encode()),
        'raw_membership': sorted([{key: row[key] for key in ('relative', 'kind', 'bytes') if
                                 key in row and (key != 'bytes' or row['kind'] == 'regular')}
                                 for row in observed['entries']], key=lambda row: Path(row['relative']).parts),
        'known_metadata_pins': {name: {key: row[key] for key in ('bytes', 'sha256')}
                               for group in (observed['metadata'], metadata['metadata'])
                               for name, row in group.items()},
        'resource_policy': expected['resource_policy'], 'canonical_manifest': expected['canonical_manifest'],
        'method_flags': ['-wp', '-wp-rte', '-wp-cache', 'none', '-wp-model', '+real', '-wp-par', '1',
            '-machdep', 'x86_64', '-rte-initialized', '@all', '-wp-no-filter-init', '-machdep', 'x86_64',
            '-wp-prover', 'alt-ergo,z3,cvc5', '-wp-timeout', '30', '-wp-par', '1', '-wp-smoke-tests',
            '-wp-status-all', '-wp-out', 'prover-files', '-wp-print', '-wp-msg-key',
            'print-generated,why3:compile,why3:import,prover:pp_task'],
        'primary_standard_support': prior['primary_support_attribution'],
        'support_boundary': 'Only exact complete non-goal assertion hashes with prior primary-source attribution. No prior goals, outcomes, proofs, project Heap claims or sibling ownership duties are imported as premises; unknown current assertions remain unresolved.',
        'constructive_consistency': {
            'classification': 'SOURCE_LEVEL_DEFINITIONAL_MODEL_ARGUMENT_NOT_EMPIRICAL_SMOKE',
            'theory_sha256': 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6',
            'model': 'Integers are ordinary unbounded integers; maps are total mathematical functions; state is the product (Int->Bool)x(Int->Int). Owners adds only total definitions, no axioms/lemmas/goals. empty uses constant false/zero maps. Set updates and every transition are total, hence the Owners extension has this concrete model relative to standard Int/Map support.',
            'empty_valid_witness': {'frontier': 1, 'active_owners': [], 'all_other_active': False, 'all_backings': 0},
            'nonvacuous_move_witness': {'frontier': 4, 'active_owners': [1, 2], 'backings': {'1': 0, '2': 3}, 'all_other_active': False, 'destination': 1, 'source': 2},
            'nonvacuous_swap_and_retire_witness': {'frontier': 5, 'active_owners': [1, 2], 'backings': {'1': 3, '2': 4}, 'all_other_active': False, 'left_or_retired': 1, 'right_or_other': 2},
            'shared_backing_countermodel_to_exclusivity': {'active_owners': [1, 2], 'backings': {'1': 3, '2': 3}, 'all_other_active': False},
            'limitation': 'Finite examples exhibit satisfiable antecedents and the intended unrestricted integer/map model; they do not prove universal goals or source/Heap correspondence. Zero generated smoke goals supply no empirical consistency or body reachability evidence. Standard theory/driver/solver soundness and source-to-runtime correspondence remain explicit TCB.'},
    }
    semantic = (HERE / 'semantic_terms.py').read_text()
    observer = (HERE / 'observer.py').read_text()
    marker = "if __name__ == '__main__':"
    assert observer.count(marker) == 1
    source = observer.replace(marker, 'CONTEXT_JSON = ' + repr(json.dumps(context, sort_keys=True, separators=(',', ':'))) +
                              '\nSEMANTIC_SOURCE = ' + repr(semantic) + '\n\n' + marker)
    # Parse and compile only. The observer's main and all actual inputs remain
    # unexecuted. No pyc is written by compile().
    ast.parse(source)
    compile(source, '<inert-ownership10-stdin-observer>', 'exec')
    (HERE / 'entry.py').write_text(source)
    write(HERE / 'context.json', context)
    command = {'schema': 'ownership10-g621-passive-stdin-command-1', 'date': '2026-10-16 ET',
        'status': 'INERT_REVIEW_REQUIRED', 'actual_executed': False,
        'host': 'mbit10', 'argv_after_root_read_only_preflight': ['/usr/bin/python3', '-I', '-B', '-'],
        'stdin': pin(HERE / 'entry.py'), 'outer_timeout_seconds': 200,
        'inner_alarm_seconds': 180, 'address_space_bytes': 536870912,
        'stdout_cap_bytes': 2097152, 'remote_filesystem_writes': False,
        'sole_child': 'Closed read-only /usr/bin/git rev-parse/status only; no tool/config/version queries.',
        'expected_completed_capture_exit': 2,
        'exit_scope': 'Exit2 is complete metadata/term capture with unresolved source encodings, never cold proof acceptance. Exit1 refuses a physical/source/guard/parser boundary; semantic acceptance remains false.',
        'root_required': 'Independent exact-source review, fresh read-only host preflight and explicit admission before any invocation. No lane claim/release, compiler/native/prover/solver execution or raw mutation.'}
    write(HERE / 'command.json', command)
    inputs = [packet_dir / name for name in ('packet.json', 'entry.py', 'expected.json', 'root-command.json')]
    inputs += [observed_path, metadata_path, prior_path,
               POC / 'evidence/t25-owned-transfer10-v2-root-execution-20261016.json',
               POC / 'evidence/t25-owned-transfer10-v2-root-admission-20261016.json']
    receipt = {'schema': 'ownership10-g621-cold-capture-source-packet-1', 'date': '2026-10-16 ET',
        'status': 'INERT_COMPLETE_CAPTURE_READER_PENDING_ENCODING_INTERPRETATION',
        'actual_executed': False, 'scientific_acceptance': False, 'root_review_required': True,
        'source_commit': expected['source_commit'], 'producer_lane': {'node': 0, 'generation': 621},
        'raw_files': 184, 'raw_bytes': 21000828, 'targets': 10, 'materialized_tasks': 20,
        'ordinary_native_valid_reported': 10, 'normal_global_lemma_smokes': 0,
        'inputs': [pin(path) for path in inputs],
        'outputs': [pin(HERE / name) for name in ('observer.py', 'semantic_terms.py', 'entry.py', 'context.json', 'command.json', 'pure_controls.py')],
        'remaining_semantic_gate': 'First physical capture does not bless Owners state-record/constant-map driver encoding or unknown non-goal support. Every such item is emitted as unresolved; no semantic cold PASS exists until independently attributed and source-reviewed.',
        'no_new_source_or_caller_or_Heap_Typed_body_default_public_record_admission': True,
        'runtime_boundary': 'Initial retained runtime snapshot plus source-recorded check control flow and fresh passive before/after hashes; not historical continuous or complete Python/OS loader/dlopen/source-to-binary closure. Prior Why3server gaps are not retroactively promoted.'}
    write(HERE / 'source-packet.json', receipt)
    print(json.dumps(pin(HERE / 'source-packet.json')))


if __name__ == '__main__':
    main()
