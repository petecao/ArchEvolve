"""BC certification instance and the derived BC contract. Created: 2026-10-03 ET (ticket 42).

The candidate matrix and its pass rule are a kernel plug-in. BFS keeps its exact
functions; BC uses BCVerifier, the forward pass's per-level frontier sizes and an
accelerated-chunk witness. Strict-layer runs are finite functional evidence only.
"""

import importlib.util
import re
import shutil
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import kernels
from swdb.cli import Failure, UsageError
from swdb.kernels import bc
from swdb.library import Library
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]


def _result(stdout, returncode=0, stderr=''):
    return {'stdout': stdout, 'stderr': stderr, 'returncode': returncode, 'timeout': False}


def _snapshot_module():
    spec = importlib.util.spec_from_file_location('prepare_bc', ROOT / 'scripts/prepare_dx100_bc_scalar_snapshot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scalar():
    return _snapshot_module().scalar_source((ROOT / 'apps/dx100' / bc.BC_SOURCE).read_text())


def test_bfs_certification_plugin_keeps_its_exact_functions():
    plugin = kernels.BFS
    assert plugin.certification_source == c.BFS and plugin.certification_snapshot == c.DEFAULT_SNAPSHOT
    assert plugin.certification_controls is c._CONTROL_EXPECTED
    output = 'Starting TDStep: 1 elements\nSWDB trusted_frontier=1\nVerification: PASS\n'
    assert plugin.certification_judge(_result(output), [1]) == c.judge_bfs(_result(output), [1])
    assert plugin.control_source((3, 4)) == 3


def test_bc_pass_rule_needs_bcverifier_frontier_sizes_and_the_accelerated_chunk_witness():
    counts = [1, 64]
    output = ('Starting PBFS: 1 elements\nSWDB trusted_frontier=1\nStarting PBFS: 64 elements\n'
              'SWDB trusted_frontier=64\nSWDB accelerated_chunks=2\nVerification: PASS\n')
    assert bc.judge(_result(output), counts) == (True, 'all_checks_passed')
    assert bc.judge(_result(output.replace('PASS', 'FAIL')), counts) == (False, 'verifier')
    assert bc.judge(_result(output.replace('PBFS: 64', 'PBFS: 63')), counts) == (False, 'frontier_size_equality')
    assert bc.judge(_result(output.replace('trusted_frontier=64', 'trusted_frontier=65')), counts) == (False, 'frontier_size_equality')
    assert bc.judge(_result(output.replace('accelerated_chunks=2', 'accelerated_chunks=0')), counts) == (False, 'execution_witness')
    assert bc.judge(_result(output.replace('accelerated_chunks=2', 'accelerated_chunks=0')), counts, threshold=65)[0]
    # BFS's frontier print never satisfies BC's rule.
    assert bc.judge(_result(output.replace('PBFS', 'TDStep')), counts) == (False, 'frontier_size_equality')
    assert bc.judge(_result(output, 88, 'SWDB_PRESERVATION_FAIL:duplicate_frontier'), counts) == (False, 'frontier_size_equality')


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
    assert {row['id'] for row in contract['negative_controls']} == set(bc.CONTROLS)
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


def test_bc_frontier_oracle_refuses_a_vacuous_source(tmp_path):
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


def _gcc():
    try:
        return c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')


def test_bc_forward_pass_certifies_with_all_18_controls_rejected(tmp_path):
    """Ticket 62 (2026-10-04 ET): BC keeps certifying after controls moved to the library seam."""
    _gcc()
    _, tree = _bc_tree(tmp_path)
    before = c.artifacts.identify(tree)['sha256']
    matrix, controls = c.certify_bfs(tree, (ROOT / 'library').resolve(), tmp_path, (16384, 1024), 4, (0,),
                                     plugin=kernels.BC)
    assert c.artifacts.identify(tree)['sha256'] == before
    assert len(matrix) == 10 and all(x['status'] == 'passed' for x in matrix)
    assert len(controls) == 18, [(x['id'], x['status']) for x in controls]
    assert all(x['status'] == 'rejected' for x in controls), [(x['id'], x['tile_size'], x['status'], x['reason']) for x in controls]
    sites = {x['id']: x['fault']['site'] for x in controls}
    assert sites.pop('stale_depth_hint') == 'candidate_tokens' and set(sites.values()) == {'library_fault'}


def test_strict_bc_candidate_passes_and_the_bc_l1_control_is_rejected(tmp_path):
    _gcc()
    _, tree = _bc_tree(tmp_path)
    graph = tmp_path / 'two-level.sg'
    c.two_level_graph(graph)
    counts = bc.frontier_oracle(graph, 0)
    library = (ROOT / 'library').resolve()
    source = bc.instrument_source((tree / bc.BC_SOURCE).read_text())
    outcomes = {}
    for name in (None, 'stale_depth_hint'):
        (tree / bc.BC_SOURCE).write_text(source if name is None else bc.control(source, name))
        binary = tmp_path / f'bc-{name}'
        build = c.compile_cpp(tree / bc.BC_SOURCE, binary, library, tile_size=1024, threads=4, tree=tree)
        assert build['returncode'] == 0, build['stderr'][-2000:]
        run = c.execute([binary, '-f', graph, '-r', 0, '-n', '1', '-v'], tmp_path / f'{name}.json')
        outcomes[name] = (run['returncode'], bc.judge(run, counts), re.findall(r'accelerated_chunks=(\d+)', run['stdout']))
    assert outcomes[None][1] == (True, 'all_checks_passed') and int(outcomes[None][2][0]) > 0
    # Reading the stale DX100 hint loses path counts; BCVerifier fails with a clean exit.
    assert outcomes['stale_depth_hint'][0] == 0 and outcomes['stale_depth_hint'][1] == (False, 'verifier')
