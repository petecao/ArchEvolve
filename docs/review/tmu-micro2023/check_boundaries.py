"""Independent retrieval/handoff boundary review; no executable TMU adapter."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from archevolve.__main__ import reference_context
from archevolve.comparison import build_comparison_artifacts, compare_designs
from archevolve.hardware_catalog import load_catalog, query_catalog, validate_catalog
from archevolve.intrinsic_handoff import build_handoff_artifacts, draft_intrinsics, validate_draft
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from tools.render_mermaid import RequestError

TARGET = '53a85a43a230dc74b4cf1b98ffcbbbfc7c70d89d'
COPY = 'fd0df20eeb10d369c363a512ded774f2d4f41620'
BASE = '6868383615c8aa89752923850d1bf0c170b6ba0b'
DESIGN = 'tmu-micro2023-fig8-spmv'
SUBTYPE = 'csr_spmv_two_lane_operand_event_supply'
HERE = Path(__file__).resolve().parent
PROPOSAL = ROOT / 'docs/proposals/tmu-micro2023'


def main():
    checks = []
    def checked(name, condition):
        assert condition, name
        checks.append(name)
    def blob(commit, path):
        return subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)
    hashes = {}
    for path in sorted(PROPOSAL.iterdir()):
        relative = str(path.relative_to(ROOT))
        contents = path.read_bytes()
        checked('exact target/root-copy bytes: ' + path.name,
                contents == blob(TARGET, relative) == blob(COPY, relative))
        hashes[relative] = hashlib.sha256(contents).hexdigest()
    production_path = 'catalog/hardware-v0.1.yaml'
    production_bytes = (ROOT / production_path).read_bytes()
    checked('production equals base and target',
            production_bytes == blob(BASE, production_path) == blob(TARGET, production_path))
    hashes[production_path] = hashlib.sha256(production_bytes).hexdigest()
    prior = json.loads((PROPOSAL / 'validation.json').read_text())
    checked('prior validation digests bound to unchanged bytes',
            prior['production_catalog_sha256'] == hashes[production_path]
            and prior['proposal_loader_digest'] == hashes['docs/proposals/tmu-micro2023/proposed-catalog.json'])
    catalog, _ = load_catalog(ROOT / production_path)
    proposal, _ = load_catalog(PROPOSAL / 'proposed-catalog.json')
    checked('standalone schema', validate_catalog(proposal)['valid'])
    for field in ('sources', 'claims'):
        catalog[field].update(deepcopy(proposal[field]))
    for field in ('designs', 'mechanism_families', 'decision_questions'):
        catalog[field].extend(deepcopy(proposal[field]))
    checked('trial schema', validate_catalog(catalog)['valid'])
    design = proposal['designs'][0]
    op = design['operations'][0]
    provenance = json.loads((PROPOSAL / 'provenance.json').read_text())
    pdf_hash = hashlib.sha256(Path(provenance['source']['pdf_path']).read_bytes()).hexdigest()
    checked('independent cached PDF identity', pdf_hash == provenance['source']['pdf_sha256']
            == 'd8ba773f792f0950abbb6cbd19a31f68619a3546813345b5c0a1d672dafc95e2')
    for payload, width in [('float32', 32), ('float64', 64)]:
        result = query_catalog(catalog, operation='read', subtype=SUBTYPE, design_id=DESIGN,
                               payload_type=payload, index_width_bits=width)['matches'][0]
        checked(f'typed exact mapping stays unknown: {payload}/{width}',
                result['status'] == 'needs_evidence'
                and result['missing_capability_evidence'] == ['payload_types', 'index_width_bits']
                and result['requirements'] == design['requirements'])
    for operation, subtype in [('write', 'scatter'), ('reduce', 'add'),
                               ('read_modify_write', 'add'), ('read_modify_write', 'cas')]:
        result = query_catalog(catalog, operation=operation, subtype=subtype, design_id=DESIGN)
        checked(f'mapping direction exclusion: {operation}/{subtype}',
                not result['matches'] and len(result['excluded']) == 1
                and result['excluded'][0]['status'] == 'excluded'
                and result['excluded'][0]['requirements'] == design['requirements'])
    for subtype in ('gather', 'stream_load'):
        result = query_catalog(catalog, operation='read', subtype=subtype)
        checked('unfiltered generic query excludes TMU: ' + subtype,
                not any(m['design_id'] == DESIGN for m in result['matches']))
    # Breadth-only inspection may return this mapping, but must retain its subtype.
    broad = query_catalog(catalog, operation='read', design_id=DESIGN)['matches'][0]
    checked('subtype omitted is inspection, not gather substitution',
            broad['status'] == 'mapping_reference' and broad['operation'] == op
            and broad['requirements'] == design['requirements'])

    case = load_normalized(ROOT / 'examples/received/bfs-sparse.features.v1.2.yaml', reference_context(ROOT))
    generic, trace = select_candidates(case, catalog, 'in-memory-review-trial', 'review-only', 16, [DESIGN])
    checked('normal focused generic selection cannot invent callback grammar',
            len(generic['candidates']) == 1 and generic['candidates'][0]['catalog_entry'] == 'cpu-baseline'
            and not any(m['design_id'] == DESIGN for q in trace['capability_queries'] for m in q['matches']))
    comparison = compare_designs(generic, catalog, [DESIGN])['designs'][0]
    checked('generic comparison is reference-only with interface and unknowns',
            comparison['interface'] == design['interface']
            and comparison['requirements'] == design['requirements']
            and not comparison['conditionally_matched_read_requests']
            and all(not q['matches'] for q in comparison['queries']))

    # Explicit synthetic adapter intent. It borrows request metadata solely to
    # exercise projection; BFS is not asserted to implement CSR SpMV callbacks.
    exact_request = deepcopy(generic['capability_requests'][0])
    exact_request.update(id='explicit-review-mapping', operation='read', subtype=SUBTYPE,
                         address_pattern='indirect', payload_type=None, index_width_bits=None,
                         require_old_value=False, purpose='read', mutable_target=False,
                         missing_workload_evidence=['workload_payload_type', 'workload_index_width'],
                         mapping_basis='Synthetic explicit TMU mapping intent; no BFS legality claim.')
    with patch('archevolve.evidence_select.capability_requests', return_value=([exact_request], [])):
        request, _ = select_candidates(case, catalog, 'in-memory-review-trial', 'review-only', 2, [DESIGN])
    candidate = request['candidates'][1]
    checked('explicit mapping candidate remains evidence-pending',
            candidate['candidate_scope'] == 'mapping_reference' and candidate['status'] == 'needs_evidence'
            and candidate['requirements'] == design['requirements']
            and candidate['requirement_status'] == 'not_discharged_by_retrieval'
            and candidate['operation_options'][0]['operation'] == op
            and candidate['software_handoff']['interface'] == design['interface'])
    checked('candidate operation claim closure retains exact located evidence',
            all(candidate['source_evidence']['claims'][ref] == proposal['claims'][ref]
                for ref in op['claim_refs'])
            and candidate['source_evidence']['sources'] == proposal['sources'])
    draft = draft_intrinsics(request, candidate)
    checked('draft preserves callbacks, result, CPU contract and unknowns',
            draft['operations'][0]['design_interface'] == design['interface']
            and draft['operations'][0]['postconditions']['catalog_result'] == op['result']
            and draft['requirements'] == design['requirements']
            and draft['operations'][0]['concrete_signature'] is None
            and not draft['readiness']['correctness_verified'])
    explicit_comparison = compare_designs(request, catalog, [DESIGN])['designs'][0]
    checked('explicit comparison retains mapping without executor promotion',
            explicit_comparison['queries'][0]['matches'][0]['status'] == 'mapping_reference'
            and explicit_comparison['queries'][0]['matches'][0]['operation'] == op
            and not explicit_comparison['conditionally_matched_read_requests']
            and explicit_comparison['source_evidence'] == candidate['source_evidence'])
    artifacts = build_handoff_artifacts(request, 'review-only')
    comparison_artifacts = build_comparison_artifacts(request, catalog, [DESIGN])
    checked('generated handoff and comparison retain event descriptions',
            any(yaml.safe_load(value)['operations'][0]['postconditions']['catalog_result'] == op['result']
                for key, value in artifacts.items() if key.endswith('intrinsic-draft.yaml'))
            and yaml.safe_load(comparison_artifacts['hardware-comparison.yaml'])['designs'][0]
            ['queries'][0]['matches'][0]['operation']['result'] == op['result'])
    for mutation in ('callback-result-loss', 'empty-row-requirement-loss', 'physical-order-invention'):
        bad = deepcopy(draft)
        if mutation == 'callback-result-loss':
            bad['operations'][0]['postconditions']['catalog_result']['form'] = 'loaded values'
        elif mutation == 'empty-row-requirement-loss':
            bad['requirements'] = [r for r in bad['requirements'] if r['id'] != 'boundaries']
        else:
            bad['operations'][0]['ordering']['description'] = 'Physical responses always arrive in stream order'
        try:
            validate_draft(bad, candidate)
        except RequestError:
            checked('reject semantic mutation: ' + mutation, True)
        else:
            raise AssertionError(mutation + ' accepted')
    checked('production still unchanged', (ROOT / production_path).read_bytes() == production_bytes)
    report = dict(format='tmu-independent-boundary-review-v1', verdict='PASS_source_scoped_mapping_reference',
                  target_commit=TARGET, root_copy_commit=COPY, base_commit=BASE, checks=checks,
                  input_sha256=hashes, reused_baseline_validation=str(PROPOSAL / 'validation.json'),
                  primary_pdf_sha256=pdf_hash,
                  prior_unchanged_query_trials=prior['unchanged_existing_query_trials'],
                  limitation='Synthetic explicit-request projection only; no adapter, event execution, runtime certification or performance evidence.')
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'valid': True, 'checks': len(checks), 'verdict': report['verdict']}))


if __name__ == '__main__':
    main()
