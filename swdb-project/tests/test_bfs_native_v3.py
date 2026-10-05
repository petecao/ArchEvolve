"""Native evaluator v3: parents are judged at full width (ticket 71). Created 2026-10-04 ET.

Differential tests of the v2 and v3 drivers on the same candidates. In-range parent vectors are
byte-identical. A wider out-of-range parent that v2 truncates into a valid one (the final code
review's P3, kept here as a regression witness) is rejected under v3 with exactly the verdict and
reason `verify_parents` gives the full-width vector. The end-to-end test runs `evaluate-pair` and
`compare-evaluations` under a v3 protocol with the CI-width gate (ticket 66); its candidate is an
external compiler contract fixture (fixture durations, never performance evidence).
"""

import copy
import gzip
import json
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from conftest import REPO, records as records_fixture
from test_bfs_native import evaluation_setup
from test_bfs_native_scalable import COMPILER, FIXTURE_CANDIDATE, PROGRAM_V2, _bfs, _graphs, _rows, verifier  # noqa: F401
from test_bfs_protocol import _command, _payload, _settings, _sg, _workload_request
from test_proposals import proposal_setup
from swdb import artifacts
from swdb import bfs_native_scalable as scalable
from swdb.bfs_native import verify_parents

pytestmark = pytest.mark.skipif(COMPILER is None, reason="C++ compiler unavailable")

V2, V3 = "tools/bfs_native/driver_scalable.cc.in", "tools/bfs_native/driver_scalable_v3.cc.in"

#: A candidate whose DOBFS returns SWDB_PARENT_T elements (default int64_t); the macros plant
#: wide values whose low 32 bits are a valid entry.
WIDE_CANDIDATE = r'''
#include <cstdint>
#include <queue>
#include <vector>
using NodeID = int32_t;
#ifndef SWDB_PARENT_T
#define SWDB_PARENT_T int64_t
#endif
struct Graph {
  int64_t n; NodeID **idx; NodeID *neigh; NodeID **inv; NodeID *ineigh;
  Graph(int64_t n, NodeID **i, NodeID *e): n(n), idx(i), neigh(e), inv(nullptr), ineigh(nullptr) {}
  Graph(int64_t n, NodeID **i, NodeID *e, NodeID **ii, NodeID *ie): n(n), idx(i), neigh(e), inv(ii), ineigh(ie) {}
  ~Graph() { delete[] idx; delete[] neigh; delete[] inv; delete[] ineigh; }
  int64_t num_nodes() const { return n; }
};
std::vector<SWDB_PARENT_T> DOBFS(const Graph &g, NodeID source, bool) {
  std::vector<int64_t> p(g.num_nodes(), -1); p[source] = source;
  std::queue<NodeID> q; q.push(source);
  while (!q.empty()) { NodeID u = q.front(); q.pop();
    for (NodeID *v = g.idx[u]; v != g.idx[u + 1]; ++v) if (p[*v] < 0) { p[*v] = u; q.push(*v); } }
#ifdef SWDB_ALIAS_HIGH
  for (int64_t v = 0; v < g.num_nodes(); ++v) if (v != source && p[v] >= 0) { p[v] += int64_t(1) << 32; break; }
#endif
#ifdef SWDB_ALIAS_LOW
  for (int64_t v = 0; v < g.num_nodes(); ++v) if (p[v] < 0) { p[v] -= int64_t(1) << 32; break; }
#endif
  std::vector<SWDB_PARENT_T> out(p.size());
  for (size_t i = 0; i < p.size(); ++i) out[i] = static_cast<SWDB_PARENT_T>(p[i]);
  return out;
}
int main() { return 99; }
'''


def _build(tmp_path, template, source, flags=(), name="driver"):
    wrapper = tmp_path / f"{name}.cc"
    text = (REPO / template).read_text()
    wrapper.write_text(text.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
    binary = tmp_path / name
    return binary, subprocess.run([COMPILER, "-std=c++11", "-O2", *flags, str(wrapper), "-o", str(binary)],
                                  capture_output=True, text=True)


def _run(binary, sg, width, source, tmp_path):
    record, parents = tmp_path / f"{binary.name}.json", tmp_path / f"{binary.name}.i32"
    done = subprocess.run([str(binary), str(sg), str(width), str(source), str(record), str(parents)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return json.loads(record.read_text()), parents


def _verdict(verifier, sg, width, source, parents):
    done = subprocess.run([str(verifier), str(sg), str(width), str(source), str(parents)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def _full_width(adjacency, source, mutation, element_bits=64, signed=True):
    """The vector DOBFS returns, at its own full width, as Python integers."""
    parents = _bfs(adjacency, source)
    if mutation == "alias_high":
        v = next(v for v in range(len(parents)) if v != source and parents[v] >= 0)
        parents[v] += 1 << 32
    elif mutation == "alias_low":
        v = next(v for v in range(len(parents)) if parents[v] < 0)
        parents[v] -= 1 << 32
    if not signed:
        parents = [p % (1 << element_bits) for p in parents]
    return parents


def test_v3_writes_the_same_bytes_as_v2_for_every_in_range_vector(verifier, tmp_path):
    source_file = tmp_path / "fixture.cc"
    source_file.write_text(FIXTURE_CANDIDATE)
    v2, built = _build(tmp_path, V2, source_file, name="v2")
    assert built.returncode == 0, built.stderr[-2000:]
    v3, built = _build(tmp_path, V3, source_file, name="v3")
    assert built.returncode == 0, built.stderr[-2000:]
    for name in ("split", "directed", "undirected"):
        graph = _graphs()[name]
        for width in (4, 8):
            sg = tmp_path / f"{name}{width}.sg"
            sg.write_bytes(_sg(graph, width))
            for source in (0, 3):
                old, old_parents = _run(v2, sg, width, source, tmp_path)
                new, new_parents = _run(v3, sg, width, source, tmp_path)
                assert old_parents.read_bytes() == new_parents.read_bytes()
                assert old["format"] == "swdb.bfs.native.trial.v2" and new["format"] == "swdb.bfs.native.trial.v3"
                assert new["parents_saturated"] == 0
                assert {k: v for k, v in new.items() if k not in ("format", "parents_saturated", "duration_s")} == \
                       {k: v for k, v in old.items() if k not in ("format", "duration_s")}
                assert scalable.check_trial_record(new, source, 1, "bfs.complete_call.v1", graph["num_vertices"],
                                                   scalable.EVALUATOR_V3) is None
                assert scalable.check_trial_record(new, source, 1, "bfs.complete_call.v1", graph["num_vertices"],
                                                   scalable.EVALUATOR_V2) is not None


@pytest.mark.parametrize("case, flags, bits, signed", [
    ("alias_high", ["-DSWDB_ALIAS_HIGH"], 64, True),       # valid parent + 2^32 truncates to the valid parent
    ("alias_low", ["-DSWDB_ALIAS_LOW"], 64, True),         # -1 - 2^32 truncates to the "unreached" -1
    ("unsigned_unreached", ["-DSWDB_PARENT_T=uint32_t"], 32, False),   # UINT32_MAX truncates to -1
    ("unsigned64_alias", ["-DSWDB_PARENT_T=uint64_t", "-DSWDB_ALIAS_HIGH"], 64, False),
])
def test_wide_out_of_range_parents_pass_v2_but_get_the_full_width_verdict_under_v3(verifier, tmp_path, case, flags,
                                                                                     bits, signed):
    source_file = tmp_path / "wide.cc"
    source_file.write_text(WIDE_CANDIDATE)
    v2, built = _build(tmp_path, V2, source_file, flags, name="v2")
    assert built.returncode == 0, built.stderr[-2000:]
    v3, built = _build(tmp_path, V3, source_file, flags, name="v3")
    assert built.returncode == 0, built.stderr[-2000:]
    graph = _graphs()["split"]                              # has unreachable vertices
    adjacency = _rows(graph)
    sg = tmp_path / "split.sg"
    sg.write_bytes(_sg(graph, 8))
    source = 0
    mutation = "alias_high" if "-DSWDB_ALIAS_HIGH" in flags else "alias_low" if "-DSWDB_ALIAS_LOW" in flags else None
    full = _full_width(adjacency, source, mutation, bits, signed)
    expected = verify_parents(adjacency, source, full)
    assert expected["passed"] is False and expected["reason"].endswith("is not an integer in [-1, n)")
    _, old_parents = _run(v2, sg, 8, source, tmp_path)
    assert _verdict(verifier, sg, 8, source, old_parents)["passed"] is True       # the review's P3, witnessed
    record, new_parents = _run(v3, sg, 8, source, tmp_path)
    assert _verdict(verifier, sg, 8, source, new_parents) == expected             # full-width verdict and reason
    saturated = sum(1 for p in full if not -2 ** 31 <= p < 2 ** 31)
    assert record["parents_saturated"] == saturated >= 1


@pytest.mark.parametrize("element", ["double", "float"])
def test_v3_refuses_to_build_a_non_integral_parent_element_type(tmp_path, element):
    source_file = tmp_path / "wide.cc"
    source_file.write_text(WIDE_CANDIDATE)
    _, built = _build(tmp_path, V2, source_file, [f"-DSWDB_PARENT_T={element}"], name="v2")
    assert built.returncode == 0                       # v2 silently narrows a floating vector
    _, built = _build(tmp_path, V3, source_file, [f"-DSWDB_PARENT_T={element}"], name="v3")
    assert built.returncode != 0 and "integral parent element type" in built.stderr


def test_v2_identity_is_unchanged():
    """v3 is a new file; the v2 template and trial format stay as frozen protocols pin them."""
    assert scalable.DRIVERS[scalable.EVALUATOR_V2] == REPO / V2
    assert scalable.TRIAL_FORMATS[scalable.EVALUATOR_V2] == "swdb.bfs.native.trial.v2"
    assert "static_cast<uint32_t>(static_cast<int32_t>(parent[i]))" in (REPO / V2).read_text()


# --- public evaluator path under v3 and the CI-width gate ---------------------------------------

PROGRAM_V3 = PROGRAM_V2.replace('"format": "swdb.bfs.native.trial.v2"', '"format": "swdb.bfs.native.trial.v3"').replace(
    '"parents_bytes": 4 * n}', '"parents_bytes": 4 * n, "parents_saturated": 0}')


@pytest.fixture(scope="module")
def v3_seed(tmp_path_factory):
    assert PROGRAM_V3 != PROGRAM_V2 and "parents_saturated" in PROGRAM_V3
    tmp = tmp_path_factory.mktemp("v3-seed")
    records = records_fixture.__wrapped__(tmp)
    setup = evaluation_setup.__wrapped__(proposal_setup.__wrapped__(records, tmp), tmp)
    _, runs, _, base = setup
    compiler = Path(base["build"]["compiler"])
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({PROGRAM_V3!r}); p.chmod(0o755)\n")
    workload = _command(records, "register-workload", _payload(tmp, "workload",
                        _workload_request(records, tmp, base["workload"]["graph"])))
    result = records.swdb("baseline-candidate", "test-source", "--id", "v3-source-baseline",
                         "--runs-dir", runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    baseline = json.loads(result.stdout)["id"]
    settings = _settings(base, workload)
    settings["evaluator"] = scalable.EVALUATOR_V3
    settings["correctness"]["verifier"] = scalable.VERIFIER_V2
    template = artifacts.file_hash(REPO / V3)
    settings["instrumentation"] = {role: {"template_sha256": template, "treatment": "included"}
                                   for role in ("baseline", "candidate")}
    collection = {"method": "native_paired.v1", "order_seed": 20260926}
    settings["sampling"].update(collection=collection, analysis="paired_repetition_circular_block_bootstrap.v1",
                                block_length=2, repetitions=6)
    settings["profitability"].pop("maximum_relative_spread", None)
    settings["profitability"].update(minimum_speedup=1.05, bootstrap_seed=20260925,
                                     gate={"statistic": "relative_ci_width.v1", "maximum": 0.05})
    frozen = _command(records, "freeze-protocol", _payload(tmp, "policy", {
        "message_version": "1.0", "id": "v3-policy", "version": 1, "settings": settings}))
    request = {"message_version": "1.0", "id": "v3-pair", "collection": collection, "budget": {"total_seconds": 600}}
    for role in ("baseline", "candidate"):
        request[role] = {**copy.deepcopy(base), "id": "v3." + role,
            "candidate": baseline if role == "baseline" else base["candidate"], "protocol_role": role,
            "protocol": frozen["id"], "workload": {"id": workload["id"]},
            "sources": workload["definition"]["sources"], "repetitions": 6,
            "budget": {"build_seconds": 120, "run_seconds": 30, "total_seconds": 600}}
    pair = records.swdb("evaluate-pair", _payload(tmp, "pair", request), "--runs-dir", runs, "--format", "json")
    assert pair.returncode == 0, pair.stdout + pair.stderr
    pair = json.loads(pair.stdout)
    comparison = {"message_version": "1.0", "id": "v3-comparison", "protocol": frozen["id"],
                  "baseline_evaluation": pair["baseline_evaluation"], "candidate_evaluation": pair["candidate_evaluation"],
                  "comparison_baseline": "gapbs-bfs-do"}
    return records, runs, request, pair, frozen, comparison, workload, settings


@pytest.fixture
def v3_setup(records, v3_seed):
    seed, *data = v3_seed
    shutil.copytree(seed.path, records.path, dirs_exist_ok=True)
    return records, *copy.deepcopy(data)


def test_v3_pair_keeps_one_parent_copy_per_distinct_vector_and_compares_under_the_gate(v3_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload, settings = v3_setup
    assert pair["outcome"]["state"] == "complete"
    evaluation = json.loads(records.swdb("get", pair["candidate_evaluation"], "--format", "json").stdout)
    assert evaluation["context"]["evaluator"] == scalable.EVALUATOR_V3
    assert evaluation["context"]["instrumentation"]["template_sha256"] == artifacts.file_hash(REPO / V3)
    sources = workload["definition"]["sources"]
    timing = evaluation["timing"]
    assert len(timing) == 6 * len(sources)
    kept = {row["parents_output"] for row in timing}
    assert len(kept) == len({row["parents_sha256"] for row in timing}) == len(set(sources))
    for row in timing:
        assert artifacts.file_hash(row["parents_output"]) == row["parents_gzip_sha256"]
    folder = Path(timing[0]["parents_output"]).parent
    assert sorted(p.name for p in folder.glob("*.parents.i32*")) == sorted(Path(p).name for p in kept)
    result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison))
    interval = result["metrics"]["confidence_interval"]
    assert result["decision"]["state"] == "fixture_comparison"
    assert interval["method"] == "paired_repetition_circular_block_bootstrap.v1" and interval["block_length"] == 2
    assert interval["relative_width"] == pytest.approx((interval["upper"] - interval["lower"])
                                                       / result["metrics"]["fixture_ratio"])


def test_v3_protocol_refuses_mixed_gate_and_spread_settings(v3_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload, settings = v3_setup
    for change, message in (
            (lambda s: s["profitability"].update(maximum_relative_spread=0.1), "no maximum_relative_spread"),
            (lambda s: s["sampling"].update(analysis="paired_repetition_block_bootstrap.v1"), "CI-width gate requires"),
            (lambda s: s["sampling"].update(block_length=4), "block_length must be"),
            (lambda s: s["profitability"]["gate"].update(maximum=1.5), "profitability.gate must be")):
        bad = copy.deepcopy(settings)
        change(bad)
        done = records.swdb("freeze-protocol", _payload(tmp_path, "bad", {
            "message_version": "1.0", "id": "bad-policy", "version": 1, "settings": bad}), "--format", "json")
        assert done.returncode == 1 and message in done.stdout + done.stderr, (message, done.stdout + done.stderr)


def test_v3_retained_vector_change_is_rejected_by_the_comparison(v3_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload, settings = v3_setup
    evaluation = json.loads(records.swdb("get", pair["candidate_evaluation"], "--format", "json").stdout)
    retained = Path(evaluation["timing"][0]["parents_output"])
    original = retained.read_bytes()
    try:
        vector = bytearray(gzip.decompress(original))
        vector[4:8] = struct.pack("<i", 4)
        retained.write_bytes(gzip.compress(bytes(vector)))
        result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison), succeeds=False)
        assert result["decision"]["state"] == "rejected"
        assert "retained parent vector" in result["decision"]["reasons"][0]
    finally:
        retained.write_bytes(original)
