"""Validate research references and non-admission; never execute the DRT source."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from archevolve.hardware_catalog import load_catalog, query_catalog, validate_catalog
from tools.render_mermaid import RequestError

BASE = 'c44ca66b5b1a121ed258d0d972172cda2de307b6'
DESIGN = 'drt-asplos2023-fig5-fixed-partition-spmspm'


def validate_research(p):
    assert p['format'] == 'drt-typed-research-proposal-v1'
    assert p['status'] == 'research_proposal_not_production'
    assert p['base_commit'] == BASE
    assert len(p['records']) == 1
    sources, claims = p['sources'], p['claims']
    assert sources and claims
    for c in claims.values():
        assert c['evidence_kind'] in {'paper_specification', 'code_inspection', 'research_inference'}
        assert c['source_refs'] and set(c['source_refs']) <= sources.keys()
        assert c['locator'] and c['statement']

    def refs(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == 'claim_refs':
                    assert v and len(v) == len(set(v)) and set(v) <= claims.keys()
                elif k == 'source_refs':
                    assert v and len(v) == len(set(v)) and set(v) <= sources.keys()
                else:
                    refs(v)
        elif isinstance(x, list):
            for item in x:
                refs(item)
    refs(p)
    r = p['records'][0]
    assert r['id'] == DESIGN and r['record_kind'] == 'research_mapping'
    assert r['role'] == 'required_hierarchy_local_sparse_tile_orchestration'
    assert [x['stage_kind'] for x in r['stages']] == [
        'capacity_admission', 'metadata_construction', 'required_tile_supply']
    assert r['result']['result_kind'] == 'hierarchy_local_tile_work'
    assert r['result']['payload_types'] == r['result']['index_width_bits'] == []
    assert r['identity']['wire_encoding'] is None
    assert r['consumer_lifetime']['release_event'] is None
    assert r['consumer_lifetime']['visibility_event'] is None
    assert not r['v0_disposition']['admitted']
    assert r['v0_disposition']['production_projection'] is None
    assert r['v0_disposition']['gap']['operation_kind'] == 'tile_orchestrate'
    assert r['mapping']['dataflows'] == {'dram_to_llb': 'J,K,I', 'llb_to_pe': 'K,I,J', 'pe_reference_only': 'I,J,K'}
    assert r['mapping']['microtile_shape'] == {'state':'fixed_reference','value':[3,3],'unit':'elements','domain':None}
    ids = [x['id'] for x in r['requirements']]
    assert len(ids) == len(set(ids))
    required_unknowns = {'dirty-output-visibility', 'tile-pointer-reuse', 'response-association',
                         'coherent-cpu-binding', 'numeric-correctness', 'evaluated-revision', 'zero-admission-fallback'}
    assert {x['id'] for x in r['requirements'] if x['verification'] == 'unknown'} == required_unknowns
    assert all(x['verification'] in {'required','unknown'} for x in r['requirements'])
    for x in r['parameters']:
        assert x['domain'] is None
        assert x['state'] in {'fixed_reference','unknown'}
        assert (x['value'] is None) == (x['state'] == 'unknown')
    assert {'ideal_LLB_partition_policy', 'oracle_static_distributor', 'oracle_SW_traffic',
            'universal_CPU_gather', 'coherent_memory_ABI', 'contained_PE_arithmetic',
            'verified_numeric_value_oracle'} <= set(r['exclusions'])
    return {'valid':True, 'records':1, 'claims':len(claims), 'required_unknowns':sorted(required_unknowns)}


def main():
    proposal = json.loads((HERE / 'proposal.json').read_text())
    provenance = json.loads((HERE / 'provenance.json').read_text())
    research = validate_research(proposal)
    # Corrupted references must actually fail, not just pass one well-formed input.
    malformed = deepcopy(proposal)
    malformed['records'][0]['stages'][0]['claim_refs'] = ['missing-claim']
    try:
        validate_research(malformed)
    except AssertionError:
        pass
    else:
        raise AssertionError('Dangling reference was accepted')
    source_checks = []
    for sid, entry in proposal['sources'].items():
        content = Path(entry['path']).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        assert digest == entry['sha256'] and len(content) == entry['bytes']
        source_checks.append({'id':sid,'sha256':digest,'bytes':len(content)})
        if sid == 'tactile-paper':
            assert content.startswith(b'%PDF-')
            info = subprocess.check_output(['pdfinfo', entry['path']], text=True)
            assert 'Pages:           15' in info
            title_page = subprocess.check_output(
                ['pdftotext', '-f', '1', '-l', '1', entry['path'], '-'], text=True)
            normalized = ' '.join(title_page.split())
            assert entry['title'] in normalized
            assert entry['doi'] in normalized and 'Volume 3' in normalized
            assert 'Toluwanimi O. Odemuyiwa' in normalized
            assert 'Christopher W. Fletcher' in normalized
    metadata = provenance['publisher_metadata']
    metadata_bytes = Path(metadata['path']).read_bytes()
    assert hashlib.sha256(metadata_bytes).hexdigest() == metadata['sha256']
    assert len(metadata_bytes) == metadata['bytes']
    message = json.loads(metadata_bytes)['message']
    assert message['title'] == [proposal['sources']['tactile-paper']['title']]
    assert message['DOI'] == '10.1145/3582016.3582064'
    assert message['page'] == '18-32'
    assert 'Volume 3' in message['container-title'][0]
    assert message['published']['date-parts'] == [[2023, 3, 25]]
    for entry in provenance['handoff_files']:
        assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest() == entry['sha256']
    assert provenance['sources'] == proposal['sources']
    assert provenance['new_download_bytes'] == 0
    assert provenance['new_download_bytes'] <= provenance['download_budget_bytes'] == 16 * 1024**2
    free_bytes = {str(p):shutil.disk_usage(p).free for p in (ROOT, Path('/tmp'))}
    assert all(n >= provenance['disk_floor_bytes'] == 16 * 1024**3 for n in free_bytes.values())

    path = ROOT / 'catalog/hardware-v0.1.yaml'
    before = path.read_bytes()
    assert before == subprocess.check_output(['git','show',BASE+':catalog/hardware-v0.1.yaml'],cwd=ROOT)
    existing, digest = load_catalog(path)
    frozen = deepcopy(existing)
    # Resolve proposal and existing source/claim registries together in memory,
    # without passing a research record to the production catalog loader.
    assert not (existing['sources'].keys() & proposal['sources'].keys())
    assert not (existing['claims'].keys() & proposal['claims'].keys())
    registry = {'sources':{**existing['sources'], **proposal['sources']},
                'claims':{**existing['claims'], **proposal['claims']}}
    assert all(set(c['source_refs']) <= registry['sources'].keys() for c in registry['claims'].values())
    assert set(proposal['records'][0]['claim_refs']) <= registry['claims'].keys()
    # No v0 projection exists: admission decision leaves the trial unchanged.
    trial = deepcopy(existing)
    assert proposal['records'][0]['v0_disposition']['production_projection'] is None
    assert trial == existing
    catalog_validation = validate_catalog(trial)
    try:
        validate_catalog(proposal)
    except RequestError as e:
        non_catalog_rejection = str(e)
    else:
        raise AssertionError('Research proposal unexpectedly accepted by v0')
    gap_trial = deepcopy(existing)
    gap_trial['designs'][0]['operations'][0]['operation'] = 'tile_orchestrate'
    try:
        validate_catalog(gap_trial)
    except RequestError as e:
        operation_gap_rejection = str(e)
    else:
        raise AssertionError('v0 unexpectedly supports tile_orchestrate')

    queries = []
    for operation, subtype in [('read','gather'), ('read','stream_load'), ('read','prefetch'),
                               ('write','scatter'), ('reduce','add'), ('read_modify_write','cas'),
                               ('read','drt_fixed_partition_tile_supply')]:
        for typed in ({}, {'payload_type':'float32','index_width_bits':32},
                      {'payload_type':'float64','index_width_bits':64}):
            q = dict(operation=operation,subtype=subtype,**typed)
            result = query_catalog(trial, **q)
            assert result == query_catalog(existing, **q)
            assert all(x['design_id'] != DESIGN for x in result['matches'] + result['excluded'])
            queries.append({'query':q,'unchanged':True,'proposal_matches':0,
                            'existing_matches':len(result['matches'])})
    unchanged_queries = 0
    for design in existing['designs']:
        for op in design['operations']:
            for typed in ({},{'payload_type':'float32','index_width_bits':32}):
                q = dict(operation=op['operation'],subtype=op['subtype'],design_id=design['id'],**typed)
                assert query_catalog(trial,**q) == query_catalog(existing,**q)
                unchanged_queries += 1
    assert existing == frozen == trial and path.read_bytes() == before
    report = {'format':'drt-proposal-validation-v1','base_commit':BASE,
              'research_validation':research,'catalog_validation':catalog_validation,
              'non_catalog_rejection':non_catalog_rejection,'operation_gap_rejection':operation_gap_rejection,
              'in_memory_source_claim_references':True,'dangling_reference_rejected':True,
              'source_checks':source_checks,'new_download_bytes':0,'free_bytes':free_bytes,
              'production_catalog_sha256':hashlib.sha256(before).hexdigest(),'loader_digest':digest,
              'query_exclusion':queries,'unchanged_existing_designs':len(existing['designs']),
              'unchanged_existing_query_trials':unchanged_queries,'all_existing_records_unchanged':True,
              'scope':'Research typing, byte provenance, references and deliberate non-admission only; no DRT build/run, numeric correctness or mapping legality certification.'}
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'valid':True,'proposal_queries':len(queries),'unchanged_existing_queries':unchanged_queries,'admitted_to_v0':False}))


if __name__ == '__main__':
    main()
