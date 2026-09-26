#!/usr/bin/env python3
"""Fixed correctness-only graph for observed DX100 coverage. Created: 2026-09-26 ET.

Topology motivates the case; only a later actual trace can establish coverage.
This generator does not execute BFS, compile code, or measure performance.
"""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile
from swdb.store import Store

FRONTIER = 4097
SHARED = 16
SOURCE = 0
FIRST_LEAF = FRONTIER + 1
FIRST_SHARED = FIRST_LEAF + FRONTIER
ISOLATED = FIRST_SHARED + SHARED
VERTICES = ISOLATED + 1
ARCS = 2 * FRONTIER * (2 + SHARED)
AUTHOR_SOURCE_SHA256 = '6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465'
RUN_ROOTS = (Path('/data1/yanruj/EvolveSWDB_runs'), Path('/data/yanruj/EvolveSWDB_runs'))


def graph():
    """One wide level, private leaves, shared successor updates, and an isolate."""
    rows = [[] for _ in range(VERTICES)]

    def edge(a, b):
        rows[a].append(b)
        rows[b].append(a)

    for u in range(1, FRONTIER + 1):
        edge(SOURCE, u)
        edge(u, FIRST_LEAF + u - 1)
        for v in range(FIRST_SHARED, ISOLATED):
            edge(u, v)
    for row in rows:
        row.sort()
    return {'num_vertices': VERTICES, 'directed': False, 'adjacency': rows}


def generate(folder):
    """Create a fresh SG32 artifact and topology receipt, never overwrite one."""
    folder = Path(folder)
    folder.mkdir(exist_ok=False)
    data = graph()
    path = folder / 'coverage.sg'
    offsets = [0]
    for row in data['adjacency']:
        offsets.append(offsets[-1] + len(row))
    if offsets[-1] != ARCS:
        raise ValueError('fixed coverage graph arc count changed')
    with path.open('xb') as stream:
        stream.write(struct.pack('<Bii', 0, ARCS, VERTICES))
        stream.write(struct.pack('<' + 'i' * len(offsets), *offsets))
        for row in data['adjacency']:
            stream.write(struct.pack('<' + 'i' * len(row), *row))
    # Reopen through the shared parser to establish format and adjacency identity.
    loaded = bfs_protocol._sg_graph(path.read_bytes(), 4)
    if loaded != data:
        raise ValueError('serialized coverage graph differs from intended adjacency')
    receipt = {
        'created': '2026-09-26', 'purpose': 'finite structural correctness and observed path coverage',
        'generator': 'bfs_dx100_coverage_graph.v1', 'source': SOURCE,
        'vertices': VERTICES, 'directed_arcs': ARCS, 'undirected_edges': ARCS // 2,
        'frontier_vertices': FRONTIER, 'shared_successors': SHARED,
        'isolated_vertex': ISOLATED, 'format': 'gapbs_sg32le',
        'representation': {'path': str(path.resolve()), 'sha256': artifacts.file_hash(path),
                           'bytes': path.stat().st_size},
        'canonical_sha256': artifacts.digest(bfs_protocol._canonical(loaded)),
        'author_bfs_source_sha256': AUTHOR_SOURCE_SHA256,
        'basis': 'generated_topology', 'execution_performed': False,
        'accelerator_coverage_claim': False, 'gain_claim': False,
        'limit': 'Expected frontiers and tile sizes are not observed simulator coverage.',
    }
    (folder / 'graph.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--lane', required=True)
    args = parser.parse_args()
    if socket.gethostname().split('.')[0] != 'mbit10':
        parser.error('actual graph preparation requires the mbit10 socket lane')
    machine = Store(args.records).get('mbit10', 'machine')
    lane = profile._verified_lane(machine, args.lane)
    folder = args.output_directory.resolve()
    if not any(base in folder.parents for base in RUN_ROOTS):
        parser.error('graph output must use a fresh directory on an authorized host run volume')
    artifacts.external_directory(folder.parent)
    receipt = generate(folder)
    receipt['lane'] = lane
    (folder / 'graph.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
