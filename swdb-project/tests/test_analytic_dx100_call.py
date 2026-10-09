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
