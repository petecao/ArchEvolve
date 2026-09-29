"""Topology/format contracts, not simulated coverage. Created: 2026-09-26 ET."""
from collections import Counter, deque
import json

import pytest

from scripts import bfs_dx100_coverage_graph as case
from swdb import bfs_protocol


def test_fixed_graph_loads_exact_bfs_levels_and_exposes_full_tail_and_parent_choices(tmp_path):
    receipt = case.generate(tmp_path / 'fixture')
    raw = (tmp_path / 'fixture' / 'coverage.sg').read_bytes()
    graph = bfs_protocol._sg_graph(raw, 4)
    rows = graph['adjacency']
    depths = [-1] * graph['num_vertices']
    depths[0] = 0
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in rows[u]:
            if depths[v] < 0:
                depths[v] = depths[u] + 1
                queue.append(v)
    assert graph['num_vertices'] == 8212
    assert sum(map(len, rows)) == 147492
    assert Counter(depths) == {0: 1, 1: 4097, 2: 4113, -1: 1}
    assert depths[case.ISOLATED] == -1
    assert all(u in rows[v] for u, row in enumerate(rows) for v in row)
    # Four 1024-frontier chunks plus one scalar remainder follow the pinned
    # author's strict > NUM_CORES * 1024 threshold. Range output, not frontier
    # width, fills the 16384-element MAA tile: 1024 * 18 = 16384 + 2048.
    frontier = [u for u, depth in enumerate(depths) if depth == 1]
    assert 4 * 1024 < len(frontier) <= 4 * 2048
    assert {len(rows[u]) for u in frontier} == {18}
    assert divmod(1024 * 18, 16384) == (1, 2048)
    assert all(sum(depths[u] == 1 for u in rows[v]) == 4097
               for v in range(case.FIRST_SHARED, case.ISOLATED))
    assert receipt['basis'] == 'generated_topology'
    assert receipt['execution_performed'] is False
    assert receipt['accelerator_coverage_claim'] is False
    assert receipt['gain_claim'] is False
    assert json.loads((tmp_path / 'fixture' / 'graph.json').read_text()) == receipt


def test_graph_generation_never_overwrites_an_existing_attempt(tmp_path):
    folder = tmp_path / 'existing'
    folder.mkdir()
    marker = folder / 'graph.json'
    marker.write_text('prior failed attempt\n')
    with pytest.raises(FileExistsError):
        case.generate(folder)
    assert marker.read_text() == 'prior failed attempt\n'


def test_cli_creates_only_the_parent_before_fresh_generation(tmp_path, monkeypatch, capsys):
    class FixtureStore:
        def __init__(self, records):
            pass

        def get(self, record_id, kind):
            assert (record_id, kind) == ('mbit10', 'machine')
            return {'id': 'mbit10'}

    monkeypatch.setattr(case, 'Store', FixtureStore)
    monkeypatch.setattr(case.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(case.profile, '_verified_lane', lambda machine, lane: 'fixture-lane')
    monkeypatch.setattr(case, 'RUN_ROOTS', (tmp_path,))
    folder = tmp_path / 'parent' / 'fresh'
    monkeypatch.setattr(case.sys, 'argv', ['generator', '--output-directory', str(folder), '--lane', '0'])
    case.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['lane'] == 'fixture-lane'
    assert receipt['representation']['path'] == str(folder / 'coverage.sg')
    assert receipt['execution_performed'] is False
