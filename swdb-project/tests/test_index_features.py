"""Index-stream feature extractor (tools/index_features), tested as a separate process.

Created 2026-09-22 (Eastern). The tool is compiled into a temporary folder with the
system C++ compiler and run on tiny.el, whose features are hand-computed in
tests/fixtures/index_features/expected.yaml, and on a small Kronecker graph for
internal consistency.
"""

import json
import math
import os
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "tools" / "index_features" / "index_features.cc"
GAPBS_SRC = REPO / "apps" / "gapbs" / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "index_features"
TINY = FIXTURES / "tiny.el"

CXX = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
if CXX is None:
    pytest.skip("no C++ compiler (c++, g++, clang++, or $CXX) found; "
                "cannot build tools/index_features", allow_module_level=True)

EXPECTED = yaml.safe_load((FIXTURES / "expected.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tool(tmp_path_factory):
    """Build the tool with the documented command; return the binary's path."""
    out = tmp_path_factory.mktemp("index_features") / "index_features"
    cmd = [CXX, "-std=c++11", "-O3", "-Wall", "-I", str(GAPBS_SRC), str(SOURCE), "-o", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, f"build failed: {' '.join(cmd)}\n{proc.stderr}"
    return out


def run_tool(tool, args, tmp_path):
    """Run the tool with --out <file>; return (completed process, parsed JSON or None)."""
    out_file = tmp_path / "features.json"
    args = [str(TINY) if a == "tiny.el" else str(a) for a in args]
    proc = subprocess.run([str(tool), "--out", str(out_file), *args],
                          capture_output=True, text=True, timeout=300)
    data = json.loads(out_file.read_text()) if out_file.exists() else None
    return proc, data


def frac(s):
    return float(Fraction(s))


def counts(histogram):
    """Bucket counts in bucket order, after checking the bucket bounds."""
    for i, b in enumerate(histogram["buckets"]):
        assert b["bucket"] == i
        assert (b["lo"], b["hi"]) == ((0, 0) if i == 0 else (2 ** (i - 1), 2 ** i - 1))
    return [b["count"] for b in histogram["buckets"]]


@pytest.mark.parametrize("case", sorted(EXPECTED))
def test_tiny_graph_matches_hand_computation(tool, tmp_path, case):
    exp = EXPECTED[case]
    proc, got = run_tool(tool, exp["args"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "", "with --out <file>, nothing may be printed on stdout"

    assert got["tool"] == "index_features"
    assert got["tool_version"] == 1
    args = exp["args"]
    want_order = args[args.index("--order") + 1] if "--order" in args else "in_neighbors_by_vertex"
    assert got["order"] == want_order
    assert got["graph"] == exp["graph"]
    assert got["stream_length"] == exp["stream_length"]
    assert got["distinct_indices"] == exp["distinct_indices"]
    assert got["duplicate_ratio"] == pytest.approx(frac(exp["duplicate_ratio"]), rel=1e-12)
    assert got["sequential_fraction"] == pytest.approx(frac(exp["sequential_fraction"]), rel=1e-12)
    assert got["same_line_fraction"] == pytest.approx(frac(exp["same_line_fraction"]), rel=1e-12)

    reuse = got["reuse_distance_histogram"]
    assert reuse["unit"] == "elements"
    assert reuse["cold"] == exp["reuse_cold"]
    assert counts(reuse) == exp["reuse_buckets"]

    line = got["line_reuse_distance_histogram"]
    assert line["unit"] == "lines"
    assert line["distinct"] == exp["line_distinct"]
    assert line["cold"] == exp["line_cold"]
    assert counts(line) == exp["line_buckets"]

    deg, exp_deg = got["degree"], exp["degree"]
    assert deg["which"] == exp_deg["which"]
    assert deg["mean"] == pytest.approx(frac(exp_deg["mean"]), rel=1e-12)
    assert deg["max"] == exp_deg["max"]
    assert deg["gini"] == pytest.approx(frac(exp_deg["gini"]), rel=1e-12)
    assert deg["cv"] == pytest.approx(math.sqrt(frac(exp_deg["cv_squared"])), rel=1e-12)


def test_symmetric_graph_same_stream_in_either_order(tool, tmp_path):
    base = ["--element-bytes", "4", "--line-bytes", "8", "--", "-f", "tiny.el", "-s"]
    _, a = run_tool(tool, ["--order", "in_neighbors_by_vertex", *base], tmp_path)
    _, b = run_tool(tool, ["--order", "out_neighbors_by_vertex", *base], tmp_path)
    for key in ("order", "degree"):
        a.pop(key), b.pop(key)
    assert a == b


def test_stdout_mode_prints_only_json(tool):
    proc = subprocess.run([str(tool), "--out", "-", "--", "-f", str(TINY)],
                          capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)  # gapbs's own lines must not be on stdout
    assert data["stream_length"] == 11
    assert "Build Time" in proc.stderr


@pytest.mark.parametrize("args", [
    ["--order", "by_magic", "--", "-f", "tiny.el"],
    ["--", "-g", "abc"],
    ["--", "-f", "tiny.el", "-x"],
    ["--", "-f", "tiny.el", "stray"],
    ["-f", "tiny.el"],
    ["--line-bytes", "0", "--", "-f", "tiny.el"],
    ["--"],
    ["--", "-f", "no_such_file.el"],
])
def test_bad_arguments_exit_nonzero(tool, tmp_path, args):
    proc, data = run_tool(tool, args, tmp_path)
    assert proc.returncode != 0
    assert proc.stderr.strip() != ""
    assert data is None, "a failed run must not leave a JSON file"


def test_kronecker_graph_is_internally_consistent(tool, tmp_path):
    proc, got = run_tool(tool, ["--", "-g", "10", "-k", "16"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    g = got["graph"]
    assert g["num_nodes"] == 1024 and g["directed"] is False
    L = got["stream_length"]
    assert L == g["num_edges_directed"] > 0

    reuse = got["reuse_distance_histogram"]
    assert got["distinct_indices"] == reuse["cold"]
    assert sum(counts(reuse)) + reuse["cold"] == L
    line = got["line_reuse_distance_histogram"]
    assert line["distinct"] == line["cold"]
    assert sum(counts(line)) + line["cold"] == L
    assert line["cold"] <= reuse["cold"]
    assert counts(reuse)[-1] > 0 and counts(line)[-1] > 0  # no trailing empty bucket

    for key in ("duplicate_ratio", "sequential_fraction", "same_line_fraction"):
        assert 0 <= got[key] <= 1
    deg = got["degree"]
    assert deg["mean"] == pytest.approx(L / g["num_nodes"], rel=1e-12)
    assert 0 <= deg["gini"] <= 1 and deg["cv"] > 0 and deg["max"] >= deg["mean"]
