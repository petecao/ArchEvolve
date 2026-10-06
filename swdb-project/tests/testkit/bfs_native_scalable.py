"""The native BFS verifier binary and synthetic graphs. Created 2026-10-05 ET (code
review T1), from tests/test_bfs_native_scalable.py."""

import random
import shutil
import subprocess
from collections import deque

import pytest

from conftest import REPO

COMPILER = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")


@pytest.fixture(scope="module")
def verifier(tmp_path_factory):
    binary = tmp_path_factory.mktemp("verifier") / "bfs-verify"
    built = subprocess.run([COMPILER, "-std=c++11", "-O2", "-Wall", "-Wextra",
                            str(REPO / "tools/bfs_native/bfs_verify.cc"), "-o", str(binary)],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    return binary


def _rows(graph):
    rows = [set() for _ in range(graph["num_vertices"])]
    for u, v in graph["edges"]:
        if u != v:
            rows[u].add(v)
            if not graph["directed"]:
                rows[v].add(u)
    return [sorted(row) for row in rows]


def _bfs(adjacency, source, reverse=False):
    parent = [-1] * len(adjacency)
    parent[source] = source
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in (reversed(adjacency[u]) if reverse else adjacency[u]):
            if parent[v] == -1:
                parent[v] = u
                queue.append(v)
    return parent


def _graphs():
    rng = random.Random(20261004)
    path = {"num_vertices": 6, "directed": False, "edges": [[i, i + 1] for i in range(5)]}
    star = {"num_vertices": 50, "directed": False, "edges": [[0, i] for i in range(1, 50)]}
    undirected = {"num_vertices": 200, "directed": False,
                  "edges": [[rng.randrange(200), rng.randrange(200)] for _ in range(700)]}
    directed = {"num_vertices": 150, "directed": True,
                "edges": [[rng.randrange(150), rng.randrange(150)] for _ in range(450)]}
    # Two components plus isolated vertices: unreachable vertices exist.
    split = {"num_vertices": 40, "directed": False,
             "edges": [[rng.randrange(15), rng.randrange(15)] for _ in range(40)]
             + [[15 + rng.randrange(15), 15 + rng.randrange(15)] for _ in range(40)]}
    return {"path": path, "star": star, "undirected": undirected, "directed": directed, "split": split}


FIXTURE_CANDIDATE = r'''
#include <cstdint>
#include <iostream>
#include <queue>
#include <vector>
using NodeID = int32_t;
template<class T> using pvector = std::vector<T>;
struct Graph {
  int64_t n; NodeID **idx; NodeID *neigh; NodeID **inv; NodeID *ineigh;
  Graph(int64_t n, NodeID **i, NodeID *e): n(n), idx(i), neigh(e), inv(nullptr), ineigh(nullptr) {}
  Graph(int64_t n, NodeID **i, NodeID *e, NodeID **ii, NodeID *ie): n(n), idx(i), neigh(e), inv(ii), ineigh(ie) {}
  ~Graph() { delete[] idx; delete[] neigh; delete[] inv; delete[] ineigh; }
  int64_t num_nodes() const { return n; }
};
pvector<NodeID> DOBFS(const Graph &g, NodeID source, bool) {
  pvector<NodeID> p(g.num_nodes(), -1); p[source] = source;
  std::queue<NodeID> q; q.push(source);
  while (!q.empty()) { NodeID u = q.front(); q.pop();
    for (NodeID *v = g.idx[u]; v != g.idx[u + 1]; ++v) if (p[*v] < 0) { p[*v] = u; q.push(*v); } }
#ifdef SWDB_BROKEN
  for (auto &x : p) if (x < 0) { x = source; break; }
#endif
  return p;
}
int main() { return 99; }
'''
PROGRAM_V2 = r'''#!/usr/bin/env python3
import json, os, struct, sys
from collections import deque
from pathlib import Path
mode = os.environ.get("SWDB_NATIVE_FIXTURE", "pass")
raw = Path(sys.argv[1]).read_bytes()
width, source = int(sys.argv[2]), int(sys.argv[3])
out, parents_file = Path(sys.argv[4]), Path(sys.argv[5])
f = "i" if width == 4 else "q"
m, n = struct.unpack_from("<" + f * 2, raw, 1)
base = 1 + 2 * width
offsets = struct.unpack_from("<" + f * (n + 1), raw, base)
targets = struct.unpack_from("<" + "i" * m, raw, base + (n + 1) * width)
parent = [-1] * n
parent[source] = source
q = deque([source])
while q:
    u = q.popleft()
    for v in targets[offsets[u]:offsets[u + 1]]:
        if parent[v] == -1:
            parent[v] = u
            q.append(v)
if mode == "unreachable_marked" and source == 0:
    parent[n - 1] = source
parents_file.write_bytes(struct.pack("<" + "i" * n, *parent))
out.write_text(json.dumps({"format": "swdb.bfs.native.trial.v2", "source": source,
    "configured_threads": int(os.environ["OMP_NUM_THREADS"]), "roi": "bfs.complete_call.v1",
    "duration_s": 0.025, "num_vertices": n, "parents_encoding": "int32le", "parents_bytes": 4 * n}))
'''
