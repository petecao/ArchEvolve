"""Executable DX100 call-shadow scope checks; no timing evidence. 2026-10-09 ET."""
import copy
import hashlib
import subprocess
from pathlib import Path

import pytest

from swdb import artifacts, analytic_dx100_call as shadow
from swdb.cli import Failure
from swdb.store import Store, Record
from testkit.bfs_protocol import _sg

GRAPH = {'num_vertices': 4, 'directed': False, 'edges': [[0, 1], [1, 2]]}
PROGRAM = r'''
using NodeID = int32_t;
template<class T> using pvector = std::vector<T>;
struct CLApp {
  int argc; char **argv; NodeID selected = -1;
  CLApp(int n, char **v, const char*): argc(n), argv(v) {}
  bool ParseArgs() {
    for (int i=1; i+1<argc; ++i)
      if (std::strcmp(argv[i], "-r")==0) selected=std::atoi(argv[++i]);
    return selected>=0;
  }
  NodeID start_vertex() const { return selected; }
  bool logging_en() const { return false; }
};
struct Graph { int64_t num_nodes() const { return 4; } };
struct Builder {
  Builder(CLApp&) {}
  Graph MakeGraph() { std::puts("fixture graph constructed"); return {}; }
};
pvector<NodeID> DOBFS(Graph &g, NodeID source, bool) {
  std::printf("fixture call source=%d\n", source);
  pvector<NodeID> parent(g.num_nodes(), -1);
  parent[source]=source;
  if (source==0) { parent[1]=0; parent[2]=1; }
#ifdef WRONG_PARENT
  parent[1]=-1;
#endif
  return parent;
}
int main() { return 99; }
'''
OBSERVER = r'''
#include <cstdio>
extern "C" void __swdb_begin() { std::puts("WINDOW begin"); }
extern "C" void __swdb_end() { std::puts("WINDOW end"); }
extern "C" void __swdb_source(unsigned long long source) {
  std::printf("WINDOW source=%llu\n", source);
}
'''


def registered(tmp_path, *, width=4, directive='', flags='-std=c++11 -DFUNC'):
    root = tmp_path / 'source'
    source = root / 'benchmarks/gapbs/src/bfs.cc'
    source.parent.mkdir(parents=True)
    source.write_text(directive + PROGRAM)
    (root / 'benchmarks/API').mkdir()
    context = {'application': 'dx100-gapbs', 'function': 'DOBFS',
        'code': [{'path': source.relative_to(root).as_posix()}],
        'build': {'flags': flags,
            'command': '{cxx} {flags} -I{app}/benchmarks/API -I{app}/benchmarks/gapbs/src {source} -o {binary}'}}
    candidate = {'id': 'fixture.shadow.candidate', 'kind': 'candidate',
        'source_snapshot': 'fixture.shadow.source', 'artifact': artifacts.identify(root),
        'protections': [], 'context': context}
    snapshot = {'id': candidate['source_snapshot'], 'kind': 'source_snapshot', 'context': context}
    graph = tmp_path / 'graph.sg'
    graph.write_bytes(_sg(GRAPH, width))
    from swdb.bfs_native import canonical_graph
    canonical, _ = canonical_graph({'graph': GRAPH, 'family': 'contract_fixture', 'generator': {'name': 'fixture'}})
    definition = {'family': 'contract_fixture', 'generator': {'name': 'fixture'},
        'canonical_sha256': artifacts.digest(canonical),
        'realized': {'num_vertices': 4, 'num_directed_edges': 4, 'directed': False},
        'representations': [{'id': 'fixture.sg', 'format': f'gapbs_sg{width*8}le',
            'application': 'dx100-gapbs', 'path': str(graph),
            'sha256': artifacts.file_hash(graph), 'canonical_sha256': artifacts.digest(canonical),
            'adjacency_verified': True}]}
    payload = {'requested_id': 'fixture.shadow.workload', 'version': 1, 'supersedes': None,
        'invalidated_comparisons': [], 'definition': definition}
    digest = artifacts.digest(payload)
    workload = {**payload, 'kind': 'workload', 'id': payload['requested_id']+'.'+digest[:16],
        'identity_sha256': digest}
    store = Store(tmp_path / 'records', indexed_records=[Record(x['id']+'.yaml', x)
        for x in (candidate, snapshot, workload)])
    return store, candidate, workload, source, graph


@pytest.mark.parametrize('selected', [0, 3])
@pytest.mark.parametrize('wrong', [False, True])
def test_compiled_window_uses_exact_source_and_keeps_original_graph_check_outside(tmp_path, cxx, selected, wrong):
    store, candidate, workload, source, graph = registered(tmp_path)
    plan = shadow.prepare(store, candidate, workload, source, selected)
    generated = tmp_path / 'counting.cc'
    generated.write_text(plan['driver'])
    observer = tmp_path / 'observer.cc'; observer.write_text(OBSERVER)
    binary = tmp_path / 'counted'
    flags = plan['flags'] + (['-DWRONG_PARENT'] if wrong else [])
    built = subprocess.run([cxx, *flags, str(generated), str(observer), '-o', str(binary)],
        capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(binary), *plan['run']], capture_output=True, text=True, timeout=5)
    assert run.returncode == (4 if wrong and selected==0 else 0), run.stdout+run.stderr
    assert run.stdout.count('WINDOW begin') == run.stdout.count('WINDOW end') == 1
    assert run.stdout.index('fixture graph constructed') < run.stdout.index('WINDOW begin')
    assert run.stdout.index('WINDOW begin') < run.stdout.index(f'WINDOW source={selected}')
    assert run.stdout.index(f'WINDOW source={selected}') < run.stdout.index(f'fixture call source={selected}')
    assert run.stdout.index(f'fixture call source={selected}') < run.stdout.index('WINDOW end')
    assert run.stdout.index('WINDOW end') < run.stdout.index('SWDB_BFS_PARENT_STORAGE') < run.stdout.index('Verification:')
    assert f'SWDB_BFS_RESULT source={selected} vertices=4 parent_count=4' in run.stdout
    # Malformed input is refused by the evaluator-owned reader before any call.
    graph.write_bytes(graph.read_bytes()[:-1])
    refused = subprocess.run([str(binary), *plan['run']], capture_output=True, text=True, timeout=5)
    assert refused.returncode == 5 and 'WINDOW begin' not in refused.stdout


def test_plan_binds_actual_sg_bytes_without_claiming_execution_or_mmio(tmp_path):
    store, candidate, workload, source, graph = registered(tmp_path)
    plan = shadow.prepare(store, candidate, workload, source, 3)
    scope = plan['scope']
    assert scope['graph_input']['sha256'] == hashlib.sha256(graph.read_bytes()).hexdigest()
    assert scope['candidate_record_sha256'] == artifacts.digest(candidate)
    assert scope['workload_record_sha256'] == artifacts.digest(workload)
    assert scope['run_arguments'] == ['-f', str(graph), '-r', '3']
    assert scope['counting_driver_sha256'] == hashlib.sha256(plan['driver'].encode()).hexdigest()
    assert plan['scope_sha256'] == artifacts.digest(scope)
    assert scope['execution_observed'] is scope['numeric_admission'] is scope['timer_values_used'] is False
    assert scope['mmio_correspondence'] == 'unknown'
    assert scope['environment']['SWDB_ROI_GATED'] == '1'
    graph.write_bytes(bytes([1])+graph.read_bytes()[1:])
    with pytest.raises(Failure, match='differs'):
        shadow.prepare(store, candidate, workload, source, 3)


def test_real_llvm_count_window_and_receipt_bind_exact_dx100_call(tmp_path, llvm22):
    store, candidate, workload, source, graph = registered(tmp_path)
    output = tmp_path / 'actual-counts'
    result = shadow.execute(store, candidate, workload, source, 0, output,
                            llvm_bin=llvm22, timeout_s=120)
    receipt, payload = result['receipt'], result['payload']
    assert receipt['execution_observed'] is True
    assert receipt['numeric_admission'] is receipt['timer_values_used'] is False
    assert receipt['mmio_correspondence'] == 'unknown'
    assert payload['sources'] == [0]
    assert receipt['counted_payload_sha256'] == artifacts.digest(payload)
    assert receipt['environment']['OMP_NUM_THREADS'] == '4'
    assert receipt['environment']['OMP_DYNAMIC'] == 'FALSE'
    assert receipt['llvm_version'].startswith('22.')
    assert receipt['toolchain_flags'][0] == '--no-default-config'
    if receipt['macos_sdk']:
        assert receipt['toolchain_flags'][1:] == ['-isysroot', receipt['macos_sdk']]
    assert receipt['build_environment'] == {'PATH': '/usr/bin:/bin', 'TMPDIR': str(output)}
    assert 'runtime_library_byte_continuity' in receipt['runtime_missing']
    assert receipt['pinned_inputs'][str(source)] == artifacts.file_hash(source)
    assert receipt['pinned_inputs'][str(graph)] == artifacts.file_hash(graph)
    for name, descriptor in receipt['artifacts'].items():
        assert descriptor['sha256'] == artifacts.file_hash(output / name)
        assert descriptor['bytes'] == (output / name).stat().st_size
    # Real counter events, rather than the print-only observer of earlier tests.
    import json
    raw = json.loads((output / 'counts.json').read_text())
    assert len(raw['trials']) == 1 and raw['trials'][0]['sources'] == [0]
    assert any(value > 0 for values in raw['trials'][0]['operations'].values() for value in values)
    # Inlining can attribute DOBFS instructions to main. The window, rather
    # than a debug-function label, determines which counters are active.
    assert any(row['operation_counts']['integer']['value'] > 0 for row in payload['regions'])
    assert 'fixture graph constructed' in (output / 'stdout.txt').read_text()
    assert 'WINDOW begin' not in (output / 'stdout.txt').read_text()
    saved = json.loads((output / 'receipt.json').read_text())
    assert saved == receipt
    identity = dict(receipt); identity.pop('identity_sha256')
    assert artifacts.digest(identity) == receipt['identity_sha256']


@pytest.mark.parametrize('change', ['none', 'extra', 'source', 'source-type', 'failed', 'vertices'])
def test_count_result_refuses_missing_changed_or_failed_window(change):
    from types import SimpleNamespace
    trials = [{'sources': [0]}]
    stdout = 'SWDB_BFS_RESULT source=0 vertices=4 parent_count=4 parent_fnv1a64=0123456789abcdef\nVerification: PASS\n'
    if change == 'none': trials = []
    if change == 'extra': trials *= 2
    if change == 'source': trials[0]['sources'] = [1]
    if change == 'source-type': trials[0]['sources'] = [False]
    if change == 'failed': stdout = stdout.replace('PASS', 'FAIL')
    if change == 'vertices': stdout = stdout.replace('vertices=4', 'vertices=5')
    observed = {'counts': {'trials': trials}, 'static': {'regions': []},
                'executed': SimpleNamespace(stdout=stdout)}
    with pytest.raises(Failure, match='counted source window|original-graph check failed'):
        shadow._counted_result(observed, {'source': 0, 'num_vertices': 4})


@pytest.mark.parametrize('variable,value', [('CPATH', '/tmp/headers'), ('LD_PRELOAD', '/tmp/observer'),
                                          ('SWDB_ROI_GATED', '0'), ('CCC_OVERRIDE_OPTIONS', '+-include /tmp/observer.h')])
def test_execute_refuses_ambient_substitution_before_build(tmp_path, monkeypatch, variable, value):
    store, candidate, workload, source, _ = registered(tmp_path)
    monkeypatch.setenv(variable, value)
    with pytest.raises(Failure, match='ambient'):
        shadow.execute(store, candidate, workload, source, 0, tmp_path / 'counted')
    assert not (tmp_path / 'counted').exists()


@pytest.mark.parametrize('selected', [-1, 4, True, '0'])
def test_source_is_exact_bounded_integer(tmp_path, selected):
    store, candidate, workload, source, _ = registered(tmp_path)
    with pytest.raises(Failure, match='source is outside'):
        shadow.prepare(store, candidate, workload, source, selected)


@pytest.mark.parametrize('fault', ['source', 'candidate', 'workload', 'scope-macro', 'sg64'])
def test_changed_identity_or_driver_substitution_refuses(tmp_path, fault):
    directive = '#define __swdb_begin() ((void)0)\n' if fault=='scope-macro' else ''
    store, candidate, workload, source, _ = registered(tmp_path, width=8 if fault=='sg64' else 4, directive=directive)
    candidate, workload = copy.deepcopy(candidate), copy.deepcopy(workload)
    if fault=='source': source.write_text(source.read_text()+'\n')
    if fault=='candidate': candidate['id'] += '.other'
    if fault=='workload': workload['definition']['generator']['name'] = 'other'
    with pytest.raises(Failure):
        shadow.prepare(store, candidate, workload, source, 0)


def test_changed_evaluator_boundary_is_not_best_effort(tmp_path, monkeypatch):
    from swdb import dx100_candidate
    original = dx100_candidate.driver
    monkeypatch.setattr(dx100_candidate, 'driver', lambda *a, **k:
        original(*a, **k).replace('  m5_reset_stats(0, 0);', '  m5_reset_stats(1, 0);'))
    with pytest.raises(Failure, match='boundary changed'):
        shadow.driver(tmp_path/'source.cc', 'DOBFS', sg_offset_bytes=4)


@pytest.mark.parametrize('extra', ['-D__swdb_begin=unmarked_begin', '-D __swdb_end=unmarked_end',
    '-U__swdb_source', '-U __swdb_source', '-include /tmp/unbound.hpp',
    '-imacros /tmp/unbound.hpp', '-DGEM5', '-UFUNC', '-DFUNC=0', '-Xclang -load /tmp/plugin.so'])
def test_registered_build_cannot_replace_markers_or_add_unbound_inputs(tmp_path, extra):
    store, candidate, workload, source, _ = registered(tmp_path, flags='-std=c++11 -DFUNC '+extra)
    with pytest.raises(Failure, match='build flags cannot substitute'):
        shadow.prepare(store, candidate, workload, source, 0)


@pytest.mark.parametrize('subject', ['workload', 'candidate'])
@pytest.mark.parametrize('converted', [float, bool])
def test_python_equal_type_confusion_does_not_change_the_bound_record(tmp_path, subject, converted):
    store, candidate, workload, source, _ = registered(tmp_path)
    original = copy.deepcopy(candidate if subject=='candidate' else workload)
    candidate, workload = copy.deepcopy(candidate), copy.deepcopy(workload)
    if subject=='candidate':
        candidate['artifact']['files'][0]['bytes'] = converted(candidate['artifact']['files'][0]['bytes'])
        changed = candidate
    else:
        workload['version'] = converted(workload['version'])
        changed = workload
    # Float substitutions, and bool for version=1, are equal in Python but
    # must not cause the plan to identify different canonical record bytes.
    if converted is float or subject=='workload': assert original == changed
    with pytest.raises(Failure, match='differs from its registered record'):
        shadow.prepare(store, candidate, workload, source, 0)


def _exact_candidate_and_target(tmp_path):
    """Narrow original record reads; only a selected counter reader needs this tree."""
    import shutil
    import yaml
    from conftest import REPO
    from swdb import certification
    from swdb.store import PLURAL
    records = tmp_path / 'records'
    rows = {}
    def load(kind, rid, *, copy_file=False):
        path = REPO / 'records' / PLURAL[kind] / (rid + '.yaml')
        data = yaml.safe_load(path.read_text())
        assert data['id'] == rid and data['kind'] == kind
        rows[rid] = Record(str(path), data)
        if copy_file:
            target = records / PLURAL[kind] / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        return data
    candidate = load('candidate', 'bfs-functional-read-offload-20261006-a1.proposal.candidate-1')
    load('source_snapshot', candidate['source_snapshot'])
    implementation = load('implementation', candidate['implementation'], copy_file=True)
    load('kernel', implementation['kernel'], copy_file=True)
    load('application', implementation['application'], copy_file=True)
    target = load('target_description', 'dx100-e4fc4af-functional-analytic-v1.t4')
    load('hardware_target', target['target'])
    for command in target['functional_observation']['commands']:
        load('intrinsic', command['intrinsic'])
        for rid in command['hardware_operations']:
            load('operation', rid)
    store = Store(records, indexed_records=list(rows.values()))
    tree, _ = certification.materialize_snapshot(store, candidate['source_snapshot'], tmp_path / 'selected-tree')
    source = tree / 'benchmarks/gapbs/src/bfs.cc'
    source.write_text(certification.peter_source(source.read_text()))
    shutil.copy2(REPO / 'library/dx100/dxc_lowering.hpp', source.parent / 'swdb_dxc_lowering.hpp')
    assert artifacts.identify(tree)['sha256'] == candidate['artifact']['sha256']
    # Small registered fixture input, never a LANL application timing/pair.
    # Retain candidate threshold/alpha unchanged: a 64-node frontier activates
    # read offload; an unreachable component keeps DOBFS in its push phase.
    edges = [[0, 1]] + [[1, i] for i in range(2, 66)]
    edges += [[i, j] for i in range(128, 256) for j in range(i+1, 256)]
    graph = {'num_vertices': 256, 'directed': False, 'edges': edges}
    path = tmp_path / 'path.sg'; path.write_bytes(_sg(graph, 4))
    from swdb.bfs_native import canonical_graph
    canonical, _ = canonical_graph({'graph': graph, 'family': 'contract_fixture', 'generator': {'name': 'fixture'}})
    digest = artifacts.digest(canonical)
    payload = {'requested_id': 'fixture.dx100.command.workload', 'version': 1, 'supersedes': None,
        'invalidated_comparisons': [], 'definition': {'family': 'contract_fixture', 'generator': {'name': 'fixture'},
            'canonical_sha256': digest, 'realized': {'num_vertices': 256, 'num_directed_edges': 2*len(edges), 'directed': False},
            'representations': [{'id': 'fixture.sg', 'format': 'gapbs_sg32le', 'application': 'dx100-gapbs',
                'path': str(path), 'sha256': artifacts.file_hash(path), 'canonical_sha256': digest, 'adjacency_verified': True}]}}
    identity = artifacts.digest(payload)
    workload = {**payload, 'kind': 'workload', 'id': payload['requested_id']+'.'+identity[:16], 'identity_sha256': identity}
    store.add(Record(workload['id']+'.yaml', workload))
    return store, candidate, workload, source, target


def test_exact_registered_candidate_observes_functional_commands_in_complete_call(tmp_path, llvm22):
    store, candidate, workload, source, target = _exact_candidate_and_target(tmp_path)
    result = shadow.execute(store, candidate, workload, source, 0, tmp_path / 'observed',
        llvm_bin=llvm22, timeout_s=120, target_description=target)
    receipt, payload = result['receipt'], result['payload']
    from swdb.estimate_protocol import estimator_identity
    assert receipt['swdb_implementation_sha256'] == estimator_identity()
    assert receipt['scope']['candidate_record_sha256'] == artifacts.digest(candidate)
    assert receipt['functional_observation_contract']['target_description_sha256'] == artifacts.digest(target)
    assert receipt['functional_observation_contract']['normative_bindings']['records']
    assert payload['semantic_commands']['complete'] is True
    calls = [call for row in payload['regions'] for call in row['accelerator_calls']
             if call['execution_count']['value']]
    assert {'dx100.functional.gather', 'dx100.functional.stream_load'} <= {call['event'] for call in calls}
    reads = [call for call in calls if call['event'] in {'dx100.functional.gather', 'dx100.functional.stream_load'}]
    assert reads and all(call['active_elements']['value'] == call['useful_accesses']['value'] > 0 for call in reads)
    assert sum(call['functional_bookkeeping']['accesses']['value'] for call in calls) > 0
    assert receipt['object_scopes'] is True
    assert receipt['execution_observed'] is True and receipt['numeric_admission'] is False
    assert receipt['mmio_correspondence'] == 'unknown'
    assert 'runtime_library_byte_continuity' in receipt['runtime_missing']
    assert {'functional-observation.json', 'commands.bc'} <= receipt['artifacts'].keys()
    assert candidate['state'] == 'unverified'


@pytest.mark.parametrize('fault', ['canonical-type', 'threads', 'normative-source'])
def test_target_binding_refuses_before_build(tmp_path, fault):
    store, candidate, workload, source, target = _exact_candidate_and_target(tmp_path)
    changed = copy.deepcopy(target)
    if fault == 'canonical-type': changed['threads'] = 4.0
    if fault == 'threads':
        changed['threads'] = 1
        store.by_id[changed['id']].data = changed
    if fault == 'normative-source':
        changed['functional_observation']['commands'][0]['aliases'][0]['source_sha256'] = '0'*64
        store.by_id[changed['id']].data = changed
    with pytest.raises(Failure, match='registered record|threads differ|source hash differs'):
        shadow.execute(store, candidate, workload, source, 0, tmp_path / 'refused', target_description=changed)
    assert not (tmp_path / 'refused').exists()


@pytest.mark.parametrize('directive', ['#undef FUNC', '#define GEM5', '#define GEM5_MAGIC',
    '#define FUNC 0', '#de\\\nfine GEM5', '# /* comment */ define GEM5', '%:undef FUNC', '%:define GEM5',
    '??=undef FUNC', '??=define GEM5', '??=de??/\nfine GEM5', '#undef FU\\ \nNC',
    '??=undef FU??/\t\nNC'])
def test_canonical_candidate_cannot_change_backend_after_initial_guard(tmp_path, directive):
    store, candidate, workload, source, _ = registered(tmp_path, directive=directive+'\n')
    # The builder recomputes artifact/record bytes: this is not an old-SHA refusal.
    with pytest.raises(Failure, match='changes the selected backend'):
        shadow.prepare(store, candidate, workload, source, 0)


@pytest.mark.parametrize('prefix', ['%:', '??='])
@pytest.mark.parametrize('name', ['__swdb_begin', '__swdb_end', '__swdb_source'])
def test_alternative_directive_cannot_replace_the_protected_counter(name, prefix, tmp_path):
    store, candidate, workload, source, _ = registered(tmp_path, directive=prefix+'define '+name+'(...) ((void)0)\n')
    with pytest.raises(Failure, match='protected driver identifier'):
        shadow.prepare(store, candidate, workload, source, 0)


@pytest.mark.parametrize('fault', ['site-missing', 'target-unknown', 'active-unknown'])
def test_command_summary_preserves_per_site_unknowns(monkeypatch, fault):
    from swdb import analytic
    from types import SimpleNamespace
    command = {'missing': ['functional_callee_count_coverage'] if fault=='site-missing' else [],
        'unknown_target': fault=='target-unknown'}
    region = {'accelerator_calls': [{'missing': command['missing'], 'active_elements':
        {'value': None if fault=='active-unknown' else 1}}], 'address_stream_counts': {}}
    monkeypatch.setattr(analytic, '_counted_regions', lambda *a, **k: ([region], []))
    observed = {'counts': {'trials': [{'sources': [0], 'semantic_commands': {'0:0': command}}]},
        'static': {'regions': [{}], 'semantic_sites': [{'descriptor': 0}]},
        'executed': SimpleNamespace(stdout='SWDB_BFS_RESULT source=0 vertices=4 parent_count=4 parent_fnv1a64=0123456789abcdef\nVerification: PASS\n')}
    result = shadow._counted_result(observed, {'source': 0, 'num_vertices': 4},
        {'functional_observation': {'commands': [{'event': 'fixture.read'}]}})
    assert result['semantic_commands']['complete'] is False
    assert result['semantic_commands']['missing'] == [{'site-missing': 'functional_callee_count_coverage',
        'target-unknown': 'semantic_target_object_identity', 'active-unknown': 'semantic_active_extent'}[fault]]


def test_changed_shared_implementation_refuses_final_count_receipt(tmp_path, llvm22, monkeypatch):
    from swdb import estimate_protocol
    original = estimate_protocol.estimator_identity()
    identities = iter([original, '0'*64])
    monkeypatch.setattr(estimate_protocol, 'estimator_identity', lambda: next(identities))
    store, candidate, workload, source, _ = registered(tmp_path)
    output = tmp_path / 'changed-bundle'
    with pytest.raises(Failure, match='changed during counting'):
        shadow.execute(store, candidate, workload, source, 0, output,
                       llvm_bin=llvm22, timeout_s=120)
    assert (output / 'counts.json').exists()
    assert not (output / 'receipt.json').exists()
