"""`swdb profile` on the Mac: a stub benchmark that prints gapbs-style timer lines, the real
index-stream extractor on the tiny fixture graph, and a fake valgrind. Created 2026-09-22.

Tests that need real gapbs, OpenMP, and valgrind are marked `lab_host` and run on mbit10.
"""

import os
import shutil
from pathlib import Path

import pytest

from conftest import FIXTURES, REPO, read_yaml

CXX = shutil.which("c++") or shutil.which("g++")
needs_cxx = pytest.mark.skipif(CXX is None, reason="no C++ compiler to build tools/index_features")
lab_host = pytest.mark.skipif(shutil.which("valgrind") is None or not shutil.which("g++"),
                              reason="needs valgrind and g++ (runs on mbit10; valgrind does not run on macOS/arm64)")


def profile(records, tmp_path, *extra, env=None):
    runs = tmp_path / "runs"
    return records.swdb("profile", "stub-impl", "tiny-sym", "testhost", "--runs-dir", runs,
                        "--threads", "1,2,4,8", "--trials", "3", *extra, env=env), runs


def only_profile(records):
    found = sorted((records.path / "profiles").glob("*.yaml"))
    assert len(found) == 1, found
    return read_yaml(found[0])


def metric(prof, name, **where):
    hits = [m for m in prof["metrics"] if m["name"] == name and all(m.get(k) == v for k, v in where.items())]
    assert len(hits) == 1, (name, where, hits)
    return hits[0]


@needs_cxx
def test_profile_writes_a_valid_record_with_timing_footprints_and_features(records, tmp_path):
    records.add_stub()
    result, runs = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 0, result.stderr
    assert records.validate().returncode == 0
    prof = only_profile(records)
    assert prof["complete"] is True
    assert prof["status"] == "draft" and prof["provenance"][0]["kind"] == "measurement"

    # timing: one entry per thread count, median and spread from the stub's own timer lines
    assert [t["threads"] for t in prof["timing"]] == [1, 2, 4, 8]
    one = prof["timing"][0]
    assert one["times_s"] == [0.08, 0.081, 0.082] and one["median_s"] == 0.081
    assert one["spread"] == pytest.approx(0.002 / 0.081)
    assert metric(prof, "speedup", threads=4)["value"] == pytest.approx(0.081 / 0.021, rel=1e-5)
    assert metric(prof, "parallel_efficiency", threads=8)["value"] == pytest.approx(0.081 / 0.021 / 8, rel=1e-5)

    # footprints: element size x element count on the input, with the measured edge count
    assert metric(prof, "footprint_bytes", array="g.in_neighbors_")["value"] == 18 * 4
    assert metric(prof, "footprint_bytes", array="g.in_index_")["value"] == 9 * 8
    # g.out_index_ is the same memory as g.in_index_ on an undirected input: counted once
    assert metric(prof, "total_footprint_bytes")["value"] == 72 + 72 + 32
    assert metric(prof, "footprint_llc_ratio")["value"] == pytest.approx(176 / 25165824, rel=1e-3)

    # index-stream features (tools/index_features on tiny.el -s): values from expected.yaml
    assert metric(prof, "index_stream_length")["value"] == 18
    assert metric(prof, "duplicate_ratio")["value"] == pytest.approx(11 / 18)
    assert metric(prof, "duplicate_ratio")["basis"] == "measured"
    assert "index_features" in metric(prof, "duplicate_ratio")["tool"]
    assert metric(prof, "reuse_distance_histogram")["value"]["cold"] == 7

    # counts carry scopes; sweeps from the step log; repetitions = trials
    assert prof["counts"]["iterations"] == {**prof["counts"]["iterations"], "value": 18, "scope": "per_sweep",
                                            "basis": "measured"}
    assert prof["counts"]["sweeps"]["value"] == 3 and prof["counts"]["sweeps"]["scope"] == "per_call"
    assert prof["counts"]["repetitions"]["value"] == 3
    assert prof["counts"]["trips_vertex"]["value"] == 8

    # bottleneck: inferred, never measured, naming its metrics
    b = prof["bottleneck"]
    assert b["basis"] == "inferred" and "parallel_efficiency" in b["rests_on"]
    assert b["value"] == "parallelism_bound"   # tiny footprint, flat after 4 threads

    # build and run facts
    assert prof["build"]["compiler"] == "c++" and prof["build"]["compiler_version"]
    assert prof["build"]["swdb_commit"] and prof["environment"]["started"].endswith("Z")
    assert "OMP_PLACES=cores" in prof["environment"]["binding"]
    parts = {p["part"]: p["outcome"] for p in prof["parts"]}
    assert parts["cachegrind"] == "skipped" and parts["correctness"] == "complete"


@needs_cxx
def test_profile_raw_output_stays_in_the_runs_folder(records, tmp_path):
    records.add_stub()
    result, runs = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    folder = Path(prof["runs_folder"]["path"])
    assert folder.parent == runs.resolve()
    for part in prof["parts"]:
        for name in part["raw_files"]:
            assert (folder / name).is_file(), name
    assert (folder / "host-state.txt").is_file() and (folder / "timing-t8.log").is_file()


def test_profile_refuses_a_runs_folder_inside_the_repo(records, tmp_path):
    records.add_stub()
    result = records.swdb("profile", "stub-impl", "tiny-sym", "testhost", "--runs-dir", REPO / "build" / "runs",
                          "--threads", "1", "--trials", "1")
    assert result.returncode == 1
    assert "inside the repo" in result.stderr


@needs_cxx
def test_profile_fills_the_measured_edge_count_into_the_input(records, tmp_path):
    records.add_stub()
    assert records.read("inputs/tiny-sym.yaml")["properties"]["num_edges_directed"]["basis"] == "unknown"
    result, _ = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 0, result.stderr
    props = records.read("inputs/tiny-sym.yaml")["properties"]
    assert props["num_edges_directed"]["value"] == 18 and props["num_edges_directed"]["basis"] == "measured"
    assert props["num_edges_undirected"]["value"] == 9
    assert records.validate().returncode == 0


@needs_cxx
def test_view_shows_the_profile(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 0, result.stderr
    view = records.swdb("view", "stub-impl", "tiny-sym", "testhost", "--format", "json")
    assert view.returncode == 0, view.stderr
    import json

    data = json.loads(view.stdout)
    assert data["counts"]["iterations"]["value"] == 18 and data["counts"]["iterations"]["scope"] == "per_sweep"
    assert data["counts"]["repetitions"]["value"] == 3
    assert data["bottleneck"]["classification"] == "parallelism_bound" and data["bottleneck"]["basis"] == "inferred"
    assert any(m["name"] == "duplicate_ratio" for m in data["metrics"])
    arrays = {a["name"]: a for a in data["patterns"][0]["arrays"]}
    assert arrays["g.in_neighbors_"]["element_count"] == 18   # measured edge count now known
    assert data["environment"]["threads"] == [1, 2, 4, 8]


def test_failed_correctness_check_writes_no_profile(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "no", "--features", "no", env={"STUB_FAIL_VERIFY": "1"})
    assert result.returncode == 1
    assert "correctness check failed" in result.stderr
    assert not (records.path / "profiles").exists()


def test_timing_timeout_is_recorded_as_incomplete(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "no", "--features", "no", "--timeout", "1",
                        env={"STUB_SLEEP_TIMING": "3"})
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    assert prof["complete"] is False
    timing = [p for p in prof["parts"] if p["part"] == "timing"]
    assert timing[0]["outcome"] == "timed_out" and timing[0]["timeout_s"] == 1
    assert prof["timing"] == []
    assert prof["bottleneck"]["basis"] == "unknown" and prof["bottleneck"]["value"] is None


def test_correctness_timeout_stops_the_profile(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "no", "--features", "no", "--timeout", "1",
                        env={"STUB_SLEEP": "3"})
    assert result.returncode == 1 and "correctness check failed" in result.stderr
    assert not (records.path / "profiles").exists()


def _fake_valgrind_path(tmp_path):
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    shutil.copy(FIXTURES / "profile" / "fake_valgrind.py", bin_dir / "valgrind")
    shutil.copy(FIXTURES / "profile" / "cachegrind.out", bin_dir / "cachegrind.out")
    os.chmod(bin_dir / "valgrind", 0o755)
    return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def test_cachegrind_misses_are_recorded_as_simulated(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "yes", "--features", "no", env=_fake_valgrind_path(tmp_path))
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    kernel = metric(prof, "sim_ll_misses", scope="per_call")
    assert kernel["value"] == 27 and kernel["basis"] == "simulated" and kernel["threads"] == 1
    assert "LL cache:         25165824 B" in kernel["note"]
    assert metric(prof, "sim_data_refs", scope="per_call")["value"] == 350
    assert metric(prof, "sim_d1_misses", scope="per_call")["value"] == 55
    assert metric(prof, "sim_ll_misses", scope="per_run")["value"] == 1032
    assert "sim_ll_miss_rate" in prof["bottleneck"]["rests_on"]
    assert prof["complete"] is True


def test_cachegrind_timeout_is_recorded_as_incomplete_not_dropped(records, tmp_path):
    records.add_stub()
    env = {**_fake_valgrind_path(tmp_path), "FAKE_VALGRIND_SLEEP": "5"}
    result, _ = profile(records, tmp_path, "--cachegrind", "yes", "--features", "no", "--cachegrind-timeout", "1",
                        env=env)
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    assert prof["complete"] is False
    part = next(p for p in prof["parts"] if p["part"] == "cachegrind" and p["outcome"] != "complete")
    assert part["outcome"] == "timed_out" and part["timeout_s"] == 1
    assert not [m for m in prof["metrics"] if m["name"].startswith("sim_")]
    view = records.swdb("view", "stub-impl", "tiny-sym", "testhost")
    assert view.returncode == 0 and "incomplete" in view.stdout


def test_profile_refuses_another_hosts_machine_record(records, tmp_path):
    records.add_stub()
    records.copy_repo("machines")
    result = records.swdb("profile", "stub-impl", "tiny-sym", "mbit10", "--runs-dir", tmp_path / "runs",
                          "--threads", "1", "--trials", "1")
    if result.returncode == 0:
        pytest.skip("running on mbit10 itself")
    assert result.returncode == 1 and "machine record 'mbit10'" in result.stderr


def test_profile_refuses_threads_beyond_one_socket(records, tmp_path):
    records.add_stub()
    result = records.swdb("profile", "stub-impl", "tiny-sym", "testhost", "--runs-dir", tmp_path / "runs",
                          "--threads", "1,32", "--trials", "1")
    assert result.returncode == 1 and "between 1 and 16" in result.stderr


@lab_host
def test_real_gapbs_pagerank_profile_with_cachegrind(records, tmp_path):
    """On mbit10: the real baseline on a small Kronecker graph, cachegrind included."""
    records.copy_repo()
    import socket

    machine = records.read("machines/mbit10.yaml")
    if socket.gethostname().split(".")[0] != machine["hostname"]:
        pytest.skip("not on mbit10")
    inp = records.read("inputs/kron-g16-k16.yaml")
    inp["id"], inp["generator"]["arguments"] = "kron-g10-k16", "-g 10 -k 16"
    inp["properties"]["num_nodes"]["value"], inp["properties"]["scale"]["value"] = 1024, 10
    records.write("inputs/kron-g10-k16.yaml", inp)
    result = records.swdb("profile", "gapbs-pr-gs", "kron-g10-k16", "mbit10", "--runs-dir", tmp_path / "runs",
                          "--threads", "1,2", "--trials", "2", "--cachegrind", "yes", "--cachegrind-timeout", "600")
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    assert prof["complete"] is True
    assert metric(prof, "sim_ll_misses", scope="per_call")["basis"] == "simulated"
    assert prof["counts"]["sweeps"]["value"] >= 1


def test_sweeps_from_a_failed_log_run_are_not_recorded(records, tmp_path):
    records.add_stub()
    result, _ = profile(records, tmp_path, "--cachegrind", "no", "--features", "no", env={"STUB_FAIL_LOG": "1"})
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    assert "sweeps" not in prof["counts"]
    assert next(p for p in prof["parts"] if p["part"] == "sweeps")["outcome"] == "failed"
    assert prof["complete"] is False


def test_sweep_count_regex_reads_a_printed_count(records, tmp_path):
    records.add_stub()
    impl = records.read("implementations/stub-impl.yaml")
    impl["run"]["sweep_log_flag"] = None
    impl["run"]["sweep_count_regex"] = r"Graph has (\d+) nodes"   # the stub prints 8
    records.write("implementations/stub-impl.yaml", impl)
    result, _ = profile(records, tmp_path, "--cachegrind", "no", "--features", "no")
    assert result.returncode == 0, result.stderr
    assert only_profile(records)["counts"]["sweeps"]["value"] == 8


def test_input_missing_a_formula_symbol_fails_before_running(records, tmp_path):
    records.add_stub()
    inp = records.read("inputs/tiny-sym.yaml")
    del inp["properties"]["num_edges_directed"]
    records.write("inputs/tiny-sym.yaml", inp)
    result, runs = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 1 and "does not define num_edges_directed" in result.stderr
    assert not runs.exists()


def test_cachegrind_without_output_is_a_failed_part(records, tmp_path):
    records.add_stub()
    env = {**_fake_valgrind_path(tmp_path), "FAKE_VALGRIND_NO_OUTPUT": "1"}
    result, _ = profile(records, tmp_path, "--cachegrind", "yes", "--features", "no", env=env)
    assert result.returncode == 0, result.stderr
    prof = only_profile(records)
    part = [p for p in prof["parts"] if p["part"] == "cachegrind"][-1]
    assert part["outcome"] == "failed" and prof["complete"] is False


@needs_cxx
def test_alias_marked_on_either_side_is_counted_once(records, tmp_path):
    records.add_stub()
    impl = records.read("implementations/stub-impl.yaml")
    impl["access_patterns"][1]["steps"][0]["array"].pop("undirected_alias")          # g.out_index_
    for step in impl["access_patterns"][0]["steps"]:
        if step["array"]["name"] == "g.in_index_":
            step["array"]["undirected_alias"] = "g.out_index_"
    records.write("implementations/stub-impl.yaml", impl)
    result, _ = profile(records, tmp_path, "--cachegrind", "no")
    assert result.returncode == 0, result.stderr
    assert metric(only_profile(records), "total_footprint_bytes")["value"] == 72 + 72 + 32


def test_sigterm_kills_the_running_benchmark(records, tmp_path):
    import signal
    import subprocess
    import sys
    import time

    records.add_stub()
    runs = tmp_path / "runs"
    env = {**os.environ, "STUB_SLEEP_TIMING": "60"}
    proc = subprocess.Popen([sys.executable, "-m", "swdb", "profile", "stub-impl", "tiny-sym", "testhost",
                             "--records", records.path, "--db", tmp_path / "db.sqlite", "--runs-dir", runs,
                             "--threads", "1", "--trials", "1", "--cachegrind", "no", "--features", "no"],
                            cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + 30
    while not list(runs.glob("*/timing-t1.log")) and time.time() < deadline:
        time.sleep(0.2)
    time.sleep(1)
    proc.send_signal(signal.SIGTERM)
    _, err = proc.communicate(timeout=30)
    assert proc.returncode == 1 and "stopped by signal SIGTERM" in err
    left = subprocess.run(["pgrep", "-f", str(runs)], capture_output=True, text=True).stdout.split()
    assert left == [], f"benchmark processes survived: {left}"
    assert not (records.path / "profiles").exists()
