"""Public native-evaluation contracts. Updated 2026-09-25.

External compiler fixtures deliberately produce fixture durations, never evidence
of native BFS performance. A separate compiler check exercises the real wrapper.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from test_proposals import proposal_setup


def test_build_directory_is_unique_external_and_enforces_host_disk_policy(tmp_path):
    from swdb.bfs_native import build_directory
    from swdb.cli import Failure
    raw = tmp_path/'raw'; records = tmp_path/'records'
    target = tmp_path/'separate-build'
    actual = build_directory({'build_directory':str(target)}, 'local-test', 'id', raw, records)
    assert actual == target and target.is_dir()
    with pytest.raises(FileExistsError):
        build_directory({'build_directory':str(target)}, 'local-test', 'id', raw, records)
    for supplied, message in [(str(records/'build'),'outside records'),(str(REPO/'build'),'outside the repository'),('relative','absolute external')]:
        with pytest.raises(Failure, match=message):
            build_directory({'build_directory':supplied}, 'local-test', 'id', raw, records)
    with pytest.raises(Failure, match='under /data1/yanruj'):
        build_directory({'build_directory':str(tmp_path/'unsafe-mbit-build')}, 'mbit10', 'id', raw, records)


PROGRAM = r'''#!/usr/bin/env python3
import json, os, signal, subprocess, sys, time
from collections import deque
from pathlib import Path
mode = os.environ.get("SWDB_NATIVE_FIXTURE", "pass")
tokens = Path(sys.argv[1]).read_text().split()
n = int(tokens[1])
source = int(sys.argv[2])
out = Path(sys.argv[3])
adj = [[] for _ in range(n)]
for i in range(4, len(tokens), 2):
    adj[int(tokens[i])].append(int(tokens[i+1]))
parent = [-1] * n
parent[source] = source
q = deque([source])
while q:
    u = q.popleft()
    for v in (reversed(adj[u]) if mode == "alternate" else adj[u]):
        if parent[v] == -1:
            parent[v] = u
            q.append(v)
if mode in {"hang", "interrupt_second"} and (mode == "hang" or out.name == "trial-0-1.json"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path(os.environ["SWDB_NATIVE_PID_FILE"]).write_text(str(child.pid))
    time.sleep(120)
if mode == "exit_zero_fail":
    print("Verification: PASS")
    print("Verification: FAIL")
    parent[source] = -1
if mode == "wrong_depth": parent[3] = 0
if mode == "out_of_range": parent[-1] = n
if mode == "wrong_source": parent[source] = -1
if mode == "reachability": parent[-1] = source
if mode == "missing": sys.exit(0)
data = {"format": "swdb.bfs.native.trial.v1", "source": source,
        "configured_threads": int(os.environ["OMP_NUM_THREADS"]),
        "roi": "bfs.complete_call.v1", "duration_s": 0.025, "parents": parent}
if mode == "no_time": data.pop("duration_s")
if mode == "bool_source": data["source"] = bool(source)
out.write_text(json.dumps(data))
'''


@pytest.fixture
def evaluation_setup(proposal_setup, tmp_path):
    records, runs, snapshot, proposal_request = proposal_setup
    keep = {"applications/gapbs.yaml", "kernels/gapbs-bfs.yaml", "implementations/gapbs-bfs-do.yaml",
            "machines/mbit10.yaml", "source_snapshots/test-source.yaml", "profile_packages/test-package.yaml"}
    for record in records.path.rglob("*.yaml"):
        if record.relative_to(records.path).as_posix() not in keep:
            record.unlink()
    impl = records.read("implementations/gapbs-bfs-do.yaml")
    impl["verification"] = {"status": "unchecked", "evidence": [], "scope": "Isolated contract fixture."}
    records.write("implementations/gapbs-bfs-do.yaml", impl)
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="native-testhost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/native-testhost.yaml", machine)
    submitted = records.swdb("submit", proposal_request(), "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text("#!/usr/bin/env python3\nimport os,sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        "if os.environ.get('SWDB_NATIVE_FIXTURE') == 'build_fail': sys.exit(7)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({PROGRAM!r}); p.chmod(0o755)\n")
    compiler.chmod(0o755)
    base = {"message_version": "1.0", "id": "eval-fixture", "candidate": candidate,
            "machine": "native-testhost", "threads": 1, "sources": [0], "repetitions": 1,
            "roi": "bfs.complete_call.v1", "fixture": True,
            "comparison_baseline": "gapbs-bfs-do",
            "build": {"compiler": str(compiler), "flags": ["-std=c++11", "-O2"]},
            "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 60},
            "workload": {"family": "contract_fixture", "graph": {"num_vertices": 5, "directed": True,
                           "edges": [[0,1], [0,2], [1,3], [2,3]]}}}

    def request(**changes):
        data = {**base, **changes}
        file = tmp_path / f"{data['id']}.yaml"
        file.write_text(yaml.safe_dump(data))
        return file
    return records, runs, request, base


def evaluate(setup, mode="pass", **changes):
    records, runs, request, _ = setup
    result = records.swdb("evaluate", request(**changes), "--runs-dir", runs, "--format", "json",
                         env={"SWDB_NATIVE_FIXTURE": mode, "SWDB_NATIVE_PID_FILE": str(runs / "child.pid")})
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)


def assert_process_gone(pid):
    until = time.monotonic() + 2
    while time.monotonic() < until:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.02)
    pytest.fail(f"evaluation descendant {pid} survived cleanup")


def test_exact_trial_correctness_and_durable_chain(evaluation_setup):
    records, _, _, _ = evaluation_setup
    result, data = evaluate(evaluation_setup, sources=[0, 4], repetitions=2)
    assert result.returncode == 0, result.stderr
    assert data["outcome"]["state"] == "complete"
    assert data["correctness"]["state"] == "passed"
    assert len(data["timing"]) == 4
    assert [(x["source"], x["repetition"]) for x in data["timing"]] == [(0,0), (4,0), (0,1), (4,1)]
    assert all(t["verified"] for t in data["timing"])
    assert data["evidence_kind"] == "contract_fixture" and not data["gain_claim"]
    assert data["profiling"]["state"] == "unavailable"
    assert data["comparison_baseline"] == "gapbs-bfs-do"
    assert records.swdb("build").returncode == 0
    retrieved = records.swdb("get", data["id"], "--chain", "--format", "json")
    assert retrieved.returncode == 0, retrieved.stderr
    assert json.loads(retrieved.stdout)["records"][data["id"]]["timing"] == data["timing"]


def test_distinct_valid_parent_trees_both_pass(evaluation_setup):
    first, left = evaluate(evaluation_setup, id="eval-first")
    second, right = evaluate(evaluation_setup, "alternate", id="eval-second")
    assert first.returncode == second.returncode == 0
    a = json.loads(Path(left["timing"][0]["output"]).read_text())["parents"]
    b = json.loads(Path(right["timing"][0]["output"]).read_text())["parents"]
    assert a != b and a[3] == 1 and b[3] == 2
    assert left["correctness"]["state"] == right["correctness"]["state"] == "passed"


def test_exhausted_total_budget_retains_no_invented_timing(evaluation_setup):
    result, data = evaluate(evaluation_setup, budget={"build_seconds": 10, "run_seconds": 5, "total_seconds": 0.001})
    assert result.returncode == 1 and data["outcome"]["state"] == "budget_exhausted"
    assert data["timing"] == [] and not data["gain_claim"]


@pytest.mark.parametrize("mode,state", [
    ("build_fail", "failed"), ("exit_zero_fail", "incorrect"), ("out_of_range", "incorrect"),
    ("wrong_depth", "incorrect"), ("wrong_source", "incorrect"), ("reachability", "incorrect"),
    ("missing", "missing_observation"), ("no_time", "missing_observation"), ("bool_source", "incompatible")])
def test_failures_are_retrievable_without_successful_profile(evaluation_setup, mode, state):
    records, _, _, base = evaluation_setup
    result, data = evaluate(evaluation_setup, mode)
    assert result.returncode == 1, result.stderr
    assert data["outcome"]["state"] == state
    assert data["outcome"]["reason"] and "summary" not in data and not data["gain_claim"]
    later = records.swdb("get", data["id"], "--format", "json")
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout)["outcome"] == data["outcome"]
    candidate = json.loads(records.swdb("get", base["candidate"], "--format", "json").stdout)
    assert candidate["state"] == "unverified"


def test_timeout_reaps_descendants_and_preserves_budget(evaluation_setup):
    _, runs, _, _ = evaluation_setup
    result, data = evaluate(evaluation_setup, "hang", budget={"build_seconds": 10, "run_seconds": 0.25, "total_seconds": 60})
    assert result.returncode == 1 and data["outcome"]["state"] == "timed_out"
    assert data["context"]["budget"]["run_seconds"] == 0.25
    pid = int((runs / "child.pid").read_text())
    assert_process_gone(pid)


def test_interrupt_retains_first_completed_trial(evaluation_setup):
    records, runs, request, _ = evaluation_setup
    path = request(sources=[0, 1], budget={"build_seconds": 10, "run_seconds": 120, "total_seconds": 180})
    env = {**os.environ, "SWDB_NATIVE_FIXTURE": "interrupt_second", "SWDB_NATIVE_PID_FILE": str(runs / "child.pid")}
    proc = subprocess.Popen([sys.executable, "-m", "swdb", "evaluate", str(path), "--records", str(records.path),
                             "--runs-dir", str(runs), "--format", "json"], cwd=REPO, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        until = time.monotonic() + 30
        while not (runs / "child.pid").exists() and proc.poll() is None and time.monotonic() < until:
            time.sleep(0.05)
        assert (runs / "child.pid").exists()
        proc.send_signal(signal.SIGTERM)
        stdout, stderr = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 1, stderr
    data = json.loads(stdout)
    assert_process_gone(int((runs / "child.pid").read_text()))
    assert data["outcome"]["state"] == "interrupted"
    assert len(data["timing"]) == 1 and data["timing"][0]["verified"]
    assert data["correctness"]["state"] == "unverified"
    later = records.swdb("get", data["id"], "--format", "json")
    assert json.loads(later.stdout)["timing"] == data["timing"]


def test_protected_build_flag_and_invalid_source_fail_before_compiling(evaluation_setup):
    _, _, _, base = evaluation_setup
    result, data = evaluate(evaluation_setup, build={**base["build"], "flags": ["-Dmain=evil"]})
    assert result.returncode == 1 and "protected" in data["outcome"]["reason"]
    assert not any(stage["stage"] == "build" for stage in data["stages"])
    result, data = evaluate(evaluation_setup, id="eval-bad-source", sources=[5])
    assert result.returncode == 1 and "outside" in data["outcome"]["reason"]
    assert not any(stage["stage"] == "build" for stage in data["stages"])


def test_candidate_macro_cannot_rewrite_trusted_clock(proposal_setup, tmp_path):
    records, runs, _, proposal_request = proposal_setup
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="macro-testhost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/macro-testhost.yaml", machine)
    proposal = proposal_request("using namespace std;", "using namespace std;\n#define /* hide */ no\\\nw fake_clock",
                                id="clock-macro")
    submitted = records.swdb("submit", proposal, "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    request = {"message_version": "1.0", "id": "eval-macro", "candidate": json.loads(submitted.stdout)["candidate"],
               "machine": "macro-testhost", "threads": 1, "sources": [0], "repetitions": 1,
               "roi": "bfs.complete_call.v1", "fixture": True,
               "workload": {"graph": {"num_vertices": 1, "directed": True, "edges": []}},
               "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 60}}
    path = tmp_path / "eval-macro.yaml"
    path.write_text(yaml.safe_dump(request))
    result = records.swdb("evaluate", path, "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1, result.stderr
    outcome = json.loads(result.stdout)
    assert "protected driver identifier now" in outcome["outcome"]["reason"]
    assert not any(stage["stage"] == "build" for stage in outcome["stages"])


def test_real_driver_compiles_and_checks_a_minimal_cpp_fixture(tmp_path):
    compiler = shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        pytest.skip("C++ compiler unavailable")
    source = tmp_path / "fixture.cc"
    source.write_text(r'''
#include <iostream>
#include <vector>
#include <cstdint>
#include <queue>
using NodeID = int32_t;
template<class T> using pvector = std::vector<T>;
struct Graph {
  std::vector<std::vector<NodeID>> adj;
  Graph(int64_t n, NodeID **idx, NodeID *neigh): adj(n) {
    for(int i=0;i<n;++i) adj[i] = std::vector<NodeID>(idx[i],idx[i+1]);
    delete[] idx; delete[] neigh;
  }
  Graph(int64_t n, NodeID **idx, NodeID *neigh, NodeID **inv, NodeID *ineigh): Graph(n,idx,neigh) {
    delete[] inv; delete[] ineigh;
  }
  int64_t num_nodes() const { return adj.size(); }
};
pvector<NodeID> DOBFS(const Graph &g, NodeID source, bool) {
  pvector<NodeID> p(g.num_nodes(), -1); p[source]=source;
  std::queue<NodeID> q; q.push(source);
  while(!q.empty()) { auto u=q.front(); q.pop(); for(auto v:g.adj[u]) if(p[v]<0) {p[v]=u;q.push(v);} }
  return p;
}
int main() { return 99; }
''')
    wrapper = tmp_path / "driver.cc"
    template = (REPO / "tools/bfs_native/driver.cc.in").read_text()
    wrapper.write_text(template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
    binary = tmp_path / "driver"
    built = subprocess.run([compiler, "-std=c++11", "-O2", str(wrapper), "-o", str(binary)], capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    graph = tmp_path / "graph"
    graph.write_text("SWDBGRAPH1 5 4 1\n0 1\n0 2\n1 3\n2 3\n")
    result_file = tmp_path / "result.json"
    result = subprocess.run([str(binary), str(graph), "0", str(result_file)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    observed = json.loads(result_file.read_text())
    assert observed["parents"] == [0,0,0,1,-1] and observed["duration_s"] > 0
    # This is fixture compilation/driver integration only, not BFS workload acceptance.
