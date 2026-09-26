"""Native registered-CSR loading contracts. Created 2026-09-25 (Eastern Time)."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct

import pytest

from swdb import bfs_native, bfs_protocol
from swdb.cli import Failure
from swdb.store import Store
from test_bfs_protocol import _payload, _workload_request
from test_bfs_native import evaluation_setup, evaluate
from test_proposals import proposal_setup


def test_more_than_five_million_arcs_match_independent_streaming_parser(tmp_path):
    if not (shutil.which('c++') or shutil.which('g++')):
        pytest.skip('C++ compiler unavailable')
    # A complete bipartite graph crosses the old five-million-arc limit with a
    # 20 MiB fixture, without allocating millions of Python edge-pair objects.
    size = 1582
    n, count = 2*size, 2*size*size
    path = tmp_path/'bipartite.sg32'
    with path.open('wb') as out:
        out.write(struct.pack('<?ii', False, count, n))
        out.write(struct.pack('<'+'i'*(n+1), *(v*size for v in range(n+1))))
        right = struct.pack('<'+'i'*size, *range(size, n))
        left = struct.pack('<'+'i'*size, *range(size))
        for _ in range(size):
            out.write(right)
        for _ in range(size):
            out.write(left)
    rep = {'id': 'large-csr', 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
           'format': 'gapbs_sg32le', 'application': 'dx100-gapbs'}
    streamed, _ = bfs_protocol._representation(rep, bfs_protocol.NORMALIZATION,
        {'work_dir': str(tmp_path), 'compile_timeout_s': 30, 'timeout_s': 30})
    canonical, facts = bfs_protocol._representation(rep, bfs_protocol.NORMALIZATION, allow_streaming=False)
    assert count > 5_000_000
    assert facts['canonical_sha256'] == streamed['canonical_sha256']
    assert canonical['num_vertices'] == n
    assert sum(map(len, canonical['adjacency'])) == count


@pytest.mark.parametrize('width', [32, 64])
@pytest.mark.parametrize('directed', [True, False])
def test_registered_sg_materialization_uses_native_bounds_and_preserves_identity(records, tmp_path, monkeypatch, width, directed):
    records.copy_repo()
    graph = {'num_vertices': 6, 'directed': directed, 'edges': [[0, 1], [0, 2], [1, 3], [2, 3]]}
    request = _workload_request(records, tmp_path, graph)
    request['representations'] = [rep for rep in request['representations'] if rep['format'] == f'gapbs_sg{width}le']
    registered = records.swdb('register-workload', _payload(tmp_path, 'register', request), '--format', 'json')
    assert registered.returncode == 0, registered.stderr
    original = json.loads(registered.stdout)
    # Registration's streaming threshold may be smaller than the native limit.
    # A registered CSR between these limits must still load without edge pairs.
    monkeypatch.setattr(bfs_protocol, 'MAX_EDGES', 2)
    materialized = bfs_protocol.materialize_workload(Store(records.path), original['id'])
    assert 'edges' not in materialized['graph']
    canonical, facts = bfs_native.canonical_graph(materialized)
    assert canonical == bfs_native.canonical_graph({'graph': graph})[0]
    assert facts['canonical_sha256'] == original['definition']['canonical_sha256']
    assert materialized['registered_representation']['sha256'] == request['representations'][0]['sha256']
    assert canonical['adjacency'][5] == []
    monkeypatch.setattr(bfs_native, 'MAX_DIRECTED_EDGES', 3)
    with pytest.raises(Failure, match='native materialization limits'):
        bfs_protocol.materialize_workload(Store(records.path), original['id'])
    monkeypatch.setattr(bfs_native, 'MAX_DIRECTED_EDGES', 32_000_000)
    path = Path(request['representations'][0]['path'])
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(Failure, match='content hash differs'):
        bfs_protocol.materialize_workload(Store(records.path), original['id'])


@pytest.mark.parametrize('graph,reason', [
    ({'adjacency': [[1, 1], [0], []]}, 'sorted, distinct'),
    ({'adjacency': [[2, 1], [0], [0]]}, 'sorted, distinct'),
    ({'adjacency': [[0], [], []]}, 'self loops'),
    ({'adjacency': [[True], [0], []]}, 'integer'),
    ({'adjacency': [[3], [], []]}, 'supported limit'),
    ({'adjacency': [[1], [], []]}, 'symmetric'),
    ({'adjacency': [[1], [0]]}, 'one bounded row'),
    ({'adjacency': [[1], [0], []], 'edges': [[0, 1]]}, 'either edges or adjacency'),
])
def test_adjacency_input_is_strictly_verified(graph, reason):
    with pytest.raises(Failure, match=reason):
        bfs_native.canonical_graph({'graph': {'num_vertices': 3, 'directed': False, **graph}})


def test_json_graph_hash_and_parser_use_the_same_bounded_bytes(tmp_path, monkeypatch):
    path = tmp_path/'mutable-graph.json'
    first = {'num_vertices': 3, 'directed': True, 'edges': [[0, 1]]}
    changed = {'num_vertices': 3, 'directed': True, 'edges': [[0, 2]]}
    payload = json.dumps(first).encode()
    path.write_bytes(payload)
    expected = bfs_native.canonical_graph({'graph': first})[0]
    original_open = Path.open
    reads = 0

    def replace_between_reads(self, mode='r', *args, **kwargs):
        nonlocal reads
        if self == path and 'r' in mode:
            reads += 1
            if reads == 2:
                with original_open(path, 'w') as out:
                    out.write(json.dumps(changed))
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', replace_between_reads)
    actual, facts = bfs_native.canonical_graph({'graph_file': str(path),
        'graph_sha256': hashlib.sha256(payload).hexdigest()})
    assert actual == expected
    assert facts['representation']['sha256'] == hashlib.sha256(payload).hexdigest()


def test_public_evaluate_accepts_exact_adjacency_and_rejects_asymmetry(evaluation_setup):
    _, _, _, base = evaluation_setup
    workload = copy.deepcopy(base['workload'])
    original, facts = bfs_native.canonical_graph(workload)
    workload['graph'] = {'num_vertices': original['num_vertices'], 'directed': original['directed'],
                         'adjacency': original['adjacency']}
    workload['loaded_adjacency_sha256'] = facts['canonical_sha256']
    result, evaluation = evaluate(evaluation_setup, workload=workload)
    assert result.returncode == 0, result.stderr
    assert evaluation['correctness']['state'] == 'passed'
    assert evaluation['context']['workload']['canonical_sha256'] == facts['canonical_sha256']
    workload['graph']['directed'] = False
    result, rejected = evaluate(evaluation_setup, id='asymmetric-csr', workload=workload)
    assert result.returncode == 1
    assert rejected['outcome']['stage'] == 'workload_resolution'
    assert 'symmetric' in rejected['outcome']['reason']
    assert rejected['timing'] == []


def test_canonical_file_reload_preserves_exact_identity_and_checks_boundaries(tmp_path, monkeypatch):
    path = tmp_path/'graph.swdb'
    path.write_text('SWDBGRAPH1 4 4 0\n0 1\n1 0\n1 2\n2 1\n')
    graph, facts = bfs_native.read_canonical_graph(path)
    expected, expected_facts = bfs_native.canonical_graph({'graph': {'num_vertices': 4, 'directed': False,
                                                                   'edges': [[0, 1], [1, 2]]}})
    assert graph == expected
    assert facts['canonical_sha256'] == expected_facts['canonical_sha256']
    monkeypatch.setattr(bfs_native, 'MAX_GRAPH_BYTES', path.stat().st_size-1)
    with pytest.raises(Failure, match='512 MiB input limit'):
        bfs_native.read_canonical_graph(path)
    monkeypatch.setattr(bfs_native, 'MAX_GRAPH_BYTES', 512*1024*1024)
    monkeypatch.setattr(bfs_native, 'MAX_DIRECTED_EDGES', 3)
    with pytest.raises(Failure, match='supported limit'):
        bfs_native.read_canonical_graph(path)
    monkeypatch.setattr(bfs_native, 'MAX_DIRECTED_EDGES', 32_000_000)
    for content in ['SWDBGRAPH1 4 4 2\n', 'SWDBGRAPH1 4 1 0\n0 4\n',
                    'SWDBGRAPH1 4 2 0\n0 1\n', 'SWDBGRAPH1 4 0 0\n0 1\n',
                    'SWDBGRAPH1 4 2 0\n1 0\n0 1\n']:
        path.write_text(content)
        with pytest.raises(Failure):
            bfs_native.read_canonical_graph(path)
