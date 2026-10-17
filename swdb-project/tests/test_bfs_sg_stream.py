"""Public artifact-size graph registration, including exact transpose checks.

Created 2026-09-25. Graphs are parser contract fixtures, not performance evidence.
"""

import hashlib
import json
import shutil
import struct
from pathlib import Path

import pytest

from testkit.bfs_protocol import NORMALIZATION, _hash, _payload, _workload_request


pytestmark = pytest.mark.skipif(not (shutil.which("c++") or shutil.which("g++")), reason="C++ parser compiler unavailable")


@pytest.mark.parametrize("directed", [True, False])
def test_streamed_adjacency_matches_json_and_both_real_offset_widths(records, tmp_path, directed):
    records.copy_repo()
    graph = {"num_vertices": 6, "directed": directed, "edges": [[0,1], [0,2], [1,3], [2,3]]}
    request = _workload_request(records, tmp_path, graph)
    request["parser"] = {"work_dir": str(tmp_path / "parser"), "timeout_s": 30}
    result = records.swdb("register-workload", _payload(tmp_path, "stream", request), "--format", "json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    reps = data["definition"]["representations"]
    assert len({row["canonical_sha256"] for row in reps}) == 1
    assert all(row["verification"]["method"] == "exact_mmap_csr_transpose_membership" for row in reps[1:])
    assert data["definition"]["realized"]["isolated_vertices"] == 2
    assert json.loads(records.swdb("get", data["id"], "--format", "json").stdout) == data


@pytest.mark.parametrize("fault", ["inverse", "unsorted", "truncated", "symmetry"])
def test_stream_parser_rejects_corrupt_loaded_adjacency(records, tmp_path, fault):
    records.copy_repo()
    before = {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")}
    graph = {"num_vertices": 5, "directed": fault != "symmetry", "edges": [[0,1], [0,2], [1,3], [2,3]]}
    request = _workload_request(records, tmp_path, graph)
    request["representations"] = [request["representations"][1]]
    request["parser"] = {"work_dir": str(tmp_path / "parser")}
    rep = request["representations"][0]
    path = Path(rep["path"])
    raw = bytearray(path.read_bytes())
    if fault == "truncated": raw = raw[:-4]
    elif fault == "unsorted": raw[33:41] = struct.pack("<ii", 2, 1)
    elif fault == "symmetry": raw[41:45] = struct.pack("<i", 2)
    else: raw[-4:] = struct.pack("<i", 0)
    path.write_bytes(raw)
    rep["sha256"] = _hash(path)
    result = records.swdb("register-workload", _payload(tmp_path, "bad-stream", request), "--format", "json")
    assert result.returncode == 1 and "SG" in result.stderr, result.stdout + result.stderr
    assert {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")} == before


def test_stream_registration_accepts_vertex_count_above_native_materialization_bound(records, tmp_path):
    records.copy_repo()
    n = 2_000_001
    path = tmp_path / "large-isolated.sg"
    with path.open("wb") as out:
        out.write(struct.pack("<?ii", True, 0, n))
        out.truncate(9 + 2*(n+1)*4)
    request = {"message_version": "1.0", "id": "large-sg", "kernel": "gapbs-bfs", "family": "contract_fixture",
               "generator": {"name": "isolated-vertices", "revision": "test-v1", "parameters": {"n": n}},
               "normalization": NORMALIZATION, "sources": [0, n-1],
               "parser": {"work_dir": str(tmp_path / "parser"), "timeout_s": 30},
               "representations": [{"id": "dx", "format": "gapbs_sg32le", "application": "dx100-gapbs",
                                    "path": str(path), "sha256": _hash(path)}]}
    result = records.swdb("register-workload", _payload(tmp_path, "large", request), "--format", "json")
    assert result.returncode == 0, result.stderr
    definition = json.loads(result.stdout)["definition"]
    assert definition["realized"] == {"num_vertices": n, "num_directed_edges": 0, "directed": True,
                                       "isolated_vertices": n, "minimum_out_degree": 0, "maximum_out_degree": 0}
    canonical = hashlib.sha256()
    canonical.update(b'{"adjacency":[')
    for vertex in range(n): canonical.update(b'[]' if vertex == 0 else b',[]')
    canonical.update(f'],"directed":true,"format":"swdb.bfs.adjacency.v1","num_vertices":{n}}}'.encode())
    assert definition["canonical_sha256"] == canonical.hexdigest()


def test_stream_parser_wall_budget_fails_without_registering(records, tmp_path):
    records.copy_repo()
    before = {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")}
    request = _workload_request(records, tmp_path, {"num_vertices": 5, "directed": True, "edges": [[0,1]]})
    request["representations"] = [request["representations"][1]]
    request["parser"] = {"work_dir": str(tmp_path / "parser"), "timeout_s": 0.000001}
    result = records.swdb("register-workload", _payload(tmp_path, "timeout", request), "--format", "json")
    assert result.returncode == 1 and "wall budget" in result.stderr
    assert {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")} == before
