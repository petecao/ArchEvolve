"""2026-10-16 ET. Minimal public closed-source proof fixture, no import probes."""
import hashlib
from pathlib import Path
import shutil

import yaml

from conftest import FIXTURES, REPO, make_records
from testkit.vector_reallocation import CONTRACT, SOURCE


CONTRACT_ID = 'contract.fixture_vector_closed_no_growth'


def build_closed_source_fixture(root, *, control='safe'):
    from swdb import c_lowering, proof_setup, std_models
    from swdb import vector_reallocation_closed_route as route
    from testkit.dx100_selector import bind_actual_lineup, read_actual_lineup
    records = make_records(root)
    records.path.mkdir(exist_ok=True)
    library = Path(root)/'library'
    methods = library/'methods'
    methods.mkdir(parents=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml', methods)
    method = yaml.safe_load((FIXTURES/'proof/methods/contract-fixture-1.yaml').read_bytes())
    method.update(id=route.METHOD, sequence=2, status='draft', created='2026-10-16',
                  description='Explicit closed-source interpretation fixture with exact historical WP mathematics.')
    method['lineup'] = yaml.safe_load((REPO/'library/methods/probata-draft-1.yaml').read_bytes())['lineup']
    next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')['flags'] += [
        '-rte-initialized', '@all', '-wp-no-filter-init']
    bind_actual_lineup(method, read_actual_lineup())
    method['c_lowering']['translators'] = [c_lowering.identity()['c_lowering'], *route.required_translators()]
    method['models']['std_vector'] = std_models.identity()
    method['checks'].update(proof_setup.identity())
    if control == 'stale_method':
        method['c_lowering']['translators'][-1]['sha256'] = '0'*64
    elif control == 'default_method':
        method['id'] = 'method.wp-vector-closed-default-v1'
        method['c_lowering']['translators'] = method['c_lowering']['translators'][:1]
    (methods/(method['id'].removeprefix('method.')+'.yaml')).write_text(yaml.safe_dump(method, sort_keys=False))
    units = library/'proof_units'
    units.mkdir()
    unit = units/SOURCE.name
    shutil.copyfile(SOURCE, unit)
    clauses = list(CONTRACT)
    if control == 'wrong_result':
        clauses[-1] = r'ensures \result == 123;'
    entry = {
        'kind': 'rewrite_contract', 'id': CONTRACT_ID, 'formal_frame': 1, 'version': '1.0',
        'provenance': {'origin': {'intrinsic_specification': 'vector-closed-source-fixture-20261016'}},
        'proof_unit': {'function': 'vector_realloc_v3_no_growth', 'source': {'root': 'library',
            'path': 'proof_units/'+SOURCE.name, 'sha256': hashlib.sha256(unit.read_bytes()).hexdigest()}},
        'concurrency_frame': [],
        'clauses': [{'id': name, 'role': role, 'statement': 'Closed source '+name,
            'discharge_mode': 'runtime_guard', 'negative_control': {'id': name+'-control', 'check': name},
            'acsl': {'text': text, 'uses': []}, 'proof_placement': {'once': 'self'}}
            for (name, role), text in zip((('pre', 'legality'), ('frame', 'postcondition'),
                                          ('post', 'postcondition')), clauses, strict=True)],
        'pattern_key': [{'roles': ['index', 'target'], 'address_shapes': ['stream', 'single_valued_indirect'],
                         'update_kind': 'read'}],
        'strategies': [], 'uses_intrinsics': [], 'uses_library_operations': [], 'runtime_guards': [],
        'knobs': [], 'preservation_obligations': [], 'correctness_check': {'kernel': 'fixture', 'check': 'fixture'},
        'execution_witness': {'check': 'fixture'},
        'negative_controls': [{'id': kind, 'kind': kind, 'check': 'fixture'}
            for kind in ('overlapping_pointer', 'double_claim', 'dropped_operand')], 'requirement_map': []}
    contracts = library/'rewrite_contracts'
    contracts.mkdir()
    (contracts/'fixture_vector_closed_no_growth.yaml').write_text(yaml.safe_dump(entry, sort_keys=False))
    if control != 'missing_bundle':
        shutil.copytree(FIXTURES/'proof/vector_closed_scientific_bundle', library/route.EVIDENCE_DIRECTORY)
    return records.path, method['id']
