"""Read-only production catalog trial; only the local proposal report is written."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from archevolve.hardware_catalog import load_catalog, query_catalog, validate_catalog

HERE = Path(__file__).resolve().parent
BASE = '6868383615c8aa89752923850d1bf0c170b6ba0b'
DESIGN = 'tmu-micro2023-fig8-spmv'
SUBTYPE = 'csr_spmv_two_lane_operand_event_supply'


def main():
    source = ROOT / 'catalog/hardware-v0.1.yaml'
    before_bytes = source.read_bytes()
    assert before_bytes == subprocess.check_output(['git', 'show', BASE + ':catalog/hardware-v0.1.yaml'], cwd=ROOT)
    existing, digest = load_catalog(source)
    frozen = deepcopy(existing)
    proposal, proposal_digest = load_catalog(HERE / 'proposed-catalog.json')
    assert proposal['designs'][0]['record_kind'] == 'mapping'
    trial = deepcopy(existing)
    for field in ('sources', 'claims'):
        assert not (set(trial[field]) & set(proposal[field]))
        trial[field].update(deepcopy(proposal[field]))
    for field in ('mechanism_families', 'decision_questions', 'designs'):
        assert not ({x['id'] for x in trial[field]} & {x['id'] for x in proposal[field]})
        trial[field].extend(deepcopy(proposal[field]))
    validation = validate_catalog(trial)
    outcomes = []

    def check(name, query, statuses, excluded=None, missing=None):
        result = query_catalog(trial, design_id=DESIGN, **query)
        assert [m['status'] for m in result['matches']] == statuses, name
        if excluded is not None:
            assert [m['status'] for m in result['excluded']] == excluded, name
        for m in result['matches']:
            assert m['requirements'] == proposal['designs'][0]['requirements']
            assert m['requirement_status'] == 'not_discharged_by_retrieval'
            if missing is not None:
                assert m['missing_capability_evidence'] == missing, name
        outcomes.append({'name': name, 'query': query,
                         'matches': [{'status': m['status'], 'missing': m['missing_capability_evidence']} for m in result['matches']],
                         'excluded': [m['status'] for m in result['excluded']]})

    check('exact mapping', {'operation': 'read', 'subtype': SUBTYPE, 'address_pattern': 'indirect', 'execution_role': 'execute'}, ['mapping_reference'], [])
    for payload, width in [('float32', 32), ('float64', 64), ('uint32', 64), ('int64', 32)]:
        check(f'unknown types {payload}/{width}', {'operation': 'read', 'subtype': SUBTYPE, 'payload_type': payload, 'index_width_bits': width}, ['needs_evidence'], [], ['payload_types', 'index_width_bits'])
    check('unknown payload alone', {'operation': 'read', 'subtype': SUBTYPE, 'payload_type': 'float32'}, ['needs_evidence'], [], ['payload_types'])
    check('generic gather gains no match', {'operation': 'read', 'subtype': 'gather'}, [], [])
    check('generic stream gains no match', {'operation': 'read', 'subtype': 'stream_load'}, [], [])
    check('not prefetch assistance', {'operation': 'read', 'execution_role': 'assist'}, [], [])
    check('pointer chase not examined', {'operation': 'read', 'subtype': SUBTYPE, 'address_pattern': 'pointer_chase'}, [], ['not_covered'])
    check('old value not supplied', {'operation': 'read', 'subtype': SUBTYPE, 'require_old_value': True}, [], ['excluded'])
    for operation, subtype in [('write', 'scatter'), ('reduce', 'add'), ('read_modify_write', 'add'), ('read_modify_write', 'cas')]:
        check(f'excluded {operation}/{subtype}', {'operation': operation, 'subtype': subtype, 'payload_type': 'float32', 'index_width_bits': 32}, [], ['excluded'])

    # Every original design is byte-for-byte logically retained, including every operation.
    original_trials = 0
    for design in frozen['designs']:
        retained = next(d for d in trial['designs'] if d['id'] == design['id'])
        assert retained == design
        for operation in design['operations']:
            for typed in ({}, {'payload_type': 'float32', 'index_width_bits': 32}):
                query = dict(operation=operation['operation'], subtype=operation['subtype'], design_id=design['id'], **typed)
                assert query_catalog(existing, **query) == query_catalog(trial, **query)
                original_trials += 1
    assert existing == frozen
    assert source.read_bytes() == before_bytes
    for field in ('sources', 'claims'):
        assert all(trial[field][k] == v for k, v in frozen[field].items())
    for field in ('mechanism_families', 'decision_questions', 'designs'):
        assert trial[field][:len(frozen[field])] == frozen[field]
    parameters = proposal['designs'][0]['parameters']
    assert all(p['domain'] is None for p in parameters)
    assert all(p['value'] is None for p in parameters if p['state'] == 'unknown')
    requirements = proposal['designs'][0]['requirements']
    assert len([r for r in requirements if r['verification'] == 'unknown']) == 5
    report = {'format': 'tmu-proposal-validation-v1', 'base_commit': BASE,
              'production_catalog_sha256': hashlib.sha256(before_bytes).hexdigest(),
              'loader_digest': digest, 'proposal_loader_digest': proposal_digest,
              'standalone': validate_catalog(proposal), 'in_memory_addition': validation,
              'proposal_queries': outcomes, 'unchanged_existing_designs': len(frozen['designs']),
              'unchanged_existing_query_trials': original_trials,
              'production_catalog_unchanged': True, 'required_unknowns_preserved': True,
              'scope': 'Catalog structure/reference and retrieval checks only; no hardware execution or mapping legality certification.'}
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'valid': True, 'proposal_queries': len(outcomes), 'unchanged_existing_query_trials': original_trials}))


if __name__ == '__main__':
    main()
