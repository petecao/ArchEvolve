"""Compiled original-graph oracle regressions. Updated: 2026-09-26.

The local m5 stubs test C++ wrapper semantics, never simulator performance.
"""

from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from swdb import artifacts
from swdb.bfs_native import _protect_driver_macros, verify_parents
from swdb.dx100_candidate import driver
from test_bfs_protocol import _sg


ROOT = Path(__file__).resolve().parents[1]


def _body(text, name):
    start = text.index('{', text.index(name + '('))
    end, depth = start + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return start, end


def _real_source(tmp_path, body):
    source_root = tmp_path / 'candidate'
    shutil.copytree(ROOT / 'apps/gapbs', source_root)
    source = source_root / 'src/bfs.cc'
    original = source.read_text()
    start, end = _body(original, 'BFSVerifier')
    verifier = original[original.rfind('bool BFSVerifier', 0, start):end]
    if body is not None:
        start, end = _body(original, 'DOBFS')
        source.write_text(original[:start] + '{\n' + body + '\n}' + original[end:])
    guards = [{'path': 'src/bfs.cc', 'kind': 'verifier', 'text': verifier}]
    artifacts.check_protections(source_root, guards)
    return source_root, source


def _compile(tmp_path, source_root, source, *, width=8):
    compiler = shutil.which('clang++') or shutil.which('g++')
    if not compiler:
        pytest.skip('C++ compiler unavailable')
    model = tmp_path / 'model'
    header = model / 'include/gem5/m5ops.h'
    header.parent.mkdir(parents=True)
    header.write_text('#pragma once\n' + '\n'.join(
        f'inline void {name}(int,int) {{ std::puts("{name}"); }}'
        for name in ('m5_checkpoint', 'm5_work_begin', 'm5_work_end', 'm5_dump_stats', 'm5_reset_stats'))
        + '\ninline void m5_exit(int) { std::puts("m5_exit"); }\n')
    generated = tmp_path / 'driver.cc'
    # Default is the upstream SG64 representation. SG32 cases exercise the
    # same trusted parser against a source fixture with the loader width changed.
    arguments = {} if width == 8 else {'sg_offset_bytes': width}
    if width == 4:
        graph_header = source_root / 'src/graph.h'
        original = graph_header.read_text()
        assert 'typedef int64_t SGOffset;' in original
        graph_header.write_text(original.replace('typedef int64_t SGOffset;', 'typedef int32_t SGOffset;'))
    text = driver(source, model, 'DOBFS', **arguments)
    generated.write_text(text)
    _protect_driver_macros({'artifact': artifacts.identify(source_root)}, source_root, extra_text=text)
    binary = tmp_path / 'bfs'
    compiled = subprocess.run([compiler, '-std=c++11', '-Wno-unknown-pragmas', str(generated), '-o', str(binary)],
                              capture_output=True, text=True, timeout=60)
    assert compiled.returncode == 0, compiled.stderr
    return binary


def test_graph_mutation_cannot_redefine_original_correctness(tmp_path):
    root, source = _real_source(tmp_path, '''
  for (NodeID u = 0; u < g.num_nodes(); ++u)
    for (auto &v : g.out_neigh(u)) v = u;
  pvector<NodeID> parent(g.num_nodes(), -1);
  parent[source] = source;
  return parent;''')
    graph = tmp_path / 'original.sg'
    graph.write_bytes(_sg({'num_vertices': 3, 'directed': False, 'edges': [[0, 1], [1, 2]]}, 8))
    assert not verify_parents([[1], [0, 2], [1]], 0, [0, -1, -1])['passed']
    binary = _compile(tmp_path, root, source)
    result = subprocess.run([str(binary), '-f', str(graph), '-r', '0'], capture_output=True, text=True, timeout=5)
    assert result.returncode == 4, result.stdout + result.stderr
    assert 'Verification: FAIL' in result.stdout
    assert result.stdout.index('m5_exit') < result.stdout.index('Verification: FAIL')


@pytest.mark.parametrize('width', [4, 8])
@pytest.mark.parametrize('body,graph,source_id,passes', [
    (None, {'num_vertices': 5, 'directed': True, 'edges': [[0, 1], [0, 2], [1, 3], [2, 3], [3, 1]]}, 0, True),
    (None, {'num_vertices': 5, 'directed': False, 'edges': [[0, 1], [1, 2]]}, 4, True),
    ('''pvector<NodeID> parent(g.num_nodes(), -1);
        parent[0]=0; parent[1]=0; parent[2]=1;
        for (NodeID u=0; u<g.num_nodes(); ++u) for (auto &v:g.out_neigh(u)) v=u;
        return parent;''', {'num_vertices': 4, 'directed': False, 'edges': [[0, 1], [1, 2]]}, 0, True),
    # Every selected parent is a real edge, but 0->1->2 is not a shortest tree.
    ('''pvector<NodeID> parent(g.num_nodes(), -1); parent[0]=0; parent[1]=0; parent[2]=1; return parent;''',
     {'num_vertices': 3, 'directed': True, 'edges': [[0, 1], [0, 2], [1, 2]]}, 0, False),
    # Correct reachability/depth labels cannot excuse a nonexistent parent edge.
    ('''pvector<NodeID> parent(g.num_nodes(), -1); parent[0]=0; parent[1]=0; parent[2]=0; parent[3]=2; return parent;''',
     {'num_vertices': 4, 'directed': True, 'edges': [[0, 1], [0, 2], [1, 3]]}, 0, False),
])
def test_independent_oracle_accepts_valid_trees_and_rejects_wrong_structure(tmp_path, width, body, graph, source_id, passes):
    root, source = _real_source(tmp_path, body)
    binary = _compile(tmp_path, root, source, width=width)
    path = tmp_path / 'original.sg'
    path.write_bytes(_sg(graph, width))
    run = subprocess.run([str(binary), '-f', str(path), '-r', str(source_id)], capture_output=True, text=True, timeout=5)
    assert run.returncode == (0 if passes else 4), run.stdout + run.stderr
    assert ('Verification: PASS' in run.stdout) is passes
    assert f'SWDB_BFS_RESULT source={source_id} vertices={graph["num_vertices"]}' in run.stdout


@pytest.mark.parametrize('width', [4, 8])
def test_malformed_and_overbudget_serialized_inputs_fail_before_checkpoint(tmp_path, width):
    root, source = _real_source(tmp_path, None)
    binary = _compile(tmp_path, root, source, width=width)
    correct = _sg({'num_vertices': 3, 'directed': False, 'edges': [[0, 1], [1, 2]]}, width)
    integer = 'i' if width == 4 else 'q'
    first_offset = 1 + 2*width
    bad_offset = bytearray(correct)
    bad_offset[first_offset:first_offset+width] = struct.pack('<' + integer, 1)
    bad_neighbor = bytearray(correct)
    edge_start = first_offset + 4*width
    bad_neighbor[edge_start:edge_start+4] = struct.pack('<i', 3)
    cases = [correct[:-1], correct+b'X', b'\x02'+correct[1:], bad_offset, bad_neighbor,
             struct.pack('<B'+integer*2, 0, 0, 200_000_000),
             struct.pack('<B'+integer*2, 0, -1, 3)]
    for index, raw in enumerate(cases):
        path = tmp_path / f'malformed-{index}.sg'
        path.write_bytes(raw)
        run = subprocess.run([str(binary), '-f', str(path), '-r', '0'], capture_output=True, text=True, timeout=5)
        assert run.returncode == 5, run.stdout + run.stderr
        assert 'm5_checkpoint' not in run.stdout and 'Verification: PASS' not in run.stdout
        assert 'Trusted BFS evaluator:' in run.stderr
        if index == 5:
            assert '2 GiB' in run.stderr
