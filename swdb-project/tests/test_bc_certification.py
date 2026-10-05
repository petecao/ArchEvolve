"""BC certification instance and the derived BC contract. Created: 2026-10-03 ET (ticket 42).
Updated: 2026-10-04 ET (ticket 70: certify 1.3 judges BC from the recorded scores and frontier windows).

The candidate matrix and its pass rule are a kernel plug-in. BFS keeps its exact
functions; BC uses BCVerifier, the forward pass's per-level frontier sizes and an
accelerated-chunk witness. Strict-layer runs are finite functional evidence only.
"""

import shutil
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import kernels
from swdb.cli import Failure, UsageError
from swdb.kernels import bc
from swdb.library import Library
from swdb.store import Store
from testkit.toolchain import load_script, require_gcc_openmp as _gcc

ROOT = Path(__file__).resolve().parents[1]


def _snapshot_module():
    module = load_script(ROOT / 'scripts/prepare_dx100_bc_scalar_snapshot.py', 'prepare_bc')
    return module


def _scalar():
    return _snapshot_module().scalar_source((ROOT / 'apps/dx100' / bc.BC_SOURCE).read_text())


def test_bfs_certification_plugin_keeps_its_exact_functions():
    plugin = kernels.BFS
    assert plugin.certification_source == c.BFS and plugin.certification_snapshot == c.DEFAULT_SNAPSHOT
    assert plugin.certification_controls is c._CONTROL_EXPECTED
    assert plugin.control_source((3, 4)) == 3
    # Ticket 70 (certify 1.3): each plug-in names its evaluator driver and out-of-process result check.
    assert plugin.certification_driver == 'dx100/certification/bfs_driver.inc' and plugin.certification_result_kind == 'i32'
    assert kernels.BC.certification_driver == 'dx100/certification/bc_driver.inc' and kernels.BC.certification_result_kind == 'f32'


def test_bc_result_check_is_bcverifiers_criterion_on_recorded_scores():
    """Ticket 70: BC's verifier verdict comes from the recorded scores, never from a printed PASS."""
    from swdb.bc_native import reference_scores
    adjacency = [[1, 2], [3], [3], []]
    reference, _ = reference_scores(adjacency, 0, 'float')
    assert kernels.BC.certification_check_result(adjacency, 0, reference)['passed']
    wrong = list(reference)
    wrong[3] += 0.5
    assert not kernels.BC.certification_check_result(adjacency, 0, wrong)['passed']
    assert not kernels.BC.certification_check_result(adjacency, 0, reference[:-1])['passed']


def test_bc_forward_pass_rewrite_replaces_only_the_scalar_pbfs():
    scalar = _scalar()
    source = bc.forward_pass_source(scalar)
    assert scalar.count('void PBFS(') == source.count('void PBFS(') == 1
    assert '#pragma omp for schedule(dynamic,1)' in source and '__dxc_accelerated_chunk();' in source
    assert '#include "swdb_dxc_lowering.hpp"' in source
    assert '__dxc_report();\n    return scores;' in source and '__dxc_session_begin();' in source
    assert source.count(bc.CPU_DEPTH) == 1  # BC-L1: the CPU rereads the depth after the CAS
    tail = scalar[scalar.index('\npvector<ScoreT> Brandes('):]
    assert 'bool BCVerifier(' in source and tail.split('bool BCVerifier(')[1] == source.split('bool BCVerifier(')[1]
    instrumented = bc.instrument_source(source)
    assert 'swdb_certification_frontier(queue);' in instrumented and '#include "MAA.hpp"' not in instrumented
    for name in bc.CONTROLS:
        assert bc.control(instrumented, name) != instrumented
    with pytest.raises(Failure):
        bc.instrument_source(source.replace(bc.FRONTIER_TEXT, 'std::cout << queue.size();'))


def test_derived_contract_cites_bfs_adds_bc_l1_and_is_shared():
    store = Store(ROOT / 'records')
    library = Library(ROOT / 'library', store)
    assert library.validate() == []
    contract = library.get('contract.bc_read_offload')
    parent = library.get('contract.bfs_read_offload')
    citation = contract['provenance']['derived_from']
    assert citation['id'] == parent['id'] and citation['content_sha256'] == library.content_sha256(parent['id'])
    assert contract['correctness_check']['kernel'] == 'gapbs-bc' and contract['correctness_check']['symbol'] == 'BCVerifier'
    clause = next(row for row in contract['clauses'] if row['id'] == 'BC-L1')
    assert clause['discharge_mode'] == 'differential_test' and clause['negative_control']['id'] == 'stale_depth_hint'
    # Every contract control runs; 2026-10-04 ET the plug-in adds the L4 part controls, which the
    # promoted contract does not list (its normative content is unchanged).
    l4_parts = {name for name, _ in kernels.BC.certification_clause_controls['L4']}
    assert {row['id'] for row in contract['negative_controls']} == set(bc.CONTROLS) - l4_parts
    assert {row['id'] for row in parent['clauses']} < {row['id'] for row in contract['clauses']}
    assert 'contract.bfs_read_offload' in {pin['id'] for pin in library.dependency_pins(contract['id'])}
    # Ticket 43 (2026-10-03 ET) promoted the derived contract; a later target evaluation may
    # raise its status (updated 2026-10-04 ET).
    state = library.state(contract['id'])
    assert state['tier'] == 'shared' and state['status'] in {'certified', 'evaluated_on_target'}
    assert library.state(parent['id']) == {'tier': 'shared', 'status': 'evaluated_on_target'}


@pytest.mark.parametrize('change, message', [
    (lambda bfs, bc_text: (bfs.replace('Continuation emits exactly', 'Continuation emits'), bc_text), 'cited contract content changed'),
    (lambda bfs, bc_text: (bfs, bc_text.replace('id: contract.bfs_read_offload', 'id: contract.missing')), 'cites another existing'),
    (lambda bfs, bc_text: (bfs, bc_text.replace('- id: L5\n', '- id: L5-renamed\n')), 'keeps every cited clause'),
])
def test_derived_contract_citation_is_checked(tmp_path, change, message):
    library_root = tmp_path / 'library'
    shutil.copytree(ROOT / 'library', library_root)
    bfs_path = library_root / 'rewrite_contracts/bfs_read_offload.yaml'
    bc_path = library_root / 'rewrite_contracts/bc_read_offload.yaml'
    bfs_text, bc_text = change(bfs_path.read_text(), bc_path.read_text())
    bfs_path.write_text(bfs_text)
    bc_path.write_text(bc_text)
    problems = Library(library_root, Store(ROOT / 'records')).validate()
    assert any(message in str(problem) and 'bc_read_offload' in str(problem) for problem in problems), problems


def test_bc_reference_frontier_counts_refuse_a_vacuous_source(tmp_path):
    graph = tmp_path / 'two-level.sg'
    c.two_level_graph(graph)
    assert bc.frontier_oracle(graph, 0) == [1, 4200, 17000]
    with pytest.raises(Failure, match='no outgoing edge'):
        bc.frontier_oracle(graph, 21216)


def _bc_tree(tmp_path):
    data = _snapshot_module().materialize(tmp_path / 'snapshot', ROOT / 'records')
    tree = Path(data['artifact']['path'])
    (tree / bc.BC_SOURCE).write_text(bc.forward_pass_source((tree / bc.BC_SOURCE).read_text()))
    shutil.copy(ROOT / 'library/dx100/dxc_lowering.hpp', tree / c.HEADER)
    return data, tree


def test_bc_candidate_scope_allows_only_bc_cc_and_the_lowering_header(tmp_path):
    data, tree = _bc_tree(tmp_path)
    assert c.check_candidate_scope(tree, data, kernels.BC) == sorted([bc.BC_SOURCE, c.HEADER])
    with pytest.raises(UsageError, match='BFS contract permits only the BFS rewrite'):
        c.check_candidate_scope(tree, data)  # the default BFS scope refuses a BC rewrite
    (tree / 'benchmarks/gapbs/src/bitmap.h').write_text('// changed\n')
    with pytest.raises(UsageError, match='changed files'):
        c.check_candidate_scope(tree, data, kernels.BC)


def test_bc_patch_matches_the_library_rewrite(tmp_path):
    patch = (ROOT / 'library/dx100/bc-forward-pass.patch').read_text()
    assert patch.startswith('--- a/' + bc.BC_SOURCE) and '+++ b/' + c.HEADER in patch
    added = {line[1:] for line in patch.splitlines() if line[:1] in '+ ' and not line.startswith('+++')}
    rewrite = (ROOT / 'library/dx100/bc_read_offload.inc').read_text().splitlines()
    assert set(rewrite) <= added  # the patch carries the library rewrite verbatim
    assert set((ROOT / 'library/dx100/dxc_lowering.hpp').read_text().splitlines()) <= added




def test_bc_forward_pass_certifies_with_every_control_rejected(tmp_path):
    """Ticket 62 (2026-10-04 ET): BC keeps certifying after controls moved to the library seam."""
    _gcc()
    _, tree = _bc_tree(tmp_path)
    before = c.artifacts.identify(tree)['sha256']
    matrix, controls = c.certify_bfs(tree, (ROOT / 'library').resolve(), tmp_path, (16384, 1024), 4, (0,),
                                     plugin=kernels.BC)
    assert c.artifacts.identify(tree)['sha256'] == before
    assert len(matrix) == 10 and all(x['status'] == 'passed' for x in matrix)
    assert len(controls) == 2 * len(bc.CONTROLS) == 24, [(x['id'], x['status']) for x in controls]
    assert all(x['status'] == 'rejected' for x in controls), [(x['id'], x['tile_size'], x['status'], x['reason']) for x in controls]
    sites = {x['id']: x['fault']['site'] for x in controls}
    token_sites = {name: sites.pop(name) for name in bc.TOKEN_CONTROLS}
    assert set(token_sites.values()) == {'candidate_tokens'} and set(sites.values()) == {'library_fault'}
    # 2026-10-04 ET: every run observed its clause's check (L4 parts: the verifier).
    assert all(x['observed_checks'] for x in controls)


def test_strict_bc_candidate_passes_and_the_bc_l1_control_is_rejected(tmp_path):
    """Ticket 70 (certify 1.3): built with the evaluator prelude and driver, judged from records."""
    from swdb import certification_isolation as isolation
    _gcc()
    _, tree = _bc_tree(tmp_path)
    graph = tmp_path / 'two-level.sg'
    c.two_level_graph(graph)
    counts = bc.frontier_oracle(graph, 0)
    library = (ROOT / 'library').resolve()
    driver = (library / kernels.BC.certification_driver).read_text()
    source = bc.instrument_source((tree / bc.BC_SOURCE).read_text())
    build = isolation.CandidateBuild(tmp_path / 'objects', library, tree, tree / bc.BC_SOURCE, 1024, 4)
    outcomes = {}
    for name in (None, 'stale_depth_hint'):
        text = (source if name is None else bc.control(source, name)) + driver
        candidate = build.candidate_object(text, name or 'positive')
        assert candidate['returncode'] == 0, candidate['stderr'][-2000:]
        binary = tmp_path / f'bc-{name}'
        assert build.link(candidate, None, binary)['returncode'] == 0
        run = isolation.run(binary, graph, 0, tmp_path / f'{name}.json', 4)
        verdict = c.judge_run(kernels.BC, run, graph, 0, counts)
        chunks = isolation.parse_records(run['record'], set())['chunks']
        outcomes[name] = (run['returncode'], (verdict['passed'], verdict['reason']), chunks)
    assert outcomes[None][1] == (True, 'all_checks_passed') and outcomes[None][2] > 0
    # Reading the stale DX100 hint loses path counts; the recorded scores fail with a clean exit.
    assert outcomes['stale_depth_hint'][0] == 0 and outcomes['stale_depth_hint'][1] == (False, 'verifier')
