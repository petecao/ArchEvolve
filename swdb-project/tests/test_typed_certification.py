"""Real strict-interface checks and fail-closed verdicts. Updated: 2026-10-03 ET."""
from pathlib import Path
import json
import shutil
import subprocess

import pytest
import yaml
from jsonschema import Draft202012Validator

from swdb import certification as c
from swdb.cli import Failure, UsageError
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'library'


@pytest.fixture(scope='module', params=[1024, 16384])
def strict_driver(request, tmp_path_factory):
    folder = tmp_path_factory.mktemp(f'strict-{request.param}')
    executable = folder / 'differential'
    build = c.compile_cpp(LIBRARY / 'dx100/drivers/differential.cc', executable,
                          LIBRARY, tile_size=request.param, threads=4)
    assert build['returncode'] == 0, build['stderr']
    return executable


@pytest.mark.parametrize('operation', [*c.OPERATIONS, 'store'])
def test_strict_matches_independent_reference_semantics(strict_driver, operation):
    run = subprocess.run([strict_driver, operation], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert f'SWDB_DIFFERENTIAL_PASS:{operation}' in run.stdout


CONTROLS = [(operation, name, check) for operation, controls in c.CONTROLS.items()
            for name, check in controls.items()]


@pytest.mark.parametrize('operation,control,expected', CONTROLS)
def test_controls_fail_a_named_runtime_check(strict_driver, operation, control, expected):
    process = subprocess.run([strict_driver, operation, control], capture_output=True, text=True)
    result = {'timeout': False, 'returncode': process.returncode,
              'stdout': process.stdout, 'stderr': process.stderr}
    assert c.rejection(result, expected) == ('rejected', expected)


@pytest.mark.parametrize('returncode,stderr,timeout,expected', [
    (-11, '', False, 'invalid'), (0, '', False, 'survived'),
    (86, 'SWDB_STRICT_ASSERT:other_check', False, 'invalid'),
    (86, 'SWDB_STRICT_ASSERT:memory_region', True, 'invalid'),
])
def test_crashes_wrong_checks_and_timeouts_never_reject_controls(returncode, stderr, timeout, expected):
    result = {'timeout': timeout, 'returncode': returncode, 'stdout': '', 'stderr': stderr}
    assert c.rejection(result, 'memory_region')[0] == expected


def test_independent_two_level_graph_has_required_frontier_and_depth(tmp_path):
    graph = tmp_path / 'two-level.sg'
    c.two_level_graph(graph)
    assert c.graph_oracle(graph, 0) == [1, 4200, 17000]
    assert c.graph_oracle(graph, 1) == [1, 17000]


def test_frontier_oracle_rejects_invalid_graph_before_traversal(tmp_path):
    graph = tmp_path / 'bad.sg'
    graph.write_bytes(b'\x01' + b'\0' * 8)
    with pytest.raises(Failure, match='invalid graph size'):
        c.graph_oracle(graph, 0)


def result(output, returncode=0, stderr=''):
    return {'stdout': output, 'stderr': stderr, 'returncode': returncode, 'timeout': False}


def test_bfs_requires_trusted_counts_and_execution_witness():
    counts = [1, 64, 12]
    output = ''.join(f'Starting TDStep: {n} elements\nSWDB trusted_frontier={n}\n' for n in counts)
    output += 'Verification: PASS\nSWDB accelerated_chunks=1\n'
    assert c.judge_bfs(result(output), counts) == (True, 'all_checks_passed')
    assert c.judge_bfs(result(output.replace('SWDB trusted_frontier=64', 'SWDB trusted_frontier=65')), counts) == (False, 'frontier_size_equality')
    assert c.judge_bfs(result(output.replace('accelerated_chunks=1', 'accelerated_chunks=0')), counts) == (False, 'execution_witness')
    assert c.judge_bfs(result(output.replace('Verification: PASS', 'Verification: FAIL')), counts) == (False, 'verifier')


def test_candidate_prints_cannot_hide_duplicate_enqueue():
    output = 'Starting TDStep: 1 elements\nVerification: PASS\nSWDB accelerated_chunks=1\n'
    rejected = c.judge_bfs(result(output, 88, 'SWDB_PRESERVATION_FAIL:duplicate_frontier'), [1])
    assert rejected == (False, 'frontier_size_equality')


def test_exact_patched_tree_preserves_vendored_identity_and_ships_header(tmp_path):
    store = Store(ROOT / 'records')
    before = c.artifacts.identify(ROOT / 'apps/dx100')
    patch = tmp_path / 'peter.patch'
    c.create_peter_patch(store, patch)
    trial = tmp_path / 'candidate';trial.mkdir()
    tree, snapshot = c.materialize_snapshot(store, c.DEFAULT_SNAPSHOT, trial)
    c.apply_patch(tree, patch)
    c.artifacts.check_protections(tree, snapshot['protections'])
    assert c.artifacts.file_hash(tree / c.HEADER) == c.artifacts.file_hash(LIBRARY / 'dx100/dxc_lowering.hpp')
    assert c.artifacts.identify(ROOT / 'apps/dx100') == before
    source = (tree / c.BFS).read_text()
    assert source.count('__dxc_session_begin();') == 1
    assert source.count('__dxc_accelerated_chunk();') == 1
    assert '__dxc_cas_probe(' in source
    assert '__dxc_report();' in source


def test_candidate_logging_is_protected_before_build():
    with pytest.raises(Failure, match='frontier logging'):
        c.instrument_source('bool BFSVerifier(){}')


def test_calibration_witness_threshold_is_from_scalar_oracle():
    counts = [1, 4200]
    output = ''.join(f'Starting TDStepMAA: {n} elements\nSWDB trusted_frontier={n}\n' for n in counts)
    output += 'Verification: PASS\nSWDB strict_operations=0\n'
    assert c.judge_bfs(result(output), counts, calibrate=True) == (False, 'execution_witness')


def test_forged_frontier_control_is_a_pure_library_fault():
    scalar = c.peter_source(Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)['regions'][0]['text'])
    instrumented = c.instrument_source(scalar)
    control = c._rewrite_control(instrumented, 'forged_frontier')
    # Ticket 62: the double enqueue is a library fault. Ticket 67: version 2 duplicates the first
    # queue push of the run. Ticket 70 (certify 1.3): no verdict is read from printed output, so the
    # protected print is no longer forged and the candidate text is unchanged.
    assert control['fault'] == 'SWDB_DXC_FAULT_FORGED_FRONTIER_V2' and control['version'] == 2
    assert control['source'] == instrumented and 'swdb_certification_frontier(queue);' in instrumented


def test_bfs_counter_reset_precedes_the_once_per_call_runtime_guard():
    snapshot = Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)
    source = c.peter_source(snapshot['regions'][0]['text'])
    assert source.index('swdb_dxc::chunks() = 0;') < source.index('swdb_acceleration_enabled = uint64_t')


def test_candidate_scope_cannot_certify_uncontracted_header_edits(tmp_path):
    store = Store(ROOT / 'records')
    patch = tmp_path / 'peter.patch'
    c.create_peter_patch(store, patch)
    trial = tmp_path / 'candidate'; trial.mkdir()
    tree, snapshot = c.materialize_snapshot(store, c.DEFAULT_SNAPSHOT, trial)
    c.apply_patch(tree, patch)
    assert c.check_candidate_scope(tree, snapshot) == sorted([c.BFS, c.HEADER])
    (tree / 'benchmarks/gapbs/src/pvector.h').write_text('// uncontracted rewrite\n')
    with pytest.raises(UsageError, match='permits only'):
        c.check_candidate_scope(tree, snapshot)


def candidate_claim_body():
    source = (LIBRARY / 'dx100/bfs_read_offload.inc').read_text()
    return source.split('for(unsigned k=0;k<count;++k){\n', 1)[1].split('\n     }\n', 1)[0]


def test_primary_claim_has_no_diagnostic_parent_read_or_degree_probe(tmp_path):
    """Check the compiled branch, including argument evaluation of a no-op probe."""
    source = tmp_path / 'claim.cc'
    source.write_text(candidate_claim_body())
    process = subprocess.run([c.compiler(), '-E', '-P', '-x', 'c++', source],
                             capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert '__atomic_load_n' not in process.stdout
    assert 'g.out_degree' not in process.stdout
    assert '__dxc_cas_probe' not in process.stdout
    assert 'hint<0&&compare_and_swap(parent[v],hint,u)' in process.stdout
    assert 'if(claimed){parent[v]=u;lqueue.push_back(v);}' in process.stdout


@pytest.fixture(scope='module')
def diagnostic_claim_driver(tmp_path_factory):
    folder = tmp_path_factory.mktemp('diagnostic-claim')
    source = folder / 'claim.cc'
    source.write_text('''#include <cstdlib>
#include <dxc_lowering.hpp>
using NodeID = int;
int cas_attempts=0;
bool compare_and_swap(int &slot,int expected,int desired){
 ++cas_attempts;return __atomic_compare_exchange_n(&slot,&expected,desired,false,__ATOMIC_RELAXED,__ATOMIC_RELAXED);
}
int main(int argc,char**argv){
 if(argc!=3)return 2;
 struct Graph{int calls=0;int out_degree(int){++calls;return 4;}}g;
 struct Queue{int pushes=0;void push_back(int){++pushes;}}lqueue;
 const int num_nodes=8,k=0;
 int vertices[]={0},frontier[]={2},hints[]={std::atoi(argv[1])};
 int parent[8]={std::atoi(argv[2])};
''' + candidate_claim_body() + '''
 std::printf("attempts=%d pushes=%d degree_calls=%d parent=%d races=%llu violations=%llu\\n",
  cas_attempts,lqueue.pushes,g.calls,parent[0],
  (unsigned long long)swdb_dxc::races().load(),(unsigned long long)swdb_dxc::violations().load());
}
''')
    executable = folder / 'claim'
    build = c.compile_cpp(source, executable, LIBRARY, tile_size=1024, threads=4,
                          defines=['-DSWDB_DXC_DIAGNOSTIC'])
    assert build['returncode'] == 0, build['stderr']
    return executable


@pytest.mark.parametrize('hint,fresh,attempts,pushes,races,violations', [
    (8, 0, 0, 0, 0, 1),       # Nonnegative hint outside the vertex-ID range.
    (1, -1, 0, 0, 0, 1),      # Nonnegative tile hint while the CPU still sees unvisited.
    (1, 1, 0, 0, 0, 0),
    (-4, -4, 1, 1, 0, 0),     # -outdegree initialization.
    (-1, -1, 1, 1, 0, 0),     # Permitted alternative -1 initialization.
    (-1, 2, 1, 0, 1, 0),      # A stale negative hint loses a race, with no enqueue.
    (-3, -3, 1, 1, 0, 1),     # Unexpected negative initialization.
])
def test_diagnostic_claim_checks_all_hints_without_changing_cpu_enqueue(
        diagnostic_claim_driver, hint, fresh, attempts, pushes, races, violations):
    process = subprocess.run([diagnostic_claim_driver, str(hint), str(fresh)],
                             capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert f'attempts={attempts} pushes={pushes} degree_calls=1 ' in process.stdout
    assert f'races={races} violations={violations}' in process.stdout


@pytest.fixture
def pinned_lowering(tmp_path):
    library = tmp_path / 'library'
    shutil.copytree(LIBRARY, library)
    entry_id = 'lowering.dxc_gather.dx100-mmio.1.0-e4fc4af'
    path = library / 'lowerings/dx100-mmio/1.0-e4fc4af/dxc_gather.yaml'
    entry = yaml.safe_load(path.read_text())
    entry['differential_test']['sha256'] = c.artifacts.file_hash(library / entry['differential_test']['path'])
    path.write_text(yaml.safe_dump(entry))
    return library, entry_id, path, entry


@pytest.mark.parametrize('use_override', [False, True])
def test_certification_compiles_the_pinned_header_and_current_build_defines(pinned_lowering, tmp_path, use_override):
    library, entry_id, path, entry = pinned_lowering
    canonical = library / 'dx100/dxc_lowering.hpp'
    original = canonical.read_text()
    pinned = library / 'dx100/other_lowering.hpp'
    old = 'maa_indirect_load<T>(base,index,dst);'
    # The canonical implementation remains good. The alternate pinned header
    # either always breaks gather, or breaks it only under its declared macro.
    mutation = ('\n#ifdef SWDB_TEST_BROKEN_GATHER\n return;\n#else\n' + old + '\n#endif\n'
                if use_override else 'return;')
    pinned.write_text(original.replace(old, mutation, 1))
    entry['location']['path'] = 'dx100/other_lowering.hpp'
    entry['code_sha256'] = c.artifacts.file_hash(pinned)
    if use_override:
        entry['build_defines']['defines'] = {'SWDB_TEST_BROKEN_GATHER': 1}
    path.write_text(yaml.safe_dump(entry))
    folder = tmp_path / 'runs'; folder.mkdir()
    matrix, _ = c.certify_lowering(entry_id, library, folder, (16384, 1024), 4)
    assert canonical.read_text() == original
    assert matrix and all(cell['status'] == 'failed' for cell in matrix)
    for cell in matrix:
        assert 'SWDB_DIFFERENTIAL_MISMATCH:reference_semantics' in cell['run']['stderr']
        assert '-DSWDB_DXC_LOWERING_HEADER="' + str(pinned) + '"' in cell['build']['command']
        if use_override:
            assert '-DSWDB_TEST_BROKEN_GATHER=1' in cell['build']['command']


def test_certification_compiles_the_actual_pinned_driver(pinned_lowering, tmp_path):
    library, entry_id, path, entry = pinned_lowering
    canonical = library / 'dx100/drivers/differential.cc'
    pinned = library / 'dx100/drivers/other.cc'
    pinned.write_text(canonical.read_text().replace('int main(int argc,char**argv){',
                      'int main(int argc,char**argv){std::cerr<<"SWDB_TEST_PINNED_DRIVER\\n";return 93;', 1))
    entry['differential_test']['path'] = 'dx100/drivers/other.cc'
    entry['differential_test']['sha256'] = c.artifacts.file_hash(pinned)
    path.write_text(yaml.safe_dump(entry))
    folder = tmp_path / 'runs'; folder.mkdir()
    matrix, controls = c.certify_lowering(entry_id, library, folder, (16384, 1024), 4)
    assert all(cell['status'] == 'failed' and cell['run']['returncode'] == 93 for cell in matrix)
    assert all(cell['status'] == 'invalid' for cell in controls)
    assert all(str(pinned) in cell['build']['command'] for cell in matrix)


@pytest.mark.parametrize('field,value', [('seeds', [19]), ('indices', ['tail']), ('long_rows', True),
                                         ('threads', 2), ('tile_sizes', [1024])])
def test_unsupported_pinned_input_sets_fail_usage_before_build(pinned_lowering, field, value):
    library, entry_id, path, entry = pinned_lowering
    entry['differential_test']['input_set'][field] = value
    path.write_text(yaml.safe_dump(entry))
    with pytest.raises(UsageError, match='input_set'):
        c.lowering_build(entry_id, library, (16384, 1024), 4)


@pytest.mark.parametrize('definitions', [
    {'strict': ['FUNC', 'GEM5'], 'tile_sizes': [16384, 1024], 'core_count': 4},
    {'strict': ['FUNC', 'GEM5', 'SWDB_STRICT', 'TILE_SIZE'], 'tile_sizes': [16384, 1024], 'core_count': 4},
    {'strict': ['FUNC', 'GEM5', 'SWDB_STRICT'], 'tile_sizes': [1024], 'core_count': 4},
    {'strict': ['FUNC', 'GEM5', 'SWDB_STRICT'], 'tile_sizes': [16384, 1024], 'core_count': 2},
    {'strict': ['FUNC', 'GEM5', 'SWDB_STRICT'], 'tile_sizes': [16384, 1024], 'core_count': 4, 'defines': {'SWDB_STRICT': 0}},
])
def test_unsupported_or_matrix_overriding_build_definitions_fail_usage(pinned_lowering, definitions):
    library, entry_id, path, entry = pinned_lowering
    entry['build_defines'] = definitions
    path.write_text(yaml.safe_dump(entry))
    with pytest.raises(UsageError):
        c.lowering_build(entry_id, library, (16384, 1024), 4)


def test_driver_cannot_ignore_the_pinned_lowering_include(pinned_lowering):
    library, entry_id, path, entry = pinned_lowering
    driver = library / entry['differential_test']['path']
    driver.write_text(driver.read_text().replace('#include SWDB_DXC_LOWERING_HEADER', '#include "dxc_lowering.hpp"', 1))
    entry['differential_test']['sha256'] = c.artifacts.file_hash(driver)
    path.write_text(yaml.safe_dump(entry))
    with pytest.raises(UsageError, match='include seams'):
        c.lowering_build(entry_id, library, (16384, 1024), 4)


def test_lowering_source_pins_must_stay_unchanged_during_build(pinned_lowering, tmp_path, monkeypatch):
    library, entry_id, _, entry = pinned_lowering
    header = library / entry['location']['path']
    def changed_source(*args, **kwargs):
        header.write_text(header.read_text() + '\n// Concurrent source change.\n')
        return {'returncode': 1, 'stderr': 'build failed', 'stdout': ''}
    monkeypatch.setattr(c, 'compile_cpp', changed_source)
    with pytest.raises(c.Failure, match='pinned source changed'):
        c.certify_lowering(entry_id, library, tmp_path, (16384, 1024), 4)


@pytest.mark.parametrize('wrong_reference', [False, True], ids=['equivalent_reference', 'changed_semantics'])
def test_real_lowering_receipt_binds_the_current_intrinsic_reference_identity(
        pinned_lowering, tmp_path, monkeypatch, wrong_reference):
    from swdb.library import Library
    library, entry_id, _, entry = pinned_lowering
    before = Library(library)
    lower_hash = before.content_sha256(entry_id)
    old_intrinsic_hash = before.content_sha256(entry['intrinsic'])
    path = library / 'intrinsics/dxc_gather.yaml'
    intrinsic = yaml.safe_load(path.read_text())
    alternate = library / 'dx100/alternate_reference.hpp'
    shutil.copyfile(library / intrinsic['reference_semantics']['path'], alternate)
    if wrong_reference:
        alternate.write_text(alternate.read_text().replace('out.push_back(base.at(i));', 'out.push_back(base.at(i)+1);', 1))
    intrinsic['reference_semantics']['path'] = 'dx100/alternate_reference.hpp'
    intrinsic['reference_semantics']['sha256'] = c.artifacts.file_hash(alternate)
    path.write_text(yaml.safe_dump(intrinsic))
    current = Library(library)
    intrinsic_hash = current.content_sha256(entry['intrinsic'])
    assert current.content_sha256(entry_id) == lower_hash
    assert intrinsic_hash != old_intrinsic_hash
    persisted = []
    monkeypatch.setattr(c.workflow, 'persist', lambda records, record, **kwargs: persisted.append(record))
    receipt = c.certify(Store(ROOT / 'records'), entry_id, library=library, runs_dir=tmp_path / 'runs')
    assert receipt['verdict'] == ('failed' if wrong_reference else 'certified')
    assert receipt['dependencies'] == [{'id': entry['intrinsic'], 'content_sha256': intrinsic_hash}]
    assert persisted == [receipt]
    assert all(cell['certification_inputs']['reference'] == str(alternate) for cell in receipt['matrix'])
    if wrong_reference:
        assert all(cell['status'] == 'failed' for cell in receipt['matrix'])
        assert all('SWDB_DIFFERENTIAL_MISMATCH:reference_semantics' in cell['run']['stderr'] for cell in receipt['matrix'])


def test_intrinsic_dependency_change_during_real_execution_aborts_receipt(pinned_lowering, tmp_path, monkeypatch):
    library, entry_id, _, _ = pinned_lowering
    path = library / 'intrinsics/dxc_gather.yaml'
    original_execute = c.execute
    changed = False
    def mutate_after_first_positive(command, log, **kwargs):
        nonlocal changed
        result = original_execute(command, log, **kwargs)
        if not changed and str(log).endswith('.positive.json'):
            intrinsic = yaml.safe_load(path.read_text())
            intrinsic['intent'] += ' Concurrent normative change during certification.'
            path.write_text(yaml.safe_dump(intrinsic))
            changed = True
        return result
    monkeypatch.setattr(c, 'execute', mutate_after_first_positive)
    persisted = []
    monkeypatch.setattr(c.workflow, 'persist', lambda records, record, **kwargs: persisted.append(record))
    with pytest.raises(c.Failure, match='dependencies changed during execution'):
        c.certify(Store(ROOT / 'records'), entry_id, library=library, runs_dir=tmp_path / 'runs')
    assert changed
    assert persisted == []
    assert not list((tmp_path / 'runs').rglob('certification.json'))


@pytest.mark.parametrize('dependencies,valid', [
    (None, True), ([], True), ([{'id': 'intrinsic.test', 'content_sha256': 'a' * 64}], True),
    ([{'id': 'intrinsic.test'}], False),
    ([{'id': 'intrinsic.test', 'content_sha256': 'stale'}], False),
    ([{'id': 'intrinsic.test', 'content_sha256': 'a' * 64, 'extra': True}], False),
    ([{'id': 'intrinsic.test', 'content_sha256': 'a' * 64}] * 2, False),
])
def test_dependency_receipt_schema_preserves_history_and_checks_pins(dependencies, valid):
    schema = json.loads((ROOT / 'schemas/certification.schema.json').read_text())
    record = {'kind': 'certification', 'entry': {'id': 'lowering.test', 'content_sha256': 'b' * 64},
              'command': {}, 'host': {}, 'matrix': [{'status': 'passed'}],
              'negative_controls': [{'status': 'rejected'}], 'verdict': 'certified', 'evidence_basis': 'simulated'}
    if dependencies is not None:
        record['dependencies'] = dependencies
    assert Draft202012Validator(schema).is_valid(record) == valid


@pytest.mark.parametrize('script', ['../tools/bfs_native/evil.py', 'tests/conftest.py',
                                    'scripts/bfs_native_pilot.py', '/etc/passwd'])
def test_snapshot_derivation_runs_only_a_checkout_preparation_script(tmp_path, script):
    """2026-10-04 ET (final code review): a record field names code that is executed."""
    from swdb.store import Record
    store = Store(ROOT / 'records')
    snapshot = json.loads(json.dumps(store.get(c.DEFAULT_SNAPSHOT, 'source_snapshot')))
    snapshot['context']['source_derivation']['script'] = script
    forged = Store(store.dir, indexed_records=[Record(snapshot['id'] + '.yaml', snapshot)])
    with pytest.raises(Failure, match='source derivation script'):
        c.materialize_snapshot(forged, c.DEFAULT_SNAPSHOT, tmp_path)
